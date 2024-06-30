from nicegui import ui
from ytautocontrol.component.base import base_grid
from ytautocontrol.utils.crud import sql
from nicegui.events import ValueChangeEventArguments, ClickEventArguments, GenericEventArguments
from loguru import logger


# ===================== 全局变量组件 ======================
dialog: ui.dialog
table: ui.table
log_dialog: ui.dialog

# ===================== 全局变量 ===========================
table_rows = []
insert_device_field = {"ip": "", "account": "", "password": ""}
log_select_options = []


def set_ip(e: ValueChangeEventArguments):
    """设置ip事件回调"""
    insert_device_field["ip"] = e.value


def set_account(e: ValueChangeEventArguments):
    """设置账号事件回调"""
    insert_device_field["account"] = e.value


def set_password(e: ValueChangeEventArguments):
    """设置密码事件回调"""
    insert_device_field["password"] = e.value


def set_table_rows():
    """获取并格式化设备数据，赋值给全局变量 table_rows"""
    global table_rows
    table_rows = sorted([{"id": x[0], "ip": x[1], "account": x[2]} for x in sql.get_all_devices_info()], key=lambda x: x["id"])
    

def refresh_table():
    """重新获取并刷新表格数据"""
    set_table_rows()
    device_table.refresh()


def set_log_select_dialog():
    global log_dialog
    with ui.dialog() as log_dialog, ui.card().classes("w-1/2"):
        with ui.card_section().classes("w-full"):
            ui.button("测试")


def single_device_select(e: GenericEventArguments):
    # ui.notify(e.args["row"]["ip"])
    log_dialog.open()
    # 从数据库获取账号密码，进入服务器获取文件信息


async def event_for_insert_device(e: ClickEventArguments):
    """插入设备数据事件回调"""
    global table_rows, dialog
    e.sender.props(add="loading")
    all_devices = [x["ip"] for x in table_rows]
    if insert_device_field["ip"] in all_devices:
        ui.notify(f"插入失败，已存在设备IP：{insert_device_field['ip']}")
        logger.error(f"插入数据失败，已存在设备IP：{insert_device_field['ip']}")
    result = sql.insert_device(**insert_device_field)
    if result is True:
        ui.notify("成功插入设备", type="positive")
        refresh_table()
        dialog.close()
    else:
        logger.error(f"插入设备 {insert_device_field['ip']} 失败")
        ui.notify("插入设备数据失败", type="negative")


def dialog_component():
    """dialog弹出框组件设置"""
    with ui.dialog() as dialog, ui.card().classes("w-1/2"):
        with ui.card_section():
            ui.label("添加执行设备").classes("text-lg font-semibold")
        with ui.card_section().classes("w-full"):
            with ui.column().classes("w-full flex space-y-2"):
                ui.input("输入设备IP", on_change=set_ip).classes("w-full")
                ui.input("输入设备账号", on_change=set_account).classes("w-full")
                ui.input("输入设备密码", on_change=set_password).classes("w-full")
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
        {"name": "ip", "label": "设备IP", "field": "ip", "align": "center"},
        {"name": "account", "label": "设备账号", "field": "account", "align": "center"},
        {"name": "event", "label": "操作", "fleld": "event", "align": "center"},
        # {"name": "password", "label": "设备密码", "field": "password"},
    ]
    with ui.table(columns=cols, rows=table_rows, selection="multiple", pagination=10, title="执行设备管理") as table:
        table.classes("w-full")
        with table.add_slot("top-right"):
            ui.button("批量删除", color="red", on_click=remove_devices).bind_visibility_from(table, "selected", backward=lambda val: bool(val)).classes("mr-2")
            ui.button("添加设备", on_click=dialog.open)
        table.add_slot("body-cell-event", """
        <q-td :props="props">
            <q-btn @click="$parent.$emit('add', props)" icon="cloud_download" color="primary" size="md" round flat/>
            <q-tooltip class="font-semibold text-md">下载日志文件</q-tooltip>
        </q-td>
        """)
        table.on("add", single_device_select)


@ui.page("/devices")
@base_grid
def devices_page():
    global dialog, table_rows
    set_table_rows()
    set_log_select_dialog()
    dialog = dialog_component()
    with ui.column().classes("flex w-full"):
        device_table()


