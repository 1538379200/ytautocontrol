from nicegui import ui
from ytautocontrol.component.base import base_grid
from ytautocontrol.utils.crud import sql
from nicegui.events import ValueChangeEventArguments, ClickEventArguments
from copy import deepcopy


# =================== 全局变量 =====================
global_word = ""
global_author = ""
global_types = ""
# devices = [{"id": x[0], "ip": x[1], "account": x[2], "password": x[3]} for x in sql.get_all_devices_info()]
# accounts = [{"id": x[0], "account": x[1], "password": x[2], "email": x[3]} for x in sql.get_all_accounts()]
devices = []
accounts = []
devices_selected = []
# device_options = list(set([x["ip"] for x in devices]).difference([x["device"] for x in devices_selected]))
# account_options = list(set([x["account"] for x in accounts]).difference(x["account"] for x in devices_selected))
device_options = []
account_options = []
# add_runner_data = {"device": "", "account": "", "word": "", "author": ""}
script_name = ""
add_runner_data = {"device": "", "device_account": "", "device_pwd": "", "account": "", "password": "", "email": "", "word": "", "author": "", "name": "", "types": "", "freq": 2}


# =================== 全局组件 =====================
table: ui.table
dialog: ui.dialog
dialog2: ui.dialog


@ui.refreshable
def device_selector():
    ui.select(device_options, label="添加执行设备", with_input=True, on_change=set_device).classes("w-full")


@ui.refreshable
def account_selector():
    ui.select(account_options, label="添加youtube账号", with_input=True, on_change=set_account).classes("w-full")



async def add_runner(e: ClickEventArguments):
    """添加执行设备回调"""
    global add_runner_data, device_options, account_options, global_word, global_author, script_name, global_types
    e.sender.props(add="loading")
    if not all([add_runner_data["device"], add_runner_data["account"]]):
        ui.notify("设备和账户信息不能为空", type="negative")
        e.sender.props(remove="loading")
        return 
    add_runner_data["device_account"], add_runner_data["device_pwd"] = [(x["account"], x["password"]) for x in devices if x["ip"] == add_runner_data["device"]][0]
    add_runner_data["password"], add_runner_data["email"] = [(x["password"], x["email"]) for x in accounts if x["account"] == add_runner_data["account"]][0]
    if not add_runner_data["word"]:
        if not global_word:
            ui.notify("未设置搜索词或者全局搜索词", type="negative")
            e.sender.props(remove="loading")
            return
        add_runner_data["word"] = global_word
    if not add_runner_data["author"]:
        if not global_author:
            ui.notify("未设置作者名称或者全局作者名", type="negative")
            e.sender.props(remove="loading")
        add_runner_data["author"] = global_author
    if not add_runner_data["types"]:
        add_runner_data["types"] = global_types
    devices_selected.append(add_runner_data)
    device_options = list(set([x["ip"] for x in devices]).difference([x["device"] for x in devices_selected]))
    account_options = list(set([x["account"] for x in accounts]).difference(x["account"] for x in devices_selected))
    e.sender.props(remove="loading")
    dialog.close()
    runner_table.refresh()
    device_selector.refresh()
    account_selector.refresh()
    # add_runner_data = {"device": "", "account": "", "word": "", "author": ""}
    # add_runner_data = {"device": "", "device_account": "", "device_pwd": "", "account": "", "password": "", "email": "", "word": "", "author": "", "name": ""}
    add_runner_data = {"device": "", "device_account": "", "device_pwd": "", "account": "", "password": "", "email": "", "word": "", "author": "", "name": "", "types": "", "freq": 2}
    ui.notify("添加设备成功", type="positive")


async def save_runner_script(e: ClickEventArguments):
    """保存执行脚本"""
    global script_name
    e.sender.props(add="loading")
    selected_copy = deepcopy(devices_selected)
    for script in selected_copy:
        script["name"] = script_name
    result = sql.insert_runner_scripts(selected_copy)
    if result is False:
        ui.notify("保存失败", type='negative')
    else:
        ui.notify("保存成功", type="positive")
    script_name = ""
    e.sender.props(remove="loading")
    dialog2.close()


def set_device(e: ValueChangeEventArguments):
    """设置设备选择框"""
    global add_runner_data
    add_runner_data["device"] = e.value


def set_account(e: ValueChangeEventArguments):
    """设置账号选择框"""
    global add_runner_data
    add_runner_data["account"] = e.value


def set_word(e: ValueChangeEventArguments):
    """输入搜索词输入框"""
    global add_runner_data
    add_runner_data["word"] = e.value


def set_author(e: ValueChangeEventArguments):
    """设置作者输入框"""
    global add_runner_data
    add_runner_data["author"] = e.value


def set_filter_types(e: ValueChangeEventArguments):
    """设置过滤类型"""
    global add_runner_data
    add_runner_data["types"] = e.value


def set_freq(e: ValueChangeEventArguments):
    global add_runner_data
    add_runner_data["freq"] = e.value


def remove_selected_device(e: ClickEventArguments):
    """删除选择设备回调"""
    global table, device_options, account_options, add_runner_data
    # add_runner_data = {"device": "", "account": "", "word": "", "author": ""}
    # add_runner_data = {"device": "", "device_account": "", "device_pwd": "", "account": "", "password": "", "email": "", "word": "", "author": "", "name": ""}
    add_runner_data = {"device": "", "device_account": "", "device_pwd": "", "account": "", "password": "", "email": "", "word": "", "author": "", "name": "", "types": "", "freq": 2}
    selected_devices = table.selected
    for d in selected_devices:
        devices_selected.remove(d)
    device_options = list(set([x["ip"] for x in devices]).difference([x["device"] for x in devices_selected]))
    account_options = list(set([x["account"] for x in accounts]).difference(x["account"] for x in devices_selected))
    runner_table.refresh()
    device_selector.refresh()
    account_selector.refresh()
    ui.notify(f"删除成功", type="positive")


def save_dialog():
    global dialog2
    with ui.dialog() as dialog2, ui.card().classes("w-1/2"):
        with ui.card_section():
            ui.label("填写名称").classes("text-lg font-semibold")
        with ui.card_section().classes("w-full"):
            ui.separator()
        with ui.card_section().classes("w-full"):
            ui.input("输入脚本名称").bind_value(globals(), "script_name").classes("w-full")
        with ui.card_section().classes("w-full"):
            with ui.row().classes("flex justify-end"):
                ui.button("提交", on_click=save_runner_script)


def insert_dialog():
    """插入执行设备框"""
    global dialog, add_runner_data, add_runner_data
    add_runner_data = {"device": "", "device_account": "", "device_pwd": "", "account": "", "password": "", "email": "", "word": "", "author": "", "name": "", "types": "", "freq": 2}
    with ui.dialog() as dialog, ui.card().classes("w-1/2"):
        with ui.card_section():
            ui.label("添加执行设备").classes("text-lg font-semibold")
        with ui.card_section().classes("w-full"):
            with ui.column().classes("flex space-y-2 w-full"):
                # ui.select([x["ip"] for x in devices], label="添加执行设备", with_input=True, on_change=set_device).classes("w-full")
                # ui.select(device_options, label="添加执行设备", with_input=True, on_change=set_device).classes("w-full")
                # ui.select([x["account"] for x in accounts], label="添加youtube账号", with_input=True, on_change=set_account).classes("w-full")
                device_selector()
                account_selector()
                ui.input("输入关键词（标题）", on_change=set_word).classes("w-full")
                ui.input("输入直播者名称", on_change=set_author).classes("w-full")
                ui.input("输入额外过滤类型", on_change=set_filter_types).classes("w-full")
                with ui.number("输入最大轮检次数", on_change=set_freq, step=1, min=1, value=2).classes("w-full"):
                    ui.tooltip("最大轮检次数，指在所有数据加载完未找到目标的情况下，重新进行搜索的次数")
        with ui.card_section().classes("w-full"):
            with ui.row().classes("flex justify-end"):
                ui.button("添加", on_click=add_runner)


@ui.refreshable
def runner_table():
    global table
    cols = [
        {"name": "device", "field": "device", "label": "设备", "align": "center"},
        {"name": "account", "field": "account", "label": "youtube账号", "align": "center"},
        {"name": "word", "field": "word", "label": "搜索关键词", "align": "center"},
        {"name": "author", "field": "author", "label": "作者", "align": "center"},
        {"name": "types", "field": "types", "label": "筛选字段", "align": "center"},
        {"name": "freq", "field": "freq", "label": "最大轮检", "align": "center"},
    ]
    table = ui.table(columns=cols, rows=devices_selected, row_key="device", selection="multiple").classes("w-full")
    with table.add_slot("top-right"):
        with ui.row().classes("flex space-x-2"):
            ui.button("批量删除", color="red", on_click=remove_selected_device).bind_visibility_from(table, "selected", backward=lambda val: bool(val)).classes("mr-2")
            ui.button("保存当前执行设备数据", on_click=dialog2.open).props("flat").classes("bg-indigo-100")
            ui.button("增加执行设备", on_click=dialog.open)


@ui.page("/")
def home_page():
    global global_word, global_author, devices, accounts, device_options, account_options
    with ui.row().classes("fixed top-0 left-0 right-0 bg-indigo-600 w-full h-14 z-10"):
        with ui.row().classes("flex w-full h-full items-center justify-center mx-4"):
            ui.button("YTYOUNB", on_click=lambda: ui.navigate.to("/")).props("flat").classes("flex-1 font-bold text-white text-lg bg-indigo-700 hover:bg-indigo-600/80")
            with ui.row().classes("flex-none"):
                ui.button(icon="menu").props("flat").classes("text-white")
                with ui.menu():
                    # __menu_component()
                    ui.menu_item("示例菜单功能", on_click=lambda: ui.notify("这是留给后续使用的菜单接口"))
    with ui.column().classes("my-20 fixed left-0 ml-4 w-1/4 h-2/4"):
        with ui.card().classes("w-1/2 h-full"):
            ui.label("页面导航").classes("text-lg font-semibold")
            ui.separator()
            # __base_sidebar()
            ui.tree([
                {"id": "/", "label": "创建执行"},
                {"id": "/accounts", "label": "账号管理"},
                {"id": "/devices", "label": "设备管理"},
                {"id": "/runner", "label": "执行管理"},
            ], label_key="label", on_select=lambda e: ui.navigate.to(e.value)).classes("w-full flex flex-col space-y-2")
    with ui.row().classes("w-full h-full"):
        with ui.column().classes("mt-20 mx-80 h-full w-full"):
            devices = [{"id": x[0], "ip": x[1], "account": x[2], "password": x[3]} for x in sql.get_all_devices_info()]
            accounts = [{"id": x[0], "account": x[1], "password": x[2], "email": x[3]} for x in sql.get_all_accounts()]
            devices_selected = []
            device_options = list(set([x["ip"] for x in devices]).difference([x["device"] for x in devices_selected]))
            account_options = list(set([x["account"] for x in accounts]).difference(x["account"] for x in devices_selected))
            with ui.card().classes("w-full"):
                with ui.card_section():
                    ui.label("全局数据").classes("text-lg font-semibold")
                    ui.label("当你未设置搜索关键词和视频作者时，将使用全局数据填入，利用此方法，避免重复数据填写").classes("text-md")
                with ui.card_section().classes("w-full"):
                    with ui.row().classes("flex justify-center").classes("w-full"):
                        ui.input("全局搜索词").bind_value(globals(), "global_word")
                        ui.input("全局作者名").bind_value(globals(), "global_author")
                        ui.input("全局过滤项").bind_value(globals(), "global_types")
            save_dialog()
            insert_dialog()
            runner_table()
