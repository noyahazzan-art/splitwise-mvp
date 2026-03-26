# Splitwise MVP - Production Deployment Guide

## 🎯 Overview
This guide covers deploying the enhanced Splitwise MVP with all security, performance, and reliability improvements.

## 📋 Prerequisites

### System Requirements
- Python 3.8+
- SQLite 3.x
- 2GB+ RAM
- 1GB+ disk space

### Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd splitwise

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 🔧 Configuration

### Environment Variables
Create `.env` file in project root:

```bash
# JWT Configuration
SECRET_KEY=your-super-secret-jwt-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_ALGORITHM=HS256

# Database Configuration
DATABASE_URL=sqlite:///./data/splitwise.db

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Security Headers Configuration
The application includes comprehensive security headers:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000
- Content-Security-Policy: default-src 'self'
- Referrer-Policy: strict-origin-when-cross-origin

## 🗄️ Database Setup

### Initial Setup
```bash
# Initialize database with migrations
python migrate.py upgrade head

# Or use direct initialization (for development)
python -c "from app.database import init_db; init_db()"
```

### Migration Management
```bash
# Create new migration
python migrate.py revision "Description of changes"

# Run migrations
python migrate.py upgrade

# Check current version
python migrate.py current

# View migration history
python migrate.py history

# Rollback if needed
python migrate.py downgrade
```

## 🚀 Production Deployment

### Option 1: Direct Python
```bash
# Set production environment
export DEBUG=false
export LOG_LEVEL=INFO

# Start application
uvicorn app.main:app --host 0.0.0.0 --port 8001 --workers 4
```

### Option 2: Docker
```bash
# Build image
docker build -t splitwise-mvp .

# Run with environment variables
docker run -d \
  -p 8001:8001 \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG=false \
  -v $(pwd)/data:/app/data \
  splitwise-mvp
```

### Option 3: Docker Compose
```bash
# Using provided docker-compose.yml
docker-compose up -d
```

## 🔐 Security Configuration

### JWT Security
- Use strong, random SECRET_KEY (32+ characters)
- Set appropriate token expiration (30 minutes recommended)
- Enable HTTPS in production

### Rate Limiting
- Default: 100 requests per minute per IP/user
- Configurable in `app/middleware.py`
- Headers included: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset

### CORS Configuration
Update allowed origins in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Production domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## 📊 Monitoring & Logging

### Log Configuration
Logs include:
- Request correlation IDs
- User authentication events
- API performance metrics
- Security events
- Error details with stack traces

### Log Location
- Application logs: stdout/stderr (configure with your logging system)
- Database logs: SQLite journal
- Access logs: Configured in web server

### Monitoring Endpoints
- `/full_status` - System health check
- `/metrics` - Basic metrics (if implemented)
- `/docs` - API documentation

## 🧪 Testing in Production

### Health Checks
```bash
# Basic health check
curl https://your-domain.com/full_status

# API documentation
curl https://your-domain.com/docs

# Test authentication
curl -X POST https://your-domain.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass"}'
```

### Load Testing
```bash
# Install artillery
npm install -g artillery

# Run load test
artillery run load-test-config.yml
```

## 🔧 PowerShell Stability (Windows)

### Production Fixes
```powershell
# Run as Administrator before deployment
.\scripts\fix_powershell_editor_services.ps1

# This ensures:
# - No PowerShell Editor Services crashes
# - Optimized performance
# - Enhanced error handling
# - System stability
```

## 🚨 Troubleshooting

### Common Issues

#### JWT Token Issues
```bash
# Check SECRET_KEY is set
echo $SECRET_KEY

# Verify token format
# JWT should be in Authorization: Bearer <token> header
```

#### Database Issues
```bash
# Check database permissions
ls -la data/

# Run migrations
python migrate.py upgrade

# Check SQLite version
sqlite3 --version
```

#### Rate Limiting
```bash
# Check rate limit headers
curl -I https://your-domain.com/api/endpoint

# Headers to check:
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 95
# X-RateLimit-Reset: 1640995200
```

### Performance Optimization

#### Database Optimization
```bash
# Create indexes (automatically created)
# Indexes on: group_id, user_id, expense_id

# Monitor query performance
# Enable SQL logging temporarily for debugging
```

#### Memory Management
```bash
# Monitor memory usage
python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
"

# Application includes automatic cleanup every 100 requests
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Use load balancer for multiple instances
- Share database via network storage
- Configure session affinity if needed

### Database Scaling
- Consider PostgreSQL for high traffic
- Implement connection pooling
- Add read replicas for queries

### Caching Strategy
- Redis for session storage
- CDN for static assets
- Application-level caching for frequent queries

## 🔒 Security Best Practices

### Production Security Checklist
- [ ] HTTPS enabled everywhere
- [ ] Strong JWT secret key configured
- [ ] CORS limited to production domains
- [ ] Rate limiting configured appropriately
- [ ] Security headers verified
- [ ] Input validation tested
- [ ] Error handling doesn't leak information
- [ ] Logging enabled and monitored
- [ ] Database backups configured
- [ ] PowerShell stability fixes applied (Windows)

### Monitoring Setup
- [ ] Application performance monitoring
- [ ] Error alerting configured
- [ ] Security event monitoring
- [ ] Database performance monitoring
- [ ] Infrastructure monitoring

## 📞 Support

### Log Analysis
Check logs for:
- Correlation IDs for request tracing
- Authentication failures
- Rate limiting events
- Database errors
- Performance bottlenecks

### Common Debug Commands
```bash
# Check application logs
docker logs splitwise-container

# Database connection test
python -c "from app.database import get_session; print('DB OK')"

# JWT token test
python -c "from app.auth import create_access_token; print('JWT OK')"
```

## 🎉 Deployment Complete!

Once deployed, your Splitwise MVP will have:
- ✅ Enterprise-grade authentication
- ✅ Comprehensive input validation
- ✅ Advanced security headers
- ✅ Rate limiting protection
- ✅ Structured logging
- ✅ Database migrations
- ✅ Performance monitoring
- ✅ Error handling
- ✅ PowerShell stability (Windows)

**Access Points:**
- API: `https://your-domain.com`
- Documentation: `https://your-domain.com/docs`
- Health Check: `https://your-domain.com/full_status`

Your Splitwise MVP is now production-ready with enterprise-grade security and reliability! 🚀
