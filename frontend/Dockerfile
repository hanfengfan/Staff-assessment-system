# -------- 构建阶段 --------
    FROM node:18 AS build-stage

    WORKDIR /app
    
    # 限制 Node 内存，避免 OOM / swap 抖动
    ENV NODE_OPTIONS="--max-old-space-size=2048"
    
    # 先复制依赖描述文件，利用缓存
    COPY package.json package-lock.json ./
    
    # 使用 npm ci + 限制并发
    RUN npm ci \
      --registry=https://registry.npmmirror.com \
      --no-audit \
      --no-fund
    
    # 再复制源码
    COPY . .
    
    # 构建
    RUN npm run build
    
    # -------- 生产阶段 --------
    FROM nginx:stable-alpine
    
    COPY --from=build-stage /app/dist /usr/share/nginx/html
    
    EXPOSE 80
    
    CMD ["nginx", "-g", "daemon off;"]