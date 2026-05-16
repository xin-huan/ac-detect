// ============================================================
// enroll.js — 人脸录入 + 声纹录入 + 统一状态提示
// ============================================================

// --- DOM 元素引用 ---
const enrollNameInput = document.getElementById('enroll-name');
const startWebcamFace = document.getElementById('start-webcam-face');
const cameraContainerFace = document.getElementById('camera-container-face');
const webcamVideoFace = document.getElementById('webcam-video-face');
const snapshotCanvasFace = document.getElementById('snapshot-canvas-face');
const snapshotAreaFace = document.getElementById('snapshot-area-face');
const snapshotImageFace = document.getElementById('snapshot-image-face');
const retrySnapshotFace = document.getElementById('retry-snapshot-face');
const confirmSnapshotFace = document.getElementById('confirm-snapshot-face');
const faceFileUpload = document.getElementById('face-file-upload');
const faceEnrolledBadge = document.getElementById('face-enrolled-badge');

const startRecordingBtn = document.getElementById('start-recording');
const stopRecordingBtn = document.getElementById('stop-recording');
const audioPlayback = document.getElementById('audio-playback');
const uploadVoiceBtn = document.getElementById('upload-voice-data');
const voiceFileUpload = document.getElementById('voice-file-upload');
const voiceEnrolledBadge = document.getElementById('voice-enrolled-badge');

// ============================================================
// 人脸录入逻辑
// ============================================================
var faceStream = null;

async function startWebcam() {
    try {
        if (!getEnrollName()) { showStatus('请先输入学生姓名', 'warning'); return; }
        faceStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        webcamVideoFace.srcObject = faceStream;
        cameraContainerFace.classList.remove('hidden');
        snapshotAreaFace.classList.add('hidden');
        faceEnrolledBadge.classList.add('hidden');
        startWebcamFace.innerHTML = '📸 拍摄快照';
    } catch (error) {
        console.error('无法启动摄像头:', error);
        showStatus('无法启动摄像头，请检查权限或设备连接。', 'error');
    }
}

function stopWebcam() {
    if (faceStream) {
        faceStream.getTracks().forEach(function(track) { track.stop(); });
        faceStream = null;
    }
    cameraContainerFace.classList.add('hidden');
    startWebcamFace.innerHTML = '📷 启动摄像头';
}

function takeSnapshot() {
    var video = webcamVideoFace;
    var canvas = snapshotCanvasFace;
    var image = snapshotImageFace;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    var context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    var dataUrl = canvas.toDataURL('image/jpeg');
    image.src = dataUrl;
    stopWebcam();
    snapshotAreaFace.classList.remove('hidden');
    startWebcamFace.classList.add('hidden');
}

async function uploadFaceData(name, file) {
    if (!name || !file) return;
    showStatus('正在上传人脸特征并录入...', 'info');
    var formData = new FormData();
    formData.append('name', name);
    formData.append('file', file);
    try {
        var response = await fetch(API_BASE + '/face/enroll', { method: 'POST', body: formData });
        var data = await response.json();
        if (response.ok && data.status === 'success') {
            showStatus('人脸特征录入成功：' + name, 'success');
            faceEnrolledBadge.classList.remove('hidden');
            snapshotAreaFace.classList.add('hidden');
            startWebcamFace.classList.remove('hidden');
            startWebcamFace.innerHTML = '📷 启动摄像头';
            updateEnrollStatusHint();
        } else {
            showStatus('人脸录入失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('人脸录入网络错误:', error);
        showStatus('网络错误，无法连接到人脸录入服务: ' + error.message, 'error');
    }
}

confirmSnapshotFace.addEventListener('click', function() {
    var name = getEnrollName();
    snapshotCanvasFace.toBlob(function(blob) {
        uploadFaceData(name, new File([blob], name + '_snapshot.jpg', { type: 'image/jpeg' }));
    }, 'image/jpeg');
});

faceFileUpload.addEventListener('change', function(event) {
    var name = getEnrollName();
    var file = event.target.files[0];
    if (name && file) { uploadFaceData(name, file); }
    else if (!name) { showStatus('请先输入姓名', 'warning'); }
});

startWebcamFace.addEventListener('click', function() {
    if (!faceStream) { startWebcam(); }
    else { takeSnapshot(); }
});

retrySnapshotFace.addEventListener('click', function() {
    snapshotAreaFace.classList.add('hidden');
    startWebcamFace.classList.remove('hidden');
    startWebcam();
});

// ============================================================
// 声纹录入逻辑
// ============================================================
async function startRecording() {
    if (!getEnrollName()) { showStatus('请先输入学生姓名', 'warning'); return; }
    try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioPlayback.classList.add('hidden');
        voiceEnrolledBadge.classList.add('hidden');
        var mimeType = 'audio/webm;codecs=opus';
        if (!MediaRecorder.isTypeSupported(mimeType)) {
            console.warn('浏览器可能不支持 ' + mimeType + ' 格式。');
        }
        mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });
        var audioChunks = [];
        mediaRecorder.ondataavailable = function(event) { audioChunks.push(event.data); };
        mediaRecorder.onstop = function() {
            audioBlob = new Blob(audioChunks, { type: mimeType });
            var audioUrl = URL.createObjectURL(audioBlob);
            audioPlayback.src = audioUrl;
            audioPlayback.classList.remove('hidden');
            uploadVoiceBtn.disabled = false;
            if (stream) {
                stream.getTracks().forEach(function(track) { track.stop(); });
                stream = null;
            }
            showStatus('录制完成，请预览或上传。', 'success');
        };
        mediaRecorder.start();
        startRecordingBtn.disabled = true;
        stopRecordingBtn.disabled = false;
        uploadVoiceBtn.disabled = true;
        showStatus('正在录音 (点击停止按钮结束)...', 'info');
    } catch (error) {
        console.error('无法启动麦克风:', error);
        showStatus('无法启动麦克风，错误信息：' + error.message + '。请检查浏览器设置中的权限。', 'error');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        startRecordingBtn.disabled = false;
        stopRecordingBtn.disabled = true;
    }
}

async function uploadVoiceData(name, audioBlobParam) {
    if (!name || !audioBlobParam) return;
    showStatus('正在上传声纹特征并录入...', 'info');
    var fileName = audioBlobParam.name || (name + '_voice.webm');
    if (!audioBlobParam || audioBlobParam.size === 0) {
        showStatus('声纹录入失败: 未检测到有效的音频数据（文件大小为0）。请重试。', 'error');
        uploadVoiceBtn.disabled = false;
        return;
    }
    var formData = new FormData();
    formData.append('name', name);
    formData.append('voice_file', audioBlobParam, fileName);
    try {
        var response = await fetch(API_BASE + '/voice/enroll', { method: 'POST', body: formData });
        var data = await response.json();
        if (response.ok && data.status === 'success') {
            showStatus('声纹特征录入成功：' + name, 'success');
            voiceEnrolledBadge.classList.remove('hidden');
            audioPlayback.classList.add('hidden');
            uploadVoiceBtn.disabled = true;
            audioBlob = null;
            updateEnrollStatusHint();
        } else {
            showStatus('声纹录入失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (error) {
        console.error('声纹录入网络错误:', error);
        showStatus('网络错误，无法连接到声纹录入服务: ' + error.message, 'error');
    }
}

startRecordingBtn.addEventListener('click', startRecording);
stopRecordingBtn.addEventListener('click', stopRecording);
uploadVoiceBtn.addEventListener('click', function() {
    var name = getEnrollName();
    if (name && audioBlob) { uploadVoiceData(name, audioBlob); }
    else { showStatus('请确保已输入姓名并录制了音频', 'warning'); }
});

voiceFileUpload.addEventListener('change', function(event) {
    var name = getEnrollName();
    var file = event.target.files[0];
    if (!name) { showStatus('请先输入学生姓名', 'warning'); event.target.value = ''; return; }
    if (file) {
        showStatus('已选择文件: ' + file.name + '，正在准备上传...', 'info');
        uploadVoiceData(name, file);
        event.target.value = '';
    }
});

// ============================================================
// 统一录入状态提示
// ============================================================
async function updateEnrollStatusHint() {
    var name = getEnrollName();
    var hint = document.getElementById('enroll-status-hint');
    if (!name) { hint.classList.add('hidden'); return; }
    try {
        var resp = await fetch(API_BASE + '/face/unified_names');
        var data = await resp.json();
        if (data.status === 'success') {
            var found = (data.users || []).find(function(u) { return u.name === name; });
            if (found) {
                hint.classList.remove('hidden');
                if (found.enrollment === 'both') {
                    hint.innerHTML = '✅ 该学生的人脸和声纹特征均已录入。重新录入将更新特征。';
                    hint.className = 'text-sm text-green-600 dark:text-green-400 mt-2';
                } else if (found.enrollment === 'face') {
                    hint.innerHTML = '⚠️ 该学生仅录入了人脸特征，声纹特征待录入。';
                    hint.className = 'text-sm text-yellow-600 dark:text-yellow-400 mt-2';
                } else if (found.enrollment === 'voice') {
                    hint.innerHTML = '⚠️ 该学生仅录入了声纹特征，人脸特征待录入。';
                    hint.className = 'text-sm text-yellow-600 dark:text-yellow-400 mt-2';
                }
            } else {
                hint.classList.remove('hidden');
                hint.innerHTML = '📝 新学生，请录入人脸和/或声纹特征。';
                hint.className = 'text-sm text-blue-600 dark:text-blue-400 mt-2';
            }
        }
    } catch (e) { hint.classList.add('hidden'); }
}

var enrollHintTimer = null;
enrollNameInput.addEventListener('input', function() {
    faceEnrolledBadge.classList.add('hidden');
    voiceEnrolledBadge.classList.add('hidden');
    if (enrollHintTimer) clearTimeout(enrollHintTimer);
    enrollHintTimer = setTimeout(updateEnrollStatusHint, 400);
});
