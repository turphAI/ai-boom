#!/bin/bash

# Complete System Startup Script for Boom-Bust Sentinel
# This script ensures the entire system is properly configured and running

set -e

echo "🚀 Starting Boom-Bust Sentinel Complete System..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -d "dashboard" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Step 1: Check Python environment
print_status "Checking Python environment..."
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

source venv/bin/activate
print_success "Python virtual environment activated"

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed"

# Step 2: Check Node.js environment for dashboard
print_status "Checking Node.js environment..."
cd dashboard

if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing..."
    npm install
fi

print_success "Node.js dependencies ready"

# Step 3: Check environment configuration
print_status "Checking environment configuration..."

if [ ! -f ".env.local" ]; then
    print_warning "Environment file not found. Creating from example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env.local
        print_warning "Please update .env.local with your actual database credentials"
    else
        print_error "No .env.example file found. Please create .env.local manually"
        exit 1
    fi
fi

# Check if DATABASE_URL is set
if ! grep -q "DATABASE_URL=mysql://" .env.local; then
    print_warning "DATABASE_URL not configured in .env.local"
    print_status "You can either:"
    print_status "1. Set up a local MySQL database"
    print_status "2. Configure PlanetScale database"
    print_status "3. Run: ./scripts/setup-local-database.sh"
fi

print_success "Environment configuration checked"

# Step 4: Setup database
print_status "Setting up database..."

# Check if database is accessible
if npm run db:push > /dev/null 2>&1; then
    print_success "Database schema is up to date"
else
    print_warning "Database setup failed. This might be due to:"
    print_warning "1. Missing database credentials in .env.local"
    print_warning "2. Database server not running"
    print_warning "3. Network connectivity issues"
    
    read -p "Do you want to set up a local database? (y/n): " setup_local
    if [ "$setup_local" = "y" ] || [ "$setup_local" = "Y" ]; then
        ./scripts/setup-local-database.sh
    else
        print_warning "Skipping database setup. Some features may not work."
    fi
fi

# Step 5: Generate initial data if needed
print_status "Checking for existing data..."

cd ..
if [ ! -d "data" ] || [ -z "$(ls -A data/*.json 2>/dev/null)" ]; then
    print_warning "No data files found. Running scrapers to generate initial data..."
    
    # Run scrapers to generate initial data
    python scripts/run_all_scrapers_safe.py
    
    if [ $? -eq 0 ]; then
        print_success "Initial data generated successfully"
    else
        print_warning "Some scrapers failed, but continuing with available data"
    fi
else
    print_success "Data files found"
fi

# Step 6: Test system health
print_status "Testing system health..."

# Start dashboard in background for testing
cd dashboard
npm run dev > /dev/null 2>&1 &
DASHBOARD_PID=$!

# Wait for dashboard to start
sleep 10

# Test dashboard health endpoint
if curl -s http://localhost:3000/api/system/health > /dev/null; then
    print_success "Dashboard is running and healthy"
else
    print_warning "Dashboard health check failed"
fi

# Stop background dashboard
kill $DASHBOARD_PID 2>/dev/null || true

print_success "System health check completed"

# Step 7: Create startup scripts
print_status "Creating convenient startup scripts..."

cd ..

# Create Python scraper startup script
cat > start_scrapers.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python scripts/run_all_scrapers_safe.py
EOF
chmod +x start_scrapers.sh

# Create dashboard startup script
cat > start_dashboard.sh << 'EOF'
#!/bin/bash
cd dashboard
npm run dev
EOF
chmod +x start_dashboard.sh

# Create full system startup script
cat > start_full_system.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Boom-Bust Sentinel Full System..."

# Start dashboard in background
cd dashboard
npm run dev &
DASHBOARD_PID=$!

# Go back to root
cd ..

# Start Python scrapers
source venv/bin/activate
python scripts/run_all_scrapers_safe.py

echo "✅ System started successfully!"
echo "Dashboard: http://localhost:3000"
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
trap "kill $DASHBOARD_PID 2>/dev/null; exit" INT
wait $DASHBOARD_PID
EOF
chmod +x start_full_system.sh

print_success "Startup scripts created"

# Step 8: Final status report
echo ""
echo "🎉 Boom-Bust Sentinel System Setup Complete!"
echo ""
echo "📋 System Status:"
echo "   ✅ Python environment: Ready"
echo "   ✅ Node.js environment: Ready"
echo "   ✅ Database: $(if npm run db:push > /dev/null 2>&1; then echo "Connected"; else echo "Needs configuration"; fi)"
echo "   ✅ Data files: $(if [ -d "data" ] && [ "$(ls -A data/*.json 2>/dev/null)" ]; then echo "Available"; else echo "Empty"; fi)"
echo ""
echo "🚀 Quick Start Commands:"
echo "   ./start_scrapers.sh     - Run data scrapers"
echo "   ./start_dashboard.sh    - Start dashboard only"
echo "   ./start_full_system.sh  - Start complete system"
echo ""
echo "🌐 Access Points:"
echo "   Dashboard: http://localhost:3000"
echo "   API Health: http://localhost:3000/api/system/health"
echo ""
echo "📚 Next Steps:"
echo "   1. Update .env.local with your database credentials"
echo "   2. Run: ./start_full_system.sh"
echo "   3. Visit http://localhost:3000"
echo "   4. Login with test@example.com / testpassword123 (if local DB setup)"
echo ""
echo "🔧 Troubleshooting:"
echo "   - Check logs in: logs/scraper_safe_run.log"
echo "   - Database issues: ./dashboard/scripts/setup-local-database.sh"
echo "   - Environment issues: Check .env.local file"
echo ""
