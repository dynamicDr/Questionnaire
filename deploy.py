import subprocess
import sys
from pathlib import Path

# ==== 可按需修改的配置 ====
PROJECT_DIR = Path(r"d:\projects\Questionnaire")  # 本地项目路径
REMOTE_HOST = "root@8.145.46.18"
REMOTE_PROJECT_DIR = "workspace/Questionnaire"
REMOTE_CONDA_ENV = "DjangoFirst"
GUNICORN_SERVICE = "gunicorn"  # systemctl 服务名
# ========================


def run(cmd, cwd=None, check=True):
    print(f"\n[RUN] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and result.returncode != 0:
        print(f"[ERROR] 命令执行失败，退出码 {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode


def main():
    # 1. 本地 git add / commit / push
    print("=== 本地提交并推送代码 ===")
    run("git add .")
    run(f'git commit -m auto')
    run("git push")

    # 2. 远程执行：git pull + conda 激活，然后停留在服务器命令行
    print("\n=== 登录服务器并更新部署（并停留在远程 shell） ===")
    remote_cmd = f"""
cd {REMOTE_PROJECT_DIR} && \
git stash && \
git pull && 
""".strip().replace("\n", " ")

    # 注意：需要本机已经配置好 SSH 免密或能输入密码
    run(f'ssh {REMOTE_HOST} "{remote_cmd}"')

    print("\n=== 已登录到远程服务器 shell，可继续操作 ===")


if __name__ == "__main__":
    main()