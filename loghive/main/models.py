import enum
from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class LoggingDetails(Base):
    __tablename__ = "logging_details"
    __table_args__ = {"schema": "logs"}
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    service_name = Column(String, nullable=False)
    data = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, nullable=False)

    # 2nd migration
    information = Column(String, nullable=True)

    # 3rd Migration
