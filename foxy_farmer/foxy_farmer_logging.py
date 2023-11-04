from logging import getLogger, StreamHandler
from pathlib import Path
from typing import Dict
from colorlog import ColoredFormatter

from chia.util.chia_logging import initialize_logging, default_log_level


def initialize_logging_with_stdout(logging_config: Dict, root_path: Path):
    service_name = "foxy_farmer"
    initialize_logging(
        service_name=service_name,
        logging_config=logging_config,
        root_path=root_path,
    )
    file_name_length = 33 - len(service_name)
    log_date_format = "%Y-%m-%dT%H:%M:%S"
    stdout_handler = StreamHandler()
    stdout_handler.setFormatter(
        ColoredFormatter(
            f"%(asctime)s.%(msecs)03d {service_name} %(name)-{file_name_length}s: "
            f"%(log_color)s%(levelname)-8s%(reset)s %(message)s",
            datefmt=log_date_format,
            reset=True,
        )
    )
    log_level = logging_config.get("log_level", default_log_level)
    stdout_handler.setLevel(log_level)
    root_logger = getLogger()
    root_logger.addHandler(stdout_handler)
