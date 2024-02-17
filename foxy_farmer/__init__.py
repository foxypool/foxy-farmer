from foxy_farmer.monkey_patch_chia_version import monkey_patch_chia_version
monkey_patch_chia_version()

from foxy_farmer.error_reporting import init_sentry, close_sentry
init_sentry()
