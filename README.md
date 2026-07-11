# OmniStudio

A high-performance, cross-platform desktop application designed for local image and video synthesis using state-of-the-art diffusion models. Powered by a PyQt6 frontend and a PyTorch/Diffusers backend, OmniStudio provides a completely offline, private environment for neural generation.

---

## Technical Architecture and Features

OmniStudio is engineered to bridge the gap between high-performance neural computing and native desktop application architecture.

- **Offline Processing Pipeline**: 100% local computation. No telemetry, external API reliance, or remote data sharing.
- **Asynchronous Execution Queue**: The PyQt6 GUI and neural engine run on decoupled threads. Long-running model loads and generation steps are handled by background workers (`QThread`), preventing UI freeze states.
- **Dynamic Model Allocation**: Supports direct integration with the Hugging Face Hub. Includes an integrated downloader (`fetch_hf_models.py`) capable of caching and running FLUX.1, Stable Diffusion (1.5, XL), and various video architectures.
- **Memory Optimization and Attention Patching**: Dynamically manages CPU/GPU memory. Integrates custom overrides to handle PyInstaller compatibility bugs with newer PyTorch versions (such as `flex_attention` version checks).
- **Extensible Addon Pipeline**: Native support for hot-loading LoRA weights and integrating ControlNet guidance (e.g., Canny edge, depth mapping).
- **Interactive Masking Canvas**: Built-in graphics scene (`QGraphicsScene`) for inpainting and image-to-image workflows, allowing users to draw pixel-perfect mask overlays.
- **Real-Time Latent Previews**: Decodes latents during the generation process using a customized VAE decoder pipeline, sending previews to the UI without blocking inference.
- **Automated Text Processing**: 
  - Integrated translation module using MarianMT (`Helsinki-NLP/opus-mt-ru-en`) to automatically translate prompts to English.
  - Prompt expansion using Gustavosta/MagicPrompt-Stable-Diffusion to generate highly detailed prompts from short descriptions.
- **ADetailer Module**: Built-in face detection and enhancement utilizing OpenCV Haar Cascades and localized inpainting to restore facial features.
- **Hardware Telemetry**: Real-time monitoring of host CPU utilization and system memory (VRAM/RAM) footprint.

---

## Technical Specifications & Implementations

### VRAM and Memory Management
OmniStudio dynamically configures PyTorch and Diffusers pipelines to run on consumer-grade GPUs:
- **Low VRAM Mode**: Integrates model CPU offloading (`enable_model_cpu_offload`), VAE slicing (`enable_vae_slicing`), and attention slicing (`enable_attention_slicing`).
- **Medium VRAM Mode**: Uses model CPU offloading and attention slicing to fit larger models like FLUX.1 or SDXL on mid-range GPUs (e.g., 8 GB VRAM).
- **Quantization Support**: Utilizes BitsAndBytes to load weights in 4-bit and 8-bit precision on CUDA devices.
- **Memory Allocation**: Forces bfloat16 and balanced device mapping for large networks (e.g., Z-Image pipelines) to prevent Out-Of-Memory (OOM) errors.

### Supported Generation Workflows
- **Text-to-Image / Image-to-Image**: Standard diffusion pipelines with dynamic scheduler swaps (Euler, Euler a, DPM++ 2M Karras, DPM++ 2S a, DPM2, DDIM, Heun).
- **Inpainting**: Custom `DrawingScene` captures white mask overlays on a black background, passing them alongside the initialized image to the inpainting pipeline.
- **Video Generation**: Generates high-fidelity MP4 files using Stable Video Diffusion and I2VGen-XL pipelines. Decodes chunks iteratively (`decode_chunk_size=8`) and exports them using custom frame-rate mapping.
- **Image Upscaling**: Native super-resolution upscaling up to 4x using pre-trained EDSR models (`edsr-base`).
- **Text Generation**: Text pipeline support for running local LLMs (e.g., Llama, Gemma, Phi) with customizable system prompts, temperature controls, and token limits.

---

## System Requirements

- **Operating System**: Windows 10/11 (64-bit) or macOS (12.0+).
- **Hardware Acceleration**: 
  - Recommended: NVIDIA GPU with CUDA support and at least 8 GB of VRAM (necessary for stable FLUX.1 or SDXL inference).
  - Minimum: 4 GB VRAM for Stable Diffusion 1.5 or lighter text models.
- **System Memory**: 16 GB RAM minimum.
- **Storage**: ~2.5 GB for the base installation + variable space for downloaded model weights (e.g., 6 GB for SDXL checkpoints).

---

## Installation and Deployment

### Windows (Pre-compiled Binary)
The simplest way to deploy the application on Windows without requiring a Python environment:
1. Navigate to [Releases](../../releases) and download the installer (`OmniStudio_Setup.exe`).
2. Run the installer to configure shortcuts and paths automatically.
3. Launch the application, set your Hugging Face Access Token in Settings, and download a model to begin.

*A portable standalone archive is also available via `OmniStudio_Portable.zip`.*

### macOS / Linux (From Source)
To run the project in a development or Unix environment:
1. Download the source package `OmniStudio_Source_Mac.zip` or clone the repository.
2. Initialize a virtual environment and install the required dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run the primary entry point:
   ```bash
   python main_mac.py
   ```

---

## Technical Stack

- **Frontend / UI**: PyQt6, styled with customized QSS (Qt Style Sheets) and custom widgets (ToggleSwitch, ClickableLabel, AnimatedTabBar).
- **AI / Compute Engine**: PyTorch, Hugging Face Diffusers, Hugging Face Transformers, Accelerate, SuperImage.
- **Packaging Tools**: PyInstaller, Inno Setup Compiler.

---
---

# OmniStudio (На русском)

Высокопроизводительное кроссплатформенное десктопное приложение для локального синтеза изображений и видео с использованием современных диффузионных моделей. Благодаря фронтенду на PyQt6 и бэкенду на PyTorch/Diffusers, OmniStudio предоставляет полностью автономную и конфиденциальную среду для нейросетевой генерации.

---

## Архитектура и функциональные возможности

OmniStudio разработан с целью объединить высокую производительность нейросетевых вычислений и отзывчивость нативного десктопного интерфейса.

- **Локальный пайплайн вычислений**: 100% локальное выполнение задач. Никакой телеметрии, зависимости от облачных API или передачи пользовательских данных во внешние сети.
- **Асинхронная очередь выполнения**: Потоки GUI PyQt6 и нейросетевого движка полностью изолированы. Загрузка тяжелых весов моделей и шаги деноизинга обрабатываются фоновыми воркерами (`QThread`), что исключает блокировку интерфейса.
- **Динамический менеджмент моделей**: Прямая интеграция с Hugging Face Hub. Встроенный загрузчик (`fetch_hf_models.py`) обеспечивает автоматическое кэширование и запуск моделей FLUX.1, Stable Diffusion (1.5, XL) и специализированных видеоархитектур.
- **Оптимизация памяти**: Автоматический контроль распределения ресурсов памяти CPU/GPU. Интегрированы патчи для обхода несовместимостей PyInstaller с последними релизами PyTorch (в частности, исправление проверок версий для модуля `flex_attention`).
- **Интеграция LoRA и ControlNet**: Поддержка "горячего" подключения весов LoRA и обработки направляющих изображений через ControlNet (Canny, Depth и др.).
- **Интерактивный графический Canvas**: Специализированный модуль холста на базе `QGraphicsScene` для задач Inpainting (дорисовки) и Image-to-Image с возможностью попиксельного создания масок.
- **Отрисовка промежуточных шагов**: Декодирование латентов в реальном времени с помощью кастомного пайплайна VAE для отправки превью-изображений на графический интерфейс без прерывания процесса инференса.
- **Автоматическая обработка текста**:
  - Модуль автоматического перевода русскоязычных промптов на английский язык с помощью локальной модели MarianMT (`Helsinki-NLP/opus-mt-ru-en`).
  - Улучшение и расширение коротких промптов с помощью модели Gustavosta/MagicPrompt-Stable-Diffusion.
- **Модуль ADetailer**: Встроенное детектирование лиц с использованием каскадов Хаара OpenCV и последующим локальным инпейнтингом для детализации и улучшения мимики.
- **Телеметрия железа**: Мониторинг утилизации ресурсов центрального процессора и оперативной/видеопамяти в реальном времени.

---

## Техническая реализация и оптимизация

### Управление VRAM и памятью
Приложение динамически адаптирует параметры работы PyTorch и Diffusers для видеокарт различной мощности:
- **Low VRAM**: Принудительно подключает выгрузку модулей на CPU (`enable_model_cpu_offload`), слайсинг VAE (`enable_vae_slicing`) и покадровый слайсинг внимания (`enable_attention_slicing`).
- **Medium VRAM**: Активирует выгрузку модулей на CPU и слайсинг внимания для работы с тяжелыми моделями уровня FLUX.1 и SDXL на графических картах среднего сегмента (от 8 ГБ VRAM).
- **Квантование весов**: Поддерживает загрузку моделей в режиме 4-bit и 8-bit на CUDA-устройствах с использованием библиотеки BitsAndBytes.
- **Аллокация ресурсов**: Форсирует точность вычислений bfloat16 и сбалансированное распределение тензоров по устройствам для предотвращения ошибок нехватки памяти (OOM) на сложных архитектурах.

### Поддерживаемые рабочие процессы
- **Text-to-Image / Image-to-Image**: Стандартные пайплайны генерации с возможностью динамической смены планировщиков (Euler, Euler a, DPM++ 2M Karras, DPM++ 2S a, DPM2, DDIM, Heun).
- **Inpainting (Дорисовка)**: Кастомный класс `DrawingScene` переносит координаты маски на бинарную карту (черно-белую маску), которая передается инпейнт-пайплайну вместе с исходным кадром.
- **Генерация видео**: Создание MP4-видеороликов с использованием Stable Video Diffusion и I2VGen-XL. Декодирование кадров происходит блоками (`decode_chunk_size=8`) с оптимизацией частоты кадров.
- **Апскейлинг изображений**: Встроенное масштабирование до 4x с использованием предобученных EDSR-моделей (`edsr-base`).
- **Генерация текста**: Поддержка запуска локальных LLM-моделей (Llama, Gemma, Phi) с обработкой системных промптов, температурных коэффициентов и лимитов вывода.

---

## Системные требования

- **Операционная система**: Windows 10/11 (64-bit) или macOS (12.0+).
- **Графический ускоритель (GPU)**: 
  - Рекомендуется: NVIDIA с поддержкой CUDA и объемом VRAM от 8 ГБ (необходимо для инференса FLUX.1 и SDXL).
  - Минимально: 4 ГБ VRAM для работы со Stable Diffusion 1.5 или компактными LLM.
- **Оперативная память**: Не менее 16 ГБ RAM.
- **Дисковое пространство**: ~2.5 ГБ под файлы приложения + место для хранения весов моделей (например, ~6 ГБ на одну модель SDXL).

---

## Инструкция по установке

### Windows (Сборка)
1. Перейдите в раздел [Releases](../../releases) и скачайте `OmniStudio_Setup.exe`.
2. Запустите установщик для автоматического развертывания ярлыков и необходимых компонентов.
3. Откройте приложение, укажите Hugging Face Access Token в настройках и выберите модель для загрузки.

*Дополнительно доступна портативная версия без установки: `OmniStudio_Portable.zip`.*

### macOS / Linux (Запуск из исходного кода)
1. Скачайте архив с исходным кодом `OmniStudio_Source_Mac.zip` или клонируйте репозиторий.
2. Создайте виртуальное окружение и установите зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Запустите основную точку входа:
   ```bash
   python main_mac.py
   ```

---

## Используемый стек

- **Интерфейс**: PyQt6, стилизованный через кастомные QSS-таблицы, а также специализированные компоненты (ToggleSwitch, ClickableLabel, AnimatedTabBar).
- **Вычисления**: PyTorch, Hugging Face Diffusers, Hugging Face Transformers, Accelerate, SuperImage.
- **Инструменты сборки**: PyInstaller, компилятор Inno Setup.
