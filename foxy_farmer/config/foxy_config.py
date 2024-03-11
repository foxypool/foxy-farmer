from typing import TypedDict, NotRequired, List, Union


class PlotNft(TypedDict):
    launcher_id: str
    owner_public_key: str
    p2_singleton_puzzle_hash: str
    payout_instructions: str
    pool_url: str
    target_puzzle_hash: str


class FoxyConfig(TypedDict):
    # General
    backend: NotRequired[str]
    plot_directories: List[str]
    plot_refresh_interval_seconds: NotRequired[int]
    plot_refresh_batch_size: NotRequired[int]
    plot_refresh_batch_sleep_ms: NotRequired[int]
    recursive_plot_scan: NotRequired[bool]
    harvester_num_threads: int
    farmer_reward_address: str
    pool_payout_address: str
    log_level: str
    listen_host: str
    enable_harvester: NotRequired[bool]
    plot_nfts: NotRequired[List[PlotNft]]
    chia_daemon_port: NotRequired[int]
    chia_farmer_port: NotRequired[int]
    chia_farmer_rpc_port: NotRequired[int]
    chia_harvester_rpc_port: NotRequired[int]
    chia_wallet_rpc_port: NotRequired[int]
    syslog_port: NotRequired[int]
    # BB
    enable_og_pooling: NotRequired[bool]
    parallel_decompressor_count: NotRequired[int]
    decompressor_thread_count: NotRequired[int]
    use_gpu_harvesting: NotRequired[bool]
    gpu_index: NotRequired[int]
    enforce_gpu_index: NotRequired[bool]
    decompressor_timeout: NotRequired[int]
    disable_cpu_affinity: NotRequired[bool]
    max_compression_level_allowed: NotRequired[int]
    # GH
    recompute_hosts: NotRequired[Union[List[str], str]]
    recompute_connect_timeout: NotRequired[int]
    recompute_retry_interval: NotRequired[int]
    chiapos_max_cores: NotRequired[int]
    chiapos_max_cuda_devices: NotRequired[int]
    chiapos_max_opencl_devices: NotRequired[int]
    chiapos_max_gpu_devices: NotRequired[int]
    chiapos_opencl_platform: NotRequired[int]
    chiapos_min_gpu_log_entries: NotRequired[int]
    cuda_visible_devices: NotRequired[str]
    # DR
    dr_plotter_client_token: NotRequired[str]
    dr_server_ip_address: NotRequired[str]
