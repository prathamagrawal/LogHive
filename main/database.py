from main.settings import settings
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy import create_engine

engine = create_engine(settings.database_url)
Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
