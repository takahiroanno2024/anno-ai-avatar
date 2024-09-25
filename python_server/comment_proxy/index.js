let isListening = false;
function startListen() {
    isListening = true;
    const webSocket = new WebSocket('ws://127.0.0.1:11180/sub');

    webSocket.onopen = function (event) {
        console.log('Connected to OneComme WebSocket API');
    };

    webSocket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        if(data.type == "comments"){
            onReceiveComment(data);
        }
    };

    webSocket.onclose = function (event) {
        if (event.wasClean) {
            console.log(`Connection closed cleanly, code=${event.code} reason=${event.reason}`);
        } else {
            console.error('Connection died');
        }
        isListening = false;
    };

    webSocket.onerror = function (error) {
        console.error(`WebSocket Error: ${error}`);
        isListening = false;
    };
}

setInterval(()=>{
    // 1000ミリ秒ごとにもしもソケットが死んでたら再開させる
    if(!isListening){
        startListen();
    }
},1000);


function onReceiveComment(data) {
    for(const comment of data.data.comments){
        const commentToSend = {
            live_id: comment.data.liveId,
            message_id: comment.data.id,
            name: comment.data.name,
            message: comment.data.comment,
            profile: comment.data.profileImage,
        };
        sendComment(commentToSend);
    }
}

async function sendComment(comment,nextWaitTime){
    try{
        await fetch(`${location.origin}/youtube/chat_message`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(comment)
          })
    }catch(e){
        // コメント送信に失敗したらバックオフリトライ
        console.error(e);
        setTimeout(()=>{
            nextWaitTime *= 2;
            nextWaitTime = Math.min(nextWaitTime,16);    
            sendComment(comment,nextWaitTime);
        },nextWaitTime);
    }
}