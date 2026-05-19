// ============================================================
// analysis.js — 报告渲染 + 视频分析 + 下载
// ============================================================

// ============================================================
// 报告渲染
// ============================================================
function renderReport(report) {
    var reportContainer = document.getElementById('report-container');
    var noReportMessage = document.getElementById('no-report-message');
    var reportContent = document.getElementById('report-content');
    var reportSkeleton = document.getElementById('report-skeleton');

    noReportMessage.classList.add('hidden');
    reportContent.style.display = 'block';
    reportSkeleton.classList.add('hidden');

    window.reportData = report;
    var downloadReportBtn = document.getElementById('download-report-btn');
    if (downloadReportBtn) { downloadReportBtn.disabled = false; }
    var printReportBtn = document.getElementById('print-report-btn');
    if (printReportBtn) { printReportBtn.disabled = false; }

    var summary = report.summary || {};
    var students = report.students || [];

    // 考勤统计
    var presentStudents = summary.attendance ? summary.attendance.present || [] : [];
    var totalStudents = summary.attendance ? summary.attendance.total || 0 : 0;
    document.getElementById('attendance-stat').innerHTML = presentStudents.length + ' / ' + totalStudents + ' <span class="text-lg font-normal text-gray-500 dark:text-gray-400">人到课</span>';
    document.getElementById('attendance-list').textContent = '到课：' + (presentStudents.join(', ') || '无');

    // 平均专注度
    var averageScore = summary.average_score || 0;
    var avgConcentrationText = 'N/A';
    var avgConcentrationColor = 'bg-gray-400';
    if (averageScore >= 80) { avgConcentrationText = '高'; avgConcentrationColor = 'bg-accent'; }
    else if (averageScore >= 60) { avgConcentrationText = '中'; avgConcentrationColor = 'bg-yellow-500'; }
    else if (averageScore > 0) { avgConcentrationText = '低'; avgConcentrationColor = 'bg-red-500'; }

    var averageScoreVal = document.getElementById('average-score-val');
    var averageScoreText = document.getElementById('average-score-text');
    averageScoreVal.innerHTML = '0<span class="text-lg font-normal text-gray-500 dark:text-gray-400">/100</span>';
    averageScoreText.textContent = avgConcentrationText;
    averageScoreText.className = 'inline-flex items-center px-4 py-1.5 rounded-full text-base font-bold text-white ' + avgConcentrationColor + ' shadow-md';

    var targetScore = Math.round(averageScore);
    setTimeout(function() {
        animateCounter(averageScoreVal.querySelector ? averageScoreVal : averageScoreVal, targetScore, 1200, '<span class="text-lg font-normal text-gray-500 dark:text-gray-400">/100</span>');
        var attEl = document.getElementById('attendance-stat');
        attEl.innerHTML = '0 / ' + totalStudents + ' <span class="text-lg font-normal text-gray-500 dark:text-gray-400">人到课</span>';
        animateAttendanceCounter(attEl, presentStudents.length, totalStudents, 1200);
    }, 200);

    // 完整转录
    var fullTranscript = summary.full_transcript || "未识别到任何课堂语音内容。";
    var fullTranscriptOutput = document.getElementById('full-transcript-output');
    fullTranscriptOutput.innerHTML = fullTranscript;
    fullTranscriptOutput.className = 'flex-grow h-64 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg whitespace-pre-wrap overflow-y-auto scrollable-container ' +
        (fullTranscript.includes("未识别") ? 'text-gray-400 dark:text-gray-500 italic' : 'text-gray-700 dark:text-gray-300 font-mono text-sm leading-relaxed');

    // 个人报告
    var individualReportsContainer = document.getElementById('individual-reports-container');
    individualReportsContainer.innerHTML = '';
    if (students.length === 0) {
        individualReportsContainer.innerHTML = '<p class="text-center text-xl text-gray-400 dark:text-gray-500 py-10 border border-dashed border-gray-300 dark:border-gray-600 rounded-xl">视频分析后将在这里显示每位学生的详细报告。</p>';
        document.getElementById('student-report-toolbar').style.display = 'none';
    } else {
        document.getElementById('student-report-toolbar').style.display = '';
        renderStudentCards(students);
    }

    document.getElementById('report-content').scrollIntoView({ behavior: 'smooth' });
}

function initCollapsibleCards() {
    document.querySelectorAll('.student-card-toggle').forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            var card = toggle.closest('.student-report-card');
            var body = card.querySelector('.student-card-body');
            var icon = toggle.querySelector('.collapse-icon');
            var isHidden = body.classList.contains('hidden');
            if (isHidden) {
                body.classList.remove('hidden');
                body.classList.add('animate-fade-in');
                icon.style.transform = 'rotate(180deg)';
                toggle.setAttribute('aria-expanded', 'true');
            } else {
                body.classList.add('hidden');
                icon.style.transform = 'rotate(0deg)';
                toggle.setAttribute('aria-expanded', 'false');
            }
        });
        toggle.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggle.click();
            }
        });
    });
}

// ============================================================
// 学生卡片渲染（支持筛选 + 排序）
// ============================================================
var studentSearchInput = document.getElementById('student-search-input');
var studentSortSelect = document.getElementById('student-sort-select');

function getFilteredAndSortedStudents() {
    if (!window.reportData || !window.reportData.students) return [];
    var students = window.reportData.students.slice();

    // 筛选
    var query = (studentSearchInput ? studentSearchInput.value : '').trim().toLowerCase();
    if (query) {
        students = students.filter(function(s) {
            return (s.name || '').toLowerCase().indexOf(query) !== -1;
        });
    }

    // 排序
    var sortBy = studentSortSelect ? studentSortSelect.value : 'score-desc';
    if (sortBy === 'score-desc') {
        students.sort(function(a, b) { return (b.concentration_score || 0) - (a.concentration_score || 0); });
    } else if (sortBy === 'score-asc') {
        students.sort(function(a, b) { return (a.concentration_score || 0) - (b.concentration_score || 0); });
    } else if (sortBy === 'name-asc') {
        students.sort(function(a, b) { return (a.name || '').localeCompare(b.name || '', 'zh'); });
    } else if (sortBy === 'name-desc') {
        students.sort(function(a, b) { return (b.name || '').localeCompare(a.name || '', 'zh'); });
    }

    return students;
}

function renderStudentCards(students) {
    var container = document.getElementById('individual-reports-container');
    container.innerHTML = '';

    if (students.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-400 dark:text-gray-500 py-8">没有匹配的学生记录。</p>';
        return;
    }

    students.forEach(function(student, index) {
        var score = student.concentration_score || 0;
        var events = student.behavior_events || [];
        var speech = student.speech_content || "该学生在视频中未检测到发言。";

        var studentScoreText = '低';
        var studentScoreColor = 'bg-red-500';
        if (score >= 80) { studentScoreText = '高'; studentScoreColor = 'bg-accent'; }
        else if (score >= 60) { studentScoreText = '中'; studentScoreColor = 'bg-yellow-500'; }

        var eventsHtml = events.map(function(event) {
            return '<div class="relative pb-6">' +
                '<div class="absolute top-0 left-[-16px] h-full w-0.5 bg-gray-200 dark:bg-gray-700"></div>' +
                '<span class="absolute top-0 left-[-22px] h-3 w-3 rounded-full bg-primary ring-2 ring-white dark:ring-gray-800 z-10"></span>' +
                '<div class="ml-2">' +
                    '<p class="text-xs font-semibold text-gray-700 dark:text-gray-300">' + (event.time || 'N/A') + '</p>' +
                    '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 dark:bg-indigo-900/40 text-indigo-800 dark:text-indigo-300">' + event.name + '</span>' +
                    '<p class="text-gray-500 dark:text-gray-400 text-xs mt-0.5">' + (event.detail || '无详情') + '</p>' +
                '</div>' +
            '</div>';
        }).join('');

        var photoUrl = API_BASE + '/face/photo/' + encodeURIComponent(student.name);
        var cardHtml = '<div class="student-report-card glass-card p-6 border-t-8 border-primary animate-fade-in">' +
            '<div class="student-card-toggle flex items-center justify-between select-none" role="button" aria-expanded="false" tabindex="0">' +
                '<div class="flex items-center gap-3">' +
                    '<img src="' + photoUrl + '" alt="' + (student.name || '') + '" class="w-12 h-12 rounded-full object-cover border-2 border-primary shadow" onerror="this.style.display=\'none\'">' +
                    '<h3 class="text-2xl font-extrabold text-gray-900 dark:text-gray-100">' + (student.name || '未知学生') + '</h3>' +
                '</div>' +
                '<div class="flex items-center gap-3">' +
                    '<span class="text-2xl font-extrabold text-gray-900 dark:text-gray-100 student-score" data-target="' + score.toFixed(0) + '">0</span>' +
                    '<span class="px-3 py-1 rounded-full text-sm font-bold text-white ' + studentScoreColor + '">' + studentScoreText + '</span>' +
                    '<svg class="collapse-icon w-5 h-5 text-gray-400 dark:text-gray-500 transition-transform duration-300" style="transform:rotate(0deg)" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>' +
                '</div>' +
            '</div>' +
            '<div class="student-card-body mt-5 grid grid-cols-1 md:grid-cols-2 gap-6 hidden">' +
                '<div class="pr-6 md:border-r border-gray-200 dark:border-gray-700">' +
                    '<h4 class="text-lg font-bold text-gray-800 dark:text-gray-200 mb-3 flex items-center">' +
                        '<svg class="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20v-2c0-.656-.126-1.283-.356-1.857M17 20H7m0 0v-9m0 0h12v9m-12 0h-2c-.656 0-1.283-.126-1.857-.356m2.857.356a3 3 0 01-3-3v-2m4.357 1.857A3 3 0 005 17v2m4.357-3.857A3 3 0 0012 20h2M9 11h3V5H9v6zm7 0h3V5h-3v6z"/></svg>' +
                        '行为记录 (' + events.length + ' 个事件)' +
                    '</h4>' +
                    '<div class="relative border-l-2 border-gray-200 dark:border-gray-700 ml-4 pl-4 max-h-72 overflow-y-auto scrollable-container">' +
                        (eventsHtml || '<p class="text-gray-500 dark:text-gray-400 text-sm py-4">未检测到显著行为事件。</p>') +
                    '</div>' +
                '</div>' +
                '<div class="pt-6 md:pt-0">' +
                    '<h4 class="text-lg font-bold text-gray-800 dark:text-gray-200 mb-3 flex items-center">' +
                        '<svg class="w-5 h-5 text-blue-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>' +
                        '语音识别内容' +
                    '</h4>' +
                    '<pre class="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg text-gray-700 dark:text-gray-300 font-sans text-sm whitespace-pre-wrap max-h-72 overflow-y-auto scrollable-container">' + speech + '</pre>' +
                '</div>' +
            '</div>' +
        '</div>';
        container.innerHTML += cardHtml;
    });

    setTimeout(function() {
        initCollapsibleCards();
        document.querySelectorAll('.student-score').forEach(function(el) {
            var target = parseInt(el.getAttribute('data-target')) || 0;
            el.textContent = '0';
            animateCounter(el, target, 800, '');
        });
    }, 100);
}

// 筛选/排序变更时重新渲染
if (studentSearchInput) {
    studentSearchInput.addEventListener('input', function() {
        if (window.reportData && window.reportData.students) {
            renderStudentCards(getFilteredAndSortedStudents());
        }
    });
}
if (studentSortSelect) {
    studentSortSelect.addEventListener('change', function() {
        if (window.reportData && window.reportData.students) {
            renderStudentCards(getFilteredAndSortedStudents());
        }
    });
}

function animateAttendanceCounter(element, present, total, duration) {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        element.innerHTML = present + ' / ' + total + ' <span class="text-lg font-normal text-gray-500 dark:text-gray-400">人到课</span>';
        return;
    }
    var start = performance.now();
    function step(now) {
        var elapsed = now - start;
        var progress = Math.min(elapsed / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = Math.round(present * eased);
        element.innerHTML = current + ' / ' + total + ' <span class="text-lg font-normal text-gray-500 dark:text-gray-400">人到课</span>';
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ============================================================
// 打印 / 导出 PDF
// ============================================================
function printReport() {
    if (!reportData) {
        showStatus('没有可打印的分析报告。请先运行分析。', 'warning');
        return;
    }

    var summary = reportData.summary || {};
    var students = reportData.students || [];
    var presentStudents = summary.attendance ? summary.attendance.present || [] : [];
    var totalStudents = summary.attendance ? summary.attendance.total || 0 : 0;
    var averageScore = summary.average_score || 0;
    var avgText = averageScore >= 80 ? '高' : (averageScore >= 60 ? '中' : (averageScore > 0 ? '低' : 'N/A'));
    var transcript = summary.full_transcript || '未识别到任何课堂语音内容。';

    var videoFileNameText = document.getElementById('video-file-name').textContent.replace(/\\.[^/.]+$/, "");

    var html = '<h1>📊 课堂分析报告</h1>';
    html += '<p style="font-size:10pt;color:#6b7280;margin-bottom:12pt;">视频: ' + videoFileNameText + ' | 生成时间: ' + new Date().toLocaleString() + '</p>';

    // 摘要卡片
    html += '<div class="print-summary-cards">';
    html += '<div class="print-card"><div class="label">考勤统计</div><div class="value">' + presentStudents.length + ' / ' + totalStudents + '</div><div style="font-size:9pt;color:#6b7280;">人到课</div></div>';
    html += '<div class="print-card"><div class="label">平均专注度</div><div class="value">' + averageScore + '<span style="font-size:10pt;font-weight:400;">/100</span></div><div style="font-size:9pt;">' + avgText + '</div></div>';
    html += '<div class="print-card"><div class="label">检测学生数</div><div class="value">' + students.length + '</div><div style="font-size:9pt;color:#6b7280;">人</div></div>';
    html += '</div>';

    // 到课名单
    html += '<h2>📋 考勤详情</h2>';
    html += '<p style="font-size:10pt;">到课学生: ' + (presentStudents.join(', ') || '无') + '</p>';

    // 学生详细报告
    html += '<h2>🎯 学生详细报告 (' + students.length + ' 人)</h2>';
    students.forEach(function(s) {
        var score = s.concentration_score || 0;
        var scoreText = score >= 80 ? '高' : (score >= 60 ? '中' : '低');
        var scoreColor = score >= 80 ? '#10b981' : (score >= 60 ? '#eab308' : '#ef4444');
        var events = s.behavior_events || [];
        var speech = s.speech_content || '该学生在视频中未检测到发言。';
        var photoUrl = API_BASE + '/face/photo/' + encodeURIComponent(s.name);

        html += '<div class="student-print-row">';
        html += '<img src="' + photoUrl + '" alt="' + s.name + '" class="avatar" onerror="this.style.display=\'none\'">';
        html += '<div class="info">';
        html += '<span class="name">' + (s.name || '未知学生') + '</span>';
        html += '<span class="score-badge" style="background:' + scoreColor + ';">' + score + ' 分 · ' + scoreText + '</span>';
        if (events.length > 0) {
            html += '<div class="events">📌 行为记录: ' + events.map(function(e) { return e.time + ' ' + e.name; }).join('、') + '</div>';
        }
        if (speech && speech.indexOf('未检测到发言') === -1) {
            html += '<div class="speech">💬 发言: ' + speech.substring(0, 200) + (speech.length > 200 ? '...' : '') + '</div>';
        }
        html += '</div></div>';
    });

    // 完整转录
    html += '<h2>📢 课堂语音转录</h2>';
    html += '<div class="transcript-block">' + transcript.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</div>';

    document.getElementById('print-report-content').innerHTML = html;
    document.getElementById('print-report').style.display = 'block';

    setTimeout(function() {
        window.print();
        setTimeout(function() {
            document.getElementById('print-report').style.display = 'none';
        }, 500);
    }, 300);
}

// ============================================================
// 历史报告加载
// ============================================================
async function loadHistory() {
    var loading = document.getElementById('history-loading');
    var empty = document.getElementById('history-empty');
    var list = document.getElementById('history-list');

    loading.classList.remove('hidden');
    empty.classList.add('hidden');
    list.classList.add('hidden');

    try {
        var resp = await fetch(API_BASE + '/analysis/history');
        var data = await resp.json();
        loading.classList.add('hidden');

        if (data.status !== 'success' || !data.reports || data.reports.length === 0) {
            empty.classList.remove('hidden');
            return;
        }

        list.classList.remove('hidden');
        list.innerHTML = '';
        data.reports.forEach(function(r) {
            var date = new Date(r.timestamp * 1000).toLocaleString('zh-CN');
            var avgColor = r.average_score >= 80 ? 'text-green-600' : (r.average_score >= 60 ? 'text-yellow-600' : 'text-red-500');
            var item = document.createElement('div');
            item.className = 'glass-card p-4 flex items-center justify-between hover:shadow-md transition-shadow cursor-pointer';
            item.innerHTML = '<div class="flex-1 min-w-0">' +
                '<h4 class="font-semibold text-gray-900 dark:text-gray-100 truncate">🎬 ' + (r.video_name || '未知视频') + '</h4>' +
                '<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">' + date + ' · ' + r.student_count + ' 位学生 · 考勤 ' + r.attendance_present + '/' + r.attendance_total + '</p>' +
                '</div>' +
                '<div class="flex items-center gap-3 flex-shrink-0 ml-4">' +
                    '<span class="text-lg font-extrabold ' + avgColor + '">' + r.average_score + '<span class="text-xs font-normal text-gray-400">/100</span></span>' +
                    '<button class="text-primary hover:text-primary-dark text-sm font-medium history-view-btn" data-video="' + r.video_name + '">📄 查看</button>' +
                    '<button class="text-red-500 hover:text-red-700 text-sm history-delete-btn" data-video="' + r.video_name + '">🗑️</button>' +
                '</div>';
            item.addEventListener('click', function(e) {
                if (e.target.classList.contains('history-view-btn') || e.target.classList.contains('history-delete-btn')) return;
                var vname = this.querySelector('.history-view-btn').getAttribute('data-video');
                if (vname) viewHistoryReport(vname);
            });
            list.appendChild(item);
        });

        // 绑定按钮事件
        document.querySelectorAll('.history-view-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                viewHistoryReport(this.getAttribute('data-video'));
            });
        });
        document.querySelectorAll('.history-delete-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                var vname = this.getAttribute('data-video');
                deleteHistoryReport(vname);
            });
        });
    } catch (e) {
        loading.classList.add('hidden');
        empty.classList.remove('hidden');
        empty.querySelector('p').textContent = '加载历史报告失败: ' + e.message;
    }
}

async function viewHistoryReport(videoName) {
    try {
        showStatus('正在加载历史报告: ' + videoName + '...', 'info');
        var resp = await fetch(API_BASE + '/analysis/report/' + encodeURIComponent(videoName));
        var data = await resp.json();
        if (data.status === 'success' && data.result) {
            reportData = data.result;
            document.getElementById('video-file-name').textContent = videoName + ' (历史)';
            renderReport(data.result);
            document.getElementById('report-content').scrollIntoView({ behavior: 'smooth' });
            showStatus('已加载历史报告: ' + videoName, 'success');
        } else {
            showStatus('加载失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showStatus('网络错误: ' + e.message, 'error');
    }
}

async function deleteHistoryReport(videoName) {
    if (!confirm('确认删除 "' + videoName + '" 的历史分析报告吗？')) return;
    try {
        var resp = await fetch(API_BASE + '/analysis/report/' + encodeURIComponent(videoName), { method: 'DELETE' });
        var data = await resp.json();
        if (resp.ok && data.status === 'success') {
            showStatus('已删除报告: ' + videoName, 'success');
            loadHistory();
        } else {
            showStatus('删除失败: ' + (data.message || '未知错误'), 'error');
        }
    } catch (e) {
        showStatus('网络错误: ' + e.message, 'error');
    }
}

// ============================================================
// 报告下载
// ============================================================
function downloadReport() {
    if (!reportData) {
        showStatus('没有可下载的分析报告。请先运行分析。', 'warning');
        return;
    }
    var reportText = JSON.stringify(reportData, null, 4);
    var blob = new Blob([reportText], { type: 'text/plain' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    var videoFileNameText = document.getElementById('video-file-name').textContent.replace(/\.[^/.]+$/, "");
    a.download = videoFileNameText + '_分析报告.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showStatus('分析报告已保存到本地。', 'success');
}

// ============================================================
// 视频分析
// ============================================================
async function startAnalysis() {
    if (!videoFile) {
        showStatus('请先选择一个视频文件', 'warning');
        return;
    }

    var downloadReportBtn = document.getElementById('download-report-btn');
    if (downloadReportBtn) { downloadReportBtn.disabled = true; }
    var printReportBtn = document.getElementById('print-report-btn');
    if (printReportBtn) { printReportBtn.disabled = true; }
    reportData = null;

    var startBtn = document.getElementById('start-analysis');
    startBtn.disabled = true;

    document.getElementById('no-report-message').classList.add('hidden');
    document.getElementById('report-content').style.display = 'none';
    document.getElementById('report-skeleton').classList.remove('hidden');

    var analysisProgress = document.getElementById('analysis-progress');
    var progressBarFill = document.getElementById('progress-bar-fill');
    var progressStatusText = document.getElementById('progress-status-text');

    analysisProgress.classList.remove('hidden');
    var PHASES = [
        { id: 1, label: '行为检测' },
        { id: 2, label: '语音识别' },
        { id: 3, label: '专注度评分' }
    ];
    PHASES.forEach(function(p) {
        var dot = document.getElementById('phase-dot-' + p.id);
        var label = document.getElementById('phase-label-' + p.id);
        if (dot) { dot.classList.remove('active', 'done'); }
        if (label) { label.classList.remove('active'); label.style.color = ''; }
    });
    progressBarFill.style.width = '0%';
    progressStatusText.textContent = '正在上传文件并启动后台分析...';

    document.getElementById('attendance-stat').innerHTML = 'N/A';
    document.getElementById('average-score-val').innerHTML = 'N/A';

    showStatus('视频分析请求已发送，后台正在处理中...', 'info');

    var formData = new FormData();
    formData.append('video_file', videoFile);

    var currentPhase = 1;
    var subPct = 0;
    var progressInterval = setInterval(function() {
        subPct += 2;
        if (subPct > 100) { subPct = 0; currentPhase = Math.min(currentPhase + 1, 3); }
        if (currentPhase < 3 && subPct > 90) { subPct = 90; }
        PHASES.forEach(function(p, i) {
            var dot = document.getElementById('phase-dot-' + p.id);
            var label = document.getElementById('phase-label-' + p.id);
            if (!dot) return;
            dot.classList.remove('active', 'done');
            if (label) { label.classList.remove('active'); label.style.color = ''; }
            if (i + 1 < currentPhase) {
                dot.classList.add('done');
                if (label) label.style.color = '#10b981';
            } else if (i + 1 === currentPhase) {
                dot.classList.add('active');
                if (label) label.classList.add('active');
            }
        });
        var total = ((currentPhase - 1) * 33.3) + (subPct * 33.3);
        progressBarFill.style.width = Math.min(total, 100) + '%';
        var statusTexts = {
            1: '阶段一：行为检测 (YOLO, 人脸识别)...',
            2: '阶段二：语音识别 (转录，声纹匹配)...',
            3: '阶段三：专注度评分与报告整合...'
        };
        progressStatusText.textContent = statusTexts[currentPhase] || statusTexts[3];
    }, 1200);

    try {
        var response = await fetch(API_BASE + '/analysis/analyze', { method: 'POST', body: formData });
        clearInterval(progressInterval);

        var data = await response.json();
        startBtn.disabled = false;

        if (response.ok && data.status === 'success') {
            PHASES.forEach(function(p) {
                var dot = document.getElementById('phase-dot-' + p.id);
                if (dot) { dot.classList.remove('active'); dot.classList.add('done'); }
                var label = document.getElementById('phase-label-' + p.id);
                if (label) label.style.color = '#10b981';
            });
            progressBarFill.style.width = '100%';
            progressStatusText.textContent = '分析完成！';
            document.getElementById('report-skeleton').classList.add('hidden');
            showStatus('视频综合分析成功完成！报告已生成。', 'success');

            if (data.result) {
                reportData = data.result;
                renderReport(data.result);
                loadHistory();
                celebrateIfAllowed();
            } else {
                showStatus('分析成功，但后端未返回完整的报告数据 (data.result 缺失)。', 'warning');
            }
        } else {
            progressStatusText.textContent = '分析失败！';
            document.getElementById('report-skeleton').classList.add('hidden');
            showStatus('视频分析失败: ' + (data.message || '未知错误'), 'error');
        }

        setTimeout(function() { analysisProgress.classList.add('hidden'); }, 2000);
    } catch (error) {
        clearInterval(progressInterval);
        startBtn.disabled = false;
        analysisProgress.classList.add('hidden');
        document.getElementById('report-skeleton').classList.add('hidden');
        progressBarFill.style.width = '0%';
        showStatus('网络错误，无法连接到视频分析服务: ' + error.message, 'error');
    }
}

// ============================================================
// 事件绑定
// ============================================================
var videoUpload = document.getElementById('video-upload');
var videoFileName = document.getElementById('video-file-name');
var startAnalysisBtn = document.getElementById('start-analysis');

videoUpload.addEventListener('change', function(event) {
    videoFile = event.target.files[0];
    if (videoFile) {
        videoFileName.textContent = videoFile.name;
        startAnalysisBtn.disabled = false;
        showStatus('已选择视频文件: ' + videoFile.name, 'info');
    } else {
        videoFileName.textContent = '未选择文件';
        startAnalysisBtn.disabled = true;
    }
});

startAnalysisBtn.addEventListener('click', startAnalysis);

var downloadReportBtn = document.getElementById('download-report-btn');
if (downloadReportBtn) {
    downloadReportBtn.addEventListener('click', downloadReport);
}

// 初始调用
updateEnrollStatusHint();
loadHistory();
