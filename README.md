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

# Install PM2 for process management
sudo npm install -g pm2
```

4. Configure Nginx:
```bash
sudo nano /etc/nginx/sites-available/taggenie
```

Add the following configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

5. Enable the site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/taggenie /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

6. Deploy the application:
```bash
# Clone the repository
git clone <repository-url> /var/www/taggenie
cd /var/www/taggenie

# Set up Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up frontend
cd frontend
npm install
npm run build

# Start the application with PM2
cd ..
pm2 start start_server.sh --name taggenie
pm2 save
pm2 startup
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

## License

[Your License Here] 