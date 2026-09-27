import ctypes
import json
import os
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk, colorchooser, messagebox

APP_NAME = "Ultimate 2 Mapper"
CONFIG = Path.home() / "Ultimate2Mapper.json"

XINPUT_DLLS = ("xinput1_4.dll", "xinput1_3.dll", "xinput9_1_0.dll")

XINPUT_GAMEPAD_DPAD_UP        = 0x0001
XINPUT_GAMEPAD_DPAD_DOWN      = 0x0002
XINPUT_GAMEPAD_DPAD_LEFT      = 0x0004
XINPUT_GAMEPAD_DPAD_RIGHT     = 0x0008
XINPUT_GAMEPAD_START          = 0x0010
XINPUT_GAMEPAD_BACK           = 0x0020
XINPUT_GAMEPAD_LEFT_THUMB     = 0x0040
XINPUT_GAMEPAD_RIGHT_THUMB    = 0x0080
XINPUT_GAMEPAD_LEFT_SHOULDER  = 0x0100
XINPUT_GAMEPAD_RIGHT_SHOULDER = 0x0200
XINPUT_GAMEPAD_A              = 0x1000
XINPUT_GAMEPAD_B              = 0x2000
XINPUT_GAMEPAD_X              = 0x4000
XINPUT_GAMEPAD_Y              = 0x8000

class XINPUT_GAMEPAD(ctypes.Structure):
    _fields_ = [
        ("wButtons", ctypes.c_ushort),
        ("bLeftTrigger", ctypes.c_ubyte),
        ("bRightTrigger", ctypes.c_ubyte),
        ("sThumbLX", ctypes.c_short),
        ("sThumbLY", ctypes.c_short),
        ("sThumbRX", ctypes.c_short),
        ("sThumbRY", ctypes.c_short),
    ]

class XINPUT_STATE(ctypes.Structure):
    _fields_ = [("dwPacketNumber", ctypes.c_ulong), ("Gamepad", XINPUT_GAMEPAD)]

def load_xinput():
    for name in XINPUT_DLLS:
        try:
            dll = ctypes.WinDLL(name)
            dll.XInputGetState.argtypes = [ctypes.c_uint, ctypes.POINTER(XINPUT_STATE)]
            dll.XInputGetState.restype = ctypes.c_uint
            return dll
        except Exception:
            pass
    return None

XINPUT = load_xinput()

BUTTONS = [
    "A", "B", "X", "Y", "LB", "RB", "LT", "RT",
    "L3", "R3", "DPad Up", "DPad Down", "DPad Left", "DPad Right",
    "View", "Menu"
]

ACTIONS = [
    "None", "Space", "Enter", "Esc", "Tab", "Shift", "Ctrl", "Alt",
    "W", "A", "S", "D", "E", "F", "Q", "R",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
]

DEFAULT = {
    "active_profile": "Gaming",
    "profiles": {
        "Gaming": {b: "None" for b in BUTTONS},
        "FPS": {b: "None" for b in BUTTONS},
        "Custom": {b: "None" for b in BUTTONS}
    },
    "rgb": {
        "enabled": True,
        "color": "#00e5ff",
        "effect": "Static",
        "brightness": 100,
        "speed": 50
    },
    "deadzone": 12
}

def deep_default():
    return json.loads(json.dumps(DEFAULT))

def load_config():
    if not CONFIG.exists():
        return deep_default()
    try:
        data = json.loads(CONFIG.read_text(encoding="utf-8"))
        base = deep_default()
        base.update(data)
        base["profiles"].update(data.get("profiles", {}))
        base["rgb"].update(data.get("rgb", {}))
        return base
    except Exception:
        return deep_default()

def save_config(data):
    CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

class ControllerPoller:
    def __init__(self, callback):
        self.callback = callback
        self.stop_event = threading.Event()
        self.last_buttons = set()
        self.last_state = None
        self.thread = threading.Thread(target=self.loop, daemon=True)

    def start(self):
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def loop(self):
        if XINPUT is None:
            self.callback(("status", "XInput is unavailable on this Windows installation."))
            return

        while not self.stop_event.is_set():
            state = XINPUT_STATE()
            result = XINPUT.XInputGetState(0, ctypes.byref(state))
            if result == 0:
                g = state.Gamepad
                pressed = set()
                bits = {
                    "A": XINPUT_GAMEPAD_A, "B": XINPUT_GAMEPAD_B,
                    "X": XINPUT_GAMEPAD_X, "Y": XINPUT_GAMEPAD_Y,
                    "LB": XINPUT_GAMEPAD_LEFT_SHOULDER,
                    "RB": XINPUT_GAMEPAD_RIGHT_SHOULDER,
                    "L3": XINPUT_GAMEPAD_LEFT_THUMB,
                    "R3": XINPUT_GAMEPAD_RIGHT_THUMB,
                    "DPad Up": XINPUT_GAMEPAD_DPAD_UP,
                    "DPad Down": XINPUT_GAMEPAD_DPAD_DOWN,
                    "DPad Left": XINPUT_GAMEPAD_DPAD_LEFT,
                    "DPad Right": XINPUT_GAMEPAD_DPAD_RIGHT,
                    "View": XINPUT_GAMEPAD_BACK,
                    "Menu": XINPUT_GAMEPAD_START,
                }
                for name, bit in bits.items():
                    if g.wButtons & bit:
                        pressed.add(name)

                if g.bLeftTrigger > 30:
                    pressed.add("LT")
                if g.bRightTrigger > 30:
                    pressed.add("RT")

                axes = (
                    g.sThumbLX / 32767.0,
                    g.sThumbLY / 32767.0,
                    g.sThumbRX / 32767.0,
                    g.sThumbRY / 32767.0,
                    g.bLeftTrigger / 255.0,
                    g.bRightTrigger / 255.0,
                )
                self.callback(("state", pressed, axes))
                self.callback(("status", "Controller detected via Windows XInput"))
            else:
                self.callback(("status", "No XInput controller detected"))
                self.callback(("state", set(), (0,0,0,0,0,0)))
            time.sleep(0.015)

class App:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1000x700")
        self.root.minsize(900, 620)
        self.root.configure(bg="#101217")
        self.data = load_config()
        self.vars = {}
        self.last_pressed = set()
        self.poller = ControllerPoller(self.controller_event)

        self.setup_style()
        self.build()
        self.load_profile()
        self.load_rgb()
        self.poller.start()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(".", background="#101217", foreground="#e8eaf0")
        style.configure("TFrame", background="#101217")
        style.configure("Card.TFrame", background="#171a21")
        style.configure("TLabel", background="#101217", foreground="#e8eaf0")
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"))
        style.configure("Sub.TLabel", foreground="#9aa1ad")
        style.configure("TButton", padding=8)
        style.configure("TNotebook", background="#101217", borderwidth=0)
        style.configure("TNotebook.Tab", padding=(16, 8))

    def build(self):
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        header = ttk.Frame(outer)
        header.pack(fill="x")
        ttk.Label(header, text="ULTIMATE 2 MAPPER", style="Title.TLabel").pack(side="left")
        self.status = ttk.Label(header, text="Starting...", style="Sub.TLabel")
        self.status.pack(side="right")

        tabs = ttk.Notebook(outer)
        tabs.pack(fill="both", expand=True, pady=(15,0))

        self.map_tab = ttk.Frame(tabs, padding=18)
        self.rgb_tab = ttk.Frame(tabs, padding=18)
        self.test_tab = ttk.Frame(tabs, padding=18)
        self.about_tab = ttk.Frame(tabs, padding=18)

        tabs.add(self.map_tab, text="Mapping")
        tabs.add(self.rgb_tab, text="RGB")
        tabs.add(self.test_tab, text="Controller Test")
        tabs.add(self.about_tab, text="About")

        self.build_mapping()
        self.build_rgb()
        self.build_test()
        self.build_about()

    def build_mapping(self):
        top = ttk.Frame(self.map_tab)
        top.pack(fill="x")

        ttk.Label(top, text="Profile:").pack(side="left")
        self.profile = ttk.Combobox(top, state="readonly", width=18,
                                    values=list(self.data["profiles"]))
        self.profile.set(self.data["active_profile"])
        self.profile.pack(side="left", padx=8)
        self.profile.bind("<<ComboboxSelected>>", lambda e: self.load_profile())

        ttk.Button(top, text="Save", command=self.save_profile).pack(side="left", padx=4)
        ttk.Button(top, text="Reset", command=self.reset_profile).pack(side="left", padx=4)

        self.map_frame = ttk.Frame(self.map_tab)
        self.map_frame.pack(fill="both", expand=True, pady=18)

        for i, button in enumerate(BUTTONS):
            r, c = divmod(i, 2)
            card = ttk.Frame(self.map_frame, style="Card.TFrame", padding=10)
            card.grid(row=r, column=c, sticky="ew", padx=6, pady=5)
            self.map_frame.columnconfigure(c, weight=1)
            ttk.Label(card, text=button, width=14, background="#171a21").pack(side="left")
            var = tk.StringVar()
            self.vars[button] = var
            cb = ttk.Combobox(card, textvariable=var, values=ACTIONS,
                              state="readonly", width=18)
            cb.pack(side="right")

        note = ttk.Label(self.map_tab,
                         text="This version uses Windows XInput for detection. It does not install a kernel driver.",
                         style="Sub.TLabel")
        note.pack(anchor="w")

    def load_profile(self):
        p = self.profile.get()
        self.data["active_profile"] = p
        mapping = self.data["profiles"].get(p, {})
        for b, var in self.vars.items():
            var.set(mapping.get(b, "None"))

    def save_profile(self):
        p = self.profile.get()
        self.data["profiles"][p] = {b: v.get() for b,v in self.vars.items()}
        self.data["active_profile"] = p
        save_config(self.data)
        messagebox.showinfo("Saved", f"Profile '{p}' saved.")

    def reset_profile(self):
        for v in self.vars.values():
            v.set("None")

    def build_rgb(self):
        ttk.Label(self.rgb_tab, text="RGB FIRE RING", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.rgb_tab,
                  text="RGB settings are stored locally. Direct proprietary RGB commands are not sent without a documented device protocol.",
                  style="Sub.TLabel").pack(anchor="w", pady=(4,20))

        self.rgb_enabled = tk.BooleanVar()
        ttk.Checkbutton(self.rgb_tab, text="Enable RGB", variable=self.rgb_enabled).pack(anchor="w", pady=8)

        row = ttk.Frame(self.rgb_tab)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text="Color", width=16).pack(side="left")
        self.rgb_preview = tk.Label(row, text="#00e5ff", width=18, relief="groove")
        self.rgb_preview.pack(side="left", padx=8)
        ttk.Button(row, text="Choose", command=self.choose_color).pack(side="left")

        row = ttk.Frame(self.rgb_tab)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text="Effect", width=16).pack(side="left")
        self.effect = ttk.Combobox(
            row,
            values=["Static", "Fire Ring", "Light-tracing", "Rainbow Ring", "Interactive Light-tracing"],
            state="readonly")
        self.effect.pack(side="left", fill="x", expand=True)

        row = ttk.Frame(self.rgb_tab)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text="Brightness", width=16).pack(side="left")
        self.brightness = tk.IntVar()
        ttk.Scale(row, from_=0, to=100, variable=self.brightness,
                  orient="horizontal").pack(side="left", fill="x", expand=True)
        self.brightness_label = ttk.Label(row, text="100%")
        self.brightness_label.pack(side="left", padx=10)

        row = ttk.Frame(self.rgb_tab)
        row.pack(fill="x", pady=8)
        ttk.Label(row, text="Speed", width=16).pack(side="left")
        self.speed = tk.IntVar()
        ttk.Scale(row, from_=0, to=100, variable=self.speed,
                  orient="horizontal").pack(side="left", fill="x", expand=True)

        ttk.Button(self.rgb_tab, text="Save RGB Settings", command=self.save_rgb).pack(anchor="w", pady=20)

    def load_rgb(self):
        rgb = self.data["rgb"]
        self.rgb_enabled.set(bool(rgb.get("enabled", True)))
        self.rgb_color = rgb.get("color", "#00e5ff")
        self.effect.set(rgb.get("effect", "Static"))
        self.brightness.set(int(rgb.get("brightness", 100)))
        self.speed.set(int(rgb.get("speed", 50)))
        self.update_rgb_preview()

    def choose_color(self):
        result = colorchooser.askcolor(color=self.rgb_color, title="RGB color")
        if result and result[1]:
            self.rgb_color = result[1]
            self.update_rgb_preview()

    def update_rgb_preview(self):
        if hasattr(self, "rgb_preview"):
            self.rgb_preview.configure(text=self.rgb_color, bg=self.rgb_color)
            self.brightness_label.configure(text=f"{int(self.brightness.get())}%")

    def save_rgb(self):
        self.data["rgb"] = {
            "enabled": bool(self.rgb_enabled.get()),
            "color": self.rgb_color,
            "effect": self.effect.get(),
            "brightness": int(self.brightness.get()),
            "speed": int(self.speed.get())
        }
        save_config(self.data)
        self.update_rgb_preview()
        messagebox.showinfo("Saved", "RGB settings saved.")

    def build_test(self):
        ttk.Label(self.test_tab, text="CONTROLLER TEST", style="Title.TLabel").pack(anchor="w")
        self.axes = ttk.Label(self.test_tab, text="LX 0.00   LY 0.00   RX 0.00   RY 0.00   LT 0%   RT 0%",
                              font=("Consolas", 13))
        self.axes.pack(anchor="w", pady=18)
        self.buttons = ttk.Label(self.test_tab, text="Buttons: —", font=("Consolas", 13))
        self.buttons.pack(anchor="w", pady=18)
        self.dpad = ttk.Label(self.test_tab, text="D-pad: —", font=("Consolas", 13))
        self.dpad.pack(anchor="w", pady=18)

    def build_about(self):
        ttk.Label(self.about_tab, text="Ultimate 2 Mapper", style="Title.TLabel").pack(anchor="w")
        ttk.Label(self.about_tab, text="Windows-only starter utility using the built-in XInput API.",
                  style="Sub.TLabel").pack(anchor="w", pady=8)
        ttk.Label(self.about_tab,
                  text="No pygame, no pip packages and no third-party controller driver are required for detection.",
                  wraplength=760).pack(anchor="w", pady=8)
        ttk.Label(self.about_tab,
                  text="Mapping profiles are saved to: " + str(CONFIG),
                  wraplength=760).pack(anchor="w", pady=8)
        ttk.Label(self.about_tab,
                  text="The RGB page is a configuration interface. Actual Fire Ring writes require the controller's proprietary RGB protocol.",
                  wraplength=760).pack(anchor="w", pady=8)

    def controller_event(self, event):
        try:
            self.root.after(0, self.handle_event, event)
        except tk.TclError:
            pass

    def handle_event(self, event):
        if event[0] == "status":
            self.status.configure(text=event[1])
            return
        _, pressed, axes = event
        self.last_pressed = pressed
        self.buttons.configure(text="Buttons: " + (", ".join(sorted(pressed)) if pressed else "—"))
        self.axes.configure(text=f"LX {axes[0]:+.2f}   LY {axes[1]:+.2f}   RX {axes[2]:+.2f}   RY {axes[3]:+.2f}   LT {axes[4]*100:.0f}%   RT {axes[5]*100:.0f}%")
        d = [x for x in ("DPad Up","DPad Down","DPad Left","DPad Right") if x in pressed]
        self.dpad.configure(text="D-pad: " + (", ".join(d) if d else "—"))

    def close(self):
        self.poller.stop()
        self.root.destroy()

if __name__ == "__main__":
    if os.name != "nt":
        messagebox.showerror(APP_NAME, "This build is intended for Windows.")
    root = tk.Tk()
    App(root)
    root.mainloop()
