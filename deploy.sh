#!/bin/bash
# 24x7 Telegram Bot One-Click Deployment Script
set -e

echo "=== Deploying 24x7 Telegram Job Broadcaster ==="

# Check if Docker is installed
if command -v docker &> /dev/null && command -v docker compose &> /dev/null; then
    echo "Docker detected. Starting with Docker Compose..."
    docker compose up -d --build
    echo "Bot is running 24x7 in background container (telegram_job_bot)!"
    echo "View live logs with: docker compose logs -f"
else
    echo "Setting up Python virtual environment..."
    python3 -m venv venv || python -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
    
    echo "Running unit test suite..."
    ./venv/bin/python -m unittest test_suite.py
    
    echo "Starting bot in background..."
    nohup ./venv/bin/python bot.py > bot.log 2>&1 &
    echo "Bot started with PID $! - Running 24x7!"
    echo "View live logs with: tail -f bot.log"
fi
