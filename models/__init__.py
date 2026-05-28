import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from ..core.database import Base

VALID_ACTION_TYPES = [
    "http_request", "database_query", "send_email", "transform_data", "condition", "loop", "delay",
    "google_sheets_read", "google_sheets_write", "google_drive_upload", "google_docs_create", "google_calendar_event",
    "ms365_send_email", "ms365_teams_meeting", "ms365_onedrive_upload", "ms365_excel_write",
    "slack_send_message", "telegram_send_message", "discord_webhook", "whatsapp_business",
    "hubspot_create_contact", "hubspot_update_deal", "salesforce_create_lead", "mailchimp_add_subscriber", "sendgrid_send_email",
    "s3_upload", "s3_download", "ftp_upload", "local_file_read", "local_file_write", "pdf_generate", "excel_generate",
    "web_scrape", "rss_feed", "webhook_send",
    "llm_text_generate", "llm_summarize", "llm_classify", "ocr_image",
    "twitter_post", "linkedin_post",
    "postgres_query", "mysql_query", "mongo_find",
    "compress_gzip", "decompress_gzip", "encrypt_aes", "decrypt_aes", "wait", "stop", "throw_error"
]

class SoftDeleteMixin:
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    @classmethod
    def not_deleted(cls):
        return cls.deleted_at.is_(None)

class Organization(Base):
    __tablename__ = "organizations"

    org_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    plan = Column(String(20), default="free")
    max_workflows = Column(Integer, default=10)
    max_executions_per_month = Column(Integer, default=1000)
    features = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    role = Column(String(50), default="viewer")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    organization = relationship("Organization")

class Workflow(SoftDeleteMixin, Base):
    __tablename__ = "workflows"

    workflow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    description = Column(String(1000))
    trigger_type = Column(String(50))
    trigger_config = Column(JSONB, default={})
    start_node = Column(UUID(as_uuid=True))
    status = Column(String(20), default="pending")
    max_iterations = Column(Integer, default=100)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('org_id', 'name', name='uq_workflow_org_name'),
    )

class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"

    node_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.workflow_id", ondelete="CASCADE"))
    action_type = Column(String(50), nullable=False)
    config = Column(JSONB, default={})
    next_node = Column(UUID(as_uuid=True))
    on_error = Column(UUID(as_uuid=True))
    retry_count = Column(Integer, default=3)
    timeout_seconds = Column(Integer, default=30)
    temp_id = Column(String(100))
    position_x = Column(Integer)
    position_y = Column(Integer)

    workflow = relationship("Workflow", back_populates="nodes")

    __table_args__ = (
        CheckConstraint(f"action_type IN ({','.join(repr(t) for t in VALID_ACTION_TYPES)})", name="ck_node_action_type"),
    )

class WorkflowExecution(Base):
    __tablename__ = "workflow_executions"

    execution_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.workflow_id", ondelete="SET NULL"))
    status = Column(String(20))
    input_data = Column(JSONB)
    output_data = Column(JSONB)
    node_outputs = Column(JSONB)
    errors = Column(JSONB)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    depth = Column(Integer, default=0)
    triggered_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))

    __table_args__ = (
        Index('ix_wf_exec_workflow_started', 'workflow_id', 'started_at'),
        Index('ix_wf_exec_status', 'status'),
    )

class APIKey(Base):
    __tablename__ = "api_keys"

    key_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    key_hash = Column(String(64), unique=True, nullable=False)
    encrypted_key = Column(String(500))
    scopes = Column(JSONB, default=[])
    expires_at = Column(DateTime(timezone=True))
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))