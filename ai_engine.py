import torch
try:
    import transformers.utils.import_utils
    transformers.utils.import_utils.get_torch_version = lambda: torch.__version__
    transformers.utils.import_utils.is_torch_greater_or_equal = lambda v, accept_dev=False: False if v == "2.9.0" else True
except:
    pass
from dotenv import load_dotenv
load_dotenv()
import os
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
import torch
if hasattr(torch, 'set_num_threads'):
    torch.set_num_threads(max(1, os.cpu_count() - 2))
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline, FluxPipeline, EulerAncestralDiscreteScheduler, EulerDiscreteScheduler, DPMSolverMultistepScheduler, DPMSolverSinglestepScheduler, KDPM2DiscreteScheduler, DDIMScheduler, HeunDiscreteScheduler, StableVideoDiffusionPipeline, I2VGenXLPipeline
from diffusers.utils import export_to_video
from PIL import Image

class AIEngine:

    def __init__(self):
        self.pipe = None
        self.current_model_id = None
        self.device = 'cpu'
        self.sampler_name = 'DPM++ 2M Karras'
        self.translator = None
        self.models_dir = os.path.join(os.path.expanduser('~'), 'OmniStudioData', 'models')
        self.current_lora_id = None
        os.makedirs(self.models_dir, exist_ok=True)

    def _clear_vram(self):
        import gc
        if hasattr(self, 'pipe') and self.pipe:
            del self.pipe
            self.pipe = None
        self.current_model_id = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def set_device(self, use_gpu: bool = None):
        if use_gpu is not None:
            if use_gpu:
                if torch.cuda.is_available():
                    self.device = 'cuda'
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.device = 'mps'
                else:
                    self.device = 'cpu'
            else:
                self.device = 'cpu'
        # Don't move pipe here - it's already placed correctly by load_model
        # Moving it again breaks CPU offloading and causes slowdowns

    def load_model(self, model_id: str, precision: str='fp16', vram_mode: str='high', controlnet_id: str=None):
        if self.current_model_id == model_id and getattr(self, 'current_controlnet_id', None) == controlnet_id and self.pipe is not None:
            return True
        try:
            print(f'[DEBUG] load_model called. self.device = {self.device}')
            print(f'[DEBUG] torch.cuda.is_available() = {torch.cuda.is_available()}')
            if torch.cuda.is_available():
                print(f'[DEBUG] GPU name: {torch.cuda.get_device_name(0)}')
                print(f'[DEBUG] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024 ** 3:.1f} GB')
            if self.pipe is not None:
                del self.pipe
                self.pipe = None
                import gc
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            self.current_controlnet_id = controlnet_id
            if self.device == 'cpu':
                dtype = torch.float32
            else:
                dtype = torch.float16 if precision == 'fp16' else torch.float32
            kwargs = {'torch_dtype': dtype, 'cache_dir': self.models_dir}
            load_id = model_id
            model_path = os.path.join(self.models_dir, f"models--{model_id.replace('/', '--')}")
            if os.path.exists(model_path):
                snapshots_dir = os.path.join(model_path, 'snapshots')
                if os.path.exists(snapshots_dir) and os.listdir(snapshots_dir):
                    snaps = os.listdir(snapshots_dir)
                    load_id = os.path.join(snapshots_dir, snaps[0])
                    kwargs['local_files_only'] = True
            is_flux = 'flux' in model_id.lower()
            is_i2vgen = 'i2vgen' in model_id.lower()
            is_svd = 'stable-video' in model_id.lower()
            is_xl = 'xl' in model_id.lower() and (not is_flux) and (not is_i2vgen)

            is_8bit = precision == '8-bit' and self.device == 'cuda'
            is_4bit = precision == '4-bit' and self.device == 'cuda'
            
            # SD 1.5 doesn't need quantization on 8GB VRAM and fails with device_map
            if not (is_flux or is_xl):
                is_8bit = False
                is_4bit = False

            if is_8bit or is_4bit:
                try:
                    from diffusers import BitsAndBytesConfig
                    if is_4bit:
                        kwargs['quantization_config'] = BitsAndBytesConfig(load_in_4bit=True)
                    else:
                        kwargs['quantization_config'] = BitsAndBytesConfig(load_in_8bit=True)
                except ImportError:
                    if is_8bit:
                        kwargs['load_in_8bit'] = True
                    else:
                        kwargs['load_in_4bit'] = True
                kwargs['device_map'] = 'balanced'; kwargs['offload_folder'] = 'offload'


            def _load(target_id):
                # --- SINGLE FILE CHECK ---
                is_single_file = False
                single_file_path = None
                
                if os.path.exists(target_id) and os.path.isfile(target_id):
                    if target_id.endswith('.safetensors') or target_id.endswith('.ckpt'):
                        is_single_file = True
                        single_file_path = target_id
                elif os.path.exists(target_id) and os.path.isdir(target_id):
                    files = os.listdir(target_id)
                    safetensors_files = [f for f in files if f.endswith('.safetensors')]
                    if safetensors_files and 'model_index.json' not in files and 'config.json' not in files:
                        is_single_file = True
                        single_file_path = os.path.join(target_id, safetensors_files[0])
                else:
                    # Check HF Hub
                    try:
                        from huggingface_hub import list_repo_files, hf_hub_download
                        files = list_repo_files(target_id)
                        safetensors_files = [f for f in files if f.endswith('.safetensors')]
                        if safetensors_files and 'model_index.json' not in files and 'config.json' not in files:
                            is_single_file = True
                            print(f"Detecting single file model on HF Hub. Downloading {safetensors_files[0]}...")
                            single_file_path = hf_hub_download(repo_id=target_id, filename=safetensors_files[0], cache_dir=self.models_dir)
                    except Exception as e:
                        pass
                        
                if is_single_file and single_file_path:
                    print(f"Loading single file model: {single_file_path}")
                    # Remove kwargs that are incompatible with from_single_file
                    kwargs.pop('transformer', None)
                    kwargs.pop('quantization_config', None)
                    kwargs.pop('load_in_8bit', None)
                    kwargs.pop('load_in_4bit', None)
                    kwargs.pop('device_map', None)
                    if is_flux:
                        import diffusers
                        try:
                            from transformers import CLIPTextModel, T5EncoderModel, CLIPTokenizer, T5TokenizerFast
                            print("Loading text encoders from sayakpaul/FLUX.1-merged for Flux single-file...")
                            te1 = CLIPTextModel.from_pretrained("sayakpaul/FLUX.1-merged", subfolder="text_encoder", torch_dtype=torch.bfloat16)
                            te2 = T5EncoderModel.from_pretrained("sayakpaul/FLUX.1-merged", subfolder="text_encoder_2", torch_dtype=torch.bfloat16)
                            tok1 = CLIPTokenizer.from_pretrained("sayakpaul/FLUX.1-merged", subfolder="tokenizer")
                            tok2 = T5TokenizerFast.from_pretrained("sayakpaul/FLUX.1-merged", subfolder="tokenizer_2")
                            kwargs["text_encoder"] = te1
                            kwargs["text_encoder_2"] = te2
                            kwargs["tokenizer"] = tok1
                            kwargs["tokenizer_2"] = tok2
                        except Exception as e:
                            print("Warning: Could not load un-gated text encoders for Flux:", e)
                        
                        return diffusers.FluxPipeline.from_single_file(single_file_path, **kwargs)
                    elif is_xl:
                        import diffusers
                        return diffusers.StableDiffusionXLPipeline.from_single_file(single_file_path, **kwargs)
                    else:
                        import diffusers
                        return diffusers.StableDiffusionPipeline.from_single_file(single_file_path, **kwargs)
                # --- END SINGLE FILE CHECK ---

                if is_i2vgen:
                    return I2VGenXLPipeline.from_pretrained(target_id, **kwargs)
                elif is_svd:
                    return StableVideoDiffusionPipeline.from_pretrained(target_id, **kwargs)
                
                if is_flux and self.device == 'cuda':
                    from diffusers import BitsAndBytesConfig
                    is_flux_2 = 'flux.2' in target_id.lower() or 'flux2' in target_id.lower()
                    if is_flux_2:
                        from diffusers import Flux2Transformer2DModel as TransformerModel
                    else:
                        from diffusers import FluxTransformer2DModel as TransformerModel
                    kwargs['torch_dtype'] = torch.bfloat16
                    if is_8bit:
                        q_conf = kwargs.pop('quantization_config', None)
                    else:
                        q_conf = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4', bnb_4bit_compute_dtype=torch.bfloat16)
                    kwargs.pop('load_in_4bit', None)
                    kwargs.pop('device_map', None)
                    kwargs.pop('quantization_config', None)
                    kwargs.pop('device_map', None)
                    kwargs.pop('quantization_config', None)
                    if q_conf is not None:
                        try:
                            transformer = TransformerModel.from_pretrained(target_id, subfolder='transformer', quantization_config=q_conf, torch_dtype=torch.bfloat16, use_safetensors=True)
                            kwargs['transformer'] = transformer
                        except Exception as e:
                            print(f'Warning: could not quantize transformer separately: {e}')
                            raise e

                if controlnet_id:
                    from diffusers import ControlNetModel
                    cnet_kwargs = {'torch_dtype': kwargs['torch_dtype']}
                    if 'local_files_only' in kwargs: cnet_kwargs['local_files_only'] = kwargs['local_files_only']
                    controlnet = ControlNetModel.from_pretrained(controlnet_id, **cnet_kwargs)
                    kwargs['controlnet'] = controlnet
                    if is_flux:
                        from diffusers import FluxControlNetPipeline
                        return FluxControlNetPipeline.from_pretrained(target_id, use_safetensors=True, **kwargs)
                    elif is_xl:
                        from diffusers import StableDiffusionXLControlNetPipeline
                        return StableDiffusionXLControlNetPipeline.from_pretrained(target_id, **kwargs)
                    else:
                        from diffusers import DiffusionPipeline
                        # For now, fallback to generic pipeline if it's not SD/SDXL explicitly, 
                        # but warning: ControlNet might not be supported natively by custom pipelines without trust_remote_code
                        return DiffusionPipeline.from_pretrained(target_id, trust_remote_code=True, **kwargs)
                else:
                    if is_flux:
                        kwargs.pop('quantization_config', None)
                        kwargs.pop('load_in_4bit', None)
                        kwargs.pop('load_in_8bit', None)
                        if "klein" in target_id.lower():
                            kwargs['device_map'] = 'balanced'
                            kwargs['offload_folder'] = 'offload'
                            from diffusers import DiffusionPipeline
                            return DiffusionPipeline.from_pretrained(target_id, trust_remote_code=True, **kwargs)
                        else:
                            from diffusers import FluxPipeline
                            return FluxPipeline.from_pretrained(target_id, use_safetensors=True, **kwargs)
                    elif is_xl:
                        kwargs.pop('quantization_config', None)
                        kwargs.pop('load_in_4bit', None)
                        kwargs.pop('load_in_8bit', None)
                        return StableDiffusionXLPipeline.from_pretrained(target_id, **kwargs)
                    else:
                        from diffusers import DiffusionPipeline
                        # Remove safety_checker if not standard SD
                        if 'safety_checker' in kwargs:
                            del kwargs['safety_checker']
                        kwargs.pop('quantization_config', None)
                        kwargs.pop('load_in_4bit', None)
                        kwargs.pop('load_in_8bit', None)
                            
                        # Force bfloat16 and balanced for Z-Image to prevent 30GB OOM
                        if 'z-image' in target_id.lower():
                            kwargs['torch_dtype'] = __import__('torch').bfloat16
                            kwargs['device_map'] = 'balanced'; kwargs['offload_folder'] = 'offload'; kwargs['max_memory'] = {0: '7GB', 'cpu': '8GB'}
                            
                        return DiffusionPipeline.from_pretrained(target_id, trust_remote_code=True, **kwargs)
            try:
                self.pipe = _load(load_id)
            except Exception as e:
                err_msg = str(e).lower()
                if '403' in err_msg or '401' in err_msg or 'gated' in err_msg:
                    raise Exception(f'Модель {model_id} является закрытой (Gated). Вам необходимо:\n1. Зарегистрироваться на huggingface.co\n2. Принять лицензионное соглашение на странице модели\n3. В терминале выполнить команду: huggingface-cli login\nИли выбрать другую открытую модель, например, FLUX.1-schnell.')
                if kwargs.get('local_files_only') and ('not found' in err_msg or 'no file named' in err_msg or 'no such file or directory' in err_msg or 'vulnerability' in err_msg or ('torch.load' in err_msg)):
                    print(f'Incomplete or unsafe local cache detected for {model_id}, downloading missing safetensors from Hub...')
                    kwargs['local_files_only'] = False
                    load_id = model_id
                    self.pipe = _load(load_id)
                else:
                    raise e
            if self.device == 'cuda':
                if 'z-image' in model_id.lower() or type(self.pipe).__name__ == 'ZImagePipeline':
                    print("Z-Image loaded via accelerate with device_map='balanced', skipping manual offload and to(cuda)")
                elif 'klein' in model_id.lower():
                    print("Klein model detected, skipping CPU offload to prevent wrapper_CUDA_mm bug")
                    if not is_8bit and not is_4bit:
                        self.pipe = self.pipe.to(self.device)
                elif vram_mode == 'low':
                    try:
                        self.pipe.enable_model_cpu_offload()
                    except AttributeError:
                        try:
                            self.pipe.enable_model_cpu_offload()
                        except:
                            pass
                    try:
                        self.pipe.enable_vae_slicing()
                    except:
                        pass
                    try:
                        self.pipe.enable_attention_slicing()
                    except:
                        pass
                elif vram_mode == 'med':
                    try:
                        self.pipe.enable_model_cpu_offload()
                    except AttributeError:
                        pass
                    try:
                        self.pipe.enable_attention_slicing()
                    except:
                        pass
                else:
                    # High VRAM mode - move entire pipeline to GPU
                    if not is_8bit and not is_4bit:
                        self.pipe = self.pipe.to(self.device)
                    try:
                        self.pipe.enable_attention_slicing()
                    except:
                        pass
            else:
                # CPU mode
                if not is_8bit and not is_4bit:
                    self.pipe = self.pipe.to(self.device)
            self.current_model_id = model_id
            # Disable NSFW safety checker — users choose NSFW models intentionally
            if hasattr(self.pipe, 'safety_checker') and self.pipe.safety_checker is not None:
                self.pipe.safety_checker = None
            if hasattr(self.pipe, 'feature_extractor'):
                self.pipe.feature_extractor = None
            if hasattr(self.pipe, 'requires_safety_checker'):
                self.pipe.requires_safety_checker = False
            self.set_sampler(self.sampler_name)
            return True
        except Exception as e:
            print(f'Error loading model: {e}')
            return False

    def unload_model(self):
        self.pipe = None
        self.current_model_id = None
        if hasattr(self, 'llm_pipeline'):
            self.llm_pipeline = None
        if hasattr(self, 'current_text_model_id'):
            self.current_text_model_id = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        import gc
        gc.collect()

    def delete_model(self, model_id: str) -> bool:
        if self.current_model_id == model_id:
            self.unload_model()
        import shutil
        safe_name = model_id.replace('/', '--')
        folder_path = os.path.join(self.models_dir, f'models--{safe_name}')
        if os.path.exists(folder_path):
            try:
                shutil.rmtree(folder_path)
                return True
            except Exception as e:
                print(f'Error deleting model {model_id}: {e}')
                return False
        return False

    def set_sampler(self, sampler_name: str):
        self.sampler_name = sampler_name
        if not self.pipe or not hasattr(self.pipe, 'scheduler'):
            return
            
        # Flow Matching models (Flux, SD3, Z-Image) do not support traditional DDPM/DPM schedulers
        if 'FlowMatch' in type(self.pipe.scheduler).__name__:
            print(f"Skipping sampler change for {type(self.pipe.scheduler).__name__}")
            return
            
        config = self.pipe.scheduler.config
        from diffusers import EulerAncestralDiscreteScheduler, DPMSolverMultistepScheduler, EulerDiscreteScheduler, DDIMScheduler, HeunDiscreteScheduler, KDPM2DiscreteScheduler, DPMSolverSinglestepScheduler
        
        try:
            if sampler_name == 'Euler a':
                self.pipe.scheduler = EulerAncestralDiscreteScheduler.from_config(config)
            elif sampler_name == 'Euler':
                self.pipe.scheduler = EulerDiscreteScheduler.from_config(config)
            elif sampler_name == 'DPM++ 2M Karras':
                self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(config, use_karras_sigmas=True, final_sigmas_type='sigma_min')
            elif sampler_name == 'DPM++ 2S a':
                self.pipe.scheduler = DPMSolverSinglestepScheduler.from_config(config)
            elif sampler_name == 'DPM2':
                self.pipe.scheduler = KDPM2DiscreteScheduler.from_config(config)
            elif sampler_name == 'DDIM':
                self.pipe.scheduler = DDIMScheduler.from_config(config)
            elif sampler_name == 'Heun':
                self.pipe.scheduler = HeunDiscreteScheduler.from_config(config)
        except Exception as e:
            print(f"Failed to set sampler {sampler_name}: {e}")

    def apply_lora(self, lora_id: str):
        if not self.pipe:
            return
        if not lora_id or str(lora_id).strip() == '':
            if self.current_lora_id is not None:
                try:
                    self.pipe.unload_lora_weights()
                except:
                    pass
                self.current_lora_id = None
            return
        if self.current_lora_id != lora_id:
            if self.current_lora_id is not None:
                try:
                    self.pipe.unload_lora_weights()
                except:
                    pass
            try:
                self.pipe.load_lora_weights(lora_id)
                self.current_lora_id = lora_id
            except Exception as e:
                print(f'Error loading LoRA {lora_id}: {e}')
                self.current_lora_id = None

    def generate_image(self, prompt: str, num_inference_steps: int=20, width: int=512, height: int=512, guidance_scale: float=7.0, negative_prompt: str=None, seed: int=-1, callback=None, lora_weight: float=1.0, controlnet_id: str=None, control_image=None, batch_size: int=1):
        if not self.pipe:
            raise ValueError('Модель не загружена. Пожалуйста, выберите модель в настройках.')
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        if seed is not None and seed >= 0:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
                
        pipe_kwargs = {'prompt': prompt, 'num_inference_steps': num_inference_steps, 'width': width, 'height': height, 'guidance_scale': guidance_scale, 'num_images_per_prompt': batch_size}
        if 'Flux' in type(self.pipe).__name__:
            pipe_kwargs['guidance_scale'] = 0.0
        elif negative_prompt:
            pipe_kwargs['negative_prompt'] = negative_prompt
        if self.current_lora_id is not None:
            pipe_kwargs['cross_attention_kwargs'] = {'scale': lora_weight}
        if callback:

            def adapter(pipe, step, timestep, callback_kwargs):
                latents = callback_kwargs['latents']
                callback(step, getattr(pipe, '_num_timesteps', len(pipe.scheduler.timesteps) if hasattr(pipe, 'scheduler') else 100), latents)
                return callback_kwargs
            pipe_kwargs['callback_on_step_end'] = adapter
        result = self.pipe(**pipe_kwargs)
        
        # Explicitly delete the result dictionary to free memory from PyTorch side
        if hasattr(result, 'images') and result.images:
            images = result.images
            del result
            import gc
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return images
        else:
            raise Exception('Pipeline did not return any images. Output was: ' + str(result))

    def upscale_image(self, image_path, scale=4, output_path=None):
        from super_image import EdsrModel, ImageLoader
        from PIL import Image
        import time
        from dotenv import load_dotenv
        load_dotenv()
        import torch
        import uuid
        import os
        if not output_path:
            output_path = os.path.join(os.path.dirname(image_path), f'upscaled_{uuid.uuid4().hex}.png')
        image = Image.open(image_path).convert('RGB')
        device = self.device
        model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=scale)
        model = model.to(device)
        inputs = ImageLoader.load_image(image).to(device)
        with torch.no_grad():
            preds = model(inputs)
        ImageLoader.save_image(preds, output_path)
        return output_path

    def generate_inpaint(self, prompt: str, init_image: Image.Image, mask_image: Image.Image, num_inference_steps: int=20, strength: float=1.0, guidance_scale: float=7.0, negative_prompt: str=None, seed: int=-1, callback=None, lora_weight: float=1.0, controlnet_id: str=None, control_image=None, batch_size: int=1) -> list:
        if not self.pipe:
            raise ValueError('Модель не загружена. Пожалуйста, выберите модель в настройках.')
        pipe_class_name = type(self.pipe).__name__
        if 'Flux' in pipe_class_name:
            from diffusers import FluxInpaintPipeline
            inpaint_pipe = FluxInpaintPipeline(**self.pipe.components)
        elif 'XL' in pipe_class_name:
            from diffusers import StableDiffusionXLInpaintPipeline
            inpaint_pipe = StableDiffusionXLInpaintPipeline(**self.pipe.components)
        else:
            from diffusers import AutoPipelineForInpainting
            inpaint_pipe = AutoPipelineForInpainting.from_pipe(self.pipe)
        is_quantized = False
        if hasattr(inpaint_pipe, 'unet') and getattr(inpaint_pipe.unet, 'is_quantized', False):
            is_quantized = True
        if hasattr(inpaint_pipe, 'transformer') and getattr(inpaint_pipe.transformer, 'is_quantized', False):
            is_quantized = True
        if not hasattr(self.pipe, 'hf_device_map') and (not is_quantized):
            inpaint_pipe = inpaint_pipe.to(self.device)
        generator = torch.Generator(device=self.device)
        if seed is not None and seed >= 0:
            generator.manual_seed(seed)
        else:
            generator.seed()
        init_image = init_image.convert('RGB')
        mask_image = mask_image.convert('RGB')
        pipe_kwargs = {'prompt': prompt, 'image': init_image, 'mask_image': mask_image, 'num_inference_steps': num_inference_steps, 'strength': strength, 'generator': generator, 'guidance_scale': guidance_scale, 'num_images_per_prompt': batch_size}
        if 'Flux' in type(self.pipe).__name__:
            pipe_kwargs['guidance_scale'] = 0.0
        elif negative_prompt:
            pipe_kwargs['negative_prompt'] = negative_prompt
        if self.current_lora_id is not None:
            pipe_kwargs['cross_attention_kwargs'] = {'scale': lora_weight}
        if callback:

            def adapter(pipe, step, timestep, callback_kwargs):
                latents = callback_kwargs['latents']
                callback(step, getattr(pipe, '_num_timesteps', len(pipe.scheduler.timesteps) if hasattr(pipe, 'scheduler') else 100), latents)
                return callback_kwargs
            pipe_kwargs['callback_on_step_end'] = adapter
            pipe_kwargs['callback_on_step_end_tensor_inputs'] = ['latents']
        images = inpaint_pipe(**pipe_kwargs).images
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return images

    def generate_img2img(self, prompt: str, init_image, strength: float=0.6, num_inference_steps: int=20, guidance_scale: float=7.0, negative_prompt: str=None, seed: int=-1, callback=None, lora_weight: float=1.0, controlnet_id: str=None, control_image=None, batch_size: int=1):
        if not self.pipe:
            raise ValueError('Модель не загружена. Пожалуйста, выберите модель в настройках.')
        import gc
        gc.collect()
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        pipe_class_name = type(self.pipe).__name__
        if 'Flux' in pipe_class_name:
            if 'text_encoder_2' not in self.pipe.components or 'tokenizer_2' not in self.pipe.components:
                raise ValueError("Эта кастомная модель имеет нестандартную архитектуру (отсутствует второй текстовый энкодер) и не поддерживает генерацию по картинке (Img2Img). Пожалуйста, удалите прикрепленное изображение или выберите стандартную модель FLUX.")
            from diffusers import FluxImg2ImgPipeline
            img2img_pipe = FluxImg2ImgPipeline(**self.pipe.components)
        elif 'XL' in pipe_class_name:
            from diffusers import StableDiffusionXLImg2ImgPipeline
            img2img_pipe = StableDiffusionXLImg2ImgPipeline(**self.pipe.components)
        else:
            from diffusers import AutoPipelineForImage2Image
            img2img_pipe = AutoPipelineForImage2Image.from_pipe(self.pipe)
        is_quantized = False
        if hasattr(img2img_pipe, 'unet') and getattr(img2img_pipe.unet, 'is_quantized', False):
            is_quantized = True
        if hasattr(img2img_pipe, 'transformer') and getattr(img2img_pipe.transformer, 'is_quantized', False):
            is_quantized = True
        if not hasattr(self.pipe, 'hf_device_map') and (not is_quantized):
            img2img_pipe = img2img_pipe.to(self.device)
        generator = torch.Generator(device=self.device)
        if seed is not None and seed >= 0:
            generator.manual_seed(seed)
        else:
            generator.seed()
        init_image = init_image.convert('RGB')
        pipe_kwargs = {'prompt': prompt, 'image': init_image, 'strength': strength, 'num_inference_steps': num_inference_steps, 'generator': generator, 'guidance_scale': guidance_scale, 'num_images_per_prompt': batch_size}
        if 'Flux' in type(self.pipe).__name__:
            pipe_kwargs['guidance_scale'] = 0.0
        elif negative_prompt:
            pipe_kwargs['negative_prompt'] = negative_prompt
        if self.current_lora_id is not None:
            pipe_kwargs['cross_attention_kwargs'] = {'scale': lora_weight}
        if callback:

            def adapter(pipe, step, timestep, callback_kwargs):
                latents = callback_kwargs['latents']
                callback(step, getattr(pipe, '_num_timesteps', len(pipe.scheduler.timesteps) if hasattr(pipe, 'scheduler') else 100), latents)
                return callback_kwargs
            pipe_kwargs['callback_on_step_end'] = adapter
            pipe_kwargs['callback_on_step_end_tensor_inputs'] = ['latents']
        images = img2img_pipe(**pipe_kwargs).images
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        return images

    def generate_video(self, image_path: str, prompt: str, output_path: str, negative_prompt: str=None, num_inference_steps: int=25, seed: int=-1, callback=None):
        if not self.pipe:
            print('No video pipeline loaded in memory')
            return None
        from PIL import Image
        import time
        from diffusers import StableVideoDiffusionPipeline, I2VGenXLPipeline
        import torch
        import gc
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        is_svd = isinstance(self.pipe, StableVideoDiffusionPipeline)
        is_i2vgen = isinstance(self.pipe, I2VGenXLPipeline)
        if not (is_svd or is_i2vgen):
            print('Current model is not a video model')
            return None
        init_image = Image.open(image_path).convert('RGB')
        (w, h) = init_image.size
        if is_svd:
            scale = 1024 / max(w, h)
        else:
            scale = 512 / max(w, h)
        (new_w, new_h) = (int(w * scale), int(h * scale))
        new_w = new_w // 8 * 8
        new_h = new_h // 8 * 8
        init_image = init_image.resize((new_w, new_h), Image.LANCZOS)
        generator = torch.Generator(device=self.device)
        if seed != -1:
            generator.manual_seed(seed)
        else:
            generator.seed()

        def pipe_callback(pipe, step, timestep, callback_kwargs):
            if callback:
                callback(step, num_inference_steps, f'Генерация кадров: {step}/{num_inference_steps}')
            time.sleep(0.01)
            return callback_kwargs
        try:
            if is_svd:
                frames = self.pipe(init_image, decode_chunk_size=8, generator=generator, num_inference_steps=num_inference_steps, callback_on_step_end=pipe_callback).frames[0]
            elif is_i2vgen:
                if not prompt or not prompt.strip():
                    prompt = 'moving, cinematic, high quality'
                if self.translator:
                    try:
                        prompt = self.translator(prompt)[0]['translation_text']
                    except:
                        pass
                frames = self.pipe(prompt=prompt, image=init_image, num_inference_steps=num_inference_steps, target_fps=16, generator=generator, callback_on_step_end=pipe_callback).frames[0]
            from diffusers.utils import export_to_video
            export_to_video(frames, output_path, fps=7 if is_svd else 16)
            import gc
            gc.collect()
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            return output_path
        except Exception as e:
            print(f'Video Generation Error: {e}')
            import traceback
            traceback.print_exc()
            return None

    def is_model_downloaded(self, model_id: str) -> bool:
        import os
        folder_name = f"models--{model_id.replace('/', '--')}"
        snapshots_dir = os.path.join(self.models_dir, folder_name, 'snapshots')
        if not os.path.isdir(snapshots_dir):
            return False
        try:
            return len(os.listdir(snapshots_dir)) > 0
        except Exception:
            return False

    import torch
    @torch.no_grad()
    def decode_latents(self, latents, width=None, height=None):
        if not self.pipe or not hasattr(self.pipe, 'vae') or self.pipe.vae is None:
            return None
            
        # Unpack latents for Flux models
        if 'Flux' in type(self.pipe).__name__:
            if width and height:
                try:
                    vae_scale_factor = getattr(self.pipe, 'vae_scale_factor', 16)
                    if hasattr(self.pipe, '_unpack_latents'):
                        latents = self.pipe._unpack_latents(latents, height, width, vae_scale_factor)
                    else:
                        from diffusers.pipelines.flux.pipeline_flux import FluxPipeline
                        latents = FluxPipeline._unpack_latents(self.pipe, latents, height, width, vae_scale_factor)
                except Exception as e:
                    return None
            else:
                return None
                
        try:
            config = self.pipe.vae.config
            scaling_factor = config.get('scaling_factor', 0.18215) if hasattr(config, 'get') else getattr(config, 'scaling_factor', 0.18215)
            
            scaled_latents = (latents / scaling_factor).to(self.pipe.vae.dtype)
            dec = self.pipe.vae.decode(scaled_latents, return_dict=False)[0]
            if hasattr(self.pipe, 'image_processor'):
                pil_images = self.pipe.image_processor.postprocess(dec, output_type='pil')
            else:
                dec = (dec / 2 + 0.5).clamp(0, 1)
                dec = dec.cpu().permute(0, 2, 3, 1).float().numpy()
                pil_images = self.pipe.numpy_to_pil(dec)
            
            # Prevent VAE memory leak during generation
            del scaled_latents
            del dec
            return pil_images[0] if pil_images else None
        except Exception as e:
            # Silently fail if decoding fails during preview to avoid spamming the console
            return None

    def translate_ru_to_en(self, text: str) -> str:
        import re
        if not bool(re.search('[а-яА-Я]', text)):
            return text
        if getattr(self, 'translator', None) is None:
            from transformers import MarianMTModel, MarianTokenizer
            self.tokenizer = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-ru-en', cache_dir=self.models_dir)
            try:
                self.translator = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-ru-en', cache_dir=self.models_dir)
            except Exception as e:
                err_msg = str(e).lower()
                if 'vulnerability' in err_msg or 'torch.load' in err_msg or 'not found' in err_msg:
                    self.translator = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-ru-en', cache_dir=self.models_dir, local_files_only=False)
                else:
                    raise e
        try:
            inputs = self.tokenizer(text, return_tensors='pt', padding=True)
            translated = self.translator.generate(**inputs)
            translated_text = self.tokenizer.decode(translated[0], skip_special_tokens=True)
            return translated_text
        except Exception as e:
            print(f'Error during translation: {e}')
        return text

    def enhance_prompt(self, text: str) -> str:
        """Enhances a short prompt using Gustavosta/MagicPrompt-Stable-Diffusion"""
        text = self.translate_ru_to_en(text)
        if getattr(self, 'prompt_enhancer', None) is None:
            from transformers import pipeline
            print('Loading MagicPrompt model...')
            try:
                self.prompt_enhancer = pipeline('text-generation', model='Gustavosta/MagicPrompt-Stable-Diffusion', device='cpu', model_kwargs={'cache_dir': self.models_dir})
            except Exception as e:
                err_msg = str(e).lower()
                if 'vulnerability' in err_msg or 'torch.load' in err_msg or 'not found' in err_msg:
                    self.prompt_enhancer = pipeline('text-generation', model='Gustavosta/MagicPrompt-Stable-Diffusion', device='cpu', model_kwargs={'cache_dir': self.models_dir, 'local_files_only': False})
                else:
                    raise e
            self.prompt_enhancer.tokenizer.pad_token_id = self.prompt_enhancer.tokenizer.eos_token_id
        try:
            result = self.prompt_enhancer(text, max_new_tokens=60, num_return_sequences=1, temperature=0.8, top_k=40, repetition_penalty=1.1, clean_up_tokenization_spaces=False)
            enhanced = result[0]['generated_text'].strip()
            if 'masterpiece' not in enhanced.lower() and 'best quality' not in enhanced.lower():
                enhanced += ', masterpiece, best quality, highly detailed, high resolution'
            import re
            enhanced = re.sub(',\\s*,', ',', enhanced)
            enhanced = re.sub('\\s+', ' ', enhanced).strip()
            return enhanced
        except Exception as e:
            print(f'Error during prompt enhancement: {e}')
            return text

    def run_adetailer(self, img: Image.Image, prompt: str, negative_prompt: str=None, seed: int=-1) -> Image.Image:
        """Runs an ADetailer-like pass to improve faces in the image"""
        try:
            import cv2
            import numpy as np
            cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            if len(faces) == 0:
                print('ADetailer: No faces detected.')
                return img
            print(f'ADetailer: Detected {len(faces)} faces, enhancing...')
            mask = np.zeros_like(gray)
            for (x, y, w, h) in faces:
                padding = int(w * 0.2)
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(img.width, x + w + padding)
                y2 = min(img.height, y + h + padding)
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            mask_pil = Image.fromarray(mask).convert('RGB')
            face_prompt = prompt + ', masterpiece, high quality, highly detailed face, perfect eyes, beautiful face'
            enhanced_imgs = self.generate_inpaint(prompt=face_prompt, init_image=img, mask_image=mask_pil, num_inference_steps=20, strength=0.4, guidance_scale=7.0, negative_prompt=negative_prompt, seed=seed)
            if enhanced_imgs:
                return enhanced_imgs[0]
            return img
        except Exception as e:
            print(f'ADetailer error: {e}')
            return img

    def load_text_model(self, model_id: str, precision: str='fp16'):
        print(f"Loading text model {model_id}...")
        self.current_text_model_id = model_id
        import torch
        from transformers import pipeline
        
        dtype = torch.float16 if precision == 'fp16' else torch.float32
        model_kwargs = {'cache_dir': self.models_dir}
        
        try:
            self.llm_pipeline = pipeline(
                "text-generation", 
                model=model_id, 
                device="cuda",
                torch_dtype=dtype,
                model_kwargs=model_kwargs
            )
            print("Text model loaded successfully.")
        except Exception as e:
            print(f"Failed to load text model: {e}")
            raise e

    def generate_text(self, prompt: str, system_prompt: str=None, max_new_tokens: int=512, temperature: float=0.7, top_p: float=0.9, repetition_penalty: float=1.1, streamer=None, cancel_check=None) -> str:
        if not getattr(self, 'llm_pipeline', None):
            return "Модель не загружена."
            
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            if hasattr(self.llm_pipeline.tokenizer, 'apply_chat_template') and self.llm_pipeline.tokenizer.chat_template is not None:
                prompt_text = self.llm_pipeline.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            else:
                prompt_text = ""
                if system_prompt: prompt_text += f"{system_prompt}\n\n"
                prompt_text += f"User: {prompt}\nAssistant:"
                
            kwargs = {
                "max_new_tokens": max_new_tokens,
                "do_sample": True if temperature > 0.1 else False,
                "temperature": max(0.1, temperature),
                "top_p": top_p,
                "repetition_penalty": repetition_penalty,
                "return_full_text": False
            }
            if cancel_check:
                from transformers import StoppingCriteria, StoppingCriteriaList
                class CancelCriteria(StoppingCriteria):
                    def __call__(self, input_ids, scores, **k):
                        return cancel_check()
                kwargs["stopping_criteria"] = StoppingCriteriaList([CancelCriteria()])
                
            if streamer:
                kwargs["streamer"] = streamer
                
            outputs = self.llm_pipeline(prompt_text, **kwargs)
            
            result = outputs[0]["generated_text"]
            if result.startswith(prompt_text):
                result = result[len(prompt_text):]
            return result.strip()
        except Exception as e:
            return f"Ошибка генерации текста: {e}"
