from sqlalchemy import Column, String, UUID, Boolean
import uuid
from app.db.database import Base 

class User(Base):
    """
    SQLAlchemy model for a User.
    Maps to the 'users' table in PostgreSQL.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    department = Column(String(100))
    role = Column(String(50), nullable=False, default='employee') # 'super_admin', 'dept_admin', 'employee'
    is_active = Column(Boolean, default=True)

    # STUB: Add relationships here, e.g.:
    # documents = relationship("Document", back_populates="uploader")
    # cases_assigned = relationship("LegalCase", back_populates="assignee")

