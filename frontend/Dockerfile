# 1. Use Node base image
FROM node:18

# 2. Set working dir
WORKDIR /app

# 3. Copy package.json from frontend folder
COPY frontend/package*.json ./

# 4. Install deps
RUN npm install

# 5. Copy rest of the frontend code
COPY frontend/ ./

# 6. Build
RUN npm run build

# 7. Serve with a simple server (optional for Docker)
RUN npm install -g serve
CMD ["serve", "-s", "build"]
