import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Google AI Studio
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Pinecone
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index_name: str = "threat-events"
    
    # Kafka
    kafka_bootstrap_servers: List[str] = ["localhost:9092"]
    kafka_camera_topic_prefix: str = "camera"
    kafka_sensor_topic: str = "sensors"
    kafka_alert_topic: str = "alerts"
    
    # Camera Configuration
    num_cameras: int = 5
    frame_interval_seconds: int = 5  # Extract frame every 5 seconds
    
    # API Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # Demo Settings
    demo_mode: bool = True
    simulation_speed: float = 1.0  # Multiplier for playback speed
    
    # Video Paths
    video_dir: str = "sample_videos"
    
    # Threat Detection Thresholds
    weapon_confidence_threshold: float = 0.7
    unknown_person_confidence_threshold: float = 0.6
    heart_rate_spike_threshold: int = 120  # bpm
    heart_rate_drop_threshold: int = 40  # bpm
    spo2_threshold: int = 90  # %
    blood_pressure_drop_threshold: int = 25  # mmHg
    
    # Alert Timeouts
    vitals_check_timeout_seconds: int = 300  # 5 minutes
    camera_restart_timeout_seconds: int = 60  # 1 minute
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()

# Kafka Topics Configuration
def get_camera_topic(camera_id: int) -> str:
    """Get Kafka topic name for a specific camera"""
    return f"{settings.kafka_camera_topic_prefix}-{camera_id}"

def get_all_camera_topics() -> List[str]:
    """Get all camera topic names"""
    return [get_camera_topic(i) for i in range(1, settings.num_cameras + 1)]