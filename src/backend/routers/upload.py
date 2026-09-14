"""
Upload router for Threat Intelligence alerts.
Handles multipart CSV uploads, performs file-level validation, and stores files safely.
"""

import io
import logging
import uuid
from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

try:
    from database.session import get_db
    from database.models import Alert as AlertDB, UserDB
    from schemas.upload import UploadResponse, ErrorResponse, IngestResponse
    from services.file_storage import FileStorageService, StorageValidationError, BASE_DIR
    from services.csv_parser import CSVParser, CSVParserError
    from repositories.alert_repository import AlertRepository
    from routers.auth import get_current_user_obj
except ImportError:
    from backend.database.session import get_db
    from backend.database.models import Alert as AlertDB, UserDB
    from backend.schemas.upload import UploadResponse, ErrorResponse, IngestResponse
    from backend.services.file_storage import FileStorageService, StorageValidationError, BASE_DIR
    from backend.services.csv_parser import CSVParser, CSVParserError
    from backend.repositories.alert_repository import AlertRepository
    from backend.routers.auth import get_current_user_obj

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1",
    tags=["Alert Upload & Ingestion"],
)

storage_service = FileStorageService()
csv_parser = CSVParser()


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Raw Alerts CSV",
    description=(
        "Accepts a raw security alert CSV file via multipart/form-data and stores it on the server.\n\n"
        "**Validation Rules:**\n"
        "- File must be provided.\n"
        "- File extension must strictly be `.csv`.\n"
        "- File content must not be empty (0 bytes).\n"
        "- Other file formats (.txt, .pdf, .xlsx, .json) are rejected with 400 Bad Request.\n\n"
        "*Note: This endpoint performs storage and file-level integrity checks only; "
        "parsing and threat correlation occur in subsequent pipeline stages.*"
    ),
    responses={
        201: {
            "description": "File successfully uploaded and stored",
            "model": UploadResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "File uploaded successfully",
                        "file_name": "alerts_20260913_153001.csv",
                        "file_path": "uploads/alerts_20260913_153001.csv",
                    }
                }
            },
        },
        400: {
            "description": "Validation failed (invalid file type, empty file, or missing file)",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_extension": {
                            "summary": "Non-CSV file uploaded",
                            "value": {
                                "success": False,
                                "message": "Only CSV files are allowed",
                            },
                        },
                        "empty_file": {
                            "summary": "Empty file uploaded",
                            "value": {
                                "success": False,
                                "message": "Uploaded file is empty",
                            },
                        },
                    }
                }
            },
        },
        500: {
            "description": "Internal server or disk error during upload processing",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "message": "An unexpected error occurred while saving the file",
                    }
                }
            },
        },
    },
)
async def upload_alerts_csv(
    file: UploadFile = File(
        ...,
        description="CSV file containing raw security alerts (e.g. SIEM, satellite, sensor logs)",
    ),
):
    """
    Handle CSV upload: validates file integrity, extension, and delegates persistence to FileStorageService.
    """
    logger.info("Upload request received")

    # Guard: Missing file object or filename
    if not file or not file.filename:
        logger.warning("Upload failed: No file was attached to the request")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                message="Only CSV files are allowed",
            ).model_dump(),
        )

    try:
        file_name, file_path = await storage_service.save_file(file)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=UploadResponse(
                success=True,
                message="File uploaded successfully",
                file_name=file_name,
                file_path=file_path,
            ).model_dump(),
        )

    except StorageValidationError as val_err:
        logger.warning(f"Validation failure during upload: {val_err.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                message=val_err.message,
            ).model_dump(),
        )

    except Exception as exc:
        logger.error(f"Unexpected error during upload processing: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                message="An unexpected error occurred while saving the file",
            ).model_dump(),
        )


@router.post(
    "/upload/ingest",
    response_model=IngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload, Parse and Ingest Alerts CSV into Database",
    description=(
        "Accepts a raw security alert CSV file, verifies formatting, saves file to disk, "
        "parses alerts via CSVParser, and bulk inserts them into PostgreSQL alerts table."
    ),
)
async def upload_and_ingest_alerts(
    file: UploadFile = File(..., description="CSV file with columns: timestamp, src_ip, dst_ip, event, severity"),
    current_user: UserDB = Depends(get_current_user_obj),
    db: Session = Depends(get_db),
):
    """
    End-to-end ingestion scoped to the authenticated user:
    1. Disk storage
    2. CSV parsing and validation
    3. PostgreSQL storage in uploads and alerts tables with user_id
    4. Auto-correlate, MITRE map, and risk score for this user's data
    """
    if not file or not file.filename:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                success=False,
                message="Only CSV files are allowed",
            ).model_dump(),
        )

    try:
        # 1. Save file to disk
        file_name, file_path = await storage_service.save_file(file)

        # 2. Read saved file content and parse
        full_path = BASE_DIR / file_path
        with open(full_path, "r", encoding="utf-8") as f:
            parse_result = csv_parser.parse(f)

        parsed_alerts = parse_result.get("alerts", [])
        if not parsed_alerts:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(
                    success=False,
                    message="CSV contains no valid alert rows",
                ).model_dump(),
            )

        # 3. Create upload record in DB with user_id
        alert_repo = AlertRepository(db)
        upload_rec = alert_repo.create_upload(
            file_name=file_name,
            file_path=file_path,
            user_id=current_user.id,
        )

        # 4. Convert schemas.alert.Alert to database.models.Alert with user_id
        orm_alerts = []
        for a in parsed_alerts:
            sev = a.severity.value if hasattr(a.severity, "value") else str(a.severity)
            orm_alerts.append(
                AlertDB(
                    id=uuid.uuid4(),
                    user_id=current_user.id,
                    upload_id=upload_rec.id,
                    timestamp=a.timestamp,
                    src_ip=a.src_ip,
                    dst_ip=a.dst_ip,
                    event=a.event,
                    severity=sev,
                )
            )

        # 5. Bulk insert alerts with user_id
        count = alert_repo.bulk_insert_alerts(
            upload_id=upload_rec.id,
            alerts=orm_alerts,
            user_id=current_user.id,
        )
        logger.info("Successfully ingested %d alerts for user %s from file %s", count, current_user.id, file_name)

        # 6. Trigger automated correlation, MITRE mapping, and risk scoring pipeline scoped to current_user
        chains_count = 0
        mitre_count = 0
        scored_count = 0
        try:
            from services.alert_correlation import AlertCorrelationEngine
            from services.mitre_mapping import MitreMappingService
            from services.risk_scoring import RiskScoringEngine

            corr_engine = AlertCorrelationEngine(db=db)
            corr_result = corr_engine.correlate(user_id=current_user.id, persist=True)
            chains_count = len(corr_result.chains)

            mitre_service = MitreMappingService(db=db)
            mitre_res = mitre_service.map_all_chains(user_id=current_user.id)
            mitre_count = mitre_res.total_techniques

            risk_engine = RiskScoringEngine(db=db)
            risk_scores = risk_engine.score_all_chains(user_id=current_user.id)
            scored_count = len(risk_scores)

            logger.info(
                f"Auto-pipeline executed for user {current_user.id}: {chains_count} chains correlated, "
                f"{mitre_count} MITRE techniques mapped, {scored_count} risk-scored"
            )
        except Exception as pipe_err:
            logger.warning(f"Correlation pipeline post-ingest warning: {pipe_err}")

        # Clear cached aggregations so all pages receive fresh ingested telemetry
        try:
            from services.cache_service import cache
            cache.clear()
        except Exception:
            pass

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=IngestResponse(
                success=True,
                message=f"Successfully ingested {count} alerts and correlated {chains_count} attack chains",
                upload_id=str(upload_rec.id),
                file_name=file_name,
                alerts_ingested=count,
                chains_correlated=chains_count,
                mitre_mapped=mitre_count,
                risk_scored=scored_count,
            ).model_dump(),
        )

    except StorageValidationError as val_err:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, message=val_err.message).model_dump(),
        )
    except CSVParserError as parse_err:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(success=False, message=str(parse_err)).model_dump(),
        )
    except Exception as exc:
        logger.error(f"Error during alert ingestion: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(success=False, message=f"Ingestion failed: {str(exc)}").model_dump(),
        )


