const API_BASE = ''; // Same origin

let statusInterval = null;

// Переключение табов
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`tab-${tabId}`).classList.add('active');
    event.currentTarget.classList.add('active');
    
    if (tabId === 'gallery') {
        loadGallery();
    }
}

// Загрузка списка моделей при старте
async function loadModels() {
    try {
        const res = await fetch(`${API_BASE}/api/models`);
        const data = await res.json();
        
        const select = document.getElementById('model-select');
        select.innerHTML = '';
        
        for (const [category, models] of Object.entries(data.models)) {
            const group = document.createElement('optgroup');
            group.label = category.toUpperCase();
            
            models.forEach(m => {
                const opt = document.createElement('option');
                opt.value = m.id;
                opt.textContent = `${m.name} (${m.safety})`;
                if (data.current_model_id === m.id) {
                    opt.selected = true;
                }
                group.appendChild(opt);
            });
            
            select.appendChild(group);
        }
    } catch (e) {
        console.error('Failed to load models', e);
    }
    
    // Add change listener to update optimal settings
    document.getElementById('model-select').addEventListener('change', applyOptimalSettings);
}

function applyOptimalSettings() {
    const modelId = document.getElementById('model-select').value.toLowerCase();
    
    let steps = 25;
    let cfg = 70; // x10
    let res = "512x512"; // index doesn't map directly in mobile, just set value if exists
    
    if (modelId.includes("schnell") || modelId.includes("flux")) {
        steps = 4;
        cfg = 10;
        res = "1024x1024";
    } else if (modelId.includes("xl") || modelId.includes("sdxl") || modelId.includes("animagine")) {
        steps = 35;
        cfg = 60;
        res = "1024x1024";
    } else if (modelId.includes("i2vgen") || modelId.includes("stable-video")) {
        steps = 25;
        cfg = 90;
        res = "512x512";
    } else {
        steps = 25;
        cfg = 70;
        res = "512x512";
    }
    
    document.getElementById('steps').value = steps;
    document.getElementById('steps-val').innerText = steps;
    
    document.getElementById('cfg').value = cfg;
    document.getElementById('cfg-val').innerText = (cfg / 10).toFixed(1);
    
    const resSelect = document.getElementById('resolution');
    // Try to select the closest matching resolution or exact match
    let found = false;
    for(let i = 0; i < resSelect.options.length; i++) {
        if(resSelect.options[i].value === res) {
            resSelect.selectedIndex = i;
            found = true;
            break;
        }
    }
    // If not exact match, just pick something similar based on target pixels
    if(!found) {
        let bestIdx = 0;
        let minDiff = Infinity;
        let targetPixels = parseInt(res.split('x')[0]) * parseInt(res.split('x')[1]);
        
        for(let i = 0; i < resSelect.options.length; i++) {
            const parts = resSelect.options[i].value.split('x');
            if(parts.length === 2) {
                const diff = Math.abs((parseInt(parts[0]) * parseInt(parts[1])) - targetPixels);
                if(diff < minDiff) {
                    minDiff = diff;
                    bestIdx = i;
                }
            }
        }
        resSelect.selectedIndex = bestIdx;
    }
}

// Старт генерации
async function startGeneration() {
    const btn = document.getElementById('generate-btn');
    const loader = btn.querySelector('.loader');
    const span = btn.querySelector('span');
    
    const prompt = document.getElementById('prompt').value;
    if (!prompt.trim()) {
        alert("Введите промпт!");
        return;
    }
    
    const payload = {
        model_id: document.getElementById('model-select').value,
        prompt: prompt,
        negative_prompt: document.getElementById('negative_prompt').value,
        steps: document.getElementById('steps').value,
        cfg: (document.getElementById('cfg').value / 10).toString(),
        resolution: document.getElementById('resolution').value
    };
    
    try {
        loader.style.display = 'block';
        span.style.display = 'none';
        btn.disabled = true;
        
        const res = await fetch(`${API_BASE}/api/generate`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            document.getElementById('progress-container').style.display = 'block';
            document.getElementById('result-container').style.display = 'none';
            statusInterval = setInterval(pollStatus, 1000);
        } else {
            const err = await res.json();
            alert(err.error || "Ошибка старта");
            resetButton();
        }
    } catch (e) {
        console.error(e);
        alert("Ошибка подключения к ПК");
        resetButton();
    }
}

function resetButton() {
    const btn = document.getElementById('generate-btn');
    btn.querySelector('.loader').style.display = 'none';
    btn.querySelector('span').style.display = 'block';
    btn.disabled = false;
}

// Опрос статуса
async function pollStatus() {
    try {
        const res = await fetch(`${API_BASE}/api/status`);
        const data = await res.json();
        
        document.getElementById('status-text').innerText = data.message;
        document.getElementById('percent-text').innerText = Math.round(data.percent * 100) + '%';
        document.getElementById('progress-bar-fill').style.width = (data.percent * 100) + '%';
        
        if (!data.is_generating) {
            clearInterval(statusInterval);
            resetButton();
            document.getElementById('progress-container').style.display = 'none';
            
            if (data.result_image) {
                const resultImg = document.getElementById('result-img');
                resultImg.src = `${API_BASE}/outputs/${data.result_image}?t=${Date.now()}`;
                document.getElementById('result-container').style.display = 'block';
                // Переключаемся на галерею через пару секунд для удобства? (Опционально)
            }
        }
    } catch (e) {
        console.error(e);
    }
}

// Галерея
async function loadGallery() {
    try {
        const res = await fetch(`${API_BASE}/api/gallery`);
        const data = await res.json();
        
        const grid = document.getElementById('gallery-grid');
        grid.innerHTML = '';
        
        data.files.forEach(file => {
            if (file.endsWith('.mp4')) return; // пока только картинки для простоты
            const img = document.createElement('img');
            img.src = `${API_BASE}/outputs/${file}`;
            img.className = 'gallery-item';
            // Открыть по клику фуллскрин
            img.onclick = () => {
                const w = window.open("");
                w.document.write(`<body style="margin:0;background:#000;display:flex;justify-content:center;align-items:center;height:100vh;"><img src="${img.src}" style="max-width:100%;max-height:100%;"></body>`);
            };
            grid.appendChild(img);
        });
    } catch (e) {
        console.error(e);
    }
}

// Инит
window.onload = () => {
    loadModels();
};
