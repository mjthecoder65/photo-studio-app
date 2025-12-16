import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_user
from configs.db import get_db
from configs.settings import settings
from models.photo import PhotoResponse, PhotoStatus
from models.user import UserResponse
from services.ai_image_generator import AIImageGeneratorService
from services.firestore import FirestoreService
from services.photo import PhotoService
from services.storage import StorageService

router = APIRouter(prefix=f"/api/{settings.APP_VERSION}/ai-photos", tags=["AI Photos"])


def get_photo_service(db: AsyncSession = Depends(get_db)) -> PhotoService:
    return PhotoService(db)


def get_storage_service() -> StorageService:
    return StorageService()


def get_firestore_service() -> FirestoreService:
    return FirestoreService()


def get_ai_generator_service() -> AIImageGeneratorService:
    return AIImageGeneratorService()


@router.post(
    "/generate", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED
)
async def generate_photo_from_text(
    prompt: str = Form(..., description="Text description of the image to generate"),
    aspect_ratio: str = Form(
        default="1:1", description="Aspect ratio (e.g., 1:1, 16:9, 9:16)"
    ),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    storage_service: StorageService = Depends(get_storage_service),
    firestore_service: FirestoreService = Depends(get_firestore_service),
    ai_service: AIImageGeneratorService = Depends(get_ai_generator_service),
):
    """
    Generate a photo from a text prompt using AI (Gemini Nano Banana).

    Args:
        prompt: Text description of the image to generate
        aspect_ratio: Aspect ratio for the generated image
        current_user: Authenticated user
        photo_service: PhotoService dependency
        storage_service: StorageService dependency
        firestore_service: FirestoreService dependency
        ai_service: AIImageGeneratorService dependency

    Returns:
        PhotoResponse: The created photo record

    Raises:
        HTTPException 400: If aspect ratio is invalid
        HTTPException 500: If generation or upload fails
    """

    supported_ratios = ai_service.get_supported_aspect_ratios()
    if aspect_ratio not in supported_ratios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid aspect ratio. Supported: {', '.join(supported_ratios)}",
        )

    try:
        image_bytes, content_type = await ai_service.generate_image_from_text(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
        )

        image_file = io.BytesIO(image_bytes)
        filename = f"ai_generated_{aspect_ratio.replace(':', 'x')}.png"

        storage_path = await storage_service.upload_file(
            file=image_file,
            filename=filename,
            user_id=current_user.id,
            content_type=content_type,
        )

        photo = await photo_service.create_photo(
            user_id=current_user.id,
            storage_path=storage_path,
            status=PhotoStatus.UPLOADING,
        )

        await firestore_service.save_photo_metadata(
            photo_id=photo.id,
            user_id=current_user.id,
            storage_path=storage_path,
            filename=filename,
            content_type=content_type,
            file_size=len(image_bytes),
            status=PhotoStatus.PROCESSED.value,
            username=current_user.username,
            email=current_user.email,
            ai_generated=True,
            ai_prompt=prompt,
            ai_aspect_ratio=aspect_ratio,
            ai_model=settings.GEMINI_IMAGE_MODEL,
        )

        await photo_service.mark_as_processed(photo.id)

        return photo

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate photo: {str(e)}",
        )


@router.post(
    "/generate-from-reference",
    response_model=PhotoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_photo_from_reference(
    prompt: str = Form(..., description="Text description for image modification"),
    reference_image: UploadFile = File(..., description="Reference image"),
    aspect_ratio: str = Form("1:1", description="Aspect ratio (e.g., 1:1, 16:9, 9:16)"),
    current_user: UserResponse = Depends(get_current_user),
    photo_service: PhotoService = Depends(get_photo_service),
    storage_service: StorageService = Depends(get_storage_service),
    firestore_service: FirestoreService = Depends(get_firestore_service),
    ai_service: AIImageGeneratorService = Depends(get_ai_generator_service),
):

    if reference_image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {reference_image.content_type} not allowed",
        )

    supported_ratios = ai_service.get_supported_aspect_ratios()
    if aspect_ratio not in supported_ratios:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid aspect ratio. Supported: {', '.join(supported_ratios)}",
        )

    try:
        image_bytes, content_type = await ai_service.generate_image_from_text_and_image(
            prompt=prompt,
            reference_image=reference_image.file,
            reference_mime_type=reference_image.content_type,
            aspect_ratio=aspect_ratio,
        )

        image_file = io.BytesIO(image_bytes)

        filename = f"ai_modified_{aspect_ratio.replace(':', 'x')}.png"

        storage_path = await storage_service.upload_file(
            file=image_file,
            filename=filename,
            user_id=current_user.id,
            content_type=content_type,
        )

        photo = await photo_service.create_photo(
            user_id=current_user.id,
            storage_path=storage_path,
            status=PhotoStatus.UPLOADING,
        )

        await firestore_service.save_photo_metadata(
            photo_id=photo.id,
            user_id=current_user.id,
            storage_path=storage_path,
            filename=filename,
            content_type=content_type,
            file_size=len(image_bytes),
            status=PhotoStatus.PROCESSED.value,
            username=current_user.username,
            email=current_user.email,
            ai_generated=True,
            ai_prompt=prompt,
            ai_aspect_ratio=aspect_ratio,
            ai_model=settings.GEMINI_IMAGE_MODEL,
            ai_reference_image=reference_image.filename,
        )

        await photo_service.mark_as_processed(photo.id)

        return photo

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate photo from reference: {str(e)}",
        )


@router.get("/supported-aspect-ratios")
async def get_supported_aspect_ratios(
    ai_service: AIImageGeneratorService = Depends(get_ai_generator_service),
):
    """
    Get list of supported aspect ratios for AI image generation.

    Returns:
        dict: List of supported aspect ratios with descriptions
    """
    ratios = ai_service.get_supported_aspect_ratios()

    aspect_ratio_descriptions = {
        "1:1": "Square (1024x1024)",
        "2:3": "Portrait (832x1248)",
        "3:2": "Landscape (1248x832)",
        "3:4": "Portrait (864x1184)",
        "4:3": "Landscape (1184x864)",
        "4:5": "Portrait (896x1152)",
        "5:4": "Landscape (1152x896)",
        "9:16": "Vertical (768x1344)",
        "16:9": "Horizontal (1344x768)",
        "21:9": "Ultra-wide (1536x672)",
    }

    return {
        "supported_aspect_ratios": [
            {"ratio": ratio, "description": aspect_ratio_descriptions.get(ratio, "")}
            for ratio in ratios
        ]
    }
