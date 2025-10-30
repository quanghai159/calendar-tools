#!/bin/bash

echo "🚀 Starting Calendar Tools System..."

# Tạo thư mục logs nếu chưa có
mkdir -p logs

# Chạy web app trong background
echo "📱 Starting Web Application..."
python3 frontend/app.py > logs/web_app.log 2>&1 &
WEB_PID=$!

# Chờ 3 giây để web app khởi động
sleep 3

# Chạy auto notification runner trong background
echo "⏰ Starting Auto Notification Runner..."
python3 auto_notification_runner.py > logs/notification_runner.log 2>&1 &
RUNNER_PID=$!

echo "✅ System started successfully!"
echo "📱 Web App: http://localhost:5000"
echo "📊 Web App PID: $WEB_PID"
echo "⏰ Notification Runner PID: $RUNNER_PID"
echo "📝 Logs: logs/web_app.log, logs/notification_runner.log"
echo ""
echo "Press Ctrl+C to stop all services..."

# Function để dừng tất cả services
cleanup() {
    echo ""
    echo "⏹️  Stopping all services..."
    kill $WEB_PID 2>/dev/null
    kill $RUNNER_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Chờ
wait