# Drafthorse TagGenie

A web application for generating and managing tags for templates and assets.

## Features

- Multi-language support (English, Finnish, Swedish, Norwegian, Danish, Estonian, Latvian, Lithuanian, Russian)
- Template and Asset tag generation
- Responsive design for both desktop and mobile
- Easy-to-use interface

## Prerequisites

- Python 3.11+
- Node.js 16+
- npm or yarn

## Local Development Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Tagmanager
```

2. Set up the backend:
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Start the development servers:
```bash
# In the root directory
./start_server.sh
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

## Production Deployment

### Digital Ocean Setup

1. Create a new Ubuntu droplet on Digital Ocean
2. Set up SSH access to the droplet
3. Install required software:
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and Node.js
sudo apt install python3.11 python3.11-venv nodejs npm nginx -y
```

4. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/taggenie
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /var/www/taggenie/frontend/build;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_redirect off;
    }
}
```

5. Enable the Nginx configuration:
```bash
sudo ln -s /etc/nginx/sites-available/taggenie /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6. Set up the application:
```bash
# Create application directory
sudo mkdir -p /var/www/taggenie
sudo chown -R $USER:$USER /var/www/taggenie

# Clone the repository
cd /var/www/taggenie
git clone <repository-url> .

# Set up Python virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up frontend
cd frontend
npm install
npm run build
```

7. Create systemd service for the backend:
```bash
sudo nano /etc/systemd/system/taggenie.service
```

Add the following configuration:
```ini
[Unit]
Description=TagGenie Backend Service
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/var/www/taggenie/app
Environment="PYTHONPATH=/var/www/taggenie"
ExecStart=/var/www/taggenie/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

8. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable taggenie
sudo systemctl start taggenie
```

9. Verify the setup:
```bash
# Check service status
sudo systemctl status taggenie

# Check Nginx status
sudo systemctl status nginx

# Test the API
curl -X POST http://localhost/api/suggest_tags -H "Content-Type: application/json" -d '{"description": "test", "type": "template"}'
```

### Updating Production

To update the production environment:

1. Pull the latest changes:
```bash
cd /var/www/taggenie
git pull
```

2. Update dependencies if needed:
```bash
# Backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm run build
```

3. Restart the backend service:
```bash
sudo systemctl restart taggenie
```

### Environment Variables

The following environment variables are used:

- `HUGGING_FACE_API_KEY`: API key for the Hugging Face model (optional, falls back to keyword matching if not available)

## License

[Your License Here] 