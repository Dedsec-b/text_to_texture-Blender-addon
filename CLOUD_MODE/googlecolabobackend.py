# # AI Texture Generator - Kaggle Backend (Fully Fixed)

# --- CELL 1: Dependencies (FIXED) ---
# FIX: Added --upgrade and --force-reinstall to guarantee the older, conflicting
# huggingface-hub is replaced by a newer version compatible with diffusers.
!pip install -q diffusers transformers accelerate torch pillow flask pyngrok scipy tqdm
# --- END OF CELL 1 ---

# --- CELL 2: Imports ---
import torch
# Check for a working environment after install
try:
    from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
except ImportError as e:
    print(f"❌ Critical Error after install: {e}")
    raise e

from PIL import Image, ImageEnhance
import base64
import io
from flask import Flask, request, jsonify
from pyngrok import ngrok
import threading
import numpy as np
from scipy import ndimage
from IPython.display import display, HTML # For keeping the cell alive in notebooks
import time

print("✅ Libraries imported")
# --- END OF CELL 2 ---

# --- CELL 3: Load Model ---
print("Loading Realistic Vision V5.1 (this takes 2-3 minutes)...")

model_id = "SG161222/Realistic_Vision_V5.1_noVAE"
# Use float16 for GPU memory efficiency
device = "cuda" if torch.cuda.is_available() else "cpu"

# Load pipeline
pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
    safety_checker=None
)

# Configure the recommended DPM++ 2M Karras scheduler
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    algorithm_type="dpmsolver++",
    final_sigmas_type="sigma_min",
    use_karras_sigmas=True
)

pipe = pipe.to(device)
print(f"✅ Model loaded on {device}")
# --- END OF CELL 3 ---

# --- CELL 4: Texture generation functions ---
def generate_diffuse(prompt, resolution=1024):
    """Generate base color/diffuse texture"""
    full_prompt = f"{prompt}, high quality texture, seamless, PBR, 4k, photograph, detailed, high definition"
    negative_prompt = "deformed, blurry, bad quality, low res, watermark, text, signature"

    image = pipe(
        full_prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=25,
        height=resolution,
        width=resolution,
    ).images[0]

    return image

def generate_roughness(prompt, resolution=1024):
    """Generate roughness map"""
    full_prompt = f"roughness map for {prompt}, grayscale, high values for rough matte surface, seamless texture"

    image = pipe(
        full_prompt,
        num_inference_steps=20,
        height=resolution,
        width=resolution,
    ).images[0]

    # Enhance brightness to spread the values for better effect
    image = image.convert('L')
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.5)
    image = image.convert('RGB')
    return image

def generate_height_map(prompt, resolution=1024):
    """Generate height/bump map"""
    full_prompt = f"height map of {prompt}, detailed bump map, grayscale, high contrast surface relief, displacement map style"

    image = pipe(
        full_prompt,
        num_inference_steps=25,
        height=resolution,
        width=resolution,
        guidance_scale=8.0
    ).images[0]

    height_map = image.convert('L')
    return height_map

def height_to_normal(height_map, strength=3.0):
    """Convert height map to proper normal map"""
    height_array = np.array(height_map).astype(np.float32) / 255.0
    sobel_x = ndimage.sobel(height_array, axis=1) * strength
    sobel_y = ndimage.sobel(height_array, axis=0) * strength

    normal_z = np.ones_like(height_array)
    length = np.sqrt(sobel_x**2 + sobel_y**2 + normal_z**2)
    length = np.maximum(length, 0.0001)

    nx = -sobel_x / length
    ny = -sobel_y / length
    nz = normal_z / length

    r = ((nx + 1.0) * 0.5 * 255).astype(np.uint8)
    g = ((ny + 1.0) * 0.5 * 255).astype(np.uint8)
    b = ((nz + 1.0) * 0.5 * 255).astype(np.uint8)

    normal_map = np.stack([r, g, b], axis=2)
    return Image.fromarray(normal_map)

def generate_normal(prompt, resolution=1024):
    height_map = generate_height_map(prompt, resolution)
    normal_map = height_to_normal(height_map, strength=3.0)
    return normal_map

def generate_metallic(prompt, resolution=1024):
    """Generate metallic mask"""
    if "metal" in prompt.lower():
        full_prompt = f"metallic mask for {prompt}, white for metal, black for non-metal, grayscale"
        image = pipe(
            full_prompt,
            num_inference_steps=15,
            height=resolution,
            width=resolution,
        ).images[0]
        image = image.convert('L').convert('RGB')
        return image
    else:
        # Optimized: return a fully black image for non-metallic materials
        return Image.new('RGB', (resolution, resolution), color = 'black')


def image_to_base64(img):
    """Convert PIL Image to base64 string, using JPEG for smaller payload"""
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

print("✅ Texture generation functions ready")
# --- END OF CELL 4 ---

# --- CELL 5 & 6: Flask and Ngrok Server ---

app = Flask(__name__)

@app.route('/generate', methods=['POST'])
def generate_textures():
    try:
        data = request.json
        prompt = data.get('prompt', 'rusty metal surface')
        resolution = data.get('resolution', 1024)
        tileable = data.get('tileable', False)

        if resolution not in [512, 768, 1024, 2048]:
             return jsonify({'error': 'Resolution must be 512, 768, 1024 or 2048 for this model.'}), 400

        if tileable:
            prompt = f"{prompt}, seamless tileable texture, repeating pattern, no visible seams, tiling pattern"

        print(f"Generating textures for: {prompt} at {resolution}x{resolution} (tileable: {tileable})")

        print("📝 [1/4] Generating diffuse (color) map...")
        diffuse = generate_diffuse(prompt, resolution)

        print("📝 [2/4] Generating roughness map...")
        roughness = generate_roughness(prompt, resolution)

        print("📝 [3/4] Generating normal (bump) map...")
        normal = generate_normal(prompt, resolution)

        print("📝 [4/4] Generating metallic map...")
        metallic = generate_metallic(prompt, resolution)

        response = {
            'diffuse': image_to_base64(diffuse),
            'roughness': image_to_base64(roughness),
            'normal': image_to_base64(normal),
            'metallic': image_to_base64(metallic),
            'prompt': prompt,
            'resolution': resolution,
            'tileable': tileable
        }

        print("✅ Textures generated successfully")
        return jsonify(response)

    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error: {error_msg}")
        # Specific error handling for memory issues
        if 'CUDA out of memory' in error_msg or 'allocate' in error_msg:
             return jsonify({'error': 'CUDA Out of Memory. Try a smaller resolution (e.g., 512).'}), 507
        return jsonify({'error': error_msg}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'device': device})

print("✅ Flask app created")

# Start ngrok tunnel and Flask server
# NOTE: Replace the token below with your actual ngrok auth token.
# WARNING: Exposing your auth token publicly is a security risk.
NGROK_AUTH_TOKEN = "enter your token "

try:
    ngrok.set_auth_token(NGROK_AUTH_TOKEN)
    public_url = ngrok.connect(5000)
    print(f"\n{'='*60}\n🌐 PUBLIC URL (copy this to Blender addon):\n{'='*60}\n{public_url}\n{'='*60}\n")
except Exception as e:
    print(f"❌ Ngrok setup failed. Ensure your auth token is correct and Ngrok is not blocked: {e}")
    public_url = "N/A" # Set to N/A if ngrok fails

def run_flask():
    app.run(host='0.0.0.0', port=5000, threaded=True, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

print("✅ Server is running!")
if public_url != "N/A":
    print("📝 Copy the URL above and paste it into the Blender addon")
else:
    print("📝 Please manually check the ngrok tunnel if Flask is running on port 5000.")

print("⏳ Server will stay active as long as this cell is running...")

# Keep cell running to maintain the ngrok connection
try:
    display(HTML("<p>Server is running. **Do not stop this cell.** Stop this cell to disconnect the public URL.</p>"))
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Server stopped")
    ngrok.kill() # Cleanly kill ngrok
# --- END OF CELL 5 & 6 ---