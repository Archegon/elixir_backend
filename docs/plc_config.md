# PLC Address Configuration System

This system allows you to easily manage and modify PLC memory addresses without changing the code. All addresses are stored in a structured JSON configuration file.

## 📁 Configuration File

The main configuration file is located at: **`config/plc_addresses.json`**

### Structure

The configuration follows this hierarchical structure:

```
Category
├── Function
    ├── address (the PLC memory address)
    └── comment (description of what this address does)
```

### Example

```json
{
  "pressure_control": {
    "internal_pressure_1": {
      "address": "VD504",
      "comment": "Internal pressure sensor 1"
    },
    "pressure_setpoint": {
      "address": "VD512", 
      "comment": "Pressure setpoint value"
    }
  }
}
```

## 🔧 How to Change Addresses

### Example: Change internal_pressure_1 from VD504 to VD200

1. Open `config/plc_addresses.json`
2. Find the `pressure_control` category
3. Locate `internal_pressure_1`
4. Change the address:

```json
"internal_pressure_1": {
  "address": "VD200",  // ← Changed from VD504 to VD200
  "comment": "Internal pressure sensor 1"
}
```

4. Save the file
5. Restart the API server or call the reload endpoint: `POST /api/config/reload`

**That's it!** The API will now use VD200 instead of VD504 for internal pressure readings.

## 📋 Available Categories

### 🔐 authentication
- Password system controls
- User/admin authentication
- Password input handling

### 🌐 language  
- Language switching (English/Chinese)
- Language status indicators

### 🎛️ control_panel
- System shutdown controls
- AC, lights, intercom controls
- Door controls

### 📊 pressure_control
- Pressure setpoint and readings
- Pressure control buttons
- Internal pressure sensors

### ⚡ session_control
- Session start/stop controls
- Session state indicators
- Depressurization controls

### 🎯 operating_modes
- Treatment modes (rest, health, professional, custom)
- Compression modes (beginner, normal, fast)
- Oxygen delivery modes (continuous, intermittent)
- Session duration settings

### 🌡️ temperature_control
- AC fan modes (auto, low, mid, high)
- Temperature setpoint
- Heating/cooling toggle

### 📡 sensors
- Temperature and humidity readings
- Oxygen level sensors
- Sensor status flags

### ⚙️ calibration
- Pressure sensor calibration
- Oxygen sensor calibration

### 🔧 manual_controls
- Manual mode toggle
- Manual control of pumps, solenoids, oxygen supply

### ⏱️ timers
- Runtime counters
- Session timers
- Total operation counters

## 🛠️ Configuration Management Tools

### API Endpoints

The API provides endpoints for configuration management:

#### `GET /api/config/addresses`
Get all configured addresses

#### `POST /api/config/reload` 
Reload configuration from file (useful after making changes)

#### `GET /api/config/search/{address}`
Search for functions using a specific address

### Examples

```bash
# Get all addresses
curl http://localhost:8000/api/config/addresses

# Search for address VD504
curl http://localhost:8000/api/config/search/VD504

# Reload configuration after changes
curl -X POST http://localhost:8000/api/config/reload
```

## 🔍 Common Use Cases

### 1. Changing Pressure Sensor Address

**Before:**
```json
"internal_pressure_1": {
  "address": "VD504",
  "comment": "Internal pressure sensor 1"
}
```

**After:**
```json
"internal_pressure_1": {
  "address": "VD200", 
  "comment": "Internal pressure sensor 1"
}
```

### 2. Adding New Address

Add a new function to any category:

```json
"pressure_control": {
  "new_pressure_sensor": {
    "address": "VD600",
    "comment": "New pressure sensor for chamber 2"
  }
}
```

### 3. Changing Control Button Address

**Before:**
```json
"pressure_add_button": {
  "address": "M1.4",
  "comment": "Adds 10 to pressure"
}
```

**After:**
```json
"pressure_add_button": {
  "address": "M2.0",
  "comment": "Adds 10 to pressure"  
}
```

## ⚠️ Important Notes

### Address Format
- **Bit addresses**: `M1.4`, `V0.1` (Memory.Bit)
- **Byte addresses**: `VB100`, `MB10` 
- **Word addresses**: `VW82`, `MW20`
- **Double word addresses**: `VD504`, `MD100`

### Best Practices

1. **Always validate** after making changes:
   ```bash
   python tools/config_manager.py --validate
   ```

2. **Check for duplicates** to avoid conflicts:
   ```bash
   python tools/config_manager.py --duplicates
   ```

3. **Test changes** with a single address first

4. **Backup** the configuration file before major changes

5. **Document** any custom addresses in the comments

### Testing Changes

1. Make the address change in `config/plc_addresses.json`
2. Restart the API server or call the reload endpoint: `POST /api/config/reload`
3. Test the affected API endpoints

## 🔄 Hot Reloading

The system supports hot reloading of configuration changes:

1. Edit `config/plc_addresses.json`
2. Call the reload API: `POST /api/config/reload`
3. Changes take effect immediately without restarting the server

## 🚨 Troubleshooting

### Configuration Not Loading
- Check JSON syntax is valid
- Ensure file path is correct
- Check file permissions

### Address Not Found Errors
- Verify the category and function names are correct
- Check for typos in the configuration file

### Duplicate Address Warnings
- Manually review the configuration file for duplicate addresses
- Resolve conflicts by using unique addresses

### API Not Reflecting Changes
- Call the reload endpoint: `POST /api/config/reload`
- Check server logs for configuration errors
- Restart the API server as a last resort

## 📖 Integration with Your Code

To use addresses in your code:

```python
from modules.plc_config import Addresses

# Easy access to addresses
pressure_addr = Addresses.pressure("internal_pressure_1")  # Returns "VD504"
temp_addr = Addresses.sensors("current_temperature")       # Returns "VD408"

# Or use the full config
from modules.plc_config import get_address
address = get_address("pressure_control", "internal_pressure_1")
```

This system makes it easy to maintain and modify PLC addresses without touching the codebase! 