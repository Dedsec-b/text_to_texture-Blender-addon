"""
AI Texture Generator for Blender
Generates PBR textures using AI via Kaggle GPU backend
"""
bl_info = {
    "name": "AI Texture Generator",
    "author": "AI Assistant",
    "version": (1, 4, 0),
    "blender": (4, 0, 0),
    "location": "Shader Editor > Sidebar > AI Textures",
    "description": "Generate PBR textures from text using AI (Stable Diffusion via Kaggle) with resize support",
    "category": "Material",
}

import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty, FloatProperty, PointerProperty
from bpy.types import Panel, Operator, PropertyGroup
import requests
import base64
import io
from PIL import Image
import os
import tempfile
import threading
import json

# ============================================================================
# Helpers
# ============================================================================
def get_ai_material(props):
    """Return the last generated material or first AI_ material."""
    mat_name = props.last_generated_material or None
    if mat_name:
        mat = bpy.data.materials.get(mat_name)
        if mat and mat.use_nodes:
            return mat
    for mat in bpy.data.materials:
        if mat.use_nodes and mat.name.startswith("AI_"):
            return mat
    return None


def ensure_mapping_setup(mat):
    """Ensure texture coordinate + mapping nodes exist and feed all image nodes."""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    mapping = nodes.get("AITEX_MAPPING")
    texcoord = nodes.get("AITEX_TEXCOORD")

    if texcoord is None:
        texcoord = nodes.new("ShaderNodeTexCoord")
        texcoord.name = "AITEX_TEXCOORD"
        texcoord.label = "AI Texture Coord"
        texcoord.location = (-900, 200)

    if mapping is None:
        mapping = nodes.new("ShaderNodeMapping")
        mapping.name = "AITEX_MAPPING"
        mapping.label = "AI Mapping"
        mapping.location = (-700, 200)

    # Ensure UV -> Mapping
    if not mapping.inputs["Vector"].links:
        links.new(texcoord.outputs.get("UV") or texcoord.outputs[0], mapping.inputs["Vector"])

    # Feed all texture nodes from mapping
    for node in nodes:
        if node.type == "TEX_IMAGE":
            if node.inputs.get("Vector"):
                # Remove existing links to Vector to keep things consistent
                for lnk in list(node.inputs["Vector"].links):
                    links.remove(lnk)
                links.new(mapping.outputs["Vector"], node.inputs["Vector"])

    return mapping


def apply_mapping_scale(props, mat=None):
    """Apply mapping scale properties to the mapping node on a material."""
    if mat is None:
        mat = get_ai_material(props)
    if not mat or not mat.use_nodes:
        return
    mapping = ensure_mapping_setup(mat)
    mapping.inputs["Scale"].default_value[0] = props.map_scale_x
    mapping.inputs["Scale"].default_value[1] = props.map_scale_y
    mapping.inputs["Scale"].default_value[2] = props.map_scale_z


def update_mapping_scale(self, context):
    """Update callback when mapping scale changes."""
    props = context.scene.ai_texture_props
    mat = get_ai_material(props)
    if mat:
        apply_mapping_scale(props, mat)


# ============================================================================
# Properties
# ============================================================================
class AITextureProperties(PropertyGroup):
    """Properties for AI Texture Generator"""
    
    # NEW: Object Picker
    target_object: PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        description="Select the object to apply the texture to",
        poll=lambda self, obj: obj.type == 'MESH'  # Only show Mesh objects (no cameras/lights)
    )
    
    prompt: StringProperty(
        name="Texture Prompt",
        description="Describe the texture you want to generate",
        default="rusty metal surface",
        maxlen=500
    )
    
    backend_url: StringProperty(
        name="Backend URL",
        description="Your local backend URL (http://127.0.0.1:5000)",
        default="http://127.0.0.1:5000",
        maxlen=1024
    )
    
    resolution: EnumProperty(
        name="Resolution",
        description="Texture resolution in pixels",
        items=[
            ('512', "512px", "Low resolution (fast)"),
            ('1024', "1024px (1K)", "Standard resolution"),
            ('2048', "2048px (2K)", "High resolution"),
            ('4096', "4096px (4K)", "Very high resolution (slow)"),
            ('8192', "8192px (8K)", "Maximum resolution (very slow)"),
        ],
        default='1024'
    )
    
    material_type: EnumProperty(
        name="Material Type",
        description="Type of material preset",
        items=[
            ('CUSTOM', "Custom", "Use custom prompt"),
            # Metals
            ('METAL_RUSTED', "Rusted Metal", "Rusty worn metal surface"),
            ('METAL_COPPER', "Copper", "Hammered copper with patina"),
            ('METAL_BRASS', "Brass", "Polished brass surface"),
            ('METAL_ALUMINUM', "Aluminum", "Brushed aluminum metal"),
            ('METAL_GOLD', "Gold", "Gold metal surface"),
            ('METAL_CHROME', "Chrome", "Shiny chrome metal"),
            ('METAL_STEEL', "Brushed Steel", "Brushed stainless steel"),
            ('METAL_IRON', "Cast Iron", "Rough cast iron"),
            # Woods
            ('WOOD_OAK', "Oak Wood", "Oak wood with grain"),
            ('WOOD_PINE', "Pine Wood", "Pine wood planks"),
            ('WOOD_MAHOGANY', "Mahogany", "Rich mahogany wood"),
            ('WOOD_BAMBOO', "Bamboo", "Bamboo texture"),
            ('WOOD_RECLAIMED', "Reclaimed Wood", "Old weathered wood"),
            # Stones
            ('STONE_GRANITE', "Granite", "Polished granite stone"),
            ('STONE_MARBLE', "Marble", "White marble with veins"),
            ('STONE_SANDSTONE', "Sandstone", "Rough sandstone blocks"),
            ('STONE_COBBLE', "Cobblestone", "Cobblestone pavement"),
            ('STONE_ROUGH', "Rough Stone", "Rough stone wall"),
            # Modern/Tech
            ('CARBON_FIBER', "Carbon Fiber", "Carbon fiber weave"),
            ('CONCRETE', "Concrete", "Rough concrete surface"),
            ('LEATHER', "Leather", "Worn leather texture"),
            ('FABRIC', "Fabric", "Woven fabric texture"),
            ('PLASTIC', "Plastic", "Smooth plastic surface"),
            ('RUBBER', "Rubber", "Textured rubber surface"),
        ],
        default='CUSTOM'
    )
    
    # Progress tracking
    is_generating: BoolProperty(
        name="Is Generating",
        description="Whether generation is in progress",
        default=False
    )
    
    generation_progress: FloatProperty(
        name="Progress",
        description="Generation progress (0.0 to 1.0)",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='PERCENTAGE'
    )
    
    generation_status: StringProperty(
        name="Status",
        description="Current generation status",
        default=""
    )
    
    # Tiling option
    make_tileable: BoolProperty(
        name="Make Tileable",
        description="Generate seamless tileable texture (perfect for floors, walls, terrain)",
        default=False
    )

    normal_strength: FloatProperty(
        name="Normal Strength",
        description="Strength of the generated normal map when applied to the material",
        default=1.5,
        min=0.1,
        max=20.0,
        soft_max=10.0
    )

    use_height_boost: BoolProperty(
        name="Height/Bump Boost",
        description="Add an extra bump from the diffuse map to enhance surface depth",
        default=False
    )

    height_strength: FloatProperty(
        name="Height Strength",
        description="Strength of the height/bump boost",
        default=0.3,
        min=0.0,
        max=5.0,
        soft_max=2.0
    )
    
    # Texture resize properties
    resize_resolution: EnumProperty(
        name="Resize To",
        description="New resolution for resizing textures",
        items=[
            ('256', "256px", "Very low resolution"),
            ('512', "512px", "Low resolution"),
            ('1024', "1024px (1K)", "Standard resolution"),
            ('2048', "2048px (2K)", "High resolution"),
            ('4096', "4096px (4K)", "Very high resolution"),
            ('8192', "8192px (8K)", "Maximum resolution"),
        ],
        default='1024'
    )
    
    resize_filter: EnumProperty(
        name="Resize Filter",
        description="Filter algorithm for resizing",
        items=[
            ('LANCZOS', "Lanczos", "High quality, best for upscaling"),
            ('BICUBIC', "Bicubic", "Good quality, smooth results"),
            ('BILINEAR', "Bilinear", "Fast, moderate quality"),
            ('NEAREST', "Nearest", "Fastest, pixelated"),
        ],
        default='LANCZOS'
    )
    
    # Store reference to last generated material
    last_generated_material: StringProperty(
        name="Last Material",
        description="Name of the last generated material",
        default=""
    )

    # Mapping scale (controls how big the texture appears on the mesh)
    map_scale_x: FloatProperty(
        name="Scale X",
        description="Texture mapping scale on X",
        default=1.0,
        min=0.01,
        soft_max=20.0,
        update=update_mapping_scale
    )
    map_scale_y: FloatProperty(
        name="Scale Y",
        description="Texture mapping scale on Y",
        default=1.0,
        min=0.01,
        soft_max=20.0,
        update=update_mapping_scale
    )
    map_scale_z: FloatProperty(
        name="Scale Z",
        description="Texture mapping scale on Z",
        default=1.0,
        min=0.01,
        soft_max=20.0,
        update=update_mapping_scale
    )


# ============================================================================
# Operators
# ============================================================================
class AITEX_OT_GenerateTextures(Operator):
    """Generate AI textures and apply to active material"""
    bl_idname = "aitex.generate_textures"
    bl_label = "Generate Textures"
    bl_options = {'REGISTER', 'UNDO'}
    
    _timer = None
    _thread = None
    _progress = 0.0
    _status = "Initializing..."
    _textures = None
    _error = None
    _prompt = ""
    
    def modal(self, context, event):
        if event.type == 'TIMER':
            # Update progress display
            context.area.tag_redraw()
            
            # Check if generation is complete
            if self._thread and not self._thread.is_alive():
                # Generation finished
                context.window_manager.event_timer_remove(self._timer)
                props = context.scene.ai_texture_props
                props.is_generating = False
                
                if self._error:
                    self.report({'ERROR'}, f"Error: {self._error}")
                    return {'CANCELLED'}
                
                if self._textures:
                    try:
                        # Apply textures to material
                        self.apply_to_material(context, self._textures, self._prompt)
                        self.report({'INFO'}, "✅ Textures generated and applied!")
                        return {'FINISHED'}
                    except Exception as e:
                        self.report({'ERROR'}, f"Error applying: {str(e)}")
                        return {'CANCELLED'}
                
                return {'CANCELLED'}
            
            # Update status display
            props = context.scene.ai_texture_props
            props.generation_progress = self._progress
            props.generation_status = self._status
            
            # Force UI redraw
            for area in context.screen.areas:
                if area.type == 'NODE_EDITOR':
                    area.tag_redraw()
        
        elif event.type in {'ESC'}:
            # Cancel generation
            context.window_manager.event_timer_remove(self._timer)
            props = context.scene.ai_texture_props
            props.is_generating = False
            self.report({'WARNING'}, "Generation cancelled")
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        props = context.scene.ai_texture_props
        
        # Check if Backend URL is set
        if not props.backend_url:
            self.report({'ERROR'}, "Please set your Backend URL (Railway or Kaggle)!")
            return {'CANCELLED'}

        # NEW: Check if Target Object is selected
        if not props.target_object:
            self.report({'ERROR'}, "Please select a Target Object first!")
            return {'CANCELLED'}
        
        # Get prompt
        self._prompt = props.prompt
        if props.material_type != 'CUSTOM':
            self._prompt = self.get_preset_prompt(props.material_type)
        
        # Reset progress
        self._progress = 0.0
        self._status = "Starting generation..."
        self._textures = None
        self._error = None
        props.is_generating = True
        props.generation_progress = 0.0
        props.generation_status = self._status
        
        # Start generation in background thread
        self._thread = threading.Thread(
            target=self._generate_thread,
            args=(props.backend_url, self._prompt, int(props.resolution), props.make_tileable)
        )
        self._thread.start()
        
        # Set up timer for modal updates
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        
        return {'RUNNING_MODAL'}
    
    def _generate_thread(self, backend_url, prompt, resolution, make_tileable):
        """Background thread for generation"""
        try:
            self._status = "Connecting to backend..."
            self._progress = 0.1
            
            # Call Backend API
            self._textures = self.generate_via_backend(backend_url, prompt, resolution, make_tileable)
            
            self._progress = 1.0
            self._status = "Complete!"
            
        except Exception as e:
            self._error = str(e)
            self._status = f"Error: {str(e)}"
    
    def get_preset_prompt(self, material_type):
        """Get preset prompt based on material type"""
        presets = {
            # Metals
            'METAL_RUSTED': "rusty worn metal surface with scratches, orange rust, blue oxidation, weathering",
            'METAL_COPPER': "hammered copper surface with verdigris patina, dents and texture",
            'METAL_BRASS': "polished brass metal surface with slight tarnish and reflections",
            'METAL_ALUMINUM': "brushed aluminum metal with linear grain pattern and scratches",
            'METAL_GOLD': "pure gold metal surface with subtle scratches and high reflectivity",
            'METAL_CHROME': "polished chrome metal with mirror-like reflections",
            'METAL_STEEL': "brushed stainless steel with directional grain and fingerprints",
            'METAL_IRON': "rough cast iron surface with pitted texture and dark finish",
            
            # Woods
            'WOOD_OAK': "oak wood planks with prominent grain, knots, and natural variations",
            'WOOD_PINE': "pine wood surface with visible grain lines and knots",
            'WOOD_MAHOGANY': "rich dark mahogany wood with fine grain and polished finish",
            'WOOD_BAMBOO': "bamboo texture with distinctive nodes and natural segmentation",
            'WOOD_RECLAIMED': "old weathered reclaimed wood with cracks, nail holes, and aged patina",
            
            # Stones
            'STONE_GRANITE': "polished granite stone with speckled pattern and crystalline structure",
            'STONE_MARBLE': "white marble with elegant gray veins and polished surface",
            'STONE_SANDSTONE': "rough sandstone blocks with layered sediment and weathering",
            'STONE_COBBLE': "dry cobblestone pavement with rectangular gray stones, individual brick pattern, matte finish, mortar gaps between stones, realistic outdoor paving",
            'STONE_ROUGH': "rough stone wall surface with cracks, texture, and natural irregularities",
            
            # Modern/Tech
            'CARBON_FIBER': "carbon fiber weave pattern with distinctive twill texture and glossy epoxy",
            'CONCRETE': "rough concrete surface with aggregate, pitting, and subtle cracks",
            'LEATHER': "worn leather texture with creases, wrinkles, and natural grain",
            'FABRIC': "woven fabric texture with detailed fiber pattern and slight roughness",
            'PLASTIC': "smooth molded plastic surface with subtle imperfections",
            'RUBBER': "textured rubber surface with grip pattern and matte finish",
        }
        return presets.get(material_type, "")
    
    def generate_via_backend(self, backend_url, prompt, resolution, make_tileable):
        """Send request to backend (Railway/Kaggle) and get textures back"""
        
        self._progress = 0.2
        self._status = "Sending request to backend..."
        
        # Prepare request
        payload = {
            "prompt": prompt,
            "resolution": resolution,
            "tileable": make_tileable
        }
        
        self._progress = 0.3
        self._status = "Generating textures with AI..."
        
        if "ngrok" in backend_url and backend_url.startswith("https://"):
            print("ℹ️ Detected ngrok URL - Forcing HTTP to bypass SSL issues")
            backend_url = backend_url.replace("https://", "http://")

        try:
            response = requests.post(
                f"{backend_url}/generate",
                json=payload,
                timeout=600, 
            )
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
        
        if response.status_code != 200:
            raise Exception(f"Backend API error: {response.status_code}")
        
        self._progress = 0.7
        self._status = "Receiving generated textures..."
        
        # Parse response
        data = response.json()
        
        self._progress = 0.85
        self._status = "Decoding texture images..."
        
        # Decode base64 images
        textures = {}
        for tex_type in ['diffuse', 'roughness', 'normal', 'metallic']:
            if tex_type in data:
                img_data = base64.b64decode(data[tex_type])
                img = Image.open(io.BytesIO(img_data))
                textures[tex_type] = img
        
        self._progress = 0.95
        self._status = "Preparing to apply textures..."
        
        return textures
    
    def apply_to_material(self, context, textures, prompt):
        """Create material and apply textures"""
        
        # NEW: Get the target object from properties
        props = context.scene.ai_texture_props
        target_obj = props.target_object
        
        if not target_obj:
            print("No target object selected!")
            return

        # Get or create material
        mat_name = f"AI_{prompt[:20]}"
        mat = bpy.data.materials.get(mat_name)
        if mat is None:
            mat = bpy.data.materials.new(name=mat_name)
        
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        
        # Clear existing nodes
        nodes.clear()
        
        # Add Principled BSDF
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        
        # Add Material Output
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (300, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        # Mapping setup
        mapping = ensure_mapping_setup(mat)
        
        # Save and add texture nodes
        y_offset = 0
        temp_dir = tempfile.gettempdir()

        # Track references for later wiring (e.g., height boost)
        diffuse_node = None
        normal_node = None
        
        for tex_type, img in textures.items():
            # Save image
            img_path = os.path.join(temp_dir, f"{mat_name}_{tex_type}.png")
            img.save(img_path)
            
            # Load into Blender
            bpy_img = bpy.data.images.load(img_path, check_existing=True)
            
            # Create texture node
            tex_node = nodes.new('ShaderNodeTexImage')
            tex_node.image = bpy_img
            tex_node.location = (-300, y_offset)
            
            # Connect mapping to tex node
            if tex_node.inputs.get("Vector"):
                links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])
            
            # Connect to BSDF
            if tex_type == 'diffuse':
                links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            elif tex_type == 'roughness':
                tex_node.image.colorspace_settings.name = 'Non-Color' # Important for roughness
                links.new(tex_node.outputs['Color'], bsdf.inputs['Roughness'])
            elif tex_type == 'metallic':
                tex_node.image.colorspace_settings.name = 'Non-Color'
                links.new(tex_node.outputs['Color'], bsdf.inputs['Metallic'])
            elif tex_type == 'normal':
                tex_node.image.colorspace_settings.name = 'Non-Color'
                # Add Normal Map node
                normal_node = nodes.new('ShaderNodeNormalMap')
                normal_node.location = (-150, y_offset)
                normal_node.inputs['Strength'].default_value = props.normal_strength
                links.new(tex_node.outputs['Color'], normal_node.inputs['Color'])
                links.new(normal_node.outputs['Normal'], bsdf.inputs['Normal'])
            
            y_offset -= 300

        # Optional height/bump boost using diffuse as height
        if props.use_height_boost and diffuse_node is not None:
            # Add RGB to BW
            rgb2bw = nodes.new('ShaderNodeRGBToBW')
            rgb2bw.label = "AI Height BW"
            rgb2bw.location = (diffuse_node.location.x + 200, diffuse_node.location.y)
            links.new(diffuse_node.outputs['Color'], rgb2bw.inputs['Color'])

            # Add Bump node
            bump_node = nodes.new('ShaderNodeBump')
            bump_node.label = "AI Height Bump"
            bump_node.location = (rgb2bw.location.x + 200, rgb2bw.location.y)
            bump_node.inputs['Strength'].default_value = props.height_strength

            links.new(rgb2bw.outputs['Val'], bump_node.inputs['Height'])

            # If normal node exists, feed it into bump Normal input to stack effects
            if normal_node:
                links.new(normal_node.outputs['Normal'], bump_node.inputs['Normal'])
                # Redirect BSDF Normal to bump output (replace prior link)
                # Remove previous normal->bsdf link
                for l in list(bsdf.inputs['Normal'].links):
                    links.remove(l)
                links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
            else:
                # No normal map; just use bump to BSDF
                links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
        
        # Assign material to the TARGET object (not just active object)
        if len(target_obj.data.materials) == 0:
            target_obj.data.materials.append(mat)
        else:
            target_obj.data.materials[0] = mat
        
        # Store material reference in properties for resize functionality
        props.last_generated_material = mat.name

        # Apply mapping scale values to the mapping node
        apply_mapping_scale(props, mat)

# ============================================================================
# Resize Operator
# ============================================================================
class AITEX_OT_ResizeTextures(Operator):
    """Resize textures in the last generated material"""
    bl_idname = "aitex.resize_textures"
    bl_label = "Resize Textures"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.ai_texture_props
        
        # Find the material
        mat_name = props.last_generated_material if hasattr(props, 'last_generated_material') else None
        if not mat_name:
            # Try to find any AI-generated material
            for mat in bpy.data.materials:
                if mat.use_nodes and mat.name.startswith("AI_"):
                    mat_name = mat.name
                    break
        
        if not mat_name:
            self.report({'ERROR'}, "No AI-generated material found! Generate textures first.")
            return {'CANCELLED'}
        
        mat = bpy.data.materials.get(mat_name)
        if not mat or not mat.use_nodes:
            self.report({'ERROR'}, f"Material '{mat_name}' not found or has no nodes!")
            return {'CANCELLED'}
        
        # Get new resolution
        new_resolution = int(props.resize_resolution)
        
        # Get resize filter
        filter_map = {
            'LANCZOS': Image.LANCZOS,
            'BICUBIC': Image.BICUBIC,
            'BILINEAR': Image.BILINEAR,
            'NEAREST': Image.NEAREST,
        }
        resize_filter = filter_map.get(props.resize_filter, Image.LANCZOS)
        
        # Find all texture image nodes
        nodes = mat.node_tree.nodes
        resized_count = 0
        
        for node in nodes:
            if node.type == 'TEX_IMAGE' and node.image:
                img = node.image
                old_size = img.size
                
                # Skip if already at target resolution
                if old_size[0] == new_resolution and old_size[1] == new_resolution:
                    continue
                
                # Resize the image
                try:
                    width, height = old_size
                    
                    # Save current image to temp file
                    temp_dir = tempfile.gettempdir()
                    temp_path = os.path.join(temp_dir, f"aitex_temp_{img.name}_{id(img)}.png")
                    
                    # Save image (use filepath if available, otherwise save_render)
                    if img.filepath and os.path.exists(bpy.path.abspath(img.filepath)):
                        temp_path = bpy.path.abspath(img.filepath)
                        pil_img = Image.open(temp_path)
                    else:
                        # Save to temp file
                        img.save_render(temp_path)
                        pil_img = Image.open(temp_path)
                    
                    # Convert to RGB if needed (handles RGBA, L, etc.)
                    if pil_img.mode != 'RGB':
                        pil_img = pil_img.convert('RGB')
                    
                    # Resize using PIL with selected filter
                    resized_pil = pil_img.resize((new_resolution, new_resolution), resize_filter)
                    
                    # Save resized image temporarily
                    resized_temp_path = os.path.join(temp_dir, f"aitex_resized_{img.name}_{id(img)}.png")
                    resized_pil.save(resized_temp_path, "PNG")
                    
                    # Update Blender image: scale first, then reload pixels
                    img.scale(new_resolution, new_resolution)
                    
                    # Load resized image data
                    resized_pil_rgba = resized_pil.convert('RGBA')
                    resized_data = list(resized_pil_rgba.getdata())
                    
                    # Convert to Blender pixel format (flat array of RGBA floats)
                    blender_pixels = []
                    for r, g, b, a in resized_data:
                        blender_pixels.extend([r / 255.0, g / 255.0, b / 255.0, a / 255.0])
                    
                    # Update image pixels
                    img.pixels[:] = blender_pixels
                    img.update()
                    
                    # Clean up temporary files
                    try:
                        if os.path.exists(temp_path) and temp_path.startswith(temp_dir):
                            os.remove(temp_path)
                        if os.path.exists(resized_temp_path):
                            os.remove(resized_temp_path)
                    except:
                        pass  # Ignore cleanup errors
                    
                    resized_count += 1
                    
                except Exception as e:
                    self.report({'WARNING'}, f"Could not resize {img.name}: {str(e)}")
                    import traceback
                    print(f"Resize error: {traceback.format_exc()}")
                    continue
        
        if resized_count > 0:
            self.report({'INFO'}, f"✅ Resized {resized_count} texture(s) to {new_resolution}x{new_resolution}")
        else:
            self.report({'INFO'}, "All textures already at target resolution")
        
        return {'FINISHED'}


# ============================================================================
# Mapping Scale Operators
# ============================================================================
class AITEX_OT_ResetMappingScale(Operator):
    """Reset texture mapping scale to 1,1,1"""
    bl_idname = "aitex.reset_mapping_scale"
    bl_label = "Reset Mapping Scale"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_texture_props
        props.map_scale_x = 1.0
        props.map_scale_y = 1.0
        props.map_scale_z = 1.0
        apply_mapping_scale(props)
        self.report({'INFO'}, "Mapping scale reset to 1,1,1")
        return {'FINISHED'}


class AITEX_OT_ApplyNormalStrength(Operator):
    """Apply the current normal strength to existing AI material"""
    bl_idname = "aitex.apply_normal_strength"
    bl_label = "Apply Normal Strength"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.ai_texture_props
        mat = get_ai_material(props)
        if not mat or not mat.use_nodes:
            self.report({'ERROR'}, "No AI material found to update.")
            return {'CANCELLED'}

        updated = 0
        for node in mat.node_tree.nodes:
            if node.type == 'NORMAL_MAP':
                node.inputs['Strength'].default_value = props.normal_strength
                updated += 1

        if updated == 0:
            self.report({'WARNING'}, "No Normal Map node found in AI material.")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Normal strength set to {props.normal_strength}")
        return {'FINISHED'}

# ============================================================================
# UI Panel
# ============================================================================
class AITEX_PT_MainPanel(Panel):
    """Main panel for AI Texture Generator"""
    bl_label = "AI Texture Generator"
    bl_idname = "AITEX_PT_main_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "AI Textures"
    
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'ShaderNodeTree'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.ai_texture_props
        
        # Backend Setup
        box = layout.box()
        box.label(text="Backend URL:", icon='URL')
        box.prop(props, "backend_url", text="")
        if not props.backend_url:
            box.label(text="⚠️ Set Railway or Kaggle URL", icon='ERROR')
        else:
            box.label(text="✓ Connected", icon='CHECKMARK')
        
        layout.separator()
        
        # Show progress if generating
        if props.is_generating:
            progress_box = layout.box()
            progress_box.label(text="Generating Textures...", icon='TIME')
            
            # Progress bar
            row = progress_box.row()
            row.prop(props, "generation_progress", slider=True, text="Progress")
            
            # Status text
            if props.generation_status:
                progress_box.label(text=props.generation_status, icon='INFO')
            
            layout.separator()
            
            # Can press ESC to cancel info
            info_row = layout.row()
            info_row.label(text="Press ESC to cancel", icon='EVENT_ESC')
            
            return  # Don't show other controls while generating
        
        # NEW: Target Object Picker
        box = layout.box()
        box.label(text="Target Object:", icon='OBJECT_DATAMODE')
        box.prop(props, "target_object", text="")
        
        # Material Type
        layout.prop(props, "material_type")
        
        # Prompt (only if custom)
        if props.material_type == 'CUSTOM':
            layout.prop(props, "prompt", text="")
        
        # Resolution
        layout.prop(props, "resolution")
        
        # Tileable option
        layout.prop(props, "make_tileable", text="Seamless Tiling")

        # Normal strength
        layout.prop(props, "normal_strength", slider=True)
        apply_row = layout.row()
        apply_row.operator("aitex.apply_normal_strength", icon='NORMALS_FACE')

        # Height/bump boost
        layout.prop(props, "use_height_boost")
        if props.use_height_boost:
            layout.prop(props, "height_strength", slider=True)
        
        layout.separator()
        
        # Generate button
        row = layout.row()
        row.scale_y = 2.0
        row.operator("aitex.generate_textures", icon='PLAY')
        
        layout.separator()
        
        # Info
        box = layout.box()
        box.label(text="Usage:", icon='INFO')
        box.label(text="1. Run install.bat (first time)")
        box.label(text="2. Run start_local_backend.bat")
        box.label(text="3. Paste http://127.0.0.1:5000 above")
        box.label(text="4. Select Object & Generate!")


# ============================================================================
# 3D Viewport Panel (Texture Scale)
# ============================================================================
class AITEX_PT_View3DScalePanel(Panel):
    """Viewport panel for adjusting texture mapping scale"""
    bl_label = "AI Texture Scale"
    bl_idname = "AITEX_PT_view3d_scale"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AI Textures"

    @classmethod
    def poll(cls, context):
        return context.object is not None and hasattr(context.scene, "ai_texture_props")

    def draw(self, context):
        layout = self.layout
        props = context.scene.ai_texture_props

        mat = get_ai_material(props)
        status_box = layout.box()
        status_box.label(text="Texture Scale", icon='TEXTURE')
        if mat:
            status_box.label(text=f"Material: {mat.name}", icon='MATERIAL')
        else:
            status_box.label(text="No AI material found", icon='ERROR')

        col = layout.column(align=True)
        col.prop(props, "map_scale_x")
        col.prop(props, "map_scale_y")
        col.prop(props, "map_scale_z")

        layout.operator("aitex.reset_mapping_scale", icon='LOOP_BACK')
        layout.label(text="Bigger value = more repeats (smaller texture)", icon='INFO')



# ============================================================================
# Registration
# ============================================================================
classes = (
    AITextureProperties,
    AITEX_OT_GenerateTextures,
    AITEX_OT_ResizeTextures,
    AITEX_PT_MainPanel,
    AITEX_OT_ResetMappingScale,
    AITEX_OT_ApplyNormalStrength,
    AITEX_PT_View3DScalePanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.ai_texture_props = bpy.props.PointerProperty(
        type=AITextureProperties
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.ai_texture_props

if __name__ == "__main__":
    register()