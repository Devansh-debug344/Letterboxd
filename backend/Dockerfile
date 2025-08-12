# 1️⃣ Backend base image
FROM python:3.11-slim AS backend

# Prevent Python from writing pyc files & enable output flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install OS dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2️⃣ Frontend build stage
FROM node:18-alpine AS frontend

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# 3️⃣ Final stage: combine backend + frontend
FROM backend AS final

# Copy backend code
COPY . .

# Copy built React files into backend static folder
COPY --from=frontend /frontend/dist ./static

# Environment variable for production
ENV ENV=prod

# Expose port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
