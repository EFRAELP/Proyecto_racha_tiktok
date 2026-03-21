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


_NEW_MSG_SELECTORS = [
    '[data-e2e="new-message-button"]',
    'button[aria-label*="New message"]',
    'button[aria-label*="Compose"]',
    'button[aria-label*="nuevo"]',
    '[class*="newMessageBtn"]',
    '[class*="compose"]',
    # ícono de lápiz/edit dentro de la barra de mensajes
    'div[class*="DM"] button',
    'aside button[aria-label]',
]

_SEARCH_SELECTORS = [
    'input[data-e2e="search-user-input"]',
    'input[placeholder*="Search"]',
    'input[placeholder*="Buscar"]',
    'input[placeholder*="search"]',
    '[role="dialog"] input',
    '[role="combobox"]',
]


def _click_new_message(driver, wait, log):
    """Intenta abrir el modal de nuevo mensaje. Devuelve True si lo logra."""
    for sel in _NEW_MSG_SELECTORS:
        try:
            btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
            btn.click()
            _delay(1.5, 2.5)
            return True
        except Exception:
            continue

    # Último recurso: buscar por texto visible
    for label in ["New message", "Nuevo mensaje", "Compose", "Redactar"]:
        try:
            btn = driver.find_element(By.XPATH, f"//*[text()='{label}']")
            btn.click()
            _delay(1.5, 2.5)
            return True
        except Exception:
            continue

    log("  ⚠ No encontré el botón 'Nuevo mensaje'")
    return False


def _send_to_user(driver, username, video_url, log):
    wait = WebDriverWait(driver, 15)
    short_wait = WebDriverWait(driver, 5)

    try:
        driver.get("https://www.tiktok.com/messages")
        _delay(3, 5)

        # Abrir modal de nuevo mensaje
        modal_open = _click_new_message(driver, wait, log)
        if not modal_open:
            log(f"  ✗ No pude abrir el modal de nuevo mensaje para {username}")
            return False

        # Buscar campo de búsqueda DENTRO del modal (debe ser interactuable)
        search = None
        for sel in _SEARCH_SELECTORS:
            try:
                search = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        if search is None:
            log(f"  ✗ No pude encontrar el campo de búsqueda para {username}")
            return False

        search.click()
        _delay(0.3, 0.6)
        search.send_keys(username.lstrip("@"))
        _delay(2, 3)

        # Clic en el resultado que coincida con el username
        uname_lower = username.lstrip("@").lower()
        try:
            # Buscar dentro del modal/lista de resultados
            resultado = wait.until(EC.element_to_be_clickable((
                By.XPATH,
                f"//*[contains(translate(@data-e2e,'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'user-result')] | "
                f"//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{uname_lower}')]"
            )))
            resultado.click()
            _delay(1.5, 2.5)
        except Exception as e:
            log(f"  ✗ No encontré a {username} en los resultados: {e}")
            return False

        # Confirmar selección si aparece un botón de confirmación
        for label in ["Chat", "Message", "Confirm", "Next", "Siguiente"]:
            try:
                confirm = short_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//*[text()='{label}']")
                ))
                confirm.click()
                _delay(1, 2)
                break
            except Exception:
                continue

        # Escribir el URL en el input del mensaje
        try:
            msg_box = wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                '[contenteditable="true"][data-e2e="message-input"], '
                '[contenteditable="true"][placeholder*="message"], '
                '[contenteditable="true"]'
            )))
            msg_box.click()
            _delay(0.4, 0.8)
            msg_box.send_keys(video_url)
            _delay(0.6, 1.2)
            msg_box.send_keys(Keys.RETURN)
            _delay(1.5, 2.5)
            log(f"  ✓ Enviado a {username}")
            return True
        except Exception as e:
            log(f"  ✗ No pude escribir/enviar el mensaje a {username}: {e}")
            return False

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
