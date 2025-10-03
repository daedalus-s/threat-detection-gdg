from pinecone import Pinecone, ServerlessSpec
from typing import Dict, Any, List
import json
from datetime import datetime
import hashlib
from backend.config.settings import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class VectorStore:
    """Store and retrieve temporal threat events using Pinecone"""
    
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index_name = settings.pinecone_index_name
        self.index = None
        self._initialize_index()
    
    def _initialize_index(self):
        """Create or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            
            if self.index_name not in [idx.name for idx in existing_indexes]:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                # Create index with appropriate dimensions
                # Using 384 dimensions for sentence embeddings (can adjust)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=384,  # Adjust based on embedding model
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=settings.pinecone_environment
                    )
                )
                logger.info(f"Index {self.index_name} created successfully")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            logger.info(f"Connected to Pinecone index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone index: {e}")
            # For demo, continue without Pinecone if it fails
            self.index = None
    
    def store_event(self, alert: Dict[str, Any]) -> bool:
        """
        Store a threat event with embeddings for retrieval
        
        Args:
            alert: Alert dictionary containing threat information
        
        Returns:
            True if successful, False otherwise
        """
        if not self.index:
            logger.warning("Pinecone index not available, skipping storage")
            return False
        
        try:
            # Generate a unique ID for the event
            event_id = self._generate_event_id(alert)
            
            # Create a simple embedding (in production, use a real embedding model)
            # For demo: use hash of description as "embedding"
            embedding = self._create_simple_embedding(alert)
            
            # Prepare metadata
            metadata = {
                'alert_type': alert.get('alert_type', 'unknown'),
                'severity': alert.get('severity', 'unknown'),
                'description': alert.get('description', ''),
                'timestamp': alert.get('timestamp', datetime.now().isoformat()),
                'camera_id': alert.get('camera_id', 0),
                'device_id': alert.get('device_id', ''),
                'confidence': alert.get('confidence', 0.0),
                'action_required': alert.get('action_required', ''),
                'source': alert.get('source', 'unknown')
            }
            
            # Upsert to Pinecone
            self.index.upsert(
                vectors=[
                    {
                        'id': event_id,
                        'values': embedding,
                        'metadata': metadata
                    }
                ]
            )
            
            logger.info(f"Event stored in Pinecone: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store event in Pinecone: {e}")
            return False
    
    def query_events(self, 
                     query_text: str = None, 
                     filter_dict: Dict[str, Any] = None,
                     top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Query stored events
        
        Args:
            query_text: Text to search for (optional)
            filter_dict: Metadata filters (e.g., {'severity': 'CRITICAL'})
            top_k: Number of results to return
        
        Returns:
            List of matching events
        """
        if not self.index:
            logger.warning("Pinecone index not available")
            return []
        
        try:
            if query_text:
                # Create embedding for query
                query_embedding = self._create_simple_embedding({'description': query_text})
            else:
                # If no query text, use a zero vector (will rely on filters)
                query_embedding = [0.0] * 384
            
            # Query Pinecone
            results = self.index.query(
                vector=query_embedding,
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True
            )
            
            # Extract and return matches
            events = []
            for match in results.matches:
                event = {
                    'id': match.id,
                    'score': match.score,
                    **match.metadata
                }
                events.append(event)
            
            logger.info(f"Retrieved {len(events)} events from Pinecone")
            return events
            
        except Exception as e:
            logger.error(f"Failed to query Pinecone: {e}")
            return []
    
    def get_recent_events(self, minutes: int = 30, severity: str = None) -> List[Dict[str, Any]]:
        """
        Get recent events within a time window
        
        Args:
            minutes: Time window in minutes
            severity: Filter by severity (optional)
        
        Returns:
            List of recent events
        """
        # Calculate timestamp threshold
        from datetime import timedelta
        threshold = datetime.now() - timedelta(minutes=minutes)
        threshold_str = threshold.isoformat()
        
        # Build filter
        filter_dict = {}
        if severity:
            filter_dict['severity'] = {'$eq': severity}
        
        # Note: Pinecone doesn't support timestamp range queries directly
        # For production, consider using a separate time-series database
        # For demo, we'll query all and filter in memory
        
        all_events = self.query_events(top_k=100, filter_dict=filter_dict if filter_dict else None)
        
        # Filter by timestamp in memory
        recent = [e for e in all_events if e.get('timestamp', '') >= threshold_str]
        
        return recent
    
    def _generate_event_id(self, alert: Dict[str, Any]) -> str:
        """Generate unique ID for event"""
        # Combine timestamp, alert type, and camera/device ID
        id_string = f"{alert.get('timestamp', '')}_{alert.get('alert_type', '')}_{alert.get('camera_id', '')}_{alert.get('device_id', '')}"
        return hashlib.md5(id_string.encode()).hexdigest()
    
    def _create_simple_embedding(self, data: Dict[str, Any], dim: int = 384) -> List[float]:
        """
        Create a simple embedding for demo purposes
        
        In production, use a real embedding model like:
        - sentence-transformers
        - OpenAI embeddings
        - Google embeddings
        """
        # For demo: Create a pseudo-random but deterministic embedding
        text = json.dumps(data, sort_keys=True)
        hash_val = int(hashlib.sha256(text.encode()).hexdigest(), 16)
        
        # Generate deterministic "random" values
        import random
        random.seed(hash_val)
        
        embedding = [random.random() for _ in range(dim)]
        
        # Normalize
        magnitude = sum(x*x for x in embedding) ** 0.5
        embedding = [x / magnitude for x in embedding]
        
        return embedding

# Global store instance
_store_instance = None

def get_vector_store() -> VectorStore:
    """Get or create global vector store instance"""
    global _store_instance
    if _store_instance is None:
        _store_instance = VectorStore()
    return _store_instance