# GA052: Schnellvergleich MD vs. Extrakt

- Extrakt gefunden: ja
- Metrik: difflib.SequenceMatcher-Ratio (0-100, höher = ähnlicher)
- length_diff: Zeichenanzahl MD minus Extrakt-Segment (negativ = Extrakt länger)

| Nr. | Vortrag | Ratio | length_diff | Hinweis |
| --- | --- | --- | --- | --- |
| 1 | DAS EWIGE UND DAS VERGÄNGLICHE DES MENSCHEN, Berlin, 6. September 1903 | 0.14 | 22227 |  |
| 2 | DER URSPRUNG DER SEELE, Berlin, 3. Oktober 1903 | 0.36 | 22338 |  |
| 3 | DAS WESEN DER GOTTHEIT VOM THEOSOPHISCHEN STANDPUNKT, Berlin 7. November 1903 | - | - | Anker nicht im Extrakt gefunden |
| 4 | THEOSOPHIE UND CHRISTENTUM, Berlin, 4. Januar 1904 | 0.11 | 39332 |  Vergleich auf 40k Zeichen gekürzt |
| 5 | DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE I, Berlin, 27. November 1903 | 0.12 | 27836 |  |
| 6 | DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE II, Berlin, 4. Dezember 1903 | 0.16 | 27746 |  |
| 7 | DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE III, Berlin, 17. Dezember 1903 | 0.09 | 28275 |  |
| 8 | THEOSOPHISCHE SEELENLEHRE I KÖRPER UND SEELE, Berlin, 16. März 1904 | 0.25 | 39352 |  Vergleich auf 40k Zeichen gekürzt |
| 9 | THEOSOPHISCHE SEELENLEHRE II SEELE UND MENSCHENSCHICKSAL, Berlin, 23. März 1904 | 0.04 | 39488 |  Vergleich auf 40k Zeichen gekürzt |
| 10 | THEOSOPHISCHE SEELENLEHRE III SEELE UND GEIST, Berlin, 30. März 1904 | 0.10 | 39391 |  Vergleich auf 40k Zeichen gekürzt |
| 11 | THEOSOPHIE UND SPIRITISMUS, Berlin, 1. Februar 1904 | 0.32 | 32740 |  |
| 12 | THEOSOPHIE UND SOMNAMBULISMUS, Berlin, 7. März 1904 | 0.22 | 39366 |  Vergleich auf 40k Zeichen gekürzt |
| 13 | DIE GESCHICHTE DES SPIRITISMUS, Berlin, 30. Mai 1904 | 0.08 | 39103 |  Vergleich auf 40k Zeichen gekürzt |
| 14 | DIE GESCHICHTE DES HYPNOTISMUS UND DES SOMNAMBULISMUS, Berlin, 6. Juni 1904 | 0.04 | 39433 |  Vergleich auf 40k Zeichen gekürzt |
| 15 | WAS FINDET DER HEUTIGE MENSCH IN DER THEOSOPHIE, Berlin, 8. März 1904 | 0.24 | 39242 |  Vergleich auf 40k Zeichen gekürzt |
| 16 | WAS WISSEN UNSERE GELEHRTEN VON THEOSOPHIE, Berlin, 28. April 1904 | 0.07 | 39315 |  Vergleich auf 40k Zeichen gekürzt |
| 17 | IST DIE THEOSOPHIE UNWISSENSCHAFTLICH, Berlin, 6. Oktober 1904 | 0.15 | 32661 |  |
| 18 | IST DIE THEOSOPHIE BUDDHISTISCHE PROPAGANDA, Berlin, 8. Dezember 1904 | 0.45 | -5916 |  Vergleich auf 40k Zeichen gekürzt |

## 1. DAS EWIGE UND DAS VERGÄNGLICHE DES MENSCHEN, Berlin, 6. September 1903
- Ratio: 0.14
- length_diff: 22227
- Beispiele für Abweichungen (erste 5):
  - replace: md='der gegenstand uber den hier gesprochen werden soll ist zweifellos einer an dem das interesse aller menschen hangt wer konnte sagen das er nicht an der frage de...' | extract='berlin 6 september...'
  - replace: md=' jahrhundert es so herrlich...' | extract='03 13 unsterblichkeit in der modernen...'
  - replace: md='eit gebracht haben...' | extract='issenschaft feuerbach haeckel stra us und in den alten mysterien sichtbares und unsichtbares in der...'
  - replace: md='ahrend in all den jahrhunderten...' | extract='elt physische...'
  - replace: md='orher nur un...' | extract='ererbung im organi schen seelische ...'

## 2. DER URSPRUNG DER SEELE, Berlin, 3. Oktober 1903
- Ratio: 0.36
- length_diff: 22338
- Beispiele für Abweichungen (erste 5):
  - insert: md='...' | extract='berlin 3 oktober 1903 27 seelenkunde ohne seele ...'
  - replace: md='er heute uber das wesen der seele s...' | extract='issenschaft und religion theoso ...'
  - replace: md='richt setzt sich...' | extract='hie als...'
  - replace: md='o...' | extract='ermittleri...'
  - replace: md='ei seiten mis...' | extract='ischen beiden seelisches entsteht nur aus seelischem das seelische steht uns unendlich nahe tol stojs kampf aus dieser anschauung die ...'

## 3. DAS WESEN DER GOTTHEIT VOM THEOSOPHISCHEN STANDPUNKT, Berlin 7. November 1903
- Hinweis: Anker nicht im Extrakt gefunden

## 4. THEOSOPHIE UND CHRISTENTUM, Berlin, 4. Januar 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.11
- length_diff: 39332
- Beispiele für Abweichungen (erste 5):
  - replace: md='o...' | extract='berlin 4 januar 1904 62 theosophie als dienerin des christentums die historisch kritische theologie des 19 jahrhunderts d ...'
  - replace: md='t...' | extract=' straus...'
  - replace: md='wechselt man heute noch das was die theosophische gesellscha...' | extract=' ...'
  - replace: md='t ist mit ...' | extract='luchtigter gottes...'
  - replace: md='uddhistischer weltanschauung ofters habe ich mir in diesen monatlichen versammlungen schon die bemerkung erlaubt das bei dem theosophischen kongres in chicago 1...' | extract='egri...'

## 5. DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE I, Berlin, 27. November 1903
- Ratio: 0.12
- length_diff: 27836
- Beispiele für Abweichungen (erste 5):
  - delete: md='mit der ...' | extract='...'
  - replace: md='merkung das die gegen...' | extract='rlin 27 november 1903 88 der einflus der kantschen philosophie erkenntnisquelle der theosophie ist eine hohere erfahrung kantianismus die ...'
  - replace: md='artige namentlich deutsche philosophie und im besonderen ihre erkenntnistheorie es den bekennern derselben sch...' | extract='elt ist meine vorstellung christian ...'
  - replace: md='ierig macht den zugang zu der theosophischen weltanschauung zu finden habe ich vor acht tagen diese vortrage eingeleitet und ich bemerkte das ich versuchen werd...' | extract='ol...'
  - replace: md='en sein mag so du...' | extract=' und kant kant und hume e...'

## 6. DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE II, Berlin, 4. Dezember 1903
- Ratio: 0.16
- length_diff: 27746
- Beispiele für Abweichungen (erste 5):
  - replace: md='mit der bemerkung dass die gegenwartige namentlich deutsche...' | extract='berlin 4 dezember 1903 104 der kantianismus kants traume eines geistersehers nach der...'
  - replace: md='ilosophie und im besonderen ihre erkenntnistheorie es den bekennern derselben schwierig macht den zugang zu der theosophischen weltanschauung zu...' | extract='ysik des 19 jahrhunderts sind...'
  - replace: md='inden habe ich vor acht tagen diese vortrage eingeleitet und ich bemerkte dass ich versuchen werde diese erkenntnistheorie diese gegenwartige philosophische wel...' | extract='arb und schall...'
  - replace: md='angen deren sich der mensch aber nicht bewusst ist solange alles wohl steht und dann aus einer ...' | extract='indungen nichts als subjektiv wahrgenommene schwin gungen mullers geset...'
  - replace: md='weiten stelle es ist manches ...' | extract=' der spe...'

## 7. DIE ERKENNTNISTHEORETISCHEN GRUNDLAGEN DER THEOSOPHIE III, Berlin, 17. Dezember 1903
- Ratio: 0.09
- length_diff: 28275
- Beispiele für Abweichungen (erste 5):
  - replace: md='in den vorhergehenden vortragen habe ich versucht die gegenwartige erkenntnistheorie wie sie an unseren universitaten getrieben wird und wie sie auch von denjen...' | extract='berlin 17 de...'
  - replace: md='u skizzieren ich versuchte zu gleicher zeit anzudeuten wie die ganze wissenschaftliche entwickelung des...' | extract='ember...'
  - insert: md='...' | extract='03 121 die erkenntnistheoretische toleranz der theosophie theo sophie widerlegt nicht die verschiedenen standpunkte sie sucht den wahrheitskern aller schopenhau...'
  - replace: md='ahrhunderts sei es die physikalische die physiologische und auch die psychologische im grunde genommen die kantsche erkenntnistheorie oder ihre ausbildung...' | extract='ede erkenntnis in den dingen sein keplers erkenntnis...'
  - replace: md='ie sie durch schopenhauer durch eduard...' | extract='ar solcher art robert hamerling die...'

## 8. THEOSOPHISCHE SEELENLEHRE I KÖRPER UND SEELE, Berlin, 16. März 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.25
- length_diff: 39352
- Beispiele für Abweichungen (erste 5):
  - replace: md='um die himmelsweisheit den menschen mitteilen zu konnen bedarf es der selbsterkenntnis plato verehrte seinen grosen lehrer sokrates aus dem grunde besonders wei...' | extract='berlin...'
  - replace: md='jahrhundert hatte man kein bewusstsein mehr von der alten einteilung selbst cartesius unterschied nur ...' | extract='mar...'
  - delete: md='wischen seele die er geist nennt und korper und so blieb es diejenigen welche heute von der psychologie oder seelenwissenschaft sprechen wissen nicht dass sie u...' | extract='...'
  - replace: md=' jahrhundert und seiner geistigen entwickelung den stempel aufgedruckt hat hat immer und immer wieder erklart dass mit ihren anschauungen eine seelenwissenschaf...' | extract='04...'
  - replace: md=' jahrhunderts s...' | extract='8 gotteserkenntnis durch selbsterkenntnis sokrates gliede rung des wesens des menschen in leib seele und geist die konzilsdogmen uber den menschen als leib und ...'

## 9. THEOSOPHISCHE SEELENLEHRE II SEELE UND MENSCHENSCHICKSAL, Berlin, 23. März 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.04
- length_diff: 39488
- Beispiele für Abweichungen (erste 5):
  - replace: md='die materialistische weltanschauung hat das moderne denken ...' | extract='berlin 23 mar...'
  - replace: md='u der grotesken behauptung gefuhrt dass die herrliche tragodie des hamlet nichts weiter sei als die umgewandelten nahrungsmittel die der grose dichter shakespea...' | extract=' 1904...'
  - replace: md=' jahrhundert geglaubt ...' | extract='3 materialistische anschauung der seele leibniz gegenargu ment lust und schmerz als grundtatsache des seelenlebens das schicksal das artmasige beim tier das ind...'
  - replace: md='orden ist dass sich ...' | extract='icklungsstu...'
  - replace: md='ische ...' | extract='e die ansicht der naturwissenscha...'

## 10. THEOSOPHISCHE SEELENLEHRE III SEELE UND GEIST, Berlin, 30. März 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.1
- length_diff: 39391
- Beispiele für Abweichungen (erste 5):
  - replace: md='die materialistisch...' | extract='berlin 30 marz 1904 191 sokrates abschiedsgesprach uber die unsterblichkeit ma thematik als schule fur vorurteilslose erkenntnis fur denken jenseits von lust un...'
  - replace: md='eltanschauung hat das moderne denken zu der grotesken behauptung gefuhrt das die herrliche tragodie des hamlet nichts...' | extract='ordenen...'
  - replace: md='eiter sei als die umgewandelten nahrungsmittel die der grose dichter shakespeare genossen hat nun zunachst konnte eine solche behauptung als eine ironische als ...' | extract='ortes die ausschaltung der seele in der hyp nose die seele als...'
  - replace: md='organge einer uhr zu verstehen haben aus dem triebwerk dieser uhr dann bleibt uns nichts anderes ubrig als in denjenigen ursachen in denen wir die grunde zu suc...' | extract='ermittlerin...'
  - replace: md='ei junge studenten miteinander dis...' | extract='ischen ...'

## 11. THEOSOPHIE UND SPIRITISMUS, Berlin, 1. Februar 1904
- Ratio: 0.32
- length_diff: 32740
- Beispiele für Abweichungen (erste 5):
  - delete: md='vor acht tagen versuchte ich ihnen zu zeigen was der moderne mensch innerhal...' | extract='...'
  - replace: md=' der theosophie heute...' | extract='erlin 1...'
  - replace: md='inden kann ...' | extract='e...'
  - replace: md='evor ich den zyklus dieser vortrage fortsetze ist die spezielle frage der theosophie zu besprechen und ihr verhaltnis zu den grosen kulturaufgaben der gegenwart...' | extract='ruar...'
  - replace: md=' jahrhunderts nun erklart sich aber die...' | extract='04 218 der gegensatz der...'

## 12. THEOSOPHIE UND SOMNAMBULISMUS, Berlin, 7. März 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.22
- length_diff: 39366
- Beispiele für Abweichungen (erste 5):
  - replace: md='das thema des heutigen vortrages soll eine art ergan...' | extract='berlin 7 mar...'
  - delete: md='ung dessen sein woruber ich vor vier wochen hier sprach eine erganzung zu dem thema theosophie und spiritismus heute will ich einiges was ich damals nur andeute...' | extract='...'
  - insert: md='...' | extract='04 242 die unterschiedliche bewertung des somnambulismus in der antike im ausgehenden mittelalter und im 19...'
  - replace: md='s im letzten drittel des 18 jahrhunderts begann menschliche seelenzustande zu studieren da gab es einige die da glaubten dass man durch das studium dieser zusta...' | extract=' magnetiseur und magnetischer...'
  - replace: md='der aber ein ganz besonderer schlafzustand ist...' | extract='traumbe wustsein und traumerlebnisse traumhandlungen physi scher...'

## 13. DIE GESCHICHTE DES SPIRITISMUS, Berlin, 30. Mai 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.08
- length_diff: 39103
- Beispiele für Abweichungen (erste 5):
  - replace: md='heute obliegt es mir uber ein thema zu ihnen zu sprechen das von der einen seite wir durfen wohl sagen millionen von begeisterten anhangern in der welt hat auf ...' | extract='berlin 30 mai...'
  - replace: md='7 jahrhundert herein erst im 17 jahrhundert beginnt im grunde genommen dasjenige eine bestimmte gestalt anzunehmen was man heute berechtigt ist spiritismus zu n...' | extract='904...'
  - replace: md='9 heiten wurde nun entruckt...' | extract='4 der spiritismus als ausgangspunkt fur blavatsky und oleott der moderne spiritismus und die mysterien des altertums die kirche und die mysterienwahrheit im mit...'
  - replace: md='eglicher menschen...' | extract='ung stilling ennemoser kerner d ...'
  - replace: md='orschung entruckt dem unmittelbaren menschlichen streben die...' | extract=' straus natur wissenschaft und spiritismus der sieg des spiritismus in amerika andrew ...'

## 14. DIE GESCHICHTE DES HYPNOTISMUS UND DES SOMNAMBULISMUS, Berlin, 6. Juni 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.04
- length_diff: 39433
- Beispiele für Abweichungen (erste 5):
  - replace: md='heute habe ich ihnen uber ein kapitel der neueren geistesgeschichte zu sprechen welches zwar eine alte geschichte in einer gewissen form wiederholt aber doch in...' | extract='berlin 6...'
  - replace: md='ahr hundert erobert habe nun lassen sie mich demgegenuber ihnen ein zeugnis aus dem 17 jahrhundert anfuhren das zeugnis das ich ihnen anfuhren mochte ist aus ei...' | extract='uni...'
  - replace: md=' jahrhunderts gesehen haben die wissen dass hansen die leute nachdem er sie in hypnotischen schla...' | extract='04 305 athanasius kirchers bericht uber hypnose bei tieren expe rimente mit hypnose die be...'
  - insert: md='...' | extract='ahigung zum hypnotiseur franz anton mesmer wilhelm preyer der tierische magne tismus ein gutachten uber den mesmerismus betrug und schwindel bei schausteller hy...'
  - replace: md='ersetzt hatte mit einer ganz geringen unter...' | extract=' xv was ...'

## 15. WAS FINDET DER HEUTIGE MENSCH IN DER THEOSOPHIE, Berlin, 8. März 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.24
- length_diff: 39242
- Beispiele für Abweichungen (erste 5):
  - replace: md='die theosophische...' | extract='berlin 8 marz 1904 333 die forschung nach dem ursprung der religionen entste hen und vergehen aller auseren erscheinung die natur des lebendigen...'
  - replace: md='eltanschauung ist ...' | extract='iedergeburt als eigenscha...'
  - replace: md='ur diejenigen welche eine ...' | extract='t des lebens die kra...'
  - replace: md='estere begrundung ihrer begriffe und ihrer vorstellungen in bezug auf die ubersinnliche welt gebrauchen und fur diejenigen die nach einer solchen tieferen begru...' | extract='te der seele...'
  - replace: md='dadurch ...' | extract='wiederge...'

## 16. WAS WISSEN UNSERE GELEHRTEN VON THEOSOPHIE, Berlin, 28. April 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.07
- length_diff: 39315
- Beispiele für Abweichungen (erste 5):
  - replace: md='wenn eine geistesrichtung sich im verlaufe der menschheitsentwickelung durchsetzen soll eine geistesrichtung welche nicht die anerkennung oder vielleicht auch n...' | extract='berlin 28 april...'
  - replace: md='0...' | extract='4 356 das stichwort theosophie in...'
  - replace: md='u ...' | extract='eitgenossischen lexika wie hartmann gegen seine philosophie des unbewusten so konnte auch die theosophie leicht eine streitschri...'
  - replace: md='inden ist also in einem der neuesten werke das tatsachlich auch die meisten theosophischen begri...' | extract='t gegen sich selbst schreiben der tatsachen...'
  - insert: md='...' | extract='anatismus der gelehr ten physische und geistige sinneswerkzeuge beweise in der theosophie zwei grundverschiedene betrachtungsweisen der atomismus goethes ...'

## 17. IST DIE THEOSOPHIE UNWISSENSCHAFTLICH, Berlin, 6. Oktober 1904
- Ratio: 0.15
- length_diff: 32661
- Beispiele für Abweichungen (erste 5):
  - replace: md='vor acht tagen versuchte ich ihnen zu zeigen was der moderne mensch innerhalb der theosophie heute finden kann bevor ich den zyklus dieser vortrage fortsetze is...' | extract='berlin 6 oktober...'
  - replace: md=' jahrhunderts nun erklart sich aber die natur...' | extract='04 385 die autoritat der ...'
  - replace: md='unserer ...' | extract='haeckels weltratsel und lebenswunder huxleys einwand der hoherentwicklung preyers vorstellung der erde als groses lebendiges wesen die entwicklung des lebendige...'
  - replace: md='it gan...' | extract='lrasse und die sieben unterrassen die trennung der ursprunglichen ein heit von wissenschaft kunst philosophie religion und ethik goethes und wagners versuche ...'
  - replace: md=' bestimmten fragen gegenuber fur unfahig sie zu beantworten gewiss wie ich das auch schon im ...' | extract='ur wieder...'

## 18. IST DIE THEOSOPHIE BUDDHISTISCHE PROPAGANDA, Berlin, 8. Dezember 1904
- Hinweis:  Vergleich auf 40k Zeichen gekürzt
- Ratio: 0.45
- length_diff: -5916
- Beispiele für Abweichungen (erste 5):
  - replace: md='der heutige...' | extract='berlin 8 dezember 1904 404 der unterschied zwischen buddhismus und budhismus exoterisch und esoterisch...'
  - replace: md='trag ist da...' | extract='geruckte individualitaten als wichtige fuhrer der menschheit die einflusse derselben auf die theosophie theosophie und christentum die rosen kreu...'
  - replace: md='u bestimmt eines der ...' | extract='er chakra...'
  - replace: md='erbreitetsten...' | extract='arti esoterik im buddhismus angebliche lebensflucht im buddhismus nirwana die lebendige gei stesstromung in der theosophie im wahren theosophen leben nicht wort...'
  - replace: md='urteile uber die theoso...' | extract='trage dieses bandes gehoren dem teil von rudolf steiners vortrags werk an mit dem er sich an die offentlichkeit wandte berlin war der ausgangs...'
