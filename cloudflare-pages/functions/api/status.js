// Cloudflare Pages Function. This reports only publicly verifiable GitHub Actions metadata.
// It NEVER labels the actual LUNOR desktop "ready" without an independent VM health signal.
const runsApi='https://api.github.com/repos/Gamevalentine/omarchy/actions/runs?branch=lunor%2Fweb-live-qa&per_page=8';
export async function onRequestGet({request}){
  const cache=caches.default;
  const key=new Request(new URL('/api/status',request.url).toString(),{method:'GET'});
  const cached=await cache.match(key);
  if(cached)return cached;
  try{
    const source=await fetch(runsApi,{
      headers:{Accept:'application/vnd.github+json','User-Agent':'LUNOR-Web-Lab-Status/1.0'},
      cf:{cacheEverything:true,cacheTtl:90}
    });
    if(!source.ok)throw new Error('GitHub status HTTP '+source.status);
    const j=await source.json();
    const runs=Array.isArray(j.workflow_runs)?j.workflow_runs:[];
    const match=runs.find(x=>x.path==='.github/workflows/lunor-web-live.yml');
    const run=match?{
      status:match.status,
      conclusion:match.conclusion,
      url:match.html_url,
      createdAt:match.created_at
    }:null;
    const response=new Response(JSON.stringify({run,desktopVerified:false,backendConnected:false}),{
      headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'public, max-age=30','X-Content-Type-Options':'nosniff'}
    });
    await cache.put(key,response.clone());
    return response;
  }catch(e){
    return new Response(JSON.stringify({error:'GitHub status unavailable',desktopVerified:false,backendConnected:false}),{
      status:503,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}
    });
  }
}
