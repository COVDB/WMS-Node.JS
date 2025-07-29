# Stow WMS Mobile Racking TCP-IP Communication

A professional Python Streamlit application for TCP-IP communication with **Stow Mobile Racking systems**. This application provides an advanced, user-friendly interface for communicating with WMS (Warehouse Management System) via TCP-IP protocol, featuring the complete **Stow Group** branding and styling.

![Stow Logo](stow_logo.jpg)

## Features

- 🔌 **Professional TCP-IP Communication** on port 2000/2001
- 📊 **Real-time Status Monitoring** of Stow Mobile Racking systems
- 🎛️ **Interactive Streamlit Interface** with modern Stow branding
- 📈 **Advanced Data Visualization** of system parameters
- 🔄 **Comprehensive Command Interface** for Mobile Racking controller
- 📋 **Professional Status Logging** and history tracking
- 💻 **Multi-Language Protocol Generator** - Generate code in Node.js, C#, Ruby, JavaScript, Python
- 🧪 **Manual Test Command Field** - Test custom commands directly
- 🔍 **Advanced Diagnostics Suite** - Network scanning and troubleshooting tools
- 🎨 **Complete Stow Group Branding** - Professional interface design

## TCP-IP Protocol Details

- **IP Address**: 1.1.1.2 (default, configurable)
- **Port**: 2000 (default) - **⚠️ See troubleshooting section**
- **Request size**: 2 bytes
- **Response size**: 20 bytes
- **Data structure**: According to WMS-Data specification

## Troubleshooting

### Common connection problems:

#### ❌ "Connection refused" on port 2000
**Cause:** Mobile Racking TCP-IP service not running on the PLC  
**Solution:**
1. Contact PLC technician
2. Check if Mobile Racking software is active
3. Activate TCP-IP communication module
4. Verify port configuration

#### ✅ Alternative ports found
If port scan shows ports 102, 2001, or 4840:
- **Port 102**: Siemens S7 PLC communication
- **Port 2001**: Possible alternative service
- **Port 4840**: OPC UA server

#### 🔍 Diagnostic tools available:
```bash
# Full diagnosis
python diagnose_plc.py

# Port scanning  
python port_scanner.py

# Basic connectivity test
python test_connection.py
```

## Installation

### Requirements
- Python 3.8 or higher
- Streamlit
- Pandas

### Setup

1. Clone the repository:
```bash
git clone https://github.com/COVDB/WMS-Node.JS.git
cd WMS-Node.JS
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Start the application:
```bash
streamlit run app.py
```

## Usage

1. **Configuration**: Set IP address and port via the sidebar
2. **Navigation**: Use sidebar to select:
   - 📊 **Dashboard**: Real-time monitoring and status overview
   - 🎛️ **Controls**: System operations and lighting control
   - 🔍 **Diagnostics**: Network scanning and troubleshooting
   - 💻 **Code Generator**: Multi-language protocol code generation
3. **Connect**: Click "Connect" to establish connection  
4. **Commands**: Use the interface to send commands
5. **Monitoring**: View real-time status updates

### 💻 Multi-Language Code Generator

The app now includes a powerful code generator that creates TCP-IP communication code in multiple programming languages:

**Supported Languages:**
- **Node.js** - Built-in `net` module, works with Node.js v12+
- **C#** - .NET Core/Framework with `System.Net.Sockets`
- **Ruby** - Built-in `socket` library  
- **JavaScript** - Browser-based with WebSocket proxy
- **Python** - Built-in `socket` library

**Features:**
- Complete working examples
- Connection-only code snippets
- Command sending code
- Response parsing utilities
- Manual command testing
- Downloadable files with correct extensions

**Usage Example:**
1. Navigate to "💻 Code Generator" 
2. Select programming language
3. Configure host/port settings
4. Choose code type (complete example recommended)
5. Click "Generate Code"
6. Download or copy the generated code
7. Use the manual test field for custom commands

## Project Structure

```
WMS-Node.JS/
├── app.py                 # Main Streamlit application
├── tcp_client.py          # TCP-IP communication module
├── wms_protocol.py        # WMS protocol definition
├── protocol_generators.py # Multi-language code generators
├── demo.py               # Demo and testing script
├── diagnose_plc.py       # Advanced PLC diagnostics
├── port_scanner.py       # Network port scanning utility
├── test_connection.py    # Basic connection testing
├── utils/
│   ├── __init__.py
│   ├── data_parser.py     # Data parsing utilities
│   └── logger.py          # Logging utilities
├── examples/             # Generated code examples
│   ├── wms_client_nodejs.js
│   └── wms_client_csharp.cs
├── logs/                 # Application logs
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── LICENSE              # MIT License
```

## WMS Data Structure

The system uses a defined data structure for communication:

- **Command Request**: 2-byte commands
- **Status Response**: 20-byte status information
- **Data Types**: Bool, Byte, DWord according to specification

## Development

### Local development

```bash
# Start development server
streamlit run app.py

# Run with debug mode
streamlit run app.py --logger.level=debug
```

### Testing

```bash
# Run tests (when available)
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the project
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Support

For questions and support, create an issue on GitHub or contact via [support@covdb.com](mailto:support@covdb.com).

## Changelog

### [1.0.0] - 2025-07-29
- Initial release
- TCP-IP communication implementation
- Streamlit interface
- WMS protocol support
