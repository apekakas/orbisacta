/* OrbisActa globe — country selection on an orthographic Natural Earth map.
   Globe renderer: d3 7.9.0 (ISC), terrain: Natural Earth 1:110m (public domain).
   Privacy: no external tiles, scripts, or tracking; all assets served locally. */
(function(){
"use strict";
const NS="http://www.w3.org/2000/svg";
const locations={
 HU:{name:"Magyarország",coord:[19.04,47.5]},
 DE:{name:"Németország",coord:[10.4,51.1]},
 FR:{name:"Franciaország",coord:[2.35,46.6]},
 IT:{name:"Olaszország",coord:[12.5,42.8]},
 JP:{name:"Japán",coord:[138.1,36.3]},
 BR:{name:"Brazília",coord:[-51.9,-14.3]},
 US:{name:"Egyesült Államok",coord:[-98.5,39.8]},
 GB:{name:"Egyesült Királyság",coord:[-2.4,54.1]},
 EU:{name:"Európai Unió",coord:[4.35,50.85]}
};
const viewpoints={europe:[12,47],america:[-78,15],asia:[120,28]};
function svgNode(tag,attrs){
 const el=document.createElementNS(NS,tag);
 Object.entries(attrs||{}).forEach(([k,v])=>el.setAttribute(k,v));
 return el;
}
function put(parent,tag,attrs){const e=svgNode(tag,attrs);parent.append(e);return e}
function mount(options){
 const svg=document.getElementById("globe-map");
 const stage=document.getElementById("globe-stage");
 const note=document.getElementById("globe-selection");
 const total=document.getElementById("globe-total");
 if(!svg||!stage)return null;
 if(!window.d3||!window.d3.geoOrthographic){
   stage.setAttribute("data-globe-unavailable","true");
   if(note)note.textContent="A földgömb betöltése nem sikerült. Az országválasztó gombokkal továbbra is böngészhetsz.";
   return {update:()=>{},focus:()=>{}};
 }
 const d3=window.d3;
 let center=[12,47],scale=192,land=null,items=[],active=new Set();
 const projection=d3.geoOrthographic().scale(scale).translate([360,218]).rotate([-center[0],-center[1]]).clipAngle(90).precision(0.75);
 const path=d3.geoPath(projection);
 const sphere={type:"Sphere"};
 const grid=d3.geoGraticule().step([20,20])();
 svg.replaceChildren();
 const defs=put(svg,"defs");
 const grad=put(defs,"radialGradient",{id:"oa-ocean",cx:"36%",cy:"28%",r:"78%"});
 put(grad,"stop",{offset:"0%","stop-color":"#1e6171"});
 put(grad,"stop",{offset:"65%","stop-color":"#164152"});
 put(grad,"stop",{offset:"100%","stop-color":"#0b263c"});
 const glow=put(svg,"circle",{cx:360,cy:219,r:209,fill:"#1cb7a4",opacity:".07"});
 const sea=put(svg,"path",{fill:"url(#oa-ocean)",stroke:"#508798","stroke-width":"1.4"});
 const graticule=put(svg,"path",{fill:"none",stroke:"#8cbac2","stroke-opacity":".19","stroke-width":".8"});
 const landPath=put(svg,"path",{fill:"#7fc1b2",stroke:"#b4ded1","stroke-width":".7","stroke-opacity":".48","fill-opacity":".96"});
 const border=put(svg,"path",{fill:"none",stroke:"#b2d7dc","stroke-opacity":".48","stroke-width":"1"});
 const pins=put(svg,"g",{class:"globe-pins"});
 const markerNodes={};
 for(const [code,loc] of Object.entries(locations)){
   const group=put(pins,"g",{class:"globe-pin",role:"button",tabindex:"0","aria-label":loc.name+" híreinek kiválasztása"});
   const halo=put(group,"circle",{r:13,fill:"#1cd5bc",opacity:".16"});
   const dot=put(group,"circle",{r:5.8,fill:"#f7fffd",stroke:"#005b60","stroke-width":"2"});
   const title=put(group,"title");title.textContent=loc.name;
   const tag=put(group,"text",{x:12,y:-10,"font-size":"13","font-weight":"700",fill:"#ffffff",stroke:"#0b2837","stroke-width":"3","paint-order":"stroke"});
   tag.textContent=loc.name;
   group.addEventListener("click",ev=>{ev.stopPropagation();focus(loc.coord);if(options.onCountry)options.onCountry(code)});
   group.addEventListener("keydown",ev=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();focus(loc.coord);if(options.onCountry)options.onCountry(code)}});
   markerNodes[code]={group,halo,dot,tag};
 }
 function redraw(){
   projection.rotate([-center[0],-center[1]]).scale(scale);
   const earth=path(sphere);
   sea.setAttribute("d",earth);graticule.setAttribute("d",path(grid));
   landPath.setAttribute("d",land?path(land):"");
   border.setAttribute("d",earth);
   glow.setAttribute("r",scale+17);
   for(const [code,loc] of Object.entries(locations)){
     const d=markerNodes[code],visible=d3.geoDistance(loc.coord,center)<Math.PI/2-.025;
     d.group.style.display=visible?"":"none";
     if(!visible)continue;
     const pos=projection(loc.coord);
     d.group.setAttribute("transform","translate("+pos[0]+","+pos[1]+")");
     const highlighted=active.size===1&&active.has(code);
     const isIncluded=active.has(code);
     d.dot.setAttribute("fill",highlighted?"#ffe7aa":isIncluded?"#f7fffd":"#a0b7bd");
     d.halo.setAttribute("opacity",highlighted?".55":".19");
     d.halo.setAttribute("r",highlighted?16:13);
     d.tag.style.display=highlighted?"":"none";
   }
 }
 function focus(next){
   center=[((next[0]+180)%360+360)%360-180,Math.max(-75,Math.min(75,next[1]))];
   redraw();
 }
 function update(articles,selected){
   items=articles||[];active=new Set(selected||[]);
   if(total)total.textContent=String(items.length);
   if(note){
     if(active.size===Object.keys(locations).length+1){
       note.textContent="Minden ország és világkitekintés – kattints egy ország jelölőjére a szűréshez.";
     }else if(active.size===1){
       const code=Array.from(active)[0];
       const count=items.filter(a=>a.country===code).length;
       note.textContent=(locations[code]?locations[code].name:code==="WORLD"?"Világhírek":code)+": "+count+" publikált hír.";
     }else{
       note.textContent=active.size+" kiválasztott földrajzi nézet – a gombokkal tovább szűrhetsz.";
     }
   }
   redraw();
 }
 let dragging=null;
 svg.addEventListener("pointerdown",ev=>{
   if(ev.button!==0||ev.target.closest(".globe-pin"))return;
   dragging={id:ev.pointerId,x:ev.clientX,y:ev.clientY,lon:center[0],lat:center[1]};
   svg.setPointerCapture(ev.pointerId);
   svg.classList.add("dragging");
 });
 svg.addEventListener("pointermove",ev=>{
   if(!dragging||ev.pointerId!==dragging.id)return;
   const ratio=720/Math.max(svg.getBoundingClientRect().width,1);
   center=[dragging.lon+(dragging.x-ev.clientX)*ratio*.3,Math.max(-75,Math.min(75,dragging.lat+(ev.clientY-dragging.y)*ratio*.3))];
   redraw();
 });
 function stop(ev){if(!dragging||ev.pointerId!==dragging.id)return;dragging=null;svg.classList.remove("dragging");}
 svg.addEventListener("pointerup",stop);svg.addEventListener("pointercancel",stop);
 svg.addEventListener("wheel",ev=>{
   ev.preventDefault();scale=Math.max(135,Math.min(232,scale+(ev.deltaY<0?12:-12)));redraw();
 },{passive:false});
 svg.setAttribute("tabindex","0");
 svg.addEventListener("keydown",ev=>{
   const delta={ArrowLeft:[-15,0],ArrowRight:[15,0],ArrowUp:[0,12],ArrowDown:[0,-12]}[ev.key];
   if(!delta)return;ev.preventDefault();focus([center[0]+delta[0],center[1]+delta[1]]);
 });
 document.querySelectorAll("[data-globe-focus]").forEach(el=>{
   el.addEventListener("click",()=>focus(viewpoints[el.dataset.globeFocus]));
 });
 const reset=document.getElementById("globe-reset");
 if(reset)reset.addEventListener("click",()=>{if(options.onReset)options.onReset();focus(viewpoints.europe)});
 redraw();
 fetch("./assets/earth-land.geojson",{cache:"force-cache"})
   .then(r=>{if(!r.ok)throw Error("Land data HTTP "+r.status);return r.json()})
   .then(data=>{if(data&&data.type==="FeatureCollection"){land=data;redraw()}})
   .catch(()=>{if(note)note.textContent="A térképvonalak nem töltődtek be, az országjelölők használhatók.";});
 return {update,focus};
}
window.OrbisGlobe={mount};
})();
