import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import os
import time
import random
import database  # Veritabanı modülümüz (database.py)
from datetime import datetime

# ==========================================
# 1. SAYFA VE GENEL AYARLAR
# ==========================================
st.set_page_config(
    page_title="Bağarası ÇPAL - Dijital Kampüs",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Veritabanını başlat
database.create_database()
# İlk kullanımda admin yoksa oluşturur
if not database.login_user("admin", "6626"):
    database.add_user("admin", "6626", "admin")

# ==========================================
# 2. SABİTLER VE HTML OYUN KODLARI
# ==========================================
GITHUB_USER = "zulfikarsitaci-prog"
GITHUB_REPO = "s-navkamp-"
GITHUB_BRANCH = "main"
GITHUB_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"

URL_LIFESIM = f"{GITHUB_BASE_URL}/lifesim_data.json"
URL_TYT_DATA = f"{GITHUB_BASE_URL}/tyt_data.json"
URL_TYT_PDF = f"{GITHUB_BASE_URL}/tytson8.pdf"
URL_MESLEK_SORULAR = f"{GITHUB_BASE_URL}/sorular.json"

# --- OYUN 1: FINANS İMPARATORU (Tam Kod) ---
FINANCE_GAME_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap');
    body { background-color: #0f172a; color: #e2e8f0; font-family: 'Montserrat', sans-serif; user-select: none; padding: 10px; text-align: center; margin: 0; }
    .container { width: 100%; max-width: 100%; box-sizing: border-box; overflow-x: hidden; }
    .dashboard { display: flex; flex-wrap: wrap; justify-content: space-between; background: linear-gradient(145deg, #1e293b, #0f172a); padding: 15px; border-radius: 12px; border: 1px solid #334155; margin-bottom: 20px; gap: 10px; }
    .stat-box { text-align: left; flex: 1; min-width: 120px; }
    .stat-label { font-size: 9px; color: #94a3b8; letter-spacing: 1px; }
    .money-val { font-size: 22px; font-weight: 900; color: #34d399; }
    .income-val { font-size: 16px; font-weight: 700; color: #facc15; }
    .clicker-btn { background: radial-gradient(circle, #3b82f6 0%, #1d4ed8 100%); border: 4px solid #1e3a8a; border-radius: 50%; width: 110px; height: 110px; font-size: 30px; cursor: pointer; box-shadow: 0 0 20px rgba(59, 130, 246, 0.4); margin: 0 auto 20px auto; display: flex; align-items: center; justify-content: center; transition: transform 0.1s; }
    .clicker-btn:active { transform: scale(0.95); }
    .asset-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px; margin-bottom: 20px; }
    .asset-card { background: #1e293b; padding: 10px; border-radius: 8px; border: 1px solid #334155; cursor: pointer; position: relative; transition: 0.2s; text-align: left; }
    .asset-card:hover { border-color: #facc15; background: #253347; }
    .asset-card.locked { opacity: 0.5; filter: grayscale(1); pointer-events: none; }
    .asset-name { font-weight: bold; font-size: 10px; color: #fff; display: block; margin-bottom: 2px;}
    .asset-cost { font-size: 10px; color: #f87171; font-weight: bold; }
    .asset-gain { font-size: 9px; color: #34d399; }
    .asset-count { position: absolute; top: 5px; right: 5px; background: #facc15; color: #000; font-weight: bold; font-size: 9px; padding: 1px 5px; border-radius: 4px; }
    .bank-area { margin-top: 10px; text-align: center; }
    .bank-btn { background: #10b981; color: #fff; border: none; padding: 8px 20px; font-weight: bold; border-radius: 6px; cursor: pointer; font-size: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: 0.2s; }
    .bank-btn:hover { background: #059669; }
    .code-display { background: #fff; color: #000; padding: 5px; margin-top: 5px; font-family: monospace; font-weight: bold; display: none; font-size: 12px; border-radius: 4px; width: 100%; box-sizing: border-box;}
</style>
</head>
<body>
<div class="container">
    <div class="dashboard">
        <div class="stat-box"><div class="stat-label">NAKİT VARLIK</div><div id="money" class="money-val">0 ₺</div></div>
        <div class="stat-box" style="text-align:right;"><div class="stat-label">PASİF GELİR</div><div id="cps" class="income-val">0.0 /sn</div></div>
    </div>
    <div class="clicker-btn" onclick="manualWork()">👆</div>
    <div style="text-align:left; color:#facc15; font-size:12px; font-weight:bold; margin-bottom:5px;">YATIRIM PORTFÖYÜ</div>
    <div class="asset-grid" id="market"></div>
    <div class="bank-area"><button class="bank-btn" onclick="generateCode()">🏦 Bankaya Aktar</button><div id="transferCode" class="code-display"></div></div>
</div>
<script>
    let money = 0;
    const assets = [
        { name: "Limonata", cost: 150, gain: 0.5, count: 0 }, { name: "Simit Tezgahı", cost: 1000, gain: 3.5, count: 0 },
        { name: "Kantin", cost: 5000, gain: 15.0, count: 0 }, { name: "Kırtasiye", cost: 20000, gain: 55.0, count: 0 },
        { name: "Yazılım Ofisi", cost: 80000, gain: 200.0, count: 0 }, { name: "E-Ticaret", cost: 250000, gain: 750.0, count: 0 },
        { name: "Fabrika", cost: 1000000, gain: 3500.0, count: 0 }, { name: "Kripto Madeni", cost: 5000000, gain: 15000.0, count: 0 },
        { name: "Uzay İstasyonu", cost: 50000000, gain: 200000.0, count: 0 }
    ];
    function updateUI() {
        document.getElementById('money').innerText = Math.floor(money).toLocaleString() + ' ₺';
        let totalCps = assets.reduce((t, a) => t + (a.count * a.gain), 0);
        document.getElementById('cps').innerText = totalCps.toFixed(1) + ' /sn';
        const market = document.getElementById('market'); market.innerHTML = '';
        assets.forEach((asset, index) => {
            let currentCost = Math.floor(asset.cost * Math.pow(1.2, asset.count));
            let div = document.createElement('div');
            div.className = 'asset-card ' + (money >= currentCost ? '' : 'locked');
            div.onclick = () => buyAsset(index);
            div.innerHTML = `<div class="asset-count">${asset.count}</div><div class="asset-name">${asset.name}</div><div class="asset-cost">${currentCost.toLocaleString()} ₺</div><div class="asset-gain">+${asset.gain}/sn</div>`;
            market.appendChild(div);
        });
    }
    function manualWork() { money += 1; updateUI(); }
    function buyAsset(index) {
        let asset = assets[index]; let currentCost = Math.floor(asset.cost * Math.pow(1.2, asset.count));
        if (money >= currentCost) { money -= currentCost; asset.count++; updateUI(); }
    }
    function generateCode() {
        if (money < 100) { alert("En az 100 ₺ birikmeli."); return; }
        let val = Math.floor(money); let hex = (val * 13).toString(16).toUpperCase(); 
        let rnd = Math.floor(Math.random() * 9999);
        let code = `FNK-${hex}-${rnd}`;
        let box = document.getElementById('transferCode'); box.innerText = code; box.style.display = 'block'; money = 0; updateUI();
    }
    setInterval(() => { let totalCps = assets.reduce((t, a) => t + (a.count * a.gain), 0); if (totalCps > 0) { money += totalCps; updateUI(); } }, 1000);
    updateUI();
</script>
</body>
</html>
"""

# --- OYUN 2: ASSET MATRIX (Tam Kod) ---
ASSET_MATRIX_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Socratic Asset Matrix</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;700;900&display=swap');
        body { margin: 0; overflow: hidden; background-color: #050505; font-family: 'Montserrat', sans-serif; color: #fff; touch-action: none; }
        #game-container { position: relative; width: 100vw; height: 100vh; display: flex; flex-direction: column; justify-content: flex-start; align-items: center; background: radial-gradient(circle at center, #1a1a1a 0%, #000000 100%); padding-top: 15px; box-sizing: border-box; }
        .header { text-align: center; margin-bottom: 10px; z-index: 2; }
        .score-label { font-size: 11px; color: #aaa; letter-spacing: 1px; text-transform: uppercase; }
        #score { font-size: 32px; font-weight: 900; color: #fff; text-shadow: 0 0 10px rgba(255, 255, 255, 0.2); transition: color 0.5s; }
        #level-indicator { font-size: 10px; margin-top: 2px; opacity: 0.7; color: #FFD700; transition: color 0.5s; }
        canvas { box-shadow: 0 0 30px rgba(0, 0, 0, 0.9); border-radius: 4px; border: 1px solid #222; background: #080808; touch-action: none; }
        .menu-screen { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.96); display: flex; flex-direction: column; justify-content: center; align-items: center; z-index: 20; transition: opacity 0.3s; padding: 20px; box-sizing: border-box; text-align: center; }
        .hidden { opacity: 0; pointer-events: none; z-index: -1; }
        h1 { font-size: 2rem; text-transform: uppercase; letter-spacing: -1px; margin-bottom: 10px; }
        h1 span { color: #FFD700; }
        p { color: #888; margin-bottom: 20px; font-size: 0.9rem; max-width: 600px; line-height: 1.5; }
        .btn { background: linear-gradient(45deg, #333, #111); border: 1px solid #444; padding: 12px 35px; font-size: 16px; font-weight: 700; color: #fff; text-transform: uppercase; cursor: pointer; border-radius: 4px; font-family: 'Montserrat', sans-serif; transition: all 0.2s; margin-top: 10px; }
        .btn:hover { background: #444; border-color: #FFD700; color: #FFD700; }
        .bank-btn-overlay { position:absolute; top:10px; right:10px; z-index:100; }
        .mini-btn { background:#38bdf8; border:none; padding:5px 10px; border-radius:4px; font-size:10px; font-weight:bold; cursor:pointer; color:#000; }
        #bankCodeDisplay { position:absolute; top:40px; right:10px; background:white; color:black; padding:5px; font-size:12px; font-weight:bold; display:none; z-index:101; border-radius:4px;}
        .quiz-box { background: #111; border: 1px solid #333; padding: 30px; border-radius: 8px; max-width: 500px; box-shadow: 0 0 50px rgba(255, 215, 0, 0.1); }
        .quiz-question { font-size: 1.2rem; color: #fff; margin-bottom: 20px; font-weight: 700; }
        .quiz-option { display: block; width: 100%; padding: 15px; margin: 10px 0; background: #222; border: 1px solid #333; color: #ccc; cursor: pointer; transition: 0.3s; text-align: left; border-radius: 4px; }
        .quiz-option:hover { background: #333; border-color: #666; }
        .feedback-msg { margin-top: 15px; font-style: italic; color: #FFD700; min-height: 40px; }
        .hap-bilgi-list { text-align: left; background: #111; padding: 20px; border-radius: 8px; border-left: 4px solid #FFD700; margin-bottom: 20px; font-size: 0.85rem; color: #ddd; }
        .hap-bilgi-list li { margin-bottom: 8px; }
    </style>
</head>
<body>
    <div id="game-container">
        <div class="bank-btn-overlay"><button class="mini-btn" onclick="getTransferCode()">🏦 BANKAYA AKTAR</button></div>
        <div id="bankCodeDisplay"></div>
        <div class="header">
            <div class="score-label">Net Varlık Değeri</div>
            <div id="score">$0</div>
            <div id="level-indicator">SEVİYE: BAŞLANGIÇ</div>
        </div>
        <canvas id="gameCanvas"></canvas>
        <div id="startScreen" class="menu-screen">
            <h1>Socratic <span>Matrix</span></h1>
            <p>Finansal piyasalar karmaşıktır. Blokları yönet, varlıklarını artır.</p>
            <button class="btn" onclick="initGame()">Simülasyonu Başlat</button>
        </div>
        <div id="quizScreen" class="menu-screen hidden">
            <div class="quiz-box">
                <div id="quizQuestion" class="quiz-question">Soru</div>
                <div id="quizOptions"></div>
                <div id="quizFeedback" class="feedback-msg"></div>
            </div>
        </div>
        <div id="gameOverScreen" class="menu-screen hidden">
            <h1 style="color: #ff4444;">LİKİDİTE KRİZİ</h1>
            <p>Piyasa kilitlendi.</p>
            <div class="hap-bilgi-list"><strong style="display:block; margin-bottom:10px; color:#FFD700;">GÜNÜN HAP BİLGİLERİ:</strong><ul id="takeawayList"></ul></div>
            <p>Son Değer: <span id="finalScore" style="color:#fff; font-weight:bold;">$0</span></p>
            <button class="btn" onclick="initGame()">Yeniden Dene</button>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('gameCanvas'); const ctx = canvas.getContext('2d');
        const scoreEl = document.getElementById('score'); const finalScoreEl = document.getElementById('finalScore');
        const levelEl = document.getElementById('level-indicator'); const startScreen = document.getElementById('startScreen');
        const gameOverScreen = document.getElementById('gameOverScreen'); const quizScreen = document.getElementById('quizScreen');
        const quizQuestionEl = document.getElementById('quizQuestion'); const quizOptionsEl = document.getElementById('quizOptions');
        const quizFeedbackEl = document.getElementById('quizFeedback'); const takeawayListEl = document.getElementById('takeawayList');
        const GRID_SIZE = 8; let CELL_SIZE = 30; let BOARD_OFFSET_X = 0; let BOARD_OFFSET_Y = 0;
        const THEMES = [{ name: "GOLD (Birikim)", start: '#FFD700', end: '#C5A028' }, { name: "PURPLE (Kaldıraç)", start: '#D500F9', end: '#7B1FA2' }, { name: "ROSE (Volatilite)", start: '#E0BFB8', end: '#B76E79' }];
        let currentLevel = 0; let levelThreshold = 30; 
        const QUESTIONS = [
            { q: "Varlığını nakde çevirme yeteneğine ne denir?", opts: ["A) Pasif Yatırım", "B) Likidite", "C) Enflasyon"], correct: 1, wrongFeedback: ["Yanlış.", "", "Yanlış."], successMsg: "Doğru! Likidite hayattır." },
            { q: "Tek büyük blok risklidir. Neden?", opts: ["A) Konsantrasyon Riski", "B) Piyasa Hızı", "C) Blok Rengi"], correct: 0, wrongFeedback: ["", "Değil.", "Değil."], successMsg: "Doğru! Çeşitlendirme yapmalısın." },
            { q: "Küçük yatırımların katlanarak büyümesi nedir?", opts: ["A) Devalüasyon", "B) Bileşik Getiri", "C) Arbitraj"], correct: 1, wrongFeedback: ["Değil.", "", "Değil."], successMsg: "Doğru! Dünyanın 8. harikası." }
        ];
        const TAKEAWAYS = ["LİKİDİTE HAYATTIR.", "ÇEŞİTLENDİRME RİSKİ AZALTIR.", "ZAMANLAMA HER ŞEYDİR."];
        let grid = [], score = 0, availablePieces = [], draggingPiece = null, isGameOver = false, isPaused = false, questionIndex = 0;
        function resize() {
            const maxWidth = window.innerWidth * 0.95; const maxHeight = window.innerHeight * 0.85; 
            let size = Math.min(maxWidth, maxHeight * 0.75); CELL_SIZE = Math.floor(size / GRID_SIZE);
            canvas.width = CELL_SIZE * GRID_SIZE + 20; canvas.height = CELL_SIZE * GRID_SIZE + 130; 
            BOARD_OFFSET_X = 10; BOARD_OFFSET_Y = 10;
            if (!isGameOver && availablePieces.length > 0) draw();
        }
        window.addEventListener('resize', resize);
        function initGame() {
            grid = Array(GRID_SIZE).fill(0).map(() => Array(GRID_SIZE).fill(0));
            score = 0; currentLevel = 0; questionIndex = 0; isGameOver = false; isPaused = false;
            updateScore(0); updateTheme();
            startScreen.classList.add('hidden'); gameOverScreen.classList.add('hidden'); quizScreen.classList.add('hidden');
            generateNewPieces(); resize(); draw();
        }
        function triggerQuiz() {
            if (questionIndex >= QUESTIONS.length) return;
            isPaused = true; quizScreen.classList.remove('hidden');
            const qData = QUESTIONS[questionIndex];
            quizQuestionEl.innerText = qData.q; quizFeedbackEl.innerText = ""; quizOptionsEl.innerHTML = "";
            qData.opts.forEach((opt, idx) => {
                const btn = document.createElement('div'); btn.className = 'quiz-option'; btn.innerText = opt;
                btn.onclick = () => handleQuizAnswer(idx, qData); quizOptionsEl.appendChild(btn);
            });
        }
        function handleQuizAnswer(idx, qData) {
            if (idx === qData.correct) {
                quizFeedbackEl.style.color = "#44ff44"; quizFeedbackEl.innerText = qData.successMsg;
                setTimeout(() => { quizScreen.classList.add('hidden'); isPaused = false; questionIndex++; draw(); }, 2000);
            } else { quizFeedbackEl.style.color = "#ffaa44"; quizFeedbackEl.innerText = qData.wrongFeedback[idx]; }
        }
        const SHAPES = [[[1]], [[1, 1]], [[1], [1]], [[1, 1, 1]], [[1], [1], [1]], [[1, 1], [1, 1]], [[1, 1, 1], [0, 1, 0]], [[1, 0], [1, 0], [1, 1]], [[1, 1, 1, 1]]];
        function generateNewPieces() {
            availablePieces = [];
            for (let i = 0; i < 3; i++) {
                const shapeMatrix = SHAPES[Math.floor(Math.random() * SHAPES.length)];
                const spawnY = BOARD_OFFSET_Y + GRID_SIZE * CELL_SIZE + 20;
                const spawnX = BOARD_OFFSET_X + (canvas.width / 6) + (i * (canvas.width / 3.2)) - (CELL_SIZE); 
                availablePieces.push({ matrix: shapeMatrix, x: spawnX, y: spawnY, baseX: spawnX, baseY: spawnY, width: shapeMatrix[0].length * CELL_SIZE, height: shapeMatrix.length * CELL_SIZE, isDragging: false });
            }
            if (checkGameOverState()) gameOver();
        }
        function updateScore(points) {
            let oldScore = score; score += points; scoreEl.innerText = "$" + score; 
            let oldLevel = Math.floor(oldScore / levelThreshold); let newLevel = Math.floor(score / levelThreshold);
            if (newLevel > oldLevel) { currentLevel = newLevel; updateTheme(); triggerQuiz(); }
        }
        function updateTheme() {
            const theme = THEMES[currentLevel % THEMES.length];
            levelEl.innerText = "SEVİYE: " + theme.name; levelEl.style.color = theme.start; scoreEl.style.color = theme.start;
            if(!isGameOver) draw();
        }
        function draw() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            drawGrid(); drawPlacedBlocks(); drawAvailablePieces();
        }
        function drawGrid() {
            ctx.lineWidth = 2; ctx.strokeStyle = '#666'; ctx.beginPath();
            for (let i = 0; i <= GRID_SIZE; i++) {
                ctx.moveTo(BOARD_OFFSET_X, BOARD_OFFSET_Y + i * CELL_SIZE); ctx.lineTo(BOARD_OFFSET_X + GRID_SIZE * CELL_SIZE, BOARD_OFFSET_Y + i * CELL_SIZE);
                ctx.moveTo(BOARD_OFFSET_X + i * CELL_SIZE, BOARD_OFFSET_Y); ctx.lineTo(BOARD_OFFSET_X + i * CELL_SIZE, BOARD_OFFSET_Y + GRID_SIZE * CELL_SIZE);
            }
            ctx.stroke();
        }
        function drawCell(x, y, size, isPreview = false) {
             const theme = THEMES[currentLevel % THEMES.length];
             const gradient = ctx.createLinearGradient(x, y, x + size, y + size);
             if(isPreview) { gradient.addColorStop(0, hexToRgbA(theme.start, 0.4)); gradient.addColorStop(1, hexToRgbA(theme.end, 0.4)); } 
             else { gradient.addColorStop(0, theme.start); gradient.addColorStop(1, theme.end); }
            ctx.fillStyle = gradient; ctx.fillRect(x + 1, y + 1, size - 2, size - 2);
            ctx.strokeStyle = "rgba(255,255,255,0.7)"; ctx.lineWidth = 2; ctx.strokeRect(x + 1, y + 1, size - 2, size - 2);
        }
        function hexToRgbA(hex, alpha){
            let c; if(/^#([A-Fa-f0-9]{3}){1,2}$/.test(hex)){ c= hex.substring(1).split(''); if(c.length== 3){ c= [c[0], c[0], c[1], c[1], c[2], c[2]]; } c= '0x'+c.join(''); return 'rgba('+[(c>>16)&255, (c>>8)&255, c&255].join(',')+','+alpha+')'; } return hex;
        }
        function drawPlacedBlocks() {
            for (let row = 0; row < GRID_SIZE; row++) for (let col = 0; col < GRID_SIZE; col++) if (grid[row][col] === 1) drawCell(BOARD_OFFSET_X + col * CELL_SIZE, BOARD_OFFSET_Y + row * CELL_SIZE, CELL_SIZE);
        }
        function drawAvailablePieces() {
            availablePieces.forEach(piece => { if (piece.isDragging) return; drawShape(piece.matrix, piece.x, piece.y, CELL_SIZE * 0.5); });
            if (draggingPiece) {
                drawShape(draggingPiece.matrix, draggingPiece.x, draggingPiece.y, CELL_SIZE);
                const { gridX, gridY } = getGridCoordsFromMouse(draggingPiece.x, draggingPiece.y);
                if (canPlace(draggingPiece.matrix, gridX, gridY)) drawShape(draggingPiece.matrix, BOARD_OFFSET_X + gridX * CELL_SIZE, BOARD_OFFSET_Y + gridY * CELL_SIZE, CELL_SIZE, true);
            }
        }
        function drawShape(matrix, startX, startY, cellSize, isPreview = false) {
            for (let row = 0; row < matrix.length; row++) for (let col = 0; col < matrix[row].length; col++) if (matrix[row][col] === 1) drawCell(startX + col * cellSize, startY + row * cellSize, cellSize, isPreview);
        }
        function canPlace(matrix, gridX, gridY) {
            for (let row = 0; row < matrix.length; row++) for (let col = 0; col < matrix[row].length; col++) if (matrix[row][col] === 1) {
                let targetX = gridX + col; let targetY = gridY + row;
                if (targetX < 0 || targetX >= GRID_SIZE || targetY < 0 || targetY >= GRID_SIZE || grid[targetY][targetX] === 1) return false;
            }
            return true;
        }
        function placePiece(matrix, gridX, gridY) {
            for (let row = 0; row < matrix.length; row++) for (let col = 0; col < matrix[row].length; col++) if (matrix[row][col] === 1) grid[gridY + row][gridX + col] = 1;
            updateScore(1); checkAndClearLines();
        }
        function checkAndClearLines() {
            let rowsToClear = [], colsToClear = [];
            for (let row = 0; row < GRID_SIZE; row++) if (grid[row].every(cell => cell === 1)) rowsToClear.push(row);
            for (let col = 0; col < GRID_SIZE; col++) { let full = true; for (let row = 0; row < GRID_SIZE; row++) if (grid[row][col] === 0) { full = false; break; } if (full) colsToClear.push(col); }
            rowsToClear.forEach(row => { for (let col = 0; col < GRID_SIZE; col++) grid[row][col] = 0; });
            colsToClear.forEach(col => { for (let row = 0; row < GRID_SIZE; row++) grid[row][col] = 0; });
            if (rowsToClear.length + colsToClear.length > 0) updateScore((rowsToClear.length + colsToClear.length) * 10);
        }
        function checkGameOverState() {
            if (availablePieces.length === 0) return false;
            for (let i = 0; i < availablePieces.length; i++) {
                const matrix = availablePieces[i].matrix;
                for (let row = 0; row < GRID_SIZE; row++) for (let col = 0; col < GRID_SIZE; col++) if (canPlace(matrix, col, row)) return false;
            }
            return true;
        }
        function gameOver() {
            isGameOver = true; finalScoreEl.innerText = scoreEl.innerText;
            takeawayListEl.innerHTML = "";
            TAKEAWAYS.forEach(item => { let li = document.createElement('li'); li.innerText = item; takeawayListEl.appendChild(li); });
            gameOverScreen.classList.remove('hidden');
        }
        let dragOffsetX = 0, dragOffsetY = 0;
        function getEventPos(e) {
            const rect = canvas.getBoundingClientRect();
            let clientX = e.clientX, clientY = e.clientY;
            if (e.touches && e.touches.length > 0) { clientX = e.touches[0].clientX; clientY = e.touches[0].clientY; }
            return { x: clientX - rect.left, y: clientY - rect.top };
        }
        function getGridCoordsFromMouse(pieceX, pieceY) {
            let rawGridX = Math.round((pieceX - BOARD_OFFSET_X) / CELL_SIZE);
            let rawGridY = Math.round((pieceY - BOARD_OFFSET_Y) / CELL_SIZE);
            return { gridX: rawGridX, gridY: rawGridY };
        }
        function handleStart(e) {
            if(isGameOver || isPaused) return; e.preventDefault(); const pos = getEventPos(e);
            for (let i = availablePieces.length - 1; i >= 0; i--) {
                const p = availablePieces[i];
                const renderSize = CELL_SIZE * 0.5; const pWidth = p.matrix[0].length * renderSize; const pHeight = p.matrix.length * renderSize;
                if (pos.x > p.x - 10 && pos.x < p.x + pWidth + 10 && pos.y > p.y - 10 && pos.y < p.y + pHeight + 10) {
                    draggingPiece = p; p.isDragging = true;
                    dragOffsetX = pos.x - p.x; dragOffsetY = pos.y - p.y;
                    dragOffsetX = (dragOffsetX / renderSize) * CELL_SIZE; dragOffsetY = (dragOffsetY / renderSize) * CELL_SIZE;
                    draw(); return;
                }
            }
        }
        function handleMove(e) {
            if (!draggingPiece) return; e.preventDefault(); const pos = getEventPos(e);
            draggingPiece.x = pos.x - dragOffsetX; draggingPiece.y = pos.y - dragOffsetY; draw();
        }
        function handleEnd(e) {
            if (!draggingPiece) return; e.preventDefault();
            const { gridX, gridY } = getGridCoordsFromMouse(draggingPiece.x, draggingPiece.y);
            if (canPlace(draggingPiece.matrix, gridX, gridY)) {
                placePiece(draggingPiece.matrix, gridX, gridY);
                availablePieces = availablePieces.filter(p => p !== draggingPiece);
                if (availablePieces.length === 0) generateNewPieces(); else if(checkGameOverState()) gameOver();
            } else { draggingPiece.x = draggingPiece.baseX; draggingPiece.y = draggingPiece.baseY; draggingPiece.isDragging = false; }
            draggingPiece = null; draw();
        }
        function getTransferCode() {
            if(score < 50) { alert("En az 50 puan gerekli."); return; }
            let val = score; let hex = (val * 13).toString(16).toUpperCase(); 
            let rnd = Math.floor(Math.random() * 9999);
            let code = `FNK-${hex}-${rnd}`;
            document.getElementById('bankCodeDisplay').innerText = code; document.getElementById('bankCodeDisplay').style.display = 'block';
            score = 0; updateScore(0); draw();
        }
        canvas.addEventListener('mousedown', handleStart); canvas.addEventListener('mousemove', handleMove); canvas.addEventListener('mouseup', handleEnd); canvas.addEventListener('mouseleave', handleEnd);
        canvas.addEventListener('touchstart', handleStart, { passive: false }); canvas.addEventListener('touchmove', handleMove, { passive: false }); canvas.addEventListener('touchend', handleEnd, { passive: false });
        resize();
    </script>
</body>
</html>
"""

# ==========================================
# 3. SERVER VE YARDIMCI FONKSİYONLAR
# ==========================================
@st.cache_resource
class SchoolServer:
    def __init__(self):
        # class_code -> { username: points }
        self.classes = {} 
        self.used_codes = set()
        self.create_class("GENEL")

    def create_class(self, class_code):
        if class_code not in self.classes:
            self.classes[class_code] = {}
        return True

    def join_or_update_student(self, class_code, username, points_to_add=0):
        if class_code not in self.classes:
            self.create_class(class_code)
        
        if username not in self.classes[class_code]:
            self.classes[class_code][username] = 0
        
        self.classes[class_code][username] += points_to_add
        return self.classes[class_code][username]

    def get_score(self, class_code, username):
        if class_code in self.classes and username in self.classes[class_code]:
            return self.classes[class_code][username]
        return 0

    def redeem_code(self, class_code, username, code_string):
        if code_string in self.used_codes:
            return False, "Bu kod kullanılmış!"
        try:
            parts = code_string.split('-')
            if len(parts) != 3 or parts[0] != "FNK": return False, "Geçersiz kod!"
            hex_val = parts[1]
            amount = int(int(hex_val, 16) / 13)
            self.used_codes.add(code_string)
            new_balance = self.join_or_update_student(class_code, username, amount)
            return True, new_balance
        except: return False, "Hata oluştu."

    def get_leaderboard(self, class_code):
        if class_code in self.classes:
            data = [{"Öğrenci": k, "Puan": v} for k, v in self.classes[class_code].items()]
            if data:
                return pd.DataFrame(data).sort_values(by="Puan", ascending=False)
        return pd.DataFrame()

server = SchoolServer()

@st.cache_data(ttl=300)
def fetch_json_data(url):
    try:
        r = requests.get(url)
        return r.json() if r.status_code == 200 else {}
    except: return {}

def load_lifesim():
    try:
        # Önce lokal dosyaya bak (varsa)
        if os.path.exists("game.html"):
             with open("game.html", "r", encoding="utf-8") as f: html = f.read()
        else:
             r = requests.get(f"{GITHUB_BASE_URL}/game.html")
             html = r.text if r.status_code == 200 else "<h3>Yüklenemedi</h3>"
        
        data = fetch_json_data(URL_LIFESIM)
        json_str = json.dumps(data if data else [])
        return html.replace("// PYTHON_DATA_HERE", f"var scenarios = {json_str};")
    except: return "Hata"

# ==========================================
# 4. ARAYÜZ MANTIĞI
# ==========================================

# Oturum Kontrolleri
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user_role" not in st.session_state: st.session_state.user_role = None
if "username" not in st.session_state: st.session_state.username = None
if "class_code" not in st.session_state: st.session_state.class_code = "GENEL"

# --- GİRİŞ EKRANI (TEK VE ORTAK) ---
if not st.session_state.logged_in:
    st.markdown("""
    <div style="text-align: center; padding: 20px;">
        <h1>🎓 Bağarası ÇPAL</h1>
        <h3>Dijital Kampüs Girişi</h3>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_master"):
            user_inp = st.text_input("Kullanıcı Adı / Okul No")
            pass_inp = st.text_input("Şifre", type="password")
            submitted = st.form_submit_button("Giriş Yap", use_container_width=True)
            
            if submitted:
                user = database.login_user(user_inp, pass_inp)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_role = user[3] # admin, teacher, student
                    st.session_state.username = user[1]
                    
                    # Öğrenciyse başlangıç puanını server'a tanıt
                    if user[3] == "student":
                        server.join_or_update_student("GENEL", user[1], 0)
                        
                    st.success("Giriş Başarılı!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
        
        st.info("Hesabınız yoksa yöneticinizle iletişime geçin.")

# --- İÇERİK EKRANLARI (ROL TABANLI) ---
else:
    # Sidebar: Kullanıcı Bilgisi ve Çıkış
    with st.sidebar:
        st.write(f"👤 **{st.session_state.username}**")
        st.caption(f"Yetki: {st.session_state.user_role.upper()}")
        
        # Öğrenciyse sınıf kodu değiştirme
        if st.session_state.user_role == "student":
            st.divider()
            code_input = st.text_input("Sınıf Kodu Gir", placeholder="Örn: 1234")
            if st.button("Sınıfa Geç"):
                st.session_state.class_code = code_input
                server.join_or_update_student(code_input, st.session_state.username)
                st.success(f"Sınıf: {code_input}")
                st.rerun()
        
        st.divider()
        if st.button("Çıkış Yap", type="primary"):
            st.session_state.logged_in = False
            st.rerun()

    # ----------------------------------------
    # SENARYO 1: ADMIN (YÖNETİM PANELİ)
    # ----------------------------------------
    if st.session_state.user_role == "admin":
        st.header("⚙️ Yönetici Paneli")
        
        tab1, tab2 = st.tabs(["Kullanıcı Ekle", "Kullanıcı Listesi"])
        with tab1:
            st.subheader("Yeni Hesap Oluştur")
            with st.form("add_user"):
                u_name = st.text_input("Kullanıcı Adı (Örn: ali123)")
                u_pass = st.text_input("Şifre")
                u_role = st.selectbox("Rol", ["student", "teacher", "admin"])
                if st.form_submit_button("Kaydet"):
                    if database.add_user(u_name, u_pass, u_role):
                        st.success("Kullanıcı oluşturuldu.")
                    else:
                        st.error("Bu kullanıcı zaten var.")
        
        with tab2:
            st.subheader("Kayıtlı Kullanıcılar")
            users = database.get_all_users()
            df = pd.DataFrame(users, columns=["Kullanıcı", "Rol"])
            st.dataframe(df, use_container_width=True)
            
            to_del = st.selectbox("Silinecek Kişi", df["Kullanıcı"])
            if st.button("Sil"):
                if to_del != "admin":
                    database.delete_user(to_del)
                    st.rerun()
                else: st.error("Admin silinemez.")

    # ----------------------------------------
    # SENARYO 2: ÖĞRETMEN PANELİ
    # ----------------------------------------
    elif st.session_state.user_role == "teacher":
        st.header("👨‍🏫 Öğretmen Paneli")
        
        if "created_code" not in st.session_state:
            st.session_state.created_code = str(random.randint(1000, 9999))
            server.create_class(st.session_state.created_code)
            
        st.info(f"Aktif Ders Kodunuz: **{st.session_state.created_code}** (Öğrencilerle paylaşın)")
        
        tab1, tab2 = st.tabs(["Liderlik Tablosu", "Duyuru Ekle"])
        
        with tab1:
            st.subheader("Sınıf Sıralaması")
            if st.button("Yenile"): st.rerun()
            df = server.get_leaderboard(st.session_state.created_code)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning("Henüz bu derse katılan öğrenci yok.")
                
        with tab2:
            with st.form("ann_form"):
                baslik = st.text_input("Başlık")
                icerik = st.text_area("Mesajınız")
                if st.form_submit_button("Yayınla"):
                    database.add_announcement(baslik, icerik, st.session_state.username)
                    st.success("Duyuru gönderildi.")

    # ----------------------------------------
    # SENARYO 3: ÖĞRENCİ (DİJİTAL KAMPÜS)
    # ----------------------------------------
    elif st.session_state.user_role == "student":
        # Üst Bilgi Barı
        puan = server.get_score(st.session_state.class_code, st.session_state.username)
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            st.title(f"Merhaba, {st.session_state.username}")
        with col_b:
            st.metric("Sınıf", st.session_state.class_code)
        with col_c:
            st.metric("Kampüs Puanı", f"{puan} ₺")

        # Ana Kampüs Sekmeleri
        tab_main, tab_lessons, tab_games, tab_life = st.tabs(["🏆 Kampüs Meydanı", "📚 Dersler & Test", "🎮 Oyun Alanı", "💼 Kariyer Sim"])

        # TAB 1: MEYDAN
        with tab_main:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown("### 🏦 Puan Yükle")
                st.caption("Oyunlardan kazandığın kodu buraya gir.")
                code_in = st.text_input("Kod:", key="code_redeem")
                if st.button("Bozdur ve Yükle"):
                    status, msg = server.redeem_code(st.session_state.class_code, st.session_state.username, code_in)
                    if status:
                        st.success(f"Başarılı! Yeni Puan: {msg}")
                        time.sleep(1); st.rerun()
                    else:
                        st.error(msg)
                
                st.divider()
                st.markdown("### 📢 Duyurular")
                anns = database.get_announcements()
                if anns:
                    for a in anns:
                        with st.expander(f"{a[1]} - {a[4]}"):
                            st.write(a[2])
                else: st.info("Duyuru yok.")

            with c2:
                st.markdown("### 🏅 Sınıf Sıralaması")
                df = server.get_leaderboard(st.session_state.class_code)
                st.dataframe(df, use_container_width=True)

        # TAB 2: DERSLER VE TESTLER (Düzeltilen Kısım)
        with tab_lessons:
            t_tyt, t_meslek = st.tabs(["📘 TYT Çalışma", "📙 Meslek Soruları"])
            
            with t_tyt:
                tyt_data = fetch_json_data(URL_TYT_DATA)
                if tyt_data:
                    dersler = sorted(list(set([v.get('ders') for v in tyt_data.values() if 'ders' in v])))
                    s_ders = st.selectbox("Ders Seçiniz:", dersler)
                    s_pages = []
                    for k, v in tyt_data.items():
                        if v.get('ders') == s_ders: s_pages.append((k, v))
                    s_pages.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 999)
                    
                    if s_pages:
                        sel = st.selectbox("Sayfa Seçiniz:", s_pages, format_func=lambda x: f"Sayfa {x[0]}")
                        p_no, det = sel
                        
                        c_p, c_o = st.columns([1.5, 1])
                        with c_p:
                            st.markdown(f'<embed src="{URL_TYT_PDF}#page={p_no}" width="100%" height="800px" type="application/pdf">', unsafe_allow_html=True)
                        with c_o:
                            with st.form(f"f_{p_no}"):
                                ans = {}
                                for i, q in enumerate(det['sorular']):
                                    st.write(f"**Soru {q}**")
                                    ans[i] = st.radio(f"C{q}", ['A','B','C','D','E'], horizontal=True, key=f"rad_{p_no}_{q}", index=None)
                                if st.form_submit_button("KONTROL ET"):
                                    d = 0
                                    for i, q in enumerate(det['sorular']):
                                        if ans[i] == det['cevaplar'][i]: d += 1
                                    sc = d * 50
                                    st.success(f"{d} Doğru. +{sc} Puan")
                                    if sc > 0:
                                        server.join_or_update_student(st.session_state.class_code, st.session_state.username, sc)
                                        time.sleep(1); st.rerun()
                else:
                    st.error("TYT Verileri yüklenemedi.")

            with t_meslek:
                m_data = fetch_json_data(URL_MESLEK_SORULAR)
                if m_data:
                    root = m_data.get("KONU_TARAMA", m_data)
                    sinif = st.selectbox("Sınıf Düzeyi:", list(root.keys()))
                    if sinif:
                        ders = st.selectbox("Ders Adı:", list(root[sinif].keys()))
                        if ders:
                            test = st.selectbox("Konu:", list(root[sinif][ders].keys()))
                            if test:
                                qs = root[sinif][ders][test]
                                with st.form(f"mf_{sinif}_{ders}_{test}"):
                                    mans = {}
                                    for i, q in enumerate(qs):
                                        st.write(f"**{i+1}. {q['soru']}**")
                                        mans[i] = st.radio("Cevap:", q['secenekler'], key=f"mrad_{i}", index=None)
                                        st.divider()
                                    if st.form_submit_button("TESTİ BİTİR"):
                                        dm = 0
                                        for i, q in enumerate(qs):
                                            if mans[i] == q['cevap']: dm += 1
                                        pm = dm * 100
                                        st.success(f"{dm} Doğru. +{pm} Puan")
                                        if pm > 0:
                                            server.join_or_update_student(st.session_state.class_code, st.session_state.username, pm)
                                            time.sleep(1); st.rerun()

        # TAB 3: OYUN ALANI (Düzeltilen Kısım)
        with tab_games:
            secim = st.selectbox("Oyun Seç:", ["Finans İmparatoru", "Asset Matrix"])
            if secim == "Finans İmparatoru":
                components.html(FINANCE_GAME_HTML, height=700)
            else:
                components.html(ASSET_MATRIX_HTML, height=750)

        # TAB 4: LIFESIM (Düzeltilen Kısım)
        with tab_life:
            st.info("Hayat Simülasyonu Yükleniyor...")
            components.html(load_lifesim(), height=800, scrolling=True)
