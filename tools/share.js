(function(){
var SITE='https://zinezine.online/',enc=encodeURIComponent;

function wrap(c,t,maxW,maxL){var w=t.split(/\s+/),ls=[],l='';for(var i=0;i<w.length;i++){var x=l?l+' '+w[i]:w[i];if(c.measureText(x).width>maxW&&l){ls.push(l);l=w[i];}else{l=x;}}if(l)ls.push(l);if(ls.length>maxL){ls=ls.slice(0,maxL);ls[maxL-1]=ls[maxL-1].replace(/\s*\S*$/,'')+'…';}return ls;}
function loadImg(src){return new Promise(function(ok){if(!src){ok(null);return;}var im=new Image();im.crossOrigin='anonymous';im.onload=function(){ok(im);};im.onerror=function(){ok(null);};im.src=src;});}
function makeCard(a,W,H){
  var h=a.querySelector('h1'),title=h.textContent.trim(),lb=a.querySelector('.post-head .lbl'),label=lb?lb.textContent.replace(/\s+/g,' ').trim():'zinezine';
  var fi=a.querySelector('figure.ph img'),src=fi?(fi.currentSrc||fi.src):'';
  var fonts=document.fonts&&document.fonts.load?Promise.all([document.fonts.load('64px "Archivo Black"'),document.fonts.load('32px "Special Elite"')]).catch(function(){}):Promise.resolve();
  return Promise.all([loadImg(src),fonts]).then(function(r){
    var im=r[0],cv=document.createElement('canvas');cv.width=W;cv.height=H;var c=cv.getContext('2d');
    c.fillStyle='#15161C';c.fillRect(0,0,W,H);
    var pad=64,top=W===1080&&H===1920?200:0,ph=H===1920?980:620;
    if(im){var y0=top,sc=Math.max(W/im.width,ph/im.height),sw=W/sc,sh=ph/sc;c.drawImage(im,(im.width-sw)/2,(im.height-sh)/2,sw,sh,0,y0,W,ph);}
    else{c.fillStyle='#FF3D7F';c.fillRect(0,top,W,ph);}
    var y=top+ph+(H===1920?70:56);
    c.textBaseline='top';c.font='32px "Special Elite","Courier New",monospace';
    var lw=Math.min(c.measureText(label.toUpperCase()).width+36,W-2*pad);
    c.fillStyle='#FF3D7F';c.fillRect(pad,y,lw,54);c.fillStyle='#15161C';c.fillText(label.toUpperCase(),pad+18,y+9,lw-36);
    y+=54+34;
    var fs=H===1920?72:60;c.font=fs+'px "Archivo Black","Arial Black",Impact,sans-serif';c.fillStyle='#EEEEE6';
    var ls=wrap(c,title,W-2*pad,H===1920?6:4);
    for(var i=0;i<ls.length;i++){c.fillText(ls[i],pad,y+i*(fs*1.18));}
    c.font='40px "Special Elite","Courier New",monospace';c.fillStyle='#FF5C93';c.textBaseline='alphabetic';
    c.fillText('zinezine.online',pad,H-(H===1920?150:56));
    return new Promise(function(ok){cv.toBlob(function(b){ok(b);},'image/png');});
  });
}
function build(a){
  var id=a.id;
  if(!/^(a|dd|e)-/.test(id)||a.querySelector('.share'))return;
  var h=a.querySelector('h1');if(!h)return;
  var title=h.textContent.trim(),url=SITE+id+'/';
  var box=document.createElement('div');box.className='share';
  var lbl=document.createElement('span');lbl.className='lbl';lbl.textContent='Bagikan artikel ini';box.appendChild(lbl);
  function link(t,href){var x=document.createElement('a');x.className='btn alt';x.textContent=t;x.href=href;x.target='_blank';x.rel='noopener';box.appendChild(x);}
  function btn(t,fn,cls){var b=document.createElement('button');b.type='button';b.className=cls||'btn alt';b.textContent=t;b.addEventListener('click',function(){fn(b);});box.appendChild(b);return b;}
  if(navigator.share){btn('Bagikan\u2026',function(){navigator.share({title:title,url:url}).catch(function(){});},'btn');}
  link('WhatsApp','https://wa.me/?text='+enc(title+' '+url));
  link('Telegram','https://t.me/share/url?url='+enc(url)+'&text='+enc(title));
  link('X','https://twitter.com/intent/tweet?text='+enc(title)+'&url='+enc(url));
  link('Facebook','https://www.facebook.com/sharer/sharer.php?u='+enc(url));
  var note=document.createElement('p');note.className='share-note';note.hidden=true;
  function ig(kind,W,H){btn('IG '+kind,function(b){
    var o=b.textContent;b.textContent='Membuat gambar…';b.disabled=true;
    makeCard(a,W,H).then(function(blob){
      b.textContent=o;b.disabled=false;if(!blob)return;
      var f=new File([blob],'zinezine-'+id+'-'+kind.toLowerCase()+'.png',{type:'image/png'});
      if(navigator.canShare&&navigator.canShare({files:[f]})){
        navigator.share({files:[f],text:title+' '+url}).catch(function(){});
      }else{
        var u=URL.createObjectURL(blob),l=document.createElement('a');l.href=u;l.download=f.name;document.body.appendChild(l);l.click();document.body.removeChild(l);setTimeout(function(){URL.revokeObjectURL(u);},4000);
        if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).catch(function(){});}
        note.textContent='Gambar '+kind+' sudah diunduh dan tautan artikel disalin. Buka Instagram, pilih '+kind+', lalu pilih gambarnya (di Story, tempel tautan lewat stiker Tautan).';note.hidden=false;
      }
    }).catch(function(){b.textContent=o;b.disabled=false;});
  });}
  ig('Story',1080,1920);ig('Post',1080,1350);
  btn('Salin tautan',function(b){
    function done(){var o=b.textContent;b.textContent='Tersalin \u2713';setTimeout(function(){b.textContent='Salin tautan';},2000);}
    function old(){var t=document.createElement('textarea');t.value=url;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(t);}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(done,old);}else{old();}
  });
  box.appendChild(note);
  var anchor=a.querySelector('.post-src');
  if(anchor){anchor.insertAdjacentElement('afterend',box);}
  else{var r=a.querySelector('.related');if(r){r.parentNode.insertBefore(box,r);}else{a.appendChild(box);}}
}
function init(){var l=document.querySelectorAll('article.post');for(var i=0;i<l.length;i++){build(l[i]);}}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}else{init();}
})();
