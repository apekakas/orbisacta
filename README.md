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
