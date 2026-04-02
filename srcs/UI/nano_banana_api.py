
"""
Wrapper for Gemini-based nano_banana API implementation.

This module exposes the functions expected by the UI:
 - t2i_generate(prompt, out_path)
 - it2i_edit(input_image, prompt, out_path)

If a `gemini/nano_banana_api.py` implementation exists, this wrapper calls
into it. If not available, it falls back to a simple placeholder implementation
that creates PNGs with the prompt text (so the UI remains usable offline).
"""
from pathlib import Path
import importlib


def _load_gemini_impl():
    try:
        return importlib.import_module("gemini.nano_banana_api")
    except Exception:
        return None


gemini_impl = _load_gemini_impl()


def _placeholder_make(text: str, out_path: Path, size=(768, 1024), bgcolor=(240, 240, 240)) -> str:
    """Create a simple placeholder PNG containing the provided text.

    This requires Pillow. Raises a RuntimeError with installation hint if
    Pillow is not available.
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception:
        raise RuntimeError("Pillow is required for placeholder image generation. Install with: pip install Pillow")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", size, bgcolor)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    # Simple word-wrap
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        line = ""
        for w in words:
            if len(line + " " + w) > 70:
                lines.append(line)
                line = w
            else:
                line = (line + " " + w).strip()
        if line:
            lines.append(line)

    y = 10
    for ln in lines:
        draw.text((10, y), ln, fill=(20, 20, 20), font=font)
        y += font.getsize(ln)[1] + 6

    img.save(out_path)
    return str(out_path)


def t2i_generate(prompt: str, out_path: str) -> str:
    """Generate an image from text.

    If a `gemini.nano_banana_api` implementation is available, call it with
    mode="t2i" and output_dir set to out_path. If it fails or is unavailable,
    produce a placeholder image.
    Returns the path to the generated image.
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if gemini_impl is not None:
        try:
            # gemini implementation signature: nano_banana_api(prompt, mode=..., api_key=..., img=..., output_dir=...)
            res = gemini_impl.nano_banana_api(prompt, mode="t2i", output_dir=str(out))
            # If the implementation returns a PIL Image-like object, try saving it.
            try:
                from PIL import Image
                if hasattr(res, "save"):
                    res.save(str(out))
            except Exception:
                # ignore; assume the implementation saved the file itself
                pass
            return str(out)
        except Exception as e:
            # fall back to placeholder
            return _placeholder_make(f"T2I:\n{prompt}\n\n(gemini call failed: {e})", out)

    return _placeholder_make(f"T2I:\n{prompt}", out)


def it2i_edit(input_image: str, prompt: str, out_path: str) -> str:
    """Edit an existing image guided by text prompt.

    If a `gemini.nano_banana_api` implementation is available, call it with
    mode="it2i", img=input_image and output_dir=out_path. Otherwise produce a placeholder.
    Returns the path to the edited image.
    """
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    if gemini_impl is not None:
        try:
            res = gemini_impl.nano_banana_api(prompt, mode="it2i", img=str(input_image), output_dir=str(out))
            try:
                from PIL import Image
                if hasattr(res, "save"):
                    res.save(str(out))
            except Exception:
                pass
            return str(out)
        except Exception as e:
            return _placeholder_make(f"IT2I edit of {Path(input_image).name}:\n{prompt}\n\n(gemini call failed: {e})", out)

    return _placeholder_make(f"IT2I edit of {Path(input_image).name}:\n{prompt}", out)
