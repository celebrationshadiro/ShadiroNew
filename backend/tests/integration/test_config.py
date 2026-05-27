from dataclasses import dataclass
import os


@dataclass(frozen=True)
class IntegrationTestConfig:
    mongo_url: str
    db_name: str


def get_test_config() -> IntegrationTestConfig:
    return IntegrationTestConfig(
        mongo_url=os.getenv("TEST_MONGO_URL", "mongodb://127.0.0.1:27017"),
        db_name=os.getenv("TEST_DB_NAME", "event_app_integration_test"),
    )
