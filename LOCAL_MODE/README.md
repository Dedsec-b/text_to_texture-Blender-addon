# 🖥️ LOCAL MODE Setup

## What This Is

This folder contains everything you need to run the AI Texture Generator **completely offline** on your own computer!

## What's Included

- `local_backend.py` - AI server that runs on your PC
- `install.bat` - One-click installer (installs Python + all dependencies)
- `start_local_backend.bat` - Daily startup script
- `blender_ai_textures.py` - Blender addon (local version)
- `requirements_local.txt` - List of dependencies
- `LOCAL_BACKEND_GUIDE.md` - Detailed instructions

## Quick Start

### Step 1: Install (One Time Only)

1. **Right-click** `install.bat`
2. Select **"Run as administrator"**
3. Wait ~20-30 minutes (installs Python, PyTorch, AI libraries)

### Step 2: Start Backend (Every Time You Use)

1. Double-click `start_local_backend.bat`
2. **First run**: Downloads AI model (~4GB, 10-15 min)
3. **After first run**: Starts instantly!
4. Copy URL: `http://127.0.0.1:5000`

### Step 3: Install Blender Addon

1. Open Blender → Edit → Preferences → Add-ons
2. Click "Install..." → Select `blender_ai_textures.py`
3. Enable the addon
4. In addon panel, paste: `http://127.0.0.1:5000`

### Step 4: Using the Addon in Blender

#### 4.1 Switch to Shader Editor

1. **Click the workspace icon** (top-left corner of Blender)
2. Select **"Shader Editor"** from the dropdown

![Workspace Selection](file:///C:/Users/Administrator/.gemini/antigravity/brain/ab4fc0e1-4082-419e-9f6c-198e7b902709/uploaded_image_1_1765432287292.png)

#### 4.2 Access AI Textures Panel

1. **Look at the right sidebar** in Shader Editor
2. **Click the "AI Textures" tab** (you may need to press `N` if sidebar is hidden)

![AI Textures Panel](file:///C:/Users/Administrator/.gemini/antigravity/brain/ab4fc0e1-4082-419e-9f6c-198e7b902709/uploaded_image_2_1765432287292.png)

#### 4.3 Select Your Object

1. In the 3D viewport (or outliner), **select the object** you want to texture
2. The object name will appear in the "Target Object" dropdown in the AI Textures panel

#### 4.4 Generate Textures

1. Choose a **material preset** (e.g., "Rusted Metal", "Oak Wood")
2. Select **resolution** (start with 1024px)
3. Check **"Seamless Tiling"** if needed (for floors/walls)
4. Click **"Generate Textures"** button
5. **Wait 3-5 minutes** for generation to complete

#### 4.5 View Your Textured Object

1. **Click the workspace icon** again (top-left)
2. Select **"3D Viewport"** (or press `Shift+F5`)

![Switch to 3D Viewport](file:///C:/Users/Administrator/.gemini/antigravity/brain/ab4fc0e1-4082-419e-9f6c-198e7b902709/uploaded_image_0_1765432287292.png)

3. **If texture doesn't appear**, change viewport shading:
   - Look for shading icons (top-right of viewport)
   - Click **"Material Preview"** (3rd icon) or press `Z` → Material Preview

#### 4.6 Adjust Texture Scale (Optional)

1. Press `N` to show the sidebar (In 3dviewport mode) 
2. Navigate to **"AI Textures"** tab
3. Under "Texture Scale", adjust **X, Y, Z** values:
   - **Higher values** = Texture repeats more (appears smaller)
   - **Lower values** = Texture appears larger
4. Click **"Apply Scale"** to update

---

## 💡 Quick Reference

**Keyboard Shortcuts:**
- `N` - Toggle sidebar on/off
- `Z` - Viewport shading menu
- `Shift+F5` - Switch to 3D Viewport
- `Shift+F3` - Switch to Shader Editor

**Viewport Shading Modes:**
- **Solid** - No textures visible
- **Material Preview** - See textures ✅
- **Rendered** - Full render preview

## System Requirements

**Minimum (CPU Mode):**
- Windows 10/11
- 16GB RAM
- 10GB free space
- ⚠️ VERY SLOW (30+ min per texture)

**Recommended (GPU Mode):**
- Windows 10/11
- NVIDIA GPU (GTX 1060 6GB or better)
- 16GB RAM
- 10GB free space
- ⚡ FAST (3-5 min per texture)

## Advantages

✅ **100% Offline** - Works without internet (after setup)  
✅ **Private** - Data never leaves your computer  
✅ **Fast** - 3-5 min on GPU  
✅ **Free** - Unlimited generations  
✅ **Reliable** - No cloud dependencies  

## Need Help?

Check `LOCAL_BACKEND_GUIDE.md` for detailed troubleshooting!

---

**Made with ❤️ for the 3D community**
