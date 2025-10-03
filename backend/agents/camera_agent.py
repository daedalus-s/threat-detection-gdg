from kafka import KafkaConsumer
import json
from typing import Dict, Any, Callable
import threading
from backend.config.settings import settings, get_camera_topic
from backend.inference.vision_detector import get_detector
from backend.inference.threat_analyzer import get_analyzer
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class CameraAgent:
    """
    Agent responsible for processing a single camera feed
    Consumes frames from Kafka, runs vision detection, and reports threats
    """
    
    def __init__(self, camera_id: int, alert_callback: Callable = None):
        self.camera_id = camera_id
        self.topic = get_camera_topic(camera_id)
        self.detector = get_detector()
        self.analyzer = get_analyzer()
        self.alert_callback = alert_callback
        self.consumer = None
        self.running = False
        self.thread = None
        
        logger.info(f"Camera Agent {camera_id} initialized")
    
    def start(self):
        """Start consuming and processing frames"""
        if self.running:
            logger.warning(f"Camera Agent {self.camera_id} already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._consume_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera Agent {self.camera_id} started")
    
    def stop(self):
        """Stop the agent"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        if self.consumer:
            self.consumer.close()
        logger.info(f"Camera Agent {self.camera_id} stopped")
    
    def _consume_loop(self):
        """Main consumption loop"""
        try:
            # Create consumer for this camera's topic
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',  # Start from latest for demo
                enable_auto_commit=True,
                group_id=f'camera_agent_{self.camera_id}'
            )
            
            logger.info(f"Camera Agent {self.camera_id} consuming from {self.topic}")
            
            for message in self.consumer:
                if not self.running:
                    break
                
                frame_data = message.value
                self._process_frame(frame_data)
                
        except Exception as e:
            logger.error(f"Camera Agent {self.camera_id} error: {e}")
        finally:
            if self.consumer:
                self.consumer.close()
    
    def _process_frame(self, frame_data: Dict[str, Any]):
        """Process a single frame"""
        try:
            logger.debug(f"Camera {self.camera_id} processing frame {frame_data.get('frame_number', 0)}")
            
            # Extract frame image data
            frame_base64 = frame_data.get('frame_data')
            
            if not frame_base64:
                logger.warning(f"Camera {self.camera_id}: No frame data")
                return
            
            # Run vision detection
            vision_result = self.detector.analyze_frame(frame_base64, self.camera_id)
            
            # Analyze for threats
            alert = self.analyzer.analyze_vision_threat(vision_result)
            
            if alert:
                logger.warning(
                    f"Camera {self.camera_id} THREAT DETECTED: "
                    f"{alert['alert_type']} - Severity: {alert['severity']}"
                )
                
                # Add frame metadata to alert
                alert['frame_number'] = frame_data.get('frame_number')
                alert['frame_timestamp'] = frame_data.get('timestamp')
                
                # Callback to orchestrator
                if self.alert_callback:
                    self.alert_callback(alert)
            else:
                logger.debug(f"Camera {self.camera_id}: No threats detected")
                
        except Exception as e:
            logger.error(f"Camera {self.camera_id} frame processing error: {e}")

class CameraAgentManager:
    """Manage multiple camera agents"""
    
    def __init__(self, alert_callback: Callable = None):
        self.agents = {}
        self.alert_callback = alert_callback
    
    def start_all_cameras(self):
        """Start agents for all cameras"""
        for camera_id in range(1, settings.num_cameras + 1):
            agent = CameraAgent(camera_id, alert_callback=self.alert_callback)
            agent.start()
            self.agents[camera_id] = agent
        
        logger.info(f"Started {len(self.agents)} camera agents")
    
    def stop_all_cameras(self):
        """Stop all camera agents"""
        for agent in self.agents.values():
            agent.stop()
        logger.info("All camera agents stopped")
    
    def get_agent(self, camera_id: int) -> CameraAgent:
        """Get specific camera agent"""
        return self.agents.get(camera_id)

# Global manager instance
_manager_instance = None

def get_camera_manager(alert_callback: Callable = None) -> CameraAgentManager:
    """Get or create global camera agent manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = CameraAgentManager(alert_callback=alert_callback)
    return _manager_instance