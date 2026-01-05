import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import requests
import json
import os
import time
import random
import database # Veritabanı modülümüz
from datetime import datetime

# ==========================================
# 1. SAYFA VE GENEL AYARLAR
# ==========================================
st.set_page_config(
    page_title="Bağarası ÇPAL Platformu",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded" # Menüyü görmek için açık bıraktık
)

# Veritabanını başlat (Yönetim Sistemi İçin)
database.create_database()
database.add_user("admin", "6626", "admin")

# ==========================================
# 2. ORTAK HTML / CSS SABİTLERİ (KAMPÜS İÇİN)
# ==========================================
# Oyun kodları ve Github bağlantıları buraya global olarak tanımlanır
GITHUB_USER = "zulfikarsitaci-prog"
GITHUB_REPO = "s-navkamp-"
GITHUB_BRANCH = "main"
GITHUB_BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"

URL_LIFESIM = f"{GITHUB_BASE_URL}/lifesim_data.json"
URL_TYT_DATA = f"{GITHUB_BASE_URL}/tyt_data.json"
URL_TYT_PDF = f"{GITHUB_BASE_URL}/tytson8.pdf"
URL_MESLEK_SORULAR = f"{GITHUB_BASE_URL}/sorular.json"

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
# 3. KAMPÜS SERVER MANTIĞI
# ==========================================
@st.cache_resource
class SchoolServer:
    def __init__(self):
        # Sınıflar: { "DERS_KODU": { "OKUL_NO": {"ad": "Ali", "puan": 0} } }
        self.classes = {} 
        self.used_codes = set()
        self.create_class("GENEL")

    def create_class(self, class_code):
        if class_code not in self.classes:
            self.classes[class_code] = {}
        return True

    def join_student(self, class_code, name, school_no, start_points=0):
        if class_code in self.classes:
            current_data = self.classes[class_code].get(str(school_no))
            if current_data:
                current_points = current_data["puan"]
                final_points = max(current_points, start_points)
                self.classes[class_code][str(school_no)] = {"ad": name, "puan": final_points}
            else:
                self.classes[class_code][str(school_no)] = {"ad": name, "puan": start_points}
            return True
        return False

    def update_score(self, class_code, school_no, points):
        if class_code in self.classes and str(school_no) in self.classes[class_code]:
            self.classes[class_code][str(school_no)]["puan"] += points
            return self.classes[class_code][str(school_no)]["puan"]
        return 0
        
    def get_student_score(self, class_code, school_no):
        if class_code in self.classes and str(school_no) in self.classes[class_code]:
            return self.classes[class_code][str(school_no)]["puan"]
        return 0

    def redeem_code(self, class_code, school_no, code_string):
        if code_string in self.used_codes:
            return False, "Bu kod daha önce kullanıldı!"
        try:
            parts = code_string.split('-')
            if len(parts) != 3 or parts[0] != "FNK": return False, "Geçersiz format!"
            hex_val = parts[1]
            amount = int(int(hex_val, 16) / 13)
            if amount <= 0: return False, "Geçersiz tutar!"
            self.used_codes.add(code_string)
            new_balance = self.update_score(class_code, school_no, amount)
            return True, new_balance
        except: return False, "Kod çözülemedi."

    def get_leaderboard(self, class_code):
        if class_code in self.classes:
            data = []
            for no, info in self.classes[class_code].items():
                data.append({"Okul No": no, "Ad Soyad": info["ad"], "Puan": info["puan"]})
            if data:
                df = pd.DataFrame(data)
                return df.sort_values(by="Puan", ascending=False).reset_index(drop=True)
        return pd.DataFrame(columns=["Sıra", "Okul No", "Ad Soyad", "Puan"])

server = SchoolServer()

# Yardımcı Fonksiyonlar
@st.cache_data(ttl=300)
def fetch_json_data(url):
    try:
        response = requests.get(url)
        if response.status_code == 200: return json.loads(response.text)
    except: pass
    return {}

def load_lifesim_html():
    try:
        # Önce lokal dosyaya bak, yoksa GitHub'dan çek
        if os.path.exists("game.html"):
            with open("game.html", "r", encoding="utf-8") as f: html = f.read()
        else:
            resp = requests.get(f"{GITHUB_BASE_URL}/game.html")
            html = resp.text if resp.status_code == 200 else "<h3>game.html bulunamadı</h3>"
        
        data = fetch_json_data(URL_LIFESIM)
        if not data: data = []
        json_str = json.dumps(data)
        return html.replace("// PYTHON_DATA_HERE", f"var scenarios = {json_str};")
    except: return "<h3>Yükleme Hatası</h3>"

# ==========================================
# 4. MODÜL 1: OKUL YÖNETİM SİSTEMİ (KLASİK)
# ==========================================
def render_management_system():
    # Session State Kontrolü (Yönetim İçin)
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False
    if "admin_role" not in st.session_state:
        st.session_state.admin_role = None

    # GİRİŞ EKRANI
    if not st.session_state.admin_logged_in:
        st.markdown("<h2 style='text-align: center;'>🏫 Yönetim Paneli Girişi</h2>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("admin_login_form"):
                username = st.text_input("Kullanıcı Adı")
                password = st.text_input("Şifre", type="password")
                submit_btn = st.form_submit_button("Giriş Yap", use_container_width=True)
                
                if submit_btn:
                    user = database.login_user(username, password)
                    if user:
                        st.session_state.admin_logged_in = True
                        st.session_state.admin_role = user[3]
                        st.session_state.admin_username = user[1]
                        st.success("Giriş yapıldı!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Hatalı bilgiler.")

    # PANEL EKRANLARI
    else:
        st.info(f"Oturum: {st.session_state.admin_username} | Yetki: {st.session_state.admin_role.upper()}")
        if st.button("Çıkış Yap (Yönetim)", type="primary"):
            st.session_state.admin_logged_in = False
            st.rerun()

        # ADMIN PANELİ
        if st.session_state.admin_role == "admin":
            st.header("🛠️ Admin Yönetim Paneli")
            tab1, tab2 = st.tabs(["Kullanıcı Ekle", "Kullanıcı Listesi & Silme"])
            with tab1:
                st.subheader("Yeni Kullanıcı Kaydı")
                col_a, col_b = st.columns(2)
                with col_a:
                    new_user = st.text_input("Kullanıcı Adı")
                    new_pass = st.text_input("Şifre", type="password")
                with col_b:
                    new_role = st.selectbox("Rol", ["admin", "teacher", "student"])
                    st.write(""); st.write("")
                    if st.button("Kullanıcıyı Kaydet"):
                        if len(new_pass) < 4: st.warning("Şifre çok kısa!")
                        else:
                            if database.add_user(new_user, new_pass, new_role): st.success(f"{new_user} eklendi.")
                            else: st.error("Kullanıcı adı zaten var.")
            with tab2:
                st.subheader("Sistemdeki Kullanıcılar")
                users = database.get_all_users()
                df = pd.DataFrame(users, columns=["Kullanıcı Adı", "Rol"])
                st.dataframe(df, use_container_width=True)
                user_to_delete = st.selectbox("Silinecek Kullanıcı", [u[0] for u in users])
                if st.button("Seçili Kullanıcıyı Sil"):
                    if user_to_delete == "admin": st.error("Ana admin hesabı silinemez!")
                    else:
                        database.delete_user(user_to_delete)
                        st.success(f"{user_to_delete} silindi."); time.sleep(1); st.rerun()

        # ÖĞRETMEN PANELİ
        elif st.session_state.admin_role == "teacher":
            st.header("📚 Öğretmen Paneli")
            tab_duyuru, tab_not = st.tabs(["📢 Duyuru Yap", "📝 Not Girişi"])
            with tab_duyuru:
                with st.form("duyuru_form"):
                    d_title = st.text_input("Duyuru Başlığı")
                    d_content = st.text_area("İçerik")
                    if st.form_submit_button("Yayınla"):
                        database.add_announcement(d_title, d_content, st.session_state.admin_username)
                        st.success("Duyuru yayınlandı.")
            with tab_not:
                students = database.get_students()
                if not students: st.warning("Öğrenci bulunamadı.")
                else:
                    col1, col2 = st.columns(2)
                    with col1:
                        selected_student = st.selectbox("Öğrenci Seç", students)
                        lesson_name = st.selectbox("Ders", ["Matematik", "Fizik", "Kimya", "Yazılım", "Türkçe"])
                    with col2:
                        grade_val = st.number_input("Not", 0, 100)
                    if st.button("Notu Kaydet"):
                        database.add_grade(selected_student, lesson_name, grade_val)
                        st.success(f"Kaydedildi: {grade_val}")

        # ÖĞRENCİ PANELİ
        elif st.session_state.admin_role == "student":
            st.header(f"🎒 Öğrenci Paneli - Hoşgeldin, {st.session_state.admin_username}")
            tab_notlar, tab_duyurular = st.tabs(["📝 Notlarım", "📢 Duyurular"])
            with tab_notlar:
                grades = database.get_student_grades(st.session_state.admin_username)
                if grades:
                    df_grades = pd.DataFrame(grades, columns=["Ders", "Not", "Tarih"])
                    st.dataframe(df_grades, use_container_width=True)
                    st.metric("Ortalama", f"{df_grades['Not'].mean():.2f}")
                else: st.info("Not bulunamadı.")
            with tab_duyurular:
                announcements = database.get_announcements()
                if announcements:
                    for ann in announcements:
                        with st.expander(f"📌 {ann[1]} ({ann[3]})"):
                            st.markdown(f"**{ann[2]}**")
                            st.caption(f"Yazan: {ann[4]}")
                else: st.warning("Duyuru yok.")

# ==========================================
# 5. MODÜL 2: DİJİTAL KAMPÜS (OYUN & ETKİLEŞİM)
# ==========================================
def render_digital_campus():
    # Kampüs için stil
    st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        .login-container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); text-align: center; border-top: 5px solid #D84315; }
        .bank-box { background: #e8f5e9; border: 2px dashed #27ae60; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

    if 'campus_logged_in' not in st.session_state: st.session_state.campus_logged_in = False
    if 'campus_role' not in st.session_state: st.session_state.campus_role = ""
    
    # GİRİŞ EKRANI
    if not st.session_state.campus_logged_in:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            st.markdown("""
            <div class="login-container">
                <h1 style="font-size: 2.2rem;">🎓 Bağarası ÇPAL</h1>
                <h2 style="color: #555;">Dijital Oyun & Etkinlik Kampüsü</h2>
            </div>
            """, unsafe_allow_html=True)
            
            tab_student, tab_free, tab_teacher = st.tabs(["SINIF GİRİŞİ", "SERBEST ÇALIŞMA", "ÖĞRETMEN"])
            
            with tab_student:
                with st.form("class_login"):
                    ad = st.text_input("Adı Soyadı")
                    no = st.text_input("Okul Numarası")
                    code = st.text_input("Ders Kodu")
                    if st.form_submit_button("Sınıfa Katıl"):
                        if server.join_student(code, ad, no):
                            st.session_state.campus_logged_in = True
                            st.session_state.campus_role = "student"
                            st.session_state.campus_user_name = ad
                            st.session_state.campus_user_no = no
                            st.session_state.class_code = code
                            st.session_state.bank_balance = server.get_student_score(code, no)
                            st.rerun()
                        else: st.error("Ders bulunamadı.")
            
            with tab_free:
                st.info("Serbest giriş modu.")
                uploaded_file = st.file_uploader("Profil Yükle (JSON)", type="json")
                with st.form("free_login"):
                    f_ad = st.text_input("Adın Soyadın")
                    f_no = st.text_input("Okul Numaran")
                    if st.form_submit_button("Giriş Yap"):
                        start_puan = 0
                        if uploaded_file:
                            try:
                                d = json.load(uploaded_file)
                                if str(d.get("no")) == str(f_no): start_puan = d.get("puan", 0)
                            except: pass
                        server.join_student("GENEL", f_ad, f_no, start_puan)
                        st.session_state.campus_logged_in = True
                        st.session_state.campus_role = "student"
                        st.session_state.campus_user_name = f_ad
                        st.session_state.campus_user_no = f_no
                        st.session_state.class_code = "GENEL"
                        st.session_state.bank_balance = server.get_student_score("GENEL", f_no)
                        st.rerun()

            with tab_teacher:
                with st.form("teacher_login"):
                    t_pass = st.text_input("Şifre", type="password")
                    if st.form_submit_button("Panel Aç"):
                        if t_pass == "1234":
                            new_code = str(random.randint(1000, 9999))
                            server.create_class(new_code)
                            st.session_state.campus_logged_in = True
                            st.session_state.campus_role = "teacher"
                            st.session_state.class_code = new_code
                            st.rerun()
                        else: st.error("Hatalı şifre")

    # UYGULAMA İÇİ
    else:
        if st.session_state.campus_role == "teacher":
            st.success(f"DERS KODU: {st.session_state.class_code}")
            if st.button("Yenile"): st.rerun()
            df = server.get_leaderboard(st.session_state.class_code)
            st.dataframe(df, use_container_width=True)
            if st.button("Çıkış"): st.session_state.campus_logged_in = False; st.rerun()

        elif st.session_state.campus_role == "student":
            c_info, c_save = st.columns([3, 1])
            with c_info:
                st.markdown(f"**{st.session_state.campus_user_name}** | 🏦: **{st.session_state.bank_balance} ₺** | Sınıf: {st.session_state.class_code}")
            with c_save:
                user_data = {"ad": st.session_state.campus_user_name, "no": st.session_state.campus_user_no, "puan": st.session_state.bank_balance}
                st.download_button("💾 KAYDET", json.dumps(user_data), f"{st.session_state.campus_user_no}.json")

            if st.button("Çıkış Yap (Kampüs)", key="logout_campus"):
                st.session_state.campus_logged_in = False
                st.rerun()

            tab_ana, tab_soru, tab_eglence, tab_lifesim = st.tabs(["🏆 ANA EKRAN", "📚 SORU ÇÖZÜM", "🎮 OYUN ALANI", "💼 LIFESIM"])

            with tab_ana:
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown('<div class="bank-box"><h3>🏦 BANKA VEZNESİ</h3></div>', unsafe_allow_html=True)
                    code = st.text_input("Kod:", key="transfer")
                    if st.button("BOZDUR"):
                        success, res = server.redeem_code(st.session_state.class_code, st.session_state.campus_user_no, code)
                        if success:
                            st.session_state.bank_balance = res
                            st.success(f"Yeni Bakiye: {res} ₺")
                            time.sleep(1); st.rerun()
                        else: st.error(res)
                with c2:
                    st.subheader("Sıralama")
                    st.dataframe(server.get_leaderboard(st.session_state.class_code), use_container_width=True)

            with tab_soru:
                t_tyt, t_meslek = st.tabs(["📘 TYT", "📙 MESLEK"])
                with t_tyt:
                    tyt_data = fetch_json_data(URL_TYT_DATA)
                    if tyt_data:
                        # Basit TYT mantığı (Örnek olarak kısaltıldı)
                        st.info("TYT Modülü yüklendi.")
                        st.markdown(f'<embed src="{URL_TYT_PDF}" width="100%" height="500px">', unsafe_allow_html=True)
                with t_meslek:
                    m_data = fetch_json_data(URL_MESLEK_SORULAR)
                    if m_data:
                        # Basit Meslek mantığı
                        st.info("Meslek Soruları yüklendi.")
            
            with tab_eglence:
                game = st.selectbox("Oyun Seç", ["Finans İmparatoru", "Asset Matrix"])
                if game == "Finans İmparatoru": components.html(FINANCE_GAME_HTML, height=700)
                else: components.html(ASSET_MATRIX_HTML, height=750)

            with tab_lifesim:
                components.html(load_lifesim_html(), height=800, scrolling=True)

# ==========================================
# 6. ANA YÖNLENDİRİCİ (MAIN)
# ==========================================
def main():
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2997/2997295.png", width=100)
    st.sidebar.title("Bağarası ÇPAL")
    
    app_mode = st.sidebar.radio("Uygulama Seçin:", ["📋 Okul Yönetim Sistemi", "🎮 Dijital Kampüs"])
    
    st.sidebar.divider()
    st.sidebar.info("Geliştirici: Bağarası ÇPAL Bilişim Bölümü")
    
    if app_mode == "📋 Okul Yönetim Sistemi":
        render_management_system()
    else:
        render_digital_campus()

if __name__ == "__main__":
    main()
