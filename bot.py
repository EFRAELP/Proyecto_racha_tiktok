import time
import random
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


_BRAVE_PATHS = [
    r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
    r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
]


def _delay(min_s=0.8, max_s=2.2):
    time.sleep(random.uniform(min_s, max_s))


def _get_driver(chrome_profile_path, profile_name):
    opts = Options()

    # Intentar Brave primero, luego Chrome por defecto
    for path in _BRAVE_PATHS:
        if os.path.exists(path):
            opts.binary_location = path
            break

    # Usar el perfil real del usuario (donde ya tiene sesión iniciada)
    # IMPORTANTE: Brave debe estar completamente cerrado antes de ejecutar el bot
    opts.add_argument(f"--user-data-dir={chrome_profile_path}")
    opts.add_argument(f"--profile-directory={profile_name}")
    opts.add_argument("--disable-notifications")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(options=opts)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    driver.maximize_window()
    return driver


def _send_to_user(driver, username, video_url, log):
    wait = WebDriverWait(driver, 15)
    short_wait = WebDriverWait(driver, 5)
    uname = username.lstrip("@")

    try:
        # Ir directo al perfil — evita tener que buscar el botón "Nuevo mensaje"
        driver.get(f"https://www.tiktok.com/@{uname}")
        _delay(3, 5)

        # Clickear el botón "Mensaje" del perfil
        msg_btn = None
        for sel in [
            '[data-e2e="message-button"]',
            'button[aria-label*="Message"]',
            'button[aria-label*="Mensaje"]',
        ]:
            try:
                msg_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        if msg_btn is None:
            for label in ["Message", "Mensaje", "Send message", "Enviar mensaje"]:
                try:
                    msg_btn = short_wait.until(EC.element_to_be_clickable(
                        (By.XPATH, f"//button[contains(., '{label}')]")
                    ))
                    break
                except Exception:
                    continue

        if msg_btn is None:
            log(f"  ✗ No encontré el botón 'Mensaje' en el perfil de {username}")
            return False

        msg_btn.click()
        _delay(2, 3)

        # Escribir el URL en el input del chat
        msg_box = None
        for sel in [
            '[contenteditable="true"][data-e2e="message-input"]',
            '[contenteditable="true"][placeholder*="message"]',
            '[contenteditable="true"][placeholder*="mensaje"]',
            '[contenteditable="true"]',
        ]:
            try:
                msg_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        if msg_box is None:
            log(f"  ✗ No encontré el campo de mensaje para {username}")
            return False

        msg_box.click()
        _delay(0.4, 0.8)
        msg_box.send_keys(video_url)
        _delay(0.6, 1.2)
        msg_box.send_keys(Keys.RETURN)
        _delay(1.5, 2.5)
        log(f"  ✓ Enviado a {username}")
        return True

    except Exception as e:
        log(f"  ✗ Error inesperado con {username}: {e}")
        return False


def ejecutar_envios(plan, chrome_profile_path, profile_name, log_callback=None, done_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)

    resultados = []
    driver = None

    try:
        log("⚠ Asegúrate de que Brave esté completamente cerrado antes de continuar.")
        log("Abriendo Brave con tu perfil (sesión iniciada)...")
        driver = _get_driver(chrome_profile_path, profile_name)

        for item in plan:
            video = item["video"]
            log(f"\n📹 '{video['label']}' → {', '.join(item['enviar_a'])}")
            for contacto in item["enviar_a"]:
                log(f"  Enviando a {contacto}...")
                ok = _send_to_user(driver, contacto, video["url"], log)
                resultados.append({
                    "video_id": video["id"],
                    "url": video["url"],
                    "label": video["label"],
                    "contacto": contacto,
                    "ok": ok,
                })
                _delay(2, 4)

        log("\n✅ Proceso de envío completado.")

    except ModuleNotFoundError as e:
        log(f"\n✗ Dependencia faltante: {e}")
        log("  → Ejecuta en tu terminal: pip install -r requirements.txt")
    except Exception as e:
        log(f"\n✗ Error crítico en el bot: {e}")

    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
        if done_callback:
            done_callback(resultados)
