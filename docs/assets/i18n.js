/* OrbisActa international UI - extend the locales table for new languages.
   Browser locale / user selection only. No IP lookup or analytics is performed. */
(function(){
"use strict";
const locales={
hu:{
 tag:"Nemzetközi hírek · Szerkesztőségi próbarendszer",eye:"Világkép",
 hero:"A világ hírei, több ország nézőpontjából.",
 lead:"Válaszd ki az országokat és témákat. Csak ellenőrzött, forrásmegjelöléssel ellátott hírösszefoglalókat jelenítünk meg.",
 globeEye:"OrbisActa · Világtérkép",globeTitle:"A hírek földrajzi nézetben.",
 globeLead:"Forgasd a Földet, válassz országot, és olvasd a rendelkezésre álló magyar összefoglalókat.",
 globeCount:"ellenőrzött hír a rendszerben",globeReady:"Országválasztásra készen.",
 globeHelp:"Forgatás egy ujjal · Nagyítás két ujjal vagy a +/− gombbal",
 globeSource:"Térképi alapadatok: Natural Earth (közkincs). A jelölők tájékoztató jellegűek.",
 europe:"Európa",america:"Amerika",asia:"Ázsia",allNews:"Összes hír",
 filtersTitle:"Országok és témák",viewResults:"Hírek megtekintése",countriesShort:"ország",countryLabel:"Országok",africa:"Afrika",oceania:"Óceánia",zoomIn:"Nagyítás",zoomOut:"Kicsinyítés",topicLabel:"Témakör",
 sort:"Rendezés",latest:"Legfrissebb elöl",importance:"Legfontosabb elöl",
 footer:"OrbisActa · Fejlesztői prototípus. Az AI-val készült összefoglalók nem helyettesítik az eredeti cikkeket vagy az emberi ellenőrzést.",
 allCountries:"Összes ország",allTopics:"Összes",topics:{politika:"Politika",gazdaság:"Gazdaság",tudomány:"Tudomány",sport:"Sport",kultúra:"Kultúra",egyéb:"Egyéb"},
 count:"ellenőrzött hír",filtered:"a szűrés után",emptyTitle:"Nincs még hír a kiválasztott szűrőkhöz.",
 emptyText:"Válassz másik országot vagy témát. A lefordított hírek száma fokozatosan bővül.",
 credit:"AI-val készített magyar összefoglaló",sourceLink:"Eredeti hír és forrásmegjelölés",backgroundTitle:"Fogalmak röviden",
 updated:"Frissítve",loadError:"A híradat még nem készült el.",
 world:"Világ",eu:"Európai Unió",global:"Világhírek",
 globeAll:"Minden ország kiválasztva – kattints egy jelölőre a szűréshez.",
 globeFiltered:"kiválasztott földrajzi nézet",globeStory:"publikált hír",mapError:"A térkép betöltése nem sikerült. Az országválasztó gombok használhatók.",
 mapLinesError:"A térképvonalak nem töltődtek be, az országjelölők használhatók.",
 chooseCountry:"híreinek kiválasztása",showGlobe:"🌍 Földgömb megnyitása",hideGlobe:"Földgömb elrejtése",featured:"Ajánlott · friss és fontos",language:"Nyelv",translationNote:"Az idegen nyelvű hírek ellenőrzött magyar összefoglalókból készülnek. Az új fordítások fokozatosan jelennek meg."
},
en:{
 tag:"International news · Editorial pilot",eye:"World view",
 hero:"World news, from more than one country's perspective.",
 lead:"Select countries and topics. Only reviewed news summaries with source attribution are published.",
 globeEye:"OrbisActa · World map",globeTitle:"Explore news around the world.",
 globeLead:"Rotate the globe, choose a country, and read available English news summaries.",
 globeCount:"verified summaries in the system",globeReady:"Choose a country to explore.",
 globeHelp:"Drag to rotate · Pinch or use +/− to zoom",
 globeSource:"Map data: Natural Earth (public domain). Markers are indicative, not official borders.",
 europe:"Europe",america:"Americas",asia:"Asia",allNews:"All news",
 filtersTitle:"Countries and topics",viewResults:"View news",countriesShort:"countries",countryLabel:"Countries",africa:"Africa",oceania:"Oceania",zoomIn:"Zoom in",zoomOut:"Zoom out",topicLabel:"Topic",
 sort:"Sort by",latest:"Newest first",importance:"Most important first",
 footer:"OrbisActa · Editorial pilot. AI-generated summaries do not replace original reporting or human editorial verification.",
 allCountries:"All countries",allTopics:"All",topics:{politika:"Politics",gazdaság:"Economy",tudomány:"Science",sport:"Sports",kultúra:"Culture",egyéb:"Other"},
 count:"verified stories",filtered:"after filtering",emptyTitle:"No translated stories for this selection yet.",
 emptyText:"Try another country or topic. More verified translations will become available over time.",
 credit:"AI-translated, source-attributed summary",sourceLink:"Read original article and attribution",backgroundTitle:"Terms explained",
 updated:"Updated",loadError:"News data is not yet available.",
 world:"World",eu:"European Union",global:"Global news",
 globeAll:"All regions selected – click a marker to filter.",
 globeFiltered:"selected regions",globeStory:"published stories",mapError:"The globe could not load. Country buttons still work.",
 mapLinesError:"Map outlines could not be loaded; country markers remain available.",
 chooseCountry:"select news from",showGlobe:"Show interactive globe",hideGlobe:"Hide globe",featured:"Recommended · fresh and relevant",language:"Language",translationNote:"English content is translated from verified Hungarian summaries. New translations appear gradually."
},
es:{
 tag:"Noticias internacionales · Proyecto editorial",eye:"Visión global",
 hero:"Noticias del mundo desde distintas perspectivas.",
 lead:"Elige países y temas. Solo publicamos resúmenes revisados con atribución de las fuentes.",
 globeEye:"OrbisActa · Mapa mundial",globeTitle:"Explora las noticias del mundo.",
 globeLead:"Gira el globo, elige un país y lee los resúmenes disponibles en español.",
 globeCount:"noticias verificadas en el sistema",globeReady:"Selecciona un país para explorar.",
 globeHelp:"Arrastra para girar · Pellizca o usa +/− para ampliar",
 globeSource:"Datos cartográficos: Natural Earth (dominio público). Los marcadores son orientativos.",
 europe:"Europa",america:"América",asia:"Asia",allNews:"Todas las noticias",
 filtersTitle:"Países y temas",viewResults:"Ver noticias",countriesShort:"países",countryLabel:"Países",africa:"África",oceania:"Oceanía",zoomIn:"Acercar",zoomOut:"Alejar",topicLabel:"Tema",
 sort:"Ordenar",latest:"Más recientes",importance:"Más importantes",
 footer:"OrbisActa · Proyecto editorial. Los resúmenes con IA no sustituyen las fuentes originales ni la revisión humana.",
 allCountries:"Todos los países",allTopics:"Todos",topics:{politika:"Política",gazdaság:"Economía",tudomány:"Ciencia",sport:"Deportes",kultúra:"Cultura",egyéb:"Otros"},
 count:"noticias verificadas",filtered:"tras filtrar",emptyTitle:"Todavía no hay noticias traducidas para esta selección.",
 emptyText:"Prueba otro país o tema. Las traducciones disponibles aumentarán progresivamente.",
 credit:"Resumen traducido con IA y atribución",sourceLink:"Noticia original y fuente",backgroundTitle:"Conceptos explicados",
 updated:"Actualizado",loadError:"Aún no hay datos de noticias disponibles.",
 world:"Mundo",eu:"Unión Europea",global:"Noticias del mundo",
 globeAll:"Todas las regiones seleccionadas. Elige un marcador para filtrar.",
 globeFiltered:"regiones seleccionadas",globeStory:"noticias publicadas",mapError:"No se pudo cargar el globo. Los botones de países funcionan.",
 mapLinesError:"No se cargaron los contornos; los marcadores siguen disponibles.",
 chooseCountry:"seleccionar noticias de",showGlobe:"Mostrar globo interactivo",hideGlobe:"Ocultar globo",featured:"Recomendadas · recientes y relevantes",language:"Idioma",translationNote:"Las noticias en español se traducen a partir de resúmenes húngaros verificados."
},
fr:{
 tag:"Actualités internationales · Projet éditorial",eye:"Regards sur le monde",
 hero:"L'actualité mondiale, vue de plusieurs pays.",
 lead:"Choisissez les pays et les thèmes. Seuls des résumés vérifiés et sourcés sont publiés.",
 globeEye:"OrbisActa · Carte du monde",globeTitle:"Explorez l'actualité sur le globe.",
 globeLead:"Faites tourner le globe, choisissez un pays et lisez les résumés disponibles en français.",
 globeCount:"articles vérifiés dans le système",globeReady:"Sélectionnez un pays.",
 globeHelp:"Glissez pour tourner · Pincez ou utilisez +/− pour zoomer",
 globeSource:"Données cartographiques : Natural Earth (domaine public). Les repères sont indicatifs.",
 europe:"Europe",america:"Amériques",asia:"Asie",allNews:"Toute l'actualité",
 filtersTitle:"Pays et thèmes",viewResults:"Voir les articles",countriesShort:"pays",countryLabel:"Pays",africa:"Afrique",oceania:"Océanie",zoomIn:"Zoom avant",zoomOut:"Zoom arrière",topicLabel:"Thème",
 sort:"Trier par",latest:"Plus récents",importance:"Plus importants",
 footer:"OrbisActa · Projet éditorial. Les résumés générés par IA ne remplacent ni les sources originales ni la vérification humaine.",
 allCountries:"Tous les pays",allTopics:"Tous",topics:{politika:"Politique",gazdaság:"Économie",tudomány:"Sciences",sport:"Sport",kultúra:"Culture",egyéb:"Autres"},
 count:"articles vérifiés",filtered:"après filtrage",emptyTitle:"Aucun article traduit pour cette sélection.",
 emptyText:"Essayez un autre pays ou thème. De nouvelles traductions arrivent progressivement.",
 credit:"Résumé traduit par IA et attribué",sourceLink:"Article original et source",backgroundTitle:"Termes expliqués",
 updated:"Mis à jour",loadError:"Les données ne sont pas encore disponibles.",
 world:"Monde",eu:"Union européenne",global:"Actualités mondiales",
 globeAll:"Toutes les régions sélectionnées – cliquez sur un repère pour filtrer.",
 globeFiltered:"régions sélectionnées",globeStory:"articles publiés",mapError:"Le globe ne s'est pas chargé. Les filtres de pays restent disponibles.",
 mapLinesError:"Les contours ne sont pas disponibles ; les repères fonctionnent.",
 chooseCountry:"sélectionner les nouvelles de",showGlobe:"Afficher le globe",hideGlobe:"Masquer le globe",featured:"À la une · récentes et importantes",language:"Langue",translationNote:"Les résumés français proviennent de contenus hongrois vérifiés. Les traductions arrivent progressivement."
},
de:{
 tag:"Internationale Nachrichten · Redaktionspilot",eye:"Weltblick",
 hero:"Weltnachrichten aus unterschiedlichen Perspektiven.",
 lead:"Wählen Sie Länder und Themen. Wir veröffentlichen nur geprüfte Zusammenfassungen mit Quellenangabe.",
 globeEye:"OrbisActa · Weltkarte",globeTitle:"Nachrichten auf der Weltkarte entdecken.",
 globeLead:"Drehen Sie die Erde, wählen Sie ein Land und lesen Sie verfügbare deutsche Zusammenfassungen.",
 globeCount:"geprüfte Nachrichten im System",globeReady:"Wählen Sie ein Land aus.",
 globeHelp:"Zum Drehen ziehen · Zum Zoomen zwei Finger oder +/− verwenden",
 globeSource:"Kartendaten: Natural Earth (gemeinfrei). Markierungen dienen der Orientierung.",
 europe:"Europa",america:"Amerika",asia:"Asien",allNews:"Alle Nachrichten",
 filtersTitle:"Länder und Themen",viewResults:"Nachrichten ansehen",countriesShort:"Länder",countryLabel:"Länder",africa:"Afrika",oceania:"Ozeanien",zoomIn:"Vergrößern",zoomOut:"Verkleinern",topicLabel:"Thema",
 sort:"Sortierung",latest:"Neueste zuerst",importance:"Wichtigste zuerst",
 footer:"OrbisActa · Redaktionspilot. KI-Zusammenfassungen ersetzen weder Originalquellen noch menschliche Prüfung.",
 allCountries:"Alle Länder",allTopics:"Alle",topics:{politika:"Politik",gazdaság:"Wirtschaft",tudomány:"Wissenschaft",sport:"Sport",kultúra:"Kultur",egyéb:"Sonstiges"},
 count:"geprüfte Nachrichten",filtered:"nach Filterung",emptyTitle:"Für diese Auswahl gibt es noch keine übersetzten Meldungen.",
 emptyText:"Wählen Sie ein anderes Land oder Thema. Weitere Übersetzungen folgen schrittweise.",
 credit:"KI-übersetzte Zusammenfassung mit Quelle",sourceLink:"Originalmeldung und Quelle",backgroundTitle:"Begriffe erklärt",
 updated:"Aktualisiert",loadError:"Die Nachrichtendaten sind noch nicht verfügbar.",
 world:"Welt",eu:"Europäische Union",global:"Weltnachrichten",
 globeAll:"Alle Regionen ausgewählt – zum Filtern eine Markierung anklicken.",
 globeFiltered:"ausgewählte Regionen",globeStory:"veröffentlichte Meldungen",mapError:"Die Weltkarte konnte nicht geladen werden. Länderfilter funktionieren weiter.",
 mapLinesError:"Kartengrenzen konnten nicht geladen werden; Markierungen sind verfügbar.",
 chooseCountry:"Nachrichten auswählen aus",showGlobe:"Globus anzeigen",hideGlobe:"Globus ausblenden",featured:"Empfohlen · aktuell und wichtig",language:"Sprache",translationNote:"Deutsche Meldungen werden aus geprüften ungarischen Zusammenfassungen übersetzt."
},
pt:{
 tag:"Notícias internacionais · Projeto editorial",eye:"Visão do mundo",
 hero:"Notícias do mundo, de diferentes perspectivas.",
 lead:"Escolha países e temas. Publicamos apenas resumos verificados com atribuição das fontes.",
 globeEye:"OrbisActa · Mapa-múndi",globeTitle:"Explore notícias pelo mundo.",
 globeLead:"Gire o globo, escolha um país e leia os resumos disponíveis em português.",
 globeCount:"notícias verificadas no sistema",globeReady:"Selecione um país.",
 globeHelp:"Arraste para girar · Aproxime com dois dedos ou use +/−",
 globeSource:"Dados cartográficos: Natural Earth (domínio público). Marcadores são indicativos.",
 europe:"Europa",america:"Américas",asia:"Ásia",allNews:"Todas as notícias",
 filtersTitle:"Países e temas",viewResults:"Ver notícias",countriesShort:"países",countryLabel:"Países",africa:"África",oceania:"Oceania",zoomIn:"Ampliar",zoomOut:"Reduzir",topicLabel:"Tema",
 sort:"Ordenar",latest:"Mais recentes",importance:"Mais importantes",
 footer:"OrbisActa · Projeto editorial. Resumos gerados por IA não substituem as fontes originais nem a revisão humana.",
 allCountries:"Todos os países",allTopics:"Todos",topics:{politika:"Política",gazdaság:"Economia",tudomány:"Ciência",sport:"Esportes",kultúra:"Cultura",egyéb:"Outros"},
 count:"notícias verificadas",filtered:"após filtro",emptyTitle:"Ainda não há notícias traduzidas para esta seleção.",
 emptyText:"Escolha outro país ou tema. Novas traduções serão disponibilizadas gradualmente.",
 credit:"Resumo traduzido com IA e fonte atribuída",sourceLink:"Notícia original e fonte",backgroundTitle:"Termos explicados",
 updated:"Atualizado",loadError:"Os dados de notícias ainda não estão disponíveis.",
 world:"Mundo",eu:"União Europeia",global:"Notícias do mundo",
 globeAll:"Todas as regiões selecionadas – clique em um marcador para filtrar.",
 globeFiltered:"regiões selecionadas",globeStory:"notícias publicadas",mapError:"O globo não pôde ser carregado. Os filtros por país seguem funcionando.",
 mapLinesError:"Os contornos do mapa não foram carregados; os marcadores seguem disponíveis.",
 chooseCountry:"selecionar notícias de",showGlobe:"Mostrar globo interativo",hideGlobe:"Ocultar globo",featured:"Em destaque · recentes e importantes",language:"Idioma",translationNote:"Os textos em português são traduzidos a partir de resumos húngaros verificados."
}
};
const fallbackCountries={HU:"Magyarország",DE:"Németország",FR:"Franciaország",IT:"Olaszország",JP:"Japán",BR:"Brazília",IN:"India",CN:"Kína",AU:"Ausztrália",SA:"Szaúd-Arábia",NG:"Nigéria",ZA:"Dél-Afrika",US:"Egyesült Államok",GB:"Egyesült Királyság"};
function supported(candidate){return Object.prototype.hasOwnProperty.call(locales,candidate)}
function normalize(language){const code=String(language||"").toLowerCase().split("-")[0];return supported(code)?code:null}
function preferred(){
 try{const stored=normalize(localStorage.getItem("orbisacta_language"));if(stored)return stored}catch(e){}
 for(const value of navigator.languages||[navigator.language]){const code=normalize(value);if(code)return code}
 return "en";
}
function choose(explicit){const lang=normalize(explicit)||preferred();return lang}
function remember(lang){if(!supported(lang))return;try{localStorage.setItem("orbisacta_language",lang)}catch(e){}}
function t(lang,key){return (locales[lang]||locales.en)[key]||locales.en[key]||key}
function name(lang,code){
 if(code==="WORLD")return t(lang,"world");
 if(code==="EU")return t(lang,"eu");
 try{
  const country=new Intl.DisplayNames([lang==="pt"?"pt-BR":lang],{type:"region"}).of(code);
  if(country&&country!==code)return country;
 }catch(e){}
 return fallbackCountries[code]||code;
}
function apply(lang){
 document.documentElement.lang=lang;
 const dictionary={
 "header small":"tag",".eyebrow":"eye","main h1":"hero","main .lead":"lead",
 ".globe-eyebrow":"globeEye",".globe-side h2":"globeTitle",
 ".globe-desc":"globeLead",".globe-total-label":"globeCount",
 ".globe-map-note":"globeHelp",".globe-source-note":"globeSource",
 '[data-globe-focus="europe"]':"europe",'[data-globe-focus="america"]':"america",
 '[data-globe-focus="asia"]':"asia",'[data-globe-focus="africa"]':"africa",'[data-globe-focus="oceania"]':"oceania","#globe-reset":"allNews",
 ".filters .group-label:first-child":"countryLabel",
 ".sort-controls label":"sort",'#sort option[value="latest"]':"latest",
 '#sort option[value="importance"]':"importance",'#sort option[value="featured"]':"featured","footer":"footer"
 };
 for(const [selector,key] of Object.entries(dictionary)){
  const element=document.querySelector(selector);
  if(element)element.textContent=t(lang,key);
 }
 const groups=document.querySelectorAll(".filters .group-label");
 if(groups[0])groups[0].textContent=t(lang,"countryLabel");
 if(groups[1])groups[1].textContent=t(lang,"topicLabel");
 const picker=document.getElementById("language");
 if(picker){
  const chosen=picker.querySelector('.language-option[data-language="'+lang+'"]');
  if(chosen){
   const flag=picker.querySelector("#current-language-flag");
   const label=picker.querySelector("#current-language-name");
   const value=chosen.querySelector(".language-label").textContent;
   flag.src=chosen.querySelector("img").getAttribute("src");
   label.textContent=value;
   picker.querySelector("summary").setAttribute("aria-label",t(lang,"language")+": "+value);
  }
  picker.querySelectorAll(".language-option").forEach(link=>{
   if(link.dataset.language===lang)link.setAttribute("aria-current","page");
   else link.removeAttribute("aria-current");
  });
 }
 document.querySelectorAll("[data-globe-zoom]").forEach(button=>{
  button.setAttribute("aria-label",t(lang,button.dataset.globeZoom==="in"?"zoomIn":"zoomOut"));
  button.title=t(lang,button.dataset.globeZoom==="in"?"zoomIn":"zoomOut");
 });
 const toggle=document.getElementById("globe-toggle");if(toggle){const label=toggle.querySelector("span");if(label)label.textContent=t(lang,"showGlobe")}
 const note=document.getElementById("translation-note");
 if(note)note.textContent=t(lang,"translationNote");
 document.title="OrbisActa · "+t(lang,"tag");
}
window.OrbisI18n={locales,choose,remember,t,name,apply};
})();
