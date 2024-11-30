from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, Field

Base = declarative_base()

# SQLAlchemy ORM Model
class SalesProductPattern(Base):
    __tablename__ = "sales_product_paterns"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    product = Column(String(100), nullable=False)
    division_code = Column(String(10), nullable=False, default="0")

    # Unique constraint
    __table_args__ = (UniqueConstraint("product", "division_code", name="UK_Prd_Div"),)


# Pydantic Model for Validation
class SalesProductPatternModel(BaseModel):
    id: int = Field(..., alias="id", ge=1)
    product: str = Field(..., max_length=100)
    division_code: str = Field(default="0", max_length=10)

    class Config:
        orm_mode = True
