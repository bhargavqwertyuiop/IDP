#!/bin/bash

# Intelligent Document Processing Setup Script
# This script sets up the complete environment for the IDP application

set -e  # Exit on any error

echo "🚀 Setting up Intelligent Document Processing Application..."
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python3 found: $(python3 --version)"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install system dependencies based on OS
echo "🔧 Installing system dependencies..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux system"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils
    elif command -v yum &> /dev/null; then
        sudo yum install -y tesseract poppler-utils
    elif command -v pacman &> /dev/null; then
        sudo pacman -S tesseract tesseract-data-eng poppler
    else
        echo "⚠️ Please install tesseract-ocr and poppler-utils manually"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS system"
    if command -v brew &> /dev/null; then
        brew install tesseract poppler
    else
        echo "❌ Homebrew not found. Please install Homebrew first or install tesseract manually"
        exit 1
    fi
else
    echo "⚠️ Unsupported OS. Please install tesseract-ocr and poppler-utils manually"
fi

# Install Python requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Download spaCy model
echo "🧠 Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads temp sample_documents

# Create sample documents directory with README
cat > sample_documents/README.md << 'EOF'
# Sample Documents

Place your test documents in this directory to try out the application.

Supported formats:
- PDF files
- PNG images
- JPG/JPEG images
- TIFF images

The application works best with:
- High-resolution images (300 DPI or higher)
- Clear, well-lit documents
- Documents with good contrast between text and background
EOF

# Check if Tesseract is working
echo "🔍 Testing Tesseract installation..."
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract installed: $(tesseract --version | head -1)"
else
    echo "❌ Tesseract not found in PATH. Please check installation."
    exit 1
fi

# Create a simple test script
cat > test_setup.py << 'EOF'
#!/usr/bin/env python3
"""
Test script to verify all dependencies are working correctly
"""

def test_imports():
    """Test all required imports"""
    try:
        import cv2
        print("✅ OpenCV imported successfully")
        
        import pytesseract
        print("✅ pytesseract imported successfully")
        
        import pdf2image
        print("✅ pdf2image imported successfully")
        
        from PIL import Image
        print("✅ PIL imported successfully")
        
        import streamlit
        print("✅ Streamlit imported successfully")
        
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy model loaded successfully")
        
        import pandas
        print("✅ Pandas imported successfully")
        
        print("\n🎉 All dependencies are working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except OSError as e:
        print(f"❌ Model loading error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing setup...")
    if test_imports():
        print("\n✅ Setup verification completed successfully!")
        print("You can now run the application with: streamlit run app.py")
    else:
        print("\n❌ Setup verification failed. Please check the errors above.")
EOF

# Run the test
echo "🧪 Running setup verification..."
python test_setup.py

# Clean up test script
rm test_setup.py

echo ""
echo "🎉 Setup completed successfully!"
echo "=================================================="
echo ""
echo "To run the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Start the application: streamlit run app.py"
echo "3. Open your browser to: http://localhost:8501"
echo ""
echo "To run with Docker:"
echo "1. Build the image: docker-compose build"
echo "2. Start the container: docker-compose up"
echo "3. Open your browser to: http://localhost:8501"
echo ""
echo "📁 Project structure:"
echo "├── app.py                 # Main application"
echo "├── requirements.txt       # Python dependencies"
echo "├── Dockerfile            # Docker configuration"
echo "├── docker-compose.yml    # Docker Compose configuration"
echo "├── setup.sh              # This setup script"
echo "├── uploads/              # Directory for uploaded files"
echo "├── temp/                 # Temporary files directory"
echo "└── sample_documents/     # Place test documents here"
echo ""
echo "Happy document processing! 📄✨"