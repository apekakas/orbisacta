/* OrbisActa editorial coverage dashboard.
 * Aggregated public data only. Lazy-loaded on first opening, no tracking.
 */
(function(){
"use strict";
const panel=document.getElementById("quality-panel");
if(!panel||!window.OrbisI18n)return;
const i18n=window.OrbisI18n;
const lang=i18n.choose(window.ORBIS_PAGE_LANG);
const t=key=>i18n.t(lang,key);
const format=new Intl.NumberFormat(lang==="pt"?"pt-BR":lang);
function elem(tag,value,cls){
 const el=document.createElement(tag);
 if(value!==null&&value!==undefined)el.textContent=String(value);
 if(cls)el.className=cls;
 return el;
}
function set(id,text){const target=document.getElementById(id);if(target)target.textContent=text}
set("quality-heading",t("qualityTitle"));
set("quality-subtitle",t("qualityHint"));
set("quality-country-title",t("qualityCountry"));
set("quality-topic-title",t("qualityTopic"));
set("quality-method",t("qualityMethod"));
function metric(container,label,value){
 const box=elem("div",null,"quality-metric");
 box.append(elem("span",label),elem("strong",format.format(value)));
 container.append(box);
}
function table(container,columns,records){
 const table=elem("table",null,"quality-table");
 const thead=elem("thead"),tr=elem("tr");
 for(const label of columns){
  const th=elem("th",label);th.scope="col";tr.append(th);
 }
 thead.append(tr);table.append(thead);
 const tbody=elem("tbody");
 for(const row of records){
  const line=elem("tr");
  if(!row.published)line.className="quality-empty-row";
  const cols=[
   row.display_name,
   format.format(row.published),
   format.format(row.two_numeric_facts),
   format.format(row.with_explainer),
   format.format(row.distinct_publishers),
   row.published>=3&&row.largest_publisher_share_pct!==null?
    format.format(row.largest_publisher_share_pct)+"%":"—"
  ];
  cols.forEach((value,index)=>{
   const cell=elem(index===0?"th":"td",value);
   if(index===0)cell.scope="row";
   else cell.className="quality-number";
   line.append(cell);
  });
  tbody.append(line);
 }
 table.append(tbody);
 const scroll=elem("div",null,"quality-table-scroll");
 scroll.tabIndex=0;
 scroll.append(table);
 container.replaceChildren(scroll);
}
function render(report){
 if(!report||!report.total||!report.countries||!report.topics||
    !report.archive||report.archive.days!==7){
  throw new Error("Invalid editorial quality report");
 }
 const summary=document.getElementById("quality-stats");
 summary.replaceChildren();
 for(const [key,val] of [
  ["qualityCount",report.total.published],
  ["qualityNumbers",report.total.two_numeric_facts],
  ["qualityExplain",report.total.with_explainer],
  ["qualityPublishers",report.total.distinct_publishers]
 ])metric(summary,t(key),val);
 const columns=[
  t("qualityCountryCol"),t("qualityCount"),t("qualityNumbers"),
  t("qualityExplain"),t("qualityPublishers"),t("qualityTopSource")
 ];
 const collation=new Intl.Collator(lang==="pt"?"pt-BR":lang,{sensitivity:"base"});
 const countries=Object.entries(report.countries).map(([code,item])=>({
  ...item,display_name:i18n.name(lang,code)
 })).sort((a,b)=>b.published-a.published||collation.compare(a.display_name,b.display_name));
 const topics=Object.entries(report.topics).map(([code,item])=>({
  ...item,display_name:(t("topics")||{})[code]||code
 })).sort((a,b)=>b.published-a.published||collation.compare(a.display_name,b.display_name));
 // Editorial attention items are based on observed coverage, not predictions.
 const attention=document.getElementById("quality-attention");
 attention.replaceChildren();
 const brief=names=>names.slice(0,7).join(", ")+(names.length>7?" (+"+(names.length-7)+")":"");
 const attentionLine=(key,names)=>{
  if(!names.length)return;
  const p=elem("p");
  p.append(elem("strong",t(key)+": "),document.createTextNode(brief(names)));
  attention.append(p);
 };
 attentionLine("qualityNoCountry",countries.filter(item=>item.published===0).map(item=>item.display_name));
 attentionLine("qualityOnlyOne",countries.filter(item=>item.published>=3&&item.distinct_publishers===1).map(item=>item.display_name));
 attentionLine("qualityNoTopic",topics.filter(item=>item.published===0).map(item=>item.display_name));
 if(!attention.childElementCount)attention.append(elem("p",t("qualityNoGaps")));
 table(document.getElementById("quality-country-table"),columns,countries);
 table(document.getElementById("quality-topic-table"),
       [t("qualityTopicCol"),...columns.slice(1)],topics);
 set("quality-date",t("qualityPeriod")+": "+
  report.archive.start_date+" – "+report.archive.end_date+
  " · "+report.archive.timezone);
 set("quality-loading",report.total.published===0?t("qualityNoNews"):"");
}
let loaded=false;
panel.addEventListener("toggle",async()=>{
 if(!panel.open||loaded)return;
 loaded=true;
 set("quality-loading",t("qualityLoading"));
 try{
  const response=await fetch("./quality.json",{cache:"no-store"});
  if(!response.ok)throw new Error("Quality report unavailable");
  const report=await response.json();
  render(report);
 }catch(error){
  loaded=false;
  set("quality-loading",t("qualityError"));
 }
});
})();