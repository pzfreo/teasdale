# Teasdale Carol

Words: Sara Teasdale. Melody: In the Wheatfield (trad.).

- `teasdale-carol.pdf`: the score (two A4 pages)
- `teasdale-carol.ly`: LilyPond source
- `teasdale-carol.musicxml`: MusicXML with lyrics, for MuseScore, Sibelius, Dorico or practice apps

To rebuild the PDF after editing:

```
lilypond -o teasdale-carol teasdale-carol.ly
```

To regenerate the MusicXML from the `.ly` (LilyPond has no MusicXML export, so
`ly2musicxml.py` converts the subset of LilyPond this score uses):

```
python3 ly2musicxml.py teasdale-carol.ly teasdale-carol.musicxml
```
