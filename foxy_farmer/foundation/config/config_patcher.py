from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union, Callable

from chia.util.bech32m import decode_puzzle_hash
from typing_extensions import Self

from foxy_farmer.foundation.util.dictionary import get_nested_dict_value, set_nested_dict_value, del_nested_dict_value


@dataclass
class ConfigPatcherResult:
    foxy_farmer_config_was_updated: bool
    chia_config_was_updated: bool


class ConfigPatcher:
    _foxy_farmer_config: Dict[str, Any]
    _chia_config: Dict[str, Any]
    _is_chia_config_updated: bool = False
    _is_foxy_farmer_config_updated: bool = False

    def __init__(self, foxy_farmer_config: Dict[str, Any], chia_config: Dict[str, Any]):
        self._foxy_farmer_config = foxy_farmer_config
        self._chia_config = chia_config

    def patch(
        self,
        foxy_farmer_config_key_path: Union[List[str], str],
        chia_config_key_path: Optional[Union[List[str], str]] = None
    ) -> Self:
        if chia_config_key_path is None:
            chia_config_key_path = foxy_farmer_config_key_path

        resolved_foxy_farmer_config_key_path: List[str] = foxy_farmer_config_key_path if isinstance(foxy_farmer_config_key_path, list) else foxy_farmer_config_key_path.split(".")
        resolved_chia_config_key_path: List[str] = chia_config_key_path if isinstance(chia_config_key_path, list) else chia_config_key_path.split(".")

        foxy_farmer_config_value = get_nested_dict_value(self._foxy_farmer_config, resolved_foxy_farmer_config_key_path)
        chia_config_value = get_nested_dict_value(self._chia_config, resolved_chia_config_key_path)

        if foxy_farmer_config_value is not None and chia_config_value != foxy_farmer_config_value:
            set_nested_dict_value(self._chia_config, resolved_chia_config_key_path, foxy_farmer_config_value)
            self._is_chia_config_updated = True

        return self

    def patch_value(self, chia_config_key_path: Union[List[str], str], value: Any) -> Self:
        resolved_chia_config_key_path: List[str] = chia_config_key_path if isinstance(chia_config_key_path, list) else chia_config_key_path.split(".")
        chia_config_value = get_nested_dict_value(self._chia_config, resolved_chia_config_key_path)

        if chia_config_value != value:
            set_nested_dict_value(self._chia_config, resolved_chia_config_key_path, value)
            self._is_chia_config_updated = True

        return self

    def remove_config_key(self, chia_config_key_path: Union[List[str], str]) -> Self:
        resolved_chia_config_key_path: List[str] = chia_config_key_path if isinstance(chia_config_key_path, list) else chia_config_key_path.split(".")
        chia_config_value = get_nested_dict_value(self._chia_config, resolved_chia_config_key_path)

        if chia_config_value is not None:
            del_nested_dict_value(self._chia_config, resolved_chia_config_key_path)
            self._is_chia_config_updated = True

        return self

    def sync_pool_payout_address(self) -> Self:
        pool_payout_address_ph = decode_puzzle_hash(self._foxy_farmer_config["pool_payout_address"]).hex()
        if self._foxy_farmer_config.get("plot_nfts") is not None:
            for pool in self._foxy_farmer_config["plot_nfts"]:
                if pool["payout_instructions"] != pool_payout_address_ph:
                    pool["payout_instructions"] = pool_payout_address_ph
                    self._is_foxy_farmer_config_updated = True

        self.patch("plot_nfts", "pool.pool_list")

        self.patch_pool_list_value(key="payout_instructions", value=pool_payout_address_ph)

        return self

    def patch_pool_list_closure(self, closure: Callable[[Dict[str, Any]], bool]) -> Self:
        if self._chia_config["pool"].get("pool_list") is not None:
            for pool in self._chia_config["pool"]["pool_list"]:
                if closure(pool):
                    self._is_chia_config_updated = True

        return self

    def patch_pool_list_value(self, key: str, value: Any) -> Self:
        if self._chia_config["pool"].get("pool_list") is not None:
            for pool in self._chia_config["pool"]["pool_list"]:
                if pool.get(key) != value:
                    pool[key] = value
                    self._is_chia_config_updated = True

        return self

    def get_result(self) -> ConfigPatcherResult:
        return ConfigPatcherResult(
            foxy_farmer_config_was_updated=self._is_foxy_farmer_config_updated,
            chia_config_was_updated=self._is_chia_config_updated
        )
