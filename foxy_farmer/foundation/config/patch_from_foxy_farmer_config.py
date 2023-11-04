from typing import Optional, Dict, Any, List

from foxy_farmer.foundation.util.dictionary import get_nested_dict_value, set_nested_dict_value


def patch_from_foxy_farmer_config(
    foxy_farmer_config: Dict[str, Any],
    chia_config: Dict[str, Any],
    foxy_farmer_config_key: List[str],
    chia_config_key: Optional[List[str]] = None,
    config_was_updated: bool = False
) -> bool:
    if chia_config_key is None:
        chia_config_key = foxy_farmer_config_key

    foxy_farmer_config_value = get_nested_dict_value(foxy_farmer_config, foxy_farmer_config_key)
    chia_config_value = get_nested_dict_value(chia_config, chia_config_key)

    if foxy_farmer_config_value is not None and chia_config_value != foxy_farmer_config_value:
        set_nested_dict_value(chia_config, chia_config_key, foxy_farmer_config_value)
        config_was_updated = True

    return config_was_updated
