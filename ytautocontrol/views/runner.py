from nicegui import ui
from ytautocontrol.component.base import base_grid
from ytautocontrol.utils.crud import sql
from nicegui.events import ClickEventArguments
import asyncio
from ytautocontrol.utils.socket_handler import SocketHandler, RunScriptFields
import time


# ====================== 全局变量 ======================

scripts = {}
selected_script = []
info_dialog: ui.dialog
device_status = []


# ====================== 全局组件 =======================

card: ui.card


def get_devices_status():
    """获取所有的设备执行状态"""
    global device_status
    device_status = sql.get_devices_running_status()


@ui.refreshable
def info_dialog_component():
    global info_dialog, selected_script
    with ui.dialog() as info_dialog, ui.card().classes("w-full"):
        info_dialog.classes("w-full")
        cols = [
            {"name": "id", "field": "id", "label": "ID", "align": "center"},
            {"name": "device", "field": "device", "label": "设备IP", "align": "center"},
            {"name": "account", "field": "account", "label": "youtube账户", "align": "center"},
            {"name": "word", "field": "word", "label": "搜索关键词", "align": "center"},
            {"name": "author", "field": "author", "label": "视频作者", "align": "center"},
            {"name": "types", "field": "types", "label": "筛选类型", "align": "center"},
            {"name": "freq", "field": "freq", "label": "轮检次数", "align": "center"},
            {"name": "status", "field": "status", "label": "执行状态", "align": "center"},
        ]

        table = ui.table(columns=cols, rows=selected_script).classes("w-full")
        table.add_slot("body-cell-status", """
        <q-td :props="props">
            <q-badge :color="props.value.color">{{ props.value.label }}</q-badge>
        </q-td>
        """)


def show_info(data):
    """显示脚本详细信息按钮回调"""
    global selected_script, device_status
    selected_script = [{"id": x[0], "device": x[1], "account": x[4], "word": x[7], "author": x[8], "types": x[10] if x[10] else "", "freq": x[11], "status": {}} for x in scripts[data]]
    for s in selected_script:
        sql.cursor.execute(f"select status from running_status where device='{s['device']}';")
        the_status = sql.cursor.fetchone()
        status = {"color": "blue-grey", "label": "未知"}
        if the_status:
            match the_status[0]:
                case 0:
                    status = {"color": "blue", "label": "执行中"}
                case 1:
                    status = {"color": "green", "label": "成功"}
                case 2:
                    status = {"color": "red", "label": "失败"}
                case _:
                    status = {"color": "blue-grey", "label": "未知"}
        s["status"] = status
    info_dialog_component.refresh()
    info_dialog.open()


def run(script_name: str):
    global scripts
    sql.cursor.execute("delete from running_status;")
    sql.conn.commit()
    for s in scripts[script_name]:
        run_script: RunScriptFields = {"account": s[4], "password": s[5], "email": s[6], "word": s[7], "author": s[8], "filter_type": s[10], "freq": int(s[11]), "addr": s[1], "script_name": script_name}
        with SocketHandler(s[1]) as client:
            client.run_script(run_script)
    while True:
        sql.cursor.execute(f"select device from running_status;")
        status_devices = [x[0] for x in sql.cursor.fetchall() if len(x) > 0]
        run_devices = [x[1] for x in scripts[script_name]]
        if len(list(set(run_devices).difference(set(status_devices)))) == 0:
            break
        time.sleep(1)
    return True


def start_script(e: ClickEventArguments, data):
    """执行当前指定脚本"""
    global selected_script
    # 执行代码
    e.sender.props(add="loading")
    run(data)
    ui.notify(f"已启动任务")
    async def status_checker():
        while True:
            devices = [x[1] for x in scripts[data]]
            status = {}
            results = []
            for device in devices:
                result = sql.get_device_status(device)
                results.append(result)
                status[device] = result
            for s in selected_script:
                status = {"color": "blue-grey", "label": "未知"}
                the_status = status[s["device"]]
                if the_status:
                    match the_status[0]:
                        case 0:
                            status = {"color": "blue", "label": "执行中"}
                        case 1:
                            status = {"color": "green", "label": "成功"}
                        case 2:
                            status = {"color": "red", "label": "失败"}
                        case _:
                            status = {"color": "blue-grey", "label": "未知"}
                s["status"] = status
            if all([x != 0 for x in results]):
                e.sender.props(remove="loading")
                break
            info_dialog_component.refresh()
            await asyncio.sleep(5)
        script_cards.refresh()
        main_card.refresh()
    asyncio.run()

async def remove_scripts(e: ClickEventArguments, script_name: str):
    global scripts
    e.sender.props(add="loading")
    result = sql.delete_script_by_name(script_name)
    if result is True:
        ui.notify("删除脚本成功", type='positive')
        scripts = sql.get_scripts_and_group()
        script_cards.refresh()
        main_card.refresh()
    else:
        ui.notify("删除脚本失败", type="negative")
    e.sender.props(remove="loading")


@ui.refreshable
def script_cards():
    global device_status
    for script_name in scripts.keys():
        with ui.card().classes("w-full bg-indigo-100").on("click", lambda: show_info(script_name)):
            with ui.row().classes("flex w-full items-center space-x-2"):
                ui.label(script_name).classes("flex-1 text-md font-semibold")
                with ui.button(icon="not_started", on_click=lambda e: start_script(e, script_name)).props("round"):
                    ui.tooltip("执行脚本")
                with ui.button(icon="delete", color="red", on_click=lambda e: remove_scripts(e, script_name)).props("round"):
                    ui.tooltip("删除脚本")


@ui.refreshable
def main_card():
    with ui.card().classes("w-full"):
        with ui.card_section():
            ui.label("脚本管理").classes("text-lg font-semibold")
            ui.markdown("> 点击脚本卡片可以展示当前的脚本详细信息")
        with ui.card_section().classes("w-full"):
            ui.separator()
        with ui.card_section().classes("w-full"):
            with ui.column().classes("flex space-y-2 w-full"):
                script_cards()



@ui.page("/runner")
@base_grid
def runner_page():
    global scripts
    get_devices_status()
    info_dialog_component()
    scripts = sql.get_scripts_and_group()
    main_card()


