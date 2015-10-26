var context;
var gainNode;
var buffers = [];
window.addEventListener('load', init, false);
function init() {
  try {
    // Fix up for prefixing
    window.AudioContext = window.AudioContext||window.webkitAudioContext;
      context = new AudioContext();
      gainNode = context.createGain();
  }
  catch(e) {
    alert('Web Audio API is not supported in this browser');
  }


  document.body.style.background = getRandomColor();
}

var metaTags=document.getElementsByTagName("meta");

var cid = "";
for (var i = 0; i < metaTags.length; i++) {
    if (metaTags[i].getAttribute("property") == "cid") {
        cid = metaTags[i].getAttribute("content");
        break;
    }
}

console.log(cid);


var ws = new WebSocket("ws://"+window.location.hostname+":8888/earyx/"+cid)
ws.binaryType = 'arraybuffer';
var exp_finish = false;
var subject_name = false
var allow_debug = false
var isIOS = ( navigator.userAgent.match(/(iPad|iPhone|iPod)/g) ? true : false );


var isUnlocked = false;
function unlock() {
			
	if(isIOS != true || isUnlocked)
		return;

	// create empty buffer and play it
	var buffer = context.createBuffer(1, 1, 22050);
	var source = context.createBufferSource();
	source.buffer = buffer;
	source.connect(context.destination);
	source.start(0);
    source.onended = endedHandler;

    function endedHandler(event) {
       isUnlocked = true;
    }

}

function getRandomColor() {
    var letters = '0123456789ABCDEF'.split('');
    var color = '#';
    for (var i = 0; i < 6; i++ ) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

window.addEventListener('touchstart', unlock, false);


ws.onclose = function() {
    if (exp_finish == false) {
        console.log('connection lost. Try to reconnect...')
        ws = new WebSocket("ws://"+window.location.hostname+":8888/earyx/"+cid)
        ws.binaryType = 'arraybuffer';
    }
}

ws.onopen = function() {
    /* function gets called automatically on start of websocket
       
       Parameters:
       -----------
       no input arguments
       
       Returns:
       --------
       no return arguments
       
    */
};


ws.onmessage = function (event) {
    /* function handles incoming events
       
       Parameters:
       -----------
       evt : message received by target (wording from:
       https://developer.mozilla.org/en-US/docs/Web/API/MessageEvent) 
       
       Returns:
       --------
       no return arguments
       
       Function either sets texts in divs or sends messages to server via 
       'send_msg' function
       
    */
    if (event.data.constructor.name === "ArrayBuffer") {
        var headerLen = new Int32Array(event.data, 0, 1)[0];
        var header = String.fromCharCode.apply(null, new Uint8Array(event.data, 4, headerLen));
        var data = event.data.slice(headerLen+4)
    } else {
        var header = event.data;
    }
    try {
        msg = JSON.parse(header);
    } catch (e) {
        console.error("Message", e.message, "is not a valid JSON object");
        return
    }


    if (msg.type == 'params' || msg.type == 'feedback' || msg.type == 'task') {
	    document.getElementById(msg.type).innerHTML = msg.content;
    }
	
	if (msg.type == 'quit') {
        exp_finish = true
        send_msg('terminate', true)
     	ws.close()
    }
   

    if (msg.type == 'play') {
        var id = 0;
        var times = msg.content
        // calc sum length of all signals
        var len = times.reduce(function(prev, cur) {
            return prev + cur;
        });
        context.decodeAudioData(data, function(decodedData) {
            var source = context.createBufferSource();
            source.buffer = decodedData
            source.connect(gainNode)
            gainNode.connect(context.destination);
            source.start(0);
        });

        var delay = 0;
        var btnNr = 1
        for(var i=1;i<=times.length;i++) {
            delay += times[i-1];
            if (i % 2 == 0) {
                btnNr++;
            }
            setTimeout(
                (function(s, n) {
                    return function() {
                        if (s % 2 != 0) {
                            document.getElementById('but'+n).style.backgroundColor = 'red'
                            document.getElementById('but'+n).disabled = false
                            console.log(n)
                        } else {
                            document.getElementById('but'+(n-1)).style.backgroundColor = 'white'
                            console.log(n)
                        }
                    }
                })(i,btnNr), delay*1000);
        }
    };


    if (msg.type == 'allow_plot') {
        console.log(content)
        if (msg.content == false)
	    document.getElementById("dbgBtn").hidden = true;
	else
	    allow_debug = true
		    
    }

    if (msg.type == 'debug_state') {
        if (msg.content == true
	    && document.getElementById('dbgBtn').value == "Activate debugging") {
            change()
        }
    }

    else if (msg.type == 'run_finished' || msg.type == 'start_signal')
	send_msg(msg.type, msg.content);
    
    else if (msg.type == 'desc')
	alert(msg.content)

    else if (msg.type == 'but1' || msg.type == 'but2'
	     || msg.type == 'but3' || msg.type == 'but4') {
	    document.getElementById(msg.type).style.backgroundColor = msg.content
        console.log(msg.content)
        if (msg.content == 'red')
            document.getElementById(msg.type).disabled = false;
    }


    else if (msg.type == 'button') {
	document.getElementsByClassName(msg.type).style.backgroundColor = msg.content
    }

    else if (msg.type == 'plot')
        plot(msg.content)

    else if (msg.type == 'name') {
	if (msg.content != '') {
	    subject_name = true
	}
    }
};


function send_msg(type, content) {
    /* function sends message to server (Python) about ongoing events
       
       Function has no output but sends JSON struct to server.  
       
       Parameters:
       -----------
       type : string 
       
       content : usually a string or an integer
       
       Returns:
       --------
       no return arguments but
       
    */
    if (type == 'next_run') {
	var confirm_msg = 'Really next run?'
	var conf = confirm(confirm_msg);
	if (conf == true)
	    type = type;
	else
	    type = "cancel";
    }
    
    else if (type == 'quit') {
	    var confirm_msg = 'Really quit experiment?'
	    var conf = confirm(confirm_msg);
	    if (conf == true) {
            var conf = confirm('Save experiment before exit?')
	        if (conf == true) {
                type = 'quit'
                content = 'save'
            }
	        else {
                type = 'quit'
                content = 'drop'
            }
	        exp_finish = true;
	    }
	    else {
	        type = "cancel";
	    }
    }
    
    else if (type == 'run_finished') {
	var confirm_msg = 'Run finished. Continue?'
	var conf = confirm(confirm_msg);
	if (conf == true)
	    type = 'next_run';
	else {
	    send_msg('quit', 'quit')
            return
        }
    }
    
    else if (type == 'name') {
	while (content == '') {
	    var person = prompt("Please enter your name:");
	    if (person != '' && person != null) {
		type = type;
		content = person;
		break
	    }
	}
    }

    else if (type == 'debug') {
	if (allow_debug) 
	    change()
    }

    else if (type == 'answer') {
        console.log('here')
        var x = document.getElementsByClassName("answer_button");
        var i;
        for (i = 0; i < x.length; i++) {
            x[i].disabled = true;
        }
    }
	
    ws.send(JSON.stringify({
	type: type,
	content: content
    }))
    
};

function change() {
    /* function changes text and text color of debug button depending on state
       
       Parameters:
       -----------
       no input arguments
       
       Returns:
       --------
       no return arguments
       
     */
    var btn = document.getElementById("dbgBtn");
    if (btn.value=="Activate debugging") {
	btn.value = "Deactivate debugging";
	btn.style.color = 'green';
	document.getElementsByClassName('buttonGroup')[0].style.float = 'left'
    }
    else {
	btn.value = "Activate debugging";
	btn.style.color = 'red';
	var plt = document.getElementById("plot")
	plt.innerHTML = ''
	document.getElementsByClassName('buttonGroup')[0].style.float = ''
    }

};

function start_quit() {
    /* function sends start/quit signal and changes text of button depending on 
       state
       
       Parameters:
       -----------
       no input arguments
       
       Returns:
       --------
       no return arguments
       
    */
    var btn = document.getElementById("sqBtn");

    if (btn.value == "start experiment") {
	if (subject_name == false) { 
	    send_msg('name', '');
	}
	send_msg('start_signal','start');
	btn.value = "quit experiment";
    }
    
    else if (btn.value == "quit experiment") {
	send_msg('quit','quit')
    }
};

function plot(content) {
    var plt = document.getElementById("plot")
    plt.innerHTML = content
    var svg = plt.getElementsByTagName('svg')[0]
    svg.setAttribute('width', '40%')
    svg.setAttribute('height', '100%')
};

window.onbeforeunload = function() {
    /* function to confirm tab/window closing
       
       Parameters:
       -----------
       no input arguments
       
       Returns:
       -------- 
       confirm message
       
    */
    if (ws.readyState != ws.CLOSED)
	return 'Are you sure you want to quit?' // does not work in MOZ
};

