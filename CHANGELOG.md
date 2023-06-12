# Changelog

## [Unreleased]

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

- Initial release

[unreleased]: https://github.com/foxypool/foxy-farmer/compare/1.5.0...HEAD
[1.5.0]: https://github.com/foxypool/foxy-farmer/compare/1.4.0...1.5.0
[1.4.0]: https://github.com/foxypool/foxy-farmer/compare/1.3.0...1.4.0
[1.3.0]: https://github.com/foxypool/foxy-farmer/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/foxypool/foxy-farmer/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/foxypool/foxy-farmer/compare/1.0.0...1.1.0
[1.0.0]: https://github.com/foxypool/foxy-farmer/releases/tag/1.0.0
