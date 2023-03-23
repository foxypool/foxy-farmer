import asyncio
import logging
from asyncio import sleep
from typing import Optional

from chia.farmer.farmer import Farmer
from chia.server.outbound_message import NodeType
from chia.server.start_service import Service

from foxy_farmer.foxy_farming_gateway import foxy_farming_gateway_address, foxy_farming_gateway_port
from foxy_farmer.service_wrapper import ServiceWrapper


class GatewayAvailabilityMonitor:
    _farmer_service: ServiceWrapper
    _reconnect_if_necessary_task: Optional[asyncio.Task] = None
    _logger: logging.Logger = logging.getLogger("gateway_availability_monitor")

    def __init__(self, farmer_service: Service[Farmer]):
        self._farmer_service = ServiceWrapper(farmer_service)

    def start(self):
        self._reconnect_if_necessary_task = asyncio.create_task(
            self._periodically_reconnect_if_necessary_task()
        )

    def stop(self):
        self._reconnect_if_necessary_task.cancel()

    async def _periodically_reconnect_if_necessary_task(self):
        time_slept = 0
        while True:
            await sleep(1)
            time_slept += 1
            if time_slept < 60:
                continue
            time_slept = 0
            self._reconnect_if_necessary()

    def _reconnect_if_necessary(self):
        if self._is_farmer_connected_to_gateway() is True:
            return
        try:
            self._reconnect_to_gateway()
        except Exception as error:
            self._logger.error(f"Failed to reconnect to the Chia Farming Gateway because an error occurred: {error}")

    def _is_farmer_connected_to_gateway(self):
        return self._farmer_service.has_active_connections(node_type=NodeType.FULL_NODE)

    def _reconnect_to_gateway(self):
        self._farmer_service.remove_all_peers()
        self._farmer_service.add_peer_with_hostname(foxy_farming_gateway_address, foxy_farming_gateway_port)
