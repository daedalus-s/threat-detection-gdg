import json
from kafka import KafkaProducer
from kafka.errors import KafkaError
from typing import Dict, Any
import time
from backend.config.settings import settings, get_camera_topic
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class ThreatDetectionProducer:
    """Kafka producer for sending camera frames and sensor data"""
    
    def __init__(self):
        self.producer = None
        self._connect()
    
    def _connect(self, retries=5, delay=2):
        """Connect to Kafka with retry logic"""
        for attempt in range(retries):
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    max_request_size=10485760,  # 10MB for large frames
                    compression_type='gzip',  # Compress large payloads
                    acks='all',  # Wait for all replicas
                    retries=3
                )
                logger.info(f"Connected to Kafka at {settings.kafka_bootstrap_servers}")
                return
            except KafkaError as e:
                logger.warning(f"Kafka connection attempt {attempt + 1} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    logger.error("Failed to connect to Kafka after multiple attempts")
                    raise
    
    def send_camera_frame(self, camera_id: int, frame_data: Dict[str, Any]):
        """Send camera frame to camera-specific topic"""
        topic = get_camera_topic(camera_id)
        
        try:
            future = self.producer.send(topic, value=frame_data)
            # Wait for confirmation (optional, for demo reliability)
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"Frame sent to {topic} - "
                f"Partition: {record_metadata.partition}, "
                f"Offset: {record_metadata.offset}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send frame to {topic}: {e}")
            return False
    
    def send_sensor_data(self, sensor_data: Dict[str, Any]):
        """Send sensor data to sensors topic"""
        try:
            future = self.producer.send(settings.kafka_sensor_topic, value=sensor_data)
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"Sensor data sent to {settings.kafka_sensor_topic} - "
                f"Device: {sensor_data.get('device_id', 'unknown')}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send sensor data: {e}")
            return False
    
    def send_alert(self, alert_data: Dict[str, Any]):
        """Send alert to alerts topic"""
        try:
            future = self.producer.send(settings.kafka_alert_topic, value=alert_data)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Alert sent to {settings.kafka_alert_topic} - "
                f"Type: {alert_data.get('alert_type', 'unknown')}, "
                f"Severity: {alert_data.get('severity', 'unknown')}"
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return False
    
    def flush(self):
        """Flush any pending messages"""
        if self.producer:
            self.producer.flush()
            logger.debug("Producer flushed")
    
    def close(self):
        """Close the producer connection"""
        if self.producer:
            self.producer.close()
            logger.info("Kafka producer closed")

# Global producer instance
_producer_instance = None

def get_producer() -> ThreatDetectionProducer:
    """Get or create global producer instance"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = ThreatDetectionProducer()
    return _producer_instance