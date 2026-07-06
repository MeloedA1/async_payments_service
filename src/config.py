import logging
from zoneinfo import ZoneInfo

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')
    # -------- main settings ----------
    service_name: str = 'async_payments_service'
    date_format: str = '%Y-%m-%d'
    datetime_format: str = '%Y-%m-%d %H:%M:%S %z'
    local_tz: str = 'Europe/Moscow'

    # ------ db settings ---------
    db_name: str = ''
    db_host: str = ''
    db_port: int = 5435
    db_user: str = ''
    db_password: str = ''

    rabbitmq_url: str = ''

    api_key: str = ''

    @computed_field()
    @property
    def service_tz(self) -> ZoneInfo:
        return ZoneInfo(self.local_tz)


settings = Settings()
