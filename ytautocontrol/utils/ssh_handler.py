from typing import Literal
import paramiko
import time
from pathlib import Path
import os


class SSHHandler:
    def __init__(self, ip: str, account: str, passwrod: str):
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.client.connect(
            hostname=ip,
            username=account,
            password=passwrod
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def execute(self, commands: list[str], platform: Literal["windows", "linux"] = "windows", no_wait_last: bool = False) -> str | None:
        """
        批量执行命令，命令为连续命令，会等待前一个命令执行完成

        Args:
            commands: 执行的命令列表
            platform: 执行命令的平台，可选windows和linux，默认windows
            no_wait_last: 布尔值，是否不等待最后一个命令执行完成，默认False

        Returns:
            字符串，执行的返回值
        """
        output = ""
        shell = self.client.invoke_shell()
        length = len(commands)
        if platform == "windows":
            enter = "\r\n"
        else:
            enter = "\n"
        # for idx, com in enumerate(commands):
        #     shell.send(f"{com}{enter}".encode())
        #     print(f"执行命令：{com}")
        #     if idx == length - 1 and no_wait_last is True:
        #         print("最后一条命令了")
        #         return
        #     while not shell.recv_ready():
        #         time.sleep(1)
        #     while True:
        #         try:
        #             data = shell.recv(9999).decode()
        #         except:
        #             data = shell.recv(9999).decode("gbk")
        #         format_data = data.strip()
        #         output += format_data
        #         if platform == "linux":
        #             if format_data.endswith("#") or format_data.endswith("$"):
        #                 break
        #         else:
        #             if format_data.endswith(">"):
        #                 break
        for com in commands:
            print(f"执行命令{com}")
            shell.send(f"{com}{enter}".encode())
        return output

    def run_remote_script(self, account: str, password: str, email: str, word: str, author: str, addr: str):
        # project_path = Path(str(os.environ.get("ProgramFiles"))) / "YTAuto" / "ytauto"
        project_path = Path("~/Documents/").expanduser() / "YTAuto" / "ytauto"
        self.execute([f"cd {str(project_path)}", f'poetry run pytest --account={account} --password={password} --email={email} --word="{word}" --author="{author}" --addr={addr}'], no_wait_last=True)


if __name__ == "__main__":
    with SSHHandler("124.222.129.98", "ubuntu", "BaMa77329601") as ssh:
        output = ssh.execute(["cd /home/servertest/servertest", "poetry run python3 main.py"])
        print(output)
    



