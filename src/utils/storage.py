import os
from datetime import datetime
import math
import uuid
from typing import Tuple, List, Dict, Any
import functools

import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from fastapi import UploadFile
from slugify import slugify

from src.config import settings
from .exceptions import BadRequest, InternalServerError
from .logging import logger

s3_client = boto3.client(
    "s3",
    endpoint_url=settings.LIARA_ENDPOINT,
    aws_access_key_id=settings.LIARA_ACCESS_KEY,
    aws_secret_access_key=settings.LIARA_SECRET_KEY,
)

ALLOWED_IMAGE_TYPES = settings.ALLOWED_IMAGE_TYPES
ALLOWED_VIDEO_TYPES = settings.ALLOWED_VIDEO_TYPES


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename."""
    return os.path.splitext(filename)[1].lower()


def generate_object_key(
    entity_type: str, entity_name: str, filename: str, media_type: str = "image"
) -> str:
    """
    Generate an object key for storage with a simplified folder structure.
    All files for the same entity will be stored in the same folder.

    Args:
        entity_type: Type of entity (e.g., 'project', 'blog')
        entity_name: Name of the entity (e.g., project name)
        filename: Original filename
        media_type: Type of media ('image', 'video', etc.)

    Returns:
        Object key string
    """
    safe_entity = slugify(entity_type)
    safe_name = slugify(entity_name)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    extension = get_file_extension(filename)

    original_name = os.path.splitext(os.path.basename(filename))[0]
    safe_original_name = slugify(original_name)

    entity_type_plural = (
        f"{safe_entity}s" if not safe_entity.endswith("s") else safe_entity
    )

    return f"{entity_type_plural}/{safe_name}/{safe_original_name}-{timestamp}-{unique_id}{extension}"


def get_public_url(object_key: str) -> str:
    """Generate a public URL for the uploaded file."""
    return f"{settings.LIARA_ENDPOINT}/{settings.LIARA_BUCKET_NAME}/{object_key}"


async def upload_file(
    upload_file: UploadFile,
    entity_type: str,
    entity_name: str,
    max_size: int,
    allowed_types: List[str],
    size_unit: str = "MB",
    media_type: str = "files",
) -> Tuple[str, str]:
    """
    Upload a file to Liara object storage.

    Args:
        upload_file: The file to upload
        entity_type: Type of entity (e.g., 'project', 'blog')
        entity_name: Name of the entity (e.g., project name)
        max_size: Maximum file size in the specified unit
        allowed_types: List of allowed MIME types
        size_unit: Unit for max_size ('KB' or 'MB')
        media_type: Type of media for folder organization

    Returns:
        Tuple of (public_url, object_key)
    """
    if upload_file.content_type not in allowed_types:
        raise BadRequest(
            f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
        )

    content = await upload_file.read()
    await upload_file.seek(0)  # Reset file pointer

    # Calculate max size in bytes based on the unit
    if size_unit == "KB":
        max_bytes = max_size * 1024
    elif size_unit == "MB":
        max_bytes = max_size * 1024 * 1024
    else:
        raise ValueError(f"Invalid size unit: {size_unit}. Use 'KB' or 'MB'.")

    if len(content) > max_bytes:
        raise BadRequest(f"File too large. Maximum size: {max_size}{size_unit}")

    object_key = generate_object_key(
        entity_type, entity_name, upload_file.filename, media_type
    )

    try:
        temp_file_path = (
            f"/tmp/{uuid.uuid4().hex}{get_file_extension(upload_file.filename)}"
        )
        os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(content)

        s3_client.upload_file(
            temp_file_path,
            settings.LIARA_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": upload_file.content_type},
        )

        os.remove(temp_file_path)

        public_url = get_public_url(object_key)
        return public_url, object_key

    except NoCredentialsError:
        raise InternalServerError("Storage credentials not available")
    except ClientError as e:
        raise InternalServerError(f"Storage error: {str(e)}")
    except Exception as e:
        raise InternalServerError(f"Error uploading file: {str(e)}")


# Create specialized versions using partial
upload_image = functools.partial(
    upload_file,
    allowed_types=ALLOWED_IMAGE_TYPES,
    max_size=500,
    size_unit="KB",
    media_type="images",
)

upload_video = functools.partial(
    upload_file,
    allowed_types=ALLOWED_VIDEO_TYPES,
    max_size=100,
    size_unit="MB",
    media_type="videos",
)

upload_document = functools.partial(
    upload_file,
    allowed_types=["application/pdf"],
    max_size=10,
    size_unit="MB",
    media_type="documents",
)


async def replace_file(
    current_object_key: str,
    upload_file: UploadFile,
    entity_type: str,
    entity_name: str,
    is_video: bool = False,
    max_size: int = 500,  # KB for images, MB for videos
) -> Tuple[str, str]:
    """
    Replace an existing file with a new one.

    Args:
        current_object_key: The current object key to replace
        upload_file: The new file to upload
        entity_type: Type of entity (e.g., 'project', 'blog')
        entity_name: Name of the entity (e.g., project name)
        is_video: Whether the file is a video
        max_size: Maximum file size (KB for images, MB for videos)

    Returns:
        Tuple of (public_url, object_key)
    """
    # Upload the new file
    if is_video:
        new_url, new_key = await upload_video(
            upload_file=upload_file,
            entity_type=entity_type,
            entity_name=entity_name,
            max_size=max_size,
        )
    else:
        new_url, new_key = await upload_image(
            upload_file=upload_file,
            entity_type=entity_type,
            entity_name=entity_name,
            max_size=max_size,
        )

    delete_file(current_object_key)

    return new_url, new_key


def delete_file(object_key: str) -> bool:
    """
    Delete a file from Liara object storage.

    Args:
        object_key: The object key to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        s3_client.delete_object(Bucket=settings.LIARA_BUCKET_NAME, Key=object_key)
        return True
    except NoCredentialsError:
        print("Credentials not available.")
        return False
    except ClientError as e:
        print(f"Failed to delete file: {e}")
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False


def delete_files(object_keys: List[str]) -> Tuple[int, int]:
    """
    Delete multiple files from Liara object storage.

    Args:
        object_keys: List of object keys to delete

    Returns:
        Tuple of (successful_deletions, total_files)
    """
    successful = 0
    total = len(object_keys)

    for key in object_keys:
        if delete_file(key):
            successful += 1

    return successful, total


def extract_object_key_from_url(url: str) -> str:
    """
    Extract the object key from a full URL.

    Args:
        url: The full URL

    Returns:
        The object key
    """
    base_url = f"{settings.LIARA_ENDPOINT}/{settings.LIARA_BUCKET_NAME}/"
    if url.startswith(base_url):
        return url[len(base_url) :]

    if url.startswith("/"):
        parts = url.split("/")
        if len(parts) > 1 and parts[1] == settings.LIARA_BUCKET_NAME:
            return "/".join(parts[2:])

    return url


def file_exists(object_key: str) -> bool:
    """
    Check if a file exists in the bucket.

    Args:
        object_key: The object key to check

    Returns:
        True if the file exists, False otherwise
    """
    try:
        s3_client.head_object(Bucket=settings.LIARA_BUCKET_NAME, Key=object_key)
        return True
    except ClientError:
        return False
    except Exception:
        return False


def list_directory(
    prefix: str = "", delimiter: str = "/", max_keys: int = 1000
) -> Dict[str, Any]:
    """
    List contents of a directory (prefix) in the bucket.

    Args:
        prefix: The prefix (directory path) to list
        delimiter: The delimiter to use (typically '/' for directory-like structure)
        max_keys: Maximum number of keys to return

    Returns:
        Dictionary containing directories (CommonPrefixes) and files (Contents)
    """
    try:
        # Ensure prefix ends with delimiter if not empty
        if prefix and not prefix.endswith(delimiter):
            prefix = f"{prefix}{delimiter}"

        response = s3_client.list_objects_v2(
            Bucket=settings.LIARA_BUCKET_NAME,
            Prefix=prefix,
            Delimiter=delimiter,
            MaxKeys=max_keys,
        )

        result = {"directories": [], "files": [], "prefix": prefix, "total_size": 0}

        # Process directories (CommonPrefixes)
        if "CommonPrefixes" in response:
            for common_prefix in response["CommonPrefixes"]:
                dir_name = common_prefix["Prefix"]
                # Remove the current prefix to get just the directory name
                if prefix:
                    dir_name = dir_name.replace(prefix, "", 1)
                # Remove trailing delimiter
                if dir_name.endswith(delimiter):
                    dir_name = dir_name[: -len(delimiter)]

                if dir_name:  # Only add non-empty directory names
                    result["directories"].append(
                        {"name": dir_name, "prefix": common_prefix["Prefix"]}
                    )

        # Process files (Contents)
        if "Contents" in response:
            for item in response["Contents"]:
                # Skip the directory marker itself if it exists as an object
                if item["Key"] == prefix:
                    continue

                file_name = item["Key"]
                # Remove the current prefix to get just the file name
                if prefix:
                    file_name = file_name.replace(prefix, "", 1)

                # Skip items that contain the delimiter (these are in subdirectories)
                if delimiter in file_name:
                    continue

                file_info = {
                    "name": file_name,
                    "key": item["Key"],
                    "size": item["Size"],
                    "last_modified": item["LastModified"],
                    "url": get_public_url(item["Key"]),
                }

                result["files"].append(file_info)
                result["total_size"] += item["Size"]

        # Add pagination info
        result["is_truncated"] = response.get("IsTruncated", False)
        if result["is_truncated"]:
            result["next_continuation_token"] = response.get("NextContinuationToken")

        # Add summary info
        result["total_files"] = len(result["files"])
        result["total_directories"] = len(result["directories"])
        result["total_size_formatted"] = format_file_size(result["total_size"])

        return result

    except NoCredentialsError:
        logger.error("Storage credentials not available")
        raise InternalServerError("Storage credentials not available")
    except ClientError as e:
        logger.error(f"Storage error while listing directory: {str(e)}")
        raise InternalServerError(f"Storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing directory: {str(e)}")
        raise InternalServerError(f"Error listing directory: {str(e)}")


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Human-readable size string
    """
    if size_bytes == 0:
        return "0 B"

    size_names = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"
