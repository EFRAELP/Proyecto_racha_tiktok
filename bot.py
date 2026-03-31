import time
import random
import os
import subprocess

import sys
import pyautogui
import pygetwindow as gw

pyautogui.FAILSAFE = True

if getattr(sys, "frozen", False):
    _BASE = os.path.dirname(sys.executable)
else:
    _BASE = os.path.dirname(os.path.abspath(__file__))

# Buscar assets/ junto al exe/script, o directamente en la misma carpeta
_ASSETS_SUBDIR = os.path.join(_BASE, "assets")
ASSETS = _ASSETS_SUBDIR if os.path.isdir(_ASSETS_SUBDIR) else _BASE

_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

ASSETS_NEEDED = [
    "share_button.png",
    "send_friends.png",
    "search_box.png",
    "contact_checkbox.png",
    "send_btn.png",
]


def _delay(min_s=0.8, max_s=2.2):
    time.sleep(random.uniform(min_s, max_s))


def _find_chrome():
    for path in _CHROME_PATHS:
        if os.path.exists(path):
            return path
    return "chrome"


def _find_on_screen(image_name, timeout=15, confidence=0.8):
    img_path = os.path.join(ASSETS, image_name)
    if not os.path.exists(img_path):
        return None
    start = time.time()
    while time.time() - start < timeout:
        try:
            loc = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
            if loc:
                return loc
        except Exception:
            pass
        time.sleep(0.5)
    return None


def _check_assets(log):
    log(f"  [debug] Buscando assets en: {ASSETS}")
    missing = [f for f in ASSETS_NEEDED if not os.path.exists(os.path.join(ASSETS, f))]
    if missing:
        log("✗ Faltan imágenes de referencia en la carpeta assets/:")
        for f in missing:
            log(f"    - {f}")
        log("  → Ejecuta setup_assets.py primero para capturarlas.")
        return False
    return True


def _close_chrome():
    try:
        pyautogui.hotkey("alt", "F4")
        _delay(0.5, 1)
    except Exception:
        pass


def _send_to_user(username, video_url, chrome_path, chrome_profile_path, profile_name, log):
    uname = username.lstrip("@")
    try:
        # Abrir Chrome con el perfil del usuario y el video
        cmd = [
            chrome_path,
            f"--user-data-dir={chrome_profile_path}",
            f"--profile-directory={profile_name}",
            "--new-window",
            "--start-maximized",
            video_url,
        ]
        subprocess.Popen(cmd)
        _delay(5, 7)

        # Traer Chrome al frente
        wins = [w for w in gw.getAllWindows() if "Chrome" in w.title]
        if wins:
            try:
                wins[-1].activate()
                _delay(0.5, 1)
            except Exception:
                pass

        # Click en el botón de compartir
        loc = _find_on_screen("share_button.png", timeout=20, confidence=0.65)
        if not loc:
            log(f"  ✗ No encontré el botón de compartir para {username}")
            _close_chrome()
            return False
        pyautogui.click(loc)
        _delay(1.5, 2.5)

        # Click en "Enviar a amigos"
        loc = _find_on_screen("send_friends.png", timeout=10)
        if not loc:
            log(f"  ✗ No encontré 'Enviar a amigos' para {username}")
            _close_chrome()
            return False
        pyautogui.click(loc)
        _delay(1.5, 2.5)

        # Click en el buscador del modal
        loc = _find_on_screen("search_box.png", timeout=10)
        if not loc:
            log(f"  ✗ No encontré el buscador para {username}")
            _close_chrome()
            return False
        pyautogui.click(loc)
        _delay(0.4, 0.8)

        # Escribir el username
        pyautogui.write(uname, interval=0.08)
        _delay(2, 3)

        # Click en el checkbox del primer resultado
        loc = _find_on_screen("contact_checkbox.png", timeout=8, confidence=0.75)
        if not loc:
            log(f"  ✗ No encontré a {username} en los resultados")
            _close_chrome()
            return False
        pyautogui.click(loc)
        _delay(0.8, 1.5)

        # Click en el botón Enviar
        loc = _find_on_screen("send_btn.png", timeout=8)
        if not loc:
            log(f"  ✗ No encontré el botón de envío para {username}")
            _close_chrome()
            return False
        pyautogui.click(loc)
        _delay(1.5, 2.5)

        log(f"  ✓ Enviado a {username}")
        _close_chrome()
        return True

    except Exception as e:
        log(f"  ✗ Error inesperado con {username}: {e}")
        _close_chrome()
        return False


def ejecutar_envios(plan, chrome_profile_path, profile_name, log_callback=None, done_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    resultados = []

    try:
        if not _check_assets(log):
            if done_callback:
                done_callback(resultados)
            return

        chrome_path = _find_chrome()
        log(f"Usando Chrome: {chrome_path}")
        log("Iniciando envíos...")

        for item in plan:
            video = item["video"]
            log(f"\n📹 '{video['label']}' → {', '.join(item['enviar_a'])}")
            for contacto in item["enviar_a"]:
                log(f"  Enviando a {contacto}...")
                ok = _send_to_user(
                    contacto, video["url"],
                    chrome_path, chrome_profile_path, profile_name,
                    log
                )
                resultados.append({
                    "video_id": video["id"],
                    "url": video["url"],
                    "label": video["label"],
                    "contacto": contacto,
                    "ok": ok,
                })
                _delay(2, 4)

        log("\n✅ Proceso de envío completado.")

    except Exception as e:
        log(f"\n✗ Error crítico: {e}")

    finally:
        if done_callback:
            done_callback(resultados)
