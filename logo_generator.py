import os
import logging
import httpx
from openai import OpenAI

logger = logging.getLogger(__name__)

try:
    client = OpenAI()
except Exception as e:
    logger.error(f"Failed to initialize OpenAI client: {e}")
    client = None

def build_logo_prompt(brand_name: str, niche: str, colors: str, style: str, slogan: str = "") -> str:
    """Automates professional branding prompt engineering rules wrapper."""
    slogan_addition = f" incorporating the slogan/tagline '{slogan}'" if slogan else ""
    
    prompt = (
        f"Create a clean, {style.lower()}, premium vector-style logo for a {niche} brand named '{brand_name}'{slogan_addition}. "
        f"Use a professional {colors} color palette. The design must be minimalist, isolated on a solid crisp white background, "
        f"scalable, suitable for professional commercial branding, websites, and high-resolution print graphics. "
        f"No realistic photographic details, sharp clean vectors only."
    )
    return prompt

async def generate_logo(prompt: str, quality_hd: bool = False) -> str:
    """Calls OpenAI image generation model to produce high-quality logo URLs."""
    if not client:
        logger.error("OpenAI client not configured.")
        return None
        
    try:
        # Standardize fallback to standard commercial generation parameters
        response = client.images.generate(
            model="dall-e-3",  # Uses robust production DALL-E 3 model architectures
            prompt=prompt,
            n=1,
            size="1024x1024",
            quality="hd" if quality_hd else "standard"
        )
        return response.data[0].url
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return None

async def download_image(url: str, save_path: str) -> bool:
    """Downloads the generated image file locally."""
    try:
        async with httpx.AsyncClient() as client_http:
            res = await client_http.get(url)
            if res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(res.content)
                return True
    except Exception as e:
        logger.error(f"Failed to download image from endpoint: {e}")
    return False

