# AirOne Professional v4.0 - User Guide
## Ultimate Unified Edition

Welcome to AirOne Professional, the most advanced CanSat ground station and drone management system.

### 🚀 Getting Started

To launch the application, simply run:
```bash
AirOne_Run.bat
```

Or via command line:
```bash
python airone.py
```

### 🛠️ Key Features

- **Unified Mode System**: Choose from 14 operational modes, ranging from Desktop GUI to Cosmic Fusion Mode.
- **AI-Powered Analysis**: Integrated `UnifiedAIService` providing real-time telemetry anomaly detection and predictive maintenance.
- **Mission Orchestration**: New "CanSat Mission Mode" specifically designed for full mission lifecycles (Launch -> Ascent -> Descent -> Landing).
- **Simulation Suite**: High-fidelity flight data simulator for Hardware-In-the-Loop (HIL) and Software-In-the-Loop (SIL) testing.
- **Enterprise Security**: Enhanced security with JWT-based authentication, role-based access control, and password rotation.

### 🚁 Running a CanSat Mission

1. Launch `airone.py`.
2. Select **Mode 14: CanSat Mission Mode** from the main menu.
3. The system will initialize the AI service and flight simulator.
4. Watch real-time telemetry as the AI detects anomalies and tracks mission phases.
5. After landing, a final mission analysis report will be generated and saved to `logs/mission_ledger.json`.

### 🖥️ Desktop GUI

To launch the full graphical interface:
```bash
python airone.py --gui
```
*Note: Requires PyQt5 installed.*

### 🔍 System Requirements

- **Python**: 3.8 or higher.
- **RAM**: 8GB recommended.
- **Packages**: See `requirements.txt`.

### 📄 Credits
Developed by the AirOne Team © 2026.
v4.0 Ultimate Unified Edition.
