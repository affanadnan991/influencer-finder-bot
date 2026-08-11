#!/bin/bash

# Setup script for Influencer Finder Bot
# This script installs all required dependencies

echo "╔════════════════════════════════════════════════════════╗"
echo "║  🎯 INFLUENCER FINDER BOT - SETUP SCRIPT 🎯          ║"
echo "║                                                        ║"
echo "║  Installing System Dependencies & Python Packages     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root for system packages
echo "📦 Installing System Dependencies..."
echo ""

# Install system dependencies for Playwright
if command -v apt-get &> /dev/null; then
    echo "Using apt package manager..."
    echo ""
    
    # Update package list
    echo "Updating package list..."
    sudo apt-get update -qq
    
    # Install Playwright dependencies
    echo "Installing browser dependencies..."
    sudo apt-get install -y \
        libnss3 \
        libxss1 \
        libasound2 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgconf-2-4 \
        libgdk-pixbuf2.0-0 \
        libglib2.0-0 \
        libgtk-3-0 \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxinerama1 \
        libxrandr2 \
        libxrender1 \
        libxshmfence1 \
        libxvidcore4 \
        libgl1-mesa-glx \
        libgl1-mesa-dri \
        xvfb \
        fonts-liberation \
        libappindicator3-1 \
        libxss1 \
        fonts-noto-color-emoji \
        > /dev/null 2>&1
    
    echo "✅ System dependencies installed"
    
elif command -v brew &> /dev/null; then
    echo "Using Homebrew package manager..."
    echo "Note: Playwright usually works out of the box on macOS"
    echo "✅ Skipping system dependencies"
    
elif command -v pacman &> /dev/null; then
    echo "Using pacman package manager..."
    sudo pacman -Syy
    sudo pacman -S --noconfirm \
        nss \
        libxss \
        alsa-lib \
        libatk \
        at-spi2-core \
        cups \
        dbus \
        libdrm \
        mesa \
        libgconf \
        gdk-pixbuf2 \
        glib2 \
        gtk3 \
        pango \
        libx11 \
        libxcomposite \
        libxcursor \
        libxdamage \
        libxext \
        libxfixes \
        libxi \
        libxinerama \
        libxrandr \
        libxrender \
        libxshmfence \
        libxvideo \
        libgl \
        ttf-liberation \
        libappindicator-gtk3 \
        libxss \
        noto-fonts-emoji \
        > /dev/null 2>&1
    
    echo "✅ System dependencies installed"
else
    echo "⚠️  Could not detect package manager"
    echo "   Please install Playwright browser dependencies manually"
    echo "   Visit: https://playwright.dev/python/docs/intro"
fi

echo ""
echo "📦 Setting up Python Virtual Environment..."
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "📦 Installing Python Packages..."
echo ""

# Upgrade pip
pip install --upgrade pip setuptools wheel -q

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    pip install -r requirements.txt -q
    echo "✅ Python packages installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

echo ""
echo "📦 Installing Playwright Browsers..."
echo ""

# Install Playwright browsers
playwright install chromium

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║  ✅ SETUP COMPLETE! 🎉                                ║"
echo "║                                                        ║"
echo "║  Next steps:                                           ║"
echo "║  1. source venv/bin/activate                           ║"
echo "║  2. python3 run.py                                     ║"
echo "║                                                        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
