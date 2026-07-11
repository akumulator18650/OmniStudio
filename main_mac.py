import os
import sys

from dotenv import load_dotenv

load_dotenv()

import uuid
import time
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QTextEdit,
                             QListWidget, QComboBox, QSlider, QProgressBar,
                             QScrollArea, QStackedWidget, QGraphicsView, QGraphicsScene,
                             QFileDialog, QFrame, QListWidgetItem, QSizePolicy,
                             QGraphicsDropShadowEffect, QLineEdit, QCheckBox, QGridLayout,
                             QGraphicsOpacityEffect, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation, QRect, QEasingCurve, QSettings, QRectF, QEvent
from PyQt6.QtGui import QPixmap, QIcon, QImage, QPainter, QFont, QFontDatabase, QFontMetrics, qAlpha, QKeySequence, QAction
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

def custom_excepthook(exc_type, exc_value, exc_traceback):
    import traceback
    with open("crash.log", "a", encoding="utf-8") as f:
        f.write("UNHANDLED EXCEPTION:\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
        f.write("-" * 50 + "\n")
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = custom_excepthook

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

def get_asset_path(*paths):
    return os.path.join(BASE_DIR, *paths)

if sys.platform == "darwin":
    from ai_engine_mac import AIEngine
else:
    from ai_engine import AIEngine


class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class NoScrollSlider(QSlider):
    def wheelEvent(self, event):
        event.ignore()

OUTPUTS_DIR = os.path.join(os.path.join(os.path.expanduser("~"), "Downloads"), "omnistudio")
os.makedirs(OUTPUTS_DIR, exist_ok=True)

RECOMMENDED_MODELS = [
    {"name": "ToonYou", "id": "stablediffusionapi/toonyou", "desc": "Яркая 3D-анимация и стилистика западных мультфильмов.", "size_gb": 2.1, "req": "GPU: VRAM 4GB+", "load_class": "Легкая", "safety": "SFW", "type": "Photo"},
    {"name": "GhostMix", "id": "stablediffusionapi/ghostmix", "desc": "Популярный микс для создания 2.5D киберпанк и меха артов.", "size_gb": 2.1, "req": "GPU: VRAM 4GB+", "load_class": "Легкая", "safety": "SFW", "type": "Photo"},
    {"name": "MeinaMix v11", "id": "stablediffusionapi/meinamix", "desc": "Эталонная легкая модель для сочного и детального аниме.", "size_gb": 2.1, "req": "GPU: VRAM 4GB+", "load_class": "Легкая", "safety": "NSFW", "type": "Photo"},
    
    {"name": "Stable Diffusion v1.5", "id": "runwayml/stable-diffusion-v1-5", "desc": "Официальная базовая модель SD 1.5.", "size_gb": 4.3, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "SFW", "type": "Photo"},
    {"name": "RevAnimated v1.2.2", "id": "stablediffusionapi/rev-animated", "desc": "Легендарная модель для 2.5D, 3D, фэнтези и аниме стилистики.", "size_gb": 4.3, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "SFW", "type": "Photo"},
    {"name": "Realistic Vision v6.0", "id": "SG161222/Realistic_Vision_V6.0_B1_noVAE", "desc": "Самая последняя версия топовой реалистичной модели.", "size_gb": 4.3, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "NSFW", "type": "Photo"},
    {"name": "CyberRealistic v3.2", "id": "stablediffusionapi/cyberrealistic-v32", "desc": "Очень популярная реалистичная модель. Отлично рисует текстуру кожи.", "size_gb": 4.0, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "NSFW", "type": "Photo"},
    {"name": "Realistic Vision v5.1 SFW", "id": "SG161222/Realistic_Vision_V5.1_noVAE", "desc": "Фотореалистичная безопасная (SFW) версия Realistic Vision.", "size_gb": 4.3, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "SFW", "type": "Photo"},
    {"name": "AbsoluteReality v1.8.1", "id": "Yntec/AbsoluteReality", "desc": "Высокодетализированная модель для создания реалистичных фотографий.", "size_gb": 4.0, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "SFW", "type": "Photo"},
    {"name": "Protogen x3.4", "id": "darkstorm2150/Protogen_x3.4_Official_Release", "desc": "Сбалансированная фото-модель с уклоном в кинематографичность.", "size_gb": 4.0, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "SFW", "type": "Photo"},
    {"name": "Counterfeit v3.0", "id": "stablediffusionapi/counterfeit-v30", "desc": "Превосходная аниме-модель с мягким освещением и проработкой фонов.", "size_gb": 4.2, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "NSFW", "type": "Photo"},
    {"name": "Chilled_Remix", "id": "stablediffusionapi/chilledremix", "desc": "Азиатская эстетика, косплей и реалистичные портреты.", "size_gb": 4.0, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "NSFW", "type": "Photo"},
    {"name": "NeverEnding Dream (NED)", "id": "stablediffusionapi/neverending-dream", "desc": "Красивый фэнтези-реализм, CG-арты и мифические существа.", "size_gb": 4.2, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "NSFW", "type": "Photo"},
    
    {"name": "Deliberate v3", "id": "stablediffusionapi/deliberate-v3", "desc": "Огромная база знаний. Вытягивает любые, даже самые сложные промпты.", "size_gb": 5.0, "req": "GPU: VRAM 8GB+", "load_class": "Тяжелая", "safety": "NSFW", "type": "Photo"},
    {"name": "Perfect World v6", "id": "stablediffusionapi/perfect-world-v6", "desc": "Тяжелая RPG/аниме модель с невероятной детализацией одежды и брони.", "size_gb": 5.6, "req": "GPU: VRAM 8GB+", "load_class": "Тяжелая", "safety": "NSFW", "type": "Photo"},
    {"name": "Illuminiati Diffusion v1.1", "id": "stablediffusionapi/illuminati-diffusion", "desc": "Упор на мрачную, атмосферную графику и контрастное освещение.", "size_gb": 5.2, "req": "GPU: VRAM 8GB+", "load_class": "Тяжелая", "safety": "SFW", "type": "Photo"},
    {"name": "MajicMix Realistic v7", "id": "stablediffusionapi/majicmix-realistic", "desc": "Тяжелый чекпоинт для генерации гламурных портретов высокого качества.", "size_gb": 5.1, "req": "GPU: VRAM 8GB+", "load_class": "Тяжелая", "safety": "NSFW", "type": "Photo"},
    {"name": "FLUX.1-Dev FLUXTASTIC (NSFW)", "id": "trongg/FLUX.1-dev_nsfw_FLUXTASTIC-v3.0", "desc": "Базовая простая NSFW версия Flux.", "size_gb": 23.8, "req": "GPU: VRAM 12GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "FLUX.2 Klein 9B", "id": "black-forest-labs/FLUX.2-klein-9B", "desc": "Новейшая быстрая и мощная модель от Black Forest Labs.", "size_gb": 9.0, "req": "GPU: VRAM 10GB+", "load_class": "Next-Gen", "safety": "SFW", "type": "Photo"},
    {"name": "FLUX.2 Klein 4B", "id": "black-forest-labs/FLUX.2-klein-4B", "desc": "Облегченная версия FLUX.2 Klein.", "size_gb": 4.5, "req": "GPU: VRAM 6GB+", "load_class": "Next-Gen", "safety": "SFW", "type": "Photo"},
    {"name": "FLUX.1 (Ungated Base)", "id": "sayakpaul/FLUX.1-merged", "desc": "Полностью открытая версия Flux. Работает без ключей HF.", "size_gb": 23.8, "req": "GPU: VRAM 16GB+", "load_class": "Next-Gen", "safety": "SFW", "type": "Photo"},
    {"name": "Stable Diffusion XL 1.0", "id": "stabilityai/stable-diffusion-xl-base-1.0", "desc": "Официальный SDXL. Отличное понимание сложных промптов.", "size_gb": 6.9, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "SFW", "type": "Photo"},
    {"name": "DreamShaper XL", "id": "Lykon/dreamshaper-xl-1-0", "desc": "Отличная SFW модель для создания артов, картин и иллюстраций.", "size_gb": 6.9, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "SFW", "type": "Photo"},
    {"name": "Pony Diffusion V6 XL", "id": "stablediffusionapi/pony-diffusion-v6-xl", "desc": "Лучшая SDXL модель для аниме, артов и NSFW контента.", "size_gb": 6.5, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "RealVisXL V4.0", "id": "SG161222/RealVisXL_V4.0", "desc": "Максимальный фотореализм. Лица и кожа фотографического качества.", "size_gb": 6.5, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "Juggernaut XL v9", "id": "stablediffusionapi/juggernaut-xl-v9", "desc": "Универсальный кинематографичный стиль, отлично понимает сложные позы.", "size_gb": 6.6, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "Animagine XL 3.1", "id": "Linaqruf/animagine-xl-3.1", "desc": "Высококачественное 2D Аниме. Знает много персонажей из игр и сериалов.", "size_gb": 6.5, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "ZavyChromaXL", "id": "Yntec/ZavychromaXL", "desc": "Полуреализм, магия, 2.5D. Креативная модель с сочными цветами.", "size_gb": 6.5, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "AutismMix SDXL", "id": "stablediffusionapi/autismmix-sdxl", "desc": "Популярный гибрид для детализированного 2D/аниме стиля без мыла.", "size_gb": 6.5, "req": "GPU: VRAM 8GB+", "load_class": "Next-Gen", "safety": "NSFW", "type": "Photo"},
    {"name": "Stable Cascade", "id": "stabilityai/stable-cascade", "desc": "Трехэтапная архитектура от Stability. Безумная скорость и четкий текст.", "size_gb": 14.0, "req": "GPU: VRAM 12GB+", "load_class": "Next-Gen", "safety": "SFW", "type": "Photo"},
    
    {"name": "Qwen 1.5 1.8B Chat", "id": "Qwen/Qwen1.5-1.8B-Chat", "desc": "Быстрая и легкая текстовая модель. Отличный ИИ-ассистент.", "size_gb": 3.7, "req": "GPU: VRAM 4GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Llama-3.2-3B-Instruct", "id": "huihui-ai/Llama-3.2-3B-Instruct-abliterated", "desc": "Модель без ограничений. Легкая и требует мало VRAM.", "size_gb": 6.5, "req": "GPU: VRAM 6GB+", "load_class": "Текст", "safety": "NSFW", "type": "Text"},
    {"name": "Llama 3.1 8B Instruct", "id": "meta-llama/Meta-Llama-3.1-8B-Instruct", "desc": "Новейшая топовая модель от Meta. Отлично подходит для общения и кода.", "size_gb": 16.0, "req": "GPU: VRAM 8GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Qwen 2.5 7B Instruct", "id": "Qwen/Qwen2.5-7B-Instruct", "desc": "Топовая мощная модель. Великолепно понимает русский язык.", "size_gb": 15.0, "req": "GPU: VRAM 8GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Mistral 7B Instruct v0.3", "id": "mistralai/Mistral-7B-Instruct-v0.3", "desc": "Популярная быстрая модель с хорошим контекстом.", "size_gb": 14.5, "req": "GPU: VRAM 8GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Gemma 2 9B IT", "id": "google/gemma-2-9b-it", "desc": "Отличная модель от Google. Очень умная для своих размеров.", "size_gb": 18.0, "req": "GPU: VRAM 10GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Phi-3.5 Mini 4K", "id": "microsoft/Phi-3.5-mini-instruct", "desc": "Крошечная, но невероятно умная модель от Microsoft.", "size_gb": 7.6, "req": "GPU: VRAM 4GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Dolphin 2.9 Llama 3 8B", "id": "cognitivecomputations/dolphin-2.9-llama3-8b", "desc": "Полностью без цензуры (Uncensored). Подходит для любых NSFW ролевых игр.", "size_gb": 16.0, "req": "GPU: VRAM 8GB+", "load_class": "Текст", "safety": "NSFW", "type": "Text"},
    {"name": "Llama 3 8B Uncensored", "id": "huihui-ai/Llama-3-8B-Instruct-abliterated", "desc": "Базовая Llama 3 со снятыми ограничениями.", "size_gb": 16.0, "req": "GPU: VRAM 8GB+", "load_class": "Текст", "safety": "NSFW", "type": "Text"},
    {"name": "Qwen 2.5 1.5B Instruct", "id": "Qwen/Qwen2.5-1.5B-Instruct", "desc": "Сверхлегкая версия Qwen 2.5. Летает на слабых ПК.", "size_gb": 3.0, "req": "GPU: VRAM 4GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    {"name": "Hermes 3 Llama 3.1 8B", "id": "NousResearch/Hermes-3-Llama-3.1-8B", "desc": "Очень креативная модель, слабая цензура. Отлична для историй.", "size_gb": 16.0, "req": "GPU: VRAM 8GB+", "load_class": "Текст", "safety": "NSFW", "type": "Text"},
    {"name": "Llama 3.2 1B Instruct", "id": "meta-llama/Llama-3.2-1B-Instruct", "desc": "Самая маленькая новая модель от Meta. Работает везде.", "size_gb": 2.5, "req": "GPU: VRAM 2GB+", "load_class": "Текст", "safety": "SFW", "type": "Text"},
    
    {"name": "I2VGen-XL (Видео по промпту)", "id": "ali-vilab/i2vgen-xl", "desc": "Анимирует картинку по тексту. Требует много памяти.", "size_gb": 15.0, "req": "GPU: VRAM 14GB+", "load_class": "Видео", "safety": "SFW", "type": "Video"},
    {"name": "Stable Video Diffusion (Авто)", "id": "stabilityai/stable-video-diffusion-img2vid", "desc": "Плавная анимация картинки без промпта. Кинематографично.", "size_gb": 9.5, "req": "GPU: VRAM 10GB+", "load_class": "Видео", "safety": "SFW", "type": "Video"},
    {"name": "CogVideoX-2B", "id": "THUDM/CogVideoX-2b", "desc": "Продвинутая text-to-video модель с высокой точностью движений.", "size_gb": 4.9, "req": "GPU: VRAM 12GB+", "load_class": "Видео", "safety": "SFW", "type": "Video"},
    
    {"name": "Qwen 1.5 1.8B Chat", "id": "Qwen/Qwen1.5-1.8B-Chat", "desc": "Быстрая и легкая текстовая модель. Отличный ИИ-ассистент.", "size_gb": 3.7, "req": "GPU: VRAM 4GB+", "load_class": "Легкая", "safety": "SFW", "type": "Text"},
    {"name": "Llama-3.2-3B-Instruct", "id": "huihui-ai/Llama-3.2-3B-Instruct-abliterated", "desc": "Текстовая модель без цензуры. Отличный размер для VRAM.", "size_gb": 6.5, "req": "GPU: VRAM 6GB+", "load_class": "Средняя", "safety": "NSFW", "type": "Text"}
]


APP_DATA_DIR = os.path.join(os.path.expanduser('~'), 'OmniStudioData')
os.makedirs(APP_DATA_DIR, exist_ok=True)
CHATS_FILE = os.path.join(APP_DATA_DIR, 'chats.json')
# Load dynamic models if available
models_file_path = os.path.join(APP_DATA_DIR, 'models.json')
if os.path.exists(models_file_path):
    try:
        import json
        with open(models_file_path, 'r', encoding='utf-8') as mf:
            dynamic_models = json.load(mf)
            seen_ids = {m.get("id") for m in RECOMMENDED_MODELS}
            for k, v in dynamic_models.items():
                if isinstance(v, list):
                    for m in v:
                        mid = m.get("id")
                        if mid and mid not in seen_ids:
                            RECOMMENDED_MODELS.append(m)
                            seen_ids.add(mid)
    except Exception as e:
        print("Error loading models.json:", e)

class TextWorker(QThread):
    text_generated = pyqtSignal(str)
    text_chunk_generated = pyqtSignal(str)
    
    def __init__(self, engine, prompt, system_prompt=None, max_new_tokens=512, temperature=0.7, top_p=0.9, repetition_penalty=1.1):
        super().__init__()
        self.engine = engine
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.is_cancelled = False
        
    def run(self):
        try:
            import threading
            tokenizer = getattr(self.engine.llm_pipeline, 'tokenizer', None) if getattr(self.engine, 'llm_pipeline', None) else None
            
            if tokenizer:
                try:
                    from transformers import TextIteratorStreamer
                    streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
                    
                    def generate():
                        try:
                            self.engine.generate_text(
                                self.prompt, 
                                system_prompt=self.system_prompt, 
                                max_new_tokens=self.max_new_tokens,
                                temperature=self.temperature,
                                top_p=self.top_p,
                                repetition_penalty=self.repetition_penalty,
                                streamer=streamer,
                                cancel_check=lambda: self.is_cancelled
                            )
                        except Exception as e:
                            pass
                    
                    t = threading.Thread(target=generate)
                    t.start()
                    
                    full_text = ""
                    for new_text in streamer:
                        if self.is_cancelled:
                            break
                        full_text += new_text
                        self.text_chunk_generated.emit(new_text)
                    
                    t.join(timeout=1.0)
                    self.text_generated.emit(full_text)
                except ImportError:
                    # Fallback if transformers isn't fully available
                    result = self.engine.generate_text(self.prompt, self.system_prompt, self.max_new_tokens, self.temperature, self.top_p, self.repetition_penalty, cancel_check=lambda: self.is_cancelled)
                    self.text_generated.emit(result)
            else:
                result = self.engine.generate_text(
                    self.prompt, 
                    system_prompt=self.system_prompt, 
                    max_new_tokens=self.max_new_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    repetition_penalty=self.repetition_penalty,
                    cancel_check=lambda: self.is_cancelled
                )
                self.text_generated.emit(result)
        except Exception as e:
            print(f"TextWorker Error: {e}")
            self.text_generated.emit(f"Error: {e}")

class GenerationWorker(QThread):
    progress_updated = pyqtSignal(int, int, str, float)
    image_preview = pyqtSignal(QImage)
    generation_finished = pyqtSignal(list)
    generation_error = pyqtSignal(str)
    prompt_translated = pyqtSignal(str)
    
    def __init__(self, engine, model_id, precision, vram_mode, prompt, batch_count, steps, width, height, sampler, negative_prompt, seed, denoise, cfg_scale, init_image=None, mask_image=None, use_adetailer=False, lora_id=None, lora_weight=1.0, controlnet_id=None, control_image=None, batch_size=1, output_dir=None):
        super().__init__()
        self.engine = engine
        self.model_id = model_id
        self.precision = precision
        self.vram_mode = vram_mode
        self.prompt = prompt
        self.batch_count = batch_count
        self.batch_size = batch_size
        self.output_dir = output_dir if output_dir else OUTPUTS_DIR
        self.steps = steps
        self.width = width
        self.height = height
        self.sampler = sampler
        self.negative_prompt = negative_prompt
        self.seed = seed
        self.denoise = denoise
        self.cfg_scale = cfg_scale
        self.init_image = init_image
        self.mask_image = mask_image
        self.use_adetailer = use_adetailer
        self.lora_id = lora_id
        self.lora_weight = lora_weight
        self.controlnet_id = controlnet_id
        self.control_image_path = control_image
        self.is_cancelled = False
        
    def run(self):
        try:
            if self.model_id and self.model_id != self.engine.current_model_id:
                self.progress_updated.emit(0, self.steps, "Загрузка модели...", 0.0)
                old_stderr = sys.stderr
                import threading
                class GenTqdmStream:
                    def __init__(self, sig):
                        self.sig = sig
                        self.buf = ""
                        self.lock = threading.Lock()
                    def write(self, text):
                        with self.lock:
                            self.buf += text
                            if '\r' in self.buf or '\n' in self.buf:
                                lines = self.buf.replace('\r', '\n').split('\n')
                                for line in lines[:-1]:
                                    if '%' in line:
                                        import re
                                        match = re.search(r'(\d+)%', line)
                                        if match:
                                            self.sig.emit(0, 100, f"Загрузка модели: {match.group(1)}%", int(match.group(1))/100)
                                self.buf = lines[-1]
                    def flush(self): pass
                sys.stderr = GenTqdmStream(self.progress_updated)
                try:
                    self.engine.load_model(self.model_id, precision=self.precision, vram_mode=self.vram_mode)
                finally:
                    sys.stderr = old_stderr
                    
                if self.is_cancelled: return

            self.engine.set_device()
            self.engine.apply_lora(self.lora_id)
            
            self.engine.set_sampler(self.sampler)
            output_paths = []
            
            prompts_list = [self.prompt.strip()] if self.prompt.strip() else [""]
                
            total_generations = len(prompts_list) * self.batch_count
            current_gen_idx = 0
            
            import itertools
            for base_prompt, b_idx in itertools.product(prompts_list, range(self.batch_count)):
                if self.is_cancelled: break
                current_gen_idx += 1
                
                start_time = time.time()
                seed_val = self.seed if self.seed != -1 else random.randint(0, 2**32 - 1)
                if self.seed != -1: self.seed += 1

                current_prompt = base_prompt
                import re
                if bool(re.search('[а-яА-Я]', current_prompt)):
                    self.progress_updated.emit(0, self.steps, "Перевод промпта...", 0.0)
                    current_prompt = self.engine.translate_ru_to_en(current_prompt)
                    self.prompt_translated.emit(current_prompt)

                def step_callback(step, total_steps, latents):
                    if self.is_cancelled: raise InterruptedError("Отменено")
                    ratio = (step + 1) / total_steps
                    elapsed = time.time() - start_time
                    spd = (step + 1) / elapsed if elapsed > 0 else 0
                    msg = f"[{current_gen_idx}/{total_generations}] Шаг: {step+1}/{total_steps} | {int(ratio*100)}% | {spd:.2f} it/s"
                    self.progress_updated.emit(step+1, total_steps, msg, ratio)
                    
                    update_interval = 1 if self.engine.device == "cuda" else 2
                    if step % update_interval == 0:
                        try:
                            pil_img = self.engine.decode_latents(latents, width=getattr(self, 'width', None), height=getattr(self, 'height', None))
                            if pil_img:
                                data = pil_img.tobytes("raw", "RGB")
                                qim = QImage(data, pil_img.width, pil_img.height, QImage.Format.Format_RGB888)
                                self.image_preview.emit(qim)
                        except: pass
                    time.sleep(0.05)
                
                from PIL import Image
                init_pil = None
                mask_pil = None
                if self.init_image and isinstance(self.init_image, str):
                    init_pil = Image.open(self.init_image)
                    if hasattr(self, "width") and hasattr(self, "height"):
                        init_pil = init_pil.resize((self.width, self.height), Image.Resampling.LANCZOS)
                if self.mask_image and isinstance(self.mask_image, str):
                    mask_pil = Image.open(self.mask_image)
                    if hasattr(self, "width") and hasattr(self, "height"):
                        mask_pil = mask_pil.resize((self.width, self.height), Image.Resampling.NEAREST)
                
                import math
                active_model = (self.model_id or self.engine.current_model_id or "").lower()
                is_video = "stable-video" in active_model or "i2vgen" in active_model
                
                cnet_img = None
                if self.controlnet_id and self.control_image_path:
                    self.progress_updated.emit(0, self.steps, "Обработка ControlNet (Canny)...", 0.0)
                    from PIL import Image, ImageFilter
                    cnet_img = Image.open(self.control_image_path).convert("RGB")
                    if hasattr(self, 'width') and hasattr(self, 'height'):
                        cnet_img = cnet_img.resize((self.width, self.height))
                    cnet_img = cnet_img.filter(ImageFilter.FIND_EDGES)

                if is_video and self.init_image:
                    vid_path = os.path.join(self.output_dir, f"video_{uuid.uuid4().hex}.mp4")
                    path = self.engine.generate_video(
                        image_path=self.init_image, 
                        prompt=current_prompt,
                        output_path=vid_path,
                        negative_prompt=self.negative_prompt, 
                        num_inference_steps=self.steps, 
                        seed=seed_val, 
                        callback=step_callback
                    )
                    if path: output_paths.append(path)
                    continue
                    
                if mask_pil and init_pil:
                    images = self.engine.generate_inpaint(
                        prompt=current_prompt, 
                        init_image=init_pil, 
                        mask_image=mask_pil, 
                        num_inference_steps=self.steps, 
                        strength=1.0, 
                        guidance_scale=self.cfg_scale,
                        negative_prompt=self.negative_prompt, 
                        seed=seed_val, 
                        callback=step_callback,
                        lora_weight=self.lora_weight,
                    controlnet_id=self.controlnet_id,
                    control_image=cnet_img,
                    batch_size=self.batch_size
                )
                elif init_pil:
                    adjusted_steps = int(math.ceil(self.steps / max(self.denoise, 0.01)))
                    try:
                        images = self.engine.generate_img2img(
                            prompt=current_prompt, 
                            init_image=init_pil, 
                            strength=self.denoise, 
                            num_inference_steps=adjusted_steps, 
                            guidance_scale=self.cfg_scale,
                            negative_prompt=self.negative_prompt, 
                            seed=seed_val, 
                            callback=step_callback,
                            lora_weight=self.lora_weight,
                            controlnet_id=self.controlnet_id,
                            control_image=cnet_img,
                            batch_size=self.batch_size
                        )
                    except ValueError as e:
                        if "не поддерживает генерацию по картинке" in str(e):
                            self.progress_updated.emit(0, self.steps, "⚠️ Картинка проигнорирована (не поддерживается)", 0.0)
                            images = self.engine.generate_image(
                                prompt=current_prompt, 
                                num_inference_steps=self.steps, 
                                width=self.width, 
                                height=self.height, 
                                guidance_scale=self.cfg_scale,
                                negative_prompt=self.negative_prompt, 
                                seed=seed_val, 
                                callback=step_callback,
                                lora_weight=self.lora_weight,
                                controlnet_id=self.controlnet_id,
                                control_image=cnet_img,
                                batch_size=self.batch_size
                            )
                        else:
                            raise e
                else:
                    images = self.engine.generate_image(
                        prompt=current_prompt, 
                        num_inference_steps=self.steps, 
                        width=self.width, 
                        height=self.height, 
                        guidance_scale=self.cfg_scale,
                        negative_prompt=self.negative_prompt, 
                        seed=seed_val, 
                        callback=step_callback,
                        lora_weight=self.lora_weight,
                    controlnet_id=self.controlnet_id,
                    control_image=cnet_img,
                    batch_size=self.batch_size
                )
                    
                for img in images:
                    if self.use_adetailer:
                        self.progress_updated.emit(self.steps, self.steps, "ADetailer: Улучшение лица...", 1.0)
                        img = self.engine.run_adetailer(img, current_prompt, self.negative_prompt, seed_val)
                        
                    path = os.path.join(self.output_dir, f"gen_{uuid.uuid4().hex}.png")
                    img.save(path)
                    output_paths.append(path)
                
            self.generation_finished.emit(output_paths)
        except Exception as e:
            self.generation_error.emit(str(e))

import threading
class TqdmStream:
    def __init__(self, signal):
        import sys
        self.signal = signal
        self.buf = ""
        self.lock = threading.Lock()
        self.original_stderr = sys.__stderr__

    def write(self, text):
        with self.lock:
            if not isinstance(text, str):
                text = str(text)
            self.buf += text
            if '\r' in self.buf or '\n' in self.buf:
                lines = self.buf.replace('\r', '\n').split('\n')
                for line in lines[:-1]:
                    if '%' in line:
                        try:
                            self.signal.emit(line.strip())
                        except Exception:
                            pass
                self.buf = lines[-1]
            try:
                self.original_stderr.write(text)
            except:
                pass

    def flush(self):
        try:
            self.original_stderr.flush()
        except:
            pass

    def __getattr__(self, name):
        return getattr(self.original_stderr, name)

class ModelLoadWorker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, engine, model_id, precision="fp16", vram_mode="high", model_type="Photo"):
        super().__init__()
        self.engine = engine
        self.model_id = model_id
        self.precision = precision
        self.vram_mode = vram_mode
        self.model_type = model_type
        
    def run(self):
        old_stderr = sys.stderr
        sys.stderr = TqdmStream(self.progress_signal)
        try:
            if self.model_type == "Text":
                self.engine.load_text_model(self.model_id, precision=self.precision)
                self.finished_signal.emit(True, "Текстовая модель загружена")
            else:
                success = self.engine.load_model(self.model_id, precision=self.precision, vram_mode=self.vram_mode)
                if success:
                    self.finished_signal.emit(True, "Модель успешно загружена")
                else:
                    self.finished_signal.emit(False, "Ошибка загрузки модели")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            sys.stderr = old_stderr

class AddonDownloadWorker(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, engine, addon_id):
        super().__init__()
        self.engine = engine
        self.addon_id = addon_id
        
    def run(self):
        old_stderr = sys.stderr
        sys.stderr = TqdmStream(self.progress_signal)
        try:
            from huggingface_hub import snapshot_download
            snapshot_download(
                repo_id=self.addon_id,
                allow_patterns=["*.safetensors", "*.bin"],
                ignore_patterns=[".*"]
            )
            self.finished_signal.emit(True, "Дополнение успешно скачано")
        except Exception as e:
            self.finished_signal.emit(False, str(e))
        finally:
            sys.stderr = old_stderr

class DrawingScene(QGraphicsScene):
    def __init__(self, mask_image, parent=None):
        super().__init__(parent)
        self.mask_image = mask_image
        self.last_point = None
        self.brush_size = 40

    def mousePressEvent(self, event):
        self.last_point = event.scenePos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.last_point and event.buttons() & Qt.MouseButton.LeftButton:
            pos = event.scenePos()
            pen = QPen(QColor(255, 0, 0, 150), self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            self.addLine(self.last_point.x(), self.last_point.y(), pos.x(), pos.y(), pen)
            
            painter = QPainter(self.mask_image)
            painter.setPen(QPen(Qt.GlobalColor.white, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(self.last_point, pos)
            painter.end()
            
            self.last_point = pos
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.last_point = None
        super().mouseReleaseEvent(event)

class CanvasDialog(QWidget):
    mask_saved = pyqtSignal(str)
    
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Встроенная рисовалка масок")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.resize(800, 600)
        self.image_path = image_path
        self.mask_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        self.original_pixmap = QPixmap(self.image_path)
        self.mask_image = QImage(self.original_pixmap.size(), QImage.Format.Format_RGB888)
        self.mask_image.fill(Qt.GlobalColor.black)

        self.scene = DrawingScene(self.mask_image)
        self.scene.addPixmap(self.original_pixmap)
        
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        layout.addWidget(self.view)
        
        btn_layout = QHBoxLayout()
        
        brush_lbl = QLabel("Размер кисти: 40")
        brush_lbl.setStyleSheet("color: white;")
        btn_layout.addWidget(brush_lbl)
        
        brush_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        brush_slider.setRange(5, 200)
        brush_slider.setValue(40)
        brush_slider.setFixedWidth(150)
        brush_slider.valueChanged.connect(lambda v: self.update_brush_size(v, brush_lbl))
        btn_layout.addWidget(brush_slider)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton("Применить маску")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedSize(180, 40)
        save_btn.clicked.connect(self.save_mask)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
        
    def update_brush_size(self, size, lbl):
        self.scene.brush_size = size
        lbl.setText(f"Размер кисти: {size}")

    def save_mask(self):
        self.mask_path = os.path.join(OUTPUTS_DIR, f"mask_{uuid.uuid4().hex}.png")
        self.mask_image.save(self.mask_path)
        self.mask_saved.emit(self.mask_path)
        self.close()

class ChatBubble(QWidget):
    def __init__(self, role, content, is_image=False, upscale_callback=None, fav_callback=None, animate_callback=None):
        super().__init__()
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.bubble = QFrame()
        self.bubble.setObjectName("chatBubbleUser" if role == "user" else "chatBubbleAI")
        self.bubble.setMaximumWidth(700)
        
        layout = QVBoxLayout(self.bubble)
        layout.setContentsMargins(15, 10, 15, 10)
        
        header = QLabel("Вы" if role == "user" else "OmniStudio AI")
        header.setStyleSheet("color: #808080; font-size: 13px; font-weight: bold;")
        
        is_video = content.endswith(".mp4")
        
        if role == "user" and not is_image and not is_video:
            header_layout = QHBoxLayout()
            header_layout.setContentsMargins(0,0,0,0)
            header_layout.addWidget(header)
            header_layout.addStretch()
            
            btn_style = "QPushButton { background-color: #2A2A2A; color: #CCCCCC; border: 1px solid #444444; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #404040; color: white; border: 1px solid #666666; }"
            
            copy_btn = QPushButton("Копировать")
            copy_btn.setStyleSheet(btn_style)
            copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(content))
            header_layout.addWidget(copy_btn)
            
            if fav_callback:
                fav_btn = QPushButton("В избранное")
                fav_btn.setStyleSheet(btn_style)
                fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                fav_btn.clicked.connect(lambda: fav_callback(content))
                header_layout.addWidget(fav_btn)
                
            layout.addLayout(header_layout)
        else:
            layout.addWidget(header)
        
        if is_video:
            from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PyQt6.QtMultimediaWidgets import QVideoWidget
            from PyQt6.QtCore import QUrl
            
            video_widget = QVideoWidget()
            video_widget.setMinimumSize(400, 300)
            
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.player.setVideoOutput(video_widget)
            self.player.setSource(QUrl.fromLocalFile(content))
            
            layout.addWidget(video_widget)
            
            controls_layout = QHBoxLayout()
            play_btn = QPushButton("▶ Play / Pause")
            play_btn.setStyleSheet("background-color: #333333; color: white; border-radius: 4px; padding: 5px;")
            play_btn.clicked.connect(lambda: self.player.pause() if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState else self.player.play())
            controls_layout.addWidget(play_btn)
            controls_layout.addStretch()
            layout.addLayout(controls_layout)
            
            self.player.play()
            
        elif is_image:
            img_lbl = QLabel()
            pixmap = QPixmap(content)
            if not pixmap.isNull():
                img_lbl.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                img_lbl.setText("Изображение не найдено")
            layout.addWidget(img_lbl)
            
            if role == "ai":
                if upscale_callback:
                    upscale_btn = QPushButton("⟡ Улучшить (Upscale 2x)")
                    upscale_btn.setStyleSheet("background-color: #1A1A1A; color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px; margin-top: 5px; font-weight: bold;")
                    upscale_btn.clicked.connect(lambda: upscale_callback(content))
                    layout.addWidget(upscale_btn)
                if animate_callback:
                    animate_btn = QPushButton("🎬 Оживить (Видео)")
                    animate_btn.setStyleSheet("background-color: #1A1A1A; color: white; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 6px; margin-top: 5px; font-weight: bold;")
                    animate_btn.clicked.connect(lambda: animate_callback(content))
                    layout.addWidget(animate_btn)
        else:
            self.text_container = QWidget()
            self.text_layout = QVBoxLayout(self.text_container)
            self.text_layout.setContentsMargins(0,0,0,0)
            
            self.think_btn = QPushButton("💭 Показать ход мыслей")
            self.think_btn.setStyleSheet("text-align: left; background: transparent; color: #888888; font-weight: bold; border: none;")
            self.think_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.think_btn.clicked.connect(self.toggle_thoughts)
            self.think_btn.hide()
            self.text_layout.addWidget(self.think_btn)
            
            self.think_lbl = QLabel()
            self.think_lbl.setWordWrap(True)
            self.think_lbl.setStyleSheet("color: #888888; font-size: 13px; font-style: italic; background-color: #1A1A1A; padding: 8px; border-radius: 6px;")
            self.think_lbl.hide()
            self.text_layout.addWidget(self.think_lbl)
            
            self.text_lbl = QLabel()
            self.text_lbl.setWordWrap(True)
            self.text_lbl.setStyleSheet("color: white; font-size: 16px;")
            self.text_layout.addWidget(self.text_lbl)
            
            layout.addWidget(self.text_container)
            self.set_content(content)
            
        if role == "user":
            main_layout.addStretch()
            main_layout.addWidget(self.bubble)
        else:
            main_layout.addWidget(self.bubble)
            main_layout.addStretch()

    def set_content(self, text):
        if hasattr(self, 'text_lbl'):
            import re
            think_match = re.search(r'<think>(.*?)(</think>|$)', text, re.DOTALL)
            if think_match:
                think_text = think_match.group(1).strip()
                self.think_lbl.setText(think_text)
                self.think_btn.show()
                main_text = re.sub(r'<think>.*?(</think>|$)', '', text, flags=re.DOTALL).strip()
                self.text_lbl.setText(main_text)
            else:
                self.text_lbl.setText(text)
                self.think_btn.hide()
                self.think_lbl.hide()
                
    def toggle_thoughts(self):
        if self.think_lbl.isVisible():
            self.think_lbl.hide()
            self.think_btn.setText("💭 Показать ход мыслей")
        else:
            self.think_lbl.show()
            self.think_btn.setText("💭 Скрыть ход мыслей")

class AnimatedTabBar(QFrame):
    tabChanged = pyqtSignal(int)
    def __init__(self, tabs):
        super().__init__()
        self.setObjectName("navBar")
        self.setFixedHeight(46)
        
        # Shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 150))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        
        # Pill Background Indicator
        self.pill = QWidget(self)
        self.pill.setStyleSheet("background-color: #FFFFFF; border-radius: 18px;")
        self.pill.resize(115, 36)
        self.pill.move(5, 5)
        self.pill.show()
        
        self.buttons = []
        self.anim = QPropertyAnimation(self.pill, b"geometry")
        self.anim.setDuration(250)
        self.anim.setEasingCurve(QEasingCurve.Type.OutExpo)
        
        font = QFont("Inter")
        font.setPixelSize(15)
        font.setBold(True)
        fm = QFontMetrics(font)
        
        for i, text in enumerate(tabs):
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setProperty("class", "NavBtn")
            
            btn_width = fm.horizontalAdvance(text) + 40
            btn.setFixedSize(btn_width, 36)
            btn.clicked.connect(lambda checked, idx=i: self.select_tab(idx))
            self.layout.addWidget(btn)
            self.buttons.append(btn)
            if i == 0:
                btn.setChecked(True)
                self.pill.resize(btn_width, 36)
                
    def select_tab(self, idx):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == idx)
        
        target_btn = self.buttons[idx]
        self.anim.setEndValue(QRect(target_btn.x(), target_btn.y(), target_btn.width(), target_btn.height()))
        self.anim.start()
        self.tabChanged.emit(idx)

class SpinnerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(24, 24)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        self.timer.start(30)
        
    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        pen = QPen(QColor(255, 255, 255))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawArc(-8, -8, 16, 16, 0, 16 * 270)
        painter.end()

class ToastNotification(QFrame):
    def __init__(self, parent, text, duration=3000):
        super().__init__(parent)
        self.setObjectName("glassPanel")
        self.setStyleSheet("background-color: rgba(20, 20, 20, 0.85); border: 1px solid rgba(255,255,255,0.2); border-radius: 12px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        lbl = QLabel(text)
        lbl.setStyleSheet("color: white; font-weight: bold; font-size: 14px; border: none; background: transparent;")
        layout.addWidget(lbl)
        
        self.adjustSize()
        # Removed window flags so it acts as an overlay child widget
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        # Position at bottom right of parent
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)
        
        self.anim_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_in.setDuration(300)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        
        self.anim_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim_out.setDuration(300)
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.finished.connect(self.deleteLater)
        
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.anim_out.start)
        self.timer.setInterval(duration)
        
    def show_toast(self):
        parent = self.parent()
        if parent:
            # Position at top right
            x = parent.width() - self.width() - 30
            y = 30
            self.move(x, y)
        self.raise_()
        self.show()
        self.anim_in.start()
        self.timer.start()

class PromptTextEdit(QTextEdit):
    enter_pressed = pyqtSignal()
    image_pasted = pyqtSignal(QImage)
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            clipboard = QApplication.clipboard()
            if clipboard.mimeData().hasImage():
                image = clipboard.image()
                if not image.isNull():
                    self.image_pasted.emit(image)
                    return
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.enter_pressed.emit()
            event.accept()
        else:
            super().keyPressEvent(event)

class ToggleSwitch(QCheckBox):
    ACCENT_COLOR = "#FFFFFF"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(36, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        bg_color = QColor("#FFFFFF") if self.isChecked() else QColor("#333333")
        
        p.setBrush(bg_color)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        thumb_color = QColor("#000000") if self.isChecked() else QColor("#888888")
        p.setBrush(thumb_color)
        
        thumb_size = self.height() - 4
        thumb_x = self.width() - thumb_size - 2 if self.isChecked() else 2
        p.drawEllipse(thumb_x, 2, thumb_size, thumb_size)

class ClickableLabel(QLabel):
    clicked = pyqtSignal(str)
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path)

class ClickableImageLabel(QLabel):
    clicked = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path = ""

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.path)


class LiveGenerationWorker(QThread):
    image_generated = pyqtSignal(str)
    
    def __init__(self, engine, model_id, prompt, seed, sampler):
        super().__init__()
        self.engine = engine
        self.model_id = model_id
        self.prompt = prompt
        self.seed = seed
        self.sampler = sampler
        self.is_cancelled = False
        
    def run(self):
        try:
            if self.is_cancelled: return
                
            self.engine.set_device()
            self.engine.set_sampler(self.sampler)
            
            # Fast settings for Live Mode
            img = self.engine.generate_image(
                prompt=self.prompt,
                num_inference_steps=4,
                width=512,
                height=512,
                guidance_scale=1.5,
                seed=self.seed,
                callback=None
            )
            
            if self.is_cancelled: return
            
            import os, uuid
            path = os.path.join(OUTPUTS_DIR, f"live_{uuid.uuid4().hex}.jpg")
            if isinstance(img, list): img = img[0]
            img.convert('RGB').save(path, quality=85)
            self.image_generated.emit(path)
        except Exception as e:
            print("LiveGen error:", e)
            


from PyQt6.QtWidgets import QGraphicsRectItem, QGraphicsItem
from PyQt6.QtGui import QColor, QPen

class GenerationFrameItem(QGraphicsRectItem):
    def __init__(self, rect):
        super().__init__(rect)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.setPen(QPen(QColor("#4CAF50"), 2, Qt.PenStyle.DashLine))
        self.setBrush(QColor(76, 175, 80, 20))
        self.setAcceptHoverEvents(True)
        self._is_resizing = False
        self._resize_margin = 15
        self._resize_dir = None
        self._start_rect = None
        self._start_pos = None

    def hoverMoveEvent(self, event):
        pos = event.pos()
        rect = self.rect()
        cursor = Qt.CursorShape.ArrowCursor
        
        on_left = pos.x() < rect.left() + self._resize_margin
        on_right = pos.x() > rect.right() - self._resize_margin
        on_top = pos.y() < rect.top() + self._resize_margin
        on_bottom = pos.y() > rect.bottom() - self._resize_margin
        
        if on_left and on_top: cursor = Qt.CursorShape.SizeFDiagCursor
        elif on_right and on_bottom: cursor = Qt.CursorShape.SizeFDiagCursor
        elif on_right and on_top: cursor = Qt.CursorShape.SizeBDiagCursor
        elif on_left and on_bottom: cursor = Qt.CursorShape.SizeBDiagCursor
        elif on_left or on_right: cursor = Qt.CursorShape.SizeHorCursor
        elif on_top or on_bottom: cursor = Qt.CursorShape.SizeVerCursor
        else: cursor = Qt.CursorShape.SizeAllCursor
        
        self.setCursor(cursor)
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            rect = self.rect()
            
            on_left = pos.x() < rect.left() + self._resize_margin
            on_right = pos.x() > rect.right() - self._resize_margin
            on_top = pos.y() < rect.top() + self._resize_margin
            on_bottom = pos.y() > rect.bottom() - self._resize_margin
            
            if on_left or on_right or on_top or on_bottom:
                self._is_resizing = True
                self._resize_dir = (on_left, on_right, on_top, on_bottom)
                self._start_rect = self.rect()
                self._start_pos = event.scenePos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_resizing:
            diff = event.scenePos() - self._start_pos
            rect = QRectF(self._start_rect)
            
            on_left, on_right, on_top, on_bottom = self._resize_dir
            
            if on_left: rect.setLeft(min(rect.right() - 64, rect.left() + diff.x()))
            if on_right: rect.setRight(max(rect.left() + 64, rect.right() + diff.x()))
            if on_top: rect.setTop(min(rect.bottom() - 64, rect.top() + diff.y()))
            if on_bottom: rect.setBottom(max(rect.top() + 64, rect.bottom() + diff.y()))
            
            self.setRect(rect)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._is_resizing:
            self._is_resizing = False
            self._resize_dir = None
            event.accept()
            return
        super().mouseReleaseEvent(event)

class CanvasTab(QWidget):
    generation_requested = pyqtSignal(str, QImage, QImage, float, float)
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-2000, -2000, 4000, 4000)
        
        self.view = QGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.setStyleSheet("background-color: #121212; border: none;")
        layout.addWidget(self.view)
        
        # Grid background
        self.scene.setBackgroundBrush(QColor("#1A1A1A"))
        
        self.gen_frame = GenerationFrameItem(QRectF(0, 0, 512, 512))
        self.scene.addItem(self.gen_frame)
        self.view.centerOn(self.gen_frame)
        
        # Bottom controls
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background-color: #1E1E1E; border-top: 1px solid #333;")
        bottom_layout = QHBoxLayout(bottom_widget)
        
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Промпт для дорисовки или генерации...")
        self.prompt_input.setFixedHeight(30)
        self.prompt_input.setStyleSheet("background-color: #0A0A0A; color: white; border: 1px solid #333; border-radius: 8px; padding: 5px;")
        self.prompt_input.installEventFilter(self)
        
        self.generate_btn = QPushButton("Генерировать")
        self.generate_btn.setFixedSize(120, 50)
        self.generate_btn.setStyleSheet("background-color: #2A2A2A; color: white; border-radius: 8px; font-weight: bold; border: 1px solid rgba(255,255,255,0.15);")
        self.generate_btn.clicked.connect(self.request_generation)
        
        self.load_img_btn = QPushButton("📂")
        self.load_img_btn.setFixedSize(50, 50)
        self.load_img_btn.setToolTip("Загрузить изображение на холст")
        self.load_img_btn.setStyleSheet("background-color: #2A2A2A; color: white; border-radius: 8px; font-size: 20px; border: 1px solid rgba(255,255,255,0.15);")
        self.load_img_btn.clicked.connect(self.load_image_to_canvas)
        
        bottom_layout.addWidget(self.load_img_btn)
        bottom_layout.addWidget(self.prompt_input)
        bottom_layout.addWidget(self.generate_btn)
        layout.addWidget(bottom_widget)
        
    def load_image_to_canvas(self):
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить изображение", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.place_image(path, self.gen_frame.pos().x(), self.gen_frame.pos().y())
            
    def place_image(self, path, x, y):
        pixmap = QPixmap(path)
        item = self.scene.addPixmap(pixmap)
        item.setPos(x, y)
        item.setFlags(QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        item.setZValue(-1)
        
    def request_generation(self):
        prompt = self.prompt_input.toPlainText()
        if not prompt:
            if hasattr(self.main_window, '_show_toast'):
                self.main_window._show_toast("⚠ Введите промпт для генерации!", 3000)
            return
        
        self.gen_frame.hide()
        
        rect = self.gen_frame.sceneBoundingRect()
        image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(image)
        self.scene.render(painter, target=QRectF(image.rect()), source=rect)
        painter.end()
        
        self.gen_frame.show()
        
        mask = QImage(image.size(), QImage.Format.Format_Grayscale8)
        mask.fill(Qt.GlobalColor.white)
        
        has_content = False
        for y in range(image.height()):
            for x in range(image.width()):
                alpha = qAlpha(image.pixel(x, y))
                if alpha > 0:
                    has_content = True
                    mask.setPixelColor(x, y, QColor(Qt.GlobalColor.black))
                else:
                    image.setPixelColor(x, y, QColor(Qt.GlobalColor.black))
                    
        # If blank, it's normal generation
        if not has_content:
            self.generation_requested.emit(prompt, QImage(), QImage(), rect.x(), rect.y())
        else:
            self.generation_requested.emit(prompt, image, mask, rect.x(), rect.y())
            
class MainWindow(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.live_mode = False
        self.live_timer = QTimer()
        self.live_timer.setSingleShot(True)
        self.live_timer.timeout.connect(self.trigger_live_generation)
        self.generation_queue = []
        self.is_generating = False
        self._old_workers = []
        self.generation_queue = []
        self.is_generating = False
        self.setWindowTitle("OmniStudio (PyQt6)")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        self.setAcceptDrops(True)
        self.settings = QSettings("OmniStudio", "App")
        
        try:
            with open(get_asset_path("style.qss"), "r", encoding="utf-8") as f:
                self.base_stylesheet = f.read()
        except:
            self.base_stylesheet = ""
            
        # Load custom fonts
        QFontDatabase.addApplicationFont(get_asset_path("assets", "fonts", "Inter.ttf"))
        QFontDatabase.addApplicationFont(get_asset_path("assets", "fonts", "Lora.ttf"))
        
        self.engine = AIEngine()
        # Apply saved GPU setting immediately on startup
        use_gpu = QSettings("OmniStudio", "OmniStudio").value("gpu", True, type=bool)
        self.engine.set_device(use_gpu)
        
        style_path = get_asset_path("style.qss")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
                
        self.chats = {}
        self.active_chat_id = None
        self.load_chats()
        
        self.init_ui()
        self.load_chats()
        if not self.chats:
            self.create_new_chat()
        else:
            self.active_chat_id = list(self.chats.keys())[0]
            self.update_chat_list_ui()
            self.update_messages_ui()
            
        self.setup_tray_icon()
        
    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icons_dir = get_asset_path("assets", "icons")
        icon_path = os.path.join(icons_dir, "app_icon.ico")
        png_path = os.path.join(icons_dir, "app_icon.png")
        app_icon = None
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
        elif os.path.exists(png_path):
            app_icon = QIcon(png_path)
        if app_icon is not None:
            self.tray_icon.setIcon(app_icon)
            self.setWindowIcon(app_icon)
        else:
            pixmap = QPixmap(32, 32)
            pixmap.fill(Qt.GlobalColor.black)
            self.tray_icon.setIcon(QIcon(pixmap))

        self.tray_icon.setToolTip("OmniStudio")

        tray_menu = QMenu()
        restore_action = QAction("Развернуть", self)
        restore_action.triggered.connect(self.show_from_tray)
        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(restore_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
        
    def on_tray_activated(self, reason):
        if reason in (
            QSystemTrayIcon.ActivationReason.DoubleClick,
            QSystemTrayIcon.ActivationReason.Trigger,
        ):
            self.show_from_tray()

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                QTimer.singleShot(0, self.hide_to_tray)
        super().changeEvent(event)

    def hide_to_tray(self):
        if self.isVisible():
            self.hide()
            if hasattr(self, "tray_icon"):
                self.tray_icon.showMessage(
                    "OmniStudio",
                    "Приложение свёрнуто в трей. Дважды щёлкните значок, чтобы открыть.",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000,
                )

    def quit_app(self):
        self.force_quit = True
        QApplication.quit()
        
    def closeEvent(self, event):
        if not getattr(self, 'force_quit', False):
            event.ignore()
            self.hide_to_tray()
        else:
            event.accept()
        

            
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            if url.isLocalFile():
                path = url.toLocalFile()
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')):
                    self.nav_bar.select_tab(0)
                    self._set_attachment(path, False)
                    break
                    

            
    def add_favorite(self, prompt):
        favs = self.settings.value("favorites", [])
        if prompt not in favs:
            favs.append(prompt)
            self.settings.setValue("favorites", favs)
            
    def show_favorites(self):
        from PyQt6.QtWidgets import QDialog, QListWidget, QVBoxLayout
        dlg = QDialog(self)
        dlg.setWindowTitle("Избранные промпты")
        dlg.resize(400, 500)
        dlg.setStyleSheet("background-color: #121212; color: white;")
        layout = QVBoxLayout(dlg)
        lst = QListWidget()
        lst.setStyleSheet("border: none; outline: none; font-size: 14px; padding: 10px;")
        lst.setSpacing(5)
        for f in reversed(self.settings.value("favorites", [])):
            lst.addItem(f)
        lst.itemClicked.connect(lambda item: self.prompt_input.setPlainText(item.text()))
        lst.itemClicked.connect(dlg.accept)
        layout.addWidget(lst)
        dlg.exec()
            
    def load_chats(self):
        if os.path.exists(CHATS_FILE):
            try:
                with open(CHATS_FILE, "r", encoding="utf-8") as f:
                    self.chats = json.load(f)
            except: pass

    def save_chats(self):
        with open(CHATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.chats, f, ensure_ascii=False, indent=2)

    def eventFilter(self, obj, event):
        if obj == self.prompt_input and event.type() == QEvent.Type.KeyPress:
            if event.matches(QKeySequence.StandardKey.Paste):
                clipboard = QApplication.clipboard()
                mime_data = clipboard.mimeData()
                if mime_data.hasImage():
                    image = clipboard.image()
                    import tempfile, uuid, os
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"pasted_{uuid.uuid4().hex[:8]}.png")
                    image.save(temp_path, "PNG")
                    self._set_attachment(temp_path, False)
                    return True
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False
                else:
                    self.start_generation()
                    return True
        return super().eventFilter(obj, event)

    def create_new_chat(self):
        chat_id = str(uuid.uuid4())
        self.chats[chat_id] = {"title": "Новый чат", "messages": []}
        self.active_chat_id = chat_id
        self.save_chats()
        self.update_chat_list_ui()
        self.update_messages_ui()

    def update_chat_list_ui(self):
        self.chat_list.clear()
        self.chat_list.setSpacing(8)
        for cid, data in self.chats.items():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, cid)
            self.chat_list.addItem(item)
            
            row_widget = QWidget()
            row_widget.setObjectName("chatItemWidget")
            
            if cid == self.active_chat_id:
                row_widget.setStyleSheet("""
                    #chatItemWidget {
                        background-color: rgba(255, 255, 255, 0.05);
                        border: 1px solid rgba(255, 255, 255, 0.2);
                        border-radius: 10px;
                    }
                """)
                item.setSelected(True)
            else:
                row_widget.setStyleSheet("""
                    #chatItemWidget {
                        background-color: transparent;
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        border-radius: 10px;
                    }
                    #chatItemWidget:hover {
                        background-color: rgba(255, 255, 255, 0.02);
                        border: 1px solid rgba(255, 255, 255, 0.1);
                    }
                """)
                
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(15, 12, 10, 12)
            
            title_lbl = QLabel(data["title"])
            title_lbl.setStyleSheet("font-family: 'Lora', serif; font-size: 14px; color: white; border: none; background: transparent;")
            title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            row_layout.addWidget(title_lbl)
            row_layout.addStretch()
            
            item.setSizeHint(row_widget.sizeHint())
            self.chat_list.setItemWidget(item, row_widget)

    def show_chat_context_menu(self, pos):
        item = self.chat_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            menu.setStyleSheet("QMenu { background-color: #1E1E1E; color: white; border: 1px solid #333; } QMenu::item:selected { background-color: #E50914; }")
            delete_action = menu.addAction(QIcon(get_asset_path("assets/icons/trash.svg")), "Удалить чат")
            action = menu.exec(self.chat_list.mapToGlobal(pos))
            if action == delete_action:
                cid = item.data(Qt.ItemDataRole.UserRole)
                self.delete_chat(cid)

    def delete_chat(self, cid):
        if cid in self.chats:
            del self.chats[cid]
        if not self.chats:
            self.create_new_chat()
        else:
            self.active_chat_id = list(self.chats.keys())[0]
            self.save_chats()
            self.update_chat_list_ui()
            self.update_messages_ui()

    def update_messages_ui(self):
        # If a generation is in progress, switching chats destroys the
        # gen_container widget tree. Stop the timer and drop our references
        # so the worker callbacks bail out instead of touching deleted Qt objects.
        if hasattr(self, "gen_timer"):
            try: self.gen_timer.stop()
            except Exception: pass
        if hasattr(self, "gen_container") and self.gen_container is not None:
            self.gen_container = None
        # Drop a stale text-streaming bubble reference too.
        if hasattr(self, "current_chat_bubble"):
            self.current_chat_bubble = None

        while self.messages_layout.count():
            child = self.messages_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if not self.active_chat_id: return
        
        chat = self.chats[self.active_chat_id]
        for msg in chat["messages"]:
            is_image = msg["content"].endswith(".png") or msg["content"].endswith(".jpg")
            bubble = ChatBubble(msg["role"], msg["content"], is_image, upscale_callback=self.trigger_upscale, fav_callback=self.add_favorite, animate_callback=self.trigger_animate)
            self.messages_layout.addWidget(bubble)
            
        self.messages_layout.addStretch()
        QTimer.singleShot(100, lambda: self.messages_area.verticalScrollBar().setValue(self.messages_area.verticalScrollBar().maximum()))

    def trigger_upscale(self, image_path):
        self.start_generation(is_upscale=True, upscale_image_path=image_path)

    def trigger_animate(self, image_path):
        # Set as attachment for I2V or SVD
        self._set_attachment(image_path, False)
        # Select 'Video' category
        self.models_cat_nav.select_tab(3)
        self.nav_bar.select_tab(0) # Go to Chat
        
        # If no video model selected, select I2VGen automatically
        current = self.model_combo.currentText().lower()
        if not ("stable-video" in current or "i2vgen" in current):
            idx = self.model_combo.findText("ali-vilab/i2vgen-xl")
            if idx >= 0:
                self.model_combo.setCurrentIndex(idx)
        
        self.prompt_input.setFocus()
        self.prompt_input.setPlaceholderText("Опишите анимацию (или оставьте пустым для авто)...")

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setObjectName("glassPanel")
        self.sidebar.setFixedWidth(230)
        
        shadow_sb = QGraphicsDropShadowEffect()
        shadow_sb.setBlurRadius(20)
        shadow_sb.setColor(QColor(0, 0, 0, 100))
        shadow_sb.setOffset(0, 0)
        self.sidebar.setGraphicsEffect(shadow_sb)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)
        
        self.new_chat_btn = QPushButton("+ Новый чат")
        self.new_chat_btn.setStyleSheet("background-color: transparent; border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; font-family: 'Inter', 'Lora', sans-serif; font-size: 15px; font-weight: 800; color: white;")
        self.new_chat_btn.setFixedHeight(40)
        self.new_chat_btn.clicked.connect(self.create_new_chat)
        sidebar_layout.addWidget(self.new_chat_btn)
        
        self.fav_btn = QPushButton("⭐ Избранные промпты")
        self.fav_btn.setStyleSheet("background-color: transparent; border: none; font-family: 'Inter', 'Lora', sans-serif; font-size: 14px; font-weight: bold; color: #BBBBBB; text-align: left; padding-left: 10px;")
        self.fav_btn.setFixedHeight(30)
        self.fav_btn.clicked.connect(self.show_favorites)
        self.fav_btn.hide() # Temporarily hidden
        sidebar_layout.addWidget(self.fav_btn)
        
        div1 = QFrame()
        div1.setFixedHeight(1)
        div1.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); margin-top: 10px; margin-bottom: 10px;")
        sidebar_layout.addWidget(div1)
        
        self.chat_list = QListWidget()
        self.chat_list.setStyleSheet("""
            QListWidget {
                border: none;
                background-color: transparent;
                outline: 0;
            }
            QListWidget::item:selected {
                background-color: transparent;
            }
            QListWidget::item:hover {
                background-color: transparent;
            }
        """)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_chat_context_menu)
        self.chat_list.itemClicked.connect(self.on_chat_selected)
        sidebar_layout.addWidget(self.chat_list)
        
        div2 = QFrame()
        div2.setFixedHeight(1)
        div2.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); margin-top: 15px; margin-bottom: 15px;")
        sidebar_layout.addWidget(div2)
        
        # System Monitor Card
        self.sys_monitor_card = QFrame()
        self.sys_monitor_card.setStyleSheet("background-color: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 10px; padding: 5px;")
        sys_layout = QVBoxLayout(self.sys_monitor_card)
        sys_lbl = QLabel("СИСТЕМА")
        sys_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #FFFFFF; border: none; background: transparent;")
        self.sys_monitor_lbl = QLabel("CPU: 0%\nRAM: 0%")
        self.sys_monitor_lbl.setStyleSheet("color: #A0A0A0; font-size: 12px; border: none; background: transparent;")
        sys_layout.addWidget(sys_lbl)
        sys_layout.addWidget(self.sys_monitor_lbl)
        sidebar_layout.addWidget(self.sys_monitor_card)

        
        # Main Area
        main_col = QVBoxLayout()
        main_col.setContentsMargins(0, 0, 0, 0)
        
        self.nav_bar = AnimatedTabBar(["Чат", "Галерея", "Настройки", "Модели", "Дополнения"])
        self.nav_bar.tabChanged.connect(self.on_tab_changed)
        
        nav_container = QHBoxLayout()
        nav_container.addStretch()
        nav_container.addWidget(self.nav_bar)
        nav_container.addStretch()
        main_col.addLayout(nav_container)
        
        self.stack = QStackedWidget()
        
        
        self.tab_chat = QWidget()
        self.tab_addons = QWidget()

        self.tab_gallery = QWidget()
        self.tab_settings = QWidget()
        self.tab_models = QWidget()
        
        self.stack.addWidget(self.tab_chat)
        self.stack.addWidget(self.tab_gallery)
        self.stack.addWidget(self.tab_settings)
        
        self.stack.addWidget(self.tab_models)
        self.stack.addWidget(self.tab_addons)

        
        main_col.addWidget(self.stack)
        
        layout.addWidget(self.sidebar)
        layout.addLayout(main_col)
        
        self.setup_chat_tab()
        self.setup_settings_tab()
        self.setup_models_tab()
        self.setup_addons_tab()
        self.setup_gallery_tab()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_sys_monitor)
        self.timer.start(2000)
        
    def on_tab_changed(self, idx):
        self.stack.setCurrentIndex(idx)
        if idx == 1:
            self.load_gallery()
        elif idx == 3:
            self.load_models()
        elif idx == 4:
            self.load_addons()
        QApplication.processEvents()
    def on_chat_selected(self, item):
        self.active_chat_id = item.data(Qt.ItemDataRole.UserRole)
        self.update_chat_list_ui()
        self.update_messages_ui()
        
    def update_sys_monitor(self):
        import psutil
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        self.sys_monitor_lbl.setText(f"CPU: {cpu}%\nRAM: {ram.used / (1024**3):.1f}/{ram.total / (1024**3):.1f} GB ({ram.percent}%)")
        
    def setup_chat_tab(self):
        layout = QVBoxLayout(self.tab_chat)
        layout.setContentsMargins(0, 10, 0, 0)
        
        # Messages Area
        self.messages_area = QScrollArea()
        self.messages_area.setWidgetResizable(True)
        self.messages_widget = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_widget)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.messages_area.setWidget(self.messages_widget)
        layout.addWidget(self.messages_area)
        
        # Input Capsule Container (Transparent wrapper)
        input_container = QFrame()
        input_container.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        shadow_in = QGraphicsDropShadowEffect()
        shadow_in.setBlurRadius(20)
        shadow_in.setColor(QColor(0, 0, 0, 150))
        shadow_in.setOffset(0, 5)
        input_container.setGraphicsEffect(shadow_in)
        
        input_layout = QVBoxLayout(input_container)
        input_layout.setContentsMargins(15, 10, 15, 10)
        input_layout.setSpacing(5)
        
        self.live_canvas = QLabel()
        self.live_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.live_canvas.setFixedHeight(256)
        self.live_canvas.setStyleSheet("background-color: rgba(0,0,0,0.5); border-radius: 12px; border: 1px solid rgba(255,255,255,0.1);")
        self.live_canvas.hide()
        input_layout.addWidget(self.live_canvas)
        
        # Middle row: Single Unified Capsule for Input and Buttons
        main_capsule = QFrame()
        main_capsule.setMaximumWidth(850)
        main_capsule.setStyleSheet("QFrame#glassInput { background-color: #222222; border-radius: 22px; border: 1px solid rgba(255,255,255,0.05); }")
        main_capsule.setObjectName("glassInput")
        
        capsule_layout = QVBoxLayout(main_capsule)
        capsule_layout.setContentsMargins(15, 10, 15, 10)
        capsule_layout.setSpacing(10)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Опишите, что вы хотите сгенерировать... (вставьте фото Ctrl+V)")
        self.prompt_input.setFixedHeight(50)
        self.prompt_input.setStyleSheet("background-color: transparent; color: white; border: none; font-size: 16px; padding: 0px;")
        self.prompt_input.textChanged.connect(self.on_prompt_changed)
        self.prompt_input.installEventFilter(self)
        
        capsule_layout.addWidget(self.prompt_input)
        
        # Bottom row inside the capsule
        capsule_bottom = QHBoxLayout()
        capsule_bottom.setContentsMargins(0, 0, 0, 0)
        
        self.attach_btn = QPushButton("+")
        self.attach_btn.setFixedSize(30, 30)
        self.attach_btn.setStyleSheet("background-color: transparent; color: #888888; font-size: 24px; font-weight: 300; border: none;")
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.clicked.connect(self.attach_image)
        capsule_bottom.addWidget(self.attach_btn)
        
        self.live_container = QWidget()
        live_lyt = QHBoxLayout(self.live_container)
        live_lyt.setContentsMargins(5, 0, 0, 0)
        live_lbl = QLabel("Live")
        live_lbl.setStyleSheet("color: #888888; font-weight: 600; font-size: 13px;")
        live_lyt.addWidget(live_lbl)
        
        self.live_switch = ToggleSwitch()
        self.live_switch.toggled.connect(self.toggle_live_mode)
        live_lyt.addWidget(self.live_switch)
        
        capsule_bottom.addWidget(self.live_container)
        
        self.text_switches_container = QWidget()
        text_lyt = QHBoxLayout(self.text_switches_container)
        text_lyt.setContentsMargins(5, 0, 0, 0)
        
        think_lbl = QLabel("Thinking")
        think_lbl.setStyleSheet("color: #888888; font-weight: 600; font-size: 13px;")
        text_lyt.addWidget(think_lbl)
        self.thinking_switch = ToggleSwitch()
        text_lyt.addWidget(self.thinking_switch)
        
        text_lyt.addSpacing(10)
        
        agent_lbl = QLabel("Agent")
        agent_lbl.setStyleSheet("color: #888888; font-weight: 600; font-size: 13px;")
        text_lyt.addWidget(agent_lbl)
        self.agent_switch = ToggleSwitch()
        text_lyt.addWidget(self.agent_switch)
        
        capsule_bottom.addWidget(self.text_switches_container)
        self.text_switches_container.hide()
        
        import os
        model_name = os.path.basename(self.engine.current_model_id) if self.engine.current_model_id else ""
        self.current_model_lbl = QLabel(model_name)
        self.current_model_lbl.setStyleSheet("color: #888888; font-size: 13px; font-weight: bold; margin-left: 10px;")
        capsule_bottom.addWidget(self.current_model_lbl)
        
        capsule_bottom.addStretch()
        
        self.magic_wand_btn = QPushButton("⟡")
        self.magic_wand_btn.setFixedSize(34, 38)
        self.magic_wand_btn.setStyleSheet("background-color: transparent; color: #FFD700; font-size: 22px; border: none; font-weight: bold; padding-bottom: 4px;")
        self.magic_wand_btn.setToolTip("Улучшить промпт (ИИ)")
        self.magic_wand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.magic_wand_btn.clicked.connect(self.enhance_prompt)
        capsule_bottom.addWidget(self.magic_wand_btn)
        
        self.generate_btn = QPushButton("↑")
        self.generate_btn.setFixedSize(36, 36)
        self.generate_btn.setStyleSheet("""
            QPushButton { background-color: white; color: black; font-size: 24px; font-weight: bold; border-radius: 18px; border: none; padding: 0px; margin: 0px; }
            QPushButton:disabled { background-color: #E0E0E0; color: #555555; }
        """)
        self.generate_btn.setToolTip('Сгенерировать')
        self.generate_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.generate_btn.clicked.connect(self.start_generation)
        capsule_bottom.addWidget(self.generate_btn)
        
        capsule_layout.addLayout(capsule_bottom)
        
        middle_row_centered = QHBoxLayout()
        middle_row_centered.addStretch(1)
        middle_row_centered.addWidget(main_capsule, stretch=8)
        middle_row_centered.addStretch(1)
        
        input_layout.addLayout(middle_row_centered)
        layout.addWidget(input_container)
        
        self.attachment_container = QWidget()
        att_layout = QHBoxLayout(self.attachment_container)
        att_layout.setContentsMargins(5, 5, 5, 5)
        
        self.attachment_preview = ClickableImageLabel()
        self.attachment_preview.setFixedSize(60, 60)
        self.attachment_preview.setStyleSheet("border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);")
        self.attachment_preview.clicked.connect(lambda _path: self.open_canvas())
        
        self.attachment_info = QLabel()
        self.attachment_info.setStyleSheet("color: #E50914; font-weight: bold; font-size: 13px;")
        self.attachment_info.hide()
        
        remove_att_btn = QPushButton("✕")
        remove_att_btn.setFixedSize(24, 24)
        remove_att_btn.setStyleSheet("background-color: #333333; color: white; border-radius: 12px; font-weight: bold;")
        remove_att_btn.clicked.connect(self.remove_attachment)
        
        att_layout.addWidget(self.attachment_preview)
        att_layout.addWidget(self.attachment_info)
        att_layout.addStretch()
        att_layout.addWidget(remove_att_btn)
        
        self.attachment_container.hide()
        layout.insertWidget(1, self.attachment_container)
        
        self.attached_image = None
        self.attached_mask = None
        
    def add_chip_text(self, text):
        current = self.prompt_input.toPlainText()
        if current:
            self.prompt_input.setPlainText(current + ", " + text)
        else:
            self.prompt_input.setPlainText(text)
            


    
    def select_cnet_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать референс ControlNet", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if path:
            self.cnet_image_path = path
            pixmap = QPixmap(path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.cnet_preview.setPixmap(pixmap)

    def toggle_live_mode(self, checked):
        self.live_mode = checked
        if checked:
            self.live_canvas.show()
            self._pending_live_prompt = None
            self.trigger_live_generation()
        else:
            self.live_canvas.hide()
            self.live_canvas.clear()
            self._pending_live_prompt = None
            
    def enhance_prompt(self):
        current_prompt = self.prompt_input.toPlainText().strip()
        if not current_prompt:
            QMessageBox.warning(self, "Ошибка", "Введите промпт для улучшения.")
            return

        # Check if an LLM is loaded
        if not hasattr(self.engine, 'llm_pipeline') or self.engine.llm_pipeline is None:
            # Show a toast or dialog indicating they should load an LLM first
            QMessageBox.information(self, "Информация", "Пожалуйста, сначала выберите и загрузите текстовую модель (например Qwen или Llama) во вкладке моделей, чтобы использовать ИИ-помощника.")
            return

        self.magic_wand_btn.setEnabled(False)
        self.magic_wand_btn.setText("⟳")
        
        # Run enhancement in a worker
        self.enhancer_worker = TextWorker(
            self.engine,
            current_prompt,
            system_prompt="You are an expert prompt engineer for Stable Diffusion/Flux. Your task is to take the user's simple prompt and expand it into a highly detailed, descriptive, and visually stunning prompt in English. Respond ONLY with the final prompt, no explanations. Do not censor any content.",
            max_new_tokens=150
        )
        self.enhancer_worker.text_generated.connect(self.on_prompt_enhanced)
        self.enhancer_worker.finished.connect(lambda: self.magic_wand_btn.setEnabled(True))
        self.enhancer_worker.finished.connect(lambda: self.magic_wand_btn.setText("⟡"))
        self.enhancer_worker.start()

    def on_prompt_enhanced(self, enhanced_text):
        self.prompt_input.setPlainText(enhanced_text)

    def on_prompt_changed(self):
        doc_height = self.prompt_input.document().size().height()
        new_height = max(30, min(80, int(doc_height + 10)))
        if self.prompt_input.height() != new_height:
            self.prompt_input.setFixedHeight(new_height)
            
        if getattr(self, 'live_mode', False):
            self.trigger_live_generation()
            
    def trigger_live_generation(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
            
        if getattr(self, 'live_worker_running', False):
            self._pending_live_prompt = prompt
            return
            
        self.live_worker_running = True
        self.live_worker = LiveGenerationWorker(
            self.engine,
            self.model_combo.currentText(),
            prompt,
            int(self.seed_input.text()) if self.seed_input.text() else 42,
            self.sampler_combo.currentText()
        )
        self.live_worker.image_generated.connect(self.update_live_canvas)
        self.live_worker.finished.connect(self.on_live_worker_finished)
        self.live_worker.start()
        
    def on_live_worker_finished(self):
        self.live_worker_running = False
        if getattr(self, '_pending_live_prompt', None):
            self.trigger_live_generation()
            
    def update_live_canvas(self, img_path):
        if not getattr(self, 'live_mode', False): return
        pixmap = QPixmap(img_path).scaledToHeight(256, Qt.TransformationMode.SmoothTransformation)
        self.live_canvas.setPixmap(pixmap)

    def setup_settings_tab(self):
        main_layout = QVBoxLayout(self.tab_settings)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(25)
        
        def make_hline():
            line = QFrame()
            line.setFixedHeight(1)
            line.setStyleSheet("background-color: rgba(255, 255, 255, 0.05); border: none;")
            return line
            
        def make_section_title(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-family: 'Lora', serif; font-size: 22px; font-weight: bold; color: white;")
            return lbl
            
        def make_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #E0E0E0;")
            return lbl
            
        # --- App Settings ---
        layout.addWidget(make_section_title("Общие Настройки"))
        layout.addWidget(make_hline())

        # Folder selection
        layout.addWidget(make_label("Папка для сохранения"))
        folder_layout = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.folder_input.setText(self.settings.value("output_folder", OUTPUTS_DIR))
        folder_layout.addWidget(self.folder_input)
        folder_btn = QPushButton("Выбрать")
        folder_btn.clicked.connect(self.select_output_folder)
        folder_layout.addWidget(folder_btn)
        layout.addLayout(folder_layout)

        # Sound toggle
        self.sound_check = QCheckBox("Звуковое уведомление по завершении")
        self.sound_check.setStyleSheet("color: white; font-weight: bold;")
        self.sound_check.setChecked(self.settings.value("play_sound", True, type=bool))
        self.sound_check.toggled.connect(self.save_settings)
        layout.addWidget(self.sound_check)
        
        layout.addSpacing(20)

        # --- Image Settings Container ---
        self.image_settings_widget = QWidget()
        img_layout = QVBoxLayout(self.image_settings_widget)
        img_layout.setContentsMargins(0,0,0,0)
        
        # --- Image Settings ---
        img_layout.addWidget(make_section_title("Настройки Изображения"))
        img_layout.addWidget(make_hline())
        
        # Active model combo box is hidden, kept for internal state
        self.model_combo = NoScrollComboBox()
        self.model_combo.hide()
        self.model_combo.currentTextChanged.connect(self.apply_optimal_settings)
        img_layout.addWidget(self.model_combo)
        
        # Format
        img_layout.addWidget(make_label("Формат"))
        self.format_combo = NoScrollComboBox()
        self.format_combo.addItems(["1:1 (Квадрат)", "16:9 (Широкий)", "9:16 (Вертикальный)", "4:3 (Фото)", "3:4 (Фото Верт.)", "21:9 (Кино)"])
        self.format_combo.currentIndexChanged.connect(self.update_resolutions)
        img_layout.addWidget(self.format_combo)
        
        # Resolution
        img_layout.addWidget(make_label("Разрешение"))
        self.res_combo = NoScrollComboBox()
        img_layout.addWidget(self.res_combo)
        
        # Batch
        batch_lbl = make_label("Количество (Последовательно): 1")
        img_layout.addWidget(batch_lbl)
        self.batch_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.batch_slider.setRange(1, 10)
        self.batch_slider.setValue(1)
        self.batch_slider.valueChanged.connect(lambda v: batch_lbl.setText(f"Количество (Последовательно): {v}"))
        img_layout.addWidget(self.batch_slider)

        batch_size_lbl = make_label("Размер батча (Параллельно): 1\n(⚠ Требует много VRAM!)")
        img_layout.addWidget(batch_size_lbl)
        self.batch_size_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.batch_size_slider.setRange(1, 4)
        self.batch_size_slider.setValue(1)
        self.batch_size_slider.valueChanged.connect(lambda v: batch_size_lbl.setText(f"Размер батча (Параллельно): {v}\n(⚠ Требует много VRAM!)"))
        img_layout.addWidget(self.batch_size_slider)
        img_layout.addWidget(make_hline())
        
        # LoRA
        img_layout.addWidget(make_label("Выбранная LoRA (Стиль/Персонаж)"))
        self.lora_input = NoScrollComboBox()
        self.lora_input.addItem("Нет")
        self.lora_input.currentIndexChanged.connect(self._sync_lora_selection)
        img_layout.addWidget(self.lora_input)
        
        # LoRA Weight (if lora is selected)
        self.lora_weight_lbl = make_label("Сила LoRA: 1.0")
        img_layout.addWidget(self.lora_weight_lbl)
        self.lora_weight = NoScrollSlider(Qt.Orientation.Horizontal)
        self.lora_weight.setRange(0, 20) # 0.0 to 2.0
        self.lora_weight.setValue(10)
        self.lora_weight.valueChanged.connect(lambda v: self.lora_weight_lbl.setText(f"Сила LoRA: {v/10.0:.1f}"))
        img_layout.addWidget(self.lora_weight)
        
        # ControlNet
        img_layout.addWidget(make_label("Выбранный ControlNet"))
        self.cnet_input = NoScrollComboBox()
        self.cnet_input.addItem("Нет")
        self.cnet_input.currentIndexChanged.connect(self._sync_cnet_selection)
        img_layout.addWidget(self.cnet_input)
        
        img_layout.addWidget(make_hline())
        
        # --- Advanced Settings Toggle ---
        self.adv_btn = QPushButton("⚙ Расширенные настройки ▼")
        self.adv_btn.setCheckable(True)
        self.adv_btn.setStyleSheet("background: transparent; border: none; color: #888888; text-align: left; font-weight: bold; padding: 5px;")
        img_layout.addWidget(self.adv_btn)
        
        self.adv_widget = QWidget()
        adv_layout = QVBoxLayout(self.adv_widget)
        adv_layout.setContentsMargins(10, 0, 0, 0)
        self.adv_widget.hide()
        
        self.adv_btn.toggled.connect(lambda c: self.adv_widget.setVisible(c))
        self.adv_btn.toggled.connect(lambda c: self.adv_btn.setText("⚙ Расширенные настройки ▲" if c else "⚙ Расширенные настройки ▼"))
        
        img_layout.addWidget(self.adv_widget)
        
        # Steps
        steps_lbl = make_label("Шаги генерации (Больше = Дольше и детальнее): 20")
        adv_layout.addWidget(steps_lbl)
        self.steps_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.steps_slider.setRange(1, 100)
        self.steps_slider.setValue(20)
        self.steps_slider.valueChanged.connect(lambda v: steps_lbl.setText(f"Шаги генерации (Больше = Дольше и детальнее): {v}"))
        adv_layout.addWidget(self.steps_slider)
        adv_layout.addWidget(make_hline())
        
        # Denoising
        denoise_lbl = make_label("Denoising Strength (Влияние на Inpaint/Img2Img): 0.75")
        adv_layout.addWidget(denoise_lbl)
        self.denoise_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.denoise_slider.setRange(0, 100)
        self.denoise_slider.setValue(75)
        self.denoise_slider.valueChanged.connect(lambda v: denoise_lbl.setText(f"Denoising Strength (Влияние на Inpaint/Img2Img): {v/100.0:.2f}"))
        adv_layout.addWidget(self.denoise_slider)
        adv_layout.addWidget(make_hline())
        
        # CFG Scale
        cfg_lbl = make_label("CFG Scale (Следование промпту): 7.0")
        adv_layout.addWidget(cfg_lbl)
        self.cfg_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.cfg_slider.setRange(10, 200) # 1.0 to 20.0
        self.cfg_slider.setValue(70)
        self.cfg_slider.valueChanged.connect(lambda v: cfg_lbl.setText(f"CFG Scale (Следование промпту): {v/10.0:.1f}"))
        adv_layout.addWidget(self.cfg_slider)
        adv_layout.addWidget(make_hline())
        
        # Negative Prompt
        adv_layout.addWidget(make_label("Негативный промпт (Нежелательные элементы)"))
        self.neg_prompt_input = QTextEdit()
        self.neg_prompt_input.setPlaceholderText("Негативный промпт\n(Нежелательные элементы)")
        self.neg_prompt_input.setFixedHeight(80)
        self.neg_prompt_input.setStyleSheet("background-color: #0A0A0A; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white;")
        adv_layout.addWidget(self.neg_prompt_input)
        adv_layout.addWidget(make_hline())
        
        # Sampler
        adv_layout.addWidget(make_label("Сэмплер (Алгоритм генерации)"))
        self.sampler_combo = NoScrollComboBox()
        self.sampler_combo.addItems(["DPM++ 2M Karras", "Euler a", "Euler", "DDIM", "DPM++ 2S a", "DPM2", "Heun"])
        adv_layout.addWidget(self.sampler_combo)
        adv_layout.addWidget(make_hline())
        
        # Seed
        adv_layout.addWidget(make_label("Зерно генерации (Seed)"))
        self.seed_input = QLineEdit("-1")
        self.seed_input.setStyleSheet("background-color: #0A0A0A; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white;")
        adv_layout.addWidget(self.seed_input)
        adv_layout.addWidget(make_hline())
        
        adv_layout.addWidget(make_hline())
        
        
        # Quantization
        adv_layout.addWidget(make_label("Точность / Квантование"))
        self.quant_combo = NoScrollComboBox()
        self.quant_combo.addItems(["4-bit (Для слабых ПК)", "8-bit (Минимум VRAM)", "16-bit (Оптимально)", "32-bit (Максимум)"])
        adv_layout.addWidget(self.quant_combo)
        adv_layout.addWidget(make_hline())

        # VRAM Mode
        adv_layout.addWidget(make_label("Использование VRAM"))
        self.vram_combo = NoScrollComboBox()
        self.vram_combo.addItems(["Без ограничений (High VRAM)", "Средне (Med VRAM)", "Минимум (Low VRAM)"])
        adv_layout.addWidget(self.vram_combo)
        img_layout.addSpacing(30)
        layout.addWidget(self.image_settings_widget)

        # --- Text Settings Container ---
        self.text_settings_widget = QWidget()
        text_layout = QVBoxLayout(self.text_settings_widget)
        text_layout.setContentsMargins(0,0,0,0)
        text_layout.addWidget(make_section_title("Настройки Текста"))
        text_layout.addWidget(make_hline())
        
        self.max_tokens_lbl = make_label("Макс. Токенов (Длина ответа): 1024")
        text_layout.addWidget(self.max_tokens_lbl)
        self.max_tokens_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.max_tokens_slider.setRange(128, 4096)
        self.max_tokens_slider.setValue(1024)
        self.max_tokens_slider.valueChanged.connect(lambda v: self.max_tokens_lbl.setText(f"Макс. Токенов (Длина ответа): {v}"))
        text_layout.addWidget(self.max_tokens_slider)
        
        self.temp_lbl = make_label("Температура (Креативность): 0.7")
        text_layout.addWidget(self.temp_lbl)
        self.temp_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(1, 20)
        self.temp_slider.setValue(7)
        self.temp_slider.valueChanged.connect(lambda v: self.temp_lbl.setText(f"Температура (Креативность): {v/10.0:.1f}"))
        text_layout.addWidget(self.temp_slider)
        
        self.top_p_lbl = make_label("Top P (Разнообразие): 0.9")
        text_layout.addWidget(self.top_p_lbl)
        self.top_p_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.top_p_slider.setRange(1, 100)
        self.top_p_slider.setValue(90)
        self.top_p_slider.valueChanged.connect(lambda v: self.top_p_lbl.setText(f"Top P (Разнообразие): {v/100.0:.2f}"))
        text_layout.addWidget(self.top_p_slider)
        
        self.rep_pen_lbl = make_label("Штраф за повторы (Rep Penalty): 1.10")
        text_layout.addWidget(self.rep_pen_lbl)
        self.rep_pen_slider = NoScrollSlider(Qt.Orientation.Horizontal)
        self.rep_pen_slider.setRange(100, 200) # 1.0 to 2.0
        self.rep_pen_slider.setValue(110)
        self.rep_pen_slider.valueChanged.connect(lambda v: self.rep_pen_lbl.setText(f"Штраф за повторы (Rep Penalty): {v/100.0:.2f}"))
        text_layout.addWidget(self.rep_pen_slider)
        
        text_layout.addWidget(make_hline())
        text_layout.addWidget(make_label("Системный Промпт (Инструкция)"))
        self.sys_prompt_input = QTextEdit()
        self.sys_prompt_input.setPlaceholderText("Введите инструкции для модели...")
        self.sys_prompt_input.setFixedHeight(80)
        self.sys_prompt_input.setStyleSheet("background-color: #0A0A0A; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white;")
        text_layout.addWidget(self.sys_prompt_input)
        
        layout.addWidget(self.text_settings_widget)
        self.text_settings_widget.hide()

        # --- System Settings ---
        layout.addWidget(make_section_title("Системные Настройки"))
        # ADetailer
        adetailer_row = QHBoxLayout()
        adetailer_info = QVBoxLayout()
        adetailer_info.addWidget(make_label("Улучшение лиц (ADetailer)"))
        adetailer_lbl2 = QLabel("Автоматически находит и делает лица кристально четкими")
        adetailer_lbl2.setStyleSheet("color: #808080; font-size: 11px;")
        adetailer_info.addWidget(adetailer_lbl2)
        adetailer_row.addLayout(adetailer_info)
        adetailer_row.addStretch()
        
        self.adetailer_check = ToggleSwitch()
        self.adetailer_check.setChecked(False)
        adetailer_row.addWidget(self.adetailer_check)
        
        layout.addLayout(adetailer_row)
        layout.addWidget(make_hline())
        
        # Color Accent
        layout.addWidget(make_label("Цветовой акцент интерфейса"))
        self.accent_combo = NoScrollComboBox()
        self.accent_combo.addItems(["Белый", "Черный", "Неоновый синий", "Малиново-красный", "Фиолетовый", "Кибер-зеленый"])
        layout.addWidget(self.accent_combo)
        layout.addWidget(make_hline())
        
        gpu_row = QHBoxLayout()
        gpu_info = QVBoxLayout()
        gpu_info.addWidget(make_label("Использовать GPU (CUDA)"))
        gpu_lbl2 = QLabel("Включи, если есть мощная видеокарта")
        gpu_lbl2.setStyleSheet("color: #808080; font-size: 11px;")
        gpu_info.addWidget(gpu_lbl2)
        gpu_row.addLayout(gpu_info)
        gpu_row.addStretch()
        
        self.gpu_check = ToggleSwitch()
        self.gpu_check.setChecked(True)
        gpu_row.addWidget(self.gpu_check)
        
        layout.addLayout(gpu_row)
        layout.addStretch()
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
        self.update_resolutions()
        
        # Load Settings
        self.batch_slider.setValue(int(self.settings.value("batch", 1)))
        self.batch_size_slider.setValue(int(self.settings.value("batch_size", 1)))
        self.steps_slider.setValue(int(self.settings.value("steps", 20)))
        self.denoise_slider.setValue(int(self.settings.value("denoise", 75)))
        self.cfg_slider.setValue(int(self.settings.value("cfg_scale", 70)))
        self.neg_prompt_input.setPlainText(str(self.settings.value("neg_prompt", "")))
        idx = self.sampler_combo.findText(str(self.settings.value("sampler", "DPM++ 2M Karras")))
        if idx >= 0: self.sampler_combo.setCurrentIndex(idx)
        self.seed_input.setText(str(self.settings.value("seed", "-1")))
        idx = self.quant_combo.findText(str(self.settings.value("quant", "8-bit (Минимум VRAM)")))
        if idx >= 0: self.quant_combo.setCurrentIndex(idx)
        idx = self.vram_combo.findText(str(self.settings.value("vram", "Средне (Med VRAM)")))
        if idx >= 0: self.vram_combo.setCurrentIndex(idx)
        idx = self.format_combo.findText(str(self.settings.value("format", "1:1 (Квадрат)")))
        if idx >= 0: self.format_combo.setCurrentIndex(idx)
        self.gpu_check.setChecked(self.settings.value("gpu", True, type=bool))
        self.adetailer_check.setChecked(self.settings.value("adetailer", False, type=bool))
        
        self.max_tokens_slider.setValue(int(self.settings.value("max_tokens", 1024)))
        self.temp_slider.setValue(int(self.settings.value("temperature", 7)))
        self.top_p_slider.setValue(int(self.settings.value("top_p", 90)))
        self.rep_pen_slider.setValue(int(self.settings.value("rep_penalty", 110)))
        self.sys_prompt_input.setPlainText(str(self.settings.value("sys_prompt", "Ты полезный AI-ассистент. Отвечай на русском языке.")))
        
        saved_accent = str(self.settings.value("accent", "Белый"))
        idx = self.accent_combo.findText(saved_accent)
        if idx >= 0: self.accent_combo.setCurrentIndex(idx)
        self.apply_accent_color(saved_accent)
        
        # Connect to save
        self.batch_slider.valueChanged.connect(self.save_settings)
        self.batch_size_slider.valueChanged.connect(self.save_settings)
        self.steps_slider.valueChanged.connect(self.save_settings)
        self.denoise_slider.valueChanged.connect(self.save_settings)
        self.cfg_slider.valueChanged.connect(self.save_settings)
        self.neg_prompt_input.textChanged.connect(self.save_settings)
        self.sampler_combo.currentIndexChanged.connect(self.save_settings)
        self.seed_input.textChanged.connect(self.save_settings)
        self.quant_combo.currentIndexChanged.connect(self.save_settings)
        self.format_combo.currentIndexChanged.connect(self.save_settings)
        self.res_combo.currentIndexChanged.connect(self.save_settings)
        self.gpu_check.toggled.connect(self.save_settings)
        self.gpu_check.toggled.connect(self.on_gpu_toggled)
        self.adetailer_check.toggled.connect(self.save_settings)
        
        self.max_tokens_slider.valueChanged.connect(self.save_settings)
        self.temp_slider.valueChanged.connect(self.save_settings)
        self.top_p_slider.valueChanged.connect(self.save_settings)
        self.rep_pen_slider.valueChanged.connect(self.save_settings)
        self.sys_prompt_input.textChanged.connect(self.save_settings)
        self.accent_combo.currentIndexChanged.connect(self.save_settings)
        self.accent_combo.currentTextChanged.connect(self.apply_accent_color)

    def on_gpu_toggled(self, checked):
        self.engine.set_device(checked)
        status = "GPU (CUDA)" if self.engine.device == "cuda" else ("GPU (MPS)" if self.engine.device == "mps" else "CPU")
        self.statusBar().showMessage(f"Устройство переключено на: {status}", 3000)

    def apply_accent_color(self, color_name):
        color_map = {
            "Белый": ("#FFFFFF", "#000000"),
            "Черный": ("#222222", "#FFFFFF"),
            "Неоновый синий": ("#00E5FF", "#000000"),
            "Малиново-красный": ("#FF0055", "#FFFFFF"),
            "Фиолетовый": ("#B900FF", "#FFFFFF"),
            "Кибер-зеленый": ("#00FF66", "#000000")
        }
        bg, text = color_map.get(color_name, ("#FFFFFF", "#000000"))
        
        ToggleSwitch.ACCENT_COLOR = bg
        
        override_qss = f"""
        QPushButton#primaryButton {{
            background-color: {bg};
            color: {text};
        }}
        QPushButton#primaryButton:hover {{
            background-color: {bg};
            opacity: 0.8;
        }}
        QProgressBar::chunk {{
            background-color: {bg};
            border-radius: 4px;
        }}
        """
        if hasattr(self, "base_stylesheet"):
            self.setStyleSheet(self.base_stylesheet + "\n" + override_qss)
        self.update()

    def update_resolutions(self):
        self.res_combo.clear()
        fmt = self.format_combo.currentText()
        if "1:1" in fmt:
            self.res_combo.addItems(["256x256", "384x384", "512x512", "768x768", "1024x1024"])
        elif "16:9" in fmt:
            self.res_combo.addItems(["426x240", "640x360", "910x512", "1280x720", "1920x1080"])
        elif "9:16" in fmt:
            self.res_combo.addItems(["240x426", "360x640", "512x910", "720x1280", "1080x1920"])
        elif "4:3" in fmt:
            self.res_combo.addItems(["320x240", "512x384", "1024x768", "1152x864"])
        elif "3:4" in fmt:
            self.res_combo.addItems(["240x320", "384x512", "768x1024", "864x1152"])
        elif "21:9" in fmt:
            self.res_combo.addItems(["560x240", "1536x640"])
        
        saved_res = str(self.settings.value("resolution", "512x512"))
        idx = self.res_combo.findText(saved_res)
        if idx >= 0:
            self.res_combo.setCurrentIndex(idx)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения", self.folder_input.text())
        if folder:
            self.folder_input.setText(folder)
            self.save_settings()

    def save_settings(self):
        if hasattr(self, 'folder_input'):
            self.settings.setValue("output_folder", self.folder_input.text())
            self.settings.setValue("play_sound", self.sound_check.isChecked())
        self.settings.setValue("batch", self.batch_slider.value())
        self.settings.setValue("batch_size", self.batch_size_slider.value())
        self.settings.setValue("steps", self.steps_slider.value())
        self.settings.setValue("denoise", self.denoise_slider.value())
        self.settings.setValue("cfg_scale", self.cfg_slider.value())
        self.settings.setValue("neg_prompt", self.neg_prompt_input.toPlainText())
        self.settings.setValue("sampler", self.sampler_combo.currentText())
        self.settings.setValue("seed", self.seed_input.text())
        self.settings.setValue("quant", self.quant_combo.currentText())
        self.settings.setValue("vram", self.vram_combo.currentText())
        self.settings.setValue("format", self.format_combo.currentText())
        self.settings.setValue("resolution", self.res_combo.currentText())
        self.settings.setValue("gpu", self.gpu_check.isChecked())
        self.settings.setValue("adetailer", self.adetailer_check.isChecked())
        self.settings.setValue("accent", self.accent_combo.currentText())
        
        if hasattr(self, 'max_tokens_slider'):
            self.settings.setValue("max_tokens", self.max_tokens_slider.value())
            self.settings.setValue("temperature", self.temp_slider.value())
            self.settings.setValue("top_p", self.top_p_slider.value())
            self.settings.setValue("rep_penalty", self.rep_pen_slider.value())
            self.settings.setValue("sys_prompt", self.sys_prompt_input.toPlainText())

    def apply_optimal_settings(self, model_name):
        if not model_name: return
        if getattr(self, "_last_optimal_model", "") == model_name:
            return
        self._last_optimal_model = model_name
        name_lower = model_name.lower()
        
        if "schnell" in name_lower or "flux" in name_lower:
            steps = 4
            cfg = 1.0
            target_pixels = 1024 * 1024
        elif "xl" in name_lower or "sdxl" in name_lower or "animagine" in name_lower:
            steps = 35
            cfg = 6.0
            target_pixels = 1024 * 1024
        elif "i2vgen" in name_lower or "stable-video" in name_lower:
            steps = 25
            cfg = 9.0
            target_pixels = 512 * 512
        else:
            # Default SD 1.5
            steps = 25
            cfg = 7.0
            target_pixels = 512 * 512
            
        self.steps_slider.setValue(steps)
        self.cfg_slider.setValue(int(cfg * 10))
        
        best_idx = 0
        min_diff = float('inf')
        for i in range(self.res_combo.count()):
            text = self.res_combo.itemText(i)
            try:
                w, h = map(int, text.split('x'))
                diff = abs((w * h) - target_pixels)
                if diff < min_diff:
                    min_diff = diff
                    best_idx = i
            except: pass
            
        if min_diff != float('inf'):
            self.res_combo.setCurrentIndex(best_idx)
        

    def setup_addons_tab(self):
        layout = QVBoxLayout(self.tab_addons)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)
        
        title_lbl = QLabel("Дополнения")
        title_lbl.setStyleSheet("font-family: 'Lora', serif; font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(title_lbl)
        
        # Animated Tab Bar for LoRA / ControlNet
        self.addons_cat_bar = AnimatedTabBar(["SFW LoRA", "NSFW LoRA", "ControlNet"])
        self.addons_cat_bar.tabChanged.connect(self.on_addons_cat_changed)
        self.current_addons_cat = 0
        
        cat_container = QHBoxLayout()
        cat_container.addWidget(self.addons_cat_bar)
        cat_container.addStretch()
        layout.addLayout(cat_container)
        
        # Search
        self.addon_search_input = QLineEdit()
        self.addon_search_input.setPlaceholderText("🔍 Поиск по названию...")
        self.addon_search_input.setStyleSheet("background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white; font-size: 14px;")
        self.addon_search_input.textChanged.connect(self.load_addons)
        layout.addWidget(self.addon_search_input)
        
        # Scrollable list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.addons_scroll_widget = QWidget()
        self.addons_layout = QVBoxLayout(self.addons_scroll_widget)
        self.addons_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.addons_layout.setSpacing(12)
        
        scroll.setWidget(self.addons_scroll_widget)
        layout.addWidget(scroll)
        
        # Populate recommended lists
        self._lora_list = [
            {"name": "Canopus Realism LoRA", "id": "prithivMLmods/Canopus-Realism-LoRA", "desc": "Повышает реалистичность генерации."},
            {"name": "Detail Tweaker XL", "id": "OedoSoldier/detail-tweaker-xl", "desc": "Усиливает детализацию для SDXL."},
            {"name": "Pixel Art XL", "id": "nerijs/pixel-art-xl", "desc": "Пиксельная графика в стиле ретро-игр для SDXL."},
            {"name": "Watercolor Style", "id": "ostris/watercolor_style_lora_sdxl", "desc": "Стиль акварельной живописи для SDXL."},
            {"name": "Logo Design LoRA", "id": "ostris/logo-design-lora", "desc": "Создание логотипов."},
            {"name": "Midjourney Style", "id": "Jovie/Midjourney", "desc": "Стиль, похожий на Midjourney V6."},
        ]
        
        self._nsfw_lora_list = [
            # Fallback list for NSFW (many HF ones are gated)
            {"name": "Pony Realism (Base)", "id": "lustlyai/Pony_Realism", "desc": "Улучшает реалистичность (если есть доступ)."},
            {"name": "SDXL NSFW Enhancer", "id": "boda/sdxl-nsfw-enhancer", "desc": "Общее улучшение NSFW контента."},
        ]
        
        self._controlnet_list = [
            {"name": "Canny SDXL", "id": "xinsir/controlnet-canny-sdxl-1.0", "desc": "Детекция контуров (Canny) для SDXL. Генерация по контуру изображения."},
            {"name": "Depth SDXL", "id": "diffusers/controlnet-depth-sdxl-1.0", "desc": "Карта глубины для SDXL. Сохраняет пространственную структуру."},
            {"name": "Canny SD 1.5", "id": "lllyasviel/sd-controlnet-canny", "desc": "Детекция контуров (Canny) для SD 1.5."},
            {"name": "OpenPose SD 1.5", "id": "lllyasviel/sd-controlnet-openpose", "desc": "Определение позы человека. Генерация в нужной позе."},
            {"name": "Depth SD 1.5", "id": "lllyasviel/sd-controlnet-depth", "desc": "Карта глубины для SD 1.5."},
            {"name": "Scribble SD 1.5", "id": "lllyasviel/sd-controlnet-scribble", "desc": "Генерация по наброскам / скетчам."},
            {"name": "Tile SD 1.5", "id": "lllyasviel/control_v11f1e_sd15_tile", "desc": "Апскейл и улучшение детализации изображения."},
            {"name": "Softedge SD 1.5", "id": "lllyasviel/control_v11p_sd15_softedge", "desc": "Мягкие контуры для более натуральной генерации."},
            {"name": "IP-Adapter FaceID", "id": "h94/IP-Adapter-FaceID", "desc": "Перенос лица с референса на генерацию."},
        ]
        
        # Load dynamic lists from HF cache
        self._load_dynamic_addon_lists()
        
        self.load_addons()
    
    def _load_dynamic_addon_lists(self):
        """Load additional LoRA/ControlNet lists from cached JSON if available."""
        addons_file = os.path.join(APP_DATA_DIR, 'addons.json')
        if os.path.exists(addons_file):
            try:
                import json
                with open(addons_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if 'lora' in data and isinstance(data['lora'], list):
                    existing_ids = {m['id'] for m in self._lora_list}
                    for m in data['lora']:
                        if m.get('id') not in existing_ids:
                            self._lora_list.append(m)
                if 'controlnet' in data and isinstance(data['controlnet'], list):
                    existing_ids = {m['id'] for m in self._controlnet_list}
                    for m in data['controlnet']:
                        if m.get('id') not in existing_ids:
                            self._controlnet_list.append(m)
            except Exception as e:
                print("Error loading addons.json:", e)
    
    def on_addons_cat_changed(self, idx):
        self.current_addons_cat = idx
        self.load_addons()
    
    def load_addons(self):
        self._clear_layout(self.addons_layout)
        
        # Custom ID input at the top
        custom_layout = QHBoxLayout()
        custom_input = QLineEdit()
        
        if self.current_addons_cat == 0:
            addon_type = "SFW LoRA"
            placeholder = "prithivMLmods/Canopus-Realism-LoRA"
            self.addon_lora_input = custom_input
            items = self._lora_list
        elif self.current_addons_cat == 1:
            addon_type = "NSFW LoRA"
            placeholder = "lustlyai/Pony_Realism"
            self.addon_lora_input = custom_input
            items = self._nsfw_lora_list
        else:
            addon_type = "ControlNet"
            placeholder = "xinsir/controlnet-canny-sdxl-1.0"
            self.addon_cnet_input = custom_input
            items = self._controlnet_list
            
        custom_input.setPlaceholderText(f"Введите HuggingFace ID {addon_type} (например: {placeholder})")
        custom_input.setStyleSheet("background-color: #0A0A0A; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white; font-size: 14px;")
        
        custom_btn = QPushButton("Добавить")
        custom_btn.setStyleSheet("background-color: #FFFFFF; color: #000000; border-radius: 8px; padding: 10px 20px; font-weight: bold;")
        custom_btn.clicked.connect(lambda: self._add_custom_addon(custom_input.text().strip()))
        
        custom_layout.addWidget(custom_input)
        custom_layout.addWidget(custom_btn)
        
        container = QWidget()
        container.setLayout(custom_layout)
        self.addons_layout.addWidget(container)
        self.addons_layout.addSpacing(10)
        
        search_term = self.addon_search_input.text().lower()
        
        row = 0
        for addon_info in items:
            if search_term:
                searchable = f"{addon_info.get('name', '')} {addon_info.get('desc', '')} {addon_info.get('id', '')}".lower()
                if search_term not in searchable:
                    continue
            card = self._create_addon_card(addon_info)
            self.addons_layout.addWidget(card)
            row += 1
    
    def _add_custom_addon(self, addon_id):
        if not addon_id or '/' not in addon_id:
            return
        name = addon_id.split('/')[-1].replace('-', ' ').title()
        entry = {"name": name, "id": addon_id, "desc": f"Пользовательское дополнение: {addon_id}"}
        if self.current_addons_cat == 0:
            if not any(m['id'] == addon_id for m in self._lora_list):
                self._lora_list.insert(0, entry)
        elif self.current_addons_cat == 1:
            if not any(m['id'] == addon_id for m in self._nsfw_lora_list):
                self._nsfw_lora_list.insert(0, entry)
        else:
            if not any(m['id'] == addon_id for m in self._controlnet_list):
                self._controlnet_list.insert(0, entry)
        self.load_addons()
    
    def _create_addon_card(self, addon_info):
        card = QFrame()
        card.setObjectName("glassPanel")
        
        main_hlayout = QHBoxLayout(card)
        main_hlayout.setContentsMargins(20, 15, 20, 15)
        
        left_col = QVBoxLayout()
        left_col.setSpacing(6)
        
        name_lbl = QLabel(addon_info.get("name", addon_info["id"].split("/")[-1]))
        name_lbl.setWordWrap(True)
        name_lbl.setMinimumWidth(1)
        name_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        left_col.addWidget(name_lbl)
        
        addon_id = addon_info["id"]
        
        id_row = QHBoxLayout()
        type_tag = "SFW LoRA" if self.current_addons_cat == 0 else "NSFW LoRA" if self.current_addons_cat == 1 else "ControlNet"
        tag_color = "#FF9800" if self.current_addons_cat in [0, 1] else "#2196F3"
        tag_lbl = QLabel(type_tag)
        tag_lbl.setStyleSheet(f"background-color: {tag_color}; color: #FFFFFF; font-weight: bold; font-size: 11px; padding: 3px 8px; border-radius: 6px;")
        id_row.addWidget(tag_lbl)
        
        id_lbl = QLabel(addon_id)
        id_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        id_row.addWidget(id_lbl)
        id_row.addStretch()
        left_col.addLayout(id_row)
        
        desc_lbl = QLabel(addon_info.get("desc", ""))
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumWidth(1)
        desc_lbl.setStyleSheet("color: #BBBBBB; font-size: 13px; margin-top: 3px;")
        left_col.addWidget(desc_lbl)
        
        main_hlayout.addLayout(left_col, stretch=1)
        
        # Right side buttons
        right_row = QHBoxLayout()
        right_row.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Check if it's selected in settings
        is_active = False
        if self.current_addons_cat in [0, 1]:
            is_active = (getattr(self, 'selected_lora_id', None) == addon_id)
        else:
            is_active = (getattr(self, 'selected_controlnet_id', None) == addon_id)
        
        is_downloading = (getattr(self, 'downloading_model_id', None) == addon_id)
        
        if is_downloading:
            self.model_dl_progress_bar = QProgressBar()
            self.model_dl_progress_bar.setFixedWidth(150)
            self.model_dl_progress_bar.setFixedHeight(8)
            self.model_dl_progress_bar.setTextVisible(False)
            self.model_dl_progress_bar.setStyleSheet("QProgressBar { border: none; background-color: #222222; border-radius: 4px; } QProgressBar::chunk { background-color: #FFFFFF; border-radius: 4px; }")
            
            self.model_dl_status_lbl = QLabel("Инициализация...")
            self.model_dl_status_lbl.setStyleSheet("color: #888888; font-size: 11px;")
            
            dl_v = QVBoxLayout()
            dl_v.addWidget(self.model_dl_status_lbl)
            dl_v.addWidget(self.model_dl_progress_bar)
            right_row.addLayout(dl_v)
            
            cancel_dl_btn = QPushButton("Отмена")
            cancel_dl_btn.setFixedSize(80, 32)
            cancel_dl_btn.setStyleSheet("background-color: transparent; border: 1px solid #C62828; color: #C62828; border-radius: 6px; font-weight: bold; font-size: 12px;")
            # cancel_dl_btn.clicked.connect(self.cancel_addon_load) # We don't have this yet, just disable button for now
            cancel_dl_btn.setEnabled(False)
            right_row.addWidget(cancel_dl_btn)
        else:
            if is_active:
                btn = QPushButton("✓ Выбрано")
                btn.setStyleSheet("background-color: #FFFFFF; color: #000000; font-weight: bold; border-radius: 8px; padding: 8px 20px; font-size: 14px;")
                btn.clicked.connect(lambda checked, aid=addon_id: self._deselect_addon())
                right_row.addWidget(btn)
            else:
                if self._is_addon_downloaded(addon_id):
                    select_btn = QPushButton("▶ Выбрать")
                    select_btn.setStyleSheet("background-color: transparent; color: #FFFFFF; font-weight: bold; border: 1px solid rgba(255,255,255,0.4); border-radius: 8px; padding: 8px 20px; font-size: 14px;")
                    select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    select_btn.clicked.connect(lambda checked, aid=addon_id: self._select_addon(aid))
                    right_row.addWidget(select_btn)
                else:
                    dl_btn = QPushButton("Скачать")
                    dl_btn.setStyleSheet("background-color: #111111; color: #FFFFFF; font-weight: bold; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 8px 20px; font-size: 14px;")
                    dl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    dl_btn.clicked.connect(lambda checked, aid=addon_id: self.start_addon_download(aid))
                    right_row.addWidget(dl_btn)
        
        main_hlayout.addLayout(right_row)
        return card
    
    def _show_toast(self, text, duration=3000):
        toast = ToastNotification(self, text, duration)
        toast.show_toast()

    def _sync_lora_selection(self, idx):
        if idx <= 0:
            self.selected_lora_id = None
        else:
            self.selected_lora_id = self.lora_input.itemText(idx)
        if self.stack.currentIndex() == 4:
            self.load_addons()

    def _sync_cnet_selection(self, idx):
        if idx <= 0:
            self.selected_controlnet_id = None
        else:
            self.selected_controlnet_id = self.cnet_input.itemText(idx)
        if self.stack.currentIndex() == 4:
            self.load_addons()

    def _deselect_addon(self):
        if self.current_addons_cat in [0, 1]:
            self.selected_lora_id = None
            if hasattr(self, 'lora_input') and self.lora_input is not None:
                self.lora_input.setCurrentText("")
        else:
            self.selected_controlnet_id = None
            if hasattr(self, 'cnet_input') and self.cnet_input is not None:
                self.cnet_input.setCurrentText("")
        self.load_addons()

    def _select_addon(self, addon_id):
        if self.current_addons_cat in [0, 1]:
            # LoRA
            if hasattr(self, 'lora_input') and self.lora_input is not None:
                idx = self.lora_input.findText(addon_id)
                if idx < 0:
                    self.lora_input.addItem(addon_id)
                    idx = self.lora_input.findText(addon_id)
                self.lora_input.setCurrentIndex(idx)
            self.selected_lora_id = addon_id
            self._show_toast(f"LoRA выбрана: {addon_id}")
        else:
            # ControlNet
            if hasattr(self, 'cnet_input') and self.cnet_input is not None:
                idx = self.cnet_input.findText(addon_id)
                if idx < 0:
                    self.cnet_input.addItem(addon_id)
                    idx = self.cnet_input.findText(addon_id)
                self.cnet_input.setCurrentIndex(idx)
            self.selected_controlnet_id = addon_id
            self._show_toast(f"ControlNet выбран: {addon_id}")
        self.load_addons()

    def setup_models_tab(self):
        layout = QVBoxLayout(self.tab_models)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)
        
        title_lbl = QLabel("Управление моделями")
        title_lbl.setStyleSheet("font-family: 'Lora', serif; font-size: 24px; font-weight: bold; color: white;")
        layout.addWidget(title_lbl)
        
        # Animated Tab Bar for Categories
        self.models_cat_bar = AnimatedTabBar(["Фото", "Видео", "Текст", "Скачанные"])
        self.models_cat_bar.tabChanged.connect(self.on_models_cat_changed)
        
        self.safety_filter_bar = AnimatedTabBar(["SFW", "NSFW"])
        self.safety_filter_bar.tabChanged.connect(self.on_safety_filter_changed)
        
        cat_container = QVBoxLayout()
        cat_container.setSpacing(10)
        
        row1 = QHBoxLayout()
        row1.addWidget(self.models_cat_bar)
        row1.addStretch()
        cat_container.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addWidget(self.safety_filter_bar)
        row2.addStretch()
        cat_container.addLayout(row2)
        
        layout.addLayout(cat_container)
        
        self.model_search_input = QLineEdit()
        self.model_search_input.setPlaceholderText("🔍 Поиск по стилю, названию или описанию (например: аниме, реализм)...")
        self.model_search_input.setStyleSheet("background-color: #1A1A1A; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white; font-size: 14px; margin-top: 10px; margin-bottom: 5px;")
        self.model_search_input.textChanged.connect(self.load_models)
        layout.addWidget(self.model_search_input)
        
        self.models_scroll = QScrollArea()
        self.models_scroll.setWidgetResizable(True)
        self.models_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.models_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.models_widget = QWidget()
        self.models_layout = QVBoxLayout(self.models_widget)
        self.models_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.models_layout.setContentsMargins(0, 0, 25, 25)
        self.models_layout.setSpacing(15)
        self.models_scroll.setWidget(self.models_widget)
        
        layout.addWidget(self.models_scroll)
        self.current_models_cat = 0
        
    def update_models_db(self):
        self.update_models_btn.setText("Обновление... (загрузка ~300 моделей)")
        self.update_models_btn.setEnabled(False)
        import subprocess
        import sys
        
        def run_update():
            subprocess.run([sys.executable, "fetch_hf_models.py"], cwd=os.getcwd())
            
        import threading
        def _thread():
            run_update()
            # Inform user to restart app for now
            print("Update complete! Please restart the app.")
        threading.Thread(target=_thread, daemon=True).start()

    def on_models_cat_changed(self, idx):
        self.current_models_cat = idx
        self.load_models()
        
    def on_safety_filter_changed(self, idx):
        self.current_safety_filter = idx
        self.load_models()
        
    def create_model_card(self, model_info):
        card = QFrame()
        card.setObjectName("glassPanel")
        
        main_hlayout = QHBoxLayout(card)
        main_hlayout.setContentsMargins(20, 20, 20, 20)
        
        left_col = QVBoxLayout()
        left_col.setSpacing(8)
        
        name_lbl = QLabel(model_info.get("name", model_info.get("id").split("/")[-1]))
        name_lbl.setWordWrap(True)
        name_lbl.setMinimumWidth(1)
        name_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        name_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        left_col.addWidget(name_lbl)
        
        model_id = model_info["id"]
        id_row = QHBoxLayout()
        
        def add_tag(text, color, bg):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"background-color: {bg}; color: {color}; font-weight: bold; font-size: 11px; padding: 3px 8px; border-radius: 6px;")
            id_row.addWidget(lbl)
            
        if "class" in model_info:
            add_tag(model_info["class"], "#000000", "#FFFFFF")
        if model_info.get("safety") == "NSFW" or "nsfw" in model_info.get("id", "").lower() or "nsfw" in model_info.get("name", "").lower():
            add_tag("NSFW", "#FFFFFF", "#D32F2F")
        elif model_info.get("safety") == "SFW":
            add_tag("SFW", "#FFFFFF", "#4CAF50")
            
        
        icons_row = QHBoxLayout()
        icons_row.setSpacing(15)
        
        # Calculate real size
        is_downloaded = os.path.exists(os.path.join(self.engine.models_dir, f"models--{model_id.replace('/', '--')}"))
        
        if is_downloaded:
            def get_dir_size(path='.'):
                total = 0
                with os.scandir(path) as it:
                    for entry in it:
                        if entry.is_file(): total += entry.stat().st_size
                        elif entry.is_dir(): total += get_dir_size(entry.path)
                return total
            real_size_bytes = get_dir_size(os.path.join(self.engine.models_dir, f"models--{model_id.replace('/', '--')}"))
            size_gb = real_size_bytes / (1024**3)
            size_str = f"{size_gb:.2f} ГБ"
        else:
            size_gb = model_info.get("size_gb", 2.0)
            size_str = f"~{size_gb:.2f} ГБ"
            
        weight_lbl = "Легкая" if size_gb < 5.0 else ("Средняя" if size_gb < 15.0 else "Тяжелая")
        weight_color = "#4CAF50" if size_gb < 5.0 else ("#FF9800" if size_gb < 15.0 else "#F44336")
        add_tag(weight_lbl, "#FFFFFF", weight_color)
        
        id_row.addStretch()
        left_col.addLayout(id_row)
            
        lbl_size = QLabel(f"💾 {size_str}")
        lbl_size.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        icons_row.addWidget(lbl_size)
        
        req = model_info.get("req", "VRAM 4GB+")
        lbl_req = QLabel(f"🖥 {req}")
        lbl_req.setStyleSheet("color: #A0A0A0; font-size: 12px;")
        icons_row.addWidget(lbl_req)
        
        if is_downloaded:
            dl_lbl = QLabel("✔ Скачано")
            dl_lbl.setStyleSheet("color: #4CAF50; font-size: 12px;")
            icons_row.addWidget(dl_lbl)
            
        icons_row.addStretch()
        left_col.addLayout(icons_row)
        
        desc_lbl = QLabel(model_info.get("desc", ""))
        desc_lbl.setWordWrap(True)
        desc_lbl.setMinimumWidth(1)
        desc_lbl.setStyleSheet("color: #DDDDDD; font-size: 14px; margin-top: 5px; font-family: 'Lora', serif;")
        left_col.addWidget(desc_lbl)
        
        main_hlayout.addLayout(left_col, stretch=1)
        
        right_row = QHBoxLayout()
        right_row.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        is_downloading = (model_id == getattr(self, "downloading_model_id", None))
        
        if is_downloading:
            self.model_dl_progress_bar = QProgressBar()
            self.model_dl_progress_bar.setFixedWidth(150)
            self.model_dl_progress_bar.setFixedHeight(8)
            self.model_dl_progress_bar.setTextVisible(False)
            self.model_dl_progress_bar.setStyleSheet("QProgressBar { border: none; background-color: #222222; border-radius: 4px; } QProgressBar::chunk { background-color: #FFFFFF; border-radius: 4px; }")
            
            self.model_dl_status_lbl = QLabel("Инициализация...")
            self.model_dl_status_lbl.setStyleSheet("color: #888888; font-size: 11px;")
            
            dl_v = QVBoxLayout()
            dl_v.addWidget(self.model_dl_status_lbl)
            dl_v.addWidget(self.model_dl_progress_bar)
            right_row.addLayout(dl_v)
            
            cancel_dl_btn = QPushButton("Отмена")
            cancel_dl_btn.setFixedSize(80, 32)
            cancel_dl_btn.setStyleSheet("background-color: transparent; border: 1px solid #C62828; color: #C62828; border-radius: 6px; font-weight: bold; font-size: 12px;")
            cancel_dl_btn.clicked.connect(self.cancel_model_load)
            right_row.addWidget(cancel_dl_btn)
            
        elif is_downloaded:
            trash_btn = QPushButton()
            trash_btn.setIcon(QIcon(get_asset_path("assets/icons/trash.svg")))
            trash_btn.setIconSize(QSize(20, 20))
            trash_btn.setFixedSize(36, 36)
            trash_btn.setStyleSheet("background-color: transparent; border: none;")
            trash_btn.clicked.connect(lambda checked, mid=model_id: self.delete_model_from_disk(mid))
            right_row.addWidget(trash_btn)
            
            is_active = (self.model_combo.currentText() == model_id)
            is_loaded = (self.engine.current_model_id == model_id and self.engine.pipe is not None) or \
                        (getattr(self.engine, 'current_text_model_id', None) == model_id and getattr(self.engine, 'llm_pipeline', None) is not None)
            
            if is_loaded:
                unload_btn = QPushButton("Выгрузить из памяти")
                unload_btn.setStyleSheet("background-color: transparent; color: #E50914; border: 1px solid #E50914; border-radius: 8px; padding: 8px 15px; font-size: 14px; margin-right: 10px;")
                unload_btn.clicked.connect(self.unload_active_model)
                right_row.addWidget(unload_btn)
                
                btn = QPushButton("В памяти")
                btn.setStyleSheet("background-color: #FFFFFF; color: #000000; font-weight: bold; border-radius: 8px; padding: 8px 20px; font-size: 15px;")
                btn.setEnabled(False)
                right_row.addWidget(btn)
            elif is_active:
                load_btn = QPushButton("Загрузить в память")
                load_btn.setStyleSheet("background-color: transparent; color: #4CAF50; border: 1px solid #4CAF50; border-radius: 8px; padding: 8px 15px; font-size: 14px; margin-right: 10px;")
                load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                load_btn.clicked.connect(lambda checked, mid=model_id: self.start_model_load(mid))
                right_row.addWidget(load_btn)
                
                btn = QPushButton("Выбрана (ждет)")
                btn.setStyleSheet("background-color: #555555; color: #FFFFFF; font-weight: bold; border-radius: 8px; padding: 8px 20px; font-size: 15px;")
                btn.setEnabled(False)
                right_row.addWidget(btn)
            else:
                btn = QPushButton("▶ Выбрать")
                btn.setStyleSheet("background-color: #111111; color: #FFFFFF; font-weight: bold; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 8px 20px; font-size: 15px;")
                btn.clicked.connect(lambda checked, mid=model_id: self.select_model(mid))
                right_row.addWidget(btn)
        else:
            req_lbl = QLabel("Требуется скачивание")
            req_lbl.setStyleSheet("color: #888888; font-size: 12px; margin-right: 10px;")
            right_row.addWidget(req_lbl)
            
            btn = QPushButton("Скачать")
            btn.setStyleSheet("background-color: #111111; color: #FFFFFF; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; padding: 8px 20px; font-size: 14px;")
            btn.clicked.connect(lambda checked, mid=model_id: self.start_model_load(mid))
            right_row.addWidget(btn)
            
        main_hlayout.addLayout(right_row)
        return card

    def delete_model_from_disk(self, model_id):
        self.engine.delete_model(model_id)
        self.load_models()

    def select_model(self, model_id):
        self.model_combo.setCurrentText(model_id)
        self.load_models() # refresh UI so it shows "Выбрана"
            
    def unload_active_model(self):
        self.engine.unload_model()
        self.load_models()
    def open_gallery_image_in_canvas(self, path):
        self._set_attachment(path, False)
        self.nav_bar.select_tab(0) # Switch to Chat tab
            
    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    self._clear_layout(child.layout())

    def cancel_model_load(self):
        if hasattr(self, "dl_worker") and self.dl_worker.isRunning():
            self.dl_worker.terminate()
            self.dl_worker.wait()
            import sys
            sys.stderr = sys.__stderr__
        self.downloading_model_id = None
        self.dl_finished(False, "Отменено")

    def start_model_load(self, model_id):
        # Memory checks
        import psutil
        import shutil

        # Find model info
        m_info = next((m for m in RECOMMENDED_MODELS if m["id"] == model_id), None)
        size_gb = m_info.get("size_gb", 6.0) if m_info else 6.0
        
        # Check Disk Space (if not downloaded)
        is_downloaded = os.path.exists(os.path.join(self.engine.models_dir, f"models--{model_id.replace('/', '--')}"))
        if not is_downloaded:
            free_disk_gb = shutil.disk_usage(self.engine.models_dir).free / (1024**3)
            if free_disk_gb < size_gb + 2.0: # 2GB buffer
                self._show_toast(f"✖ Недостаточно места на диске! Требуется: ~{size_gb:.1f} ГБ", 5000)
                return
                
        # Check RAM
        free_ram_gb = psutil.virtual_memory().available / (1024**3)
        if free_ram_gb < size_gb * 0.8: # If RAM is significantly less than model size
            self._show_toast(f"⚠ Внимание: Свободно {free_ram_gb:.1f} ГБ ОЗУ. Возможны зависания.", 5000)

        self.downloading_model_id = model_id
        self.load_models()
        
        q_text = self.quant_combo.currentText()
        precision = "fp16"
        if "4-bit" in q_text: precision = "4-bit"
        elif "8-bit" in q_text: precision = "8-bit"
        elif "32-bit" in q_text: precision = "fp32"
        
        vram_text = self.vram_combo.currentText()
        vram_mode = "high"
        if "Low" in vram_text: vram_mode = "low"
        elif "Med" in vram_text: vram_mode = "med"
        
        # Find model type
        model_type = "Photo"
        for m in RECOMMENDED_MODELS:
            if m["id"] == model_id:
                model_type = m.get("type", "Photo")
                break
                
        self.dl_worker = ModelLoadWorker(self.engine, model_id, precision, vram_mode, model_type=model_type)
        self.dl_worker.progress_signal.connect(self.update_dl_progress)
        self.dl_worker.finished_signal.connect(self.dl_finished)
        self.dl_worker.start()
        
    def _dl_widget_alive(self, name):
        w = getattr(self, name, None)
        if w is None:
            return False
        from PyQt6 import sip
        try:
            return not sip.isdeleted(w)
        except Exception:
            return False

    def update_dl_progress(self, msg):
        import re
        match = re.search(r'(\d+)%', msg)
        if match:
            pct = int(match.group(1))

            # Prevent jumping down (HuggingFace sometimes resets progress for multiple files)
            if not hasattr(self, "_dl_max_pct"):
                self._dl_max_pct = 0
            if pct < self._dl_max_pct and (self._dl_max_pct - pct) > 20:
                # If it dropped significantly, it's probably a new file in a multi-file download
                pass # Just show the new file progress, but it's jumping. Actually, let's keep it simple.

            if self._dl_widget_alive("model_dl_status_lbl"):
                # If we're at 100% or very close, call it Initialization
                if pct > 98:
                    self.model_dl_status_lbl.setText("Инициализация...")
                else:
                    self.model_dl_status_lbl.setText(f"Скачивание: {pct}%")
            if self._dl_widget_alive("model_dl_progress_bar"):
                self.model_dl_progress_bar.setValue(pct)
        
    def dl_finished(self, success, msg):
        self.downloading_model_id = None
        self.load_models()
        if not success:
            if "Отменено" in msg:
                self._show_toast("Отменено", 3000)
            else:
                from PyQt6.QtWidgets import QMessageBox
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("Ошибка загрузки")
                msg_box.setText("Не удалось загрузить модель.")
                msg_box.setInformativeText(msg)
                msg_box.setStyleSheet("background-color: #1A1A1A; color: white;")
                msg_box.exec()

    def _is_addon_downloaded(self, addon_id):
        import os
        from huggingface_hub.constants import HUGGINGFACE_HUB_CACHE
        # Simplistic check if the repo folder exists in cache
        # e.g., models--ostris--ip-composition-adapter
        repo_folder = "models--" + addon_id.replace("/", "--")
        cache_path = os.path.join(HUGGINGFACE_HUB_CACHE, repo_folder)
        return os.path.exists(cache_path)

    def start_addon_download(self, addon_id):
        if hasattr(self, 'dl_worker') and self.dl_worker.isRunning():
            self._show_toast("Уже идет загрузка!", 3000)
            return
            
        self.downloading_model_id = addon_id
        self.load_addons()
        
        self.dl_worker = AddonDownloadWorker(self.engine, addon_id)
        self.dl_worker.progress_signal.connect(self.update_dl_progress)
        self.dl_worker.finished_signal.connect(self.addon_dl_finished)
        self.dl_worker.start()

    def addon_dl_finished(self, success, msg):
        self.downloading_model_id = None
        self.load_addons()
        if success:
            self._show_toast("✔ Дополнение скачано!", 3000)
        else:
            if "Отменено" in msg:
                self._show_toast("Отменено", 3000)
            else:
                self._show_toast(f"✖ Ошибка загрузки: {msg}", 6000)
            
    def setup_gallery_tab(self):
        layout = QVBoxLayout(self.tab_gallery)
        self.gallery_area = QScrollArea()
        self.gallery_area.setWidgetResizable(True)
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.gallery_area.setWidget(self.gallery_widget)
        layout.addWidget(self.gallery_area)
        
    def load_gallery(self):
        while self.gallery_layout.count():
            child = self.gallery_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if not os.path.exists(OUTPUTS_DIR): return
        files = [os.path.join(OUTPUTS_DIR, f) for f in os.listdir(OUTPUTS_DIR) if f.lower().endswith(".png") and not "mask" in f]
        files.sort(key=os.path.getmtime, reverse=True)
        
        row = 0
        col = 0
        for fp in files[:40]: # Show last 40
            lbl = ClickableImageLabel()
            lbl.path = fp
            lbl.setPixmap(QPixmap(fp).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            lbl.clicked.connect(self.open_gallery_image_in_canvas)
            self.gallery_layout.addWidget(lbl, row, col)
            col += 1
            if col > 3:
                col = 0
                row += 1

    def load_models(self):
        self._clear_layout(self.models_layout)
            
        models_to_show = []
        if self.current_models_cat == 3: # Local / Custom
            custom_layout = QHBoxLayout()
            self.custom_id_input = QLineEdit()
            self.custom_id_input.setPlaceholderText("Например: black-forest-labs/FLUX.1-schnell")
            self.custom_id_input.setStyleSheet("background-color: #0A0A0A; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 10px; color: white; font-size: 15px;")
            
            custom_dl_btn = QPushButton("Скачать / Добавить")
            custom_dl_btn.setStyleSheet("background-color: #FFFFFF; color: #000000; border-radius: 8px; padding: 10px 20px; font-weight: bold;")
            custom_dl_btn.clicked.connect(self.add_custom_model)
            
            custom_layout.addWidget(self.custom_id_input)
            custom_layout.addWidget(custom_dl_btn)
            
            container = QWidget()
            container.setLayout(custom_layout)
            self.models_layout.addWidget(container)
            self.models_layout.addSpacing(20)
            
            title = QLabel("Скачанные модели (локально):")
            title.setStyleSheet("font-family: 'Lora', serif; font-size: 18px; font-weight: bold; color: white;")
            self.models_layout.addWidget(title)
            
            safety_str = "SFW" if getattr(self, "current_safety_filter", 0) == 0 else "NSFW"
            
            if os.path.exists(self.engine.models_dir):
                for d in os.listdir(self.engine.models_dir):
                    if d.startswith("models--"):
                        m_id = d.replace("models--", "").replace("--", "/")
                        found = next((m for m in RECOMMENDED_MODELS if m["id"] == m_id), None)
                        if found:
                            if found.get("safety", "SFW") == safety_str:
                                models_to_show.append(found)
                        else:
                            models_to_show.append({"id": m_id, "name": m_id.split("/")[-1], "class": "Local", "safety": "SFW"})
        else:
            safety_str = "SFW" if getattr(self, "current_safety_filter", 0) == 0 else "NSFW"
            
            if self.current_models_cat == 0:
                cat_type = "Photo"
            elif self.current_models_cat == 1:
                cat_type = "Video"
            else:
                cat_type = "Text"

            for m in RECOMMENDED_MODELS:
                m_type = m.get("type", "Photo")
                if "Video" in m.get("class", "") and "type" not in m:
                    m_type = "Video"
                
                if m_type == cat_type and m.get("safety", "SFW") == safety_str:
                    models_to_show.append(m)
            
        search_term = self.model_search_input.text().lower()
        for m in models_to_show:
            if search_term:
                searchable_text = f"{m.get('name', '')} {m.get('desc', '')} {m.get('safety', '')} {m.get('class', '')}".lower()
                if search_term not in searchable_text:
                    continue
            self.models_layout.addWidget(self.create_model_card(m))
            
        self.models_layout.addStretch()
            
        # Update combo box too
        local_models = []
        if os.path.exists(self.engine.models_dir):
            for d in os.listdir(self.engine.models_dir):
                if d.startswith("models--"):
                    local_models.append(d.replace("models--", "").replace("--", "/"))
                    
        current_selected = self.model_combo.currentText()
        self.model_combo.clear()
        for lm in local_models:
            self.model_combo.addItem(lm)
        if current_selected:
            self.model_combo.setCurrentText(current_selected)
            
        active_model = next((m for m in RECOMMENDED_MODELS if m['id'] == self.model_combo.currentText()), None)
        if active_model:
            is_text = active_model.get('type') == 'Text'
            if hasattr(self, 'live_container'):
                self.live_container.setVisible(not is_text)
            if hasattr(self, 'text_switches_container'):
                self.text_switches_container.setVisible(is_text)
            if hasattr(self, 'attach_btn'):
                self.attach_btn.setVisible(not is_text)
            if hasattr(self, 'image_settings_widget'):
                self.image_settings_widget.setVisible(not is_text)
            if hasattr(self, 'text_settings_widget'):
                self.text_settings_widget.setVisible(is_text)
            
    def add_custom_model(self):
        mid = self.custom_id_input.text().strip()
        if mid:
            self.select_model(mid)
            
    def handle_pasted_image(self, image):
        path = os.path.join(OUTPUTS_DIR, f"pasted_{uuid.uuid4().hex}.png")
        image.save(path)
        self._set_attachment(path, False)

    def attach_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            self._set_attachment(path, False)
            
    def open_canvas(self):
        if self.attached_image:
            self.canvas_dialog = CanvasDialog(self.attached_image)
            self.canvas_dialog.mask_saved.connect(self.on_mask_saved)
            self.canvas_dialog.show()
            
    def _set_attachment(self, path, has_mask):
        self.attached_image = path
        pixmap = QPixmap(path).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        self.attachment_preview.setPixmap(pixmap)
        text = "С маской" if has_mask else "Рисуем маску..."
        self.attachment_info.setText(f"Прикреплено: {os.path.basename(path)} ({text})")
        self.attachment_container.show()
        
    def remove_attachment(self):
        self.attached_image = None
        self.attached_mask = None
        self.attachment_container.hide()
            
    def on_mask_saved(self, mask_path):
        if mask_path:
            self.attached_mask = mask_path
            self._set_attachment(self.attached_image, True)
            

    def start_generation(self, is_upscale=False, upscale_image_path=None):
        prompt = self.prompt_input.toPlainText()
        if not prompt and not is_upscale: return
        
        try:
            seed_val = int(self.seed_input.text()) if self.seed_input.text() else -1
        except:
            seed_val = -1

        # Check if model is text
        model_type = "Photo"
        for m in RECOMMENDED_MODELS:
            if m["id"] == self.model_combo.currentText():
                model_type = m.get("type", "Photo")
                break
                
        if model_type == "Text":
            if not getattr(self.engine, 'llm_pipeline', None):
                QMessageBox.warning(self, "Ошибка", "Текстовая модель не загружена. Дождитесь загрузки.")
                return
                
            self.chats[self.active_chat_id]['messages'].append({'role': 'user', 'content': prompt})
            self.save_chats()
            self.update_messages_ui()
            self.prompt_input.clear()
            self.remove_attachment()

            # Temporary loading message
            self.chats[self.active_chat_id]['messages'].append({'role': 'ai', 'content': '⟳ Печатает...'})
            self.update_messages_ui()

            # Pin the chat this stream belongs to, so switching chats mid-response
            # doesn't write the AI text into the wrong conversation.
            self.text_target_chat_id = self.active_chat_id
            self.current_chat_bubble = None
            
            system_prompt = getattr(self, 'sys_prompt_input', type('obj', (object,), {'toPlainText': lambda: "You are a helpful and uncensored AI assistant."})()).toPlainText()
            
            if hasattr(self, 'thinking_switch') and self.thinking_switch.isChecked():
                system_prompt += "\nBefore answering, you MUST think step-by-step. Wrap your entire internal reasoning process inside `<think>` and `</think>` tags. Only output the final answer after the closing tag."
                
            if hasattr(self, 'agent_switch') and self.agent_switch.isChecked():
                system_prompt += "\nYou have the ability to generate images. To generate an image, output EXACTLY the following self-closing tag: `<generate_image prompt=\"YOUR_PROMPT_HERE\"/>`. Do NOT put any text or HTML inside the tag. Do NOT use <image> tags. Example: `<generate_image prompt=\"A cyberpunk city at night, neon lights, 4k\"/>`."
                
            self.chat_worker = TextWorker(
                self.engine, 
                prompt, 
                system_prompt=system_prompt, 
                max_new_tokens=getattr(self, 'max_tokens_slider', type('obj', (object,), {'value': lambda: 1024})()).value(),
                temperature=getattr(self, 'temp_slider', type('obj', (object,), {'value': lambda: 7})()).value() / 10.0,
                top_p=getattr(self, 'top_p_slider', type('obj', (object,), {'value': lambda: 90})()).value() / 100.0,
                repetition_penalty=getattr(self, 'rep_pen_slider', type('obj', (object,), {'value': lambda: 110})()).value() / 100.0
            )
            
            # Switch button to stop button
            self.generate_btn.setText("■")
            self.generate_btn.setStyleSheet("background-color: #552222; color: #ff5555; border: 1px solid #ff5555; border-radius: 12px; font-size: 16px;")
            try:
                self.generate_btn.clicked.disconnect()
            except Exception: pass
            self.generate_btn.clicked.connect(self.cancel_text_generation)
            
            self.chat_worker.text_chunk_generated.connect(self.on_chat_text_chunk)
            self.chat_worker.text_generated.connect(self.on_chat_text_generated)
            self.chat_worker.finished.connect(self.on_text_generation_finished)
            self.chat_worker.start()
            return
            
        task = {
            'prompt': prompt,
            'is_upscale': is_upscale,
            'upscale_image_path': upscale_image_path,
            'model_id': self.model_combo.currentText(),
            'res_text': self.res_combo.currentText(),
            'quant_text': self.quant_combo.currentText(),
            'vram_text': self.vram_combo.currentText(),
            'batch_count': self.batch_slider.value(),
            'batch_size': self.batch_size_slider.value(),
            'steps': self.steps_slider.value(),
            'sampler': self.sampler_combo.currentText(),
            'denoise': self.denoise_slider.value() / 100.0,
            'cfg_scale': self.cfg_slider.value() / 10.0,
            'seed': seed_val,
            'lora_id': getattr(self, 'selected_lora_id', None) or '',
            'lora_weight': getattr(self, 'lora_slider', None).value() / 10.0 if hasattr(self, 'lora_slider') else 1.0,
            'use_adetailer': getattr(self, 'adetailer_check', None).isChecked() if hasattr(self, 'adetailer_check') else False,
            'attached_image': self.attached_image,
            'attached_mask': self.attached_mask,
            'active_chat_id': self.active_chat_id,
            'neg_prompt': getattr(self, 'neg_prompt_input', None).toPlainText() if hasattr(self, 'neg_prompt_input') else "",
            'use_cnet': getattr(self, 'cnet_check', None).isChecked() if hasattr(self, 'cnet_check') else False,
            'cnet_id': getattr(self, 'selected_controlnet_id', None) or '',
            'cnet_image': getattr(self, 'cnet_image_path', None)
        }
        
        if not is_upscale and self.attached_image:
            self.chats[self.active_chat_id]['messages'].append({'role': 'user', 'content': self.attached_image})
            
        if is_upscale:
            self.chats[self.active_chat_id]['messages'].append({'role': 'user', 'content': '⟡ Улучшение качества (Upscale 2x)'})
        else:
            self.chats[self.active_chat_id]['messages'].append({'role': 'user', 'content': prompt})
            
        self.save_chats()
        self.update_messages_ui()
        self.prompt_input.clear()
        self.remove_attachment()
        
        self.generation_queue.append(task)
        self.update_queue_ui()
        
        if not getattr(self, 'is_generating', False):
            self.process_next_in_queue()
            
    

    def cancel_text_generation(self):
        if hasattr(self, 'chat_worker') and self.chat_worker and self.chat_worker.isRunning():
            self.chat_worker.is_cancelled = True
            
    def on_text_generation_finished(self):
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("↑")
        self.generate_btn.setStyleSheet("""
            QPushButton { background-color: white; color: black; font-size: 24px; font-weight: bold; border-radius: 18px; border: none; padding: 0px; margin: 0px; }
            QPushButton:disabled { background-color: #E0E0E0; color: #555555; }
        """)
        try:
            self.generate_btn.clicked.disconnect()
        except Exception: pass
        self.generate_btn.clicked.connect(self.start_generation)

    def scroll_to_bottom(self):
        if hasattr(self, 'messages_area'):
            self.messages_area.verticalScrollBar().setValue(self.messages_area.verticalScrollBar().maximum())

    def on_chat_text_chunk(self, chunk):
        if not chunk: return
        
        if not hasattr(self, 'typing_queue'):
            self.typing_queue = ""
            self.typing_timer = QTimer(self)
            self.typing_timer.timeout.connect(self.process_typing_queue)
            
        self.typing_queue += chunk
        
        if not self.typing_timer.isActive():
            self.typing_timer.start(15)

    def _text_target_id(self):
        return getattr(self, 'text_target_chat_id', None) or self.active_chat_id

    def _bubble_alive(self, bubble):
        if bubble is None:
            return False
        from PyQt6 import sip
        try:
            return not sip.isdeleted(bubble)
        except Exception:
            return False

    def process_typing_queue(self):
        generation_active = hasattr(self, 'chat_worker') and getattr(self.chat_worker, 'isRunning', lambda: False)()
        
        if not hasattr(self, 'typing_queue') or not self.typing_queue:
            if not generation_active:
                if hasattr(self, 'typing_timer'): self.typing_timer.stop()
                if hasattr(self, 'current_chat_bubble') and self.current_chat_bubble:
                    # Clear any leftover cursor
                    target_id = self._text_target_id()
                    chat = self.chats.get(target_id)
                    if chat and chat['messages']:
                        self.current_chat_bubble.set_content(chat['messages'][-1]['content'])
                return

        if self.typing_queue:
            chars_to_take = max(1, len(self.typing_queue) // 10)
            chunk = self.typing_queue[:chars_to_take]
            self.typing_queue = self.typing_queue[chars_to_take:]
        else:
            chunk = ""

        target_id = self._text_target_id()
        chat = self.chats.get(target_id)
        if not chat or not chat['messages']:
            if hasattr(self, 'typing_timer'): self.typing_timer.stop()
            return
            
        msg_list = chat['messages']
        if chunk:
            if msg_list[-1]['content'] == '⟳ Печатает...':
                msg_list[-1]['content'] = chunk
            else:
                msg_list[-1]['content'] += chunk

        if not hasattr(self, 'current_chat_bubble') or not self._bubble_alive(getattr(self, 'current_chat_bubble', None)):
            self.current_chat_bubble = None
            if self.active_chat_id == target_id:
                for i in range(self.messages_layout.count() - 1, -1, -1):
                    item = self.messages_layout.itemAt(i)
                    if item and item.widget() and type(item.widget()).__name__ == 'ChatBubble':
                        self.current_chat_bubble = item.widget()
                        break

        bubble = getattr(self, 'current_chat_bubble', None)
        if self._bubble_alive(bubble) and hasattr(bubble, 'set_content'):
            import time
            cursor = " ▌" if int(time.time() * 2) % 2 == 0 and generation_active else ""
            bubble.set_content(msg_list[-1]['content'] + cursor)
            
        if chunk:
            self.scroll_to_bottom()

        if self.active_chat_id == target_id:
            self.scroll_to_bottom()

    def on_chat_text_generated(self, result_text):
        if hasattr(self, 'typing_timer'):
            self.typing_timer.stop()
        self.typing_queue = ""

        target_id = self._text_target_id()
        chat = self.chats.get(target_id)
        if not chat:
            self.text_target_chat_id = None
            self.current_chat_bubble = None
            return
        msg_list = chat['messages']
        msg_list[-1]['content'] = result_text

        bubble = getattr(self, 'current_chat_bubble', None)
        if self._bubble_alive(bubble) and hasattr(bubble, 'set_content'):
            bubble.set_content(result_text)

        self.current_chat_bubble = None
        self.text_target_chat_id = None
        import re
        gen_matches = list(re.finditer(r'<generate_image\s+prompt=["\'](.*?)["\']\s*/>', result_text, re.IGNORECASE))
        if gen_matches:
            result_text = re.sub(r'<generate_image\s+prompt=["\'](.*?)["\']\s*/>', '', result_text, flags=re.IGNORECASE).strip()

        if msg_list[-1]['role'] == 'ai':
            msg_list[-1]['content'] = result_text
        else:
            msg_list.append({'role': 'ai', 'content': result_text})
        self.save_chats()
        if self.active_chat_id == target_id:
            self.update_messages_ui()

        if gen_matches:
            image_model = self.engine.current_model_id
            if not image_model or 'Text' in str(next((m for m in RECOMMENDED_MODELS if m['id'] == image_model), {}).get('type', '')):
                image_model = "black-forest-labs/FLUX.1-schnell"

            for match in gen_matches:
                prompt = match.group(1)
                task = {
                    'prompt': prompt,
                    'is_upscale': False,
                    'upscale_image_path': None,
                    'model_id': image_model,
                    'res_text': "1024x1024",
                    'quant_text': "fp16",
                    'vram_text': "low",
                    'batch_count': 1,
                    'batch_size': 1,
                    'steps': 4 if "flux" in image_model.lower() or "schnell" in image_model.lower() else 25,
                    'sampler': "Euler",
                    'denoise': 0.75,
                    'cfg_scale': 1.0 if "flux" in image_model.lower() else 7.0,
                    'seed': -1,
                    'lora_id': '',
                    'lora_weight': 1.0,
                    'use_adetailer': False,
                    'attached_image': None,
                    'attached_mask': None,
                    'active_chat_id': target_id,
                    'neg_prompt': "",
                    'use_cnet': False,
                    'cnet_id': '',
                    'cnet_image': None
                }
                self.generation_queue.append(task)

            self.update_queue_ui()
            if not getattr(self, 'is_generating', False):
                self.process_next_in_queue()

    def start_canvas_generation(self, prompt, image, mask, x, y):
        try:
            seed_val = int(self.seed_input.text()) if self.seed_input.text() else -1
        except:
            seed_val = -1
            
        import tempfile, os
        img_path, mask_path = None, None
        
        if not image.isNull():
            tmp_dir = tempfile.gettempdir()
            img_path = os.path.join(tmp_dir, f"canvas_img_{uuid.uuid4().hex}.png")
            mask_path = os.path.join(tmp_dir, f"canvas_mask_{uuid.uuid4().hex}.png")
            image.save(img_path)
            mask.save(mask_path)
            
        task = {
            'is_canvas': True,
            'canvas_x': x,
            'canvas_y': y,
            'prompt': prompt,
            'is_upscale': False,
            'upscale_image_path': None,
            'model_id': self.model_combo.currentText(),
            'res_text': self.res_combo.currentText(),
            'quant_text': self.quant_combo.currentText(),
            'vram_text': self.vram_combo.currentText(),
            'batch_count': self.batch_slider.value(),
            'batch_size': self.batch_size_slider.value(),
            'steps': self.steps_slider.value(),
            'sampler': self.sampler_combo.currentText(),
            'denoise': self.denoise_slider.value() / 100.0,
            'cfg_scale': self.cfg_slider.value() / 10.0,
            'seed': seed_val,
            'lora_id': getattr(self, 'selected_lora_id', None) or '',
            'lora_weight': getattr(self, 'lora_slider', None).value() / 10.0 if hasattr(self, 'lora_slider') else 1.0,
            'use_adetailer': getattr(self, 'adetailer_check', None).isChecked() if hasattr(self, 'adetailer_check') else False,
            'attached_image': img_path,
            'attached_mask': mask_path,
            'active_chat_id': self.active_chat_id,
            'neg_prompt': getattr(self, 'neg_prompt_input', None).toPlainText() if hasattr(self, 'neg_prompt_input') else "",
            'use_cnet': getattr(self, 'cnet_check', None).isChecked() if hasattr(self, 'cnet_check') else False,
            'cnet_id': getattr(self, 'cnet_input', None).currentText().strip() if hasattr(self, 'cnet_input') and hasattr(getattr(self, 'cnet_input'), 'currentText') else "",
            'cnet_image': getattr(self, 'cnet_image_path', None)
        }
        
        self.generation_queue.append(task)
        self.update_queue_ui()
        if not getattr(self, 'is_generating', False):
            self.process_next_in_queue()

    def update_queue_ui(self):
        if hasattr(self, 'generation_queue') and len(self.generation_queue) > 0:
            self.generate_btn.setToolTip(f'В очереди: {len(self.generation_queue)}')
            self.generate_btn.setStyleSheet("background-color: #2A2A2A; border-radius: 12px; border: 1px solid rgba(255,255,255,0.15);")
        else:
            self.generate_btn.setToolTip('Сгенерировать')
            self.generate_btn.setStyleSheet(getattr(self, "_gen_btn_style", "background-color: #1E1E1E; border-radius: 12px;"))
            
    def process_next_in_queue(self):
        if not hasattr(self, 'generation_queue') or len(self.generation_queue) == 0:
            self.is_generating = False
            # self.generate_btn.setEnabled(True)
            self.update_queue_ui()
            return
        from PyQt6.QtCore import Qt, QTimer
        self.is_generating = True
        # self.generate_btn.setEnabled(True)
        self.update_queue_ui()
        task = self.generation_queue.pop(0)
        self.current_task = task
        
        self.gen_container = QFrame()
        self.gen_container.setObjectName("glassPanel")

        gen_layout = QVBoxLayout(self.gen_container)
        gen_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        header_row = QHBoxLayout()
        self.spinner = SpinnerWidget()
        title_lbl = QLabel("Генерация изображения...")
        title_lbl.setStyleSheet("font-weight: bold; font-size: 15px; font-family: 'Lora', serif; color: white;")
        self.cancel_btn = QPushButton("✕ Отмена")
        self.cancel_btn.setStyleSheet("background-color: #C62828; color: white; border: none; border-radius: 15px; font-weight: bold;")
        self.cancel_btn.setFixedSize(120, 30)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        
        header_row.addWidget(self.spinner)
        header_row.addWidget(title_lbl)
        header_row.addStretch()
        header_row.addWidget(self.cancel_btn)
        gen_layout.addLayout(header_row)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(500)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background-color: #222222; border-radius: 4px; } QProgressBar::chunk { background-color: #FFFFFF; border-radius: 4px; }")
        gen_layout.addWidget(self.progress_bar)
        
        self.status_lbl = QLabel("Ожидание запуска шагов генерации...")
        self.status_lbl.setStyleSheet("color: #888888; font-size: 12px; margin-top: 5px;")
        gen_layout.addWidget(self.status_lbl)
        
        self.time_lbl = QLabel("Прошло времени: 0 сек")
        self.time_lbl.setStyleSheet("color: #888888; font-size: 12px;")
        gen_layout.addWidget(self.time_lbl)
        
        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_lbl.setContentsMargins(0, 15, 0, 0)
        from PyQt6.QtWidgets import QGraphicsBlurEffect
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(20)
        self.preview_lbl.setGraphicsEffect(self.blur_effect)
        gen_layout.addWidget(self.preview_lbl)
        
        if not task.get('is_canvas'):
            self.messages_layout.addWidget(self.gen_container)
        QTimer.singleShot(100, lambda: self.messages_area.verticalScrollBar().setValue(self.messages_area.verticalScrollBar().maximum()))
        
        import time, os, uuid
        self.gen_start_time = time.time()
        self.gen_timer = QTimer()
        self.gen_timer.timeout.connect(self.update_gen_time)
        self.gen_timer.start(1000)
        
        is_upscale = task['is_upscale']
        if is_upscale:
            from PIL import Image
            orig = Image.open(task['upscale_image_path'])
            new_w, new_h = orig.width * 2, orig.height * 2
            upscaled = orig.resize((new_w, new_h), Image.Resampling.LANCZOS)
            tmp_path = os.path.join(OUTPUTS_DIR, f"upscale_tmp_{uuid.uuid4().hex}.png")
            upscaled.save(tmp_path)
            attached = tmp_path
            denoise_val = 0.25
            final_prompt = "masterpiece, best quality, ultra detailed, 8k resolution"
            final_negative = "lowres, bad quality, blurry, pixelated"
        else:
            final_prompt = task['prompt']
            final_negative = task['neg_prompt']
            attached = task['attached_image']
            if not attached:
                for msg in reversed(self.chats[task['active_chat_id']]["messages"]):
                    if msg["role"] == "ai" and msg["content"].endswith(".png") and os.path.exists(msg["content"]):
                        attached = msg["content"]
                        break
            denoise_val = task['denoise']
            
        try:
            w_str, h_str = task['res_text'].split("x")
            width, height = int(w_str), int(h_str)
            width = (width // 8) * 8
            height = (height // 8) * 8
        except:
            width, height = 512, 512
            
        q_text = task['quant_text']
        precision = "fp16"
        if "4-bit" in q_text: precision = "4-bit"
        elif "8-bit" in q_text: precision = "8-bit"
        elif "32-bit" in q_text: precision = "fp32"
        
        vram_text = task['vram_text']
        vram_mode = "high"
        if "Low" in vram_text: vram_mode = "low"
        elif "Med" in vram_text: vram_mode = "med"
        
        if hasattr(self, "worker") and self.worker is not None:
            self._old_workers.append(self.worker)
            self.worker.deleteLater()
            
        self._old_workers = [w for w in self._old_workers if w.isRunning()]

        self.worker = GenerationWorker(
            self.engine, task['model_id'], precision, vram_mode, final_prompt, task['batch_count'], task['steps'],
            width, height, task['sampler'], final_negative, task['seed'], denoise_val, task['cfg_scale'], attached, task['attached_mask'],
            use_adetailer=task['use_adetailer'], lora_id=task['lora_id'], lora_weight=task['lora_weight'],
            controlnet_id=task.get('cnet_id') if task.get('use_cnet') else None,
            control_image=task.get('cnet_image') if task.get('use_cnet') else None,
            batch_size=task.get('batch_size', 1),
            output_dir=self.settings.value("output_folder", OUTPUTS_DIR)
        )
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.image_preview.connect(self.update_preview)
        self.worker.generation_finished.connect(self.generation_done)
        self.worker.generation_error.connect(self.generation_error)
        self.worker.prompt_translated.connect(self.update_translated_prompt)
        
        self.worker.start()
        
        self.remove_attachment()
        
    def update_translated_prompt(self, translated_text):
        chat = self.chats[self.active_chat_id]
        if len(chat["messages"]) > 0 and chat["messages"][-1]["role"] == "user":
            chat["messages"][-1]["content"] += f"\n\n[Перевод: {translated_text}]"
            self.save_chats()
            
            # Обновляем текст в UI без перезагрузки всего чата
            for i in range(self.messages_layout.count() - 1, -1, -1):
                item = self.messages_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), ChatBubble):
                    bubble = item.widget()
                    # Ищем QLabel внутри bubble
                    for child in bubble.findChildren(QLabel):
                        if child.text().startswith(chat["messages"][-1]["content"].split("\n\n[Перевод:")[0]):
                            child.setText(chat["messages"][-1]["content"])
                            break
                    break

    def cancel_generation(self):
        if hasattr(self, "worker") and self.worker.isRunning():
            self.worker.is_cancelled = True
        self.cleanup_generation()
        
    def _gen_alive(self):
        # True only if the generation container still exists and hasn't been
        # destroyed (e.g. by a chat switch that wiped messages_layout).
        from PyQt6 import sip
        c = getattr(self, "gen_container", None)
        if c is None:
            return False
        try:
            if sip.isdeleted(c):
                self.gen_container = None
                if hasattr(self, "gen_timer"):
                    self.gen_timer.stop()
                return False
        except Exception:
            return False
        return True

    def update_gen_time(self):
        if not self._gen_alive(): return
        elapsed = int(time.time() - self.gen_start_time)
        self.time_lbl.setText(f"Прошло времени: {elapsed} сек")

    def update_progress(self, step, total, msg, ratio):
        if hasattr(self, "web_server"):
            try:
                self.web_server.update_progress(step, total, msg, ratio)
            except Exception:
                pass
        if not self._gen_alive(): return
        self.progress_bar.setValue(int(ratio * 100))
        self.status_lbl.setText(msg.replace("[1/1] ", ""))
        new_blur = max(0, 20 - int(20 * ratio))
        self.blur_effect.setBlurRadius(new_blur)

    def update_preview(self, qim):
        if not self._gen_alive(): return
        pixmap = QPixmap.fromImage(qim).scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        from PyQt6.QtGui import QPainterPath
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 12, 12)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)
        painter.end()
        
        self.preview_lbl.setPixmap(rounded)
        
    def cleanup_generation(self):
        if hasattr(self, "gen_timer"):
            try: self.gen_timer.stop()
            except Exception: pass
        # self.generate_btn.setEnabled(True)
        if hasattr(self, "gen_container") and self.gen_container is not None:
            from PyQt6 import sip
            try:
                if not sip.isdeleted(self.gen_container):
                    self.gen_container.deleteLater()
            except Exception:
                pass
            self.gen_container = None
    def generation_done(self, paths):
        if hasattr(self, "web_server"):
            self.web_server.finish_generation(True, paths[0] if paths else "")
            
        self.cleanup_generation()
        
        target_chat_id = self.current_task.get('active_chat_id', self.active_chat_id) if hasattr(self, 'current_task') else self.active_chat_id
        
        for p in paths:
            if target_chat_id in self.chats:
                self.chats[target_chat_id]["messages"].append({"role": "ai", "content": p})
            
        self.save_chats()
        self.process_next_in_queue()
        self.update_messages_ui()
        
        self.attached_image = None
        self.attached_mask = None
        self.attachment_container.hide()
        
    def generation_error(self, err_msg):
        if hasattr(self, "web_server"):
            self.web_server.finish_generation(False, err_msg)
            
        self.cleanup_generation()
        
        target_chat_id = self.current_task.get('active_chat_id', self.active_chat_id) if hasattr(self, 'current_task') else self.active_chat_id
        if target_chat_id in self.chats:
            self.chats[target_chat_id]["messages"].append({"role": "ai", "content": f"Ошибка генерации:\n{err_msg}"})
        self.save_chats()
        self.update_messages_ui()
        self.process_next_in_queue()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
