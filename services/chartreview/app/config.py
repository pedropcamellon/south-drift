from folium.core.chart_review import CHARTREVIEW_TASK_QUEUE, CHARTREVIEW_WORKFLOW_NAME
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    chartreview_task_queue: str = CHARTREVIEW_TASK_QUEUE
    chartreview_workflow_name: str = CHARTREVIEW_WORKFLOW_NAME
    ai_service_base_url: str
    ai_provider_name: str = "local"
    ai_model_name: str = "mediphi-clinical"
    chartreview_backend_url: str
    chartreview_internal_token: str
    log_level: str = "INFO"
    request_timeout_seconds: float = 600.0
    activity_start_to_close_timeout_seconds: int = 600
    activity_max_attempts: int = 2
    history_decision_max_tokens: int = 64
    review_max_tokens: int = 512

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
