import sentry_sdk
from sentry_sdk import Hub
from sentry_sdk.integrations.logging import LoggingIntegration

from foxy_farmer.foundation.sentry.filter_sentry_events import filter_sentry_events
from foxy_farmer.version import version


def init_sentry():
    sentry_sdk.init(
        dsn="https://313b953dcdac8bb1ed84bc12b99ba285@o236153.ingest.sentry.io/4506149603180544",
        release=f"foxy-farmer@{version}",
        integrations=[
            LoggingIntegration(event_level=None),
        ],
        before_send=filter_sentry_events,
    )


def close_sentry():
    client = Hub.current.client
    if client is not None:
        client.close(timeout=2.0)
