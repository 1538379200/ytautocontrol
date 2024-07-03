from nicegui import ui
from functools import wraps


def __base_sidebar():
    # ui.button("账号管理", on_click=lambda: ui.navigate.to("/accounts"), icon="account_circle").props("flat").classes("w-full text-black text-start")
    ui.tree([
        {"id": "/", "label": "创建执行"},
        {"id": "/accounts", "label": "账号管理"},
        {"id": "/devices", "label": "设备管理"},
        {"id": "/runner", "label": "执行管理"},
    ], label_key="label", on_select=lambda e: ui.navigate.to(e.value)).classes("w-full flex flex-col space-y-2")

def __menu_component():
    ui.menu_item("示例菜单功能", on_click=lambda: ui.notify("这是留给后续使用的菜单接口"))


def base_grid(func):
    @wraps(func)
    def inner(*args, **kwargs):
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
                func(*args, **kwargs)
    return inner





