# Ultimate2Mapper

Controller mapper for the 8BitDo Ultimate 2 Wireless.

## Run
Double-click `start.bat`.

## GitHub updates
The launcher checks:

https://raw.githubusercontent.com/tvrdprijatelj/Ultimate2Mapper/main/version.json

When a newer version is published, `release_url` in `version.json` can point to the release ZIP and the updater can install it.

## Project files
- `ultimate2_mapper.py` - main application
- `launcher.py` - update check + app launcher
- `update.py` - update installer
- `version.json` - current version/update manifest
- `start.bat` - normal Windows launcher

## GitHub Actions
The `.github/workflows/release.yml` workflow creates a release ZIP when a version tag such as `v1.0.1` is pushed.
