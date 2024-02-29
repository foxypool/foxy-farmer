from typing import Dict, Any, Optional, List

Event = Dict[str, Any]
Hint = Dict[str, Any]

ignored_error_messages: List[str] = [
    "Please initialize (or migrate) your config directory with chia init",
]


def filter_sentry_events(event: Event, hint: Hint) -> Optional[Event]:
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        error_message = exc_value.args[0]
        for ignored_error in ignored_error_messages:
            if ignored_error in error_message:
                return None
    return event
