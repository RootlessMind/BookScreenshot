# Changelog

All notable changes to BookScreenshot will be documented here.

This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.1] - 2026-11-26

### Added
- Added the option to keep or delete captured screenshots when PDF generation is declined.

### Fixed
- Fixed ESC-based backward navigation throughout the supported capture setup workflow.
- Improved focus restoration between the reader application and the console.

## [0.1.0] - 2026-11-25

### Added
- Initial public Alpha release.
- Automated book-page screenshot capture.
- Configurable capture settings, including page count, capture delays, cropping, image format, image quality, and excluded areas.
- Configurable pause intervals during capture operations.
- Batch-based screenshot organization.
- PDF generation from captured screenshots.
- JSON configuration and reusable profiles.
- Application logging.
- Application icon.
- Standalone Windows executable.

### Changed
- Improved application startup and error handling.
- Improved logging initialization and error reporting.

### Notes
- This is an early Alpha release.
- Python 3.13 or newer is required for source installation.
- The standalone Windows executable does not require a separate Python installation.
- If disk space runs out during capture, partial captures may remain and PDF generation may fail.