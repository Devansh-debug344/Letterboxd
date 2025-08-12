# Stage 1: Build frontend
FROM node:20 AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Build backend
FROM python:3.11 AS backend
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend .

# Copy built frontend into backend's "static" folder
COPY --from=frontend-builder /app/frontend/dist ./app/static

# Expose backend port
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
