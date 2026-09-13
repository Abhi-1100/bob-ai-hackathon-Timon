"""
Pydantic V2 schemas for the File Upload module.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UploadResponse(BaseModel):
    """Schema for successful CSV file upload responses."""
    success: bool = Field(default=True, description="Indicates whether the upload succeeded")
    message: str = Field(default="File uploaded successfully", description="Status message")
    file_name: str = Field(..., description="Unique generated filename saved on disk")
    file_path: str = Field(..., description="Relative path where the file is stored")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "message": "File uploaded successfully",
                "file_name": "alerts_20260913_153001.csv",
                "file_path": "uploads/alerts_20260913_153001.csv",
            }
        }
    )


class ErrorResponse(BaseModel):
    """Schema for failed upload responses (validation or server errors)."""
    success: bool = Field(default=False, description="Indicates whether the upload succeeded")
    message: str = Field(..., description="Error description explaining the failure")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "message": "Only CSV files are allowed",
            }
        }
    )


class IngestResponse(BaseModel):
    """Schema for successful CSV alert upload, parsing, and database persistence."""
    success: bool = Field(default=True, description="Indicates whether ingestion succeeded")
    message: str = Field(default="Alerts successfully ingested into database", description="Status message")
    upload_id: str = Field(..., description="Database UUID for the upload record")
    file_name: str = Field(..., description="Uploaded filename")
    alerts_ingested: int = Field(..., description="Total number of alert rows inserted into database")
    chains_correlated: Optional[int] = Field(default=0, description="Number of attack chains produced")
    mitre_mapped: Optional[int] = Field(default=0, description="Total MITRE techniques mapped")
    risk_scored: Optional[int] = Field(default=0, description="Number of chains evaluated for risk")

