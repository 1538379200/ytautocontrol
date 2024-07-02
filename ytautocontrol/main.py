from nicegui import ui, app
from ytautocontrol.views.creator import home_page
from ytautocontrol.views.accouts import account_page
from ytautocontrol.views.devices import devices_page
from ytautocontrol.views.runner import runner_page
from loguru import logger

app.add_static_files("/statics", "./statics/")
logger.add("./log/log_{time}.log", level="ERROR")
ui.run(port=9527, title="YTAuto", reload=False)




