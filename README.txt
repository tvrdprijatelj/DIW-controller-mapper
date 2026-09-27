ULTIMATE 2 MAPPER v2
=====================

This rebuild intentionally uses ONLY Python's standard library plus Windows' built-in XInput API.

That means:
- no pygame
- no pygame-ce
- no pip install
- no setuptools problem
- no third-party controller driver

START
-----
1. Install Python 3 from python.org if "py" is not recognized.
2. Put this folder at:
   D:\controller mapper
3. Double-click start.bat
   OR run:
   py ultimate2_mapper.py

FEATURES
--------
- Windows XInput controller detection
- Live button tester
- Stick/trigger values
- Mapping profiles: Gaming, FPS, Custom
- Button -> keyboard action configuration
- JSON saving
- RGB UI with color/effect/brightness/speed settings

IMPORTANT
---------
This version does NOT install a virtual controller driver and therefore does not pretend to remap the physical controller at the OS/game level.

The mapping UI is ready for a future virtual-controller backend.

RGB:
The Ultimate 2 Wireless supports RGB Fire Ring configuration through 8BitDo's official software. The controller's proprietary RGB command protocol is not included in this app, so the RGB page stores settings and provides a preview rather than sending undocumented commands to the hardware.

If your controller is connected through 2.4G/USB in XInput mode, the Controller Test tab should show live input without any extra Python package.
