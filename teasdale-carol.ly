\version "2.24.0"

\header {
  title = "Teasdale Carol"
  poet = "Words: Sara Teasdale"
  composer = "Melody: In the Wheatfield (trad.)"
  tagline = ##f
}

\paper {
  #(set-paper-size "a4")
  top-margin = 12\mm
  bottom-margin = 12\mm
  left-margin = 15\mm
  right-margin = 15\mm
  system-system-spacing.basic-distance = #14
  ragged-last-bottom = ##f
  ragged-bottom = ##f
  page-count = 2
  systems-per-page = 6
}

#(set-global-staff-size 20)

global = {
  \key es \major
  \time 3/4
  \tempo "Andante sostenuto"
  \compressEmptyMeasures
}

ah = \markup \italic "Ah"

% next note takes its own syllable even though it is under a slur
sylInSlur = \once \set melismaBusyProperties = #'()

% lift the next tie (drawn above) so it runs between the stem tops
tieAtStems = \shape #'((0 . 2.8) (0 . 3.6) (0 . 3.6) (0 . 2.8)) Tie

upper = {
  \global
  R2.*4 |
  % verse 1
  es'8\p g' bes'4. g'8 | aes'8 aes' g'4. aes'8 | bes'8 g' es'4. g'8 | bes'8 bes' bes'4 r8 g'8 |
  aes'8 aes' c''4. aes'8 | g'8 g' bes'4. g'8 | g'8 f' f'4. es'16( d') | es'8 es' es'4. r8 |
  % verse 2
  es'8 es' es''4. d''8 | bes'8 bes' bes'4 r8 aes'8 | f'8 f' f''4. d''8 | bes'8 bes' bes'4 r8 g'8 |
  aes'8 aes' c''4. aes'8 | g'8 g' bes'4. g'8 | g'8 f' f'4. es'16( d') | es'8 es' es'4. r8 |
  R2.^\markup \italic "(Ommm)" |
  << { \voiceOne es''4\p\melisma d'' bes' | c''4 bes'4. r8 }
     \new Voice { \voiceTwo <es' g'>2.~ | <es' f'>4 <es' g'>4. s8 } >>
  << { \voiceOne g'4 <g' c''> <c'' es''> | <bes' d''>4 <d'' f''>8 r <bes' d''>4 | <f' c''>4 <aes' es''> <f' c''> | <f' bes'>4 <g' d''>4 <f' bes'>4 | <aes' c''>4 <es' aes'> <d' f'> | <es' g'>4 <g' bes'> <bes' es''>\melismaEnd | <c'' es''>4\melisma <aes' c''> <c'' es''> | <c'' f''>4 <aes' c''> r4 | <d'' f''>4 <bes' d''> <d'' f''> | <d'' g''>4\p <bes' d''> <g' bes'> | <f' c''>4 <aes' es''> <f' c''> | <f' bes'>4 <g' d''>4 <f' bes'>4 | <aes' c''>4 <f' aes'> <d' f'> | <es' g'>4 <g' bes'>2 | <g' bes'>8\melismaEnd r r2 \oneVoice }
     \new Voice { \voiceTwo es'4 es' g' | f'4 g'8 s f'4 | es'4 f' es' | d'4 f' d' | es'4 c' c' | bes4 es' g' | aes'4 es' aes' | aes'4 f' s4 | bes'4 f' bes' | bes'4 g' d' | es'4 f' es' | d'4 f' d' | es'4 c' aes | bes4 es'2 | es'8 s s2 } >>
  
  R2.*3 |
  es'8\mf g' bes'4. g'8 | aes'8 aes' g'4. aes'8 | bes'8 g' es'4. g'8 | bes'8 bes' bes'4 r8 g'8 |
  aes'8 aes' c''4. aes'8 | g'8 g' bes'4. g'8 | g'8 f' f'4. es'16( d') | es'8 es' es'4 r8 es'8 |
  es'8 es' es''4. c''8 | aes'8 aes' aes'4. g'8 | f'8 f' f''4. d''8 | bes'8\mp bes' bes'4 r8 g'8 |
  aes'8 aes' c''4. aes'8 | g'8 g' bes'4. g'8 | g'8 f' f'4. es'16( d') | es'8( es' es'2~ | es'2.) |
  << \new Voice { \voiceOne r8 g'8 bes'4 g'4 | aes'4 c''2 | bes'2. | bes'2.\fermata | bes'8 r r2 }
     \new Voice { \voiceTwo s8 d'8 g'4 d'4 | es'4 aes'2 | g'2. | g'2. | g'8 s s2 } >>
  
  \bar "|."
}

upperWords = \lyricmode {
  Kings they came from out the South, All dressed in er -- mine fine; __ _ _
  They bore Him gold and chry -- so -- prase, And gifts of pre -- cious wine. __ _ _
  Shep -- herds came from out the North, their coats were brown and old; __ _ _
  They brought Him lit -- tle new -- born lambs— They had not a -- ny gold. __ _ _
  Ah __ Ah __
  Kings they knocked up -- on the door, The wise men en -- tered in. __ _ _
  The shep -- herds fol -- lowed af -- ter them To hear the song be -- gin. __ _ _
  The an -- gels sang all through the night Un -- til the ri -- sing sun, __ _ _
  But lit -- tle Je -- sus fell a -- sleep Be -- fore the song was done.
}

lower = {
  \global
  R2.*4 |
  es'4\p( g') es' | f'4( es') es' | d'4( c') es' | d'2 r4 |
  r4 es' f'~ | f' c'( \sylInSlur aes) | es'( c') aes | aes f4. r8 |
  es'4\mp( bes') g' | aes' g' es' | f' c'' a' | bes'( aes') f' |
  r4 es' f'~ | f' d' bes | es'( c') aes | bes g4. r8 |
  R2. |
  es'8\p g' bes'4. g'8 | aes'8 aes' g'4. aes'8 | bes'8 g' es'4. g'8 | bes'8 bes' bes'4 r8 g'8 |
  aes'8 aes' c''4. aes'8 | g'8 g' bes'4. g'8 | g'8 f' f'4. es'16( d') | es'8 es' es'4. r8 |
  es'8\mf es' es''4. c''8 | aes'8 aes' aes'4. g'8 | f'8 f' f''4. d''8 | bes'8 bes' bes'4 r8 g'8 |
  aes'8 aes' c''4. aes'8 | g'8 g' bes'4. g'8 | g'8 f' f'4. es'16( d') | es'8 es' es'2 | es'8 r r2 |
  R2.*3 |
  es'8\mf g' bes'4. g'8 | aes'8 aes' g'4. aes'8 | bes'8 g' es'4. g'8 | bes'8 bes' bes'4 r4 |
  \new Voice {
    es'4(_\ah g' f') | d'( f' es') | c'( es' \tieAtStems d'^~) | d'( c' bes) |
    g4( bes des') | c'2( c'4) | a( c' es') | d'2\mp r4 |
    es'4\p( g' f') | d'( f' es') | c'( es' d') | es'2.~ | es'2. |
  }
  << \new Voice { \voiceOne r8 d'8 g'4 d'4 | es'4\mp\< es' f'\! | g'2. | g'2.\fermata | g'8 r r2 }
     \new Voice { \voiceTwo s8 bes8 d'4 bes4 | c'4 es' d' | es'2. | es'2. | es'8 s s2 } >>
  
  \bar "|."
}

lowerWords = \lyricmode {
  Kings __ _ dressed in er -- mine fine.
  And gifts __ _ of pre -- cious wine. __ _
  Shep -- herds came __ _ _ out from the North, __ _
  they had __ _ not a -- ny gold. __ _
  Wise men came from out the East, And they were wrapped in white; __ _ _
  The star that led them all the way Did glo -- ri -- fy the night. __ _ _
  An -- gels came from hea -- ven high, And they were clad with wings; __ _ _
  And lo, they brought a joy -- ful song The host of hea -- ven sings. __ _ _ _
  Kings they knocked up -- on the door, The wise men en -- tered in. __ _ _
}

\score {
  \new ChoirStaff <<
    \new Staff \with { instrumentName = "Upper" shortInstrumentName = "U" } {
      \new Voice = "up" \upper
    }
    \new Lyrics \lyricsto "up" \upperWords
    \new Staff \with { instrumentName = "Lower" shortInstrumentName = "L" } {
      \new Voice = "down" \lower
    }
    \new Lyrics \lyricsto "down" \lowerWords
  >>
  \layout {
    \context { \Score \override BarNumber.break-visibility = ##(#f #t #t) }
  }
}
