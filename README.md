# BookScreenshot

Download the latest release from the [Releases page](https://github.com/RootlessMind/BookScreenshot/releases). The standalone Windows executable does not require a separate Python installation.

[![Version](https://img.shields.io/badge/version-0.1.1%20Alpha-blue)](https://github.com/RootlessMind/BookScreenshot/releases/tag/v0.1.1)

**A customizable screenshot automation tool for capturing pages, organizing batches, and generating PDFs.**

BookScreenshot is a Windows-focused screenshot automation application designed primarily for capturing books, documents, web pages, and other on-screen content.

The project aims to provide a flexible and reliable tool that gives users control over how screenshots are captured, organized, processed, and converted into PDFs.

BookScreenshot is currently in **Alpha development**. The existing capture workflow is functional, while its architecture and additional features are being developed incrementally.

## ✨ Current Features

The current version includes:

- **Book Capture:** An automated workflow for capturing pages.
- **Configurable Capture:** Configure capture settings before starting an operation.
- **Image Configuration:** Configure screenshot formats, image quality, cropping, and excluded areas.
- **Keyboard Navigation:** Use ESC to navigate backward through supported setup steps.
- **Focus Management:** Improved focus restoration between the reader application and the console.
- **Capture Pause Intervals:** Pause an operation after a user-defined number of screenshots and resume it.
- **PDF Generation:** Convert captured screenshots into PDF documents.
- **Screenshot Retention:** Choose whether to keep or delete captured screenshots after PDF generation or when PDF creation is declined.
- **Reusable Profiles:** Save and reuse settings through JSON configuration profiles.
- **Logging:** Application logging for troubleshooting and diagnosing errors.
- **Modular Architecture:** A package structure designed to support future functionality.

Some features are still handled by the original capture workflow and have not yet been integrated into a new interface.

## 🗺️ Planned Features

The following functionality is planned for future releases:

- **General Screenshot:** Capture full screens, individual monitors, selected regions, windows, and client areas.
- **Batch Management:** Organize screenshots into sequential batches with configurable naming and storage options.
- **Interrupted Capture Recovery:** Offer the option to resume or cancel an operation stopped using ESC or the corner fail-safe.
- **Session Recovery:** Save unfinished jobs and resume them after restarting the application.
- **PDF Organization:** Generate individual PDFs for each batch and one combined PDF.
- **Simple and Advanced Modes:** Provide both an accessible interface and detailed configuration options.
- **Custom Shortcuts:** Customize keyboard shortcuts.

## 🖥️ Operating Modes

Two operating modes are planned:

**Simple Mode**

A straightforward interface for users who want to start capturing without dealing with extensive configuration.

**Advanced Mode**

Provides access to detailed settings, capture behavior, shortcut customization, image options, batch management, and other advanced features.

Neither mode is currently implemented as a separate interface.

## 📦 Optional Modules

BookScreenshot is being designed with a modular architecture. Additional functionality may be distributed through separately installable modules.

Planned modules include:

| Module | Purpose |
|---|---|
| OCR | Extract searchable text from captured pages. |
| Image Processing | Additional image enhancement and processing tools. |
| Remote Monitoring | Monitor and manage capture sessions remotely. |

These modules are planned and are not currently available.

## 🚀 Getting Started

### Requirements

- Windows 10 or Windows 11
- Python 3.13 or newer
- Git (to clone the repository)

### Downloading the Application

The standalone Windows executable is available from the [GitHub Releases page](https://github.com/RootlessMind/BookScreenshot/releases).

No Python installation is required to run the standalone executable.

### Running from Source

Clone the repository:

```powershell
git clone https://github.com/RootlessMind/BookScreenshot.git
```
```powershell
cd BookScreenshot
```

Create a virtual environment:

```powershell
py -3.13 -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install the application and its development dependencies:

```powershell
py -m pip install -e ".[dev]"
```

Run BookScreenshot:

```powershell
py -m bookscreenshot
```

The editable installation is useful for development because changes to the source code are available without reinstalling the package.

## 🔨 Building

BookScreenshot uses PyInstaller to create a standalone Windows executable.

Install the development dependencies:

```powershell
py -m pip install -e ".[dev]"
```

Install PyInstaller:

```powershell
py -m pip install pyinstaller
```

Build the executable using the project's specification file:

```powershell
py -m PyInstaller --clean --noconfirm BookScreenshot.spec
```

The resulting executable will be available at:

```text
dist\BookScreenshot.exe
```

The specification file defines the executable name, application icon, console mode, entry point, and required hidden imports.

## 📚 Capture Workflow

The current capture workflow supports configurable page counts, capture delays, cropping, image formats, image quality, and excluded areas.

Users can configure an automatic pause after a specified number of screenshots and resume the operation.

A remaining issue is that operations stopped using ESC or the corner fail-safe cannot currently be resumed. Future versions will offer the choice to resume or cancel these interrupted operations.

Further workflow improvements are planned:

- Save unfinished operations and restore them after restarting the application.
- Improve batch management and PDF organization.
- Allow users to repeat operations while reusing or modifying previous settings.

## 🛣️ Roadmap

BookScreenshot is an evolving project. The roadmap below outlines the planned development direction.

- [x] Initial modular application structure
- [x] Existing book-capture workflow integration
- [x] Configuration management and JSON reusable profiles
- [x] Configurable image settings, including format, quality, cropping, and excluded areas
- [x] Centralized application paths
- [x] Application logging
- [x] Initial configuration manager tests
- [x] Improved capture setup navigation and focus restoration
- [x] Standalone Windows executable
- [x] Configurable capture pause intervals
- [ ] New capture interface
- [ ] General screenshot functionality
- [ ] Simple and Advanced modes
- [ ] Configurable keyboard shortcuts
- [ ] Batch management and sequential naming
- [ ] Resume or cancel operations stopped using ESC or the corner fail-safe
- [ ] Persistent sessions and resume-later support
- [ ] Enhanced PDF generation and organization
- [ ] Repeat operations with reusable or modifiable settings
- [ ] Optional OCR module
- [ ] Optional image-processing module
- [ ] Optional remote-monitoring module
- [ ] Expanded documentation and user guides

## 🤝 Contributing

Contributions, suggestions, bug reports, and feature requests are welcome.

If you have an idea that could improve BookScreenshot, feel free to open an issue or submit a pull request.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📄 License

BookScreenshot is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**BookScreenshot — Capture your pages. Organize your work. Stay in control.**
