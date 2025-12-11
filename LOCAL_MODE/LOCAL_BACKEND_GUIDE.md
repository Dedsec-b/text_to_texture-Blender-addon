# Local Backend Quick Start Guide

## What is This?

The local backend allows you to run AI texture generation **entirely on your computer** - no cloud, no internet required after initial setup!

## System Requirements

### Minimum (CPU Mode):
- Windows 10/11
- 16GB RAM
- 10GB free disk space
- Internet (for initial setup only)
- ⚠️ **Very slow**: 30+ minutes per texture

### Recommended (GPU Mode):
- Windows 10/11
- NVIDIA GPU with 6GB+ VRAM (GTX 1060 6GB or better)
- 16GB RAM
- 10GB free disk space
- Internet (for initial setup only)
- ⚡ **Fast**: 3-5 minutes per texture

## Installation

### Step 1: Install Everything

1. **Right-click** `install.bat`
2. Select **"Run as administrator"**
3. Follow the prompts
4. Wait for installation to complete (~20-30 minutes)

**What gets installed:**
- Python 3.10 (if not present)
- PyTorch with CUDA support (if NVIDIA GPU detected)
- All AI libraries
- Flask web server

### Step 2: First-Time Model Download

1. Double-click `start_local_backend.bat`
2. Wait for AI model download (~4GB, 10-15 minutes)
3. Model is cached locally - only downloaded once!

### Step 3: Use in Blender

1. Server shows: `✅ Server ready! Use this URL in Blender:`
2. Copy the URL: `http://127.0.0.1:5000`
3. In Blender → AI Textures panel → Backend URL
4. Paste the URL
5. Generate textures!

## Daily Usage

After initial setup, it's super simple:

1. Double-click `start_local_backend.bat`
2. Wait ~30 seconds for server to start
3. Open Blender and generate textures
4. When done, press `Ctrl+C` in the backend window

**No internet needed after setup!** ✅

## Troubleshooting

### "Python is not installed"
- Run `install.bat` as administrator
- Manually install Python 3.10 from python.org
- Make sure "Add Python to PATH" is checked

### "CUDA out of memory"
- Lower resolution in Blender (1024px instead of 4K)
- Close other GPU applications (games, browsers)
- Your GPU needs 6GB+ VRAM for 1024px textures

### "Generation is very slow"
- Running on CPU? Expected behavior (use Cloud Mode instead)
- Close background applications
- Lower resolution to 512px

### "Cannot connect to http://127.0.0.1:5000"
- Make sure `start_local_backend.bat` is running
- Check for firewall blocking
- Restart the backend

### Model download fails
- Check internet connection
- Ensure 10GB+ free disk space
- Try again (downloads resume from where they stopped)

## File Structure

```
ai-texture-generator/
├── local_backend.py           # Main backend script
├── install.bat                # One-time installer
├── start_local_backend.bat    # Daily startup script
├── requirements_local.txt     # Python dependencies
└── models/                    # Model cache (created automatically)
    └── model_cache/           # ~4GB AI model stored here
```

## Advantages of Local Mode

✅ **Offline**: Works without internet (after setup

)  
✅ **Fast**: 3-5 min on GPU vs 30+ min on CPU  
✅ **Private**: Data never leaves your computer  
✅ **Free**: No cloud costs, unlimited generations  
✅ **Professional**: Perfect for demos/presentations  

## Disadvantages

❌ **Initial setup**: 20-30 min installation time  
❌ **Disk space**: Requires 10GB for model  
❌ **GPU recommended**: CPU mode is very slow  
❌ **Windows only**: These .bat files are Windows-specific  

## Need Help?

- Check the main README.md for detailed troubleshooting
- Open an issue on GitHub
- Use Cloud Mode if local setup is too complex

---

**Made with ❤️ for the 3D community**
