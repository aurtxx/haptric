'use strict';
(() => {
 const questions=[
 {text:'A study group has 6 students. Each gets 4 practice sheets. How many sheets are needed?',options:['10 sheets','18 sheets','24 sheets','30 sheets']},
 {text:'Which part of this demonstration stays available when the internet is disconnected?',options:['The school’s local network','The cloud connection','Every website on the internet','None of the above']},
 {text:'A teacher wants one record for one attempt. What should a repeated synchronization do?',options:['Create a second attempt','Keep the same accepted record','Delete the local answer','Restart the exam']}
 ];
 let online=true,index=0,answers={},cloud={},revision=0,cloudRevision=0,submitted=false,receipt=null,view='student';
 const $=id=>document.getElementById(id);
 function announce(text){$('activity-message').textContent=text;}
 function switchView(next){view=next;for(const tab of document.querySelectorAll('[data-view]')){const active=tab.dataset.view===next;tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;$('panel-'+tab.dataset.view).hidden=!active;}render();}
 function sync(){cloud={...answers};cloudRevision=revision;}
 function render(){
  $('wan').classList.toggle('offline',!online);$('wan-label').textContent=online?'Internet connected':'Internet disconnected';
  $('connection-status').textContent=online?'● Internet connected':'◌ Internet disconnected · LAN stays on';
  $('toggle-network').textContent=online?'Simulate internet outage':'Reconnect & synchronize';
  const count=Object.keys(answers).length,pending=revision-cloudRevision;
  $('hub-summary').textContent=count+' answers held locally';$('cloud-summary').textContent=Object.keys(cloud).length+' answers synchronized';
  $('saved-count').textContent=count+' / 3';$('pending-count').textContent=String(pending);$('attempt-status').textContent=submitted?'Submitted':'In progress';
  $('question-count').textContent='Question '+(index+1)+' of 3';$('question-text').textContent=questions[index].text;
  const palette=document.querySelector('.palette');palette.replaceChildren();
  questions.forEach((q,i)=>{const b=document.createElement('button');b.textContent=(i+1)+(answers[i]!==undefined?' ✓':'');b.className=answers[i]!==undefined?'answered':'';b.setAttribute('aria-label','Question '+(i+1)+(answers[i]!==undefined?', answered':''));b.setAttribute('aria-current',String(i===index));b.onclick=()=>{index=i;render();$('question-text').focus();};palette.append(b);});
  const choices=$('choices');choices.replaceChildren();const legend=document.createElement('legend');legend.className='sr-only';legend.textContent='Select an answer';choices.append(legend);
  questions[index].options.forEach((option,i)=>{const label=document.createElement('label');label.className='choice';const input=document.createElement('input');input.type='radio';input.name='answer';input.value=String(i);input.checked=answers[index]===i;input.disabled=submitted;input.onchange=()=>{if(answers[index]!==i){answers[index]=i;revision++;if(online)sync();}const focused=i;render();$('choices').querySelectorAll('input')[focused].focus();announce(online?'Answer saved at the school and synchronized to the cloud.':'Answer saved at the school. It will synchronize when the internet returns.');};const text=document.createElement('span');text.textContent=option;label.append(input,text);choices.append(label);});
  $('previous').disabled=index===0;$('next').hidden=index===2;$('submit').hidden=index!==2;$('submit').disabled=submitted;
  $('save-note').textContent=submitted?'Submitted. Your answers are locked for this demo.':answers[index]!==undefined?(online?'✓ Saved locally and synchronized.':'✓ Saved locally. Cloud sync is waiting.'):'Choose an answer to begin.';
  const tbody=$('answer-rows');tbody.replaceChildren();questions.forEach((q,i)=>{const tr=document.createElement('tr');['Q'+(i+1),answers[i]===undefined?'Not answered':q.options[answers[i]],cloud[i]===undefined?'No cloud answer':q.options[cloud[i]],answers[i]===undefined?'Waiting':cloud[i]===answers[i]?'Synchronized':'Queued locally'].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.append(td);});tbody.append(tr);});
  $('receipt-empty').hidden=submitted;$('receipt-ready').hidden=!submitted;
  if(submitted){$('receipt-id').textContent=receipt;$('receipt-answers').textContent=count+' of 3';$('receipt-cloud').textContent=online&&pending===0?'Same accepted record':'Waiting for connection';}
 }
 $('toggle-network').onclick=()=>{online=!online;if(online){sync();announce('Connection restored. All local changes reconciled. No duplicate attempt created.');}else announce('Only the simulated internet link is down. Keep answering over the local network.');render();};
 $('previous').onclick=()=>{index=Math.max(0,index-1);render();$('question-text').focus();};
 $('next').onclick=()=>{index=Math.min(2,index+1);render();$('question-text').focus();};
 $('submit').onclick=()=>{if(Object.keys(answers).length<3){$('save-note').textContent='For the pitch walkthrough, answer all three questions before submitting.';announce('Some questions still need an answer. Use the question buttons to find them.');return;}if(!submitted){submitted=true;revision++;receipt='HAP-DEMO-'+String(revision).padStart(3,'0');if(online)sync();}switchView('receipt');$('tab-receipt').focus();announce('Practice submitted once. The receipt stays the same when synchronization is repeated.');};
 $('replay').onclick=()=>{if(online){sync();$('replay-note').textContent='Replayed successfully. Receipt '+receipt+' is unchanged; there is still one attempt.';}else $('replay-note').textContent='The internet is still disconnected. Reconnect to replay synchronization.';render();};
 $('reset').onclick=()=>{online=true;index=0;answers={};cloud={};revision=0;cloudRevision=0;submitted=false;receipt=null;$('replay-note').textContent='';switchView('student');announce('Demo restarted. Disconnect the internet and save your first answer.');};
 document.querySelectorAll('[data-view]').forEach(tab=>{tab.onclick=()=>switchView(tab.dataset.view);tab.onkeydown=e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const tabs=[...document.querySelectorAll('[data-view]')];let i=tabs.indexOf(tab);i=e.key==='Home'?0:e.key==='End'?2:(i+(e.key==='ArrowRight'?1:2))%3;switchView(tabs[i].dataset.view);tabs[i].focus();};});
 $('back-to-desk').onclick=()=>{switchView('student');$('tab-student').focus();};$('pitch-notes').onclick=()=>$('notes').showModal();
 $('present').onclick=()=>{document.body.classList.toggle('pitch-mode');$('present').textContent=document.body.classList.contains('pitch-mode')?'Exit pitch mode':'Pitch mode';$('demo').scrollIntoView();$('exit-pitch').focus();announce('Pitch mode. Press Escape to return to the full story.');};
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.body.classList.remove('pitch-mode');$('present').textContent='Pitch mode';}});
 $('exit-pitch').onclick=()=>{document.body.classList.remove('pitch-mode');$('present').textContent='Pitch mode';$('present').focus();};
 render();
})();
