// ============================================================
// archive.js — 学生档案管理（加载、筛选、修改、删除）
// ============================================================

async function loadArchive() {
    var loading = document.getElementById('archive-loading');
    var empty = document.getElementById('archive-empty');
    var content = document.getElementById('archive-content');
    var tableBody = document.getElementById('archive-table-body');
    var editPanel = document.getElementById('archive-edit-panel');
    var filter = document.getElementById('archive-filter').value;

    loading.classList.remove('hidden');
    empty.classList.add('hidden');
    content.classList.add('hidden');
    editPanel.classList.add('hidden');

    try {
        var resp = await fetch(API_BASE + '/face/unified_names');
        var data = await resp.json();
        if (data.status !== 'success') throw new Error(data.message);

        var allUsers = data.users || [];

        var filtered = allUsers.filter(function(u) {
            if (filter === 'all') return true;
            return u.enrollment === filter;
        });

        loading.classList.add('hidden');

        if (filtered.length === 0) {
            empty.classList.remove('hidden');
            if (filter !== 'all') {
                empty.querySelector('p:first-child').textContent = '🔍';
                empty.querySelector('p:nth-child(2)').textContent = '没有匹配的学生';
            }
            return;
        }

        content.classList.remove('hidden');
        tableBody.innerHTML = '';
        filtered.forEach(function(user, idx) {
            var faceStatus = (user.enrollment === 'both' || user.enrollment === 'face') ?
                '<span class="text-green-600 dark:text-green-400 font-medium">✅ 已录入</span>' :
                '<span class="text-red-500 dark:text-red-400 font-medium">❌ 未录入</span>';
            var voiceStatus = (user.enrollment === 'both' || user.enrollment === 'voice') ?
                '<span class="text-green-600 dark:text-green-400 font-medium">✅ 已录入</span>' :
                '<span class="text-red-500 dark:text-red-400 font-medium">❌ 未录入</span>';
            var statusBadge = '';
            var statusClass = '';
            if (user.enrollment === 'both') { statusBadge = '完整'; statusClass = 'bg-accent text-white'; }
            else if (user.enrollment === 'face') { statusBadge = '仅人脸'; statusClass = 'bg-yellow-500 text-white'; }
            else if (user.enrollment === 'voice') { statusBadge = '仅声纹'; statusClass = 'bg-voice text-white'; }
            else { statusBadge = '未录入'; statusClass = 'bg-red-500 text-white'; }

            var row = document.createElement('tr');
            row.className = 'archive-row border-b border-gray-100 dark:border-gray-700';
            row.setAttribute('data-name', user.name);
            row.setAttribute('data-enrollment', user.enrollment);
            row.setAttribute('tabindex', '0');
            row.setAttribute('role', 'button');
            row.setAttribute('aria-expanded', 'false');
            row.innerHTML = '<td class="text-gray-400">' + (idx + 1) + '</td>' +
                '<td class="font-semibold text-gray-900 dark:text-gray-100">' + user.name + '</td>' +
                '<td>' + faceStatus + '</td>' +
                '<td>' + voiceStatus + '</td>' +
                '<td><span class="px-2 py-0.5 text-xs font-semibold rounded-full ' + statusClass + '">' + statusBadge + '</span></td>' +
                '<td><button class="text-primary hover:text-primary-dark text-sm font-medium archive-edit-btn" data-name="' + user.name + '">✏️ 修改</button></td>' +
                '<td><button class="text-red-500 hover:text-red-700 text-sm font-medium archive-delete-btn" data-name="' + user.name + '" title="删除学生">🗑️</button></td>';
            row.addEventListener('click', function(e) {
                if (e.target.classList.contains('archive-edit-btn') || e.target.classList.contains('archive-delete-btn')) return;
                toggleArchiveEdit(user);
            });
            tableBody.appendChild(row);
        });

        document.querySelectorAll('.archive-edit-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var name = this.getAttribute('data-name');
                var user = allUsers.find(function(u) { return u.name === name; });
                if (user) showArchiveEditPanel(user);
            });
        });
        document.querySelectorAll('.archive-delete-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var name = this.getAttribute('data-name');
                deleteStudent(name);
            });
        });
    } catch (e) {
        loading.classList.add('hidden');
        showStatus('加载学生档案失败: ' + e.message, 'error');
    }
}

function toggleArchiveEdit(user) {
    var panel = document.getElementById('archive-edit-panel');
    if (!panel.classList.contains('hidden') && panel.getAttribute('data-current-name') === user.name) {
        panel.classList.add('hidden');
        panel.setAttribute('data-current-name', '');
        return;
    }
    showArchiveEditPanel(user);
}

function showArchiveEditPanel(user) {
    var panel = document.getElementById('archive-edit-panel');
    panel.classList.remove('hidden');
    panel.setAttribute('data-current-name', user.name);

    var hasFace = user.enrollment === 'both' || user.enrollment === 'face';
    var hasVoice = user.enrollment === 'both' || user.enrollment === 'voice';

    var photoUrl = API_BASE + '/face/photo/' + encodeURIComponent(user.name);
    panel.innerHTML = '<div class="flex items-center justify-between mb-4">' +
        '<div class="flex items-center gap-4">' +
            '<img src="' + photoUrl + '" alt="' + user.name + '" class="w-16 h-16 rounded-full object-cover border-2 border-primary shadow-md" onerror="this.style.display=\'none\'">' +
            '<h3 class="text-xl font-bold text-gray-900 dark:text-gray-100">✏️ 修改学生: ' + user.name + '</h3>' +
        '</div>' +
        '<button class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-sm" onclick="document.getElementById(\'archive-edit-panel\').classList.add(\'hidden\')">✕ 关闭</button>' +
        '</div>' +
        '<div class="grid grid-cols-1 md:grid-cols-2 gap-6">' +
        '<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">' +
            '<h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center">' +
                '<span class="w-7 h-7 rounded-lg bg-red-100 dark:bg-red-900/40 flex items-center justify-center mr-2 text-sm">📸</span>人脸特征' +
                '<span class="ml-2 px-2 py-0.5 text-xs rounded-full ' + (hasFace ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300') + '">' + (hasFace ? '已录入' : '未录入') + '</span>' +
            '</h4>' +
            '<p class="text-sm text-gray-500 dark:text-gray-400 mb-3">' + (hasFace ? '可重新拍照或上传新图片来更新人脸特征。' : '该学生尚未录入人脸特征，请拍照或上传图片。') + '</p>' +
            '<div class="flex flex-wrap gap-2">' +
                '<button class="py-2 px-4 bg-camera text-white text-sm rounded-lg hover:shadow-lg transition-all active:scale-[0.98] archive-face-webcam" data-name="' + user.name + '">📷 拍照更新</button>' +
                '<label class="py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm cursor-pointer transition-colors">' +
                    '📁 上传图片<input type="file" class="hidden archive-face-file" data-name="' + user.name + '" accept="image/*">' +
                '</label>' +
                (hasFace ? '<button class="py-2 px-4 border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors active:scale-[0.98] archive-face-delete" data-name="' + user.name + '">🗑️ 删除</button>' : '') +
            '</div>' +
            '<div id="archive-face-status-' + user.name + '" class="mt-3 hidden"></div>' +
        '</div>' +
        '<div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4">' +
            '<h4 class="font-semibold text-gray-800 dark:text-gray-200 mb-3 flex items-center">' +
                '<span class="w-7 h-7 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center mr-2 text-sm">🎤</span>声纹特征' +
                '<span class="ml-2 px-2 py-0.5 text-xs rounded-full ' + (hasVoice ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300' : 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300') + '">' + (hasVoice ? '已录入' : '未录入') + '</span>' +
            '</h4>' +
            '<p class="text-sm text-gray-500 dark:text-gray-400 mb-3">' + (hasVoice ? '可重新录制或上传新音频来更新声纹特征。' : '该学生尚未录入声纹特征，请录制或上传音频。') + '</p>' +
            '<div class="flex flex-wrap gap-2">' +
                '<button class="py-2 px-4 bg-voice text-white text-sm rounded-lg hover:shadow-lg transition-all active:scale-[0.98] archive-voice-record" data-name="' + user.name + '">🎙️ 录制更新</button>' +
                '<label class="py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 text-sm cursor-pointer transition-colors">' +
                    '📂 上传音频<input type="file" class="hidden archive-voice-file" data-name="' + user.name + '" accept="audio/*, video/*">' +
                '</label>' +
                (hasVoice ? '<button class="py-2 px-4 border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 text-sm rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 transition-colors active:scale-[0.98] archive-voice-delete" data-name="' + user.name + '">🗑️ 删除</button>' : '') +
            '</div>' +
            '<div class="mt-3 hidden" id="archive-voice-recorder-' + user.name + '">' +
                '<div class="flex space-x-2 mb-2">' +
                    '<button class="flex-1 py-1.5 bg-voice text-white text-sm rounded-lg archive-voice-start">🎙️ 开始</button>' +
                    '<button class="flex-1 py-1.5 bg-gray-400 text-white text-sm rounded-lg disabled:opacity-50 archive-voice-stop" disabled>⏹️ 停止</button>' +
                '</div>' +
                '<audio class="w-full hidden archive-voice-preview" controls></audio>' +
                '<button class="w-full mt-2 py-1.5 bg-primary text-white text-sm rounded-lg disabled:opacity-50 archive-voice-confirm" disabled>✅ 确认上传</button>' +
            '</div>' +
            '<div id="archive-voice-status-' + user.name + '" class="mt-3 hidden"></div>' +
        '</div>' +
        '</div>';

    // Bind face actions
    panel.querySelector('.archive-face-webcam').addEventListener('click', function() {
        archiveCaptureFace(user.name);
    });
    panel.querySelector('.archive-face-file').addEventListener('change', function(e) {
        var file = e.target.files[0];
        if (file) uploadFaceData(user.name, file).then(function() { loadArchive(); });
    });
    var faceDelBtn = panel.querySelector('.archive-face-delete');
    if (faceDelBtn) {
        faceDelBtn.addEventListener('click', function() {
            deleteFaceEnrollment(user.name);
        });
    }

    // Bind voice actions
    panel.querySelector('.archive-voice-record').addEventListener('click', function() {
        archiveRecordVoice(user.name, panel);
    });
    panel.querySelector('.archive-voice-file').addEventListener('change', function(e) {
        var file = e.target.files[0];
        if (file) uploadVoiceData(user.name, file).then(function() { loadArchive(); });
    });
    var voiceDelBtn = panel.querySelector('.archive-voice-delete');
    if (voiceDelBtn) {
        voiceDelBtn.addEventListener('click', function() {
            deleteVoiceEnrollment(user.name);
        });
    }
}

// Archive face capture
async function archiveCaptureFace(name) {
    try {
        var capStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        showStatus('摄像头已启动，3秒后自动拍照...', 'info');
        setTimeout(function() {
            var video = document.createElement('video');
            video.srcObject = capStream;
            video.play();
            video.addEventListener('canplay', function() {
                var canvas = document.createElement('canvas');
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                canvas.getContext('2d').drawImage(video, 0, 0);
                canvas.toBlob(function(blob) {
                    capStream.getTracks().forEach(function(t) { t.stop(); });
                    uploadFaceData(name, new File([blob], name + '_update.jpg', { type: 'image/jpeg' })).then(function() { loadArchive(); });
                }, 'image/jpeg');
            });
        }, 3000);
    } catch (e) {
        showStatus('无法启动摄像头: ' + e.message, 'error');
    }
}

// Archive voice recording
var archiveMediaRecorder = null;
var archiveAudioChunks = [];
var archiveStream = null;

function archiveRecordVoice(name, panel) {
    var recorderDiv = document.getElementById('archive-voice-recorder-' + name);
    recorderDiv.classList.remove('hidden');
    var startBtn = recorderDiv.querySelector('.archive-voice-start');
    var stopBtn = recorderDiv.querySelector('.archive-voice-stop');
    var preview = recorderDiv.querySelector('.archive-voice-preview');
    var confirmBtn = recorderDiv.querySelector('.archive-voice-confirm');

    startBtn.addEventListener('click', async function() {
        try {
            archiveStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            archiveAudioChunks = [];
            var mimeType = 'audio/webm;codecs=opus';
            archiveMediaRecorder = new MediaRecorder(archiveStream, { mimeType: mimeType });
            archiveMediaRecorder.ondataavailable = function(e) { archiveAudioChunks.push(e.data); };
            archiveMediaRecorder.onstop = function() {
                var blob = new Blob(archiveAudioChunks, { type: mimeType });
                preview.src = URL.createObjectURL(blob);
                preview.classList.remove('hidden');
                confirmBtn.disabled = false;
                confirmBtn.onclick = function() {
                    uploadVoiceData(name, blob).then(function() { loadArchive(); });
                };
                if (archiveStream) {
                    archiveStream.getTracks().forEach(function(t) { t.stop(); });
                    archiveStream = null;
                }
            };
            archiveMediaRecorder.start();
            startBtn.disabled = true;
            stopBtn.disabled = false;
            showStatus('正在录音...', 'info');
        } catch (e) {
            showStatus('无法启动麦克风: ' + e.message, 'error');
        }
    });

    stopBtn.addEventListener('click', function() {
        if (archiveMediaRecorder && archiveMediaRecorder.state !== 'inactive') {
            archiveMediaRecorder.stop();
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    });
}

async function deleteFaceEnrollment(name) {
    if (!confirm('确认删除 ' + name + ' 的人脸特征录入吗？此操作不可恢复。')) return;
    try {
        var resp = await fetch(API_BASE + '/face/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        var data = await resp.json();
        if (resp.ok && data.status === 'success') {
            showStatus('已删除 ' + name + ' 的人脸特征', 'success');
            loadArchive();
        } else {
            showStatus('删除失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showStatus('网络错误: ' + e.message, 'error');
    }
}

async function deleteStudent(name) {
    if (!confirm('确认删除学生 "' + name + '" 的全部档案（人脸 + 声纹）吗？此操作不可恢复。')) return;
    try {
        var resp = await fetch(API_BASE + '/face/delete-student', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        var data = await resp.json();
        if (resp.ok && data.status === 'success') {
            showStatus('已删除学生: ' + name, 'success');
            loadArchive();
        } else {
            showStatus('删除失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showStatus('网络错误: ' + e.message, 'error');
    }
}

async function deleteVoiceEnrollment(name) {
    if (!confirm('确认删除 ' + name + ' 的声纹特征录入吗？此操作不可恢复。')) return;
    try {
        var resp = await fetch(API_BASE + '/voice/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        var data = await resp.json();
        if (resp.ok && data.status === 'success') {
            showStatus('已删除 ' + name + ' 的声纹特征', 'success');
            loadArchive();
        } else {
            showStatus('删除失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showStatus('网络错误: ' + e.message, 'error');
    }
}

// --- Archive event bindings ---
document.getElementById('archive-filter').addEventListener('change', loadArchive);
document.getElementById('refresh-archive-btn').addEventListener('click', loadArchive);
