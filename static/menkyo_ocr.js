const video  = document.querySelector("#camera");
const canvas = document.querySelector("#picture");
const pfs    = document.getElementById("place_for_suggestions");

let a = -1;  // 反転ボタン用変数初期化
let videoTimer;

document.querySelector("#chenge").addEventListener("click", () => {
  // 動画反転
  a *= -1;
  var iframe2 = document.querySelector("#iframe2");
  console.log(a);
  document.querySelector("#camera").style.transform = `scaleX(${a})`;
  // 　赤枠反転
  if (a === -1){
      iframe2.style.marginLeft = "300px";
  }else{
      iframe2.style.marginLeft = "180px";
  }
})

function get_pict(){
    const ctx = canvas.getContext("2d");
    // 演出的な目的で一度映像を止めてSEを再生する
    video.pause();  // 映像を停止
    setTimeout( () => {
      video.play();    // 0.5秒後にカメラ再開
    }, 500);

    // canvasに画像を貼り付ける
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    function send_img(){
        //canvas elementを取得
        var canvas = document.getElementById('picture');
        //base64データを取得（エンコード）
        var base64 = canvas.toDataURL('image/jpeg', 0.75);

        var fData = new FormData();
        fData.append('img', base64);
        $("#place_for_suggestions").html("少々お待ちください")
        //ajax送信
        $.ajax({
            //画像処理サーバーに返す場合
            url: '/image_ocr_ajax',
            type: 'POST',
            data: fData ,
            contentType: false,
            processData: false,
            dataType: "text",
            success: function(data, dataType) {
                //非同期で通信成功時に読み出される [200 OK 時]
                console.log('Success', data);
                $("#place_for_suggestions").html(data);
                //location.reload(true);
            },
            error: function(XMLHttpRequest, textStatus, errorThrown) {
                //非同期で通信失敗時に読み出される
                console.log('Error : ' + errorThrown);
            }
        });
    }
    send_img()
}

// 自動撮影の処理スタートする関数
function startTimer(){
    console.log("start")
    videoTimer = setInterval(function(){
        if (pfs.textContent !== "少々お待ちください"){
            if (isNaN(pfs.textContent)　|| !pfs.textContent){
                get_pict();
            } else {
                stopTimer();
            }
        }
      }, 1000/500);
    }

// 自動撮影の処理をストップする関数
function stopTimer(){
    console.log("stop")
    clearInterval(videoTimer);
    }


window.onload = () => {
  /** カメラ設定 */
  const constraints = {
    audio: false,
    video: {
      width: { ideal : 640 },
      height: { ideal : 380 },
      facingMode: "user"   // フロントカメラを利用する
      // facingMode: { exact: "environment" }  // リアカメラを利用する場合
    }
  };

  /**
   * カメラを<video>と同期
   */
  navigator.mediaDevices.getUserMedia(constraints)
  .then( (stream) => {
    console.log(video.onloadedmetadata)
    video.srcObject = stream;
    video.onloadedmetadata = (e) => {
      video.play();
    }
  })
  .catch( (err) => {
    console.log(err.name + ": " + err.message);
  });


  /**
   * シャッターボタン
   */
   document.querySelector("#shutter").addEventListener("click", () => {
    stopTimer()
    get_pict()
  });
};