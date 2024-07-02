from nicegui import ui
from enum import Enum
from loguru import logger
from ytautocontrol.component.base import base_grid
from ytautocontrol.utils.crud import sql
from nicegui.events import UploadEventArguments, ClickEventArguments


@ui.page("/accounts")
@base_grid
def account_page():
    cols_fields = [
        {"name": "id", "label": "ID", "field": "id", "align": "center"},
        {"name": "account", "label": "Google账号", "field": "account", "align": "center"},
        {"name": "password", "label": "Google密码", "field": "password", "align": "center"},
        {"name": "email", "label": "备用邮箱", "field": "email", "align": "center"},
    ]
    # rows = [
    #     {"id": 0, "account": "12345", "password": "12445", "email": "122@ss"}
    # ]
    # ui.notify(sql.get_all_accounts())
    new_rows = [
        {"id": 1, "account": "888", "password": "999", "email": "111"}
    ]
    data = {"account": "", "password": "", "email": ""}


    def set_account(e):
        nonlocal data
        data["account"] = e.value


    def set_pwd(e):
        nonlocal data
        data["password"] = e.value


    def set_email(e):
        nonlocal data
        data["email"] = e.value


    def submit(e: ClickEventArguments):
        e.sender.props(add="loading")
        if not all(data.values()):
            ui.notify("请填写所有数据后再操作",type="negative")
            return
        # 进行数据库数据保存操作
        result = sql.insert_accounts(**data)
        e.sender.props(remove="loading")
        dialog.close()
        if result is True:
            # ui.notify("成功创建数据", type="positive")
            logger.success(f"成功插入账号：{data['account']}")
            ui.run_javascript("location.reload();")
        else:
            logger.error(f"插入账号 {data['account']} 失败")
            ui.notify("创建失败", type="negative")


    def remove_accounts(e: ClickEventArguments):
        """删除所有账号点击事件"""
        e.sender.props(add="loading")
        selected_ids = [int(x["id"]) for x in table.selected]
        selected_ids = tuple(selected_ids)
        result = sql.delete_accounts(selected_ids)
        e.sender.props(remove="loading")
        if result is False:
            logger.error(f"批量删除账号失败：{selected_ids}")
            ui.notify("删除失败", type="negative")
            return
        logger.success(f"成功删除账号组：{selected_ids}")
        ui.run_javascript("location.reload();")


    def upload_accounts(e: UploadEventArguments):
        """账号文件上传事件"""
        lines = e.content.readlines()
        for line in lines:
            if line:
                datas = line.decode().strip().split("----")
                if len(datas) < 2:
                    logger.error(f"数据不全，未插入账号：{datas[0]}")
                    continue
                elif len(datas) == 2:
                    result = sql.insert_accounts(datas[0], datas[1], "")
                else:
                    result = sql.insert_accounts(datas[0], datas[1], datas[2])
                if result is False:
                    logger.error(f"插入账号 {datas[0]} 失败")
                else:
                    logger.success(f"成功插入账号：{datas[0]}")
        ui.run_javascript("location.reload();")


    with ui.dialog().classes() as dialog, ui.card().classes("w-1/2 h-2/3 border-1"):
        with ui.card_section().classes("w-full bg-indigo-600"):
            ui.label("添加账号数据").classes("text-lg font-semibold w-full text-white")
        with ui.card_section().classes("w-full flex flex-col h-full"):
            with ui.column().classes("w-full flex-1 flex space-y-4"):
                validator = {"必填": lambda value: len(value) > 0}
                ui.input("输入账号",  validation=validator, on_change=set_account).classes("w-full")
                ui.input("输入密码", validation=validator, on_change=set_pwd).classes("w-full")
                ui.input("输入备用邮箱", validation=validator, on_change=set_email).classes("w-full")
            with ui.row().classes("flex-none flex justify-end"):
                ui.button("提交", on_click=submit).props("flat").classes("bg-indigo-600 hover:bg-indigo-600/80 text-white font-semibold")
    rows = [{"id": x[0], "account": x[1], "password": x[2], "email": x[3]} for x in sql.get_all_accounts()]
    rows.sort(key=lambda x: x["id"])
    with ui.card().classes("w-full"):
        ui.markdown("""
        > 使用TXT文件上传，文件内容每个账号占一行，内容格式为 “xxx----xxx----xxx” 分别代表 账号----密码----备用邮箱，如：
        > ```
        > testuser@gmail.com----&##43grfd7----testuser@firfox.com
        > ```
        """)
    ui.upload(label="使用文件上传", on_upload=upload_accounts).classes("w-full")
    with ui.table(columns=cols_fields, rows=rows, selection="multiple", title="账号资源管理", pagination=10).classes("w-full") as table:
        with table.add_slot("top-right"):
            ui.button("批量删除", color="red", on_click=remove_accounts).bind_visibility_from(table, "selected", backward=lambda val: bool(val)).classes("mr-2")
            ui.button("增加数据", on_click=dialog.open)
