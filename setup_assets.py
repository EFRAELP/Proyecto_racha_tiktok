"""
setup_assets.py — Captura de imágenes de referencia para el bot.

Ejecuta este script UNA SOLA VEZ antes de usar el bot.
Te guiará para capturar cada botón que el bot necesita reconocer en pantalla.

Cómo usarlo:
  1. Abre Chrome y navega a un video de TikTok
  2. Corre este script: python setup_assets.py
  3. Sigue las instrucciones en pantalla para cada imagen
"""

import os
import time
import pyautogui

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS, exist_ok=True)

REGION_SIZE = 70  # Tamaño en píxeles de la región a capturar alrededor del cursor

STEPS = [
    (
        "share_button.png",
        "Botón COMPARTIR (flecha/avión) del video",
        "Abre un video en TikTok. Mueve el cursor ENCIMA del ícono de compartir (la flecha)."
    ),
    (
        "send_friends.png",
        "Opción 'Enviar a amigos'",
        "Haz click en el botón compartir para abrir el menú. Mueve el cursor encima de 'Enviar a amigos'."
    ),
    (
        "search_box.png",
        "Campo de búsqueda del modal",
        "Dentro del modal 'Enviar a amigos', mueve el cursor encima del campo de búsqueda (donde dice 'Buscar')."
    ),
    (
        "contact_checkbox.png",
        "Checkbox de un contacto en los resultados",
        "Busca un contacto cualquiera. Mueve el cursor encima del CÍRCULO/CHECKBOX a la derecha del nombre."
    ),
    (
        "send_btn.png",
        "Botón ENVIAR (para confirmar)",
        "Selecciona un contacto (el círculo se llena). Mueve el cursor encima del botón 'Enviar' que aparece."
    ),
]


def capture_step(filename, title, instruction):
    print(f"\n{'─' * 50}")
    print(f"  [{title}]")
    print(f"  {instruction}")
    print(f"{'─' * 50}")
    print("  Cuando el cursor esté ENCIMA del elemento, presiona ENTER.")
    input("  → ")

    x, y = pyautogui.position()
    half = REGION_SIZE // 2
    region = (x - half, y - half, REGION_SIZE, REGION_SIZE)

    screenshot = pyautogui.screenshot(region=region)
    path = os.path.join(ASSETS, filename)
    screenshot.save(path)
    print(f"  ✓ Guardado: {filename}")
    time.sleep(0.5)


def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║   Setup de imágenes — TikTok Rachas Bot      ║")
    print("╚══════════════════════════════════════════════╝")
    print("\nEste proceso captura pequeñas imágenes de los botones")
    print("que el bot necesita reconocer. Es un proceso de una sola vez.")
    print("\nTen Chrome abierto con TikTok antes de continuar.")
    input("\nPresiona ENTER para comenzar...")

    for filename, title, instruction in STEPS:
        capture_step(filename, title, instruction)

    print("\n╔══════════════════════════════════════════════╗")
    print("║  ✅ Todas las imágenes capturadas             ║")
    print("║  Ya puedes usar el bot normalmente.           ║")
    print("╚══════════════════════════════════════════════╝\n")


if __name__ == "__main__":
    main()
