# --- 第一阶段：构建构建 ---
    FROM node:16 as build-stage
    WORKDIR /app
    COPY package*.json ./
    # 安装依赖 (使用淘宝源)
    RUN npm install --registry=https://registry.npmmirror.com
    COPY . .
    # 开始打包 (生成 dist 文件夹)
    RUN npm run build
    
    # --- 第二阶段：生产环境 ---
    FROM nginx:stable-alpine
    # 从第一阶段复制打包好的文件到 Nginx 目录
    COPY --from=build-stage /app/dist /usr/share/nginx/html
    EXPOSE 80
    CMD ["nginx", "-g", "daemon off;"]