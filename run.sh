#!/bin/bash

# VitalFlow AI - Start All Services
# This script starts all VitalFlow AI services

echo "=========================================="
echo "       VitalFlow AI - Neon Cortex        "
echo "=========================================="
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "Error: Streamlit is not installed."
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Parse command line arguments
SERVICE="main"
PORT=8501

while [[ $# -gt 0 ]]; do
    case $1 in
        --admin)
            SERVICE="admin"
            shift
            ;;
        --staff)
            SERVICE="staff"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --admin     Start only the Admin Dashboard"
            echo "  --staff     Start only the Staff Mobile Interface"
            echo "  --port NUM  Set the port number (default: 8501)"
            echo "  --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run.sh              # Start main app (homepage + routing)"
            echo "  ./run.sh --admin      # Start admin dashboard directly"
            echo "  ./run.sh --staff      # Start staff mobile directly"
            echo "  ./run.sh --port 8502  # Start on port 8502"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Start the appropriate service
case $SERVICE in
    "admin")
        echo "Starting Admin Dashboard on port $PORT..."
        echo "URL: http://localhost:$PORT"
        echo ""
        streamlit run frontend/admin_dashboard/app.py --server.port $PORT
        ;;
    "staff")
        echo "Starting Staff Mobile Interface on port $PORT..."
        echo "URL: http://localhost:$PORT"
        echo ""
        streamlit run frontend/staff_mobile/app.py --server.port $PORT
        ;;
    *)
        echo "Starting VitalFlow AI on port $PORT..."
        echo "URL: http://localhost:$PORT"
        echo ""
        echo "Demo Credentials:"
        echo "  Admin:   admin@vitalflow.ai / admin123"
        echo "  Doctor:  doctor@vitalflow.ai / doctor123"
        echo "  Nurse:   nurse@vitalflow.ai / nurse123"
        echo ""
        streamlit run main.py --server.port $PORT
        ;;
esac
