import ctypes
import msvcrt
import os
import re
import time
from datetime import datetime

from .config_manager import ConfigManager
from .logging_manager import configure_logging
from .paths import get_app_paths

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
    """Restore and foreground the console, including after another app was clicked."""
    hwnd = get_console_window()
    if not hwnd:
        return False

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    attached_threads = []

    try:
        SW_RESTORE = 9
        user32.ShowWindow(hwnd, SW_RESTORE)

        current_thread = kernel32.GetCurrentThreadId()
        foreground_hwnd = user32.GetForegroundWindow()
        foreground_thread = (
            user32.GetWindowThreadProcessId(foreground_hwnd, None) if foreground_hwnd else 0
        )
        console_thread = user32.GetWindowThreadProcessId(hwnd, None)

        # Windows may reject SetForegroundWindow when the user just clicked
        # another application. Temporarily attach the input queues so the
        # console can be activated reliably, then detach them again.
        for thread_id in {foreground_thread, console_thread}:
            if thread_id and thread_id != current_thread:
                if user32.AttachThreadInput(current_thread, thread_id, True):
                    attached_threads.append(thread_id)

        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)
        user32.SetFocus(hwnd)
        time.sleep(0.1)
        return user32.GetForegroundWindow() == hwnd
    except Exception as exc:
        LOGGER.debug("Could not restore console focus: %s", exc)
        return False
    finally:
        current_thread = kernel32.GetCurrentThreadId()
        for thread_id in reversed(attached_threads):
            try:
                user32.AttachThreadInput(current_thread, thread_id, False)
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


def ask_int(prompt, minimum=0, default=None, allow_escape=False):
    while True:
        if allow_escape:
            raw = read_console_input(prompt)
            if raw is None:
                return None
            raw = raw.strip()
        else:
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


def read_console_input(prompt):
    """Read a console line while allowing ESC to cancel the current step."""
    print(prompt, end="", flush=True)
    characters = []

    while True:
        char = msvcrt.getwch()

        if char == "\x1b":
            print()
            return None
        if char in ("\r", "\n"):
            print()
            return "".join(characters)
        if char == "\x03":
            raise KeyboardInterrupt
        if char == "\b":
            if characters:
                characters.pop()
                print("\b \b", end="", flush=True)
            continue
        if char.isprintable():
            characters.append(char)
            print(char, end="", flush=True)


def ask_point(prompt):
    while True:
        raw = read_console_input(prompt)
        if raw is None:
            return None

        try:
            x_text, y_text = raw.replace(" ", "").split(",")
            return int(x_text), int(y_text)
        except Exception:
            print("Enter coordinates as X,Y (for example: 100,200).")


def ask_delay_ms(default=DEFAULT_DELAY_MS, allow_escape=False):
    while True:
        prompt = f"Page-turn delay in milliseconds [{default}]: "
        if allow_escape:
            raw = read_console_input(prompt)
            if raw is None:
                return None
            value = raw.strip()
        else:
            value = input(prompt).strip()

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
    """Wait for a left click, or return None when ESC is pressed."""
    result = {}

    bring_console_to_front()
    print("\n" + instruction)
    print("Click once with the LEFT mouse button. Press ESC to go back.")

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            result["point"] = (round(x), round(y))
            return False

    def on_key_press(key):
        if key == keyboard.Key.esc:
            result["cancelled"] = True
            return False

    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_key_press)
    mouse_listener.start()
    keyboard_listener.start()

    try:
        while (
            mouse_listener.is_alive()
            and keyboard_listener.is_alive()
            and "point" not in result
            and not result.get("cancelled")
        ):
            time.sleep(0.05)
    finally:
        mouse_listener.stop()
        keyboard_listener.stop()
        mouse_listener.join(timeout=1)
        keyboard_listener.join(timeout=1)

    bring_console_to_front()
    time.sleep(0.2)

    if result.get("cancelled"):
        # pynput detects ESC globally, but Windows also leaves the key in the
        # console input buffer. Clear it so the next prompt does not treat the
        # same ESC press as a second cancellation.
        while msvcrt.kbhit():
            msvcrt.getwch()

        print("\nReturning to the previous calibration step...")
        return None

    point = result["point"]
    print(f"Recorded: {point[0]}, {point[1]}")
    return point


def calibrate_profile(name, reader, width, height, delay_ms):
    while True:
        print("\nCUSTOM COORDINATE CALIBRATION")
        print("----------------------------------------")
        print("The console will return to the foreground after each click.")

        print("\nChoose calibration method:")
        print("1. Click the requested locations")
        print("2. Type coordinates manually")
        print("Press ESC to return to the configuration menu.")

        method_input = read_console_input("Select [1/2] (default 1): ")
        if method_input is None:
            return None

        method = method_input.strip() or "1"
        if method not in ("1", "2"):
            print("Please choose 1 or 2.")
            continue

        if method == "2":
            steps = [
                ("turn", "Page-turn button X,Y: ", "point"),
                ("activate", "Window activation point X,Y: ", "point"),
                ("top_left", "Crop top-left X,Y: ", "point"),
                ("bottom_right", "Crop bottom-right X,Y: ", "point"),
            ]
        else:
            steps = [
                ("top_left", "1/4: Click the TOP-LEFT corner of the crop area.", "click"),
                ("bottom_right", "2/4: Click the BOTTOM-RIGHT corner of the crop area.", "click"),
                (
                    "activate",
                    "3/4: Click inside the reader window where it can be activated.",
                    "click",
                ),
                ("turn", "4/4: Click the next-page button.", "click"),
            ]

        coordinates = {}
        step_index = 0
        while step_index < len(steps):
            key, prompt, input_kind = steps[step_index]
            if input_kind == "point":
                point = ask_point(prompt)
            else:
                point = capture_mouse_click(prompt)

            if point is None:
                if step_index == 0:
                    print("Returning to calibration method selection...")
                    break
                coordinates.pop(steps[step_index - 1][0], None)
                step_index -= 1
                continue

            coordinates[key] = point
            step_index += 1

        if step_index < len(steps):
            continue

        turn = coordinates["turn"]
        activate = coordinates["activate"]
        top_left = coordinates["top_left"]
        bottom_right = coordinates["bottom_right"]
        break

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
        "calibration_method": "manual" if method == "2" else "click",
    }


def recalibrate_profile_from_end(profile, width, height):
    """Recalibrate coordinates with ESC moving backward through setup."""
    method = profile.get("calibration_method")

    def coordinate_order(selected_method):
        if selected_method == "click":
            return ["top_left", "bottom_right", "activate", "turn"]
        return ["turn", "activate", "top_left", "bottom_right"]

    def read_coordinate(key, selected_method):
        prompts = {
            "top_left": "1/4: Click the TOP-LEFT corner of the crop area.",
            "bottom_right": "2/4: Click the BOTTOM-RIGHT corner of the crop area.",
            "activate": "3/4: Click inside the reader window where it can be activated.",
            "turn": "4/4: Click the next-page button.",
        }
        if selected_method == "click":
            return capture_mouse_click(prompts[key])

        manual_prompts = {
            "turn": "Page-turn button X,Y: ",
            "activate": "Window activation point X,Y: ",
            "top_left": "Crop top-left X,Y: ",
            "bottom_right": "Crop bottom-right X,Y: ",
        }
        return ask_point(manual_prompts[key])

    def store_coordinate(key, point):
        if key == "top_left":
            profile["crop"] = [point[0], point[1], profile["crop"][2], profile["crop"][3]]
        elif key == "bottom_right":
            profile["crop"] = [profile["crop"][0], profile["crop"][1], point[0], point[1]]
        else:
            profile[key] = list(point)

    while method not in ("click", "manual"):
        print("\nChoose calibration method:")
        print("1. Click the requested locations")
        print("2. Type coordinates manually")
        print("Press ESC to return to reader configurations.")
        choice = read_console_input("Select [1/2]: ")
        bring_console_to_front()
        if choice is None:
            return False
        choice = choice.strip()
        if choice == "1":
            method = "click"
        elif choice == "2":
            method = "manual"
        else:
            print("Please choose 1 or 2.")

    order = coordinate_order(method)
    index = len(order) - 1
    print("\nReturning to the final coordinate-recording step.")

    while True:
        key = order[index]
        point = read_coordinate(key, method)
        bring_console_to_front()
        time.sleep(0.25)

        if point is None:
            if index > 0:
                index -= 1
                print("\nReturning to the previous coordinate-recording step...")
                continue

            print("\nChoose calibration method:")
            print("1. Click the requested locations")
            print("2. Type coordinates manually")
            print("Press ESC to return to reader configurations.")
            choice = read_console_input("Select [1/2]: ")
            bring_console_to_front()
            if choice is None:
                return False
            choice = choice.strip()
            if choice == "1":
                method = "click"
            elif choice == "2":
                method = "manual"
            else:
                print("Please choose 1 or 2.")
                continue
            order = coordinate_order(method)
            index = 0
            print("\nStarting coordinate recording from step 1.")
            continue

        store_coordinate(key, point)
        if index < len(order) - 1:
            index += 1
            continue

        if validate_profile(profile, width, height):
            profile["calibration_method"] = method
            bring_console_to_front()
            time.sleep(0.2)
            bring_console_to_front()
            print("\nCoordinates updated. Returning to page-count entry.")
            return True

        print("\nThe coordinates are invalid. Re-record the final coordinate or go back.")
        index = len(order) - 1


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
        print("0. Back")

        choice = ask_int("\nChoose an option (ESC to return to main menu): ", 0, None, True)

        if choice is None or choice == 0:
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

            if profile is None:
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

            if updated is None:
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


def choose_image_format(current=None):
    print("\nIMAGE FORMAT")
    print("1. PNG - lossless, larger files")
    print("2. JPEG - compressed, smaller files")

    configured_format = str(APP_SETTINGS.get("default_image_format", "JPEG")).upper()
    default_choice = "1" if (current or configured_format) == "PNG" else "2"
    choice = read_console_input(f"Choose format [1/2] (default {default_choice}): ")
    if choice is None:
        return None
    choice = choice.strip() or default_choice

    if choice == "1":
        return "PNG"
    if choice == "2":
        return "JPEG"

    print("Please choose 1 or 2.")
    return choose_image_format(current)


def choose_jpeg_quality(current=None):
    print("\nJPEG quality:")
    print("1. 100 - maximum quality")
    print("2. 95  - very high quality")
    print("3. 90  - high quality")
    print("4. 85  - balanced")
    print("5. 80  - smaller files")

    qualities = {"1": 100, "2": 95, "3": 90, "4": 85, "5": 80}
    default_quality_choice = min(
        qualities, key=lambda key: abs(qualities[key] - (current or JPEG_QUALITY_DEFAULT))
    )
    choice = read_console_input(f"Choose quality [1-5] (default {default_quality_choice}): ")
    if choice is None:
        return None
    choice = choice.strip() or default_quality_choice
    if choice not in qualities:
        print("Please choose a quality from 1 to 5.")
        return choose_jpeg_quality(current)
    return qualities[choice]


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


def delete_screenshots(image_paths, session_dir):
    """Delete captured images and remove their session folder if it is empty."""
    failed = []

    for path in image_paths:
        try:
            os.remove(path)
            LOGGER.info("Deleted screenshot: %s", path)
        except FileNotFoundError:
            continue
        except OSError as exc:
            failed.append((path, exc))
            LOGGER.exception("Could not delete screenshot %s: %s", path, exc)

    if failed:
        print(f"Could not delete {len(failed)} screenshot file(s).")
        for path, exc in failed:
            print(f"  {path}: {exc}")
        return False

    try:
        os.rmdir(session_dir)
    except FileNotFoundError:
        pass
    except OSError as exc:
        LOGGER.warning("Screenshots deleted, but session folder was retained: %s", exc)
        print("Screenshots deleted, but the session folder could not be removed.")
    else:
        LOGGER.info("Removed empty capture session folder: %s", session_dir)

    return True


# ============================================================
# CAPTURE SESSION
# ============================================================


def run_capture(profile, width, height):
    LOGGER.info(
        "Capture requested: profile=%s resolution=%sx%s", profile.get("name"), width, height
    )
    print("\nCAPTURE SETTINGS")
    show_profile(profile)

    default_pause = int(APP_SETTINGS.get("default_pause_after", 0))
    default_name = datetime.now().strftime("Capture_%Y%m%d_%H%M%S")
    total_pages = None
    pause_after = default_pause
    delay_ms = int(profile.get("delay_ms", DEFAULT_DELAY_MS))
    image_format = str(APP_SETTINGS.get("default_image_format", "JPEG")).upper()
    if image_format not in ("PNG", "JPEG"):
        image_format = "JPEG"
    jpeg_quality = JPEG_QUALITY_DEFAULT
    session_name = default_name

    # Each ESC moves back exactly one setup step. Page-count ESC retains its
    # special coordinate-recalibration behavior.
    step = 0
    while step < 7:
        if step == 0:
            value = ask_int(
                (
                    "\nHow many pages should be captured? "
                    "(Press ESC to re-record the final coordinate) "
                ),
                1,
                allow_escape=True,
            )
            if value is None:
                if not recalibrate_profile_from_end(profile, width, height):
                    return "reader_config"
                bring_console_to_front()
                time.sleep(0.2)
                continue
            total_pages = value
            step = 1

        elif step == 1:
            value = ask_int(
                f"Pause after how many screenshots? (0 = disabled) [{default_pause}]: ",
                0,
                default_pause,
                allow_escape=True,
            )
            if value is None:
                step = 0
            else:
                pause_after = value
                step = 2

        elif step == 2:
            value = ask_delay_ms(delay_ms, allow_escape=True)
            if value is None:
                step = 1
            else:
                delay_ms = value
                step = 3

        elif step == 3:
            value = choose_image_format(image_format)
            if value is None:
                step = 2
            else:
                image_format = value
                step = 4 if image_format == "JPEG" else 5

        elif step == 4:
            value = choose_jpeg_quality(jpeg_quality)
            if value is None:
                step = 3
            else:
                jpeg_quality = value
                step = 5

        elif step == 5:
            raw_name = read_console_input(f"\nName for this capture [{session_name}]: ")
            if raw_name is None:
                step = 4 if image_format == "JPEG" else 3
            else:
                session_name = clean_name(raw_name.strip() or session_name)
                step = 6

        elif step == 6:
            print("\n" + "=" * 54)
            print("READY TO CAPTURE")
            print("=" * 54)
            print(f"Pages: {total_pages}")
            print(f"Pause after: {pause_after}")
            print(f"Delay: {delay_ms} ms")
            print(f"Format: {image_format}")
            if image_format == "JPEG":
                print(f"JPEG quality: {jpeg_quality}")
            print(f"Output folder: {os.path.join(CAPTURES_DIR, session_name)}")
            print("\nPress ESC to go back and change settings.")
            confirmation = read_console_input("Position the reader and press ENTER to start... ")
            if confirmation is None:
                step = 5
            else:
                break

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

    # The reader was left in the foreground during capture. Restore the
    # console before showing completion details or asking post-capture questions.
    if not bring_console_to_front():
        time.sleep(0.2)
        bring_console_to_front()

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
                if delete_screenshots(image_paths, session_dir):
                    print("Screenshot images deleted; PDF retained.")
        else:
            print("Screenshots have been retained because PDF creation failed.")

    else:
        print("PDF not created.")
        keep_images = ask_yes_no(
            "Keep the original screenshot files?",
            default=bool(APP_SETTINGS.get("keep_screenshots", True)),
        )

        if not keep_images and delete_screenshots(image_paths, session_dir):
            print("Screenshot images and session folder deleted.")
        elif keep_images:
            print("Screenshots have been retained.")

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

        choice = read_console_input("\nSelect [1/2] (ESC to exit): ")

        if choice is None or choice.strip() == "2":
            print("Goodbye.")
            break

        if choice.strip() != "1":
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
            while profile is not None:
                result = run_capture(profile, width, height)
                if result != "reader_config":
                    break
                profile = choose_profile(width, height)
        except KeyboardInterrupt:
            print("\nOperation interrupted.")
        except Exception as exc:
            LOGGER.exception("Unexpected capture workflow error: %s", exc)
            print(f"\nUnexpected error: {exc}")

        # ESC from the reader-configuration menu already means Back to the
        # main menu. Do not block there with an extra Enter-only prompt.
        if profile is None:
            continue

        input("\nPress ENTER to return to the main menu...")
