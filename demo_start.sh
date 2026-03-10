#!/bin/bash
# Quick Demo Start Script

echo "🎯 OpenClaw Mission Control - Demo Mode Quick Start"
echo "=================================================="

echo ""
echo "🚀 Starting Demo Environment..."
echo ""

# Check if services are running
echo "1. Checking backend status..."
if curl -s http://localhost:8000/healthz > /dev/null; then
    echo "   ✅ Backend is running"
else
    echo "  ❌ Backend not running - starting..."
    cd backend && uv run uvicorn app.main:app --reload --port 8000 &
    sleep 5
fi

echo ""
echo "2. Checking frontend status..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "   ✅ Frontend is running"
else
    echo "   ❌ Frontend not running - starting..."
    cd frontend && npm run dev &
    sleep 5
fi

echo ""
echo "3. Verifying demo mode..."
if [ -f "frontend/.env" ] && grep -q "NEXT_PUBLIC_DEMO_MODE=true" frontend/.env; then
    echo "   ✅ Demo mode is enabled"
else
    echo "  ⚠  Demo mode not enabled - enabling..."
    echo "NEXT_PUBLIC_DEMO_MODE=true" >> frontend/.env
fi

echo ""
echo "4. Opening Mission Control..."
echo "  🌐 Access URLs:"
echo "   - Local:  http://localhost:3000"
echo "   - Network: http://192.168.29.250:3000"
echo ""
echo "   🎯 Demo Features:"
echo "   - No login required"
echo "   - Yellow banner shows 'Demo Mode Active'"
echo "   - Pre-authenticated with valid token"
echo ""

# Open browser (cross-platform)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000
elif command -v open > /dev/null; then
    open http://localhost:3000
elif command -v start > /dev/null; then
    start http://localhost:3000
fi

echo "✅ Demo environment is ready!"
echo "Look for the yellow 'Demo Mode Active' banner at the top of the page."
echo ""
echo "📋 Next steps:"
echo "1. Explore the Activity Feed"
echo "2. Visit your 'Mr. Happy Digital CEO Board'"
echo "3. Check the Agents dashboard"
echo "4. Try creating a test task"
echo ""
echo "🔧 For troubleshooting, check:"
echo "- Browser console (F12)"
echo "- Backend logs in terminal"
echo "- Demo mode banner visibility"