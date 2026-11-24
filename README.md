# BookScreenshot

**A customizable screenshot automation tool for capturing pages, organizing batches, and generating PDFs.**

BookScreenshot is a Windows-focused screenshot automation application designed primarily for capturing books, documents, web pages, and other on-screen content.

The project aims to provide a flexible and reliable tool that gives users control over how screenshots are captured, organized, processed, and converted into PDFs.

BookScreenshot is currently in **Alpha development**. The existing capture workflow is functional, while its architecture and additional features are being developed incrementally.

## ✨ Current Features

The current version includes:

- **Book Capture:** An existing automated page-capture workflow.
- **Automated Screenshots:** Capture pages using configurable capture settings.
- **PDF Generation:** Convert captured screenshots into PDF documents.
- **Configuration Management:** A foundation for loading and saving application settings.
- **Logging:** Application logging for troubleshooting and diagnosing errors.
- **Modular Architecture:** A package structure designed to support future functionality.

Some features are still handled by the original capture workflow and have not yet been integrated into a new interface.

## 🗺️ Planned Features

The following functionality is planned for future releases:

- **General Screenshot:** Capture full screens, individual monitors, selected regions, windows, and client areas.
- **Batch Management:** Organize screenshots into sequential batches with configurable naming and storage options.
- **Pause & Resume:** Pause, resume, cancel, or retry capture operations.
- **Session Recovery:** Save unfinished jobs and resume them after restarting the application.
- **PDF Organization:** Generate individual PDFs for each batch and one combined PDF.
- **Image Configuration:** Configure screenshot formats, image quality, cropping, and excluded areas.
- **Custom Shortcuts:** Customize keyboard shortcuts.
- **Reusable Profiles:** Save settings and configurations as JSON profiles.
- **Simple and Advanced Modes:** Provide both an accessible interface and detailed configuration options.

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

### Running from Source

Clone the repository:

```powershell
git clone https://github.com/RootlessMind/BookScreenshot.git
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

A standalone Windows executable is planned for distribution using PyInstaller.

Build instructions will be added once the packaging configuration has been tested and finalized.

## 📚 Capture Workflow

The current release retains the existing capture workflow.

Future versions aim to provide a more flexible workflow that will allow users to:

1. Configure the number of pages to capture.
2. Set capture delays and automatic pause intervals.
3. Configure cropping, image format, and quality.
4. Start, pause, resume, or cancel a capture session.
5. Automatically save progress throughout an operation.
6. Continue an existing session or save it for later.
7. Generate separate PDFs for individual batches.
8. Generate one combined PDF containing all captured pages.

Additional workflow improvements will include the ability to reuse an existing configuration, modify job settings, save sessions, and return to the main menu.

## 🛣️ Roadmap

BookScreenshot is an evolving project. The roadmap below outlines the planned development direction.

- [x] Initial modular application structure
- [x] Existing book-capture workflow integration
- [x] Configuration management foundation
- [x] Centralized application paths
- [x] Application logging
- [x] Initial configuration manager tests
- [ ] New capture interface
- [ ] General screenshot functionality
- [ ] Simple and Advanced modes
- [ ] Configurable keyboard shortcuts
- [ ] Batch management and sequential naming
- [ ] Pause, resume, cancel, and retry functionality
- [ ] Persistent sessions and resume-later support
- [ ] Enhanced PDF generation and organization
- [ ] JSON configuration and reusable profiles
- [ ] Optional OCR module
- [ ] Optional image-processing module
- [ ] Optional remote-monitoring module
- [ ] Portable Windows executable
- [ ] Documentation and user guides

## 🤝 Contributing

Contributions, suggestions, bug reports, and feature requests are welcome.

If you have an idea that could improve BookScreenshot, feel free to open an issue or submit a pull request.

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📄 License

BookScreenshot is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**BookScreenshot — Capture your pages. Organize your work. Stay in control.**
