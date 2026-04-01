import time
import random
import os
import subprocess

import pyautogui
import pygetwindow as gw

pyautogui.FAILSAFE = True

_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]

# Claves fijas del perfil (los contactos van en coords["contacts"])
COORD_KEYS = ["share_button", "send_friends", "send_btn"]


def _delay(min_s=0.8, max_s=2.2):
    time.sleep(random.uniform(min_s, max_s))


def _find_chrome():
    for path in _CHROME_PATHS:
        if os.path.exists(path):
            return path
    return "chrome"


def _close_chrome():
    try:
        pyautogui.hotkey("alt", "F4")
        _delay(0.5, 1)
    except Exception:
        pass


def _send_video_to_contacts(video_url, usernames, chrome_path,
                            chrome_profile_path, profile_name, coords, log):
    """Abre Chrome una sola vez y selecciona cada contacto por su posición en el modal."""
    results = {u: False for u in usernames}
    contact_coords = coords.get("contacts", {})

    # Verificar que todos los contactos tienen coordenadas
    sin_coords = [u for u in usernames if u not in contact_coords]
    if sin_coords:
        for u in sin_coords:
            log(f"  ✗ Sin coordenadas para {u} — calibra el perfil")
        return results

    try:
        cmd = [
            chrome_path,
            f"--user-data-dir={chrome_profile_path}",
            f"--profile-directory={profile_name}",
            "--new-window",
            "--start-maximized",
            video_url,
        ]
        subprocess.Popen(cmd)
        _delay(7, 9)

        wins = [w for w in gw.getAllWindows() if "Chrome" in w.title]
        if wins:
            try:
                wins[-1].activate()
                _delay(1, 2)
            except Exception:
                pass

        # Click botón compartir
        pyautogui.click(*coords["share_button"])
        _delay(2.5, 3.5)

        # Click "Enviar a amigos"
        pyautogui.click(*coords["send_friends"])
        _delay(2.5, 3.5)

        # Click en la posición de cada contacto en la lista reciente
        for username in usernames:
            pyautogui.click(*contact_coords[username])
            _delay(0.5, 0.8)
            log(f"  ✓ Seleccionado: {username}")
            results[username] = True

        # Enviar a todos los seleccionados de una vez
        pyautogui.click(*coords["send_btn"])
        _delay(1.5, 2.5)

        log(f"  📤 Enviado a: {', '.join(usernames)}")
        _close_chrome()
        return results

    except Exception as e:
        log(f"  ✗ Error: {e}")
        _close_chrome()
        return results


def ejecutar_envios(plan, chrome_profile_path, profile_name, coord_profile,
                    log_callback=None, done_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    resultados = []

    try:
        if not coord_profile:
            log("✗ No hay perfil de coordenadas activo.")
            log("  → Ve a la pestaña Perfiles, crea uno y calibra las coordenadas.")
            if done_callback:
                done_callback(resultados)
            return

        chrome_path = _find_chrome()
        log(f"Chrome: {chrome_path}")
        log("Iniciando envíos...")

        for item in plan:
            video = item["video"]
            contactos = item["enviar_a"]
            log(f"\n📹 '{video['label']}' → {', '.join(contactos)}")

            results = _send_video_to_contacts(
                video["url"], contactos,
                chrome_path, chrome_profile_path, profile_name,
                coord_profile["coords"], log,
            )

            for contacto in contactos:
                resultados.append({
                    "video_id": video["id"],
                    "url": video["url"],
                    "label": video["label"],
                    "contacto": contacto,
                    "ok": results.get(contacto, False),
                })

            _delay(2, 4)

        log("\n✅ Proceso de envío completado.")

    except Exception as e:
        log(f"\n✗ Error crítico: {e}")

    finally:
        if done_callback:
            done_callback(resultados)
