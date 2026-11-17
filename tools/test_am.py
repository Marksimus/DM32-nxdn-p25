#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Check AM receiver gain and register restoration on the host, with AM on and off.

Requires a C compiler with ASan/UBSan. Uses only the generated derivative and
synthetic RSSI samples; never opens a radio or downloads stock firmware.
"""
import os
from pathlib import Path
import subprocess
import tempfile

from build_radiofoundry import prepare, DEST


def main():
    prepare()
    sources = [
        "tests/host/fd6818Test.c",
        "drivers/rf/fd6818/fd6818.c",
        "drivers/rf/rfbus/rfbus.c",
        "boards/dm1801pro/rf_tables_dm1801pro.c",
        "drivers/rf/subaudio/subaudio.c",
    ]
    flags = [
        "-std=gnu99", "-Wall", "-Wextra", "-Wshadow", "-Werror", "-Wno-unused-parameter",
        "-g", "-fsanitize=address,undefined", "-fno-sanitize-recover=undefined",
        "-fno-omit-frame-pointer", "-D__attribute__(x)=",
        "-I" + str(DEST / "core"), "-I" + str(DEST / "drivers"),
    ]
    env = {**os.environ, "UBSAN_OPTIONS": "halt_on_error=1:print_stacktrace=1"}
    with tempfile.TemporaryDirectory(prefix="am-gain-") as tmp:
        for enabled in (1, 0):
            binary = Path(tmp) / f"fd6818-am-{enabled}"
            subprocess.run([
                os.environ.get("CC", "cc"), *flags, f"-DCONFIG_AM_RX={enabled}",
                *[str(DEST / p) for p in sources], "-o", str(binary),
            ], check=True)
            subprocess.run([str(binary)], check=True, env=env)
            print(f"AM_RX={enabled}: driver and register regressions passed (ASan/UBSan)", flush=True)


if __name__ == "__main__":
    main()
