# OrbisActa — nemzetközi AI-hírportál, online pilot v0.3

**Cél:** valódi hírforrások automatikus gyűjtése, jogosultságellenőrzés, magyar nyelvű hírösszefoglalás, forrás- és szerzőfeltüntetés. A 3D földgömb **még nincs** megvalósítva. Az online változat GitHub Actions és GitHub Pages útján telepíthető; még nem éles szolgáltatás. A telepítéshez lásd: ONLINE_INDULAS.md.

## Mi változott a v0.1-hez képest?

- **15 hírforrás-csatorna** (nem 15 külön kiadó): Global Voices ország- és témacsatornák, Eurostat, NASA, USGS, brit pénzügyminisztérium. A `sources.json` tartalmazza a címeket és a licencnyilvántartást.
- Magyarország, Németország, USA mellett Egyesült Királyság, EU és nemzetközi (`WORLD`) hírek.
- Gazdaság, politika, tudomány, sport, kultúra, egyéb témák.
- A **Global Voices** nyílt **CC BY 3.0** tartalma; Eurostat szerkesztőségi tartalmai általában **CC BY 4.0**; GOV.UK saját szövegei jellemzően **OGL 3.0**. Mindháromnál a kiadványokban és egyes cikkekben jelzett kivételek elsőbbséget élveznek. NASA és USGS kormányzati tartalmaknál szintén lehetnek kivételek. A USGS AI alapból letiltva a további ellenőrzésig. **360info** licencét ellenőriztük, de bizonytalan RSS-végpont miatt csak későbbi integrációs jelölt.
- Minden kiválasztott összefoglaló mellett szerepel az eredeti cikk linkje, a hírforrás, az ismert szerző, valamint a licenc és a változtatás ténye. Ha a Global Voices-szerző hiányzik, az AI feldolgozás `needs_review` státusszal megáll.
- A teljes cikkeket, képeket nem tesszük közzé; csak saját magyar rövid összefoglalót. A bejegyzések eredeti 15+ karakteres szövegrészletekkel támasztják alá az állításokat (a bizonyítékok a weboldalra nem kerülnek). Az ismétlődő összefoglaló-mondatokat elutasítjuk.
- Országbesorolás: egy országra célzott hírfolyam az adott országot kapja; a globális csatornák esetében a modell javasol országot, de bizonytalan esetben `WORLD` marad.
- A nyilvános JSON-exportban csak a **30 napon belül megjelent**, validált rekordok vannak; régi cikk nem kerül „friss hír” címkével ki.
- 11 offline automatikus teszt, köztük v0.1 adatbázis migrációja.

## Fontos korlátok

1. **Valódi hálózatos RSS és OpenAI API próba nem történt ebben a futtatókörnyezetben.** XML-es végpontok közül több ismert; a Global Voices részletes ország- és téma RSS-útvonalai a hivatalos kategóriaoldal alapján felvett **tesztjelöltek** (`feed_status: needs_feed_test`). Ezek működését a `check-feeds` paranccsal lehet kideríteni az internetkapcsolattal rendelkező futtatókörnyezetben.
2. A feldolgozó nem teljes körű tényellenőrző rendszer. Az idézetszöveg valódiságát ellenőrzi, de a kijelentések bizonyító erejét és a fordítás pontosságát emberi szerkesztőnek is át kell tekintenie.
3. **A nyílt licenc nem automatikus engedély minden cikkre vagy képre.** Egyes bejegyzések kivételeinek, robots- és hozzáférési feltételeinek ellenőrzése üzemeltetői feladat. A külön engedélyköteles anyagok nem publikálhatók.
4. A rendszer nem hozott létre valós cikkekből magyar AI-összefoglalásokat. Semmilyen tartalmat nem állítunk be megtörtént hírként puszta teszt alapján.
5. A `sources.json` kiadónkénti jóváhagyása az ismert alaplicencre vonatkozik; a konkrét cikkek jogi megfelelőségét és az automatizált letöltést az első éles futtatás után felül kell vizsgálni. Képek nem kerülnek átvételre.

## Indítás Windows alatt

Szükséges: Windows 10/11, internet, **Python 3.11+** (https://www.python.org/downloads/). Kicsomagolás után indítható az `INDITAS_WINDOWS.bat` fájl. Telepíti a Python függőségeket, megpróbál RSS-t gyűjteni, és megnyitja a helyi weboldalt.

A kézi indítás:

```bat
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python orbisacta.py sources
python orbisacta.py check-feeds
python orbisacta.py collect --limit-per-feed 8
python orbisacta.py latest
python orbisacta.py serve
```

A helyi weboldal: http://127.0.0.1:8000

### OpenAI API

Az összefoglalóhoz szükséges az OpenAI API külön fizetős kulcsa, *nem elegendő* a ChatGPT előfizetés:

```bat
set OPENAI_API_KEY=SAJAT_KULCS
python orbisacta.py process --max-ai 10
python orbisacta.py export
```

Ezt követően nyisd újra a helyi oldalt. A próbaverzió jelenleg öt, bizonyítékkal megtámasztott magyar mondatot kér minden feldolgozott cikkhez, de az OrbisActa arculata nem kötődik az ötmondatos formátumhoz.

A `.env.example` csak sablon. Ne küldd el az API-kulcsot üzenetben, ne töltsd fel nyilvános tárhelyre.

## Forrásjogok / tájékoztató

- Global Voices attribúciós szabályai: https://globalvoices.org/about/global-voices-attribution-policy/
- Global Voices hivatalos RSS-lista: https://globalvoices.org/feeds/
- Eurostat felhasználási jogok: https://ec.europa.eu/eurostat/help/copyright-notice
- Eurostat RSS: https://ec.europa.eu/eurostat/en/web/rss/
- GOV.UK: https://www.gov.uk/help/terms-conditions
- OGL 3.0: https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/
- NASA RSS: https://www.nasa.gov/rss-feeds/
- NASA médiahasználat: https://www.nasa.gov/nasa-brand-center/images-and-media/
- 360info: https://360info.org/how-to-use-our-content/ (integráció még nincs)

## Következő fejlesztési feladat

1. Internetes `check-feeds` eredmények és robots / szolgáltatási feltételek ellenőrzése.
2. Éles OpenAI API-végpont-teszt minimális kerettel, forrásokra vonatkozó ellenőrzéssel.
3. Nemzetközi hírpriorizálás több forrás alapján, minőség-ellenőrzés, kézi publikációs jóváhagyás és javítási folyamat.
4. Automatizált szerveres működés és kattintható földgömb, max. 10 országos személyre szabott nézettel.


## International v0.5

A hat induló nyelv: magyar (hu), angol (en), spanyol (es), francia (fr),
német (de), portugál (pt). A használható nyelvi útvonalak:
`/hu/`, `/en/`, `/es/`, `/fr/`, `/de/`, `/pt/`.
A kezdőoldalon a kézi nyelvválasztás elsőbbséget élvez, különben
a böngésző beállított nyelvét használjuk; az ismeretlen nyelvek angolra
állnak vissza. A döntéshez **nem kérünk le IP-címet**. Az IP-alapú
országbecslést külön, adatvédelmi mérlegelés után lehet később
hozzáadni. A nyelv a hírek földrajzi szűrésétől független.

Az eredeti, ellenőrzött magyar hírek a korábbi `articles` táblában
maradnak. A nemzetközi fordítások az `article_translations` SQLite
táblába kerülnek, és időközönként `docs/news-en.json`,
`news-es.json`, `news-fr.json`, `news-de.json`, illetve
`news-pt.json` néven exportálódnak. Csak a minőségellenőrzésen
átjutott fordításokat tesszük közzé; más nyelvű tartalmat nem
címkézünk át automatikusan. Az egyes nyelveken emiatt
kezdetben eltérő számú cikk lehet.

A szerkesztőségi AI-ellenőrzés legfeljebb 10 cikket dolgoz fel futtatásonként.
A külön fordítási keret legfeljebb 3 ellenőrzött cikk öt nyelvi
változatának generálását engedi egy futásban, egyszerre egy
API-kérésben cikkenként. A meglevő fordítások újrahasznosulnak.

A `docs/ads-config.json` és a `data-ad-slot` jelölők csak
**inaktív hirdetési helyeket** készítenek elő. Nincs betöltve AdSense,
külső reklámhálózat, követőkód, helymeghatározás vagy CMP. Az éles
hirdetésekhez külön jóváhagyás, hirdetési fiók, megfelelő
hozzájáruláskezelés, adatvédelmi dokumentáció, ads.txt és
szolgáltatói integráció szükséges.

A GitHub Pages statikus tárhely. Automatikus IP-alapú
nyelvfelismeréshez külön, jogszerű helymeghatározási réteg kell.
A nyelvi SEO-végpontok a jelenlegi Pages-címen működnek, de a
saját domainre átálláskor a kanonikus URL-eket és sitemapet
aktualizálni kell.


## Mobilos megjelenítés és szerkesztői változatosság (v0.6 pilot)

- A mobilos nézetben a földgömb alapértelmezésben becsukva jelenik meg,
  de egyetlen gombbal előhívható. A hírek és az ország-/témaválasztó
  kisebb képernyőn kerülnek előtérbe.
- Zászlójelölések a hat nyelv mellett, zászlók az országválasztóknál;
  ujjmozdulattal görgethető, billentyűzettel is használható gombok.
- Az „Ajánlott” nézet frissesség, szerkesztőségi fontosság és eltérő
  kiadók megjelenítése alapján rendez. **Nem mért népszerűségi rangsor.**
  Megmarad a „Legfrissebb” és „Legfontosabb” válogatás is.
- A hírgyűjtés változatosabb tudományos forrásokkal bővült:
  NOAA (klíma/óceán), NIH (egészségügy), PLOS ONE (kutatások).
  A teljes forráslista 22 RSS-csatorna, de egy új csatorna csak
  sikeres RSS-ellenőrzés után ad tényleges híreket. Az AI-korlát nem nőtt.
- A hírek első körös AI-válogatása országok között körbejár, egy
  országon belül pedig 36 órán belüli hasonlóan friss cikkek esetén
  előnyt ad egy másik kiadónak; nem tol régi hírt előre csak azért,
  mert más kiadótól származik.
- A látogatottság és országonkénti népszerűség mérése **még nincs
  bekapcsolva**. Később agregált, adatvédelmileg megfelelő analitikai
  mérés vagy külön országos keresési trendjelzés építhető be, de a
  keresési trend nem azonos a cikk olvasottságával.


## Számszerű tények és országfogalmak (új szerkesztőségi szabály)

- Ha a hír alapjául szolgáló cikkben legalább **két fontos, számszerűen
  leírt statisztikai eredmény** található, az ötmondatos magyar összefoglalóban
  legalább két, különböző számadatnak szerepelnie kell. Az ellenőrző
  algoritmus az eredeti cikk és az AI által mellékelt szó szerinti
  bizonyító szövegrészlet számértékeit is összeveti az összefoglalóval.
  Az önmagukban álló éveket és ISO-dátumokat nem tekinti statisztikának.
- Két adatra vonatkozó szabály csak akkor érvényes, amikor a cikk tényleg
  tartalmaz legalább két érdemi, számként felismerhető statisztikát.
  Egyetlen valós adat esetén nem szabad másodikat kitalálni.
- Az AI a cikkben megjelenő országfüggő törvény, intézmény vagy fogalom
  mellé **legfeljebb két külön háttérmagyarázó mondatot** készíthet;
  ezek az ötmondatos hírösszefoglalón felül, külön blokkban jelennek meg.
  A magyarázat az eredeti forrásban megjelenő fogalomhoz és bizonyító
  szöveghelyhez kötött. Ha nincs elegendő forrás, nem jelenik meg.
- A forrásadatok és a forrásból kiragadott bizonyító idézetek továbbra sem
  kerülnek ki a nyilvános JSON-ba; csak az ellenőrzött saját összefoglaló
  és a kiegészítő szöveg jelenik meg.
- A hatnyelvű rendszer a háttérmagyarázatokat a hírekkel együtt,
  **ugyanabban a korlátozott fordítási API-kérésben** fordítja le.
  A régi hírek és fordítások kompatibilisek maradnak, de a korábban
  publikált cikkekre az új szabály nem kerül automatikusan, költségesen
  visszamenőleg alkalmazásra.
- A számfelismerés szándékosan konzervatív: fontos marad a kézi ellenőrzés
  arra, hogy egy százalék vagy más mérőszám szövegkörnyezete,
  időszaka és jelentése nem változott-e meg a fordítás során.


## Globális országkínálat és telefonos használat

- Hozzáadott országok: India (IN), Kína (CN), Ausztrália (AU),
  Szaúd-Arábia (SA), Nigéria (NG), Dél-Afrika (ZA).
- Az országlista telefonon kétoszlopos, valóban tördelődő rács:
  nincs oldalra kilógó vagy csak vízszintesen lapozva elérhető elem.
  A földgömb megmarad külön megnyitható nézetnek, egyujjas
  forgatással, kétujjas csippentéses nagyítással és +/− gombokkal.
- Az országok számának növekedése nem jelenti azt, hogy rögtön
  van mindegyikről magyar, illetve öt idegen nyelvű összefoglaló.
  Az új országok Global Voices RSS-csatornái először éles
  ellenőrzésen mennek át; az esetleg hibás vagy üres feed
  miatt nem állhat le a többi ország hírgyűjtése.
- A meglévő 10 AI-cikk és 3 ötnyelvű fordítás futtatásonkénti
  költségkorlátja változatlan. Az országszűrés és a hírportál
  nyelvválasztása továbbra is független egymástól.


## Olvashatóbb hírkártyák és fogalommagyarázatok

- Mind a hat nyelven a cikkek témája pasztell árnyalatú keretet,
  témacímkét és a témaválasztóval egyező ikont kap. A cikk fejlécében
  szerepel a hír földrajzi besorolásának országzászlója, illetve
  világhír esetén a 🌐 jelzés. A zászló a hírhez társított országot
  jelzi, nem feltétlenül a hírközlő szervezet székhelyét.
- Amikor a forrás alátámasztja, a cikk szövegdoboza ALATT,
  elkülönülő pasztell sávban „Fogalmak röviden” magyarázat
  jelenik meg. Legfeljebb két bővített mondat.
- A fogalom lehet országspecifikus intézmény, jogszabály,
  rövidítés, tudományos/technikai vagy gazdasági szakkifejezés.
  Csak az eredeti cikkben igazolható, forrásszövegre támaszkodó
  meghatározás jelenhet meg. Ellenőrizetlen szakkifejezéshez
  nem generálunk biztosként állított definíciót.
- A már korábban publikált híreknél, ahol nincs ellenőrzött
  fogalommagyarázat, ez a külön mező nem látszik.
  A bővített utasítás az újonnan feldolgozott híreket érinti,
  a régi cikkek visszamenőleges újragenerálása nélkül.
- Androidon a földgömb nagyítását látható százalék jelzi;
  ez a kijelzés egyszerű szövegelemből áll és minden újrarajzoláskor
  frissül. A +/− gombok és a kétujjas gesztus megmaradtak.
- A meglévő 10 hír és 3 ötnyelvű fordítás / futás
  korlát változatlan.

## Következő szerkesztőségi lépés: hírérték és hétnapos archívum

- Az AI öt magyar mondata továbbra is öt külön, a forrásból
  alátámasztott tény. Nem jelenhet meg helyette olyan metaszöveg,
  hogy „A cikk bemutatja...” vagy „A tanulmány ismerteti...”.
  Új offline ellenőrzés vizsgálja a tipikus üres fordulatokat.
  A korábbi két, eredeti forrásidézettel alátámasztott statisztikai
  adat szabálya és a legfeljebb kétmondatos fogalommagyarázat megmarad.
- A publikus híradat mostantól **hét UTC-naptári napot** tartalmaz,
  a mai napot is beleértve. A news.json és az öt news-{lang}.json
  ugyanazt az archive metaadatot tartalmazza
  (start_date, end_date, days=7, timezone=UTC).
- A felhasználó az „Országok” és „Témák” **két külön,
  összecsukható paneljén** szűrhet, mobilon ezek alapból
  összecsukva jelennek meg; az országválasztás független a
  hírportál nyelvétől. A „Hírek megtekintése” gomb mindkét
  panelt bezárja és a hírfolyamhoz görget.
- Az egyetlen dátumválasztó az elmúlt hét napból **egy napot**
  választhat ki; „Mind a 7 nap” gombbal minden rendelkezésre
  álló hír ismét látszik. Nem tartalmaz további időszakot.
  A dátum az *eredeti hírforrás publikálási dátuma UTC szerint*,
  nem az AI által készített összefoglaló létrehozási ideje.
  A kliens ugyanabból az előre elkészített hírhalmazból szűr;
  dátumváltáskor nincs új AI-kérés és nincs új szerverköltség.
- A hírek és a nyelvi fordítások már korábban is a GitHub Actions
  futások között visszatöltött SQLite-adatbázisban élnek. A
  hétnapos szűrés nem törli visszamenőleg a korábbi belső rekordokat;
  csak a nyilvános hírfolyamból szűri ki a régebbi tételeket.
  Ez a cache-alapú tárolás **pilothoz megfelelő**, de
  önmagában nem tartós mentés vagy garantált archívum:
  a GitHub cache lejárhat vagy kiürülhet. Az éles üzemi,
  jogilag és üzletileg fontos archívumhoz külön tartós
  adatbázis vagy automatikus mentés ajánlott.
- A 10 új AI-hírfeldolgozás és a 3 ötnyelvű fordítás /
  futtatás korlátja nem változik.

## A szerkesztőségi minőség számszerű követése

Minden sikeres hír-export friss, nyilvános **docs/quality.json** összesítést
készít ugyanabból a hét UTC-naptári napra korlátozott, már publikálásra
jóváhagyott magyar hírhalmazból, amelyet a news.json tartalmaz.
A hírportálon a panel alapból zárt, csak megnyitáskor töltődik be.

A panel országonként és témánként közli a publikált hírek számát,
azokat a híreket, amelyekben legalább két különböző statisztikai érték
felismerhető, a forráshoz kötött fogalommagyarázatot tartalmazó híreket,
a különböző **szerkesztőségi kiadók** számát és az egy kiadóhoz
tartozó hírek arányát. A Global Voices különböző országos és tematikus
RSS-csatornái nem számítanak külön kiadónak.

A panel külön jelzi, ahol nem jelent meg friss ellenőrzött hír, ahol
legalább három cikk egyetlen szerkesztőségtől származik, illetve
ahol egy témában nincs friss hír. A hiány nem azt jelenti, hogy
az adott országban nem történt esemény, hanem hogy a jelenlegi
forrás- és szerkesztői rendszerben nincs jóváhagyott új cikk.

**A számfelismerés tájékoztató jellegű mutató:** a meglévő összefoglaló
szövegéből történik. A régi cikkek eredeti forrását nem kérjük le újra,
és a két szám jelenléte önmagában nem igazolja a tényhelyességet.
Nem várunk statisztikai számokat minden témájú cikktől; a
fogalommagyarázat hiánya sem feltétlenül hiba.
Ez nem olvasottsági vagy népszerűségi rangsor.

Nem kerülnek ki a belső, jóvá nem hagyott hírek, azok címei,
az AI-hibák és belső bizonyító idézetek. Nincs látogatói
IP-feldolgozás, követés vagy személyre szabott mérés.
A kimutatások az eddigi GitHub-futtatásonkénti
**10 új AI-hír + 3 ötnyelvű fordítás** költségkeretét nem növelik.

## Címközpontú, összecsukható hírek

A hírkártyákban alapból csak az ország zászlója és neve, a témakör
pasztell jelvénye és a címsor látszik. Natív details/summary elemek
biztosítják a billentyűzettel is kezelhető lenyitást. A Részletek
megnyitásakor jelenik meg az ötmondatos összefoglaló, a szerző,
a dátum, a kiadó, a licenc, az eredeti hír linkje és a meglévő,
forráshoz kötött fogalommagyarázat. A böngészőkben a közös name
attribútum egyszerre legfeljebb egy kibontott hírt enged.

A földgömb mobilos megnyitógombján csak egy földgömb ikon marad,
az országmenü helyjelölőt (📍), a világkategória térképet (🗺️) használ.
A minőségpanel változatlanul megmarad, de összecsukva.
Ez kizárólag felületi változás, nem növeli az AI-költséget.
