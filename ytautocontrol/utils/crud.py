from threading import ExceptHookArgs
import psycopg2
import toml
from pathlib import Path
from contextlib import suppress
from typing import Any, Literal, TypedDict
from loguru import logger


class RunnerScripts(TypedDict):
    device: str
    device_account: str
    device_pwd: str
    account: str
    password: str
    email: str
    word: str
    author: str
    name: str
    types: str
    freq: int

class Sql:
    def __init__(self):
        config_file = Path(__file__).resolve().parents[1] / "config" / "sql.toml"
        self.config = toml.load(config_file)
        # self.conn = psycopg2.connect(**config["ytauto"])
        self.conn = psycopg2.connect(
            host=self.config["ytauto"]["host"],
            port=self.config["ytauto"]["port"],
            user=self.config["ytauto"]["user"],
            password=self.config["ytauto"]["password"],
            dbname=self.config["ytauto"]["dbname"]
        )
        self.conn.autocommit = True
        self.cursor = self.conn.cursor()
    
    def get_all_accounts(self):
        """获取数据库中所有账号数据"""
        self.cursor.execute("select * from accounts;")
        return self.cursor.fetchall()

    def __check_connected(self):
        if self.conn.closed:
            logger.error(f"数据库连接关闭，尝试重新连接……")
            self.conn = psycopg2.connect(
                host=self.config["ytauto"]["host"],
                port=self.config["ytauto"]["port"],
                user=self.config["ytauto"]["user"],
                password=self.config["ytauto"]["password"],
                dbname=self.config["ytauto"]["dbname"]
            )
        if self.cursor.closed:
            logger.error("数据库游标已关闭，尝试重新连接……")
            self.cursor = self.conn.cursor()
        try:
            self.cursor.execute("select 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            logger.error(f"数据库连接失败，正在尝试重新连接……")
            with suppress(Exception):
                self.cursor.close()
                self.conn.close()
            self.conn = psycopg2.connect(
                host=self.config["ytauto"]["host"],
                port=self.config["ytauto"]["port"],
                user=self.config["ytauto"]["user"],
                password=self.config["ytauto"]["password"],
                dbname=self.config["ytauto"]["dbname"]
            )
            self.conn.autocommit = True
            self.cursor = self.conn.cursor()

    def execute(self, sql: str, fetch: Literal["all", "one", None] = None) -> Any:
        self.__check_connected()
        self.cursor.execute(sql)
        if fetch is not None:
            if fetch == "all":
                results = self.cursor.fetchall()
            else:
                results = self.cursor.fetchone()
            self.conn.commit()
            return results
        self.conn.commit()

    def insert_accounts(self, account: str, password: str, email: str) -> bool:
        """
        向数据库中添加账号信息

        Args:
            account: 账号，一般为邮箱
            password: 密码
            email: 备用邮箱

        Returns:
            bool，是否创建成功
        """
        self.__check_connected()
        with suppress(Exception):
            self.cursor.execute(f"insert into accounts (account, password, email) values ('{account}', '{password}', '{email}');")
            self.conn.commit()
            return True
        self.conn.commit()
        return False

    def delete_accounts(self, ids: tuple) -> bool:
        """
        批量删除账号信息

        Args:
            ids: 需要删除的账号id

        Returns:
            布尔值，是否删除成功
        """
        self.__check_connected()
        with suppress(Exception):
            if len(ids) == 1:
                sql = f"delete from accounts where id={ids[0]}"
            else:
                sql = f"delete from accounts where id in {ids};"
            self.cursor.execute(sql)
            self.conn.commit()
            return True
        self.conn.commit()
        return False

    def get_all_devices_info(self):
        """获取设备表中的所有设备信息"""
        self.__check_connected()
        self.cursor.execute("select id, ip, account, password, \"name\", \"desc\" from devices;")
        return self.cursor.fetchall()

    def insert_device(self, ip: str, account: str, password: str, name: str, desc: str) -> bool:
        """
        插入设备数据信息

        Args:
            device_ip: 设备ip
            account: 设备登录账号
            password: 设备登录密码

        Returns:
            布尔值，是否插入成功
        """
        self.__check_connected()
        with suppress(Exception):
            self.cursor.execute(f"insert into devices (ip, account, password, \"name\", \"desc\") values ('{ip}', '{account}', '{password}', '{name}', '{desc}');")
            self.conn.commit()
            return True
        self.conn.commit()
        return False

    def delete_devices(self, ids: list) -> bool:
        """
        批量删除设备信息

        Args:
            ids: 设备id

        Returns:
            布尔值，是否删除成功
        """
        self.__check_connected()
        with suppress(Exception):
            if len(ids) == 1:
                sql = f"delete from devices where id={ids[0]}"
            else:
                sql = f"delete from devices where id in {ids};"
            self.cursor.execute(sql)
            self.conn.commit()
            return True
        self.conn.commit()
        return False

    def insert_runner_scripts(self, data: list[RunnerScripts]) -> bool:
        """批量插入执行脚本"""
        self.__check_connected()
        values = []
        for script in data:
            value = f"('{script['device']}', '{script['device_account']}', '{script['device_pwd']}', '{script['account']}', '{script['password']}', '{script['email']}', '{script['word']}', '{script['author']}', '{script['name']}', '{script['types']}', '{script['freq']}')"
            values.append(value)
        sql_value = ", ".join(values)
        try:
            sql = f"insert into runner_scripts (device_ip, device_account, device_pwd, account, password, email, word, author, name, types, freq) values {sql_value};"
            self.cursor.execute(sql)
            self.conn.commit()
            return True
        except Exception:
            self.conn.commit()
            return False

    def get_scripts_names(self) -> list[str]:
        self.__check_connected()
        self.cursor.execute(f"select distinct name from runner_scripts;")
        names = [x[0] for x in self.cursor.fetchall()]
        return names

    def get_scripts_and_group(self) -> dict[str, RunnerScripts]:
        """获取脚本数据并进行格式化映射操作"""
        self.__check_connected()
        script_mapping = {}
        self.cursor.execute(f"select distinct name from runner_scripts;")
        names = [x[0] for x in self.cursor.fetchall()]
        for name in names:
            self.cursor.execute(f"select * from runner_scripts where name = '{name}';")
            script_mapping[name] = self.cursor.fetchall()
        return script_mapping

    def get_devices_running_status(self, script_name: str | None = None) -> list[tuple[Any, ...]]:
        """获取所有的设备执行状态"""
        self.__check_connected()
        if script_name is None:
            self.cursor.execute(f"select * from running_status;")
        else:
            self.cursor.execute(f"select * from running_status where script_name='{script_name}';")
        return self.cursor.fetchall()

    def get_device_status(self, device_ip: str, script_name: str):
        self.__check_connected()
        self.cursor.execute(f"select status from running_status where device='{device_ip}' and script_name='{script_name}';")
        result = self.cursor.fetchone()
        if result is not None and len(result) > 0:
            return result[0]
        else:
            return -1

    def delete_script_by_name(self, name: str):
        """通过脚本名称删除脚本"""
        self.__check_connected()
        try:
            self.cursor.execute(f"delete from runner_scripts where name='{name}';")
            self.conn.commit()
            return True
        except Exception:
            self.conn.commit()
            return False


sql = Sql()
 



