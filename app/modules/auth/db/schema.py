import uuid
from datetime import datetime, timezone
from sqlalchemy import (Column, String, UUID, Boolean, DateTime,
                        ForeignKey, Integer, Text, JSON, Enum, Date)
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String, unique=True)
    full_name = Column(String)
    email = Column(String, unique=True, index=True)
    mobile_number = Column(String)
    department = Column(String)
    designation = Column(String)
    hashed_password = Column(String)
    profile_picture_url = Column(String, nullable=True)
    account_status = Column(Enum('Active', 'Inactive', 'Locked', 'Pending', name='user_status_enum'), default='Pending')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)
    last_password_change = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    password_expiry_date = Column(Date, nullable=True)
    role = Column(String(50), nullable=False, default='employee') # 'super_admin', 'dept_admin', 'employee'
    is_active = Column(Boolean, default=True) # Retained for simple active check, complements account_status

class ModuleAccess(Base):
    __tablename__ = "module_access"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    module_name = Column(String)
    access_type = Column(Enum('Default', 'Admin-Granted', name='access_type_enum'))
    granted_by_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    valid_from = Column(Date, nullable=True)
    valid_until = Column(Date, nullable=True)
    access_reason = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

class LoginHistory(Base):
    __tablename__ = "login_history"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    login_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String)
    device_type = Column(String)
    browser = Column(String)
    location = Column(String, nullable=True)
    status = Column(Enum('Success', 'Failed', name='login_status_enum'))
    failure_reason = Column(String, nullable=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=True)
    action_type = Column(String)
    action_description = Column(Text)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ip_address = Column(String)
    device_info = Column(JSON)
    status = Column(Enum('Success', 'Failed', 'Partial', name='audit_status_enum'))
    additional_data = Column(JSON)

