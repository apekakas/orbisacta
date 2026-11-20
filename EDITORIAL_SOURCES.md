# OrbisActa – további hírszerkesztőségek és engedélyezési terv

Frissítés: 2026-11-20. Ez a lista **szerkesztőségi jelöltlista**,
nem automatizáltan jogtisztázott, aktivált RSS-források listája.

## Miért nincs még elég hír?

A 2026-11-20 19:24 UTC GitHub-futtatás logja szerint az adattárban
49 korábban jóváhagyott hír szerepelt, ezek közül 44 volt a nyilvános
hétnapos időszakon belül, 125 cikk feldolgozásra várt,
33 ellenőrzést igényelt, 30 cikknek nem egyezett a várt országa.
A publikus RSS-kínálat önmagában nem magyarázza a publikált hírek számát:
a futtatásonkénti AI-keret 10 új hír, ebből a megfelelően igazolható,
a forrásszöveget ténylegesen tartalmazó cikkek jelenhetnek meg.

A 2026. novemberi fejlesztés: Oroszország külön ország,
engedélyezett Global Voices ország-RSS jelölttel; natív
cirill/japán/kínai forrásfeldolgozás és a nem egyértelmű országú
cikkek kizárása mellett az egyértelműen más országról szóló
cikkek korrekt átsorolása. Előzetesen hibás szerzői/adatkinyerési
tételek helyett ugyanabban a 10 API-hívásos keretben másik
forráscikket választhat a rendszer. A 10/hívásos keretet nem emeljük.

## Szerkesztőségi jelöltek, nem automatikusan jóváhagyott források

| Terület | Szerkesztőségek | Felhasználási státusz |
| --- | --- | --- |
| Oroszország | Meduza (https://meduza.io/en); The Moscow Times (https://www.themoscowtimes.com/); Mediazona (https://zona.media/); Novaya Gazeta Europe (https://novayagazeta.eu/) | Csak a Meduza egyes cikkei CC BY feltételűek. Minden cikkre külön licencellenőrzés, a többinél engedély vagy megfelelő jogalap szükséges |
| Japán | NHK World Japan (https://www3.nhk.or.jp/nhkworld/); Kyodo News (https://english.kyodonews.net/); Nikkei Asia (https://asia.nikkei.com/) | Szerzői jogok és technikai elérhetőség ellenőrzendő |
| Kína | Caixin (https://www.caixin.com/); Sixth Tone (https://www.sixthtone.com/); Reuters (https://www.reuters.com/) | Különösen fontos a különböző nézőpont, az eredeti kínai szövegek kezelése és a jogtisztázás |
| India | The Hindu (https://www.thehindu.com/); The Indian Express (https://indianexpress.com/) | Jogi ellenőrzésig csak szerkesztőségi jelöltek |
| Afrika | Daily Maverick (https://www.dailymaverick.co.za/); Premium Times (https://www.premiumtimesng.com/) | Jogi ellenőrzésig csak szerkesztőségi jelöltek |
| Ausztrália | ABC News (https://www.abc.net.au/news); SBS News (https://www.sbs.com.au/news/) | Jogi ellenőrzésig csak szerkesztőségi jelöltek |
| Világ | Associated Press (https://apnews.com/); Reuters (https://www.reuters.com/); BBC News (https://www.bbc.com/news); France 24 (https://www.france24.com/) | Minőségi, szerkesztett sajtóforrások, de nincs általános automatikus teljes szöveges újrafelhasználási engedély |

Oroszországnál külön kell választani az **állami szervek állításait**
(elsődleges, ellenőrizendő közlés) a független szerkesztőségek
riportjaitól és tényellenőrzésétől. A hírszemle nem fogadja el
egyik szereplő állítását sem automatikusan bizonyított tényként.
A cikkek feltételezett CC-licencét sosem szabad kizárólag
egy adott kiadó általános nevéből levezetni.

## Javasolt bevezetési sorrend

1. RSS URL, nyelv, robots- és hozzáférési feltételek ellenőrzése.
2. Szerzői/licencjogosultság megállapítása az adott cikk vagy
   tartalomfajta alapján; csak ezután ai_approved=true.
3. Cikkminőségi teszt: elegendő forrásszöveg,
   tényszerűség, ország, több nézőpont, pontos számok.
4. Hétnapos ország- és témaköri lefedettség összevetése,
   kézi mintavétel a forrás és a magyar összefoglaló között.
5. Ha további **napi mennyiséget** szeretnénk a megtisztított
   feldolgozáson túl, a futtatásonkénti OpenAI API-keretet
   külön döntésként lehet emelni; ez többletköltséget okoz.

A hírek olvasása/feldolgozása Unicode-alapú: cirill, japán,
egyszerűsített és hagyományos kínai írás megmarad a forrásszövegben.
A közönségnek továbbra is csak HU/EN/ES/FR/DE/PT nyelven
készül összefoglaló; RU/JA/ZH új kimeneti nyelv még nincs.
