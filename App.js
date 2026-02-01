const templates={shocking:{inputs:[{key:"topic",label:"Ämne"},{key:"stat",label:"Siffra"},{key:"group",label:"Målgrupp"}],generate:d=>({script:[{text:`Det här visste du INTE om ${d.topic}...`,type:"hook"},{text:`${d.stat} av ${d.group} gör FEL.`,type:"body"},{text:`Följ + kommentera JA!`,type:"cta"}],images:["Chockad person","Graf","Hemlig stämpel"]})},secret:{inputs:[{key:"tool",label:"Verktyg"},{key:"benefit",label:"Fördel"},{key:"time",label:"Tid"}],generate:d=>({script:[{text:`99% känner inte till ${d.tool}.`,type:"hook"},{text:`Kan ${d.benefit} på ${d.time}.`,type:"body"},{text:`Följ + skriv KNEP!`,type:"cta"}],images:["Logo","Pengar","Klocka"]})}};

let currentTemplate=null,currentResult=null;

function selectTemplate(t){currentTemplate=t;const tpl=templates[t];document.querySelectorAll('.template-card').forEach(c=>c.classList.remove('selected'));event.currentTarget.classList.add('selected');document.getElementById('dynamicInputs').innerHTML=tpl.inputs.map(i=>`<div class="input-group"><label>${i.label}</label><input id="input_${i.key}"></div>`).join('');document.getElementById('step1').classList.remove('active');document.getElementById('step2').classList.add('active')}

function goBack(){document.getElementById('step2').classList.remove('active');document.getElementById('step1').classList.add('active')}

function resetApp(){document.getElementById('step3').classList.remove('active');document.getElementById('step1').classList.add('active')}

function generateContent(){if(!currentTemplate)return;const tpl=templates[currentTemplate],data={};for(let i of tpl.inputs){data[i.key]=document.getElementById(`input_${i.key}`).value}currentResult=tpl.generate(data);displayScript(currentResult.script);displayStoryboard(currentResult.script,currentResult.images);document.getElementById('step2').classList.remove('active');document.getElementById('step3').classList.add('active')}

function displayScript(s){document.getElementById('generatedScript').innerHTML=s.map((l,i)=>`<div class="script-line ${l.type}">${l.text}<span class="line-number">${i+1}</span></div>`).join('')}

function displayStoryboard(s,img){document.getElementById('generatedStoryboard').innerHTML=s.map((l,i)=>`<div class="story-item"><div class="story-visual">${i+1}</div><div class="story-content"><div class="story-text">${l.text}</div><div class="story-image-desc">🎬 ${img[i]}</div></div></div>`).join('')}

function copyScript(){navigator.clipboard.writeText(currentResult.script.map(s=>s.text).join('\n'))}

function copyStoryboard(){let t='MANUS:\n\n';currentResult.script.forEach((l,i)=>{t+=`${i+1}. ${l.text}\n🎬 ${currentResult.images[i]}\n\n`});navigator.clipboard.writeText(t)}
