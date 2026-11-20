# OrbisActa – Közérthető hírek szerkesztési alapelve

**Alapelv:** minden hírt úgy fogalmazunk meg, hogy az általános műveltségű, de az adott témában nem szakértő olvasó első olvasásra megértse, mi történt és miért fontos.

## A hírek megírásának szabályai

1. **Közérthető magyar nyelv.** Kerüljük a gépies tükörfordításokat, körülményes bürokratikus megfogalmazást, fölösleges szakszavakat. A pontosság és a természetes magyar mondatszerkesztés egyszerre követelmény.
2. **A nehéz fogalmakat magyarázzuk.** Ha egy szakszó helyettesíthető köznyelvi szóval, azt használjuk. Ha szakmailag szükséges, első előfordulásánál röviden értelmezzük; utána egyszerűbb szóval hivatkozunk rá. Ha az eredeti forrás megfelelően alátámasztja, egy külön „Háttér / Mit jelent?” magyarázat is megjelenhet.
3. **Nem találunk ki definíciókat.** Bonyolult mutató pontos képletét, küszöbértékét, részletes módszertanát csak ellenőrzött forrásbizonyíték alapján állítjuk. Ha a forrásból nem igazolható, nem közöljük találgatásként.
4. **Az ötmondatos hír legyen önmagában érthető.** Nem feltétlenül kell a fogalmat öt mondaton át ismételni; az első mondatban elegendő rövid magyarázatot adni, a továbbiakban természetesebb megnevezést használni.
5. **Megőrizzük a tényeket.** Nem módosulhat a mérőszám, nevező, időszak, ország, forráshoz kötött értelmezés vagy a százalék és százalékpont közötti különbség. Az eredeti forrásidézet változatlan marad.
6. **Minden szakterületre vonatkozik.** Közgazdaság, egészségügy, tudomány, statisztika, jog, külpolitika, technológia, sport és kultúra.
7. **Nincs magyarázatnak álcázott vélemény.** Ha a hírben vitatott értelmezés szerepel, egyértelműen a forráshoz kötjük.

## Szerkesztési példák

- Ne: „A deprivációs ráta 6,3%.”  
  Inkább: „A lakosság 6,3%-a élt súlyos anyagi és társadalmi nélkülözésben.”  
  Ha a cikk alátámasztja: „Ez azt jelenti, hogy az érintettek több alapvető szükségletet anyagi okokból nem tudnak biztosítani.”
- Ne: „A total mastectomy-k aránya 70.1.”  
  Inkább: „A teljes emlőeltávolítások aránya 70,1 műtét volt 100 000 női lakosra vetítve.”
- Ne: „A reálkeresetek emelkedtek” magyarázat nélkül, ha a hír ennek jelentésére épül.  
  Inkább: „A fizetések vásárlóereje emelkedett, vagyis ugyanabból a keresetből több terméket és szolgáltatást lehetett megvásárolni” — kizárólag ha a forrás ezt alátámasztja.

## Technikai megvalósítás

A fő AI-szerkesztési utasítás a fenti alapelvet minden új magyar összefoglalóra kötelezővé teszi. Az `editorial_quality.py` a külön fogalommagyarázatot kizárólag alátámasztott, eredeti forrásból vett idézet esetén engedi közzétenni. A `hungarian_language.py` néhány egyértelműen javítható tükörfordítást szabályalapon javít, de nem helyettesíti az emberi szerkesztői ellenőrzést.
