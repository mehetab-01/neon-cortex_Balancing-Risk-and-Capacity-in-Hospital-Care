# VitalFlow AI - Intelligent Hospital Management System

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> An intelligent hospital command center providing real-time monitoring, bed management, and AI-driven decision support for hospital administrators and clinical staff.

## Overview

**VitalFlow AI** is designed to balance risk assessment and capacity management in hospital care through an integrated dashboard with visual analytics and intelligent recommendations. Built during a 10-hour hackathon, this project emphasizes rapid prototyping, visual impact, and clean architecture for seamless backend integration.

## Features

- **Real-Time Statistics Dashboard** - Live monitoring of hospital metrics and KPIs
- **Visual Floor Map** - Color-coded patient status visualization for quick assessment
- **Multi-Hospital Network Mapping** - Manage and monitor multiple facilities from a single interface
- **AI Decision Support** - Intelligent recommendations with full transparency logging
- **Modular Architecture** - Reusable components designed for scalability
- **Multiple Data Source Modes** - Support for mock data, API integration, and JSON sources

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.9+ | Core programming language |
| Streamlit 1.28+ | Web framework for dashboard |
| Pydantic | Data validation and models |
| RESTful API | Backend communication |
| WebSocket | Real-time updates |

## Project Structure

```
neon-cortex_Balancing-Risk-and-Capacity-in-Hospital-Care/
├── frontend/
│   ├── admin_dashboard/      # Administrator/Dean dashboard interface
│   └── staff_mobile/         # Mobile interface for clinical staff
├── backend/
│   ├── core_logic/           # Business rules and workflows
│   └── ai_services/          # Machine learning and decision support
├── shared/                   # Reusable modules (models, constants, mock data)
├── simulation/               # Demo and testing environment
├── VitalFlow/                # Primary application code
├── .devcontainer/            # Development environment configuration
├── config/                   # Configuration files
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── run.sh                    # Startup script
├── DASHBOARD_README.md       # Dashboard-specific documentation
└── GOOGLE_AUTH_SETUP.md      # Authentication configuration guide
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/mehetab-01/neon-cortex_Balancing-Risk-and-Capacity-in-Hospital-Care.git
   cd neon-cortex_Balancing-Risk-and-Capacity-in-Hospital-Care
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   # Using Python
   python main.py

   # Or using the startup script
   ./run.sh
   ```

5. **Access the dashboard**

   Open your browser and navigate to `http://localhost:8501`

## Configuration

The application supports multiple configuration modes:

| Mode | Description |
|------|-------------|
| `mock` | Uses simulated data for demo purposes |
| `api` | Connects to a live backend API |
| `json` | Loads data from JSON files |

Configuration files are located in the `config/` directory.

## API Integration

VitalFlow AI provides RESTful endpoints with WebSocket support for real-time updates. For detailed API contracts and integration guidelines, refer to the backend documentation.

### Example API Endpoints

```
GET  /api/v1/patients          # Retrieve patient list
GET  /api/v1/beds/status       # Get bed availability
POST /api/v1/ai/recommend      # Get AI recommendations
WS   /ws/realtime              # WebSocket for live updates
```

## Usage

### Admin Dashboard

The admin dashboard provides hospital administrators with:
- Overview of hospital capacity and occupancy
- Risk assessment metrics
- AI-driven recommendations for resource allocation
- Historical data analysis and trends

### Staff Mobile Interface

Clinical staff can access:
- Patient status updates
- Bed assignment notifications
- Quick action items
- Real-time alerts

## Development

### Setting Up Development Environment

1. Use the provided `.devcontainer/` configuration for VS Code Dev Containers
2. Run tests from the `simulation/` directory
3. Follow the coding standards outlined in the project

### Running in Development Mode

```bash
streamlit run main.py --server.runOnSave true
```

## Team

Built by the **Neon Cortex** team with specialized roles:

- Frontend Development
- Mobile Interface Design
- Backend Logic
- AI Services
- Simulation & Demonstration

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built during a 10-hour hackathon
- Designed with scalability and real-world hospital workflows in mind
- Special thanks to all contributors and mentors

---

<p align="center">
  <strong>VitalFlow AI</strong> - Balancing Risk and Capacity in Hospital Care
</p>
