"""Database models for transcoding service.

Requirements: 10.1, 10.2, 10.5
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TranscodeStatus(str, Enum):
    """Status of a transcoding job."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Resolution(str, Enum):
    """Supported output resolutions.
    
    Requirements: 10.1 - Support 720p, 1080p, 2K, 4K output.
    """
    RES_720P = "720p"
    RES_1080P = "1080p"
    RES_2K = "2k"
    RES_4K = "4k"


# Resolution dimensions mapping
RESOLUTION_DIMENSIONS = {
    Resolution.RES_720P: (1280, 720),
    Resolution.RES_1080P: (1920, 1080),
    Resolution.RES_2K: (2560, 1440),
    Resolution.RES_4K: (3840, 2160),
}


class LatencyMode(str, Enum):
    """Latency mode for streaming optimization.
    
    Requirements: 10.4 - Optimize for low latency mode.
    """
    NORMAL = "normal"
    LOW = "low"
    ULTRA_LOW = "ultra_low"


class TranscodeJob(Base):
    """Model for transcoding jobs.
    
    Requirements: 10.1, 10.2
    """
    __tablename__ = "transcode_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Source file
    source_file_path = Column(String(1024), nullable=False)
    source_file_size = Column(Integer, nullable=True)  # bytes
    source_duration = Column(Float, nullable=True)  # seconds
    
    # Target settings
    target_resolution = Column(SQLEnum(Resolution), nullable=False)
    target_bitrate = Column(Integer, nullable=True)  # bps
    latency_mode = Column(SQLEnum(LatencyMode), default=LatencyMode.NORMAL)
    enable_abr = Column(Boolean, default=False)  # Adaptive bitrate
    
    # Output
    output_file_path = Column(String(1024), nullable=True)
    output_file_size = Column(Integer, nullable=True)  # bytes
    output_width = Column(Integer, nullable=True)
    output_height = Column(Integer, nullable=True)
    cdn_url = Column(String(1024), nullable=True)
    
    # Status tracking
    status = Column(SQLEnum(TranscodeStatus), default=TranscodeStatus.QUEUED)
    progress = Column(Float, default=0.0)  # 0-100
    error_message = Column(Text, nullable=True)
    
    # Worker assignment
    assigned_worker_id = Column(String(255), nullable=True)
    worker_load_at_assignment = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    account_id = Column(UUID(as_uuid=True), ForeignKey("youtube_accounts.id"), nullable=True)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id"), nullable=True)
    live_event_id = Column(UUID(as_uuid=True), ForeignKey("live_events.id"), nullable=True)

    def __repr__(self) -> str:
        return f"<TranscodeJob {self.id} - {self.target_resolution.value} - {self.status.value}>"


class TranscodeWorker(Base):
    """Model for FFmpeg worker nodes.
    
    Requirements: 10.2 - Distribute to FFmpeg worker cluster based on load.
    """
    __tablename__ = "transcode_workers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Worker identification
    hostname = Column(String(255), nullable=False, unique=True)
    ip_address = Column(String(45), nullable=True)
    
    # Capacity and load
    max_concurrent_jobs = Column(Integer, default=2)
    current_jobs = Column(Integer, default=0)
    current_load = Column(Float, default=0.0)  # 0-100 percentage
    
    # Status
    is_healthy = Column(Boolean, default=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    
    # Capabilities
    supports_4k = Column(Boolean, default=True)
    supports_hardware_encoding = Column(Boolean, default=False)
    gpu_type = Column(String(100), nullable=True)
    
    # Timestamps
    registered_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TranscodeWorker {self.hostname} - load: {self.current_load}%>"

    def is_available(self) -> bool:
        """Check if worker can accept new jobs."""
        return self.is_healthy and self.current_jobs < self.max_concurrent_jobs


class TranscodedOutput(Base):
    """Model for storing transcoded output metadata.
    
    Requirements: 10.5 - Store transcoded output in CDN-backed storage.
    """
    __tablename__ = "transcoded_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Reference to job
    transcode_job_id = Column(UUID(as_uuid=True), ForeignKey("transcode_jobs.id"), nullable=False)
    
    # Output details
    resolution = Column(SQLEnum(Resolution), nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    bitrate = Column(Integer, nullable=False)  # bps
    file_size = Column(Integer, nullable=False)  # bytes
    duration = Column(Float, nullable=False)  # seconds
    
    # Storage
    storage_bucket = Column(String(255), nullable=False)
    storage_key = Column(String(1024), nullable=False)
    cdn_url = Column(String(1024), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<TranscodedOutput {self.id} - {self.resolution.value}>"
