(function(){
var SITE='https://zinezine.online/',enc=encodeURIComponent;
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
  btn('Salin tautan',function(b){
    function done(){var o=b.textContent;b.textContent='Tersalin \u2713';setTimeout(function(){b.textContent='Salin tautan';},2000);}
    function old(){var t=document.createElement('textarea');t.value=url;t.style.position='fixed';t.style.opacity='0';document.body.appendChild(t);t.select();try{document.execCommand('copy');done();}catch(e){}document.body.removeChild(t);}
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(done,old);}else{old();}
  });
  var anchor=a.querySelector('.post-src');
  if(anchor){anchor.insertAdjacentElement('afterend',box);}
  else{var r=a.querySelector('.related');if(r){r.parentNode.insertBefore(box,r);}else{a.appendChild(box);}}
}
function init(){var l=document.querySelectorAll('article.post');for(var i=0;i<l.length;i++){build(l[i]);}}
if(document.readyState==='loading'){document.addEventListener('DOMContentLoaded',init);}else{init();}
})();
