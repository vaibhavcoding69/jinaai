# Jina AI Proxy API - Deployment Guide

## Overview
This is a Flask-based web API that provides proxy-enabled access to Jina AI's search and reader services. It includes automatic proxy rotation, error handling, and fallback mechanisms to avoid rate limiting.

## Features
- 🔍 Web search using Jina AI's search API
- 📄 URL content extraction using Jina AI's reader API  
- 🔄 Automatic proxy rotation to avoid rate limits
- 📊 Built-in statistics and health monitoring
- 🛡️ Error handling and fallback mechanisms
- 📈 Request logging and monitoring

## Quick Start

### Local Development
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the API:
   ```bash
   python enhanced_jina_api.py
   ```

3. Test the API:
   ```bash
   python test_api.py
   ```

The API will be available at `http://localhost:5000`

### Docker Deployment
1. Build the Docker image:
   ```bash
   docker build -t jina-proxy-api .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 jina-proxy-api
   ```

### Heroku Deployment
1. Install Heroku CLI and login:
   ```bash
   heroku login
   ```

2. Create a new Heroku app:
   ```bash
   heroku create your-app-name
   ```

3. Deploy to Heroku:
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

### Other Free Hosting Options
- **Render**: https://render.com/ (recommended)
- **Railway**: https://railway.app/
- **PythonAnywhere**: https://www.pythonanywhere.com/
- **Vercel**: https://vercel.com/ (for serverless)
- **Google Cloud Run**: https://cloud.google.com/run

## API Endpoints

### 1. Search Web Content
- **URL**: `/search`
- **Method**: `POST`
- **Body**: `{"query": "your search term"}`
- **Response**: Search results from Jina AI

### 2. Read URL Content  
- **URL**: `/read`
- **Method**: `POST`
- **Body**: `{"url": "https://example.com"}`
- **Response**: Clean text content from the URL

### 3. Health Check
- **URL**: `/health`
- **Method**: `GET` 
- **Response**: API health status and statistics

### 4. Statistics
- **URL**: `/stats`
- **Method**: `GET`
- **Response**: Detailed API usage statistics

## Example Usage

### Python
```python
import requests

# Search example
response = requests.post('http://your-api-url/search', 
                        json={'query': 'latest AI news'})
print(response.json())

# Read URL example  
response = requests.post('http://your-api-url/read',
                        json={'url': 'https://example.com'})
print(response.json())
```

### cURL
```bash
# Search
curl -X POST -H "Content-Type: application/json" \
     -d '{"query":"AI developments"}' \
     http://your-api-url/search

# Read URL
curl -X POST -H "Content-Type: application/json" \
     -d '{"url":"https://example.com"}' \
     http://your-api-url/read
```

### JavaScript/Fetch
```javascript
// Search
fetch('http://your-api-url/search', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query: 'AI news'})
})
.then(response => response.json())
.then(data => console.log(data));

// Read URL
fetch('http://your-api-url/read', {
    method: 'POST', 
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url: 'https://example.com'})
})
.then(response => response.json())
.then(data => console.log(data));
```

## Configuration

### Environment Variables
- `PORT`: Port to run the API (default: 5000)
- `FLASK_DEBUG`: Enable debug mode (default: True)
- `JINA_API_KEY`: Optional Jina AI API key for higher rate limits

### Proxy Configuration
The API uses a built-in list of free proxies that are automatically tested and rotated. You can extend the proxy list in the `_load_proxy_list()` method.

## Monitoring and Maintenance

### Health Monitoring
Monitor the `/health` endpoint to check API status:
- `healthy`: All systems operational
- `degraded`: Limited functionality (no working proxies)

### Logs
The API provides detailed logging for debugging and monitoring:
- Request/response information
- Proxy rotation events  
- Error handling

### Statistics
View API statistics at `/stats`:
- Total requests processed
- Proxy success rates
- Uptime information

## Security Considerations

1. **Rate Limiting**: The API includes built-in proxy rotation to avoid rate limits
2. **Error Handling**: Graceful fallback to direct connections when proxies fail
3. **Input Validation**: All inputs are validated and sanitized
4. **HTTPS**: Use HTTPS in production deployments

## Troubleshooting

### Common Issues
1. **No working proxies**: The API will fall back to direct connections
2. **Rate limiting**: Automatic proxy rotation should handle this
3. **Connection timeouts**: Retry logic is built-in

### Debug Mode
Enable debug mode for development:
```bash
export FLASK_DEBUG=True
python enhanced_jina_api.py
```

## Contributing
Feel free to improve the proxy list, add new features, or fix bugs. The code is designed to be easily extensible.

## License  
This project is open source. Use responsibly and respect the terms of service of Jina AI and proxy providers.
