# 1. Use Node image
FROM node:18

# 2. Set workdir
WORKDIR /app

# 3. Copy package.json & install deps
COPY package*.json ./
RUN npm install

# 4. Copy frontend code
COPY . .

# 5. Build frontend
RUN npm run build

# 6. Serve build using a simple web server
RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
