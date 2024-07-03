from nicegui import ui, app
from ytautocontrol.views.creator import home_page
from ytautocontrol.views.accouts import account_page
from ytautocontrol.views.devices import devices_page
from ytautocontrol.views.runner import runner_page
from loguru import logger
from pathlib import Path
from contextlib import suppress


log_dir = Path(__file__).resolve().parent / "log"

logger.info("清理过往日志")
for log in log_dir.glob("*.log"):
    with suppress(PermissionError):
        log.unlink(missing_ok=True)
app.add_static_files("/statics", "./statics/")
logger.add("./log/log_{time}.log", level="ERROR")
# ui.run(port=9527, title="YTAuto", reload=False)
ui.run(port=9527, title="YTAuto", favicon="statics/youtube.svg")





