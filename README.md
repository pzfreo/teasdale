# Teasdale Carol

Words: Sara Teasdale. Melody: In the Wheatfield (trad.).

- `teasdale-carol.pdf`: the score (two A4 pages)
- `teasdale-carol.ly`: LilyPond source
- `teasdale-carol.musicxml`: MusicXML with lyrics, for MuseScore, Sibelius, Dorico or practice apps
- `teasdale-carol.mxl`: the same, compressed (the form most apps and sites prefer)

To rebuild the PDF after editing:

```
lilypond -o teasdale-carol teasdale-carol.ly
```

To regenerate the MusicXML from the `.ly` (LilyPond has no MusicXML export, so
`ly2musicxml.py` converts the subset of LilyPond this score uses):

```
python3 ly2musicxml.py teasdale-carol.ly teasdale-carol.musicxml
```

To see what changed as notation (git revisions; default `HEAD` against the
working tree). This writes old and new PDFs with the changed bars in red, and an
overlay of the two per page: red for the old version only, green for the new:

```
python3 notediff.py [OLD [NEW]]
```
