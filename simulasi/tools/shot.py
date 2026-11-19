"""Tangkapan layar tampilan 3D via Chrome DevTools Protocol (headless), sekaligus membaca log konsol.

python tools/shot.py "http://127.0.0.1:8000/?mulai=S0&kamera=Mulut%20Gerlong" out.png --wait 25
Opsional: --js "kode" dijalankan sebelum tangkapan (mis. memindah kamera).
"""
import argparse
import asyncio
import base64
import random
import json
import os
import subprocess
import tempfile
import time
import urllib.request

from websockets.asyncio.client import connect

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
GPU_FLAGS = ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist", "--enable-webgl"]


async def run(url, out, wait, w, h, js):
    prof = tempfile.mkdtemp(prefix="cdp_")
    port = random.randint(9300, 9900)
    p = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={prof}",
                          *GPU_FLAGS,
                          f"--window-size={w},{h}", "--no-first-run", "--no-default-browser-check", "about:blank"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
                page = [t for t in tabs if t["type"] == "page"][0]
                break
            except Exception:
                time.sleep(0.2)
        async with connect(page["webSocketDebuggerUrl"], max_size=2 ** 26) as ws:
            mid = 0

            async def cmd(method, params=None):
                nonlocal mid
                mid += 1
                my = mid
                await ws.send(json.dumps({"id": my, "method": method, "params": params or {}}))
                while True:
                    m = json.loads(await ws.recv())
                    if m.get("id") == my:
                        return m.get("result", m)
                    log(m)

            def log(m):
                meth = m.get("method")
                if meth == "Runtime.consoleAPICalled":
                    print("console:", " ".join(str(a.get("value", a.get("description", ""))) for a in m["params"]["args"]))
                elif meth == "Runtime.exceptionThrown":
                    d = m["params"]["exceptionDetails"]
                    print("EXCEPTION:", d.get("text"), d.get("exception", {}).get("description", "")[:800])

            await cmd("Runtime.enable")
            await cmd("Page.enable")
            await cmd("Emulation.setDeviceMetricsOverride", {"width": w, "height": h, "deviceScaleFactor": 1, "mobile": False})
            await cmd("Page.navigate", {"url": url})
            t_end = time.time() + wait
            while time.time() < t_end:
                try:
                    m = json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5))
                    log(m)
                except asyncio.TimeoutError:
                    pass
            if js:
                r = await cmd("Runtime.evaluate", {"expression": js, "awaitPromise": True})
                print("js:", json.dumps(r)[:300])
                t2 = time.time() + 3
                while time.time() < t2:
                    try:
                        log(json.loads(await asyncio.wait_for(ws.recv(), timeout=0.5)))
                    except asyncio.TimeoutError:
                        pass
            r = await cmd("Page.captureScreenshot", {"format": "png"})
            open(out, "wb").write(base64.b64decode(r["data"]))
            print("tersimpan:", out)
    finally:
        p.terminate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--wait", type=float, default=20)
    ap.add_argument("--w", type=int, default=1600)
    ap.add_argument("--h", type=int, default=900)
    ap.add_argument("--js")
    a = ap.parse_args()
    asyncio.run(run(a.url, a.out, a.wait, a.w, a.h, a.js))
