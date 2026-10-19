"""Convert teasdale-carol.ly to MusicXML (with lyrics).

Handles only the LilyPond subset this score uses: absolute pitches, chords,
`q`, rests, spacers, full-bar rests, ties, slurs, \\melisma, two-voice
`<< { } \\new Voice { } >>` blocks, and \\lyricsto-style lyric alignment.

    python3 ly2musicxml.py teasdale-carol.ly teasdale-carol.musicxml
"""
import re
import sys
from xml.sax.saxutils import escape

DIV = 4  # divisions per quarter note (sixteenths are the shortest value)
BAR = 3 * DIV  # 3/4
KEY_FLATS = {"B": -1, "E": -1, "A": -1}  # E-flat major


def strip_comments(text):
    return re.sub(r"%[^\n]*", "", text)


def block(text, name):
    """Return the body of `name = { ... }` or `name = \\lyricmode { ... }`."""
    m = re.search(r"^%s = (?:\\lyricmode )?\{" % name, text, re.M)
    i = m.end()
    depth = 1
    j = i
    while depth:
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
        j += 1
    return text[i : j - 1]


TOKEN = re.compile(
    r'"[^"]*"|<<|>>|\{|\}|<[^>]*>[0-9.]*|\\[A-Za-z]+|[_^]\\[A-Za-z]+|\\[<>!]|'
    r"[a-gqrsR][a-z]*[',]*[0-9]*\.*(?:\*\d+)?|~|\(|\)|\|"
)


def tokens(src):
    return TOKEN.findall(src)


def parse_pitch(s):
    m = re.match(r"([a-g])([a-z]*)([',]*)$", s)
    letter, acc, octs = m.groups()
    if letter + acc == "es":
        alter = -1
    else:
        alter = acc.count("is") - acc.count("es")
    octave = 3 + octs.count("'") - octs.count(",")
    return (letter.upper(), alter, octave)


def parse_duration(s, prev):
    m = re.match(r"(\d+)(\.*)", s)
    if not m:
        return prev
    base = 4 * DIV // int(m.group(1))
    d = base
    add = base
    for _ in m.group(2):
        add //= 2
        d += add
    return d


class Event:
    def __init__(self, start, dur, pitches, kind="note"):
        self.start, self.dur, self.pitches, self.kind = start, dur, pitches, kind
        self.tie_start = self.tie_stop = False
        self.slur_start = self.slur_stop = False
        self.melisma_start = self.melisma_end = False
        self.lyric = None  # (syllabic, text)
        self.fermata = False


class Music:
    """Parses a music block into voices: {voice_no: [Event]}, plus which
    events belong to the lyric-bearing (named) voice."""

    def __init__(self):
        self.voices = {1: [], 2: []}
        self.lyric_events = []
        self.prev_dur = DIV
        self.prev_chord = None

    def parse(self, src):
        toks = tokens(strip_comments(src))
        self.seq(toks, 0, 0, voice=1, lyric=True)
        return self

    def seq(self, toks, i, t, voice, lyric, stop="}"):
        """Parse a sequence until `stop`; returns (index, end_time)."""
        while i < len(toks):
            tok = toks[i]
            if tok == stop:
                return i + 1, t
            if tok == "<<":
                i, t = self.simul(toks, i + 1, t, voice, lyric)
                continue
            if tok == "\\new":  # \new Voice { ... } on its own
                i += 2
                assert toks[i] == "{"
                v = voice
                if toks[i + 1] == "\\voiceTwo":
                    v = 2
                i, t = self.seq(toks, i + 1, t, v, lyric=False)
                continue
            if tok == "{":
                i, t = self.seq(toks, i + 1, t, voice, lyric)
                continue
            i, t = self.item(toks, i, t, voice, lyric)
        return i, t

    def simul(self, toks, i, t, voice, lyric):
        ends = []
        while toks[i] != ">>":
            if toks[i] == "\\new":
                i += 2
                v = 2 if toks[i + 1] == "\\voiceTwo" else 1
                i, e = self.seq(toks, i + 1, t, v, lyric=False)
            else:
                assert toks[i] == "{"
                i, e = self.seq(toks, i + 1, t, voice, lyric)
            ends.append(e)
        return i + 1, max(ends)

    def item(self, toks, i, t, voice, lyric):
        tok = toks[i]
        evs = self.voices[voice]
        last = evs[-1] if evs else None
        if tok == "~":
            last.tie_start = True
        elif tok == "(":
            last.slur_start = True
        elif tok == ")":
            last.slur_stop = True
        elif tok == "\\melisma":
            last.melisma_start = True
        elif tok == "\\melismaEnd":
            last.melisma_end = True
        elif tok == "\\fermata":
            last.fermata = True
        elif tok in ("^\\markup", "_\\markup"):
            i += 2  # skip \italic "text"
        elif tok.startswith("\\") or tok.startswith("^") or tok.startswith("_") or tok.startswith('"') or tok == "|":
            if tok == "\\bar":
                i += 1
        elif tok.startswith("R"):
            m = re.match(r"R([0-9.]*)(?:\*(\d+))?", tok)
            n = int(m.group(2) or 1)
            for _ in range(n):
                e = Event(t, BAR, None, "rest")
                evs.append(e)
                t += BAR
        elif tok.startswith("<"):
            m = re.match(r"<([^>]*)>(.*)", tok)
            pitches = [parse_pitch(p) for p in m.group(1).split()]
            d = parse_duration(m.group(2), self.prev_dur)
            t = self.add(evs, Event(t, d, pitches), t, lyric)
            self.prev_chord = pitches
        else:
            m = re.match(r"([a-gqrs][a-z]*[',]*)([0-9]*\.*)", tok)
            name, durs = m.groups()
            d = parse_duration(durs, self.prev_dur)
            if name == "r":
                e = Event(t, d, None, "rest")
            elif name == "s":
                e = Event(t, d, None, "space")
            elif name == "q":
                e = Event(t, d, self.prev_chord)
            else:
                e = Event(t, d, [parse_pitch(name)])
            t = self.add(evs, e, t, lyric)
        return i + 1, t

    def add(self, evs, e, t, lyric):
        self.prev_dur = e.dur
        if evs and evs[-1].tie_start and e.kind == "note":
            e.tie_stop = True
        evs.append(e)
        if lyric:
            self.lyric_events.append(e)
        return t + e.dur


def attach_lyrics(music, words):
    toks = words.split()
    notes = []
    in_slur = in_melisma = False
    tied = False
    for e in music.lyric_events:
        if e.kind != "note":
            continue
        cont = tied or in_slur or in_melisma
        if not cont:
            notes.append(e)
        tied = e.tie_start
        if e.slur_start:
            in_slur = True
        elif e.slur_stop:
            in_slur = False
        if e.melisma_start:
            in_melisma = True
        elif e.melisma_end:
            in_melisma = False
    n = 0
    hyphen_before = False
    k = 0
    while k < len(toks):
        tok = toks[k]
        k += 1
        if tok in ("--", "__"):
            continue
        if n >= len(notes):
            break
        e = notes[n]
        n += 1
        if tok == "_":
            continue
        hyphen_after = k < len(toks) and toks[k] == "--"
        syl = {(False, False): "single", (False, True): "begin", (True, True): "middle", (True, False): "end"}[
            (hyphen_before, hyphen_after)
        ]
        e.lyric = (syl, tok)
        hyphen_before = hyphen_after


STEP_ORDER = "CDEFGAB"
TYPES = {16: "whole", 8: "half", 4: "quarter", 2: "eighth", 1: "16th"}


def note_type(d):
    for base in (16, 8, 4, 2, 1):
        if d == base:
            return TYPES[base], 0
        if d == base * 3 // 2:
            return TYPES[base], 1
    raise ValueError(d)


def pitch_xml(p, chord, e, voice, staff_stem, beam=None):
    step, alter, octave = p
    out = ["<note>"]
    if chord:
        out.append("<chord/>")
    out.append("<pitch><step>%s</step>%s<octave>%d</octave></pitch>" % (
        step, "<alter>%d</alter>" % alter if alter else "", octave))
    out.append("<duration>%d</duration>" % e.dur)
    if e.tie_start:
        out.append('<tie type="start"/>')
    if e.tie_stop:
        out.append('<tie type="stop"/>')
    out.append("<voice>%d</voice>" % voice)
    typ, dots = note_type(e.dur)
    out.append("<type>%s</type>" % typ + "<dot/>" * dots)
    if alter != KEY_FLATS.get(step, 0):
        out.append("<accidental>%s</accidental>" % {0: "natural", 1: "sharp", -1: "flat"}[alter])
    if staff_stem:
        out.append("<stem>%s</stem>" % staff_stem)
    if beam and not chord:
        for n, kind in enumerate(beam, 1):
            out.append('<beam number="%d">%s</beam>' % (n, kind))
    notations = []
    if e.tie_start:
        notations.append('<tied type="start"/>')
    if e.tie_stop:
        notations.append('<tied type="stop"/>')
    if not chord:
        if e.slur_start or e.melisma_start:
            notations.append('<slur type="start"/>' if e.slur_start else "")
        if e.slur_stop:
            notations.append('<slur type="stop"/>')
        if e.fermata:
            notations.append("<fermata/>")
    notations = [n for n in notations if n]
    if notations:
        out.append("<notations>%s</notations>" % "".join(notations))
    if not chord and e.lyric:
        syl, text = e.lyric
        out.append('<lyric number="1"><syllabic>%s</syllabic><text>%s</text></lyric>' % (syl, escape(text)))
    out.append("</note>")
    return "".join(out)


def beams(evs):
    """Beam runs of eighths/sixteenths that sit within one quarter-note beat."""
    marks = {}
    run = []

    def flush():
        if len(run) > 1:
            for k, e in enumerate(run):
                kind = "begin" if k == 0 else "end" if k == len(run) - 1 else "continue"
                levels = [kind]
                if e.dur == 1:
                    prev16 = k > 0 and run[k - 1].dur == 1
                    next16 = k < len(run) - 1 and run[k + 1].dur == 1
                    levels.append("continue" if prev16 and next16 else "end" if prev16 else
                                  "begin" if next16 else ("backward hook" if k else "forward hook"))
                marks[id(e)] = levels
        run.clear()

    for e in evs:
        short = e.kind == "note" and e.dur < DIV
        beat = e.start // DIV
        if short and run and run[-1].start // DIV == beat and run[-1].start + run[-1].dur == e.start:
            run.append(e)
        else:
            flush()
            if short and e.start % DIV + e.dur <= DIV:
                run.append(e)
    flush()
    return marks


def measure_events(evs, m):
    lo, hi = m * BAR, (m + 1) * BAR
    return [e for e in evs if lo <= e.start < hi]


def part_xml(pid, music, nbars, extra_lyrics):
    for e, text in extra_lyrics:
        e.lyric = ("single", text)
    two_voice_bars = {e.start // BAR for e in music.voices[2] if e.kind == "note"}
    out = ['<part id="%s">' % pid]
    for m in range(nbars):
        out.append('<measure number="%d">' % (m + 1))
        if m == 0:
            out.append("<attributes><divisions>%d</divisions><key><fifths>-3</fifths></key>"
                       "<time><beats>3</beats><beat-type>4</beat-type></time>"
                       "<clef><sign>G</sign><line>2</line></clef></attributes>" % DIV)
        split = m in two_voice_bars
        for v in (1, 2):
            evs = measure_events(music.voices[v], m)
            if v == 2:
                if not split:
                    break
                out.append("<backup><duration>%d</duration></backup>" % BAR)
            t = m * BAR
            bm = beams(evs)
            for e in evs:
                if e.start > t:
                    out.append("<forward><duration>%d</duration></forward>" % (e.start - t))
                    t = e.start
                stem = ("up" if v == 1 else "down") if split else None
                if e.kind == "space":
                    out.append("<forward><duration>%d</duration></forward>" % e.dur)
                elif e.kind == "rest":
                    whole = e.dur == BAR
                    typ = "" if whole else "<type>%s</type>%s" % (note_type(e.dur)[0], "<dot/>" * note_type(e.dur)[1])
                    out.append('<note><rest%s/><duration>%d</duration><voice>%d</voice>%s</note>' % (
                        ' measure="yes"' if whole else "", e.dur, v, typ))
                else:
                    for k, p in enumerate(e.pitches):
                        out.append(pitch_xml(p, k > 0, e, v, stem, bm.get(id(e))))
                t = e.start + e.dur
            if t < (m + 1) * BAR and evs:
                out.append("<forward><duration>%d</duration></forward>" % ((m + 1) * BAR - t))
        if m == nbars - 1:
            out.append('<barline location="right"><bar-style>light-heavy</bar-style></barline>')
        out.append("</measure>")
    out.append("</part>")
    return "\n".join(out)


def first_note_in_bar(music, voice, bar):
    for e in music.voices[voice]:
        if e.kind == "note" and e.start // BAR == bar - 1:
            return e


def main(src, dst):
    text = open(src, encoding="utf-8").read()
    up = Music().parse(block(text, "upper"))
    down = Music().parse(block(text, "lower"))
    attach_lyrics(up, block(text, "upperWords"))
    attach_lyrics(down, block(text, "lowerWords"))
    title = re.search(r'title = "([^"]*)"', text).group(1)
    poet = re.search(r'poet = "([^"]*)"', text).group(1)
    composer = re.search(r'composer = "([^"]*)"', text).group(1)
    nbars = max(e.start + e.dur for v in (up, down) for evs in v.voices.values() for e in evs) // BAR
    # The "Ah" vocalises are markups/melismas in the .ly; give them a lyric here.
    up_ah = [(first_note_in_bar(up, 1, 22), "Ah"), (first_note_in_bar(up, 1, 30), "Ah")]
    down_ah = [(first_note_in_bar(down, 1, 46), "Ah")]
    xml = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
        '"http://www.musicxml.org/dtds/partwise.dtd">',
        '<score-partwise version="4.0">',
        "<work><work-title>%s</work-title></work>" % escape(title),
        '<identification><creator type="lyricist">%s</creator><creator type="composer">%s</creator></identification>'
        % (escape(poet.replace("Words: ", "")), escape(composer.replace("Melody: ", ""))),
        "<part-list>",
        '<score-part id="P1"><part-name>Upper</part-name></score-part>',
        '<score-part id="P2"><part-name>Lower</part-name></score-part>',
        "</part-list>",
        part_xml("P1", up, nbars, up_ah),
        part_xml("P2", down, nbars, down_ah),
        "</score-partwise>",
    ]
    open(dst, "w", encoding="utf-8").write("\n".join(xml) + "\n")
    print("wrote", dst, nbars, "bars")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
