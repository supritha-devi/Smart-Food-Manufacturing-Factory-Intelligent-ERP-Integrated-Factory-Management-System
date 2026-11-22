document.querySelectorAll('.password-toggle').forEach(function(button){button.addEventListener('click',function(){var input=document.getElementById(button.dataset.target);if(!input)return;var show=input.type==='password';input.type=show?'text':'password';button.textContent=show?'Hide':'Show';});});

document.querySelectorAll('.zone').forEach(function(zone){
  function activate(){ 
    var name=zone.dataset.name||'';var status=zone.dataset.status||'';var detail=zone.dataset.detail||'';
    var nameEl=document.getElementById('factoryInfoName');var statusEl=document.getElementById('factoryInfoStatus');var detailEl=document.getElementById('factoryInfoDetail');
    if(nameEl)nameEl.textContent=name;
    if(statusEl){statusEl.textContent=status;statusEl.className='status '+(status==='Operational'||status==='ACTIVE'||status==='Active'?'active':'inactive');}
    if(detailEl)detailEl.textContent=detail;
    var route=window.factoryDepartmentRoutes&&window.factoryDepartmentRoutes[name];
    if(route)window.location.href=route;
  }
  zone.addEventListener('click',activate);
  zone.addEventListener('keydown',function(event){if(event.key==='Enter'||event.key===' '){event.preventDefault();activate();}});
});

var zoom=1;var map=document.getElementById('factoryMap');function setZoom(){if(map)map.style.zoom=zoom;}var zoomIn=document.getElementById('zoomIn'),zoomOut=document.getElementById('zoomOut'),zoomReset=document.getElementById('zoomReset');if(zoomIn)zoomIn.onclick=function(){zoom=Math.min(1.5,zoom+.1);setZoom();};if(zoomOut)zoomOut.onclick=function(){zoom=Math.max(.7,zoom-.1);setZoom();};if(zoomReset)zoomReset.onclick=function(){zoom=1;setZoom();};

if(document.getElementById('moduleChart')&&window.Chart&&window.moduleChartData){var d=window.moduleChartData;new Chart(document.getElementById('moduleChart'),{type:'bar',data:{labels:['Departments','Products','Machines','Employees','Stock','Batches','Orders','Purchases','Inspections','Maintenance','Dispatches','Invoices'],datasets:[{label:'Records',data:[d.departments,d.products,d.machines,d.employees,d.stock,d.batches,d.orders,d.purchases,d.inspections,d.maintenance,d.dispatches,d.invoices],backgroundColor:['#B77950','#F4C6CF','#795548','#EADDD5','#D6C3D9','#E6EFDB','#E9D9AA','#CFE2BD','#BED7E1','#B77950','#F4C6CF','#8A7B74'],borderRadius:8}]},options:{responsive:true,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true}}}});}
function factoryClockTick(){
  document.querySelectorAll('[data-live-clock]').forEach(function(el){
    var parts=new Intl.DateTimeFormat('en-IN',{timeZone:'Asia/Kolkata',day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:true}).formatToParts(new Date());
    var values={};
    parts.forEach(function(part){values[part.type]=part.value});
    el.textContent=(values.day+'-'+values.month+'-'+values.year+' - '+values.hour+':'+values.minute+':'+values.second+' '+values.dayPeriod).replace(/  /g,' ');
  });
  document.querySelectorAll('[data-live-elapsed]').forEach(function(el){
    var start=Date.parse(el.dataset.start);
    if(!start)return;
    var seconds=Math.max(0,Math.floor((Date.now()-start)/1000));
    var h=Math.floor(seconds/3600),m=Math.floor((seconds%3600)/60),s=seconds%60;
    el.textContent=String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0');
  });
}
factoryClockTick();
setInterval(factoryClockTick,1000);

(function initVoiceRecorder(){
  var recorderRoot=document.getElementById('voiceRecorder');
  if(!recorderRoot)return;

  var startButton=document.getElementById('voiceStart');
  var pauseButton=document.getElementById('voicePause');
  var resumeButton=document.getElementById('voiceResume');
  var stopButton=document.getElementById('voiceStop');
  var statusText=document.getElementById('voiceStatus');
  var timerText=document.getElementById('voiceTimer');
  var preview=document.getElementById('voicePreview');
  var fileInput=document.getElementById('voiceFile');
  var transcript=document.getElementById('voiceTranscript');
  var durationInput=document.getElementById('durationSeconds');
  var mediaRecorder=null, chunks=[], stream=null, timerId=null, seconds=0, blob=null, speechRecognition=null;

  function setStatus(text, recording){
    statusText.textContent=text;
    var dot=document.querySelector('.voice-status-dot');
    if(dot)dot.className='voice-status-dot'+(recording?' recording':'');
  }

  function tickTimer(){
    seconds+=1;
    timerText.textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');
    durationInput.value=String(seconds);
  }

  function setDataFile(file){
    try{
      var transfer=new DataTransfer();
      transfer.items.add(file);
      fileInput.files=transfer.files;
    }catch(error){
      // Some browsers do not allow assigning FileList; manual file selection remains available.
    }
  }

  if(window.SpeechRecognition||window.webkitSpeechRecognition){
    var Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    speechRecognition=new Recognition();
    speechRecognition.continuous=true;
    speechRecognition.interimResults=true;
    speechRecognition.lang='ta-IN';
  }

  startButton.addEventListener('click',async function(){
    if(!navigator.mediaDevices||!navigator.mediaDevices.getUserMedia){
      setStatus('Microphone recording is unavailable; use audio upload.',false);
      return;
    }
    try{
      stream=await navigator.mediaDevices.getUserMedia({audio:true});
      var mimeType=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')?'audio/webm;codecs=opus':'audio/webm';
      mediaRecorder=new MediaRecorder(stream,{mimeType:mimeType});
      chunks=[];
      mediaRecorder.ondataavailable=function(event){if(event.data&&event.data.size>0)chunks.push(event.data);};
      mediaRecorder.onstop=function(){
        blob=new Blob(chunks,{type:mimeType});
        var file=new File([blob],'voice-recording.webm',{type:'audio/webm'});
        setDataFile(file);
        var url=URL.createObjectURL(blob);
        preview.src=url;
        preview.style.display='block';
        setStatus('Recording ready for review',false);
      };
      mediaRecorder.start(1000);
      seconds=0;
      timerText.textContent='00:00';
      timerId=setInterval(tickTimer,1000);
      setStatus('Recording in progress',true);
      startButton.disabled=true;pauseButton.disabled=false;stopButton.disabled=false;
      if(speechRecognition){
        try{speechRecognition.start();}catch(error){}
        speechRecognition.onresult=function(event){
          var text='';
          for(var i=event.resultIndex;i<event.results.length;i++)text+=event.results[i][0].transcript;
          if(text)transcript.value=(transcript.value+' '+text).trim();
        };
        speechRecognition.onerror=function(){setStatus('Recording audio; speech recognition fallback is manual text.',true);};
      }
    }catch(error){
      setStatus('Microphone permission denied or unavailable.',false);
    }
  });

  pauseButton.addEventListener('click',function(){
    if(mediaRecorder&&mediaRecorder.state==='recording'){
      mediaRecorder.pause();clearInterval(timerId);
      setStatus('Recording paused',false);pauseButton.disabled=true;resumeButton.disabled=false;
    }
  });

  resumeButton.addEventListener('click',function(){
    if(mediaRecorder&&mediaRecorder.state==='paused'){
      mediaRecorder.resume();timerId=setInterval(tickTimer,1000);
      setStatus('Recording resumed',true);pauseButton.disabled=false;resumeButton.disabled=true;
    }
  });

  stopButton.addEventListener('click',function(){
    if(mediaRecorder&&mediaRecorder.state!=='inactive')mediaRecorder.stop();
    if(speechRecognition){try{speechRecognition.stop();}catch(error){}}
    if(stream)stream.getTracks().forEach(function(track){track.stop();});
    if(timerId)clearInterval(timerId);
    startButton.disabled=false;pauseButton.disabled=true;resumeButton.disabled=true;stopButton.disabled=true;
  });
})();
