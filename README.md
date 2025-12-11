# 🎨 AI Texture Generator for Blender

> Generate professional PBR textures from text descriptions using AI — choose your mode!

[![Blender](https://img.shields.io/badge/Blender-4.0%2B-orange?logo=blender)](https://www.blender.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🚀 Choose Your Mode

This project offers **two ways** to generate AI textures. Choose based on your needs:

### 📁 **LOCAL_MODE/** - Run on Your Computer

**Best for:** Users with NVIDIA GPU

**Advantages:**
- ✅ **100% Offline** after initial setup
- ✅ **Fast** (3-5 min on GPU)
- ✅ **Private** (data never leaves PC)
- ✅ **Reliable** (no cloud dependencies)

**Requirements:**
- NVIDIA GPU with 6GB+ VRAM
- 10GB disk space
- Windows 10/11

[→ Go to LOCAL_MODE folder](./LOCAL_MODE/)

---

### 📁 **CLOUD_MODE/** - Use Free Cloud GPUs

**Best for:** Users without powerful GPU

**Advantages:**
- ✅ **Works on any PC** (even old laptops)
- ✅ **Free cloud GPU** (Kaggle/Colab)
- ✅ **No installation** needed
- ✅ **Easy setup** (5 minutes)

**Requirements:**
- Internet connection
- Kaggle or Google Colab account (free)

[→ Go to CLOUD_MODE folder](./CLOUD_MODE/)

---

## 🤔 Which Mode Should I Choose?

| Question | Answer | Recommended Mode |
|----------|--------|------------------|
| Do you have NVIDIA GPU (GTX 1060 6GB+)? | Yes | **LOCAL_MODE** |
| Do you have NVIDIA GPU? | No | **CLOUD_MODE** |
| Need to work without internet? | Yes | **LOCAL_MODE** |
| Want easiest setup? | Yes | **CLOUD_MODE** |
| Want fastest generation? | Yes | **LOCAL_MODE** |
| Using old/weak computer? | Yes | **CLOUD_MODE** |

**Still unsure?** Try CLOUD_MODE first (easier), then switch to LOCAL_MODE later if you want!

---

## ✨ Features (Both Modes)

- 🤖 **AI-Powered** - Uses Stable Diffusion
- 🎨 **Complete PBR Materials** - Generates 4 texture maps:
  - Diffuse/Base Color
  - Roughness
  - Normal Map
  - Metallic
- 🔧 **25+ Material Presets** - Metals, woods, stones, fabrics, etc.
- 🔄 **Seamless Tiling** - Perfect for floors/walls
- 📐 **UV Controls** - Adjust texture scale
- 🖼️ **Texture Resizing** - Change resolution after generation
- 🆓 **Completely Free** - No subscriptions

---

## 📖 Quick Start

### 1. Choose Your Mode

Navigate to either `LOCAL_MODE/` or `CLOUD_MODE/` folder

### 2. Follow the README

Each folder has its own README.md with specific instructions

### 3. Install Blender Addon

Install the `blender_ai_textures.py` from your chosen folder

### 4. Generate Textures!

Select object → Choose material → Generate!

---

## 📊 Mode Comparison

| Feature | LOCAL MODE | CLOUD MODE |
|---------|------------|------------|
| **Internet Required** | Setup only 🔌 | Always 🌐 |
| **Speed** | 3-5 min ⚡ | 3-5 min ⚡ |
| **Setup Time** | 20-30 min | 5-10 min |
| **GPU Requirement** | NVIDIA 6GB+ | None |
| **Privacy** | 100% private 🔒 | Uses cloud servers |
| **Reliability** | Always works ✅ | Depends on Kaggle |
| **Cost** | $0 💰 | $0 💰 |

---

## 🎯 What Makes This Special?

**vs. Texture Libraries (Polyhaven, Poliigon):**
- ✅ Unlimited custom textures from text
- ✅ No browsing/searching needed
- ✅ Completely free

**vs. Manual Creation (Photoshop/GIMP):**
- ✅ 100x faster (3 min vs 6 hours)
- ✅ No artistic skills needed
- ✅ Complete PBR workflow

**vs. Substance Designer:**
- ✅ Free (vs $20/month)
- ✅ Simpler (text prompt vs node graphs)
- ✅ Faster for prototyping

---

## 📚 Documentation

- [`LOCAL_MODE/README.md`](./LOCAL_MODE/README.md) - Local setup guide
- [`CLOUD_MODE/README.md`](./CLOUD_MODE/README.md) - Cloud setup guide
- [`LOCAL_MODE/LOCAL_BACKEND_GUIDE.md`](./LOCAL_MODE/LOCAL_BACKEND_GUIDE.md) - Detailed local troubleshooting

---

## 🐛 Need Help?

1. Check the README in your chosen mode folder
2. Look at mode-specific documentation
3. Open an issue on GitHub

---

## 🤝 Contributing

Contributions welcome! This project is open source.

---

## Future Development

> **Current Version:** 1.0 - Basic PBR texture generation from text prompts

This is an early release focused on core functionality. The following improvements are planned to address current limitations and expand capabilities.

### Planned Improvements

**Generation Quality**
- Image-to-texture conversion for matching real-world references
- Texture inpainting to edit specific regions without full regeneration  
- Real-time preview using faster diffusion models (LCM/Turbo)
- Higher quality normal map generation from dedicated models

**Workflow Integration**
- Batch processing for multiple objects simultaneously
- Material library with save/load functionality
- Preset customization and user-defined material templates
- Automatic LOD texture generation for performance optimization

**Control & Precision**
- Geometry-aware texture generation using ControlNet
- Fine-grained control over material properties (metalness, roughness ranges)
- Reference image style matching with CLIP guidance
- Texture variation generator from single base texture

**Production Features**
- Asset variation system for creating unique instances
- Context-aware weathering based on object type and environment
- Team collaboration with shared material libraries
- Scene-wide material consistency tools

**AI Assistant & Automation**
- Natural language Blender agent for workflow automation
- Automated modeling assistance (modifiers, boolean operations, array patterns)
- Intelligent material node network generation from descriptions
- Scene setup automation (lighting rigs, camera setups, render settings)
- Asset management and organization with AI suggestions
- Multi-step operation execution from simple text commands

**Technical Enhancements**
- Support for additional texture maps (ambient occlusion, displacement, emission)
- Multi-platform optimization (Windows, Linux, macOS)
- Integration with render engines beyond Cycles/Eevee
- Custom model fine-tuning on user-provided texture datasets

### Current Limitations

- Generation time: 3-5 minutes per material on local GPU
- Resolution: Optimal at 1024px, higher resolutions may timeout
- Material types: Best results with common materials (wood, metal, stone)
- Platform: Windows/Linux support, macOS in development

### Contributing

This project is open source. Contributions, bug reports, and feature suggestions are welcome through the project repository.

---

## License

MIT License - free to use, modify, and distribute!

---

## 🙏 Acknowledgments

- **Stable Diffusion** by Stability AI
- **Realistic Vision V5.1** model by SG161222
- **Blender Foundation** for amazing 3D software
- **Kaggle** for free GPU access

---

## ⭐ Support This Project

If you find this useful:
- Star this repository ⭐
- Share with other 3D artists
- Report bugs or suggest features
- Contribute code or documentation

---

**Made with ❤️ for the 3D community**

**Choose your mode and start creating! 🎨✨**
