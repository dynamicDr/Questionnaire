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
    run(f'ssh {REMOTE_HOST}')


if __name__ == "__main__":
    main()