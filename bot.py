import time
import random
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def _delay(min_s=0.8, max_s=2.2):
    time.sleep(random.uniform(min_s, max_s))


def _get_driver(chrome_profile_path, profile_name):
    opts = Options()

    # Usar el perfil real de Chrome (donde ya tiene sesión de TikTok iniciada)
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
        # Navegar directamente al video
        driver.get(video_url)
        _delay(3, 5)

        # Buscar el botón nativo de compartir (flecha)
        share_btn = None
        for sel in [
            '[data-e2e="share-arrow"]',
            'button[aria-label*="Share"]',
            'button[aria-label*="Compartir"]',
            '[data-e2e="video-share-arrow"]',
        ]:
            try:
                share_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        if share_btn is None:
            log(f"  ✗ No encontré el botón de compartir en el video para {username}")
            return False

        share_btn.click()
        _delay(1.5, 2.5)

        # Buscar la opción "Enviar a amigos" / "Send to friends"
        send_friends_btn = None
        for label in ["Send to friends", "Enviar a amigos", "Enviar", "Send"]:
            try:
                send_friends_btn = short_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//*[contains(text(), '{label}')]")
                ))
                break
            except Exception:
                continue

        # Fallback por data-e2e
        if send_friends_btn is None:
            for sel in [
                '[data-e2e="share-friend"]',
                '[data-e2e="send-to-friends"]',
            ]:
                try:
                    send_friends_btn = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    break
                except Exception:
                    continue

        if send_friends_btn is None:
            log(f"  ✗ No encontré la opción 'Enviar a amigos' para {username}")
            return False

        send_friends_btn.click()
        _delay(1.5, 2.5)

        # Buscar el campo de búsqueda dentro del modal
        search_box = None
        for sel in [
            'input[placeholder*="Buscar"]',
            'input[placeholder*="Search"]',
            '[data-e2e="search-user-input"]',
            'input[type="search"]',
            'input[type="text"]',
        ]:
            try:
                search_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        if search_box is None:
            log(f"  ✗ No encontré el buscador en el modal para {username}")
            return False

        search_box.click()
        _delay(0.3, 0.6)
        search_box.send_keys(uname)
        _delay(1.5, 2.5)

        # Seleccionar el primer resultado que coincida con el username
        contact_item = None
        for sel in [
            f'[data-e2e="search-result-user-item"]',
            f'[data-e2e="friend-item"]',
        ]:
            try:
                contact_item = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                break
            except Exception:
                continue

        # Fallback: buscar por texto del username en la lista
        if contact_item is None:
            try:
                contact_item = short_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//*[contains(@class,'user') or contains(@class,'item')][.//*[contains(text(),'{uname}')]]")
                ))
            except Exception:
                pass

        if contact_item is None:
            log(f"  ✗ No encontré a {username} en los resultados de búsqueda")
            return False

        contact_item.click()
        _delay(0.8, 1.5)

        # Confirmar el envío con el botón "Enviar" / "Send"
        confirm_btn = None
        for label in ["Enviar", "Send"]:
            try:
                confirm_btn = short_wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//button[contains(text(), '{label}')]")
                ))
                break
            except Exception:
                continue

        if confirm_btn is None:
            for sel in ['[data-e2e="send-btn"]', 'button[type="submit"]']:
                try:
                    confirm_btn = short_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                    break
                except Exception:
                    continue

        if confirm_btn is None:
            log(f"  ✗ No encontré el botón de confirmar envío para {username}")
            return False

        confirm_btn.click()
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
        log("Abriendo Chrome con tu perfil (sesión iniciada)...")
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
