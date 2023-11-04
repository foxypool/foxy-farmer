from typing import Dict, Any, List, Optional


def set_nested_dict_value(dic: Dict[str, Any], keys: List[str], value: Any):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def get_nested_dict_value(dic: Dict[str, Any], keys: List[str]) -> Optional[Any]:
    for key in keys[:-1]:
        dic = dic.get(key, {})

    return dic.get(keys[-1])
