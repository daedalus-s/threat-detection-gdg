from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import asyncio
import json
from datetime import datetime

from backend.agents.orchestrator_agent import get_orchestrator
from backend.storage.vector_store import get_vector_store
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(title="Threat Detection API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("API Server starting up...")
    # Orchestrator is already started in main.py

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("API Server shutting down...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "service": "Threat Detection System",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/alerts")
async def get_alerts():
    """Get all active alerts"""
    orchestrator = get_orchestrator()
    alerts = orchestrator.get_active_alerts()
    
    return {
        "count": len(alerts),
        "alerts": alerts
    }

@app.get("/api/alerts/critical")
async def get_critical_alerts():
    """Get only critical alerts"""
    orchestrator = get_orchestrator()
    all_alerts = orchestrator.get_active_alerts()
    critical = [a for a in all_alerts if a.get('severity') == 'CRITICAL']
    
    return {
        "count": len(critical),
        "alerts": critical
    }

@app.post("/api/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert"""
    orchestrator = get_orchestrator()
    success = orchestrator.acknowledge_alert(alert_id)
    
    if success:
        # Notify all connected clients
        await broadcast_alert_update({
            "type": "alert_acknowledged",
            "alert_id": alert_id
        })
        return {"success": True, "message": "Alert acknowledged"}
    
    return {"success": False, "message": "Alert not found"}

@app.post("/api/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: str):
    """Dismiss an alert"""
    orchestrator = get_orchestrator()
    success = orchestrator.dismiss_alert(alert_id)
    
    if success:
        # Notify all connected clients
        await broadcast_alert_update({
            "type": "alert_dismissed",
            "alert_id": alert_id
        })
        return {"success": True, "message": "Alert dismissed"}
    
    return {"success": False, "message": "Alert not found"}

@app.get("/api/history")
async def get_history(limit: int = 50):
    """Get historical events from vector store"""
    vector_store = get_vector_store()
    events = vector_store.query_events(top_k=limit)
    
    return {
        "count": len(events),
        "events": events
    }

@app.get("/api/history/recent")
async def get_recent_history(minutes: int = 30):
    """Get recent events within time window"""
    vector_store = get_vector_store()
    events = vector_store.get_recent_events(minutes=minutes)
    
    return {
        "count": len(events),
        "events": events,
        "time_window_minutes": minutes
    }

@app.get("/api/devices")
async def get_devices():
    """Get status of all devices"""
    # For demo: return mock device statuses
    devices = []
    
    # Cameras
    for i in range(1, settings.num_cameras + 1):
        devices.append({
            "id": f"camera_{i}",
            "name": f"Camera {i}",
            "type": "camera",
            "location": get_camera_location(i),
            "status": "online",
            "last_seen": datetime.now().isoformat()
        })
    
    # Other sensors
    devices.extend([
        {
            "id": "smartwatch_001",
            "name": "Primary Smartwatch",
            "type": "smartwatch",
            "location": "Wrist",
            "status": "online",
            "last_seen": datetime.now().isoformat()
        },
        {
            "id": "accelerometer_001",
            "name": "Wearable Accelerometer",
            "type": "accelerometer",
            "location": "Wrist",
            "status": "online",
            "last_seen": datetime.now().isoformat()
        },
        {
            "id": "microphone_001",
            "name": "Living Room Microphone",
            "type": "microphone",
            "location": "Living Room",
            "status": "online",
            "last_seen": datetime.now().isoformat()
        },
        {
            "id": "smoke_detector_001",
            "name": "Kitchen Smoke Detector",
            "type": "smoke_detector",
            "location": "Kitchen",
            "status": "online",
            "last_seen": datetime.now().isoformat()
        }
    ])
    
    return {
        "count": len(devices),
        "devices": devices
    }

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    orchestrator = get_orchestrator()
    alerts = orchestrator.get_active_alerts()
    
    critical_count = len([a for a in alerts if a.get('severity') == 'CRITICAL'])
    high_count = len([a for a in alerts if a.get('severity') == 'HIGH'])
    medium_count = len([a for a in alerts if a.get('severity') == 'MEDIUM'])
    
    return {
        "active_alerts": len(alerts),
        "critical_alerts": critical_count,
        "high_alerts": high_count,
        "medium_alerts": medium_count,
        "devices_online": 9,  # 5 cameras + 4 other sensors
        "system_status": "operational"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time alert updates"""
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket client connected. Total connections: {len(active_connections)}")
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(active_connections)}")

async def broadcast_alert_update(data: Dict[str, Any]):
    """Broadcast alert update to all connected clients"""
    message = json.dumps(data)
    
    # Remove disconnected clients
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            disconnected.append(connection)
    
    for conn in disconnected:
        active_connections.remove(conn)

def get_camera_location(camera_id: int) -> str:
    """Get camera location based on ID"""
    locations = {
        1: "Front Door",
        2: "Living Room",
        3: "Hallway",
        4: "Kitchen",
        5: "Backyard"
    }
    return locations.get(camera_id, f"Camera {camera_id}")

# Background task to push new alerts to WebSocket clients
async def alert_broadcaster():
    """Background task to push alerts to WebSocket clients"""
    orchestrator = get_orchestrator()
    last_alert_count = 0
    
    while True:
        try:
            current_alerts = orchestrator.get_active_alerts()
            current_count = len(current_alerts)
            
            if current_count > last_alert_count:
                # New alert detected
                new_alerts = current_alerts[last_alert_count:]
                for alert in new_alerts:
                    await broadcast_alert_update({
                        "type": "new_alert",
                        "alert": alert
                    })
                last_alert_count = current_count
            
            await asyncio.sleep(1)  # Check every second
            
        except Exception as e:
            logger.error(f"Alert broadcaster error: {e}")
            await asyncio.sleep(5)

# Start broadcaster on startup
@app.on_event("startup")
async def start_broadcaster():
    asyncio.create_task(alert_broadcaster())