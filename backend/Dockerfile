# 1. Use Python base image
FROM python:3.10

# 2. Set work directory inside container
WORKDIR /app

# Copy only requirements first for caching
COPY backend/requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Copy rest of backend code
COPY backend/ /app/

# 5. Run FastAPI using uvicorn
CMD ["uvicorn", "run:app", "--host", "0.0.0.0", "--port", "8000"]
