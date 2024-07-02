from nicegui import ui
from ytautocontrol.component.base import base_grid
from ytautocontrol.utils.crud import sql
from nicegui.events import ClickEventArguments, GenericEventArguments
import asyncio
from ytautocontrol.utils.socket_handler import SocketHandler, RunScriptFields
import time
from concurrent.futures.thread import ThreadPoolExecutor
from threading import RLock


# ====================== 全局变量 ======================

scripts = {}
selected_script = []
info_dialog: ui.dialog
device_status = []
lock = RLock()
pool = ThreadPoolExecutor()
script_status = {}


# ====================== 全局组件 =======================

card: ui.card


def get_devices_status():
    """获取所有的设备执行状态"""
    global device_status
    device_status = sql.get_devices_running_status()


@ui.refreshable
def info_dialog_component():
    global info_dialog, selected_script
    with ui.dialog().props("full-width") as info_dialog, ui.card().classes("w-full"):
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
        with ui.card_section().classes("flex justify-end w-full"):
            ui.button("关闭", on_click=info_dialog.close, color='red')
        with ui.card_section().classes("w-full"):
            table = ui.table(columns=cols, rows=selected_script).classes("w-full")
            table.add_slot("body-cell-status", """
            <q-td :props="props">
                <q-badge :color="props.value.color">{{ props.value.label }}</q-badge>
            </q-td>
            """)


# def show_info(data):
def show_info(e: GenericEventArguments):
    """显示脚本详细信息按钮回调"""
    global selected_script, device_status
    script_name = e.args["row"]["script_name"]
    selected_script = [{"id": x[0], "device": x[1], "account": x[4], "word": x[7], "author": x[8], "types": x[10] if x[10] else "", "freq": x[11], "status": {}} for x in scripts[script_name]]
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


async def remove_scripts(e: GenericEventArguments):
    global scripts
    script_name = e.args["row"]["script_name"]
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


def run_script(e: GenericEventArguments):
    global scripts
    script_name = e.args["row"]["script_name"]
    sql.execute(f"delete from running_status where script_name='{script_name}';")
    for script in scripts[script_name]:
        run_fields: RunScriptFields = {"account": script[4], "password": script[5], "email": script[6], "word": script[7], "author": script[8], "filter_type": script[10], "freq": int(script[11]), "addr": script[1], "script_name": script_name}
        with SocketHandler(script[1]) as client:
            client.run_script(run_fields)
    while True:
        results = sql.execute(f"select device from running_status where script_name='{script_name}';", fetch="all")
        status_devices = [x[0] for x in results if len(x) > 0]
        run_devices = [x[1] for x in scripts[script_name]]
        if len(list(set(run_devices).difference(set(status_devices)))) == 0:
            break
        time.sleep(1)
    e.sender.props(remove="loading")
    script_cards.refresh()
    main_card.refresh()
    return True


def checker(e: GenericEventArguments):
    global selected_script
    script_name = e.args["row"]["script_name"]
    lock.acquire()
    run_script(e)
    lock.release()
    while True:
        all_status = sql.get_devices_running_status(script_name)
        if all([x[2] != 0 for x in all_status]):
            lock.acquire()
            script_cards.refresh()
            main_card.refresh()
            lock.release()
            return
        else:
            time.sleep(3)
        lock.acquire()
        script_cards.refresh()
        main_card.refresh()
        lock.release()


async def start_script(e: GenericEventArguments):
    e.sender.props(add="loading")
    future = pool.submit(checker, e)
    # e.sender.props(remove="loading")
    # ui.notify(f"已提交执行任务", type="positive")


@ui.refreshable
def script_cards():
    global device_status, script_status
    cols = [
        {"name": "script_name", "field": "script_name", "label": "脚本名称", "align": "center"},
        {"name": "status", "field": "status", "label": "执行状态", "align": "center"},
        {"name": "events", "field": "events", "label": "脚本操作", "align": "end"},
    ]
    rows = []
    script_names = [x for x in scripts.keys()]
    for name in script_names:
        all_status = sql.get_devices_running_status(name)
        if all([x[2] != 0 for x in all_status]):
            row = {"script_name": name, "status": "已停止"}
            # script_status[name] = 1
        else:
            row = {"script_name": name, "status": "正在执行"}
            # script_status[name] = 0
        rows.append(row)
    table = ui.table(columns=cols, rows=rows, row_key="name").classes("w-full").props("table-header-class='bg-indigo-100 font-semibold text-lg'")
    table.add_slot("body-cell-events", """
    <q-td :props="props">
        <div class="flex gap-4 justify-end">
            <q-btn @click="$parent.$emit('desc', props)" label="详情" color="primary" flat/>
            <q-btn @click="$parent.$emit('run', props)" icon="not_started" color="primary" round/>
            <q-btn @click="$parent.$emit('remove', props)" icon="delete" color="red" round/>
        </div>
    </q-td>
    """)
    table.on("desc", show_info)
    table.on("run", start_script)
    table.on("remove", remove_scripts)

@ui.refreshable
def main_card():
    with ui.card().classes("w-full"):
        with ui.card_section():
            ui.label("脚本管理").classes("text-lg font-semibold")
            ui.markdown("> 点击脚本卡片详情可以展示当前的脚本详细信息")
            ui.markdown("> 脚本以设备为参照，仅可执行一个脚本，不保证多脚本执行的数据显示正确性，如需多设备执行，请添加对应需求的脚本")
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


