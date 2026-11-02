# ==========================================
# Giai đoạn 1: Build mã nguồn React + Vite
# ==========================================
FROM node:20-alpine AS build-stage

WORKDIR /app

# Khai báo các tham số môi trường lúc build
ARG VITE_API_URL=http://localhost:5000/api
ARG VITE_SOCKET_URL=http://localhost:5000

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_SOCKET_URL=$VITE_SOCKET_URL

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# ==========================================
# Giai đoạn 2: Phục vụ file tĩnh qua Nginx Alpine
# ==========================================
FROM nginx:alpine

# Copy cấu hình Nginx tối ưu cho React SPA và reverse proxy
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy thư mục dist đã biên dịch từ Stage 1 sang Nginx
COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

