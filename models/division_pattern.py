from sqlalchemy import Column, String, PrimaryKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

# SQLAlchemy ORM Model
class DivisionPattern(Base):
    __tablename__ = "division_patterns"

    code = Column(String(9), nullable=False)
    pattern = Column(String(255), nullable=False)

    # Define composite primary key
    __table_args__ = (
        PrimaryKeyConstraint("code", "pattern", name="PK_Code_Pattern"),
    )

# Pydantic Schema
class DivisionPatternSchema(BaseModel):
    code: str = Field(..., max_length=9)
    pattern: str = Field(..., max_length=255)

    class Config:
        orm_mode = True
