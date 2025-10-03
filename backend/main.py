import os
import sys
import time
import threading
from dotenv import load_dotenv

# Add parent directory to path to find backend module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from backend directory
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from backend.config.settings import settings
from backend.ingestion.video_processor import VideoProcessor
from backend.ingestion.sensor_simulator import SensorSimulator
from backend.ingestion.kafka_producer import get_producer
from backend.agents.camera_agent import get_camera_manager
from backend.agents.sensor_agent import get_sensor_agent
from backend.agents.orchestrator_agent import get_orchestrator
from backend.utils.logger import get_logger
import uvicorn

logger = get_logger(__name__)

class ThreatDetectionSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.orchestrator = None
        self.camera_manager = None
        self.sensor_agent = None
        self.producer = None
        self.video_threads = []
        self.sensor_threads = []
        self.running = False
        
    def initialize(self):
        """Initialize all components"""
        logger.info("=" * 60)
        logger.info("🏠 AGENTIC HOME THREAT DETECTION SYSTEM")
        logger.info("=" * 60)
        
        # Initialize orchestrator
        logger.info("Initializing Orchestrator Agent...")
        self.orchestrator = get_orchestrator()
        self.orchestrator.start()
        
        # Initialize camera agents
        logger.info("Initializing Camera Agents...")
        self.camera_manager = get_camera_manager(alert_callback=self.orchestrator.receive_alert)
        self.camera_manager.start_all_cameras()
        
        # Initialize sensor agent
        logger.info("Initializing Sensor Agent...")
        self.sensor_agent = get_sensor_agent(alert_callback=self.orchestrator.receive_alert)
        self.sensor_agent.start()
        
        # Initialize producer
        logger.info("Initializing Kafka Producer...")
        self.producer = get_producer()
        
        logger.info("✅ All components initialized successfully")
    
    def start_video_ingestion(self):
        """Start ingesting video frames from sample videos"""
        logger.info("Starting video ingestion...")
        
        video_configs = [
            {"camera_id": 1, "video_file": "camera1_normal.mp4"},
            {"camera_id": 2, "video_file": "camera2_weapon.mp4"},
            {"camera_id": 3, "video_file": "camera3_fall.mp4"},
            {"camera_id": 4, "video_file": "camera4_fire.mp4"},
            {"camera_id": 5, "video_file": "camera5_crowd.mp4"}
        ]
        
        for config in video_configs:
            thread = threading.Thread(
                target=self._ingest_video,
                args=(config['camera_id'], config['video_file']),
                daemon=True
            )
            thread.start()
            self.video_threads.append(thread)
            time.sleep(0.5)  # Stagger starts
        
        logger.info(f"✅ Started {len(self.video_threads)} video ingestion threads")
    
    def start_sensor_simulation(self):
        """Start simulating sensor data"""
        logger.info("Starting sensor simulation...")
        
        # Start background thread for sensor simulation
        thread = threading.Thread(target=self._simulate_sensors, daemon=True)
        thread.start()
        self.sensor_threads.append(thread)
        
        logger.info("✅ Sensor simulation started")
    
    def _ingest_video(self, camera_id: int, video_file: str):
        """Ingest frames from a video file"""
        video_path = os.path.join(settings.video_dir, video_file)
        
        if not os.path.exists(video_path):
            logger.warning(f"Video file not found: {video_path}")
            logger.info(f"Creating placeholder video path for camera {camera_id}")
            return
        
        try:
            processor = VideoProcessor(camera_id, video_path)
            
            for frame_data in processor.extract_frames():
                if not self.running:
                    break
                
                # Send frame to Kafka
                self.producer.send_camera_frame(camera_id, frame_data)
                
                # Simulate frame interval
                time.sleep(settings.frame_interval_seconds / settings.simulation_speed)
            
            logger.info(f"Camera {camera_id} video ingestion completed")
            
        except Exception as e:
            logger.error(f"Video ingestion error for camera {camera_id}: {e}")
    
    def _simulate_sensors(self):
        """Simulate sensor data generation"""
        simulator = SensorSimulator()
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                
                # Simulate different scenarios over time
                if iteration % 20 == 5:
                    # Trigger elevated heart rate scenario
                    data = simulator.generate_smartwatch_data("elevated_heart_rate")
                    self.producer.send_sensor_data(data)
                    logger.info("Simulated: Elevated heart rate")
                
                elif iteration % 20 == 10:
                    # Trigger fall detection
                    data = simulator.generate_accelerometer_data("fall")
                    self.producer.send_sensor_data(data)
                    logger.info("Simulated: Fall detected")
                
                elif iteration % 20 == 15:
                    # Trigger scream detection
                    data = simulator.generate_microphone_data("scream")
                    self.producer.send_sensor_data(data)
                    logger.info("Simulated: Scream detected")
                
                else:
                    # Normal data
                    data = simulator.generate_smartwatch_data("normal")
                    self.producer.send_sensor_data(data)
                
                time.sleep(5)  # Send sensor data every 5 seconds
                
            except Exception as e:
                logger.error(f"Sensor simulation error: {e}")
                time.sleep(5)
    
    def start(self):
        """Start the entire system"""
        self.running = True
        
        logger.info("=" * 60)
        logger.info("🚀 STARTING THREAT DETECTION SYSTEM")
        logger.info("=" * 60)
        
        # Initialize components
        self.initialize()
        
        # Wait a bit for Kafka consumers to be ready
        logger.info("Waiting for Kafka consumers to initialize...")
        time.sleep(3)
        
        # Start data ingestion
        if settings.demo_mode:
            self.start_video_ingestion()
            self.start_sensor_simulation()
        
        logger.info("=" * 60)
        logger.info("✅ SYSTEM FULLY OPERATIONAL")
        logger.info("=" * 60)
    
    def stop(self):
        """Stop the system"""
        logger.info("Stopping Threat Detection System...")
        self.running = False
        
        if self.sensor_agent:
            self.sensor_agent.stop()
        
        if self.camera_manager:
            self.camera_manager.stop_all_cameras()
        
        if self.orchestrator:
            self.orchestrator.stop()
        
        if self.producer:
            self.producer.close()
        
        logger.info("✅ System stopped")

def main():
    """Main entry point"""
    
    # Create system instance
    system = ThreatDetectionSystem()
    
    try:
        # Start the system
        system.start()
        
        # Start API server in main thread
        logger.info("Starting API Server...")
        uvicorn.run(
            "backend.api.server:app",
            host=settings.api_host,
            port=settings.api_port,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"System error: {e}")
    finally:
        system.stop()

if __name__ == "__main__":
    main()