from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    task = Column(Text)
    deadline = Column(String)
    status = Column(String, default="PENDING")  # PENDING / APPROVED / REJECTED

Base.metadata.create_all(bind=engine)