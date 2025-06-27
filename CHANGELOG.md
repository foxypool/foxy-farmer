# Changelog

## [Unreleased]

### Changed

- Update `chia` to 2.5.4.
- Update `gigahorse` to 2.5.1.giga36.

## [1.24.0] - 2024-07-05

### Added

- Add monitoring for stale farmer connections.

### Changed

- Update `chia` to 2.4.1.
- Update `gigahorse` to 2.4.1.giga36.
- Update `drplotter` to 1.0.4.

### Fixed

- Fix auto-update replace logic when updating multiple times during the lifetime of the binary.

## [1.23.1] - 2024-05-19

### Changed

- Update `drplotter` to 1.0.3.

## [1.23.0] - 2024-05-17

### Added

- Add support for auto updates when using the binary, to enable set `auto_update: true` in the `foxy-farmer.yaml`.

### Changed

- Update `drplotter` to 1.0.2. This release requires you to set up your own DrServer and configure its ip/hostname and port via the `dr_server_ip_address` config option in your `foxy-farmer.yaml`, if you have been using the token system until now. Please see the [official release notes](https://github.com/drnick23/drplotter/releases/tag/1.0.2) for more info.

## [1.22.7] - 2024-05-04

### Changed

- Update `chia` to 2.3.0.
- Update `gigahorse` to 2.3.0.giga36.

## [1.22.6] - 2024-04-27

### Changed

- Update `drplotter` to 0.12.1.

### Fixed

- Fix `CHIA_MNEMONIC` not being applied when `.chia_keys` is present but empty.
- Fix an empty `foxy-farmer.yaml` not triggering the first run wizard.
- Fix the wallet sync not properly detecting PlotNFTs for dusted wallets.

## [1.22.5] - 2024-03-30

### Changed

- Update `chia` to 2.2.1.
- Update `drplotter` to 0.12.0.
- Update `gigahorse` to 2.2.1.giga35.

## [1.22.4] - 2024-03-26

### Changed

- Update `gigahorse` to 2.2.1.giga33.

## [1.22.3] - 2024-03-25

### Changed

- Update `gigahorse` to 2.1.4.giga32.

## [1.22.2] - 2024-03-24

### Fixed

- Fix crashing on exit when the chia daemon does not respond to the exit command.

## [1.22.1] - 2024-03-22

### Changed

- Update `drplotter` to 0.11.0. The `drplotter` upstream release fixes a critical bug, see its [release notes](https://github.com/drnick23/drplotter/releases/tag/0.11.0) for more info.

## [1.22.0] - 2024-03-20

### Added

- Add support for configuring a local DrServer to first run wizard.

### Changed

- Update `drplotter` to 0.10.0.

## [1.21.0] - 2024-03-10

### Added

- Add PlotNFT creation support to first run wizard.

### Changed

- Update `gigahorse` to 2.1.4.giga31.

## [1.20.0] - 2024-03-07

### Added

- Update `gigahorse` to 2.1.4.giga30, adding support for C30-C33 plots.

## [1.19.0] - 2024-03-03

### Added

- Add pool join question to first run wizard.
- Add PlotNFT sync question to first run wizard.

### Changed

- Update `drplotter` to 0.9.2.
- Update dependencies.
- Improve DrPlotter client token input validation in first run wizard.

### Fixed

- Fix login link generation crashing if pool is unavailable.
- Fix harvester id shown on startup missing the last 2 characters.
- Fix shutdown on windows when just closing the window.

## [1.18.0] - 2024-02-19

### Added

- Add interactive first run wizard to simplify the setup for first time users.

## [1.17.0] - 2024-02-16

### Added

- Add support for DrPlotter plots using backend `drplotter`. Set your solver client token in the `foxy-farmer.yaml` with key `dr_plotter_client_token`.

## [1.16.0] - 2024-02-02

### Added

- Add support for Gigahorse. You can switch between using Bladebit or Gigahorse using the config option `backend` with either `bladebit` or `gigahorse`. Foxy-GH-Farmer is now deprecated in favor of a unified codebase.

## [1.15.0] - 2024-01-25

### Added

- Migrate the pool url in existing configs.

### Changed

- Update the pool url to use when joining the pool.

## [1.14.0] - 2024-01-07

### Added

- Show connection infos in `summary` command.
- Add `--fee` option to `join-pool` command.

## [1.13.2] - 2023-12-19

### Changed

- Bump chia to 2.1.3+og-1.5.0.

## [1.13.1] - 2023-12-14

### Changed

- Bump chia to 2.1.2+og-1.5.0.

## [1.13.0] - 2023-11-12

### Added

- Add new `init` command to ensure configurations are available without running the farmer.
- Add support for `--version` argument to print the version and exit.

## [1.12.1] - 2023-11-05

### Changed

- Show a more helpful error message when the `foxy-farmer.yaml` is not formatted correctly and can not be parsed.

### Fixed

- Fix harvester not connecting to the farmer on new installs.

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

[unreleased]: https://github.com/foxypool/foxy-farmer/compare/1.24.0...HEAD
[1.24.0]: https://github.com/foxypool/foxy-farmer/compare/1.23.1...1.24.0
[1.23.1]: https://github.com/foxypool/foxy-farmer/compare/1.23.0...1.23.1
[1.23.0]: https://github.com/foxypool/foxy-farmer/compare/1.22.7...1.23.0
[1.22.7]: https://github.com/foxypool/foxy-farmer/compare/1.22.6...1.22.7
[1.22.6]: https://github.com/foxypool/foxy-farmer/compare/1.22.5...1.22.6
[1.22.5]: https://github.com/foxypool/foxy-farmer/compare/1.22.4...1.22.5
[1.22.4]: https://github.com/foxypool/foxy-farmer/compare/1.22.3...1.22.4
[1.22.3]: https://github.com/foxypool/foxy-farmer/compare/1.22.2...1.22.3
[1.22.2]: https://github.com/foxypool/foxy-farmer/compare/1.22.1...1.22.2
[1.22.1]: https://github.com/foxypool/foxy-farmer/compare/1.22.0...1.22.1
[1.22.0]: https://github.com/foxypool/foxy-farmer/compare/1.21.0...1.22.0
[1.21.0]: https://github.com/foxypool/foxy-farmer/compare/1.20.0...1.21.0
[1.20.0]: https://github.com/foxypool/foxy-farmer/compare/1.19.0...1.20.0
[1.19.0]: https://github.com/foxypool/foxy-farmer/compare/1.18.0...1.19.0
[1.18.0]: https://github.com/foxypool/foxy-farmer/compare/1.17.0...1.18.0
[1.17.0]: https://github.com/foxypool/foxy-farmer/compare/1.16.0...1.17.0
[1.16.0]: https://github.com/foxypool/foxy-farmer/compare/1.15.0...1.16.0
[1.15.0]: https://github.com/foxypool/foxy-farmer/compare/1.14.0...1.15.0
[1.14.0]: https://github.com/foxypool/foxy-farmer/compare/1.13.2...1.14.0
[1.13.2]: https://github.com/foxypool/foxy-farmer/compare/1.13.1...1.13.2
[1.13.1]: https://github.com/foxypool/foxy-farmer/compare/1.13.0...1.13.1
[1.13.0]: https://github.com/foxypool/foxy-farmer/compare/1.12.1...1.13.0
[1.12.1]: https://github.com/foxypool/foxy-farmer/compare/1.12.0...1.12.1
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
