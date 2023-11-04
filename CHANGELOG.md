# Changelog

## [Unreleased]

## [1.12.0] - 2023-11-05

### Added

- Add plot refresh batch options `plot_refresh_batch_size` and `plot_refresh_batch_sleep_ms`.
- Add port override config options and `--root-path` command line argument to allow running multiple Foxy-Farmer instances.

### Fixed

- Fix crash on startup when using the binary and no `farmer_reward_address` and/or `pool_payout_address` are set.

## [1.11.0] - 2023-11-03

### Added

- Add sentry error reporting.
- Add `plot_nfts` config option to easily deploy new Foxy-Farmers for already joined PlotNFTs.

## [1.10.2] - 2023-10-31

### Fixed

- Prevent deadlock when joining many PlotNFTs to the pool.

## [1.10.1] - 2023-10-30

### Changed

- Package ubuntu binaries using ubuntu 20.04 to support older systems.

### Fixed

- Prevent crash by exiting early on missing `farmer_reward_address` and/or `pool_payout_address`.
- The Foxy-Farmer version is now shown on the pool in the Harvesters tab again.

## [1.10.0] - 2023-10-26

### Added

- Add additional wallet sync info while running `./foxy-farmer join-pool`.
- Support configuring BladeBit compression config options in `foxy-farmer.yaml`.
- Add `auth` command to generate PlotNFT login links.

## [1.9.1] - 2023-10-17

### Fixed

- Fix detection of another instance already running in `join-pool` command.
- Fix farmer not exiting properly on ctrl-c.
- Fix `join-pool` command not working properly when another chia wallet is running.

## [1.9.0] - 2023-10-13

### Added

- Add support for automatic PlotNFT pool joining via `./foxy-farmer join-pool`.
- Support adding your first key via a `CHIA_MNEMONIC` environment variable to simplify docker setups.

## [1.8.0] - 2023-10-06

### Added

- Bump chia to 2.1.0+og-1.4.0.

## [1.7.0] - 2023-09-06

### Added

- Bump chia to 2.0.0+og-1.4.0.
- Log the harvester node id on startup to more easily identify it in the pools harvesters tab when it is unnamed.

## [1.6.1] - 2023-08-02

### Fixed

- Installing foxy-farmer via pip is now working again.
- Fix a crash when starting foxy-farmer for the first time and no pool reward address is present.

## [1.6.0] - 2023-06-28

### Added

- Bump chia to 1.8.2+og-1.4.0.
- The chia cmds `keys`, `passphrase` and `plots` are now available for convenience.

### Fixed

- Starting foxy-farmer on a system which never ran chia before works correctly now.

## [1.5.1] - 2023-06-12

### Fixed

- When using an encrypted keyring foxy-farmer will now correctly ask for its passphrase on startup.

## [1.5.0] - 2023-05-17

### Added

- Bump chia to 1.8.1+og-1.4.0.

## [1.4.0] - 2023-05-04

### Added

- Bump chia to 1.8.0+og-1.4.0.

## [1.3.0] - 2023-04-13

### Added

- Add support for showing the farm summary using the `summary` command, eg. `./foxy-farmer summary`.
- Include foxy-farmer version in partial submits in the user-agent header.
- Bump chia to 1.7.1+og-1.3.0 to support `harvester_id` in OG partial submits.

## [1.2.0] - 2023-03-23

### Added

- Log to stdout/console and the `debug.log` file located in `.foxy-farmer/mainnet/log`

### Fixed

- Fixed foxy-farmer being unable to reconnect to the Chia Farming Gateway when the network connection was interrupted for extended periods

### Changed

- Upgraded python to 3.11 for release builds

## [1.1.0] - 2023-03-22

### Added

- Added support for configurable config paths using the `-c` or `--config` argument when starting foxy-farmer

### Changed

- Upgraded chia to 1.7.1
- Upgraded python to 3.11 in docker

## [1.0.0] - 2023-02-25

### Added

- Initial release

[unreleased]: https://github.com/foxypool/foxy-farmer/compare/1.12.0...HEAD
[1.12.0]: https://github.com/foxypool/foxy-farmer/compare/1.11.0...1.12.0
[1.11.0]: https://github.com/foxypool/foxy-farmer/compare/1.10.2...1.11.0
[1.10.2]: https://github.com/foxypool/foxy-farmer/compare/1.10.1...1.10.2
[1.10.1]: https://github.com/foxypool/foxy-farmer/compare/1.10.0...1.10.1
[1.10.0]: https://github.com/foxypool/foxy-farmer/compare/1.9.1...1.10.0
[1.9.1]: https://github.com/foxypool/foxy-farmer/compare/1.9.0...1.9.1
[1.9.0]: https://github.com/foxypool/foxy-farmer/compare/1.8.0...1.9.0
[1.8.0]: https://github.com/foxypool/foxy-farmer/compare/1.7.0...1.8.0
[1.7.0]: https://github.com/foxypool/foxy-farmer/compare/1.6.1...1.7.0
[1.6.1]: https://github.com/foxypool/foxy-farmer/compare/1.6.0...1.6.1
[1.6.0]: https://github.com/foxypool/foxy-farmer/compare/1.5.1...1.6.0
[1.5.1]: https://github.com/foxypool/foxy-farmer/compare/1.5.0...1.5.1
[1.5.0]: https://github.com/foxypool/foxy-farmer/compare/1.4.0...1.5.0
[1.4.0]: https://github.com/foxypool/foxy-farmer/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/foxypool/foxy-farmer/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/foxypool/foxy-farmer/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/foxypool/foxy-farmer/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/foxypool/foxy-farmer/releases/tag/1.0.0
