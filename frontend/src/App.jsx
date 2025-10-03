import { useState, useEffect } from 'react';
import { AlertCircle, Shield, Camera, Activity, Bell, CheckCircle, Phone, Users, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [alerts, setAlerts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [stats, setStats] = useState({ active_alerts: 0, devices_online: 0 });
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [ws, setWs] = useState(null);

  useEffect(() => {
    fetchAlerts();
    fetchDevices();
    fetchStats();
    
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/ws');
    websocket.onopen = () => console.log('WebSocket connected');
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'new_alert') {
        setAlerts(prev => [data.alert, ...prev]);
      }
    };
    setWs(websocket);
    
    const interval = setInterval(() => {
      fetchAlerts();
      fetchStats();
    }, 5000);
    
    return () => {
      clearInterval(interval);
      if (websocket) websocket.close();
    };
  }, []);

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts`);
      const data = await res.json();
      setAlerts(data.alerts || []);
    } catch (err) {
      console.error('Failed to fetch alerts:', err);
    }
  };

  const fetchDevices = async () => {
    try {
      const res = await fetch(`${API_BASE}/devices`);
      const data = await res.json();
      setDevices(data.devices || []);
    } catch (err) {
      console.error('Failed to fetch devices:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      const data = await res.json();
      setStats(data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const handleAcknowledge = async (alert) => {
    try {
      await fetch(`${API_BASE}/alerts/${alert.timestamp}/acknowledge`, { method: 'POST' });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert:', err);
    }
  };

  const handleDismiss = async (alert) => {
    try {
      await fetch(`${API_BASE}/alerts/${alert.timestamp}/dismiss`, { method: 'POST' });
      fetchAlerts();
    } catch (err) {
      console.error('Failed to dismiss alert:', err);
    }
  };

  const getSeverityColor = (severity) => {
    const colors = {
      CRITICAL: 'bg-red-100 text-red-800 border-red-300',
      HIGH: 'bg-orange-100 text-orange-800 border-orange-300',
      MEDIUM: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      LOW: 'bg-blue-100 text-blue-800 border-blue-300'
    };
    return colors[severity] || colors.MEDIUM;
  };

  const formatTimestamp = (timestamp) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now - date;
      const diffMins = Math.floor(diffMs / 60000);
      
      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins} min ago`;
      const diffHours = Math.floor(diffMins / 60);
      if (diffHours < 24) return `${diffHours}h ago`;
      return date.toLocaleString();
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">Home Threat Detection</h1>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setActiveView('dashboard')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  activeView === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setActiveView('devices')}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  activeView === 'devices' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                Devices
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {activeView === 'dashboard' ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Stats */}
            <div className="lg:col-span-3 grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Active Alerts</p>
                    <p className="text-3xl font-bold text-gray-900">{stats.active_alerts}</p>
                  </div>
                  <Bell className="w-10 h-10 text-blue-600" />
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Devices Online</p>
                    <p className="text-3xl font-bold text-gray-900">{stats.devices_online}</p>
                  </div>
                  <Activity className="w-10 h-10 text-green-600" />
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-4 border border-gray-200">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">System Status</p>
                    <p className="text-lg font-semibold text-green-600">Operational</p>
                  </div>
                  <CheckCircle className="w-10 h-10 text-green-600" />
                </div>
              </div>
            </div>

            {/* Alerts List */}
            <div className="lg:col-span-2 bg-white rounded-lg shadow border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Current Alerts</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                {alerts.length === 0 ? (
                  <div className="p-8 text-center text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-2 text-green-500" />
                    <p>No active alerts</p>
                  </div>
                ) : (
                  alerts.map((alert, idx) => (
                    <div
                      key={idx}
                      className={`p-4 hover:bg-gray-50 cursor-pointer border-l-4 ${
                        alert.severity === 'CRITICAL' ? 'border-red-500' : 
                        alert.severity === 'HIGH' ? 'border-orange-500' : 'border-yellow-500'
                      }`}
                      onClick={() => setSelectedIncident(alert)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`px-2 py-1 rounded text-xs font-semibold ${getSeverityColor(alert.severity)}`}>
                              {alert.severity}
                            </span>
                            <span className="text-sm text-gray-500">{formatTimestamp(alert.timestamp)}</span>
                          </div>
                          <h3 className="font-semibold text-gray-900 mb-1">{alert.alert_type?.replace(/_/g, ' ')}</h3>
                          <p className="text-sm text-gray-600">{alert.description}</p>
                          {alert.camera_id && (
                            <p className="text-xs text-gray-500 mt-1">Camera {alert.camera_id}</p>
                          )}
                        </div>
                        <div className="flex gap-2 ml-4">
                          <button
                            onClick={(e) => { e.stopPropagation(); handleAcknowledge(alert); }}
                            className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium hover:bg-blue-200"
                          >
                            Acknowledge
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); handleDismiss(alert); }}
                            className="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs font-medium hover:bg-gray-200"
                          >
                            Dismiss
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Device Status */}
            <div className="bg-white rounded-lg shadow border border-gray-200">
              <div className="p-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Devices</h2>
              </div>
              <div className="divide-y divide-gray-200 max-h-[600px] overflow-y-auto">
                {devices.slice(0, 5).map((device, idx) => (
                  <div key={idx} className="p-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${device.status === 'online' ? 'bg-green-500' : 'bg-red-500'}`} />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{device.name}</p>
                          <p className="text-xs text-gray-500">{device.location}</p>
                        </div>
                      </div>
                      <Camera className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow border border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">All Devices</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Device</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Location</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {devices.map((device, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      <td className="px-4 py-3 text-sm font-medium text-gray-900">{device.name}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{device.type}</td>
                      <td className="px-4 py-3 text-sm text-gray-600">{device.location}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          device.status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {device.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>

      {/* Incident Modal */}
      {selectedIncident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="p-6 border-b border-gray-200 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">Incident Details</h2>
              <button onClick={() => setSelectedIncident(null)} className="text-gray-400 hover:text-gray-600">
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6">
              <div className="mb-4">
                <span className={`px-3 py-1 rounded text-sm font-semibold ${getSeverityColor(selectedIncident.severity)}`}>
                  {selectedIncident.severity} ALERT
                </span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {selectedIncident.alert_type?.replace(/_/g, ' ')}
              </h3>
              <p className="text-gray-700 mb-4">{selectedIncident.description}</p>
              
              <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">Time</p>
                  <p className="font-medium">{formatTimestamp(selectedIncident.timestamp)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Source</p>
                  <p className="font-medium">
                    {selectedIncident.camera_id ? `Camera ${selectedIncident.camera_id}` : selectedIncident.source}
                  </p>
                </div>
                {selectedIncident.confidence && (
                  <div>
                    <p className="text-sm text-gray-600">Confidence</p>
                    <p className="font-medium">{(selectedIncident.confidence * 100).toFixed(0)}%</p>
                  </div>
                )}
              </div>

              <div className="flex gap-3">
                {selectedIncident.severity === 'CRITICAL' && (
                  <button className="flex-1 bg-red-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-red-700 flex items-center justify-center gap-2">
                    <Phone className="w-5 h-5" />
                    Call 911
                  </button>
                )}
                <button className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 flex items-center justify-center gap-2">
                  <Users className="w-5 h-5" />
                  Notify Contact
                </button>
                <button 
                  onClick={() => { handleDismiss(selectedIncident); setSelectedIncident(null); }}
                  className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg font-semibold hover:bg-gray-300"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;