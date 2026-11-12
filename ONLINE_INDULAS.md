# OrbisActa: online indítás GitHub Pages segítségével

**Nem kell Pythont telepítened.** A GitHub a felhőben futtatja a programot és publikálja a weboldalt. A ZIP tartalmát a GitHub új repository-jának gyökerébe töltsd fel (ne magát a ZIP-et). A fájlok a ZIP gyökerében vannak.

## 1. GitHub fiók, új repository

1. Jelentkezz be a https://github.com/ oldalon.
2. Hozz létre egy **public** repository-t, ajánlott név: `orbisacta`.
3. Töltsd fel a kicsomagolt `orbisacta_v03_online` mappa **tartalmát** a repository gyökerébe (`orbisacta.py`, `docs`, `.github`, stb.). A `.github/workflows/orbisacta-online.yml` fájlnak ténylegesen jelen kell lennie. A GitHub webes fájlfeltöltése bizonyos rejtett fájlokat elrejthet; ellenőrizd őket.
4. A repository alapértelmezett ága legyen `main` (ha eltér, az `on.push.branches` sort módosítani kell).

## 2. A weboldal publikálása

1. A repository oldalán: **Settings → Pages**.
2. **Build and deployment → Source: GitHub Actions**.
3. **Actions → OrbisActa online hírfeldolgozás és publikálás → Run workflow**.
4. Ha a két feladat (news/publish) zölden lefutott, a **Settings → Pages** alatt megjelenik a nyilvános webcím, általában `https://FELHASZNALONEV.github.io/orbisacta/`.

**Az első futás AI-kulcs nélkül is létrehozza a weboldalt, de híreket még nem fog közölni.** Így ellenőrizhető, hogy a telepítés sikerült-e.

## 3. AI-feldolgozás bekapcsolása

1. Az OpenAI API platformon hozz létre saját kulcsot és állíts be költési limitet: https://platform.openai.com/api-keys és https://platform.openai.com/settings/organization/limits . A ChatGPT-előfizetés nem azonos az API-számlázással.
2. GitHub repository: **Settings → Secrets and variables → Actions → New repository secret**.
3. Név: `OPENAI_API_KEY`; érték: a kulcsod. **Soha ne tedd a forráskódba és ne küldd el chatben.**
4. A modell alapértéke `gpt-4o-mini`. Átállíthatod `OPENAI_MODEL` repository variable-lel kompatibilis másik API-modellre (először kisméretű éles teszttel).
5. Futtasd ismét kézzel az Actiont. A weboldalon csak a bizonyítékkal ellenőrzött és forrással ellátott összefoglalók jelennek meg.

## 4. Automatikus frissülés

- A program **6 óránként** próbál frissíteni: 00:17, 06:17, 12:17, 18:17 UTC.
- Később a `.github/workflows/orbisacta-online.yml` `cron` sorával 1 óránként is futtatható, az API- és runnerköltségek figyelembevételével.
- A GitHub ütemezett futtatása késhet, vagy terheléskor kimaradhat. Nyilvános, **60 napig inaktív** repositoryknál az ütemezett munkafolyamatot automatikusan letilthatják.
- A helyi SQLite-adatbázis GitHub Actions cache-ben tárolódik. A cache **nem tartós adatbázis**, automatikusan törlődhet: ez egy pilot. Éles üzemi használathoz perzisztens adatbázis (pl. Supabase/PostgreSQL) szükséges.

## 5. Források, jogi és minőségi ellenőrzés

A `sources.json` 15 forráscsatornát tartalmaz, amelyek egy részének RSS-címe **még nincs élesben ellenőrizve**. A futás az elérhetetlen csatornákat hibaként naplózza, nem állítja, hogy működtek. Ezenkívül minden forrás és cikk licence, robots/hozzáférési feltételei és képi jogai külön vizsgálatot igényelnek. Az egyedi licenckivételek automatikus felismerése nincs kész.

Ezt a változatot tekintsd **nyilvánosan elérhető technikai pilotnak**, nem emberi szerkesztő által jóváhagyott, teljes értékű kereskedelmi hírportálnak. Az éles üzem előtt szükséges a forrásengedélyek és a hírek tényellenőrzésének szigorítása, hibajelzés, korrekció, megbízható adatbázis, adatvédelmi és impresszumoldal.

## 6. A saját domain beállítása

Ha az `orbisacta.com` vagy más domaint valóban regisztráltad, a **Settings → Pages → Custom domain** mezőben adható hozzá; ezután a domain DNS-ében a GitHub által előírt rekordokat kell létrehozni. Nem állítjuk, hogy a domain regisztrálva van.

GitHub hivatalos dokumentáció: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

## Első hibakeresés

Ha a GitHub Actions piros: **Actions → a hibás futás → news/publish → napló**. A *Kódtesztek* lépés pytestet futtat; ezt az online pilotban kijavítottuk. Ha nincs hír, nézd meg a `Hírek gyűjtése és feldolgozása` lépést: a rendszer jelezheti az elérhetetlen RSS-címeket vagy a hiányzó API-kulcsot. A GitHub titkot nem írjuk ki a naplóba.
