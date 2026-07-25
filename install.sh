#!/bin/bash

# Photo Sorting Tool - Install Script
# This script sets up the project environment and installs all dependencies

set -e  # Exit on any error

echo "Photo Sorting Tool - Installation"
echo "================================="

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✓ Found Python $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
pip install --upgrade pip

# Install dependencies and package in editable mode
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "📦 Installing photo-sorting package in editable mode..."
pip install -e .

# Test installation
echo "🧪 Testing installation..."
python -c "from photo_sorting import extract_date_from_directory, MetadataReader, MetadataWriter, setup_logger; print('✓ All imports successful!')"

# Test CLI command
echo "🔧 Testing CLI command..."
photo-sorting --help > /dev/null && echo "✓ CLI command 'photo-sorting' available!" || echo "❌ CLI command failed"

echo ""
echo "✅ Installation complete!"
echo ""
echo "The tool is now available as 'photo-sorting' command!"
echo ""
echo "Usage examples:"
echo "  photo-sorting -f \"/path/to/2023.6.15 - Event\" --dry-run --verbose"
echo "  photo-sorting -f \"/path/to/photos\" -d \"2023.6.15\" --backup-dir \"originals\""
echo ""
echo "You can also use it directly:"
echo "  python main.py --help"