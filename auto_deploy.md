第一步：准备一把“钥匙” (SSH Key)
GitHub 需要权限才能登录你的服务器，我们不能把密码直接告诉它（不安全），而是用密钥对。

在你的本地电脑生成一对新密钥（不要用之前的，专门给 GitHub 用）：

Bash

ssh-keygen -t rsa -b 4096 -C "github-actions-deploy" -f ./github_deploy_key
# 一路回车，不要设置密码
这会在当前目录生成两个文件：

github_deploy_key (私钥，给 GitHub 的)

github_deploy_key.pub (公钥，放服务器的)

把公钥放入服务器： 复制 github_deploy_key.pub 的内容。 登录你的阿里云服务器，执行：

Bash

# 如果没有这个文件就创建
mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys

# 把公钥追加进去
echo "你的公钥内容(ssh-rsa AAAA...)" >> ~/.ssh/authorized_keys

# 确保权限正确（非常重要，权限不对 SSH 会拒绝连接）
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
第二步：把私钥交给 GitHub (Secrets)
打开你的 GitHub 项目仓库页面。

点击 Settings -> 左侧 Secrets and variables -> Actions。

点击 New repository secret，添加以下三个变量：

HOST: 你的阿里云服务器 IP 地址。

USERNAME: root

KEY: 复制 github_deploy_key (私钥) 的全部内容（包括 -----BEGIN... 和 -----END...）。

第三步：编写自动化脚本 (Workflow)
在你的本地项目根目录下，创建目录和文件：.github/workflows/deploy.yml。

复制以下内容进去：

YAML

name: Auto Deploy

# 触发条件：当 main 分支收到 push 时
on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    # 1. 这里不需要拉取代码，因为我们是去服务器上拉取
    
    # 2. 使用 SSH 远程连接服务器并执行命令
    - name: Remote SSH Commands
      uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        # 执行的命令
        script: |
          # 进入项目目录 (请修改为你真实的目录路径)
          cd /home/Staff-assessment-system
          
          # 执行我们在上一轮对话中写的更新脚本
          # 如果你还没写那个脚本，也可以直接写命令：
          # git pull origin main
          # docker-compose up -d --build
          # docker image prune -f
          bash update.sh
第四步：推送到 GitHub
保存上述文件。

执行 Git 提交推送：

Bash

git add .
git commit -m "配置 GitHub Actions 自动部署"
git push origin main
第五步：见证奇迹
去 GitHub 仓库的 Actions 标签页。

你会看到一个正在转圈的任务 Auto Deploy。

等它变成绿色对勾（Success），你的阿里云服务器就已经自动更新完毕了！