import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

MYSQL_USER     = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_HOST     = os.getenv("MYSQL_HOST")
MYSQL_PORT     = os.getenv("MYSQL_PORT")
MYSQL_DB       = os.getenv("MYSQL_DB")

# How to obtain CA certificate for MySQL connection
# mkdir ~/.mysql
# curl -o ~/.mysql/root.crt https://storage.yandexcloud.net/cloud-certs/CA.pem
ssl_ca_path = os.path.expanduser("~/.mysql/root.crt")
assert os.path.isfile(ssl_ca_path), "MySQL CA certificate not found"

engine = create_engine(
    f"mysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?ssl_ca={ssl_ca_path}",
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Prime the connection pool to avoid first-request latency
with engine.connect() as connection:
    pass
