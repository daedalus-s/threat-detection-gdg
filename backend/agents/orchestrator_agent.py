from typing import Dict, Any, List
from datetime import datetime
import threading
import time
from queue import Queue
from backend.storage.vector_store import get_vector_store
from backend.ingestion.kafka_producer import get_producer
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class OrchestratorAgent:
    """
    Central orchestrator agent that receives alerts from sub-agents and makes escalation decisions
    Implements the decision flow logic from the specification
    """
    
    def __init__(self):
        self.alert_queue = Queue()
        self.active_alerts = []
        self.vector_store = get_vector_store()
        self.producer = get_producer()
        self.running = False
        self.thread = None
        
        # State tracking for decision flow
        self.camera_status = {i: 'online' for i in range(1, 6)}
        self.vitals_pending_response = {}
        
        logger.info("Orchestrator Agent initialized")
    
    def start(self):
        """Start the orchestrator"""
        if self.running:
            logger.warning("Orchestrator already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.thread.start()
        logger.info("Orchestrator Agent started")
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Orchestrator Agent stopped")
    
    def receive_alert(self, alert: Dict[str, Any]):
        """Receive alert from sub-agent"""
        logger.info(f"Orchestrator received alert: {alert.get('alert_type')} - Severity: {alert.get('severity')}")
        self.alert_queue.put(alert)
    
    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process alerts from queue
                if not self.alert_queue.empty():
                    alert = self.alert_queue.get()
                    self._process_alert(alert)
                else:
                    time.sleep(0.1)  # Small sleep to prevent busy waiting
                    
            except Exception as e:
                logger.error(f"Orchestrator processing error: {e}")
    
    def _process_alert(self, alert: Dict[str, Any]):
        """
        Process an alert and make escalation decisions based on the decision flow
        """
        alert_type = alert.get('alert_type')
        severity = alert.get('severity')
        
        logger.info(f"Processing alert: {alert_type} (Severity: {severity})")
        
        # Store event in vector database for history
        self.vector_store.store_event(alert)
        
        # Add to active alerts
        self.active_alerts.append(alert)
        
        # Decision flow logic
        action = self._determine_action(alert)
        
        # Execute action
        self._execute_action(action, alert)
        
        # Publish alert to Kafka for frontend
        self.producer.send_alert({
            **alert,
            'action': action,
            'processed_at': datetime.now().isoformat()
        })
    
    def _determine_action(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implement the decision tree from specification
        Returns action dictionary with type and details
        """
        alert_type = alert.get('alert_type')
        severity = alert.get('severity')
        
        # PRIMARY CHECK: Weapon + Unfamiliar Face = Critical
        if alert_type == 'WEAPON_INTRUDER' and severity == 'CRITICAL':
            return {
                'type': 'CALL_911',
                'reason': 'Weapon detected with unfamiliar person',
                'priority': 'CRITICAL',
                'notify_contacts': True
            }
        
        # FIRE DETECTION = Critical
        if alert_type == 'FIRE_DETECTED' and severity == 'CRITICAL':
            return {
                'type': 'CALL_911',
                'reason': 'Fire detected',
                'priority': 'CRITICAL',
                'notify_contacts': True
            }
        
        # WEAPON DETECTED (familiar or unknown)
        if alert_type == 'WEAPON_DETECTED':
            return {
                'type': 'NOTIFY_OWNER',
                'reason': 'Weapon detected - immediate attention required',
                'priority': 'HIGH',
                'check_cameras': True
            }
        
        # AGGRESSIVE BEHAVIOR
        if alert_type == 'AGGRESSIVE_BEHAVIOR':
            return {
                'type': 'NOTIFY_OWNER',
                'reason': 'Aggressive behavior detected',
                'priority': 'HIGH',
                'check_cameras': True
            }
        
        # FALL DETECTED or PERSON DOWN
        if alert_type in ['FALL_DETECTED', 'PERSON_DOWN']:
            return {
                'type': 'CHECK_VITALS',
                'reason': 'Person down - checking vitals',
                'priority': 'HIGH',
                'next_steps': ['check_smartwatch', 'notify_if_no_response']
            }
        
        # VITALS ABNORMAL
        if alert_type == 'VITALS_ABNORMAL':
            vitals_severity = alert.get('severity')
            if vitals_severity == 'CRITICAL':
                return {
                    'type': 'CALL_911',
                    'reason': 'Critical vital signs detected',
                    'priority': 'CRITICAL',
                    'notify_contacts': True
                }
            else:
                return {
                    'type': 'CHECK_PERSON',
                    'reason': 'Abnormal vitals - checking on person',
                    'priority': 'HIGH',
                    'send_text': True,
                    'timeout_seconds': 300  # 5 minutes
                }
        
        # SCREAM DETECTED
        if alert_type == 'SCREAM_DETECTED':
            return {
                'type': 'CHECK_CAMERAS',
                'reason': 'Scream detected - reviewing cameras',
                'priority': 'HIGH',
                'correlate_with_video': True
            }
        
        # SMOKE DETECTED
        if alert_type == 'SMOKE_DETECTED':
            return {
                'type': 'NOTIFY_OWNER',
                'reason': 'Smoke detected',
                'priority': 'HIGH',
                'check_cameras': True
            }
        
        # LOUD NOISE / GLASS BREAK
        if alert_type in ['LOUD_NOISE', 'GLASS_BREAK']:
            return {
                'type': 'CHECK_CAMERAS',
                'reason': f'{alert_type.replace("_", " ").title()} - investigating',
                'priority': 'MEDIUM',
                'correlate_with_video': True
            }
        
        # CROWD ALERT
        if alert_type == 'CROWD_ALERT':
            return {
                'type': 'NOTIFY_OWNER',
                'reason': 'Unusual number of people detected',
                'priority': 'MEDIUM'
            }
        
        # Default: Notify owner
        return {
            'type': 'NOTIFY_OWNER',
            'reason': alert.get('description', 'Alert detected'),
            'priority': severity
        }
    
    def _execute_action(self, action: Dict[str, Any], alert: Dict[str, Any]):
        """
        Execute the determined action
        For demo: Log actions (in production: make actual calls, send notifications)
        """
        action_type = action.get('type')
        
        logger.info(f"EXECUTING ACTION: {action_type}")
        logger.info(f"  Reason: {action.get('reason')}")
        logger.info(f"  Priority: {action.get('priority')}")
        
        if action_type == 'CALL_911':
            self._handle_emergency_call(alert, action)
        
        elif action_type == 'NOTIFY_OWNER':
            self._handle_owner_notification(alert, action)
        
        elif action_type == 'CHECK_VITALS':
            self._handle_vitals_check(alert, action)
        
        elif action_type == 'CHECK_PERSON':
            self._handle_person_check(alert, action)
        
        elif action_type == 'CHECK_CAMERAS':
            self._handle_camera_check(alert, action)
        
        if action.get('notify_contacts'):
            self._notify_emergency_contacts(alert)
    
    def _handle_emergency_call(self, alert: Dict[str, Any], action: Dict[str, Any]):
        """Handle 911 call (demo: create critical alert)"""
        logger.critical("=" * 60)
        logger.critical("🚨 EMERGENCY: CALLING 911 🚨")
        logger.critical(f"Reason: {action.get('reason')}")
        logger.critical(f"Details: {alert.get('description')}")
        logger.critical("=" * 60)
        
        # In production: trigger actual emergency call
        # For demo: Flag as critical alert for frontend
        alert['emergency_action'] = 'CALL_911'
    
    def _handle_owner_notification(self, alert: Dict[str, Any], action: Dict[str, Any]):
        """Send notification to owner"""
        logger.warning(f"📱 NOTIFYING OWNER: {action.get('reason')}")
        # In production: send push notification, SMS, or call
        alert['notification_sent'] = True
    
    def _handle_vitals_check(self, alert: Dict[str, Any], action: Dict[str, Any]):
        """Check vitals on smartwatch"""
        logger.info("💓 CHECKING VITALS on smartwatch")
        # In production: query smartwatch API
        # For demo: log the check
        alert['vitals_check_requested'] = True
    
    def _handle_person_check(self, alert: Dict[str, Any], action: Dict[str, Any]):
        """Check on person (text, then call)"""
        logger.info(f"👤 CHECKING ON PERSON: Sending text message")
        # In production: send SMS, wait for response
        # Set timeout for escalation
        alert['person_check_initiated'] = True
        alert['check_timeout'] = action.get('timeout_seconds', 300)
    
    def _handle_camera_check(self, alert: Dict[str, Any], action: Dict[str, Any]):
        """Review camera footage"""
        logger.info("📹 REVIEWING CAMERA FOOTAGE")
        # In production: pull recent footage, correlate events
        alert['camera_review_requested'] = True
    
    def _notify_emergency_contacts(self, alert: Dict[str, Any]):
        """Notify emergency contacts"""
        logger.warning("📞 NOTIFYING EMERGENCY CONTACTS")
        # In production: call/text emergency contacts from settings
        alert['emergency_contacts_notified'] = True
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        return self.active_alerts
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert (mark as seen)"""
        for alert in self.active_alerts:
            if alert.get('id') == alert_id:
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                logger.info(f"Alert {alert_id} acknowledged")
                return True
        return False
    
    def dismiss_alert(self, alert_id: str) -> bool:
        """Dismiss an alert (remove from active)"""
        for i, alert in enumerate(self.active_alerts):
            if alert.get('id') == alert_id:
                dismissed = self.active_alerts.pop(i)
                logger.info(f"Alert {alert_id} dismissed: {dismissed.get('alert_type')}")
                return True
        return False

# Global orchestrator instance
_orchestrator_instance = None

def get_orchestrator() -> OrchestratorAgent:
    """Get or create global orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = OrchestratorAgent()
    return _orchestrator_instance