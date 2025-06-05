# Communication Architecture: WebSocket + HTTP Pattern for PLC Systems

## Overview

This document describes the communication architecture for PLC-controlled hyperbaric chamber systems, implementing a hybrid WebSocket + HTTP pattern that provides immediate user feedback while maintaining safety-critical confirmation from the PLC.

## Core Principles

### 🎯 **Separation of Concerns**
- **HTTP Endpoints**: Commands and control operations (writing to PLC)
- **WebSocket Endpoints**: Real-time status monitoring (reading from PLC)
- **PLC**: All control logic, safety systems, and decision-making

### 🎯 **Immediate Feedback Pattern**
- **Optimistic UI Updates**: Immediate visual response to user actions
- **Server Confirmation**: HTTP response provides expected state
- **PLC Verification**: WebSocket confirms actual hardware state
- **Error Recovery**: Automatic rollback on command failure

## Architecture Components

### 1. **WebSocket Communication (Status Reading)**

#### **Primary Endpoints**
```
/ws/system-status     - Comprehensive system status (1s updates)
/ws/critical-status   - High-frequency safety data (500ms updates)
/ws/pressure          - Pressure system monitoring
/ws/sensors           - Environmental sensor data
```

#### **Data Structure**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "control_panel": {
    "ac_state": true,
    "ceiling_lights_state": false,
    "reading_lights_state": true,
    "intercom_state": false
  },
  "pressure": {
    "setpoint": 2.0,
    "internal_pressure_1": 1.95,
    "internal_pressure_2": 1.97
  },
  "session": {
    "running_state": true,
    "pressuring_state": false,
    "stabilising_state": true
  },
  "system": {
    "plc_connected": true,
    "communication_errors": 0,
    "last_update": "2024-01-15T10:30:00Z"
  }
}
```

### 2. **HTTP Communication (Commands Only)**

#### **Command Pattern**
```http
POST /api/control/lights/ceiling/toggle
Content-Type: application/json

Response:
{
  "success": true,
  "data": {
    "ceiling_lights": true,
    "previous_state": false,
    "expected_state": true,
    "command_timestamp": "2024-01-15T10:30:00Z"
  },
  "message": "Ceiling lights toggled"
}
```

#### **Key Command Categories**
- **Authentication**: `/api/auth/*`
- **Control Panel**: `/api/control/*`
- **Pressure Control**: `/api/pressure/*`
- **Session Management**: `/api/session/*`
- **Mode Settings**: `/api/modes/*`
- **Climate Control**: `/api/ac/*`

## Implementation Guide

### 1. **Frontend Controller Class**

```javascript
class ControlSystem {
  constructor() {
    this.wsStatus = null;              // Real-time WebSocket data
    this.optimisticStates = {};        // Immediate UI states
    this.pendingCommands = new Set();  // Commands in progress
    this.initWebSocket();
  }

  // WebSocket connection with auto-reconnect
  initWebSocket() {
    this.ws = new WebSocket('ws://localhost:8000/ws/system-status');
    
    this.ws.onmessage = (event) => {
      this.wsStatus = JSON.parse(event.data);
      this.updateAllControls();
    };

    this.ws.onclose = () => {
      console.warn('WebSocket disconnected, reconnecting...');
      setTimeout(() => this.initWebSocket(), 1000);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  // Command execution with immediate feedback
  async executeCommand(endpoint, controlName, buttonId) {
    const commandId = `${controlName}_${Date.now()}`;
    this.pendingCommands.add(commandId);

    try {
      // 1. Immediate optimistic update
      const currentState = this.getCurrentState(controlName);
      this.optimisticStates[controlName] = !currentState;
      this.updateButton(buttonId, !currentState, true);

      // 2. Send HTTP command
      const response = await fetch(endpoint, { method: 'POST' });
      const result = await response.json();
      
      if (!response.ok || !result.success) {
        throw new Error(result.message || 'Command failed');
      }

      // 3. Update with server response
      if (result.data && result.data[controlName] !== undefined) {
        this.optimisticStates[controlName] = result.data[controlName];
      }

      // 4. Wait for PLC confirmation
      await this.waitForPLCConfirmation(controlName, this.optimisticStates[controlName]);
      
      console.log(`✅ ${controlName} command successful`);

    } catch (error) {
      console.error(`❌ ${controlName} command failed:`, error);
      
      // Revert optimistic state
      delete this.optimisticStates[controlName];
      this.showNotification(`Failed to control ${controlName}`, 'error');
      
    } finally {
      this.pendingCommands.delete(commandId);
      this.updateAllControls();
    }
  }

  // Get current state (optimistic or WebSocket)
  getCurrentState(controlName) {
    if (this.optimisticStates[controlName] !== undefined) {
      return this.optimisticStates[controlName];
    }
    
    // Map to WebSocket data structure
    const stateMap = {
      ceiling_lights: 'control_panel.ceiling_lights_state',
      reading_lights: 'control_panel.reading_lights_state',
      ac: 'control_panel.ac_state',
      intercom: 'control_panel.intercom_state'
    };
    
    const path = stateMap[controlName];
    if (path && this.wsStatus) {
      return this.getNestedValue(this.wsStatus, path) || false;
    }
    
    return false;
  }

  // Wait for PLC state confirmation
  async waitForPLCConfirmation(controlName, expectedState, timeout = 3000) {
    return new Promise((resolve, reject) => {
      const startTime = Date.now();
      
      const checkConfirmation = () => {
        const actualState = this.getCurrentState(controlName);
        
        if (actualState === expectedState) {
          delete this.optimisticStates[controlName];
          resolve();
        } else if (Date.now() - startTime > timeout) {
          reject(new Error(`PLC confirmation timeout for ${controlName}`));
        } else {
          setTimeout(checkConfirmation, 100);
        }
      };
      
      checkConfirmation();
    });
  }

  // Update button visual state
  updateButton(buttonId, state, isPending = false) {
    const button = document.getElementById(buttonId);
    if (!button) return;

    // Update text and base styling
    const labels = {
      'ceiling-lights-btn': state ? 'LIGHTS ON' : 'LIGHTS OFF',
      'reading-lights-btn': state ? 'READING ON' : 'READING OFF',
      'ac-btn': state ? 'AC ON' : 'AC OFF',
      'intercom-btn': state ? 'INTERCOM ON' : 'INTERCOM OFF'
    };

    button.textContent = labels[buttonId] || (state ? 'ON' : 'OFF');
    button.className = `control-btn ${state ? 'btn-on' : 'btn-off'}`;
    
    // Visual states
    if (isPending) {
      button.classList.add('pending');
      button.disabled = true;
    } else {
      button.classList.remove('pending');
      button.disabled = false;
    }

    // Show optimistic state indicator
    const controlName = this.getControlNameFromButtonId(buttonId);
    if (this.optimisticStates[controlName] !== undefined) {
      button.classList.add('optimistic');
    } else {
      button.classList.remove('optimistic');
    }
  }

  // Update all control elements
  updateAllControls() {
    const controls = [
      { name: 'ceiling_lights', buttonId: 'ceiling-lights-btn' },
      { name: 'reading_lights', buttonId: 'reading-lights-btn' },
      { name: 'ac', buttonId: 'ac-btn' },
      { name: 'intercom', buttonId: 'intercom-btn' }
    ];

    controls.forEach(({ name, buttonId }) => {
      const isPending = Array.from(this.pendingCommands).some(cmd => cmd.includes(name));
      this.updateButton(buttonId, this.getCurrentState(name), isPending);
    });
  }

  // Utility functions
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  getControlNameFromButtonId(buttonId) {
    const mapping = {
      'ceiling-lights-btn': 'ceiling_lights',
      'reading-lights-btn': 'reading_lights',
      'ac-btn': 'ac',
      'intercom-btn': 'intercom'
    };
    return mapping[buttonId];
  }

  showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
  }
}
```

### 2. **Event Handlers Setup**

```javascript
// Initialize control system
const controlSystem = new ControlSystem();

// Wire up button events
document.getElementById('ceiling-lights-btn').addEventListener('click', () => {
  controlSystem.executeCommand(
    '/api/control/lights/ceiling/toggle',
    'ceiling_lights',
    'ceiling-lights-btn'
  );
});

document.getElementById('reading-lights-btn').addEventListener('click', () => {
  controlSystem.executeCommand(
    '/api/control/lights/reading/toggle',
    'reading_lights',
    'reading-lights-btn'
  );
});

document.getElementById('ac-btn').addEventListener('click', () => {
  controlSystem.executeCommand(
    '/api/control/ac/toggle',
    'ac',
    'ac-btn'
  );
});

document.getElementById('intercom-btn').addEventListener('click', () => {
  controlSystem.executeCommand(
    '/api/control/intercom/toggle',
    'intercom',
    'intercom-btn'
  );
});
```

### 3. **CSS Styling for Visual Feedback**

```css
.control-btn {
  padding: 12px 24px;
  border: 2px solid #ccc;
  border-radius: 8px;
  font-weight: bold;
  font-size: 14px;
  transition: all 0.2s ease;
  cursor: pointer;
  min-width: 120px;
}

.btn-on {
  background-color: #4CAF50;
  color: white;
  border-color: #45a049;
  box-shadow: 0 0 10px rgba(76, 175, 80, 0.3);
}

.btn-off {
  background-color: #f44336;
  color: white;
  border-color: #da190b;
  box-shadow: 0 0 10px rgba(244, 67, 54, 0.3);
}

.pending {
  opacity: 0.7;
  cursor: not-allowed;
  animation: pulse 1s infinite;
}

.optimistic {
  border-style: dashed;
  border-width: 3px;
  box-shadow: 0 0 15px rgba(255, 193, 7, 0.5);
}

@keyframes pulse {
  0% { opacity: 0.7; }
  50% { opacity: 1; }
  100% { opacity: 0.7; }
}

.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 24px;
  border-radius: 4px;
  color: white;
  font-weight: bold;
  z-index: 1000;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.notification-error {
  background-color: #f44336;
  border-left: 4px solid #d32f2f;
}

.notification-success {
  background-color: #4CAF50;
  border-left: 4px solid #388e3c;
}

.notification-warning {
  background-color: #ff9800;
  border-left: 4px solid #f57c00;
}
```

## Safety Considerations

### 1. **Error Handling**

```javascript
// Always implement comprehensive error handling
try {
  await controlSystem.executeCommand(endpoint, control, buttonId);
} catch (error) {
  // Log for debugging
  console.error('Control command failed:', error);
  
  // Notify user
  controlSystem.showNotification('Command failed - system may be offline', 'error');
  
  // Revert UI state
  delete controlSystem.optimisticStates[controlName];
  controlSystem.updateAllControls();
}
```

### 2. **WebSocket Connection Health**

```javascript
// Monitor connection health
class ConnectionMonitor {
  constructor(controlSystem) {
    this.controlSystem = controlSystem;
    this.lastHeartbeat = Date.now();
    this.checkInterval = setInterval(() => this.checkHealth(), 5000);
  }

  checkHealth() {
    const timeSinceLastUpdate = Date.now() - this.lastHeartbeat;
    
    if (timeSinceLastUpdate > 10000) { // 10 seconds
      this.showConnectionWarning();
    }
  }

  onWebSocketMessage(data) {
    this.lastHeartbeat = Date.now();
    this.hideConnectionWarning();
  }

  showConnectionWarning() {
    const warning = document.getElementById('connection-warning');
    if (warning) {
      warning.style.display = 'block';
    }
  }
}
```

### 3. **Command Rate Limiting**

```javascript
// Prevent command spam
class RateLimiter {
  constructor(maxCommands = 5, timeWindow = 1000) {
    this.maxCommands = maxCommands;
    this.timeWindow = timeWindow;
    this.commandHistory = [];
  }

  canExecute() {
    const now = Date.now();
    
    // Remove old commands outside time window
    this.commandHistory = this.commandHistory.filter(
      timestamp => now - timestamp < this.timeWindow
    );
    
    if (this.commandHistory.length >= this.maxCommands) {
      return false;
    }
    
    this.commandHistory.push(now);
    return true;
  }
}
```

## Best Practices

### ✅ **Do's**
- Always use WebSocket for status monitoring
- Implement optimistic UI updates for better UX
- Provide visual feedback for all command states
- Handle WebSocket reconnection automatically
- Validate commands on both frontend and backend
- Log all command operations for audit trails
- Implement proper error recovery mechanisms

### ❌ **Don'ts**
- Don't poll HTTP endpoints for status updates
- Don't rely solely on optimistic updates for safety-critical data
- Don't ignore WebSocket connection failures
- Don't allow unlimited command rate
- Don't suppress error messages from users
- Don't bypass PLC safety systems

## Testing Strategy

### 1. **Connection Failure Tests**
```javascript
// Test WebSocket disconnection
async function testConnectionFailure() {
  // Simulate network failure
  controlSystem.ws.close();
  
  // Verify UI shows disconnection warning
  // Verify automatic reconnection attempt
  // Verify commands fail gracefully
}
```

### 2. **Command Failure Tests**
```javascript
// Test PLC command rejection
async function testCommandRejection() {
  // Send command that PLC will reject
  await controlSystem.executeCommand('/api/invalid/endpoint', 'test', 'test-btn');
  
  // Verify UI reverts to original state
  // Verify error notification appears
}
```

### 3. **State Synchronization Tests**
```javascript
// Test optimistic vs actual state sync
async function testStateSynchronization() {
  // Send command
  // Verify immediate UI update
  // Verify WebSocket confirmation
  // Verify final state consistency
}
```

## Performance Considerations

### 1. **WebSocket Message Frequency**
- **System Status**: 1 second updates (general monitoring)
- **Critical Status**: 500ms updates (safety-critical data)
- **Pressure Data**: 500ms updates (real-time control)
- **Sensor Data**: 2 second updates (environmental monitoring)

### 2. **Memory Management**
```javascript
// Clean up optimistic states
setInterval(() => {
  const maxAge = 10000; // 10 seconds
  const now = Date.now();
  
  Object.keys(controlSystem.optimisticStates).forEach(key => {
    const state = controlSystem.optimisticStates[key];
    if (state.timestamp && now - state.timestamp > maxAge) {
      delete controlSystem.optimisticStates[key];
    }
  });
}, 5000);
```

## Monitoring and Debugging

### 1. **Command Logging**
```javascript
// Log all commands for debugging
const commandLogger = {
  log(command, status, duration) {
    console.log(`[COMMAND] ${command} - ${status} (${duration}ms)`);
    
    // Send to monitoring service
    if (window.monitoring) {
      window.monitoring.trackCommand(command, status, duration);
    }
  }
};
```

### 2. **WebSocket Health Metrics**
```javascript
// Track WebSocket performance
const wsMetrics = {
  messagesReceived: 0,
  lastMessageTime: 0,
  reconnectCount: 0,
  
  onMessage() {
    this.messagesReceived++;
    this.lastMessageTime = Date.now();
  },
  
  onReconnect() {
    this.reconnectCount++;
  },
  
  getHealthStatus() {
    const timeSinceLastMessage = Date.now() - this.lastMessageTime;
    return {
      isHealthy: timeSinceLastMessage < 5000,
      messagesReceived: this.messagesReceived,
      reconnectCount: this.reconnectCount,
      lastMessageAge: timeSinceLastMessage
    };
  }
};
```

## Conclusion

This communication architecture provides:

- **Immediate User Feedback**: Optimistic UI updates for responsive interface
- **Safety Verification**: PLC confirmation for all critical operations
- **Real-time Monitoring**: WebSocket for continuous status updates
- **Error Recovery**: Graceful handling of failures and disconnections
- **Scalability**: Efficient message distribution and state management

The pattern is specifically designed for safety-critical PLC-controlled systems where both user experience and operational safety are paramount.

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**Author**: Elixir Backend Team 