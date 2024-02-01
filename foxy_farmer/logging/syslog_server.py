import aioudp

from asyncio import Event
from logging import getLogger
from typing import Dict, Any
from pyparsing import Word, alphas, Suppress, nums, Regex

from foxy_farmer.logging.configure_logging import add_stdout_handler


def map_priority_to_log_level(priority: int) -> int:
    level = priority - 8
    if level == 7:
        return 10
    if level == 6:
        return 20
    if level == 4:
        return 30
    if level == 3:
        return 40
    if level == 2:
        return 50

    return 0


class Parser(object):
    def __init__(self):
        ints = Word(nums)

        # priority
        priority = Suppress("<") + ints + Suppress(">")

        # service
        hostname = Word(alphas + nums + "_" + "-" + ".")

        # message
        message = Regex("(.|\n)*\x00")

        # pattern build
        self.__pattern = priority + hostname + message

    def parse(self, line):
        parsed = self.__pattern.parseString(line)
        priority = int(parsed[0])

        return {
            "log_level": map_priority_to_log_level(priority),
            "service": parsed[1],
            "message": parsed[2].rstrip("\x00"),
        }


class SyslogServer:
    _parser: Parser = Parser()
    _logging_config: Dict[str, Any]
    _stop_event: Event = Event()

    def __init__(self, logging_config: Dict[str, Any]):
        self._logging_config = logging_config

    async def _handle_connection(self, connection):
        async for message in connection:
            parsed = self._parser.parse(bytes.decode(message.strip()))
            logger = getLogger(parsed["service"])
            logger.propagate = False
            if not logger.hasHandlers():
                add_stdout_handler(logger, logging_config=self._logging_config)
            logger.log(parsed["log_level"], parsed["message"])

    async def run(self):
        async with aioudp.serve(host="127.0.0.1", port=self._logging_config["log_syslog_port"], handler=self._handle_connection):
            await self._stop_event.wait()

    def stop(self):
        self._stop_event.set()
