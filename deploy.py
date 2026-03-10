import subprocess
import sys
import time
from pathlib import Path

# ==== 可按需修改的配置 ====
PROJECT_DIR = Path(r"d:\projects\Questionnaire")  # 本地项目路径
REMOTE_HOST = "root@8.145.46.18"
REMOTE_PROJECT_DIR = "workspace/Questionnaire"
REMOTE_CONDA_ENV = "DjangoFirst"
GUNICORN_SERVICE = "gunicorn"  # systemctl 服务名
PUSH_RETRIES = 3  # git push 最大重试次数
PUSH_RETRY_DELAY = 5  # 每次重试之间的等待秒数
# ========================


def run(cmd, cwd=None, check=True):
    print(f"\n[RUN] {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd)
    if check and result.returncode != 0:
        print(f"[ERROR] 命令执行失败，退出码 {result.returncode}")
        sys.exit(result.returncode)
    return result.returncode


def run_with_retry(cmd, retries=PUSH_RETRIES, delay=PUSH_RETRY_DELAY, cwd=None):
    """
    简单重试封装：用于 git push 等可能临时失败的命令。
    """
    attempt = 1
    while attempt <= retries:
        print(f"\n[TRY {attempt}/{retries}] {cmd}")
        result = subprocess.run(cmd, shell=True, cwd=cwd)
        if result.returncode == 0:
            print("[OK] 命令执行成功")
            return 0
        if attempt < retries:
            print(f"[WARN] 命令失败（退出码 {result.returncode}），{delay} 秒后重试...")
            time.sleep(delay)
            attempt += 1
        else:
            print(f"[ERROR] 命令在重试 {retries} 次后仍然失败，退出码 {result.returncode}")
            sys.exit(result.returncode)


def main():
    print("=== 本地提交并推送代码 ===")
    run("git add .")
    run('git commit -m "auto"')
    run_with_retry("git push")
    
    print("\n=== 连接远程服务器并执行部署命令 ===")
    
    # 先执行远程命令
    remote_cmd = (
        f"cd {REMOTE_PROJECT_DIR} && "
        f"git stash && "
        f"git pull"
    )
    
    result = subprocess.run(
        ["ssh", "root@8.145.46.18", remote_cmd],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.returncode != 0:
        print(f"错误: {result.stderr}")
        return
    
    print("\n=== 进入交互式 SSH ===")
    print("\n=== 激活conda环境：conda activate DjangoFirst ===")
    print("\n=== 重启gunicorn：sudo systemctl restart gunicorn ===")
    # 命令执行成功后，进入交互式 SSH 并激活 conda 环境
    interactive_cmd = (
        f"cd {REMOTE_PROJECT_DIR} && "
        f"source ~/anaconda3/etc/profile.d/conda.sh && "
        f"bash"
    )
    
    subprocess.run([
        "ssh", "-t",
        "root@8.145.46.18",
        interactive_cmd
    ])

if __name__ == "__main__":
    main()