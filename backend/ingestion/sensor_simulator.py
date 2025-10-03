import random
from datetime import datetime
from typing import Dict, Any, List
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class SensorSimulator:
    """Simulate various sensor data in realistic formats"""
    
    @staticmethod
    def generate_smartwatch_data(scenario: str = "normal") -> Dict[str, Any]:
        """
        Generate smartwatch health data
        
        Scenarios: normal, elevated_heart_rate, low_heart_rate, low_spo2, bp_drop
        """
        base_data = {
            "device_id": "smartwatch_001",
            "device_type": "smartwatch",
            "timestamp": datetime.now().isoformat(),
            "user_id": "user_primary",
        }
        
        if scenario == "normal":
            data = {
                **base_data,
                "heart_rate": random.randint(60, 80),
                "spo2": random.randint(95, 99),
                "blood_pressure": {
                    "systolic": random.randint(110, 130),
                    "diastolic": random.randint(70, 85)
                },
                "activity": "resting"
            }
        elif scenario == "elevated_heart_rate":
            data = {
                **base_data,
                "heart_rate": random.randint(130, 160),
                "spo2": random.randint(92, 96),
                "blood_pressure": {
                    "systolic": random.randint(140, 160),
                    "diastolic": random.randint(90, 100)
                },
                "activity": "stressed"
            }
        elif scenario == "low_heart_rate":
            data = {
                **base_data,
                "heart_rate": random.randint(30, 45),
                "spo2": random.randint(88, 92),
                "blood_pressure": {
                    "systolic": random.randint(80, 95),
                    "diastolic": random.randint(50, 65)
                },
                "activity": "unconscious"
            }
        elif scenario == "low_spo2":
            data = {
                **base_data,
                "heart_rate": random.randint(75, 95),
                "spo2": random.randint(85, 89),
                "blood_pressure": {
                    "systolic": random.randint(100, 120),
                    "diastolic": random.randint(65, 80)
                },
                "activity": "distress"
            }
        elif scenario == "bp_drop":
            data = {
                **base_data,
                "heart_rate": random.randint(50, 70),
                "spo2": random.randint(90, 94),
                "blood_pressure": {
                    "systolic": random.randint(70, 90),  # Significant drop
                    "diastolic": random.randint(45, 60)
                },
                "activity": "shock"
            }
        else:
            data = base_data
        
        return data
    
    @staticmethod
    def generate_accelerometer_data(scenario: str = "normal") -> Dict[str, Any]:
        """
        Generate accelerometer data for fall detection
        
        Scenarios: normal, fall, impact
        """
        base_data = {
            "device_id": "accelerometer_001",
            "device_type": "accelerometer",
            "timestamp": datetime.now().isoformat(),
        }
        
        if scenario == "normal":
            data = {
                **base_data,
                "acceleration": {
                    "x": random.uniform(-0.5, 0.5),
                    "y": random.uniform(-0.5, 0.5),
                    "z": random.uniform(9.3, 10.1)  # Gravity
                },
                "magnitude": random.uniform(9.5, 10.2),
                "orientation": "upright"
            }
        elif scenario == "fall":
            data = {
                **base_data,
                "acceleration": {
                    "x": random.uniform(-2.5, 2.5),
                    "y": random.uniform(-2.5, 2.5),
                    "z": random.uniform(-0.5, 2.0)  # Sudden drop
                },
                "magnitude": random.uniform(15.0, 25.0),  # High impact
                "orientation": "horizontal",
                "event": "FALL_DETECTED"
            }
        elif scenario == "impact":
            data = {
                **base_data,
                "acceleration": {
                    "x": random.uniform(-5.0, 5.0),
                    "y": random.uniform(-5.0, 5.0),
                    "z": random.uniform(-5.0, 5.0)
                },
                "magnitude": random.uniform(20.0, 35.0),
                "orientation": "unknown",
                "event": "HIGH_IMPACT"
            }
        else:
            data = base_data
        
        return data
    
    @staticmethod
    def generate_microphone_data(scenario: str = "normal") -> Dict[str, Any]:
        """
        Generate microphone audio classification data
        
        Scenarios: normal, scream, loud_noise, breaking_glass
        """
        base_data = {
            "device_id": "microphone_001",
            "device_type": "microphone",
            "timestamp": datetime.now().isoformat(),
        }
        
        if scenario == "normal":
            data = {
                **base_data,
                "sound_level_db": random.uniform(30, 50),
                "classification": "ambient",
                "confidence": random.uniform(0.85, 0.95)
            }
        elif scenario == "scream":
            data = {
                **base_data,
                "sound_level_db": random.uniform(85, 105),
                "classification": "scream",
                "confidence": random.uniform(0.80, 0.95),
                "event": "SCREAM_DETECTED"
            }
        elif scenario == "loud_noise":
            data = {
                **base_data,
                "sound_level_db": random.uniform(80, 95),
                "classification": "loud_bang",
                "confidence": random.uniform(0.75, 0.90),
                "event": "LOUD_NOISE"
            }
        elif scenario == "breaking_glass":
            data = {
                **base_data,
                "sound_level_db": random.uniform(75, 90),
                "classification": "breaking_glass",
                "confidence": random.uniform(0.70, 0.88),
                "event": "GLASS_BREAK"
            }
        else:
            data = base_data
        
        return data
    
    @staticmethod
    def generate_smoke_detector_data(scenario: str = "normal") -> Dict[str, Any]:
        """
        Generate smoke detector data
        
        Scenarios: normal, smoke, fire
        """
        base_data = {
            "device_id": "smoke_detector_001",
            "device_type": "smoke_detector",
            "timestamp": datetime.now().isoformat(),
            "location": "kitchen"
        }
        
        if scenario == "normal":
            data = {
                **base_data,
                "smoke_level": random.uniform(0.0, 0.05),
                "temperature_celsius": random.uniform(18, 24),
                "status": "normal"
            }
        elif scenario == "smoke":
            data = {
                **base_data,
                "smoke_level": random.uniform(0.3, 0.6),
                "temperature_celsius": random.uniform(28, 35),
                "status": "smoke_detected",
                "event": "SMOKE_DETECTED"
            }
        elif scenario == "fire":
            data = {
                **base_data,
                "smoke_level": random.uniform(0.7, 1.0),
                "temperature_celsius": random.uniform(45, 80),
                "status": "fire_alarm",
                "event": "FIRE_DETECTED"
            }
        else:
            data = base_data
        
        return data

# Demo scenario sequences
DEMO_SCENARIOS = {
    "scenario_1_weapon": {
        "camera_2": "weapon_detected",
        "smartwatch": "elevated_heart_rate",
        "microphone": "scream"
    },
    "scenario_2_fall": {
        "camera_3": "fall_detected",
        "accelerometer": "fall",
        "smartwatch": "low_heart_rate"
    },
    "scenario_3_fire": {
        "camera_4": "fire_detected",
        "smoke_detector": "fire",
        "microphone": "loud_noise"
    },
    "scenario_4_crowd": {
        "camera_5": "crowd_detected",
        "microphone": "loud_noise"
    }
}