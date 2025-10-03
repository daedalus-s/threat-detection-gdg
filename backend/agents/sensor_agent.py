from kafka import KafkaConsumer
import json
from typing import Dict, Any, Callable
import threading
from backend.config.settings import settings
from backend.inference.threat_analyzer import get_analyzer
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class SensorAgent:
    """
    Agent responsible for processing sensor data (smartwatch, accelerometer, microphone, smoke detector)
    Consumes sensor data from Kafka and reports threats
    """
    
    def __init__(self, alert_callback: Callable = None):
        self.topic = settings.kafka_sensor_topic
        self.analyzer = get_analyzer()
        self.alert_callback = alert_callback
        self.consumer = None
        self.running = False
        self.thread = None
        
        logger.info("Sensor Agent initialized")
    
    def start(self):
        """Start consuming and processing sensor data"""
        if self.running:
            logger.warning("Sensor Agent already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()
        logger.info("Sensor Agent started")
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.consumer:
            self.consumer.close()
        logger.info("Sensor Agent stopped")
    
    def _consume_loop(self):
        """Main consumption loop"""
        try:
            # Create consumer for sensor topic
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='sensor_agent'
            )
            
            logger.info(f"Sensor Agent consuming from {self.topic}")
            
            for message in self.consumer:
                if not self.running:
                    break
                
                sensor_data = message.value
                self._process_sensor_data(sensor_data)
                
        except Exception as e:
            logger.error(f"Sensor Agent error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
    
    def _process_sensor_data(self, sensor_data: Dict[str, Any]):
        """Process sensor data"""
        try:
            device_type = sensor_data.get('device_type', 'unknown')
            device_id = sensor_data.get('device_id', 'unknown')
            
            logger.debug(f"Processing {device_type} data from {device_id}")
            
            # Analyze for threats
            alert = self.analyzer.analyze_sensor_threat(sensor_data)
            
            if alert:
                logger.warning(
                    f"Sensor THREAT DETECTED: "
                    f"{alert['alert_type']} - Severity: {alert['severity']}"
                )
                
                # Callback to orchestrator
                if self.alert_callback:
                    self.alert_callback(alert)
            else:
                logger.debug(f"{device_type}: No threats detected")
                
        except Exception as e:
            logger.error(f"Sensor data processing error: {e}")

# Global sensor agent instance
_sensor_agent_instance = None

def get_sensor_agent(alert_callback: Callable = None) -> SensorAgent:
    """Get or create global sensor agent"""
    global _sensor_agent_instance
    if _sensor_agent_instance is None:
        _sensor_agent_instance = SensorAgent(alert_callback=alert_callback)
    return _sensor_agent_instance