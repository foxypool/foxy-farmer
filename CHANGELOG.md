# Changelog

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

- Initial release
