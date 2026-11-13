import type { Router } from 'vue-router';
export function startAccessTracking(router: Router) {
  let visitorId='';
  try { visitorId=sessionStorage.getItem('medical_visit_id')||crypto.randomUUID();sessionStorage.setItem('medical_visit_id',visitorId); } catch { return; }
  const send=(kind:'page_view'|'heartbeat')=>{
    if(document.visibilityState!=='visible')return;
    const token=localStorage.getItem('medical_auth_token');
    void fetch(`${import.meta.env.VITE_API_BASE_URL||''}/api/access/visit`,{method:'POST',headers:{'Content-Type':'application/json',...(token?{Authorization:`Bearer ${token}`}:{})},body:JSON.stringify({path:router.currentRoute.value.path,visitor_id:visitorId,kind}),keepalive:true}).catch(()=>{});
  };
  router.afterEach((to,from,failure)=>{if(!failure&&to.path!==from.path)send('page_view');});
  window.setInterval(()=>send('heartbeat'),30000);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')send('heartbeat');});
}
