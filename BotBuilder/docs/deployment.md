# Production Deployment Guide

## Environment Setup

1. **Copy Environment Template**
   ```bash
   cp .env.template .env
   ```

2. **Configure Required Variables**
   - `OPENAI_API_KEY`: Your OpenAI API key (required)
   - `SECRET_KEY`: Strong secret key for session security
   - `DATABASE_URL`: Production database connection string
   - `BASE_WEBHOOK_URL`: Your public domain for webhooks

## Replit Always-On Deployment

1. **Configure Environment Variables**
   - Go to Replit Secrets tab
   - Add all variables from `.env.template`
   - Ensure `OPENAI_API_KEY` is set

2. **Enable Always-On**
   - Click "Deploy" in Replit
   - Select "Autoscale Deployment"
   - Your app will be available at: `https://your-repl-name.replit.app`

3. **Webhook Configuration**
   - Set `BASE_WEBHOOK_URL` to your Replit domain
   - Use `/health` endpoint for monitoring

## VPS Deployment (DigitalOcean, Render, Railway)

### Using Gunicorn (Recommended)

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Database Migration**
   ```bash
   python migrations/migrate.py
   ```

3. **Start Production Server**
   ```bash
   gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
   ```

### Using Docker

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   EXPOSE 5000
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
   ```

2. **Build and Run**
   ```bash
   docker build -t llm-bot-builder .
   docker run -p 5000:5000 --env-file .env llm-bot-builder
   ```

## Health Monitoring

- **Health Check**: `GET /health`
- **Quick Check**: `GET /health/quick`
- **System Status**: Available in dashboard

## Rate Limiting

- Configure `MESSAGES_PER_MINUTE` and `MESSAGES_PER_SECOND`
- Default: 60 messages/minute, 2 messages/second per bot
- Adjust based on your OpenAI API limits

## Logging

- Logs stored in `/logs` directory
- Daily rotation enabled by default
- Monitor `errors.log` for issues
- `messages.log` for conversation tracking

## Security Checklist

- [ ] Strong `SECRET_KEY` set
- [ ] `DEBUG=False` in production
- [ ] Database credentials secured
- [ ] OpenAI API key protected
- [ ] HTTPS enabled (automatic on Replit)
- [ ] Rate limiting enabled
- [ ] Regular log monitoring

## Scaling Considerations

- Use PostgreSQL for production database
- Monitor memory usage via `/health`
- Scale workers based on load
- Consider Redis for session storage in multi-instance setups