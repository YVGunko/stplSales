from sqlalchemy import Column, Integer, String, Date, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field
from datetime import date

Base = declarative_base()

# SQLAlchemy ORM Model
class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    product = Column(String(100), nullable=False)
    total = Column(Integer, nullable=False)
    date_of_change = Column(Date, nullable=False)
    division_code = Column(String(10), nullable=False, default="0")

    # Unique constraint
    __table_args__ = (
        UniqueConstraint("product", "date_of_change", "division_code", name="UK_Prd_Dat_Div"),
    )

# Pydantic Schema
class SaleSchema(BaseModel):
    id: int = Field(..., ge=1)
    product: str = Field(..., max_length=100)
    total: int = Field(..., ge=0)
    date_of_change: date = Field(...)
    division_code: str = Field(default="0", max_length=10)

    class Config:
        orm_mode = True
