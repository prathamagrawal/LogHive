from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_db_host: str
    postgres_db_name: str
    postgres_db_user: str
    postgres_db_password: str
    postgres_db_port: str

    class Config:
        env_file = "../config.env"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_db_user}:"
            f"{self.postgres_db_password}@{self.postgres_db_host}:{self.postgres_db_port}/"
            f"{self.postgres_db_name}"
        )


settings = Settings()
