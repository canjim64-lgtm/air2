# AirOne Professional v4.0 - Complete User Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [CLI Commands](#cli-commands)
3. [GUI Features](#gui-features)
4. [Report Generation](#report-generation)
5. [DeepSeek Integration](#deepseek-integration)
6. [Data Processing](#data-processing)
7. [Module Reference](#module-reference)

---

## Quick Start

### Installation
```bash
cd air2_source
pip install -r requirements.txt
python main_launch.py
```

### First Launch
```bash
$ python main_launch.py
╔═══════════════════════════════════════════════════════════════╗
║     ██████╗ ███████╗ █████╗ ██████╗                         ║
║     ██╔══██╗██╔════╝██╔══██╗██╔══██╗                        ║
║     ██████╔╝█████╗  ███████║██║  ██║                        ║
║     ██╔══██╗██╔══╝  ██╔══██║██║  ██║                        ║
║     ██║  ██║███████╗██║  ██║██████╔╝                        ║
║     ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝                         ║
║                    v4.0 CLI Edition                           ║
╚═══════════════════════════════════════════════════════════════╝

airone> help
```

---

## CLI Commands

### System Commands
```bash
airone> help          # Show all commands
airone> status        # System status
airone> install       # Install AirOne
airone> uninstall    # Uninstall AirOne
airone> report        # Generate report
airone> settings     # Open settings
airone> q            # Quit
```

### Operating Modes
```bash
airone> 1   # Desktop GUI (Qt5)
airone> 2   # Simulation Mode
airone> 3   # CLI Mode (Headless)
airone> 4   # Security Mode
airone> 5   # Offline Mode
airone> 6   # Web Dashboard
airone> 7   # REST API Server
airone> 8   # Scheduler
airone> 9   # Health Monitor
airone> d   # Database Mode
```

### Feature Modules
```bash
airone> b   # Backup Manager
airone> c   # Cloud Integration
airone> f   # Flight Control
airone> m   # Mapping & GIS
airone> n   # Mission Planning
airone> p   # Plugin Manager
airone> w   # Weather Service
airone> v   # Voice Assistant
airone> t   # Telemetry Analyzer
airone> e   # Error Handler
airone> x   # Radio/SDR System
airone> y   # Notifications
airone> z   # Compliance & Audit
airone> o   # Performance Optimizer
```

### Data Processing Commands
```bash
airone> dp     # Data Processing Pipeline
airone> ai     # AI Processing
airone> ml     # Machine Learning
airone> fp     # Fusion Processing
airone> sa     # Scientific Analysis
airone> ap     # Advanced Pipeline
```

### System Monitoring
```bash
airone> status   # System status (CPU, Memory, Disk)
airone> monitor  # Process monitor
airone> logs     # View system logs
airone> config   # Configuration editor
airone> perf     # Performance metrics
```

### Advanced
```bash
airone> sec  # Security Audit
airone> db   # Database Query
airone> tst  # System Test
```

---

## GUI Features

### Desktop GUI Tabs
1. **Dashboard** - System overview with live charts
2. **Telemetry** - Real-time flight data
3. **Mapping** - GPS and GIS visualization
4. **AI Processing** - DeepSeek and ML
5. **Mission Planner** - Waypoint management
6. **Weather** - Atmospheric conditions
7. **Security** - Threat monitoring
8. **Reports** - Report generation
9. **Settings** - Configuration
10. **DeepSeek** - AI assistant

### GUI Launch
```bash
airone> 1
# Opens PyQt5 window with 10 tabs
```

---

## Report Generation

### CLI Report
```bash
airone> report
# Generates system report
```

### GUI Report
- Navigate to **Reports** tab
- Select report type:
  - Flight Report
  - Mission Summary
  - System Health
  - Security Audit
  - Performance Analysis
- Click "Generate Report"
- Export as PDF/HTML/CSV

### Report Types
```python
from reports.enhanced_report_generator import ReportGeneratorGUI
gui = ReportGeneratorGUI()
gui.show()
```

---

## DeepSeek Integration

### DeepSeek R1 8B INT
- Quantum-enhanced AI model
- Located in `src/ai/deepseek_integration.py`

### Features
- Natural language processing
- Code generation
- Data analysis
- Autonomous decision making

### Check Status
```bash
airone> k   # or from menu: DeepSeek Status
```

### GUI DeepSeek Tab
- Navigate to **DeepSeek** tab in GUI
- Chat interface for AI queries
- Real-time response processing

---

## Data Processing

### Processing Pipeline
```
Input → Validation → Processing → Output
```

### CLI Data Processing
```bash
airone> dp
# Shows data processing pipeline with progress
# - Input validation
# - Data transformation
# - AI analysis
# - Results output
```

### Processing Modules

#### 1. Data Pipeline (`data_processing/`)
```bash
# Batch processing
from data_processing.batch_processor import BatchProcessor
bp = BatchProcessor()
bp.process()
```

#### 2. Data Export (`data_export/`)
```bash
# Export to multiple formats
from data_export.data_exporter import DataExporter
exporter = DataExporter()
exporter.export_csv()
exporter.export_json()
exporter.export_excel()
```

#### 3. Scientific Processing (`scientific/`)
```bash
# Scientific data analysis
from scientific.data_analyzer import DataAnalyzer
analyzer = DataAnalyzer()
analyzer.analyze()
```

#### 4. Pipeline (`pipeline/`)
```bash
# Advanced pipeline processing
from pipeline.data_pipeline import DataPipeline
pipeline = DataPipeline()
pipeline.run()
```

---

## Module Reference

### Core Modules
| Module | Description | Command |
|--------|-------------|---------|
| `database/` | SQLite database | `d` |
| `backup/` | Backup management | `b` |
| `cloud/` | Cloud integration | `c` |

### AI Modules
| Module | Description | Command |
|--------|-------------|---------|
| `ai/` | Complete AI System | `ai` |
| `ml/` | Machine Learning | `ml` |
| `deepseek/` | DeepSeek R1 | `k` |

### Processing Modules
| Module | Description | Command |
|--------|-------------|---------|
| `data_processing/` | Batch processing | `dp` |
| `data_export/` | Export tools | - |
| `pipeline/` | Pipeline | `fp` |
| `scientific/` | Scientific analysis | - |

### System Modules
| Module | Description | Command |
|--------|-------------|---------|
| `scheduler/` | Task scheduling | `8` |
| `monitoring/` | Health monitoring | `9` |
| `notifications/` | Alert system | `y` |

---

## Configuration

### Settings File
```bash
airone> settings
# Opens configuration menu
```

### Database Location
```
air2_source/src/data/database/airone.db
```

### Logs Location
```
air2_source/src/logs/
```

---

## Troubleshooting

### Common Issues

#### Module Not Found
```bash
# Install dependencies
pip install -r requirements.txt
```

#### Database Error
```bash
# Check database file exists
ls air2_source/src/data/database/
```

#### GUI Not Opening
```bash
# Install PyQt5
pip install PyQt5
```

---

## Support

### Getting Help
```bash
airone> help
# Shows all available commands
```

### System Status
```bash
airone> status
# Shows version, modules loaded, database status
```

---

*AirOne Professional v4.0 - CLI Edition*
*All features integrated and working*