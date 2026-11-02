# Sử dụng Node.js LTS Alpine siêu nhẹ (~150MB)
FROM node:20-alpine

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Thiết lập biến môi trường production
ENV NODE_ENV=production

# Copy file định nghĩa phụ thuộc để tận dụng Docker cache layer
COPY package*.json ./

# Cài đặt các thư viện phụ thuộc production
RUN npm ci --omit=dev

# Copy toàn bộ mã nguồn backend vào container
COPY src ./src

# Khai báo cổng lắng nghe của backend
EXPOSE 5000

# Lệnh khởi động server
CMD ["npm", "start"]

