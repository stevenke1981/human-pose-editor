"""
prop_generator.py — Analyze an image and generate Three.js code for a 3D prop.

Pipeline:
  1. Load & analyze image (dimensions, aspect ratio, dominant colors)
  2. Determine shape category + structural decomposition
  3. Generate a Three.js factory function (JavaScript) that constructs the prop
  4. Return the JS code string for loading in the 3D viewer
"""
import math
import json
import os
from typing import Optional
from dataclasses import dataclass, field

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ======================================================================
#  Image Analysis
# ======================================================================

@dataclass
class ImageProfile:
    """Profile extracted from an input image."""
    width: int = 0
    height: int = 0
    aspect_ratio: float = 1.0
    dominant_colors: list = field(default_factory=list)  # [(r,g,b), ...]
    is_landscape: bool = True
    has_transparency: bool = False
    brightness: float = 0.5  # 0-1
    edge_density: float = 0.5  # 0-1 estimate
    category: str = "generic"  # tall, wide, square, humanoid, vehicle, organic


def _extract_dominant_colors(img, num_colors: int = 4) -> list:
    """Extract dominant colors by coarse quantization."""
    # Convert to RGB, handling RGBA transparency
    if img.mode == "RGBA":
        # Create a white background version
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])  # Use alpha as mask
        img = bg
    else:
        img = img.convert("RGB")

    # Resize for speed
    small = img.copy()
    small.thumbnail((64, 64), Image.NEAREST)
    pixels = list(small.getdata())
    if not pixels:
        return [(128, 128, 128)]

    # Handle grayscale (single int value per pixel)
    if isinstance(pixels[0], int):
        pixels = [(p, p, p) for p in pixels]

    # Simple color quantization: bin by coarse 32-per-channel buckets
    buckets = {}
    for r, g, b in pixels:
        key = ((r >> 5) << 10) | ((g >> 5) << 5) | (b >> 5)
        if key not in buckets:
            buckets[key] = {"count": 0, "r": 0, "g": 0, "b": 0}
        buckets[key]["count"] += 1
        buckets[key]["r"] += r
        buckets[key]["g"] += g
        buckets[key]["b"] += b

    # Take top buckets by count
    sorted_buckets = sorted(buckets.values(), key=lambda x: -x["count"])
    top = []
    for b in sorted_buckets[:num_colors]:
        n = b["count"]
        top.append((b["r"] // n, b["g"] // n, b["b"] // n))
    return top


def _estimate_edge_density(img) -> float:
    """Crude edge density estimate using PIL convolution."""
    try:
        from PIL import ImageFilter
        edges = img.convert("L").filter(ImageFilter.FIND_EDGES)
        pixels = list(edges.getdata())
        bright_pixels = sum(1 for p in pixels if p > 64)
        return bright_pixels / max(len(pixels), 1)
    except Exception:
        return 0.5


def analyze_image(image_path: str) -> Optional[ImageProfile]:
    """Analyze an image and return an ImageProfile."""
    if not HAS_PIL:
        return None

    try:
        img = Image.open(image_path)
        w, h = img.size
        profile = ImageProfile(
            width=w,
            height=h,
            aspect_ratio=w / max(h, 1),
            dominant_colors=_extract_dominant_colors(img),
            is_landscape=w > h,
            has_transparency=img.mode in ("RGBA", "P") and "transparency" in img.info,
        )

        # Brightness estimate
        gray = img.convert("L")
        pixels = list(gray.getdata())
        profile.brightness = sum(pixels) / (len(pixels) * 255.0) if pixels else 0.5

        # Edge density
        profile.edge_density = _estimate_edge_density(img)

        # Category by aspect ratio + brightness variance
        ar = profile.aspect_ratio
        if ar > 2.0:
            profile.category = "wide"
        elif ar < 0.5:
            profile.category = "tall"
        elif 0.8 <= ar <= 1.2:
            profile.category = "square"
        elif ar > 1.2 and profile.edge_density > 0.4:
            profile.category = "organic"
        elif ar < 0.8 and profile.brightness > 0.6:
            profile.category = "humanoid"
        else:
            profile.category = "generic"

        return profile
    except Exception as e:
        print(f"[prop_generator] Image analysis failed: {e}")
        return None


# ======================================================================
#  Three.js Code Generation Templates
# ======================================================================

CSS_COLOR_MAP = {
    0: "#ff4444", 1: "#44ff44", 2: "#4444ff", 3: "#ffff44",
    4: "#ff44ff", 5: "#44ffff", 6: "#ff8844", 7: "#88ff44",
}


def _rgb_to_hex(rgb) -> str:
    """Convert (r,g,b) to #xxxxxx hex string."""
    r, g, b = [min(255, max(0, int(c))) for c in rgb[:3]]
    return f"#{r:02x}{g:02x}{b:02x}"


def _make_material_blocks(colors: list, prefix: str = "") -> str:
    """Generate Three.js material definitions from color list."""
    blocks = []
    for i, rgb in enumerate(colors):
        hex_color = _rgb_to_hex(rgb)
        blocks.append(
            f'    const {prefix}mat{i} = new THREE.MeshStandardMaterial({{\n'
            f'      color: "{hex_color}",\n'
            f'      roughness: 0.5,\n'
            f'      metalness: 0.1,\n'
            f'    }});'
        )
    if not blocks:
        blocks.append(
            f'    const {prefix}mat0 = new THREE.MeshStandardMaterial({{\n'
            f'      color: "#88aadd",\n'
            f'      roughness: 0.5,\n'
            f'      metalness: 0.1,\n'
            f'    }});'
        )
    return "\n".join(blocks)


# ---- Shape templates ----

def _gen_wide_shape(profile: ImageProfile, colors: list) -> str:
    """Generate a wide object (e.g. vehicle, table, animal)."""
    w = min(profile.aspect_ratio * 0.8, 2.5)
    h = 0.6
    d = 0.8
    return f"""    // Main body
    const body = new THREE.Mesh(
      new THREE.BoxGeometry({w:.2f}, {h:.2f}, {d:.2f}),
      mat0.clone()
    );
    body.position.y = {h/2:.2f};
    body.castShadow = true;
    body.receiveShadow = true;
    group.add(body);

    // Top detail
    const top = new THREE.Mesh(
      new THREE.BoxGeometry({w*0.6:.2f}, {h*0.3:.2f}, {d*0.5:.2f}),
      mat1.clone()
    );
    top.position.y = {h + h*0.15:.2f};
    top.castShadow = true;
    group.add(top);
"""


def _gen_tall_shape(profile: ImageProfile, colors: list) -> str:
    """Generate a tall object (e.g. bottle, lamp, tree trunk)."""
    h = min(1.5 / profile.aspect_ratio, 2.0)
    r = 0.25
    return f"""    // Main body
    const body = new THREE.Mesh(
      new THREE.CylinderGeometry({r:.2f}, {r:.2f}, {h:.2f}, 16),
      mat0.clone()
    );
    body.position.y = {h/2:.2f};
    body.castShadow = true;
    body.receiveShadow = true;
    group.add(body);

    // Top
    const top = new THREE.Mesh(
      new THREE.SphereGeometry({r*0.7:.2f}, 12, 12),
      mat1.clone()
    );
    top.position.y = {h:.2f};
    top.castShadow = true;
    group.add(top);
"""


def _gen_square_shape(profile: ImageProfile, colors: list) -> str:
    """Generate a compact/square object (e.g. ball, box, pot)."""
    s = 0.6
    return f"""    // Core
    const core = new THREE.Mesh(
      new THREE.SphereGeometry({s:.2f}, 20, 20),
      mat0.clone()
    );
    core.position.y = {s:.2f};
    core.castShadow = true;
    core.receiveShadow = true;
    group.add(core);

    // Base
    const base = new THREE.Mesh(
      new THREE.CylinderGeometry({s*0.8:.2f}, {s*0.9:.2f}, {s*0.3:.2f}, 16),
      mat1.clone()
    );
    base.position.y = {s*0.15:.2f};
    base.castShadow = true;
    base.receiveShadow = true;
    group.add(base);
"""


def _gen_organic_shape(profile: ImageProfile, colors: list) -> str:
    """Generate an organic/organic object."""
    return f"""    // Main form (organic approximation)
    const body = new THREE.Mesh(
      new THREE.SphereGeometry(0.5, 24, 24),
      mat0.clone()
    );
    body.scale.set({min(profile.aspect_ratio, 2.0):.2f}, 1.0, 0.8);
    body.position.y = 0.5;
    body.castShadow = true;
    body.receiveShadow = true;
    group.add(body);

    // Detail elements
    const detail = new THREE.Mesh(
      new THREE.SphereGeometry(0.15, 12, 12),
      mat1.clone()
    );
    detail.position.set(0.3, 0.7, 0.3);
    detail.castShadow = true;
    group.add(detail);

    const detail2 = new THREE.Mesh(
      new THREE.SphereGeometry(0.12, 12, 12),
      ({'mat' + str(min(len(colors)-1, 2))}) || mat0.clone()
    );
    detail2.position.set(-0.25, 0.6, 0.25);
    detail2.castShadow = true;
    group.add(detail2);
"""


def _gen_humanoid_shape(profile: ImageProfile, colors: list) -> str:
    """Generate a humanoid/prop-like shape."""
    return """    // Torso
    const torso = new THREE.Mesh(
      new THREE.CylinderGeometry(0.3, 0.35, 0.7, 12),
      mat0.clone()
    );
    torso.position.y = 0.35;
    torso.castShadow = true;
    group.add(torso);

    // Head
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.2, 16, 16),
      mat1.clone()
    );
    head.position.y = 0.8;
    head.castShadow = true;
    group.add(head);
"""


def _gen_generic_shape(profile: ImageProfile, colors: list) -> str:
    """Default generic object generation."""
    w = min(profile.aspect_ratio * 0.6, 1.5)
    h = min(1.0 / profile.aspect_ratio if profile.aspect_ratio > 0 else 1.0, 1.5)
    d = 0.6
    return f"""    // Main form
    const body = new THREE.Mesh(
      new THREE.BoxGeometry({w:.2f}, {h:.2f}, {d:.2f}),
      mat0.clone()
    );
    body.position.y = {h/2:.2f};
    body.castShadow = true;
    body.receiveShadow = true;
    group.add(body);
"""


SHAPE_GENERATORS = {
    "wide": _gen_wide_shape,
    "tall": _gen_tall_shape,
    "square": _gen_square_shape,
    "organic": _gen_organic_shape,
    "humanoid": _gen_humanoid_shape,
    "generic": _gen_generic_shape,
}


# ======================================================================
#  Main Generation API
# ======================================================================

def generate_prop_code(
    image_path: str,
    prop_name: str = "GeneratedProp",
    complexity: str = "simple",
) -> Optional[str]:
    """Analyze an image and generate Three.js JavaScript code for a 3D prop.

    Args:
        image_path: Path to the reference image.
        prop_name: Name for the generated prop (used in JS identifiers).
        complexity: 'simple', 'moderate', 'detailed'.

    Returns:
        JavaScript code string, or None if generation fails.
    """
    profile = analyze_image(image_path)
    if profile is None:
        print(f"[prop_generator] Could not analyze: {image_path}")
        return None

    # Get colors - use dominant colors from image
    colors = profile.dominant_colors
    if not colors:
        colors = [(136, 170, 221), (100, 130, 180), (200, 200, 200)]

    # Pick shape generator
    cat = profile.category
    generator = SHAPE_GENERATORS.get(cat, _gen_generic_shape)
    shape_code = generator(profile, colors)

    # Build the complete JS code
    safe_name = prop_name.replace("'", "").replace('"', "").replace(" ", "_")
    js_code = f"""// Auto-generated Three.js prop: {prop_name}
// Image: {os.path.basename(image_path)}
// Category: {cat} | {profile.width}x{profile.height}

{_make_material_blocks(colors)}

function create{safe_name}() {{
  const group = new THREE.Group();
  group.name = '{safe_name}';

{shape_code}

  return group;
}}
"""

    return js_code


def generate_json_spec(
    image_path: str,
    prop_name: str = "GeneratedProp",
) -> Optional[dict]:
    """Generate a lightweight JSON spec describing the prop (metadata only)."""
    profile = analyze_image(image_path)
    if profile is None:
        return None

    return {
        "name": prop_name,
        "source_image": os.path.basename(image_path),
        "schema_version": "1.0",
        "profile": {
            "width": profile.width,
            "height": profile.height,
            "aspect_ratio": profile.aspect_ratio,
            "category": profile.category,
            "dominant_colors": [list(c) for c in profile.dominant_colors],
        },
        "generation": {
            "engine": "prop_generator.py",
            "complexity": "simple",
            "target": "threejs",
        },
    }
