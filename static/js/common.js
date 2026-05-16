// ============================================================
// common.js — 全局变量、Toast 通知、暗色模式、Tab 导航、动画工具
// ============================================================

// --- 全局变量 ---
const API_BASE = '/api';
let stream = null;
let videoFile = null;
let audioBlob = null;
let mediaRecorder = null;
let reportData = null;

// ============================================================
// Toast 通知系统
// ============================================================
const toastContainer = document.getElementById('toast-container');
const TOAST_DURATIONS = { success: 4000, info: 4000, warning: 6000, error: 0 };

function showToast(message, type, duration) {
    if (type === void 0) type = 'info';
    var dur = duration !== undefined ? duration : (TOAST_DURATIONS[type] || 4000);
    var icons = {
        success: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        error: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
        warning: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>',
        info: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>'
    };
    var toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.innerHTML = '<span class="flex-shrink-0 mt-0.5">' + icons[type] + '</span>' +
        '<span class="flex-1 text-sm font-medium">' + message + '</span>' +
        '<button class="flex-shrink-0 opacity-70 hover:opacity-100 ml-2 text-lg leading-none" aria-label="关闭通知">&times;</button>';
    var progressEl = null;
    var animationId = null;
    function removeToast(t) {
        if (t._removing) return;
        t._removing = true;
        if (animationId) cancelAnimationFrame(animationId);
        t.classList.add('removing');
        t.addEventListener('animationend', function() {
            if (t.parentNode) t.parentNode.removeChild(t);
        });
    }
    if (dur > 0) {
        progressEl = document.createElement('div');
        progressEl.className = 'toast-progress';
        progressEl.style.width = '100%';
        toast.appendChild(progressEl);
        var start = performance.now();
        function step(now) {
            var elapsed = now - start;
            var pct = Math.max(0, 100 - (elapsed / dur) * 100);
            progressEl.style.width = pct + '%';
            if (pct > 0) animationId = requestAnimationFrame(step);
            else removeToast(toast);
        }
        animationId = requestAnimationFrame(step);
    }
    toast.addEventListener('click', function() { removeToast(toast); });
    var closeBtn = toast.querySelector('button');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            removeToast(toast);
        });
    }
    toastContainer.appendChild(toast);
}

function showStatus(message, type) {
    if (type === void 0) type = 'info';
    showToast(message, type);
}

// ============================================================
// 暗色模式
// ============================================================
var DARK_KEY = 'ac-detect-theme';

function applyTheme(mode) {
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var isDark = mode === 'dark' || (mode === 'auto' && prefersDark);
    document.documentElement.classList.toggle('dark', isDark);
    updateToggleIcon(isDark, mode);
}

function updateToggleIcon(isDark, mode) {
    var lightIcon = document.getElementById('theme-icon-light');
    var darkIcon = document.getElementById('theme-icon-dark');
    var autoIcon = document.getElementById('theme-icon-auto');
    if (!lightIcon || !darkIcon || !autoIcon) return;
    lightIcon.classList.add('hidden');
    darkIcon.classList.add('hidden');
    autoIcon.classList.add('hidden');
    if (mode === 'auto') autoIcon.classList.remove('hidden');
    else if (isDark) darkIcon.classList.remove('hidden');
    else lightIcon.classList.remove('hidden');
}

function cycleTheme() {
    var current = localStorage.getItem(DARK_KEY) || 'auto';
    var order = ['auto', 'light', 'dark'];
    var next = order[(order.indexOf(current) + 1) % order.length];
    localStorage.setItem(DARK_KEY, next);
    applyTheme(next);
    var labels = { auto: '已切换至跟随系统主题', light: '已切换至浅色模式', dark: '已切换至深色模式' };
    showToast(labels[next], 'info', 2000);
}

// 初始化主题
var savedTheme = localStorage.getItem(DARK_KEY) || 'auto';
applyTheme(savedTheme);
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function() {
    applyTheme(localStorage.getItem(DARK_KEY) || 'auto');
});

// ============================================================
// Tab 导航
// ============================================================
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
    });
    document.querySelectorAll('.tab-panel').forEach(function(panel) {
        panel.classList.remove('active');
    });
    var btn = document.getElementById('tab-btn-' + tabName);
    var panel = document.getElementById('tab-' + tabName);
    if (btn) { btn.classList.add('active'); btn.setAttribute('aria-selected', 'true'); }
    if (panel) { panel.classList.add('active'); }
    if (tabName === 'archive') { loadArchive(); }
}

document.querySelectorAll('.tab-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
        switchTab(this.getAttribute('data-tab').replace('tab-', ''));
    });
});

// ============================================================
// 分数计数器动画
// ============================================================
function animateCounter(element, target, duration, suffix) {
    if (duration === void 0) duration = 1000;
    if (suffix === void 0) suffix = '';
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        element.innerHTML = Math.round(target) + suffix;
        return;
    }
    var initialVal = parseFloat(element.textContent) || 0;
    var start = performance.now();
    function step(now) {
        var elapsed = now - start;
        var progress = Math.min(elapsed / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        var current = initialVal + (target - initialVal) * eased;
        element.innerHTML = Math.round(current) + suffix;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ============================================================
// 获取统一姓名
// ============================================================
function getEnrollName() {
    return document.getElementById('enroll-name').value.trim();
}

// ============================================================
// 庆祝五彩纸屑
// ============================================================
function celebrateIfAllowed() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var canvas = document.getElementById('confetti-canvas');
    canvas.style.display = 'block';
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    var ctx = canvas.getContext('2d');
    var colors = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];
    var particles = [];
    for (var i = 0; i < 80; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height - canvas.height,
            w: Math.random() * 10 + 4,
            h: Math.random() * 6 + 3,
            color: colors[Math.floor(Math.random() * colors.length)],
            vy: Math.random() * 3 + 1.5,
            vx: (Math.random() - 0.5) * 2,
            rotation: Math.random() * 360,
            rv: (Math.random() - 0.5) * 6
        });
    }
    var animId;
    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        var alive = false;
        particles.forEach(function(p) {
            p.y += p.vy;
            p.x += p.vx;
            p.rotation += p.rv;
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.rotation * Math.PI / 180);
            ctx.fillStyle = p.color;
            ctx.fillRect(-p.w / 2, -p.h / 2, p.w, p.h);
            ctx.restore();
            if (p.y < canvas.height + 50) alive = true;
        });
        if (alive) animId = requestAnimationFrame(draw);
        else { canvas.style.display = 'none'; cancelAnimationFrame(animId); }
    }
    animId = requestAnimationFrame(draw);
}
