# 1. 使用 Python 官方基础镜像 (根据你的本地版本修改，如 3.9)
FROM python:3.9

# 2. 设置容器内的工作目录
WORKDIR /app

# 3. 先复制依赖文件 (利用 Docker 缓存机制加速构建)
COPY requirements.txt .

# 4. 安装依赖 (使用阿里云源加速)
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 5. 安装 Gunicorn (生产环境用的 Web 服务器，必须安装)
RUN pip install gunicorn

# 6. 复制项目所有代码到容器
COPY . .

# 7. 声明容器内部服务端口 (仅作声明，不直接暴露)
EXPOSE 8000

# 8. 启动命令 (替换 myproject 为你的 Django 项目同名文件夹名字)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]