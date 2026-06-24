const k=require('katex'); const fs=require('fs');
const d=JSON.parse(fs.readFileSync(process.argv[2]));
let out={};
for(const [id,latex] of Object.entries(d)){
  try{k.renderToString(latex,{throwOnError:true,displayMode:true}); out[id]=true;}
  catch(e){ out[id]=false; }
}
process.stdout.write(JSON.stringify(out));
