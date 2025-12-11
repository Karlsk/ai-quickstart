#!/bin/bash

# FastAPI 服务器启动脚本

echo "=================================================="
echo "Dynamic Workflow Management API"
echo "=================================================="
echo ""

cd "$(dirname "$0")"

# 检查 Python 环境
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed"
    exit 1
fi

echo "Starting FastAPI server..."
echo ""
echo "API Documentation: http://localhost:8000/docs"
echo "ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
