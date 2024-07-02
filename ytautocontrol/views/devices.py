from nicegui import ui
import json
from ytautocontrol.component.base import base_grid
from ytautocontrol.utils.crud import sql
from nicegui.events import UploadEventArguments, ValueChangeEventArguments, ClickEventArguments, GenericEventArguments
from loguru import logger
from ytautocontrol.utils.socket_handler import SocketHandler


# ===================== 全局变量组件 ======================
dialog: ui.dialog
table: ui.table
log_dialog: ui.dialog
log_content_dialog: ui.dialog

# ===================== 全局变量 ===========================
table_rows = []
select_device = ""
insert_device_field = {"ip": "", "account": "", "password": "", "name": "", "desc": ""}
log_select_options = []
log_names = []
log_content = ""


def set_ip(e: ValueChangeEventArguments):
    """设置ip事件回调"""
    insert_device_field["ip"] = e.value


def set_account(e: ValueChangeEventArguments):
    """设置账号事件回调"""
    insert_device_field["account"] = e.value


def set_password(e: ValueChangeEventArguments):
    """设置密码事件回调"""
    insert_device_field["password"] = e.value

def set_name(e: ValueChangeEventArguments):
    insert_device_field["name"] = e.value

def set_desc(e: ValueChangeEventArguments):
    insert_device_field["desc"] = e.value


def set_table_rows():
    """获取并格式化设备数据，赋值给全局变量 table_rows"""
    global table_rows
    table_rows = sorted([{"id": x[0], "ip": x[1], "account": x[2], "name": x[4], "desc": x[5]} for x in sql.get_all_devices_info()], key=lambda x: x["id"])
    

def refresh_table():
    """重新获取并刷新表格数据"""
    set_table_rows()
    device_table.refresh()


@ui.refreshable
def show_log_content_dialog():
    global log_content, log_content_dialog
    with ui.dialog().props("full-width") as log_content_dialog, ui.card().classes("w-full h-full"):
        with ui.card_section().classes("w-full flex justify-end"):
            ui.button("关闭", on_click=log_content_dialog.close)
        with ui.card_section().classes("w-full h-full"):
            log = ui.log().classes("w-full h-full")
            for content in log_content:
                log.push(content)


def show_run_log(e: GenericEventArguments):
    global select_device, log_content_dialog, log_dialog, log_content
    log_name = e.args["row"]["name"]
    log_dialog.close()
    with SocketHandler(select_device) as client:
        log_content = client.get_log_content(log_name)
    show_log_content_dialog.refresh()
    log_content_dialog.open()
    # notify = ui.notification(timeout=None, close_button=True, position="right")
    # notify.message = "</br>".join(log_content)
    # with ui.dialog() as log_content_dialog, ui.card():
    #     with ui.card_section():
    #         log = ui.log()
    #         for content in log_content:
    #             log.push(content)
    # log_content_dialog.open()


@ui.refreshable
def set_log_select_dialog():
    global log_dialog, log_names
    with ui.dialog() as log_dialog, ui.card().classes("w-1/2"):
        with ui.card_section().classes("w-full"):
            cols = [
                {"name": "name", "field": "name", "label": "日志文件", "align": "center"},
                {"name": "event", "field": "event", "label": "操作", "align": "center"},
            ]
            rows = [{"name": x} for x in log_names]
            log_table = ui.table(columns=cols, rows=rows, row_key="name").props("table-header-class='bg-indigo-100'")
            log_table.add_slot("body-cell-event", """
            <q-td :props="props">
                <q-btn label="显示日志" @click="$parent.$emit('show_log', props)" color="primary" outline >
            </q-td>
            """)
            log_table.on("show_log", show_run_log)


def single_device_select(e: GenericEventArguments):
    # ui.notify(e.args["row"]["ip"])
    global log_names, select_device
    select_device = e.args["row"]["ip"]
    with SocketHandler(select_device) as client:
        log_names = client.get_logs()
    set_log_select_dialog.refresh()
    log_dialog.open()
    # 从数据库获取账号密码，进入服务器获取文件信息


async def event_for_insert_device(e: ClickEventArguments):
    """插入设备数据事件回调"""
    global table_rows, dialog
    e.sender.props(add="loading")
    all_devices = [x["ip"] for x in table_rows]
    if insert_device_field["ip"] in all_devices:
        ui.notify(f"插入失败，已存在设备IP：{insert_device_field['ip']}", type="negative")
        e.sender.props(remove="loading")
        logger.error(f"插入数据失败，已存在设备IP：{insert_device_field['ip']}")
        return
    result = sql.insert_device(**insert_device_field)
    if result is True:
        ui.notify("成功插入设备", type="positive")
        refresh_table()
        dialog.close()
    else:
        logger.error(f"插入设备 {insert_device_field['ip']} 失败")
        ui.notify("插入设备数据失败", type="negative")
    e.sender.props(remove="loading")


def dialog_component():
    """dialog弹出框组件设置"""
    with ui.dialog() as dialog, ui.card().classes("w-1/2"):
        with ui.card_section():
            ui.label("添加执行设备").classes("text-lg font-semibold")
        with ui.card_section().classes("w-full"):
            with ui.column().classes("w-full flex space-y-2"):
                ui.input("输入设备名称", on_change=set_name).classes("w-full")
                ui.input("输入设备IP", on_change=set_ip).classes("w-full")
                ui.input("填写备注", on_change=set_desc).classes("w-full")
        with ui.card_section().classes("w-full"):
            with ui.row().classes("flex justify-end w-full"):
                ui.button("提交", on_click=event_for_insert_device)
    return dialog


async def remove_devices(e: ClickEventArguments):
    e.sender.props(add="loading")
    ids = [int(x["id"]) for x in table.selected]
    # await asyncio.sleep()
    result = sql.delete_devices(ids)
    e.sender.props(remove="loading")
    if result is True:
        ui.notify(f"删除设备成功", type="positive")
        refresh_table()
    else:
        logger.error(f"批量删除设备失败")
        ui.notify(f"删除设备失败", type="negative")


@ui.refreshable
def device_table():
    global table_rows, table
    cols = [
        {"name": "id", "label": "ID", "field": "id", "align": "center"},
        {"name": "name", "field": "name", "label": "名称", "align": "center"},
        {"name": "ip", "label": "设备IP", "field": "ip", "align": "center"},
        {"name": "desc", "field": "desc", "label": "备注", "align": "center"},
        {"name": "event", "label": "操作", "fleld": "event", "align": "center"},
    ]
    with ui.table(columns=cols, rows=table_rows, selection="multiple", pagination=10, title="执行设备管理") as table:
        table.classes("w-full")
        with table.add_slot("top-right"):
            ui.button("批量删除", color="red", on_click=remove_devices).bind_visibility_from(table, "selected", backward=lambda val: bool(val)).classes("mr-2")
            ui.button("添加设备", on_click=dialog.open)
        table.add_slot("body-cell-event", """
        <q-td :props="props">
            <q-btn @click="$parent.$emit('check_log', props)" icon="cloud_download" color="primary" size="md" round flat/>
            <q-tooltip class="font-semibold text-md">下载日志文件</q-tooltip>
        </q-td>
        """)
        table.on("check_log", single_device_select)


def upload_callback(e: UploadEventArguments):
    lines = e.content.readlines()
    for line in lines:
        if line:
            try:
                datas = line.decode().strip().split("----")
            except:
                ui.notify(f"解码文件出错，请创建正常的utf8文件，你可以使用 sublime 等程序", type="negative")
                return
            name = datas[0]
            ip = datas[1]
            desc = datas[2]
            result = sql.insert_device(ip, "", "", name, desc)
            if result is False:
                logger.error(f"插入设备 {ip} 失败")
    device_table.refresh()
    ui.run_javascript("location.reload();")


@ui.refreshable
def upload_card():
    with ui.card_section().classes("w-full"):
        ui.markdown("""
        > 上传文件，每个设备占用一行，上传格式为 `设备名称----设备IP----设备描述`，如 `测试设备----192.168.14.111----这是描述文字`，注意中间为四个 `-`，前后的 `----` 不可省略，如果不需要描述，你可以写成 `name----192.168.14.111----`
        """)
    with ui.card().classes("w-full"):
        with ui.card_section().classes("w-full"):
            ui.upload(label="上传设备数据", on_upload=upload_callback).classes("w-full")


@ui.page("/devices")
@base_grid
def devices_page():
    global dialog, table_rows
    set_table_rows()
    set_log_select_dialog()
    show_log_content_dialog()
    dialog = dialog_component()
    upload_card()
    with ui.column().classes("flex w-full"):
        device_table()


