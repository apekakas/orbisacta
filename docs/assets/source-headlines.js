/* OrbisActa secondary, clearly labelled linked source-headline stream.
 * No auto-summaries, no generated translations, no extra API calls.
 */
(function(){
  "use strict";
  const container=document.getElementById("source-headlines");
  if(!container)return;
  const lang=window.ORBIS_PAGE_LANG||"hu";
  const labels={
    hu:["További friss hírek a forrásokból","Eredeti nyelvű címek, közvetlen forráshivatkozással. Ezekhez még nincs ellenőrzött, ötmondatos összefoglaló.","Megnyitás a forrásnál","Forráscímek betöltése…","Nincs további friss forráshír."],
    en:["More recent stories from sources","Original-language headlines and direct source links. These are not verified five-sentence briefs.","Read at source","Loading source headlines…","No additional recent stories."],
    de:["Weitere aktuelle Meldungen aus den Quellen","Originalsprachige Schlagzeilen mit direkten Quellenlinks, noch ohne überprüfte Zusammenfassung.","Originalquelle öffnen","Quellenmeldungen werden geladen…","Keine weiteren aktuellen Meldungen."],
    fr:["Autres actualités des sources","Titres dans leur langue d'origine avec lien direct. Il ne s'agit pas de résumés vérifiés.","Lire à la source","Chargement des titres…","Pas d'autres actualités récentes."],
    es:["Más noticias recientes de las fuentes","Titulares en idioma original con enlace directo. Aún no son resúmenes verificados.","Leer en la fuente","Cargando titulares…","No hay más noticias recientes."],
    pt:["Mais notícias recentes das fontes","Títulos no idioma original e ligações para a fonte. Ainda não são resumos verificados.","Ler na fonte","A carregar títulos…","Não há mais notícias recentes."]
  }[lang]||[];
  const title=document.createElement("summary");
  title.textContent=labels[0];
  const explanatory=document.createElement("p");
  explanatory.textContent=labels[1];
  const status=document.createElement("p");
  status.setAttribute("role","status");
  status.textContent=labels[3];
  const list=document.createElement("ul");
  list.className="source-headline-list";
  container.append(title,explanatory,status,list);
  function timeLabel(value){
    const date=new Date(value);
    if(!Number.isFinite(date.getTime()))return "";
    return date.toLocaleDateString(lang==="pt"?"pt-BR":lang,{year:"numeric",month:"short",day:"numeric"});
  }
  fetch("./headlines.json",{cache:"no-store"}).then(response=>{
    if(!response.ok)throw Error("not available");
    return response.json();
  }).then(payload=>{
    if(!payload||payload.type!=="unverified_source_headlines"||!Array.isArray(payload.articles)){
      throw Error("invalid data");
    }
    const items=payload.articles.slice(0,120);
    list.replaceChildren();
    for(const story of items){
      const value=String(story.url||"");
      let u;
      try{u=new URL(value)}catch(_){continue}
      if(!["https:","http:"].includes(u.protocol))continue;
      const li=document.createElement("li");
      const link=document.createElement("a");
      link.href=u.href;link.rel="noopener noreferrer";link.target="_blank";
      link.textContent=String(story.title_original||"");
      const meta=document.createElement("span");
      meta.className="source-headline-meta";
      meta.textContent=[story.source_name,timeLabel(story.published_utc),labels[2]]
        .filter(Boolean).join(" · ");
      li.append(link,meta);list.append(li);
    }
    status.textContent=list.children.length?"":labels[4];
    title.textContent=labels[0]+" ("+list.children.length+")";
  }).catch(()=>{status.textContent=labels[4];});
})();