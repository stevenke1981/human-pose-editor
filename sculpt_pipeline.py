"""
sculpt_pipeline.py — Bridge to the Three.js Object Sculptor pipeline.

Wraps the sculpt CLI scripts as reusable Python components for:
  1. probe: analyze an image
  2. spec creation: build an ObjectSculptSpec JSON
  3. validation: validate the spec for a given pass
  4. generation: generate Three.js TypeScript factory code
  5. TS→JS conversion: adapt generated code for browser eval

All sculpt scripts live in threejs_sculpt_plugin/scripts/.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

# Path to the sculpt scripts directory
_SCRIPTS_DIR = Path(__file__).parent / "threejs_sculpt_plugin" / "scripts"


# ======================================================================
#  Subprocess Helpers
# ======================================================================

def _run_script(script_name: str, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Run a sculpt CLI script with arguments, return CompletedProcess."""
    script_path = _SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Sculpt script not found: {script_path}")

    cmd = [sys.executable, str(script_path), *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(_SCRIPTS_DIR),
    )
    return result


def _check_result(result: subprocess.CompletedProcess, label: str = "") -> str:
    """Check subprocess result; return stdout or raise on error."""
    if result.returncode != 0:
        stderr = result.stderr.strip() or "(no stderr)"
        raise RuntimeError(f"Sculpt {label} failed (code {result.returncode}):\n{stderr}")
    return result.stdout.strip()


# ======================================================================
#  Step 1: Probe — analyze a reference image
# ======================================================================

def probe_image(image_path: str) -> dict:
    """Run probe_reference_image.py on the given image.

    Returns a dict with image metadata (size, format, etc.).
    """
    path = str(Path(image_path).resolve())
    result = _run_script("probe_reference_image.py", path)
    output = _check_result(result, "probe")
    return json.loads(output)


# ======================================================================
#  Step 2: Spec Creation
# ======================================================================

def create_spec(
    target_name: str,
    image_path: Optional[str] = None,
    complexity: str = "moderate",
    intended_use: str = "browser-prop",
    quality_profile: str = "balanced",
    out_path: Optional[str] = None,
) -> str:
    """Run new_sculpt_spec.py to create an ObjectSculptSpec JSON.

    Args:
        target_name: Name of the object.
        image_path: Optional path to reference image.
        complexity: 'simple' | 'moderate' | 'complex' | 'ultra'
        intended_use: 'browser-prop' | 'game-prop' | 'animated' | etc.
        quality_profile: 'balanced' | 'reference-fidelity'
        out_path: Where to write the spec JSON. If None, uses a temp file.

    Returns:
        Path to the generated spec JSON file (as string).
    """
    args = [target_name, "--intended-use", intended_use,
            "--quality-profile", quality_profile,
            "--complexity", complexity]

    if image_path:
        args.extend(["--image", str(Path(image_path).resolve())])

    if out_path:
        args.extend(["--out", str(Path(out_path).resolve()), "--force"])
        _run_script("new_sculpt_spec.py", *args)
        return out_path
    else:
        # Use temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        tmp_path = tmp.name
        tmp.close()
        args.extend(["--out", tmp_path, "--force"])
        _run_script("new_sculpt_spec.py", *args)
        return tmp_path


# ======================================================================
#  Step 3: Validation
# ======================================================================

def validate_spec(spec_path: str, pass_id: str = "blockout") -> dict:
    """Validate a spec JSON file for a given pass.

    We import validate_spec from the sculpt module directly for speed.

    Returns:
        Dict with 'errors' (list), 'warnings' (list).
    """
    # Import from sculpt module
    sys.path.insert(0, str(_SCRIPTS_DIR))
    try:
        from validate_sculpt_spec import validate_spec as _validate
        from sculpt_contract import load_spec_file
        spec = load_spec_file(Path(spec_path))
        errors, warnings, _ = _validate(spec, pass_id)
        return {"errors": errors or [], "warnings": warnings or []}
    except Exception as e:
        # Fallback: run as subprocess
        result = _run_script(
            "validate_sculpt_spec.py", spec_path,
            "--for-pass", pass_id, "--strict-quality"
        )
        output = _check_result(result, "validate")
        return {"errors": [output] if result.returncode != 0 else [], "warnings": []}
    finally:
        sys.path.pop(0)


# ======================================================================
#  Step 4: Generation — run generate_threejs_factory.py
# ======================================================================

def generate_factory(spec_path: str, out_ts_path: Optional[str] = None) -> str:
    """Generate Three.js TypeScript factory code from a spec.

    Args:
        spec_path: Path to the ObjectSculptSpec JSON.
        out_ts_path: Where to write the .ts output. If None, uses temp file.

    Returns:
        Path to the generated .ts file.
    """
    if out_ts_path:
        out = str(Path(out_ts_path).resolve())
    else:
        tmp = tempfile.NamedTemporaryFile(suffix=".generated.ts", delete=False, mode="w")
        out = tmp.name
        tmp.close()

    result = _run_script(
        "generate_threejs_factory.py",
        str(Path(spec_path).resolve()),
        "--out", out,
        "--force",
    )
    # The script prints the output path on stdout on success
    _check_result(result, "generation")
    # If stdout has a path, use it; otherwise use our out
    stdout_path = result.stdout.strip()
    if stdout_path and Path(stdout_path).exists():
        return stdout_path
    return out


# ======================================================================
#  Step 5: TS → JS conversion for browser eval
# ======================================================================

def ts_to_js(ts_code: str) -> str:
    """Convert generated TypeScript Three.js factory to plain JavaScript.

    Strips TypeScript type annotations, interfaces, and type imports,
    converts `export function` to plain function, and removes
    type-only constructs.

    Args:
        ts_code: TypeScript source code from the generator.

    Returns:
        Plain JavaScript code that can be eval'd in a browser.
    """
    js = ts_code

    # 1. Strip full interface/type declarations (multi-line safe)
    #    Match from "interface Name {" or "type Name =" to balancing "}"
    js = re.sub(
        r'^(interface|type)\s+\w+[\s\S]*?\{[^}]*\}',
        '', js, flags=re.MULTILINE
    )

    # 2. Strip type imports (e.g., import type { ... } from ...)
    js = re.sub(r'^import\s+type\s+.*?;\s*$', '', js, flags=re.MULTILINE)

    # 3. Convert regular imports to assume THREE global
    js = re.sub(
        r'import\s+\*\s+as\s+THREE\s+from\s+[\'"]three[\'"]',
        '// THREE is global',
        js,
    )
    js = re.sub(
        r'import\s+\{\s*(.*?)\s*\}\s+from\s+[\'"]three[\'"]',
        r'const {\1} = THREE;',
        js,
    )
    js = re.sub(
        r'import\s+.*?from\s+[\'"]three/addons/.*?[\'"]',
        '',
        js,
    )

    # 4. Strip type annotations from function parameters
    js = re.sub(
        r':\s*(?:'
        r'string|number|boolean|void|any|never|undefined|null|'
        r'(?:THREE\.)?(?:Group|Mesh|Object3D|Vector3|Vector2|Color|'
        r'BufferGeometry|Material|MeshStandardMaterial|'
        r'MeshPhysicalMaterial|Texture|'
        r'ProceduralModelOptions|SculptRuntimeReceipt|'
        r'ReadonlyArray<\w+>|'
        r'Record\s*<\s*string\s*,\s*[^>]+\s*>'
        r')'
        r')(?=\s*[=,);{\])])',
        '', js
    )

    # 5. Remove `export` keyword but keep the declaration
    js = re.sub(r'\bexport\s+', '', js)

    # 6. Remove `as const` assertions
    js = re.sub(r'\sas\s+const', '', js)

    # 7. Remove readability type casts: `value as Type`
    js = re.sub(r'\s+as\s+\w+', '', js)

    # 8. Remove angle bracket type assertions: `<Type>value`
    js = re.sub(r'<[A-Z]\w+[A-Za-z<>]*>', '', js)

    # 9. Clean up empty lines from stripping
    js = re.sub(r'\n\s*\n\s*\n', '\n\n', js)

    return js.strip()


def read_and_convert_ts(ts_path: str) -> str:
    """Read a .ts file and convert to plain JS."""
    with open(ts_path, "r", encoding="utf-8") as f:
        ts_code = f.read()
    return ts_to_js(ts_code)


# ======================================================================
#  Full Pipeline
# ======================================================================

class PipelineResult:
    """Result of running the full sculpt pipeline."""
    def __init__(self):
        self.probe_result: Optional[dict] = None
        self.spec_path: Optional[str] = None
        self.validation: Optional[dict] = None
        self.ts_path: Optional[str] = None
        self.js_code: Optional[str] = None
        self.success: bool = False
        self.error: Optional[str] = None


def run_pipeline(
    image_path: str,
    target_name: str,
    complexity: str = "moderate",
    intended_use: str = "browser-prop",
    quality_profile: str = "balanced",
    pass_id: str = "blockout",
    work_dir: Optional[str] = None,
) -> PipelineResult:
    """Run the full sculpt pipeline end-to-end.

    Args:
        image_path: Path to reference image.
        target_name: Name of the object to sculpt.
        complexity: Complexity tier.
        intended_use: How the model will be used.
        quality_profile: Quality target.
        pass_id: Which build pass to generate.
        work_dir: Working directory for intermediate files. Defaults to temp dir.

    Returns:
        PipelineResult with all artifacts.
    """
    result = PipelineResult()

    try:
        # Ensure work directory
        if work_dir:
            base = Path(work_dir)
            base.mkdir(parents=True, exist_ok=True)
        else:
            base = Path(tempfile.mkdtemp(prefix="sculpt_pipeline_"))

        # Step 1: Probe
        print(f"[sculpt] Probing image: {image_path}")
        result.probe_result = probe_image(image_path)
        if not isinstance(result.probe_result, dict):
            raise RuntimeError(f"Probe returned non-dict: {result.probe_result}")

        # Step 2: Create spec
        spec_path = str(base / f"{target_name.lower().replace(' ', '_')}_spec.json")
        print(f"[sculpt] Creating spec: {spec_path}")
        result.spec_path = create_spec(
            target_name=target_name,
            image_path=image_path,
            complexity=complexity,
            intended_use=intended_use,
            quality_profile=quality_profile,
            out_path=spec_path,
        )

        # Step 3: Validate
        print(f"[sculpt] Validating spec for pass '{pass_id}'")
        result.validation = validate_spec(result.spec_path, pass_id=pass_id)
        if result.validation.get("errors"):
            errs = result.validation["errors"][:3]
            print(f"[sculpt] Validation warnings: {result.validation.get('warnings', [])}")
            print(f"[sculpt] Validation errors (first 3): {errs}")
            # Continue even with validation errors (generation may still work)

        # Step 4: Generate
        ts_path = str(base / f"{target_name.lower().replace(' ', '_')}.generated.ts")
        print(f"[sculpt] Generating Three.js factory: {ts_path}")
        result.ts_path = generate_factory(result.spec_path, out_ts_path=ts_path)

        # Step 5: Convert TS→JS
        print(f"[sculpt] Converting TS to JS")
        result.js_code = read_and_convert_ts(result.ts_path)

        result.success = True
        print(f"[sculpt] Pipeline complete")
        return result

    except Exception as e:
        result.error = str(e)
        result.success = False
        print(f"[sculpt] Pipeline failed: {e}")
        return result
