import logging
from contextlib import contextmanager
from logging import Logger, StreamHandler, getLogger
from pathlib import Path
from typing import Dict, Iterator

from chia.util.chia_logging import initialize_logging, default_log_level
from colorlog import ColoredFormatter


def add_stdout_handler(logger: Logger, logging_config: Dict):
    service_name = "foxy_farmer"
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
    stdout_handler.setLevel(logging_config.get("log_level", default_log_level))
    logger.addHandler(stdout_handler)


def initialize_logging_with_stdout(logging_config: Dict, root_path: Path):
    service_name = "foxy_farmer"
    initialize_logging(
        service_name=service_name,
        logging_config={
            "log_filename": logging_config["log_filename"],
            "log_level": logging_config["log_level"],
            "log_maxbytesrotation": logging_config.get(
                "log_maxbytesrotation",
                logging_config.get("log_maxbytessrotation", 52428800)
            ),
            "log_maxfilesrotation": logging_config.get("log_maxfilesrotation", 7),
            "log_stdout": False,
            "log_syslog": False,
            "log_syslog_host": "127.0.0.1",
            "log_syslog_port": 514,
        },
        root_path=root_path,
    )

    root_logger = getLogger()
    add_stdout_handler(root_logger, logging_config=logging_config)


@contextmanager
def disabled_logging() -> Iterator[None]:
    logging.disable(level=logging.CRITICAL)
    try:
        yield
    finally:
        logging.disable(level=logging.NOTSET)

