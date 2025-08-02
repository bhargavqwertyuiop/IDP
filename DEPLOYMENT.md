# 🚀 Deployment Guide

This guide provides step-by-step instructions for deploying the Intelligent Document Processing application in different environments.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu/Debian preferred), macOS, or Windows
- **Python**: Version 3.8 or higher
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: At least 1GB free space
- **Network**: Internet connection for downloading dependencies

### Required System Dependencies
- **Tesseract OCR**: For text extraction from images
- **Poppler**: For PDF to image conversion
- **OpenCV dependencies**: For image processing

## 🐳 Docker Deployment (Recommended)

Docker deployment is the easiest and most reliable method.

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### Steps

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd intelligent-document-processing
   ```

2. **Build and run with Docker Compose:**
   ```bash
   # Build and start the application
   docker-compose up --build

   # Or run in detached mode
   docker-compose up -d --build
   ```

3. **Access the application:**
   - Open your browser to: http://localhost:8501
   - The application should be running and ready to use

4. **View logs (if running in detached mode):**
   ```bash
   docker-compose logs -f
   ```

5. **Stop the application:**
   ```bash
   docker-compose down
   ```

### Production Deployment with Nginx

For production environments, use the nginx reverse proxy:

```bash
# Start with production profile
docker-compose --profile production up -d --build

# Access via http://localhost (port 80)
```

## 🖥️ Local Development Setup

### Ubuntu/Debian

1. **Install system dependencies:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-venv python3-pip
   sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils
   ```

2. **Clone and setup the project:**
   ```bash
   git clone <repository-url>
   cd intelligent-document-processing
   
   # Run the automated setup script
   chmod +x setup.sh
   ./setup.sh
   ```

3. **Start the application:**
   ```bash
   source venv/bin/activate
   streamlit run app.py
   ```

### macOS

1. **Install Homebrew (if not already installed):**
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install system dependencies:**
   ```bash
   brew install python tesseract poppler
   ```

3. **Setup the project:**
   ```bash
   git clone <repository-url>
   cd intelligent-document-processing
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Start the application:**
   ```bash
   source venv/bin/activate
   streamlit run app.py
   ```

### Windows

1. **Install Python 3.8+** from [python.org](https://python.org)

2. **Install Tesseract OCR:**
   - Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to your PATH environment variable

3. **Install Poppler:**
   - Download from [poppler for Windows](https://blog.alivate.com.au/poppler-windows/)
   - Extract and add to PATH

4. **Setup the project:**
   ```cmd
   git clone <repository-url>
   cd intelligent-document-processing
   
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

5. **Start the application:**
   ```cmd
   venv\Scripts\activate
   streamlit run app.py
   ```

## ☁️ Cloud Deployment

### AWS EC2

1. **Launch an EC2 instance:**
   - Use Ubuntu 20.04 LTS or newer
   - Minimum t3.medium instance type
   - Open port 8501 in security group

2. **Connect to instance and setup:**
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Update system
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose git
   
   # Clone and deploy
   git clone <repository-url>
   cd intelligent-document-processing
   sudo docker-compose up -d --build
   ```

3. **Access via:** `http://your-ec2-ip:8501`

### Google Cloud Platform

1. **Create a Compute Engine instance:**
   - Use Ubuntu 20.04 LTS
   - Enable HTTP/HTTPS traffic
   - Minimum e2-medium machine type

2. **Setup and deploy:**
   ```bash
   # Install Docker
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose git
   sudo usermod -aG docker $USER
   
   # Logout and login again, then:
   git clone <repository-url>
   cd intelligent-document-processing
   docker-compose up -d --build
   ```

### Azure Container Instances

1. **Create resource group:**
   ```bash
   az group create --name idp-rg --location eastus
   ```

2. **Build and push image:**
   ```bash
   # Build locally
   docker build -t idp-app .
   
   # Tag and push to Azure Container Registry
   az acr create --resource-group idp-rg --name idpregistry --sku Basic
   az acr login --name idpregistry
   docker tag idp-app idpregistry.azurecr.io/idp-app:latest
   docker push idpregistry.azurecr.io/idp-app:latest
   ```

3. **Deploy container:**
   ```bash
   az container create \
     --resource-group idp-rg \
     --name idp-container \
     --image idpregistry.azurecr.io/idp-app:latest \
     --ports 8501 \
     --dns-name-label idp-app-unique
   ```

## 🔧 Configuration

### Environment Variables

Set these environment variables for production:

```bash
# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ENABLE_CORS=false
STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0

# OCR Configuration
TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata/
```

### Performance Tuning

For high-traffic deployments:

1. **Increase worker processes** in docker-compose.yml:
   ```yaml
   deploy:
     replicas: 3
   ```

2. **Add resource limits:**
   ```yaml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

3. **Use nginx load balancer** for multiple instances

## 📊 Monitoring

### Health Checks

The application includes built-in health checks:
- **Endpoint**: `http://localhost:8501/_stcore/health`
- **Docker**: Automatic health checks configured

### Logging

View application logs:
```bash
# Docker deployment
docker-compose logs -f

# Local deployment
# Logs appear in terminal where streamlit is running
```

## 🔒 Security

### Production Security Checklist

- [ ] Use HTTPS (configure SSL certificates)
- [ ] Set up firewall rules (only allow necessary ports)
- [ ] Use environment variables for sensitive configuration
- [ ] Regularly update dependencies
- [ ] Monitor for security vulnerabilities
- [ ] Implement rate limiting if needed
- [ ] Use strong authentication if required

### SSL/HTTPS Setup

For production with custom domain:

1. **Get SSL certificate** (Let's Encrypt recommended)
2. **Update nginx.conf** with SSL configuration
3. **Redirect HTTP to HTTPS**

## 🛠️ Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process using port 8501
sudo lsof -i :8501
# Kill the process
sudo kill -9 <PID>
```

**Docker build fails:**
```bash
# Clean Docker cache
docker system prune -a
# Rebuild
docker-compose build --no-cache
```

**Tesseract not found:**
```bash
# Check if Tesseract is installed
which tesseract
tesseract --version

# Install if missing (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng
```

**spaCy model missing:**
```bash
# Download the model
python -m spacy download en_core_web_sm
```

### Performance Issues

**Slow OCR processing:**
- Ensure images are high quality but not unnecessarily large
- Use preprocessing to improve image quality
- Consider using GPU-accelerated Tesseract if available

**Memory issues:**
- Increase container memory limits
- Process smaller batches of documents
- Optimize image sizes before processing

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Review application logs
3. Verify all dependencies are installed correctly
4. Check system resources (CPU, memory, disk space)

---

**Need help?** Create an issue in the repository with:
- Your operating system and version
- Error messages and logs
- Steps you've already tried