import ctypes
import msvcrt
import os
import re
import time
from datetime import datetime

from .config_manager import ConfigManager
from .logging_manager import configure_logging
from .paths import ensure_app_directories, get_app_paths

# ============================================================
# WINDOWS DPI AWARENESS
# Must be set before importing PyAutoGUI.
# ============================================================


def enable_dpi_awareness():
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(
            ctypes.c_void_p(-4)  # PER_MONITOR_AWARE_V2
        )
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


enable_dpi_awareness()

import img2pdf  # noqa: E402
import pyautogui  # noqa: E402
from pynput import keyboard, mouse  # noqa: E402

# ============================================================
# GENERAL SETTINGS
# ============================================================

DEFAULT_DELAY_MS = 300
JPEG_QUALITY_DEFAULT = 95
INITIAL_DELAY_SECONDS = 2.0
CUSTOM_PRESETS_FILE = "custom_presets.json"

# Keep PyAutoGUI's corner-triggered emergency stop enabled.
# Moving the cursor to a screen corner raises FailSafeException,
# which is handled as a normal user-requested cancellation below.
# Escape remains available as a second cancellation method.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


# ============================================================
# PATHS / CONFIGURATION / LOGGING
# ============================================================


APP_PATHS = get_app_paths()
ensure_app_directories(APP_PATHS)
CONFIG = ConfigManager(APP_PATHS)
LOGGER = configure_logging(APP_PATHS)
APP_SETTINGS = CONFIG.load_settings()
DEFAULT_DELAY_MS = int(APP_SETTINGS.get("default_delay_ms", DEFAULT_DELAY_MS))
JPEG_QUALITY_DEFAULT = int(APP_SETTINGS.get("jpeg_quality", JPEG_QUALITY_DEFAULT))
BASE_DIR = str(APP_PATHS.base)
CAPTURES_DIR = str(APP_PATHS.captures)


# ============================================================
# WINDOWS HELPERS
# ============================================================


def get_screen_info():
    width, height = pyautogui.size()

    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        scaling = round(dpi / 96 * 100)
    except Exception:
        scaling = 100

    return width, height, scaling


def get_console_window():
    try:
        return ctypes.windll.kernel32.GetConsoleWindow()
    except Exception:
        return None


def bring_console_to_front():
    hwnd = get_console_window()
    if hwnd:
        try:
            SW_RESTORE = 9
            ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
            ctypes.windll.user32.BringWindowToTop(hwnd)
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        except Exception:
            pass


def bring_reader_to_front(activation_point):
    """Foreground the reader without changing its maximized/restored state."""
    x, y = activation_point

    try:

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

        point = POINT(int(x), int(y))
        user32 = ctypes.windll.user32

        hwnd = user32.WindowFromPoint(point)

        if hwnd:
            root = user32.GetAncestor(hwnd, 2)  # GA_ROOT
            if root:
                hwnd = root

            # Do not call ShowWindow(SW_RESTORE): it can unmaximize a reader.
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
            time.sleep(0.15)

        # Click the configured activation point to activate the reader.
        safe_click(x, y)
        return True

    except Exception as exc:
        LOGGER.exception("Could not foreground reader automatically: %s", exc)
        print(f"Could not foreground reader automatically: {exc}")
        return False


# ============================================================
# COORDINATE HELPERS
# ============================================================


def scale_point(point, factor):
    return (round(point[0] * factor), round(point[1] * factor))


def scale_rectangle(rectangle, factor):
    return tuple(round(value * factor) for value in rectangle)


def full_page_crop(width, height, base_width, base_height):
    """Scale the 23px top and 50px bottom margins from the base profile."""
    factor = width / base_width
    return (0, round(23 * factor), width, height - round(50 * factor))


# ============================================================
# PRESET FACTORIES
# ============================================================


def fidibo_landscape(width, height, label):
    factor = width / 1920

    return [
        {
            "name": f"Fidibo {label}",
            "reader": "Fidibo",
            "turn": scale_point((60, 500), factor),
            "activate": scale_point((1000, 120), factor),
            "crop": scale_rectangle((670, 80, 1250, 930), factor),
            "delay_ms": DEFAULT_DELAY_MS,
        },
        {
            "name": f"Fidibo Text {label}",
            "reader": "Fidibo",
            "turn": scale_point((10, 1024), factor),
            "activate": scale_point((1000, 10), factor),
            "crop": full_page_crop(width, height, 1920, 1080),
            "delay_ms": DEFAULT_DELAY_MS,
        },
    ]


def fidibo_portrait(width, height, label):
    factor = width / 1080

    return {
        "name": f"Fidibo Portrait {label}",
        "reader": "Fidibo",
        "turn": scale_point((60, 920), factor),
        "activate": scale_point((500, 120), factor),
        "crop": full_page_crop(width, height, 1080, 1920),
        "delay_ms": DEFAULT_DELAY_MS,
    }


def taaghche_landscape(width, height, label):
    factor = width / 1920

    return {
        "name": f"Taaghche {label}",
        "reader": "Taaghche",
        "turn": scale_point((920, 24), factor),
        "activate": scale_point((1000, 120), factor),
        "crop": scale_rectangle((675, 60, 1395, 1075), factor),
        "delay_ms": DEFAULT_DELAY_MS,
    }


def taaghche_text_landscape(width, height, label):
    factor = width / 1920

    return {
        "name": f"Taaghche Text {label}",
        "reader": "Taaghche",
        "turn": scale_point((21, 535), factor),
        "activate": scale_point((949, 86), factor),
        "crop": scale_rectangle((1, 30, 1918, 1075), factor),
        "delay_ms": DEFAULT_DELAY_MS,
    }


def taaghche_portrait(width, height, label):
    factor = width / 1080

    # 90-degree clockwise rotation of Taaghche landscape click points:
    # (x, y) -> (1080-y, x)
    return {
        "name": f"Taaghche Portrait {label}",
        "reader": "Taaghche",
        "turn": scale_point((1056, 920), factor),
        "activate": scale_point((960, 1000), factor),
        "crop": scale_rectangle((10, 90, 1080, 1615), factor),
        "delay_ms": DEFAULT_DELAY_MS,
    }


def build_presets():
    presets = {}

    landscape_sizes = [
        (1920, 1080, "1080p"),
        (2560, 1440, "2K"),
        (3840, 2160, "4K"),
    ]

    portrait_sizes = [
        (1080, 1920, "1080p"),
        (1440, 2560, "2K"),
        (2160, 3840, "4K"),
    ]

    for width, height, label in landscape_sizes:
        presets[(width, height)] = fidibo_landscape(width, height, label) + [
            taaghche_landscape(width, height, label),
            taaghche_text_landscape(width, height, label),
        ]

    for width, height, label in portrait_sizes:
        presets[(width, height)] = [
            fidibo_portrait(width, height, label),
            taaghche_portrait(width, height, label),
        ]

    return presets


PRESETS = build_presets()


# ============================================================
# CUSTOM PRESET STORAGE
# ============================================================


def load_custom_presets():
    """Load user profiles from the centralized, versioned config store."""
    try:
        return CONFIG.load_custom_profiles()
    except Exception as exc:
        LOGGER.exception("Could not read custom profiles: %s", exc)
        print(f"Could not read custom profiles: {exc}")
        return []


def save_custom_presets(presets):
    """Save user profiles atomically through ConfigManager."""
    CONFIG.save_custom_profiles(presets)


def clean_name(name):
    name = re.sub(r'[<>:"/\\|?*]', "_", name.strip())
    return name.strip(" .") or "Capture"


# ============================================================
# INPUT HELPERS
# ============================================================


def ask_int(prompt, minimum=0, default=None):
    while True:
        raw = input(prompt).strip()

        if raw == "" and default is not None:
            return default

        try:
            value = int(raw)
            if value < minimum:
                print(f"Enter a value of at least {minimum}.")
                continue
            return value
        except ValueError:
            print("Please enter a whole number.")


def ask_yes_no(prompt, default=True):
    suffix = "[Y/n]" if default else "[y/N]"

    while True:
        answer = input(f"{prompt} {suffix}: ").strip().lower()

        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False

        print("Please answer Y or N.")


def ask_point(prompt):
    while True:
        raw = input(prompt).strip()

        try:
            x_text, y_text = raw.replace(" ", "").split(",")
            return int(x_text), int(y_text)
        except Exception:
            print("Enter coordinates as X,Y (for example: 100,200).")


def ask_delay_ms(default=DEFAULT_DELAY_MS):
    while True:
        value = input(f"Page-turn delay in milliseconds [{default}]: ").strip()

        if not value:
            return default

        try:
            delay = int(value)
            if delay < 0:
                print("Delay cannot be negative.")
                continue
            return delay
        except ValueError:
            print("Enter milliseconds as a whole number, e.g. 300.")


# ============================================================
# CALIBRATION
# ============================================================


def capture_mouse_click(instruction):
    """Wait for a left click, then bring the console back to the foreground."""
    result = {}

    bring_console_to_front()
    print("\n" + instruction)
    print("Click once with the LEFT mouse button.")

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            result["point"] = (round(x), round(y))
            return False

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    try:
        while listener.is_alive() and "point" not in result:
            time.sleep(0.05)
    finally:
        listener.stop()
        listener.join(timeout=1)

    bring_console_to_front()
    time.sleep(0.2)

    point = result["point"]
    print(f"Recorded: {point[0]}, {point[1]}")
    return point


def calibrate_profile(name, reader, width, height, delay_ms):
    print("\nCUSTOM COORDINATE CALIBRATION")
    print("----------------------------------------")
    print("The console will return to the foreground after each click.")

    print("\nChoose calibration method:")
    print("1. Click the requested locations")
    print("2. Type coordinates manually")

    method = input("Select [1/2] (default 1): ").strip() or "1"

    if method == "2":
        turn = ask_point("Page-turn button X,Y: ")
        activate = ask_point("Window activation point X,Y: ")
        top_left = ask_point("Crop top-left X,Y: ")
        bottom_right = ask_point("Crop bottom-right X,Y: ")
    else:
        top_left = capture_mouse_click("1/4: Click the TOP-LEFT corner of the crop area.")
        bottom_right = capture_mouse_click("2/4: Click the BOTTOM-RIGHT corner of the crop area.")
        activate = capture_mouse_click(
            "3/4: Click inside the reader window where it can be activated."
        )
        turn = capture_mouse_click("4/4: Click the next-page button.")

    left, top = top_left
    right, bottom = bottom_right

    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        raise ValueError("Invalid crop rectangle. Check top-left and bottom-right points.")

    for label, point in (("Page-turn", turn), ("Activation", activate)):
        if not (0 <= point[0] < width and 0 <= point[1] < height):
            raise ValueError(f"{label} point is outside the screen.")

    return {
        "name": name,
        "reader": reader,
        "turn": list(turn),
        "activate": list(activate),
        "crop": [left, top, right, bottom],
        "delay_ms": delay_ms,
        "custom": True,
    }


def validate_profile(profile, width, height):
    try:
        turn = tuple(profile["turn"])
        activate = tuple(profile["activate"])
        crop = tuple(profile["crop"])

        if len(turn) != 2 or len(activate) != 2 or len(crop) != 4:
            return False

        left, top, right, bottom = crop

        return (
            0 <= turn[0] < width
            and 0 <= turn[1] < height
            and 0 <= activate[0] < width
            and 0 <= activate[1] < height
            and 0 <= left < right <= width
            and 0 <= top < bottom <= height
        )
    except Exception:
        return False


def show_profile(profile):
    print("\nSelected configuration:")
    print(f"Name: {profile['name']}")
    print(f"Page-turn coordinates: {tuple(profile['turn'])}")
    print(f"Activation coordinates: {tuple(profile['activate'])}")
    print(f"Crop area: {tuple(profile['crop'])}")
    print(f"Default delay: {profile.get('delay_ms', DEFAULT_DELAY_MS)} ms")


# ============================================================
# PRESET SELECTION / RE-CALIBRATION
# ============================================================


def choose_profile(width, height):
    custom_presets = load_custom_presets()
    built_in = PRESETS.get((width, height), [])

    while True:
        print("\n" + "=" * 54)
        print("READER CONFIGURATIONS")
        print("=" * 54)
        print(f"Detected display: {width} x {height}")
        print("\nBuilt-in presets:")

        options = []

        for preset in built_in:
            options.append(("builtin", preset))
            print(f"{len(options)}. {preset['name']}")

        print("\nSaved custom presets:")

        for index, preset in enumerate(custom_presets):
            options.append(("custom", preset))
            print(f"{len(options)}. {preset['name']}")

        create_number = len(options) + 1
        print(f"\n{create_number}. Create a new custom configuration")
        print("0. Exit")

        choice = ask_int("\nChoose an option: ", 0, None)

        if choice == 0:
            return None

        if choice == create_number:
            name = input("Name this custom configuration: ").strip()
            if not name:
                name = "Custom Reader"

            reader = input("Reader/application name [Custom]: ").strip() or "Custom"
            delay = ask_delay_ms(DEFAULT_DELAY_MS)

            try:
                profile = calibrate_profile(name, reader, width, height, delay)
            except Exception as exc:
                print(f"\nCalibration failed: {exc}")
                input("Press Enter to return to the menu...")
                continue

            custom_presets.append(profile)
            save_custom_presets(custom_presets)
            print("Custom configuration saved.")
            return profile

        if 1 <= choice <= len(options):
            kind, selected = options[choice - 1]
            profile = dict(selected)

            # Coordinates in built-in profiles are already physical pixels.
            show_profile(profile)

            if ask_yes_no("Are these coordinates correct?", default=True):
                if not validate_profile(profile, width, height):
                    print("These coordinates do not fit the detected screen.")
                    continue
                return profile

            name = profile["name"]
            reader = profile.get("reader", "Custom")
            delay = int(profile.get("delay_ms", DEFAULT_DELAY_MS))

            try:
                updated = calibrate_profile(name, reader, width, height, delay)
            except Exception as exc:
                print(f"\nCalibration failed: {exc}")
                input("Press Enter to return to the menu...")
                continue

            if kind == "custom":
                original_name = selected.get("name")
                for index, item in enumerate(custom_presets):
                    if item.get("name") == original_name:
                        custom_presets[index] = updated
                        break
                else:
                    custom_presets.append(updated)
            else:
                # Recalibrated built-in profiles are saved as custom profiles
                # so the built-in preset remains unchanged.
                updated["name"] = name + " (customized)"
                custom_presets.append(updated)

            save_custom_presets(custom_presets)
            print("Updated coordinates saved.")
            return updated

        print("Invalid selection.")


# ============================================================
# IMAGE OUTPUT SETTINGS
# ============================================================


def choose_image_format():
    print("\nIMAGE FORMAT")
    print("1. PNG - lossless, larger files")
    print("2. JPEG - compressed, smaller files")

    configured_format = str(APP_SETTINGS.get("default_image_format", "JPEG")).upper()
    default_choice = "1" if configured_format == "PNG" else "2"
    choice = input(f"Choose format [1/2] (default {default_choice}): ").strip() or default_choice

    if choice == "1":
        return "PNG", None

    if choice != "2":
        print("Invalid choice. Using JPEG.")
        return "JPEG", 95

    print("\nJPEG quality:")
    print("1. 100 - maximum quality")
    print("2. 95  - very high quality")
    print("3. 90  - high quality")
    print("4. 85  - balanced")
    print("5. 80  - smaller files")

    qualities = {"1": 100, "2": 95, "3": 90, "4": 85, "5": 80}
    default_quality_choice = min(
        qualities, key=lambda key: abs(qualities[key] - JPEG_QUALITY_DEFAULT)
    )
    quality_choice = (
        input(f"Choose quality [1-5] (default {default_quality_choice}): ").strip()
        or default_quality_choice
    )

    if quality_choice not in qualities:
        print(f"Invalid choice. Using JPEG {JPEG_QUALITY_DEFAULT}.")
        quality_choice = default_quality_choice

    return "JPEG", qualities[quality_choice]


# ============================================================
# UNIQUE NAMES / CAPTURE FOLDERS
# ============================================================


def unique_directory(parent, base_name):
    candidate = os.path.join(parent, base_name)
    number = 2

    while os.path.exists(candidate):
        candidate = os.path.join(parent, f"{base_name}_{number:03d}")
        number += 1

    os.makedirs(candidate)
    return candidate


def unique_file_path(folder, filename):
    stem, extension = os.path.splitext(filename)
    candidate = os.path.join(folder, filename)
    number = 2

    while os.path.exists(candidate):
        candidate = os.path.join(folder, f"{stem}_{number:03d}{extension}")
        number += 1

    return candidate


# ============================================================
# MOUSE CLICK
# ============================================================


def safe_click(x, y):
    """
    Click at a screen point and restore the cursor to where it was.
    Keep the user's hands off the mouse during active capture for
    the most reliable timing; the cursor cannot be made stationary
    while using ordinary coordinate-based mouse clicks.
    """
    original = pyautogui.position()

    try:
        pyautogui.click(x, y)
    except pyautogui.FailSafeException:
        # Do not attempt to restore the cursor: it is deliberately
        # positioned in a corner to trigger the emergency stop.
        raise
    else:
        pyautogui.moveTo(original.x, original.y, duration=0)


# ============================================================
# PDF CREATION
# ============================================================


def create_pdf(image_paths, pdf_path):
    LOGGER.info("PDF generation requested: %s (%d images)", pdf_path, len(image_paths))
    if not image_paths:
        print("There are no screenshots to put into a PDF.")
        return False

    try:
        with open(pdf_path, "wb") as output:
            output.write(img2pdf.convert(image_paths))

        LOGGER.info("PDF created: %s", pdf_path)
        print(f"\nPDF created: {pdf_path}")
        return True

    except Exception as exc:
        LOGGER.exception("PDF creation failed: %s", exc)
        print(f"\nPDF creation failed: {exc}")
        return False


# ============================================================
# CAPTURE SESSION
# ============================================================


def run_capture(profile, width, height):
    LOGGER.info(
        "Capture requested: profile=%s resolution=%sx%s", profile.get("name"), width, height
    )
    print("\nCAPTURE SETTINGS")
    show_profile(profile)

    total_pages = ask_int("\nHow many pages should be captured? ", 1)

    default_pause = int(APP_SETTINGS.get("default_pause_after", 0))
    pause_after = ask_int(
        f"Pause after how many screenshots? (0 = disabled) [{default_pause}]: ", 0, default_pause
    )

    delay_ms = ask_delay_ms(int(profile.get("delay_ms", DEFAULT_DELAY_MS)))

    image_format, jpeg_quality = choose_image_format()

    default_name = datetime.now().strftime("Capture_%Y%m%d_%H%M%S")
    session_name = input(f"\nName for this capture [{default_name}]: ").strip() or default_name
    session_name = clean_name(session_name)

    os.makedirs(CAPTURES_DIR, exist_ok=True)
    session_dir = unique_directory(CAPTURES_DIR, session_name)

    extension = ".png" if image_format == "PNG" else ".jpg"
    image_paths = []

    LOGGER.info(
        "Capture initialized: pages=%d delay_ms=%d format=%s output=%s",
        total_pages,
        delay_ms,
        image_format,
        session_dir,
    )
    print("\n" + "=" * 54)
    print("READY TO CAPTURE")
    print("=" * 54)
    print(f"Pages: {total_pages}")
    print(f"Pause after: {pause_after}")
    print(f"Delay: {delay_ms} ms")
    print(f"Format: {image_format}")
    if jpeg_quality is not None:
        print(f"JPEG quality: {jpeg_quality}")
    print(f"Output folder: {session_dir}")
    print("\nPress ESC at any time to cancel.")
    input("\nPosition the reader and press ENTER to start...")

    cancelled = False

    def on_key_press(key):
        nonlocal cancelled
        if key == keyboard.Key.esc:
            cancelled = True
            print("\nESC detected. Stopping after the current operation...")
            return False

    escape_listener = keyboard.Listener(on_press=on_key_press)
    escape_listener.start()

    try:
        print("\nBringing reader to the foreground...")
        bring_reader_to_front(tuple(profile["activate"]))
        time.sleep(INITIAL_DELAY_SECONDS)

        for page_number in range(1, total_pages + 1):
            if cancelled:
                break

            screenshot = None
            cropped = None

            try:
                screenshot = pyautogui.screenshot()
                left, top, right, bottom = profile["crop"]

                if right > screenshot.width or bottom > screenshot.height:
                    raise ValueError(
                        f"Crop rectangle {tuple(profile['crop'])} exceeds "
                        f"screen size {screenshot.size}."
                    )

                cropped = screenshot.crop((left, top, right, bottom))

                filename = os.path.join(session_dir, f"page_{page_number:04d}{extension}")

                if image_format == "PNG":
                    cropped.save(filename, "PNG", optimize=True)
                else:
                    cropped.convert("RGB").save(
                        filename, "JPEG", quality=jpeg_quality, optimize=True
                    )

                image_paths.append(filename)
                LOGGER.info("Captured page %d/%d: %s", page_number, total_pages, filename)
                print(f"Captured {page_number}/{total_pages}")

            except Exception as exc:
                LOGGER.exception("Capture failed on page %d: %s", page_number, exc)
                print(f"\nCapture error on page {page_number}: {exc}")
                break

            finally:
                if cropped is not None:
                    cropped.close()
                if screenshot is not None:
                    screenshot.close()

            if page_number < total_pages:
                if cancelled:
                    break

                safe_click(*profile["turn"])

                # Delay is interruptible by Escape.
                remaining = delay_ms / 1000.0
                while remaining > 0 and not cancelled:
                    step = min(0.05, remaining)
                    time.sleep(step)
                    remaining -= step

                if cancelled:
                    break

            if (
                pause_after > 0
                and page_number == pause_after
                and page_number < total_pages
                and not cancelled
            ):
                bring_console_to_front()
                print("\n" + "=" * 54)
                print(f"PAUSED after {page_number} screenshots.")
                print("You can now use the reader or other applications.")
                print("Press ENTER here to resume; press ESC to cancel.")
                print("=" * 54)

                # Poll the console instead of using input(), so Escape
                # can cancel even while the program is paused.
                while not cancelled:
                    if msvcrt.kbhit():
                        pressed = msvcrt.getwch()
                        if pressed in ("\r", "\n"):
                            break
                    time.sleep(0.05)

                if not cancelled:
                    print("Bringing reader back to the foreground...")
                    bring_reader_to_front(tuple(profile["activate"]))
                    time.sleep(0.5)

    except pyautogui.FailSafeException:
        cancelled = True
        LOGGER.warning("PyAutoGUI corner fail-safe triggered; capture cancelled by user")
        print("\nPyAutoGUI corner fail-safe triggered. Capture cancelled safely.")
    finally:
        escape_listener.stop()
        escape_listener.join(timeout=1)

    LOGGER.info(
        "Capture finished: %d/%d screenshots in %s", len(image_paths), total_pages, session_dir
    )
    print("\n" + "=" * 54)
    print("CAPTURE SESSION FINISHED")
    print(f"Screenshots captured: {len(image_paths)}")
    print(f"Session folder: {session_dir}")
    print("=" * 54)

    if not image_paths:
        print("No images were captured.")
        return

    if ask_yes_no(
        "\nCreate a PDF from these screenshots?",
        default=bool(APP_SETTINGS.get("create_pdf", True)),
    ):
        requested_pdf_name = input(f"PDF filename [{session_name}.pdf]: ").strip()

        if not requested_pdf_name:
            requested_pdf_name = session_name + ".pdf"

        requested_pdf_name = clean_name(os.path.splitext(requested_pdf_name)[0]) + ".pdf"

        pdf_path = unique_file_path(session_dir, requested_pdf_name)
        pdf_created = create_pdf(image_paths, pdf_path)

        if pdf_created:
            keep_images = ask_yes_no(
                "Keep the original screenshot files?",
                default=bool(APP_SETTINGS.get("keep_screenshots", True)),
            )

            if not keep_images:
                try:
                    for path in image_paths:
                        os.remove(path)

                    print("Screenshot images deleted; PDF retained.")
                except Exception as exc:
                    print(f"Could not delete all screenshots: {exc}")
        else:
            print("Screenshots have been retained because PDF creation failed.")

    else:
        print("PDF not created. Screenshots have been retained.")

    print(f"\nSession saved in: {session_dir}")


# ============================================================
# MAIN MENU
# ============================================================


def main():
    os.makedirs(CAPTURES_DIR, exist_ok=True)
    LOGGER.info("Legacy book-capture interface entered")

    while True:
        width, height, scaling = get_screen_info()

        print("\n" + "=" * 54)
        print("          BOOK SCREENSHOT CAPTURE")
        print("=" * 54)
        print(f"Detected resolution: {width} x {height}")
        print(f"Orientation: {'Portrait' if height > width else 'Landscape'}")
        print(f"Windows scaling: {scaling}%")
        print("\n1. Start a capture")
        print("2. Exit")

        choice = input("\nSelect [1/2]: ").strip()

        if choice == "2":
            print("Goodbye.")
            break

        if choice != "1":
            print("Invalid selection.")
            continue

        profile = choose_profile(width, height)

        if profile is None:
            continue

        if not validate_profile(profile, width, height):
            print("\nThe selected coordinates do not fit this display.")
            input("Press ENTER to return to the main menu...")
            continue

        try:
            run_capture(profile, width, height)
        except KeyboardInterrupt:
            print("\nOperation interrupted.")
        except Exception as exc:
            LOGGER.exception("Unexpected capture workflow error: %s", exc)
            print(f"\nUnexpected error: {exc}")

        input("\nPress ENTER to return to the main menu...")
