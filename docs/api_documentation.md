# Elixir Backend API Documentation

## Overview

The Elixir Backend API provides both HTTP REST endpoints and WebSocket connections for interacting with the S7-200 PLC system controlling the hyperbaric chamber.

- **Base URL**: `http://localhost:8000`
- **WebSocket URL**: `ws://localhost:8000`
- **API Version**: 1.0.0
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Design Philosophy

- **HTTP Endpoints**: Used for user actions and one-time data requests
- **WebSocket Endpoints**: Used for real-time data streaming and live updates
- **RESTful Design**: Following standard HTTP methods and status codes
- **Consistent Responses**: All endpoints return standardized JSON responses

## Authentication & Security

Currently, the API operates without external authentication. Security is handled at the PLC level through the password system endpoints.

## Response Format

All HTTP endpoints return responses in this format:

```json
{
  "success": true,
  "data": {...},
  "message": "Operation completed",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## HTTP Endpoints

### Root & Health

#### `GET /`
Returns API information and available endpoints.

**Response:**
```json
{
  "message": "Elixir Backend API",
  "version": "1.0.0",
  "status": "operational",
  "docs": "/docs",
  "endpoints": {...}
}
```

#### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890,
  "service": "elixir-backend"
}
```

### Authentication/Password System

#### `POST /api/auth/show`
Show the password screen on the PLC interface.

**PLC Address**: `M12.4`

#### `POST /api/auth/proceed`
Proceed from password screen after authentication.

**PLC Address**: `M12.5`

#### `POST /api/auth/back`
Go back from password screen.

**PLC Address**: `M12.6`

#### `POST /api/auth/input`
Set password input value.

**PLC Address**: `VD654`

**Request Body:**
```json
{
  "password": 1234
}
```

#### `GET /api/auth/status`
Get current authentication status.

**Response:**
```json
{
  "success": true,
  "data": {
    "proceed_status": true,
    "change_pw_status": false,
    "user_pw": 1234,
    "admin_pw": 5678
  }
}
```

### Language Control

#### `POST /api/language/switch`
Switch between English and Chinese interface.

**PLC Address**: `M28.0`

#### `GET /api/language/current`
Get current language setting.

**Response:**
```json
{
  "success": true,
  "data": {
    "english": true,
    "chinese": false,
    "current": "english"
  }
}
```

### Control Panel

#### `POST /api/control/shutdown`
Trigger system shutdown.

**PLC Address**: `M1.6`

#### `POST /api/control/ac/toggle`
Toggle AC system on/off.

**PLC Address**: `M11.4`

#### `POST /api/control/lights/ceiling/toggle`
Toggle ceiling lights.

**PLC Address**: `M13.5`

#### `POST /api/control/lights/reading/toggle`
Toggle reading lights.

**PLC Address**: `M15.5`

#### `POST /api/control/intercom/toggle`
Toggle intercom system.

**PLC Address**: `M14.3`

#### `GET /api/control/status`
Get current control panel status.

**Response:**
```json
{
  "success": true,
  "data": {
    "ac_state": true,
    "ceiling_lights": false,
    "intercom": true,
    "reading_lights": false,
    "door_light": true,
    "shutdown_status": false
  }
}
```

### Pressure Control

#### `POST /api/pressure/add`
Add 10 to pressure setpoint.

**PLC Address**: `M1.4`

#### `POST /api/pressure/subtract`
Subtract 10 from pressure setpoint.

**PLC Address**: `M1.5`

#### `POST /api/pressure/setpoint`
Set pressure setpoint directly.

**PLC Address**: `VD512`

**Request Body:**
```json
{
  "setpoint": 1.5
}
```

#### `GET /api/pressure/current`
Get current pressure readings.

**Response:**
```json
{
  "success": true,
  "data": {
    "setpoint": 1.5,
    "internal_pressure_1": 1.45,
    "internal_pressure_2": 1.47
  }
}
```

### Session Control

#### `POST /api/session/start`
Start treatment session and begin pressurization.

**PLC Address**: `M3.0`

#### `POST /api/session/end`
End treatment session and begin depressurization.

**PLC Address**: `M3.1`

#### `POST /api/session/depressurize/confirm`
Confirm depressurization process.

**PLC Address**: `M15.2`

### Operating Modes

#### `POST /api/modes/set`
Set the operating mode and duration.

**Request Body:**
```json
{
  "mode": "health",
  "duration": 90
}
```

**Valid Modes:**
- `rest` - Rest mode (`M4.0`)
- `health` - Health mode (`M4.1`)
- `professional` - Professional mode (`M4.2`)
- `custom` - Custom mode (`M4.3`)
- `o2_100` - 100% O2 mode (`M4.4`)
- `o2_120` - 120 minute O2 mode (`M4.5`)

**Duration**: `VD682` (60-120 minutes)

#### `POST /api/modes/compression?mode={mode}`
Set compression mode.

**Valid Modes:**
- `beginner` - (`M5.0`)
- `normal` - (`M5.1`)
- `fast` - (`M5.2`)

#### `POST /api/modes/oxygen?mode={mode}`
Set oxygen delivery mode.

**Valid Modes:**
- `continuous` - (`M5.6`)
- `intermittent` - (`M15.0`)

### AC & Temperature Control

#### `POST /api/ac/mode?mode={mode}`
Set AC fan mode.

**Valid Modes:**
- `auto` - (`M11.0`)
- `low` - (`M11.1`)
- `mid` - (`M11.2`)
- `high` - (`M11.3`)

#### `POST /api/ac/temperature`
Set temperature setpoint.

**PLC Address**: `VD900`

**Request Body:**
```json
{
  "setpoint": 22.5
}
```

#### `POST /api/ac/heating-cooling/toggle`
Toggle between heating and cooling modes.

**PLC Address**: `M28.1`

### Sensor Readings

#### `GET /api/sensors/readings`
Get all current sensor readings.

**Response:**
```json
{
  "success": true,
  "data": {
    "current_temp": 22.5,
    "current_humidity": 45.2,
    "ambient_o2": 20.8,
    "ambient_o2_2": 20.9,
    "internal_pressure_1": 1.45,
    "internal_pressure_2": 1.47,
    "ambient_o2_check_flag": true
  }
}
```

### Calibration

#### `POST /api/calibration/pressure`
Start pressure sensor calibration.

**PLC Address**: `M1.1`

#### `POST /api/calibration/oxygen`
Start oxygen sensor calibration.

**PLC Address**: `M1.2`

### Manual Controls

#### `POST /api/manual/toggle`
Toggle manual mode on/off.

**PLC Address**: `M14.0`

#### `POST /api/manual/controls`
Set manual control values.

**Request Body:**
```json
{
  "control": "air_pump1",
  "value": true
}
```

**Available Controls:**
- `release_solenoid` - (`M13.4`)
- `air_pump1` - (`M13.6`)
- `air_pump2` - (`M13.7`)
- `oxygen_supply1` - (`M14.1`)
- `oxygen_supply2` - (`M13.7`)
- `release_solenoid_set` - (`VW82`) - Value range: 5530-27000

### System Status

#### `GET /api/status/system`
Get comprehensive system status.

**Response:**
```json
{
  "success": true,
  "data": {
    "session_status": {
      "equalise_state": false,
      "running_state": true,
      "pressuring_state": false,
      "stabilising_state": true,
      "stop_state": false,
      "depressurise_state": false
    },
    "timers": {
      "run_time_remaining_sec": 30,
      "run_time_remaining_min": 30
    },
    "shutdown_status": false,
    "ambient_o2_check": true
  }
}
```

## WebSocket Endpoints

### `/ws/live-data`
Real-time streaming of all system data.

**Update Frequency**: Every 1 second

**Message Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "sensors": {
    "current_temp": 22.5,
    "current_humidity": 45.2,
    "ambient_o2": 20.8,
    "ambient_o2_2": 20.9,
    "internal_pressure_1": 1.45,
    "internal_pressure_2": 1.47
  },
  "status": {
    "session_running": true,
    "pressuring": false,
    "stabilising": true,
    "depressurising": false,
    "ac_state": true,
    "ambient_o2_check": true
  },
  "timers": {
    "run_time_remaining_sec": 30,
    "run_time_remaining_min": 30,

  },
  "setpoints": {
    "pressure": 1.5,
    "temperature": 22.5
  }
}
```

### `/ws/pressure`
Real-time pressure data streaming.

**Update Frequency**: Every 0.5 seconds

**Message Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "setpoint": 1.5,
  "internal_pressure_1": 1.45,
  "internal_pressure_2": 1.47,
  "pressuring_state": false,
  "stabilising_state": true,
  "depressurise_state": false
}
```

### `/ws/sensors`
Real-time sensor data streaming.

**Update Frequency**: Every 2 seconds

**Message Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "temperature": 22.5,
  "humidity": 45.2,
  "ambient_o2": 20.8,
  "ambient_o2_2": 20.9,
  "ambient_o2_check": true
}
```

## Error Handling

### HTTP Status Codes

- `200` - Success
- `400` - Bad Request (invalid parameters)
- `500` - Internal Server Error (PLC communication error)
- `503` - Service Unavailable (PLC not connected)

### Error Response Format

```json
{
  "success": false,
  "message": "Error description",
  "error": "Detailed error information"
}
```

## Usage Examples

### JavaScript/Browser

```javascript
// HTTP API Usage
async function getPressure() {
  const response = await fetch('/api/pressure/current');
  const data = await response.json();
  console.log('Pressure:', data.data.setpoint);
}

async function startSession() {
  const response = await fetch('/api/session/start', {
    method: 'POST'
  });
  const result = await response.json();
  console.log('Session started:', result.success);
}

// WebSocket Usage
const ws = new WebSocket('ws://localhost:8000/ws/live-data');
ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Live data:', data);
};
```

### Python Client

```python
import requests
import asyncio
import websockets
import json

# HTTP Usage
response = requests.get('http://localhost:8000/api/sensors/readings')
data = response.json()
print('Temperature:', data['data']['current_temp'])

# WebSocket Usage
async def listen_to_live_data():
    uri = "ws://localhost:8000/ws/live-data"
    async with websockets.connect(uri) as websocket:
        async for message in websocket:
            data = json.loads(message)
            print('Pressure:', data['sensors']['internal_pressure_1'])

asyncio.run(listen_to_live_data())
```

### cURL Examples

```bash
# Get sensor readings
curl http://localhost:8000/api/sensors/readings

# Start session
curl -X POST http://localhost:8000/api/session/start

# Set pressure setpoint
curl -X POST http://localhost:8000/api/pressure/setpoint \
     -H "Content-Type: application/json" \
     -d '{"setpoint": 1.5}'

# Toggle AC
curl -X POST http://localhost:8000/api/control/ac/toggle
```

## Development & Testing

### Running the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Environment Configuration

Create a `.env` file:

```env
PLC_IP=192.168.1.100
PLC_LOCALTSAP=0x0100
PLC_REMOTETSAP=0x0200
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### Testing

```bash
# Run the demo client
python examples/api_client_demo.py

# Test with pytest
pytest tests/
```

## Logging

The API includes comprehensive logging for all operations:

- **HTTP requests** - Method, path, status code, timing
- **PLC operations** - Read/write operations with addresses and values
- **WebSocket connections** - Connection/disconnection events
- **Errors** - Detailed error information with context

Logs are structured and include contextual information for easy debugging and monitoring.

## Production Considerations

1. **Security**: Implement proper authentication and CORS policies
2. **Rate Limiting**: Add rate limiting for API endpoints
3. **Load Balancing**: Use reverse proxy for multiple instances
4. **Monitoring**: Set up monitoring and alerting
5. **SSL/TLS**: Use HTTPS in production
6. **Error Handling**: Implement circuit breakers for PLC connections
7. **Backup**: Implement connection failover strategies

## Support

For support and questions:
- Check the interactive API docs at `/docs`
- Review the example client code in `examples/`
- Check logs for detailed error information
- Ensure PLC connectivity and address mappings are correct 
