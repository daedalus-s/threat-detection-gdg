import cv2
import os
import base64
from datetime import datetime
from typing import Generator, Dict, Any
from PIL import Image
import io
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class VideoProcessor:
    """Process video files and extract frames at specified intervals"""
    
    def __init__(self, camera_id: int, video_path: str):
        self.camera_id = camera_id
        self.video_path = video_path
        self.frame_interval = settings.frame_interval_seconds
        self.simulation_speed = settings.simulation_speed
        
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")
    
    def extract_frames(self) -> Generator[Dict[str, Any], None, None]:
        """
        Extract frames from video at specified intervals
        
        Yields:
            Dictionary containing frame data, timestamp, and metadata
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            logger.error(f"Failed to open video: {self.video_path}")
            return
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        logger.info(f"Camera {self.camera_id}: Processing video - FPS: {fps}, Duration: {duration:.2f}s, Total Frames: {total_frames}")
        
        # Calculate frame skip based on interval and simulation speed
        frame_skip = int(fps * self.frame_interval / self.simulation_speed)
        frame_count = 0
        extracted_count = 0
        
        while True:
            ret, frame = cap.read()
            
            if not ret:
                logger.info(f"Camera {self.camera_id}: End of video reached. Extracted {extracted_count} frames.")
                break
            
            if frame_count % frame_skip == 0:
                # Convert frame to base64 for transmission
                frame_data = self._frame_to_base64(frame)
                
                timestamp = datetime.now()
                video_timestamp = frame_count / fps
                
                yield {
                    "camera_id": self.camera_id,
                    "frame_number": frame_count,
                    "video_timestamp": video_timestamp,
                    "timestamp": timestamp.isoformat(),
                    "frame_data": frame_data,
                    "resolution": {
                        "width": frame.shape[1],
                        "height": frame.shape[0]
                    }
                }
                
                extracted_count += 1
            
            frame_count += 1
        
        cap.release()
    
    def _frame_to_base64(self, frame) -> str:
        """Convert OpenCV frame to base64 encoded JPEG"""
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Convert to PIL Image
        pil_image = Image.fromarray(rgb_frame)
        
        # Save to bytes buffer
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        
        # Encode to base64
        base64_encoded = base64.b64encode(buffer.read()).decode('utf-8')
        
        return base64_encoded
    
    def get_frame_as_bytes(self, frame) -> bytes:
        """Convert frame to JPEG bytes"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_frame)
        
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        buffer.seek(0)
        
        return buffer.read()

def process_all_cameras():
    """Process all camera videos and yield frames"""
    video_files = {
        1: "camera1_normal.mp4",
        2: "camera2_weapon.mp4",
        3: "camera3_fall.mp4",
        4: "camera4_fire.mp4",
        5: "camera5_crowd.mp4"
    }
    
    processors = []
    for camera_id, video_file in video_files.items():
        video_path = os.path.join(settings.video_dir, video_file)
        if os.path.exists(video_path):
            processors.append(VideoProcessor(camera_id, video_path))
        else:
            logger.warning(f"Video file not found for camera {camera_id}: {video_path}")
    
    return processors