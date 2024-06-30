import socket
from pathlib import Path
from typing import TypedDict
import toml


config_file = Path(__file__).resolve().parents[1] / "config" / "socket.toml"
config = toml.load(config_file)


class RunScriptFields(TypedDict):
    account: str
    password: str
    email: str
    word: str
    author: str
    addr: str
    filter_type: str
    freq: int
    script_name: str


class SocketHandler:
    def __init__(self, ip: str):
        port = config["server"]["port"]
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((ip, port))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


    def send(self, message: str) -> str:
        """
        发送socket消息

        Args:
            message: 发送的信息

        Returns:
            字符串，服务端返回数据
        """
        self.client.send(message.encode())
        response = self.client.recv(1024)
        try:
            data = response.decode()
        except:
            data = response.decode("gbk")
        return data

    def run_script(self, script: RunScriptFields) -> str:
        """
        执行远程脚本

        Args:
            script: 脚本字段

        Returns:
            字符串，socket服务器返回
        """
        account = script["account"]
        password = script["password"]
        word = script["word"]
        author = script["author"]
        addr = script["addr"]
        email = script["email"]
        filter_types = script["filter_type"]
        freq = script["freq"]
        script_name = script["script_name"]
        # run_script = f'''poetry run pytest --account="{account}" --password="{password}" --word="{word}" --author="{author}" --email="{email}" --addr="{addr}" --filter-types="{filter_types}" --freq={freq} --script-name="{script_name}"'''
        run_fields = f'''"{account}" "{password}" "{email}" "{word}" "{author}" "{addr}" "{filter_types}" {freq} "{script_name}"'''
        return self.send(f"run {run_fields}")

    def close(self):
        self.client.close()



