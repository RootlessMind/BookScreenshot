# BookScreenshot

**A customizable screenshot automation tool for capturing pages, organizing batches, and generating PDFs.**

BookScreenshot is a Windows-focused screenshot automation application designed for capturing books, documents, web pages, and other on-screen content.

The goal is to provide a flexible and reliable tool that gives users control over how screenshots are captured, organized, processed, and converted into PDFs.

Unlike applications with rigid workflows and limited configuration, BookScreenshot is being designed around customization, modularity, and user control.

## ✨ Features

The application is being developed with the following features in mind:

- **Book Capture:** Automatically capture pages with configurable page counts, delays, and pause intervals.
- **General Screenshot:** Capture full screens, individual monitors, selected regions, windows, and client areas.
- **Batch Management:** Organize screenshots into sequential batches with configurable naming and storage options.
- **Pause & Resume:** Pause, resume, cancel, or retry capture operations.
- **Session Recovery:** Automatically save progress and allow unfinished jobs to be resumed, even after closing the application.
- **PDF Generation:** Generate individual PDFs for each batch and a combined PDF containing all captured pages.
- **Image Configuration:** Configure screenshot formats, image quality, cropping, and excluded areas.
- **Custom Shortcuts:** Customize keyboard shortcuts to suit your workflow.
- **Flexible Configuration:** Save settings and configurations as reusable JSON profiles.

## 🖥️ Operating Modes

BookScreenshot is planned to offer two operating modes:

**Simple Mode**

A straightforward interface for users who want to start capturing without dealing with extensive configuration.

**Advanced Mode**

Provides access to detailed settings, capture behavior, shortcut customization, image options, batch management, and other advanced features.

## 📦 Optional Modules

BookScreenshot is designed with a modular architecture. Additional functionality will be available through separately downloadable modules.

Planned optional modules include:

| Module | Purpose |
|---|---|
| OCR | Extract searchable text from captured pages. |
| Image Processing | Additional image enhancement and processing tools. |
| Remote Monitoring | Monitor and manage capture sessions remotely. |

The core application will remain independent of these optional modules, allowing users to install only the functionality they need.

## 🚀 Getting Started

### Requirements

- Windows 10 or Windows 11
- Python 3.13 (for development)
- Required Python dependencies

### Running from Source

Clone the repository:

```bash
git clone https://github.com/RootlessMind/BookScreenshot.git
cd BookScreenshot
```

Create a virtual environment:

```bash
py -3.13 -m venv .venv
```

Activate it:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

*Note: The entry point and dependency list may change during development.*

## 🔨 Building

BookScreenshot is intended to be distributed as a portable, standalone Windows executable using PyInstaller.

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the executable:

```bash
pyinstaller --onefile --console --name BookScreenshot main.py
```

The resulting executable will be available in the `dist` directory.

Optional modules will be distributed separately, allowing users to extend the application without requiring a completely different build.

## 📚 Capture Workflow

The planned book-capture workflow will allow users to:

1. Configure the number of pages to capture.
2. Set capture delays and automatic pause intervals.
3. Configure cropping, image format, and quality.
4. Start, pause, resume, or cancel a capture session.
5. Automatically save progress throughout the operation.
6. Continue an existing session or save it for later.
7. Generate separate PDFs for individual batches.
8. Generate one combined PDF containing all captured pages.

After completing a capture job, users will be able to continue with the existing configuration, modify settings, save the session and exit, or return to the main menu.

## 🗺️ Roadmap

BookScreenshot is an evolving project. The following features are planned:

- [ ] Core screenshot capture engine
- [ ] Book capture automation
- [ ] General screenshot functionality
- [ ] Simple and Advanced modes
- [ ] Configurable keyboard shortcuts
- [ ] Batch management and sequential naming
- [ ] Pause, resume, cancel, and retry functionality
- [ ] Persistent sessions and resume-later support
- [ ] PDF generation (separate batches and combined PDF)
- [ ] JSON configuration and reusable profiles
- [ ] Optional OCR module
- [ ] Optional image-processing module
- [ ] Optional remote-monitoring module
- [ ] Portable Windows executable
- [ ] Documentation and user guides

## 🤝 Contributing

Contributions, suggestions, bug reports, and feature requests are welcome.

If you have an idea that could improve BookScreenshot, feel free to open an issue or submit a pull request.

The project aims to remain modular, customizable, and extensible.

## 📄 License

BookScreenshot is distributed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

**BookScreenshot — Capture your pages. Organize your work. Stay in control.**
