# TikTok Rachas Manager

Automatizador de rachas de TikTok con biblioteca de videos, algoritmo de optimización y Selenium.

---

## Setup inicial (una sola vez)

### 1. Prerrequisitos
- Python 3.10+: https://python.org
- Git: https://git-scm.com
- Google Chrome instalado

### 2. Crear el repositorio privado en GitHub
1. Ve a github.com → New repository
2. Nómbralo `tiktok-rachas`, márcalo como **Privado**
3. No agregues README ni .gitignore (lo haremos manual)

### 3. Clonar y configurar en tu PC principal
```bash
git clone https://github.com/TU_USUARIO/tiktok-rachas.git
cd tiktok-rachas
```
Copia todos los archivos del proyecto dentro de esa carpeta.

```bash
git add .
git commit -m "setup inicial"
git push
```

### 4. Instalar dependencias y construir el .exe
```bash
pip install -r requirements.txt
build.bat
```
El `.exe` se genera en `dist\`. Cópialo a la raíz del proyecto (junto a `data\` y `config.json`).

### 5. Configurar el perfil de Chrome
Al abrir la app por primera vez, ve a **⚙ Config** e ingresa la ruta de tu perfil de Chrome.

**Cómo encontrar la ruta:**
- Abre Chrome → barra de dirección → escribe `chrome://version`
- Busca el campo **"Profile Path"**
- Copia todo hasta `\User Data` (sin incluir `\Default`)

Ejemplo:
```
C:\Users\Efrain\AppData\Local\Google\Chrome\User Data
```

> **Importante:** Chrome debe estar cerrado cuando el bot se ejecute. TikTok debe estar con sesión iniciada en ese perfil.

---

## Setup en la segunda PC (laptop)

```bash
git clone https://github.com/TU_USUARIO/tiktok-rachas.git
cd tiktok-rachas
pip install -r requirements.txt
build.bat
```
Configura el perfil de Chrome igual que en el paso 5.
Desde ahí, el Pull/Push mantiene las BDs sincronizadas automáticamente.

---

## Uso diario

1. Ejecuta `TikTokRachas.exe`
2. La app hace **Pull** automático para tener la BD más reciente
3. Ve a **🚀 Enviar Hoy** → **Calcular plan óptimo**
4. Revisa el plan → **Ejecutar envíos**
5. Selenium manda todo y hace **Push** automático al terminar

---

## Flujo de datos

- `data/biblioteca.json` → videos pendientes con sus destinatarios
- `data/historial.json` → registro de todos los envíos realizados
- `data/contactos.json` → lista de @usuarios de racha

Cuando un video se envía a alguien, esa persona se elimina de su lista `para`.
Si la lista queda vacía, el video sale de la biblioteca automáticamente.

---

## Notas sobre el bot

El bot usa tu perfil real de Chrome para evitar detección. Aun así, TikTok
puede detectar automatización. Para minimizar el riesgo:
- El bot agrega delays aleatorios entre acciones
- No ejecutes envíos masivos (más de 10-15 por sesión)
- Si falla con un contacto específico, lo logea y continúa con el siguiente

Si TikTok cambia su UI y el bot deja de funcionar, los selectores
se actualizan en `bot.py` (busca los `CSS_SELECTOR`).
