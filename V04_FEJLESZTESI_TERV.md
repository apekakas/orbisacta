# OrbisActa v0.4 – minőségi hírek bővítése (fejlesztőági terv)

## Elfogadott konfiguráció
- Szerkesztőségi cél: **100 elfogadott magyar hír naponta**, nem garantált minimum.
- Gyűjtés: **6 óránként**, változatlan GitHub Actions cron (UTC 00:17, 06:17, 12:17, 18:17).
- Forrásstratégia: nemzetközi és országos források vegyesen.
- Hírminőség: változatlan öt állítás + idézett forrásbizonyíték, számszerű és szerkesztőségi ellenőrzések.
- Meglévő éles API-keret: **10 cikkfeldolgozási hívás/futás**, max. 3 fordítás/futás. A célérték NEM növeli a költséget.

## Ami ezen az ágon változik
1. A gyűjtés RSS-csatornánként 6 helyett 12 új bejegyzést vizsgál (nem jelent AI-hívást).
2. A feldolgozó az AI-kvótához arányított, 4-szeres jelölt-előválogatást használ, megszűnik a fix 40-es plafon.
3. A `quality_capacity.py` kiszámolja a napi cél hátralevő részét és a ténylegesen engedélyezett AI-feldolgozási keretet.
4. Új forrásjelöltek a `sources.json` végén (BBC, DW, France 24, ANSA, NHK, NPR, Guardian, Európai Bizottság). **Mindegyik letiltva** a feed és a felhasználási jogok éles ellenőrzéséig. Egyelőre nem gyűjtenek és nem használnak API-t.
5. Új offline tesztek és külön v0.4 GitHub Actions tesztfolyamat.

## API-költség engedélyezése — KIZÁRÓLAG külön jóváhagyás után
A `--daily-target 100` kizárólag szerkesztőségi cél. A `--max-ai` paraméter önmagában nem emelheti a 10-es korlátot.
A magasabb API-felhasználáshoz **két külön beállítás** kell: 
- a munkafolyamat `--max-ai` értéke, és
- egy kifejezetten operátor által beállított `ORBIS_APPROVED_MAX_AI_PER_RUN` környezeti változó.

**Egyiket sem növeltük ezen a fejlesztőágon.** 100 elfogadott hírhez jellemzően több mint 25 feldolgozás/futás szükséges az elutasított cikkek miatt, tehát külön költségkalkuláció és jóváhagyás kell.

## Minőségi és jogi kontroll
- Az RSS-hírcím vagy kivonat önmagában nem elég az ötmontados összefoglalóhoz: teljes, ellenőrizhető szövegrész és idézett bizonyíték kell.
- A különböző médiumok nézőpontjai maradhatnak, de duplikációkat eseményszinten további fejlesztéssel kell csoportosítani.
- RSS elérhetősége nem ad automatikusan jogot a cikkek teljes szövegének átvételére vagy AI-feldolgozására.
- Új kiadói feedet csak dokumentált jogi/technikai ellenőrzés után engedélyezzünk.
- Éles, száz hír/nap üzemi célhoz tartós adatbázis, költségfigyelés és hibatűrés fejlesztése is szükséges.

## Teszt
`python -m pytest -q tests/`

## Élesítés
Ez **csak egy felülvizsgálatra szánt fejlesztőág**, nem indulhat el automatikusan a 100 hír/nap publikálás. Az ágat a `main` ágba csak külön döntés után egyesítsük. Az API-hívások plafonjának emelése külön jóváhagyást igényel.
