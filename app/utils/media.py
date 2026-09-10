import os
import re
import logging
from typing import Optional, List, Dict, Any, Union
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configure Cloudinary credentials from environment
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )
else:
    logger.info("Cloudinary credentials are not fully set in environment variables.")

# Regex patterns for URL parsing
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}
TRANSFORMATION_PATTERN = re.compile(r"^(?:[a-z]{1,3}_[a-zA-Z0-9_-]+|s--.+--)$")


def parse_cloudinary_url(url: str) -> Dict[str, Optional[str]]:
    """
    Extracts Cloudinary public_id and media_type (image/video) from a Cloudinary URL or identifier.
    Works with folders, transformations, and version prefixes.
    """
    if not url:
        return {"public_id": None, "media_type": "image"}

    # If it is not an HTTP URL, it is likely already a raw public_id
    if not url.startswith(("http://", "https://")):
        return {"public_id": url, "media_type": "image"}

    clean_url = url.split("?")[0].split("#")[0]

    # Detect video from path or extension
    is_video = "/video/" in clean_url or any(
        clean_url.lower().endswith(ext) for ext in VIDEO_EXTENSIONS
    )
    media_type = "video" if is_video else "image"

    if "/upload/" not in clean_url:
        return {"public_id": None, "media_type": media_type}

    after_upload = clean_url.split("/upload/", 1)[1]
    segments = after_upload.split("/")

    public_id_parts = []
    for i, seg in enumerate(segments):
        # Version segment like v1570979139
        if re.match(r"^v\d+$", seg):
            public_id_parts = segments[i + 1:]
            break
        # Skip transformation segments like w_200,h_200 or s--hash--
        elif ("," in seg) or bool(TRANSFORMATION_PATTERN.match(seg)):
            continue
        else:
            # First segment of actual folder/public_id
            public_id_parts = segments[i:]
            break

    if public_id_parts:
        raw_id = "/".join(public_id_parts)
        # Strip file extension (.jpg, .png, etc.) as Cloudinary IDs don't include it
        public_id = re.sub(r"\.[a-zA-Z0-9]+$", "", raw_id)
        return {"public_id": public_id, "media_type": media_type}

    return {"public_id": None, "media_type": media_type}


def process_media_item(item: Union[Dict[str, Any], str, Any]) -> Dict[str, Any]:
    """
    Normalizes a media input into a dict containing {url, media_type, public_id}.
    Automatically detects public_id and media_type from the URL if not provided.
    """
    if isinstance(item, str):
        parsed = parse_cloudinary_url(item)
        return {
            "url": item,
            "media_type": parsed["media_type"],
            "public_id": parsed["public_id"],
        }

    # If item is a Pydantic model or dict-like object
    if hasattr(item, "model_dump"):
        item_dict = item.model_dump()
    elif hasattr(item, "dict"):
        item_dict = item.dict()
    elif isinstance(item, dict):
        item_dict = dict(item)
    else:
        item_dict = {"url": str(item)}

    url = item_dict.get("url", "")
    public_id = item_dict.get("public_id")
    media_type = item_dict.get("media_type")

    # If public_id or media_type is missing, attempt to extract from URL
    if url and (not public_id or not media_type):
        parsed = parse_cloudinary_url(url)
        if not public_id:
            public_id = parsed.get("public_id")
        if not media_type:
            media_type = parsed.get("media_type", "image")

    return {
        "url": url,
        "media_type": media_type or "image",
        "public_id": public_id,
    }


def process_media_list(media_items: Optional[List[Any]]) -> List[Dict[str, Any]]:
    """
    Processes a list of media items and returns standard normalized media objects.
    """
    if not media_items:
        return []
    return [process_media_item(item) for item in media_items]


def delete_cloudinary_media(public_id: str, resource_type: str = "image") -> bool:
    """
    Sends an API request to Cloudinary to delete the media asset.
    """
    if not public_id:
        return False

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not (cloud_name and api_key and api_secret):
        logger.warning(
            f"Cloudinary credentials missing in .env. Skipping remote delete for public_id: {public_id}"
        )
        return False

    try:
        response = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
        logger.info(f"Cloudinary destroy response for '{public_id}' ({resource_type}): {response}")
        return response.get("result") in ["ok", "not found"]
    except Exception as exc:
        logger.error(f"Failed to delete Cloudinary media '{public_id}': {exc}")
        return False


def delete_post_media_files(media_list: Optional[List[Dict[str, Any]]]) -> None:
    """
    Iterates through a list of media dicts and removes each one from Cloudinary.
    """
    if not media_list or not isinstance(media_list, list):
        return

    for item in media_list:
        if not isinstance(item, dict):
            continue

        public_id = item.get("public_id")
        media_type = item.get("media_type") or "image"
        url = item.get("url")

        # Fallback: if public_id was not saved, extract it from URL now
        if not public_id and url:
            parsed = parse_cloudinary_url(url)
            public_id = parsed.get("public_id")
            if not media_type:
                media_type = parsed.get("media_type", "image")

        if public_id:
            delete_cloudinary_media(public_id=public_id, resource_type=media_type) #type: ignore
