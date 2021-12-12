
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

"""
pool_size= – the number of connections to keep open inside the connection pool. 
    This used with QueuePool as well as SingletonThreadPool. 
    With QueuePool, a pool_size setting of 0 indicates no limit; 
    to disable pooling, set poolclass to NullPool instead.


max_overflow – the number of connections to allow in connection pool “overflow”, 
    that is connections that can be opened above and beyond the pool_size setting, 
    which defaults to five. this is only used with QueuePool.
"""

Base = declarative_base()
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://dev:dev@localhost:3306/todoapp_routing?charset=utf8mb4"
engine = create_engine(SQLALCHEMY_DATABASE_URL,
                       echo=True,
                       pool_size=20,
                       echo_pool=True,
                       max_overflow=10)
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


