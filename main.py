import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import uuid
import sys
import threading
import calendar as cal_mod
from datetime import datetime

from algoritmo import calcular_plan
from sync import git_pull, git_push
import bot

# ── Paths ─────────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BASE = os.path.dirname(sys.executable)
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

DATA = os.path.join(BASE, "data")
CONFIG_PATH = os.path.join(BASE, "config.json")
BIBLIOTECA_PATH = os.path.join(DATA, "biblioteca.json")
HISTORIAL_PATH = os.path.join(DATA, "historial.json")
CONTACTOS_PATH = os.path.join(DATA, "contactos.json")
COORD_PROFILES_PATH = os.path.join(DATA, "coord_profiles.json")

# ── Colores ───────────────────────────────────────────────────────────────────
BG = "#0d1117"
BG2 = "#161b22"
BG3 = "#21262d"
ACCENT = "#e91e8c"

CALIB_STEPS = [
    ("share_button",      "Botón Compartir",
     "Abre TikTok en un video en Chrome.\nMueve el cursor al botón de compartir (↗) y presiona Capturar."),
    ("send_friends",      "Enviar a amigos",
     "Haz click en el botón compartir para abrir el menú.\nMueve el cursor a 'Enviar a amigos' y presiona Capturar."),
    ("search_box",        "Campo de búsqueda",
     "Dentro del modal 'Enviar a amigos',\nmueve el cursor al campo de búsqueda y presiona Capturar."),
    ("contact_checkbox",  "Checkbox del contacto",
     "Busca cualquier contacto. Mueve el cursor al\ncírculo/checkbox del primer resultado y presiona Capturar."),
    ("send_btn",          "Botón Enviar",
     "Selecciona el contacto (el círculo se llena).\nMueve el cursor al botón 'Enviar' y presiona Capturar."),
]
ACCENT2 = "#c2185b"
FG = "#e6edf3"
FG2 = "#8b949e"
GREEN = "#3fb950"
RED = "#f85149"
YELLOW = "#d29922"


# ── Helpers JSON ──────────────────────────────────────────────────────────────
def _leer(path, default):
    os.makedirs(DATA, exist_ok=True)
    if not os.path.exists(path):
        _guardar(path, default)
        return default
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            _guardar(path, default)
            return default


def _guardar(path, data):
    os.makedirs(DATA, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _leer_config():
    if not os.path.exists(CONFIG_PATH):
        cfg = {"chrome_profile": "", "chrome_profile_name": "Default"}
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
        return cfg
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)


def _guardar_config(cfg):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TikTok Rachas Manager")
        self.geometry("860x620")
        self.minsize(760, 540)
        self.configure(bg=BG)
        self._plan_actual = []
        self._bib_row_ids = {}
        self._setup_styles()
        self._build_top_bar()
        self._build_notebook()
        self.refresh_all()

    # ── Styles ────────────────────────────────────────────────────────────────
    def _setup_styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG2, foreground=FG2,
                    padding=[14, 7], font=("Segoe UI", 9))
        s.map("TNotebook.Tab",
              background=[("selected", BG3)],
              foreground=[("selected", FG)])
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=FG, font=("Segoe UI", 9))
        s.configure("Header.TLabel", background=BG, foreground=FG,
                    font=("Segoe UI", 10, "bold"))
        s.configure("TButton", background=ACCENT, foreground="white",
                    font=("Segoe UI", 9, "bold"), padding=[10, 5], borderwidth=0)
        s.map("TButton",
              background=[("active", ACCENT2), ("disabled", BG3)],
              foreground=[("disabled", FG2)])
        s.configure("Secondary.TButton", background=BG3, foreground=FG)
        s.map("Secondary.TButton", background=[("active", BG2)])
        s.configure("Treeview", background=BG2, foreground=FG,
                    fieldbackground=BG2, font=("Segoe UI", 9), rowheight=26)
        s.configure("Treeview.Heading", background=BG3, foreground=FG2,
                    font=("Segoe UI", 9, "bold"))
        s.map("Treeview", background=[("selected", ACCENT)])
        s.configure("TScrollbar", background=BG3, troughcolor=BG2,
                    arrowcolor=FG2, borderwidth=0)
        s.configure("TLabelframe", background=BG, bordercolor=BG3)
        s.configure("TLabelframe.Label", background=BG, foreground=FG2,
                    font=("Segoe UI", 8))

    # ── Top bar ───────────────────────────────────────────────────────────────
    def _build_top_bar(self):
        bar = tk.Frame(self, bg=BG2, pady=10)
        bar.pack(fill="x")

        tk.Label(bar, text="🎵  TikTok Rachas", bg=BG2, fg=FG,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=16)

        self.sync_lbl = tk.Label(bar, text="", bg=BG2, fg=FG2,
                                 font=("Segoe UI", 8))
        self.sync_lbl.pack(side="left", padx=8)

        ttk.Button(bar, text="⚙ Config", style="Secondary.TButton",
                   command=self._open_config).pack(side="right", padx=6)
        ttk.Button(bar, text="⬆ Push", style="Secondary.TButton",
                   command=self._push).pack(side="right", padx=4)
        ttk.Button(bar, text="⬇ Pull", style="Secondary.TButton",
                   command=self._pull).pack(side="right", padx=4)
        tk.Label(bar, text="", bg=BG2).pack(side="right", padx=4)

    # ── Notebook ──────────────────────────────────────────────────────────────
    def _build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=10, pady=8)

        self.tab_dash = ttk.Frame(self.nb)
        self.tab_bib = ttk.Frame(self.nb)
        self.tab_cont = ttk.Frame(self.nb)
        self.tab_enviar = ttk.Frame(self.nb)

        self.tab_perfiles = ttk.Frame(self.nb)
        self.tab_historial = ttk.Frame(self.nb)

        self.nb.add(self.tab_dash, text="  📊 Dashboard  ")
        self.nb.add(self.tab_bib, text="  📚 Biblioteca  ")
        self.nb.add(self.tab_cont, text="  👥 Contactos  ")
        self.nb.add(self.tab_enviar, text="  🚀 Enviar Hoy  ")
        self.nb.add(self.tab_perfiles, text="  🖥 Perfiles  ")
        self.nb.add(self.tab_historial, text="  📅 Historial  ")

        self._build_dashboard()
        self._build_biblioteca()
        self._build_contactos()
        self._build_enviar()
        self._build_perfiles()
        self._build_historial()

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD
    # ══════════════════════════════════════════════════════════════════════════
    def _build_dashboard(self):
        f = self.tab_dash
        ttk.Label(f, text="Videos pendientes por contacto",
                  style="Header.TLabel").pack(pady=(14, 6), padx=14, anchor="w")

        frame_tree = tk.Frame(f, bg=BG)
        frame_tree.pack(fill="both", expand=True, padx=14, pady=4)

        cols = ("contacto", "pendientes", "ultimo_envio")
        self.tree_dash = ttk.Treeview(frame_tree, columns=cols, show="headings", height=12)
        self.tree_dash.heading("contacto", text="Contacto")
        self.tree_dash.heading("pendientes", text="Pendientes")
        self.tree_dash.heading("ultimo_envio", text="Último envío")
        self.tree_dash.column("contacto", width=220)
        self.tree_dash.column("pendientes", width=100, anchor="center")
        self.tree_dash.column("ultimo_envio", width=200, anchor="center")

        sb = ttk.Scrollbar(frame_tree, orient="vertical", command=self.tree_dash.yview)
        self.tree_dash.configure(yscrollcommand=sb.set)

        self.tree_dash.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        ttk.Button(f, text="↺  Actualizar", style="Secondary.TButton",
                   command=self._refresh_dashboard).pack(pady=10)

    def _refresh_dashboard(self):
        for r in self.tree_dash.get_children():
            self.tree_dash.delete(r)

        biblioteca = _leer(BIBLIOTECA_PATH, [])
        contactos = _leer(CONTACTOS_PATH, [])
        historial = _leer(HISTORIAL_PATH, [])

        conteo = {c: 0 for c in contactos}
        for v in biblioteca:
            for c in v.get("para", []):
                if c in conteo:
                    conteo[c] += 1

        ultimo = {}
        for h in historial:
            c, fecha = h.get("enviado_a"), h.get("fecha", "")
            if c and (c not in ultimo or fecha > ultimo[c]):
                ultimo[c] = fecha

        for contacto in contactos:
            n = conteo.get(contacto, 0)
            tag = "ok" if n > 0 else "vacio"
            icono = "✓" if n > 0 else "⚠"
            self.tree_dash.insert("", "end", values=(
                contacto, f"{icono} {n}", ultimo.get(contacto, "—")
            ), tags=(tag,))

        self.tree_dash.tag_configure("ok", foreground=GREEN)
        self.tree_dash.tag_configure("vacio", foreground=YELLOW)

    # ══════════════════════════════════════════════════════════════════════════
    # BIBLIOTECA
    # ══════════════════════════════════════════════════════════════════════════
    def _build_biblioteca(self):
        f = self.tab_bib

        tree_frame = tk.Frame(f, bg=BG)
        tree_frame.pack(fill="both", expand=True, padx=14, pady=14)

        cols = ("label", "url", "para")
        self.tree_bib = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree_bib.heading("label", text="Nombre")
        self.tree_bib.heading("url", text="URL")
        self.tree_bib.heading("para", text="Destinatarios")
        self.tree_bib.column("label", width=180)
        self.tree_bib.column("url", width=310)
        self.tree_bib.column("para", width=230)

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_bib.yview)
        self.tree_bib.configure(yscrollcommand=sb.set)

        self.tree_bib.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        btn_frame = tk.Frame(f, bg=BG)
        btn_frame.pack(pady=(0, 12))
        ttk.Button(btn_frame, text="➕  Agregar video",
                   command=self._agregar_video).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✏  Editar", style="Secondary.TButton",
                   command=self._editar_video).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑  Eliminar", style="Secondary.TButton",
                   command=self._eliminar_video).pack(side="left", padx=6)

    def _refresh_biblioteca(self):
        for r in self.tree_bib.get_children():
            self.tree_bib.delete(r)
        self._bib_row_ids = {}
        for v in _leer(BIBLIOTECA_PATH, []):
            row_id = self.tree_bib.insert("", "end", values=(
                v["label"], v["url"], ", ".join(v.get("para", []))
            ))
            self._bib_row_ids[row_id] = v["id"]

    def _video_dialog(self, title, label="", url="", para_actual=None):
        """Ventana reutilizable para agregar/editar video. Retorna dict o None."""
        win = tk.Toplevel(self)
        win.title(title)
        win.geometry("500x480")
        win.configure(bg=BG)
        win.grab_set()
        win.resizable(False, True)
        result = {}

        def lbl(text):
            tk.Label(win, text=text, bg=BG, fg=FG2,
                     font=("Segoe UI", 8)).pack(pady=(10, 2), padx=20, anchor="w")

        lbl("Nombre del video")
        e_label = tk.Entry(win, width=56, font=("Segoe UI", 9),
                           bg=BG3, fg=FG, insertbackground=FG, relief="flat")
        e_label.insert(0, label)
        e_label.pack(padx=20, ipady=4)

        lbl("URL de TikTok")
        e_url = tk.Entry(win, width=56, font=("Segoe UI", 9),
                         bg=BG3, fg=FG, insertbackground=FG, relief="flat")
        e_url.insert(0, url)
        e_url.pack(padx=20, ipady=4)

        lbl("Enviar a")
        contactos = _leer(CONTACTOS_PATH, [])

        # Botón anclado al fondo — se pack ANTES del área expandible
        btn_frame = tk.Frame(win, bg=BG)
        btn_frame.pack(side="bottom", fill="x", pady=10)

        cb_outer = tk.Frame(win, bg=BG3, relief="flat")
        cb_outer.pack(padx=20, fill="both", expand=True, pady=(0, 4))

        cb_canvas = tk.Canvas(cb_outer, bg=BG3, highlightthickness=0)
        cb_scroll = ttk.Scrollbar(cb_outer, orient="vertical", command=cb_canvas.yview)
        cb_canvas.configure(yscrollcommand=cb_scroll.set)
        cb_scroll.pack(side="right", fill="y")
        cb_canvas.pack(side="left", fill="both", expand=True)

        cb_inner = tk.Frame(cb_canvas, bg=BG3)
        cb_canvas.create_window((0, 0), window=cb_inner, anchor="nw")

        check_vars = {}
        for c in contactos:
            var = tk.BooleanVar(value=bool(para_actual and c in para_actual))
            chk = tk.Checkbutton(
                cb_inner, text=c, variable=var,
                bg=BG3, fg=FG, selectcolor=BG2,
                activebackground=BG3, activeforeground=FG,
                font=("Segoe UI", 9), anchor="w"
            )
            chk.pack(fill="x", padx=8, pady=2)
            check_vars[c] = var

        cb_inner.bind("<Configure>",
                      lambda e: cb_canvas.configure(scrollregion=cb_canvas.bbox("all")))

        def confirmar():
            l = e_label.get().strip()
            u = e_url.get().strip()
            sel = [c for c, var in check_vars.items() if var.get()]
            if not l or not u or not sel:
                messagebox.showwarning("Faltan datos",
                                       "Completa nombre, URL y al menos 1 destinatario.",
                                       parent=win)
                return
            result["label"] = l
            result["url"] = u
            result["para"] = sel
            win.destroy()

        ttk.Button(btn_frame, text="Guardar", command=confirmar).pack()
        win.wait_window()
        return result if result else None

    def _agregar_video(self):
        contactos = _leer(CONTACTOS_PATH, [])
        if not contactos:
            messagebox.showinfo("Sin contactos",
                                "Agrega contactos primero en la pestaña Contactos.")
            return
        r = self._video_dialog("Agregar video")
        if not r:
            return
        bib = _leer(BIBLIOTECA_PATH, [])
        bib.append({"id": str(uuid.uuid4())[:8], **r})
        _guardar(BIBLIOTECA_PATH, bib)
        self._refresh_biblioteca()
        self._refresh_dashboard()

    def _editar_video(self):
        sel = self.tree_bib.selection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un video de la lista.")
            return
        vid_id = self._bib_row_ids.get(sel[0])
        if not vid_id:
            return
        bib = _leer(BIBLIOTECA_PATH, [])
        video = next((v for v in bib if v["id"] == vid_id), None)
        if not video:
            return
        r = self._video_dialog("Editar video", video["label"],
                               video["url"], video.get("para", []))
        if not r:
            return
        for v in bib:
            if v["id"] == vid_id:
                v.update(r)
                break
        _guardar(BIBLIOTECA_PATH, bib)
        self._refresh_biblioteca()
        self._refresh_dashboard()

    def _eliminar_video(self):
        sel = self.tree_bib.selection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un video primero.")
            return
        if not messagebox.askyesno("Confirmar", "¿Eliminar este video de la biblioteca?"):
            return
        vid_id = self._bib_row_ids.get(sel[0])
        if not vid_id:
            return
        bib = [v for v in _leer(BIBLIOTECA_PATH, []) if v["id"] != vid_id]
        _guardar(BIBLIOTECA_PATH, bib)
        self._refresh_biblioteca()
        self._refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # CONTACTOS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_contactos(self):
        f = self.tab_cont
        ttk.Label(f, text="Contactos de racha",
                  style="Header.TLabel").pack(pady=(14, 6), padx=14, anchor="w")

        self.lb_cont = tk.Listbox(f, font=("Segoe UI", 11), bg=BG2, fg=FG,
                                  selectbackground=ACCENT, activestyle="none",
                                  relief="flat", height=14)
        self.lb_cont.pack(fill="both", expand=True, padx=14, pady=4)

        btn_frame = tk.Frame(f, bg=BG)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="➕  Agregar",
                   command=self._agregar_contacto).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑  Eliminar", style="Secondary.TButton",
                   command=self._eliminar_contacto).pack(side="left", padx=6)

    def _refresh_contactos(self):
        self.lb_cont.delete(0, "end")
        for c in _leer(CONTACTOS_PATH, []):
            self.lb_cont.insert("end", c)

    def _agregar_contacto(self):
        username = simpledialog.askstring(
            "Agregar contacto", "Ingresa el @usuario de TikTok:", parent=self
        )
        if not username:
            return
        username = username.strip()
        if not username.startswith("@"):
            username = "@" + username
        contactos = _leer(CONTACTOS_PATH, [])
        if username in contactos:
            messagebox.showinfo("Ya existe", f"{username} ya está en tu lista.")
            return
        contactos.append(username)
        _guardar(CONTACTOS_PATH, contactos)
        self._refresh_contactos()
        self._refresh_dashboard()

    def _eliminar_contacto(self):
        sel = self.lb_cont.curselection()
        if not sel:
            return
        username = self.lb_cont.get(sel[0])
        if not messagebox.askyesno("Confirmar",
                                   f"¿Eliminar {username}?\nSe quitará de todos los videos también."):
            return
        contactos = [c for c in _leer(CONTACTOS_PATH, []) if c != username]
        _guardar(CONTACTOS_PATH, contactos)

        bib = _leer(BIBLIOTECA_PATH, [])
        for v in bib:
            v["para"] = [c for c in v.get("para", []) if c != username]
        bib = [v for v in bib if v["para"]]
        _guardar(BIBLIOTECA_PATH, bib)

        self._refresh_contactos()
        self._refresh_biblioteca()
        self._refresh_dashboard()

    # ══════════════════════════════════════════════════════════════════════════
    # ENVIAR HOY
    # ══════════════════════════════════════════════════════════════════════════
    def _build_enviar(self):
        f = self.tab_enviar

        btn_top = tk.Frame(f, bg=BG)
        btn_top.pack(pady=12, padx=14, fill="x")
        ttk.Button(btn_top, text="⚡  Calcular plan óptimo",
                   command=self._calcular_plan).pack(side="left")
        self.btn_ejecutar = ttk.Button(btn_top, text="🚀  Ejecutar envíos",
                                       command=self._ejecutar, state="disabled")
        self.btn_ejecutar.pack(side="right")

        plan_frame = ttk.LabelFrame(f, text=" Plan del día ")
        plan_frame.pack(fill="both", padx=14, pady=4, expand=False)

        cols = ("video", "enviar_a")
        self.tree_plan = ttk.Treeview(plan_frame, columns=cols, show="headings", height=5)
        self.tree_plan.heading("video", text="Video")
        self.tree_plan.heading("enviar_a", text="Enviar a")
        self.tree_plan.column("video", width=260)
        self.tree_plan.column("enviar_a", width=450)
        self.tree_plan.pack(fill="both", padx=8, pady=8)

        log_frame = ttk.LabelFrame(f, text=" Log de ejecución ")
        log_frame.pack(fill="both", padx=14, pady=4, expand=True)

        self.log_text = tk.Text(
            log_frame, height=8, bg="#0d1117", fg=GREEN,
            font=("Consolas", 8), state="disabled", relief="flat"
        )
        log_sb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_sb.set)
        self.log_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        log_sb.pack(side="right", fill="y", pady=8)

    def _calcular_plan(self):
        for r in self.tree_plan.get_children():
            self.tree_plan.delete(r)

        biblioteca = _leer(BIBLIOTECA_PATH, [])
        if not biblioteca:
            messagebox.showinfo("Sin videos", "La biblioteca está vacía.")
            return

        plan, sin_cobertura = calcular_plan(biblioteca)
        self._plan_actual = plan

        if not plan:
            messagebox.showinfo("Sin plan", "No hay videos asignados a ningún contacto.")
            return

        for item in plan:
            self.tree_plan.insert("", "end", values=(
                item["video"]["label"],
                ", ".join(item["enviar_a"])
            ))

        self._log(f"Plan calculado: {len(plan)} video(s) para enviar hoy.")

        if sin_cobertura:
            self._log(f"⚠ Sin videos: {', '.join(sin_cobertura)}")
            messagebox.showwarning(
                "Contactos sin videos",
                f"Estos contactos no tienen videos asignados:\n{chr(10).join(sin_cobertura)}"
            )

        self.btn_ejecutar.config(state="normal")

    def _log(self, msg):
        self.log_text.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _ejecutar(self):
        if not self._plan_actual:
            return

        cfg = _leer_config()
        chrome_profile = cfg.get("chrome_profile", "").strip()
        chrome_profile_name = cfg.get("chrome_profile_name", "Default")

        if not chrome_profile:
            messagebox.showerror(
                "Configuración incompleta",
                "Configura el path de tu perfil de Chrome en ⚙ Config primero."
            )
            return

        # Cargar perfil de coordenadas activo
        activo_id = cfg.get("active_coord_profile", "")
        perfiles = _leer(COORD_PROFILES_PATH, [])
        coord_profile = next((p for p in perfiles if p["id"] == activo_id), None)
        if not coord_profile:
            messagebox.showerror(
                "Sin perfil activo",
                "Ve a la pestaña 🖥 Perfiles, crea un perfil y calibra las coordenadas."
            )
            return

        self.btn_ejecutar.config(state="disabled")
        self._log(f"Iniciando Chrome con perfil '{coord_profile['name']}'...")

        def on_done(resultados):
            bib = _leer(BIBLIOTECA_PATH, [])
            historial = _leer(HISTORIAL_PATH, [])
            now = datetime.now().strftime("%Y-%m-%d %H:%M")

            ok_count = 0
            for r in resultados:
                if not r["ok"]:
                    self.after(0, lambda c=r["contacto"]: self._log(f"✗ Falló envío a {c}"))
                    continue
                ok_count += 1
                historial.append({
                    "video_id": r["video_id"],
                    "url": r["url"],
                    "label": r["label"],
                    "enviado_a": r["contacto"],
                    "fecha": now,
                })
                for v in bib:
                    if v["id"] == r["video_id"] and r["contacto"] in v.get("para", []):
                        v["para"].remove(r["contacto"])

            bib = [v for v in bib if v.get("para")]
            _guardar(BIBLIOTECA_PATH, bib)
            _guardar(HISTORIAL_PATH, historial)

            self.after(0, lambda: self._log(
                f"✅ {ok_count}/{len(resultados)} envíos exitosos. Sincronizando con GitHub..."
            ))
            ok_push, msg_push = git_push()
            self.after(0, lambda: self._log(
                f"Git push: {'✓ OK' if ok_push else '✗ Error — ' + msg_push}"
            ))
            self.after(0, self.refresh_all)
            self.after(0, lambda: self.btn_ejecutar.config(state="normal"))

        threading.Thread(
            target=bot.ejecutar_envios,
            args=(
                self._plan_actual,
                chrome_profile,
                chrome_profile_name,
                coord_profile,
                lambda m: self.after(0, lambda msg=m: self._log(msg)),
                on_done,
            ),
            daemon=True,
        ).start()

    # ══════════════════════════════════════════════════════════════════════════
    # HISTORIAL / CALENDARIO
    # ══════════════════════════════════════════════════════════════════════════
    def _build_historial(self):
        f = self.tab_historial
        now = datetime.now()
        self._cal_year = now.year
        self._cal_month = now.month

        # Barra de navegación
        nav = tk.Frame(f, bg=BG)
        nav.pack(fill="x", padx=14, pady=(12, 6))
        ttk.Button(nav, text="◀", style="Secondary.TButton",
                   command=self._prev_mes).pack(side="left")
        self.lbl_mes = tk.Label(nav, text="", bg=BG, fg=FG,
                                font=("Segoe UI", 11, "bold"))
        self.lbl_mes.pack(side="left", padx=12)
        ttk.Button(nav, text="▶", style="Secondary.TButton",
                   command=self._next_mes).pack(side="left")
        ttk.Button(nav, text="Hoy", style="Secondary.TButton",
                   command=self._ir_hoy).pack(side="left", padx=8)

        # Grid del calendario
        self.cal_frame = tk.Frame(f, bg=BG)
        self.cal_frame.pack(fill="both", expand=True, padx=14, pady=4)

        # Panel de detalle
        self.lbl_detalle = tk.Label(f, text="Haz click en un día para ver detalles",
                                    bg=BG2, fg=FG2, font=("Segoe UI", 9),
                                    anchor="w", padx=12, pady=6)
        self.lbl_detalle.pack(fill="x", padx=14, pady=(0, 10))

    def _refresh_historial(self):
        self._draw_calendar()

    def _prev_mes(self):
        if self._cal_month == 1:
            self._cal_month, self._cal_year = 12, self._cal_year - 1
        else:
            self._cal_month -= 1
        self._draw_calendar()

    def _next_mes(self):
        if self._cal_month == 12:
            self._cal_month, self._cal_year = 1, self._cal_year + 1
        else:
            self._cal_month += 1
        self._draw_calendar()

    def _ir_hoy(self):
        now = datetime.now()
        self._cal_year, self._cal_month = now.year, now.month
        self._draw_calendar()

    def _draw_calendar(self):
        for w in self.cal_frame.winfo_children():
            w.destroy()

        MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_mes.config(text=f"{MESES[self._cal_month - 1]} {self._cal_year}")

        # Cargar historial y agrupar por fecha
        historial = _leer(HISTORIAL_PATH, [])
        sends_by_date = {}
        for h in historial:
            fecha = h.get("fecha", "")[:10]
            if fecha:
                sends_by_date.setdefault(fecha, []).append(h.get("enviado_a", ""))

        # Cabecera días
        DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        for i, d in enumerate(DIAS):
            tk.Label(self.cal_frame, text=d, bg=BG, fg=FG2,
                     font=("Segoe UI", 8, "bold"), width=8).grid(
                row=0, column=i, padx=2, pady=(0, 4))

        hoy = datetime.now().strftime("%Y-%m-%d")
        weeks = cal_mod.monthcalendar(self._cal_year, self._cal_month)

        for week_i, week in enumerate(weeks):
            for day_i, day in enumerate(week):
                if day == 0:
                    tk.Frame(self.cal_frame, bg=BG, width=70, height=52).grid(
                        row=week_i + 1, column=day_i, padx=2, pady=2)
                    continue

                date_str = f"{self._cal_year}-{self._cal_month:02d}-{day:02d}"
                sends = sends_by_date.get(date_str, [])
                es_hoy = date_str == hoy

                if sends:
                    bg_c, fg_c = GREEN, "#0d1117"
                elif es_hoy:
                    bg_c, fg_c = ACCENT, "white"
                else:
                    bg_c, fg_c = BG3, FG2

                cell = tk.Frame(self.cal_frame, bg=bg_c, width=70, height=52,
                                cursor="hand2" if sends else "")
                cell.grid(row=week_i + 1, column=day_i, padx=2, pady=2, sticky="nsew")
                cell.grid_propagate(False)

                tk.Label(cell, text=str(day), bg=bg_c, fg=fg_c,
                         font=("Segoe UI", 10, "bold")).pack(pady=(6, 0))
                if sends:
                    n = len(sends)
                    tk.Label(cell, text=f"{n} envío{'s' if n > 1 else ''}",
                             bg=bg_c, fg=fg_c, font=("Segoe UI", 7)).pack()

                if sends:
                    for widget in [cell] + cell.winfo_children():
                        widget.bind("<Button-1>",
                                    lambda e, s=sends, d=date_str: self._mostrar_dia(d, s))

        for i in range(7):
            self.cal_frame.columnconfigure(i, weight=1)

    def _mostrar_dia(self, fecha, contactos):
        unicos = sorted(set(contactos))
        self.lbl_detalle.config(
            fg=FG,
            text=f"  {fecha}  —  Enviado a: {', '.join(unicos)}"
        )

    # ══════════════════════════════════════════════════════════════════════════
    # PERFILES DE COORDENADAS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_perfiles(self):
        f = self.tab_perfiles

        ttk.Label(f, text="Perfiles de coordenadas",
                  style="Header.TLabel").pack(pady=(14, 2), padx=14, anchor="w")
        ttk.Label(f, text="Cada perfil guarda las coordenadas de los botones para una PC específica.",
                  style="TLabel").pack(padx=14, anchor="w")

        self.lbl_activo = tk.Label(f, text="", bg=BG, fg=GREEN,
                                   font=("Segoe UI", 9, "bold"))
        self.lbl_activo.pack(padx=14, pady=(6, 2), anchor="w")

        list_frame = tk.Frame(f, bg=BG)
        list_frame.pack(fill="both", expand=True, padx=14, pady=4)

        self.lb_perfiles = tk.Listbox(list_frame, font=("Segoe UI", 11),
                                      bg=BG2, fg=FG, selectbackground=ACCENT,
                                      activestyle="none", relief="flat", height=10)
        self.lb_perfiles.pack(fill="both", expand=True)

        btn_frame = tk.Frame(f, bg=BG)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="➕  Nuevo",
                   command=self._nuevo_perfil).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🎯  Calibrar", style="Secondary.TButton",
                   command=self._calibrar_perfil).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="✓  Activar", style="Secondary.TButton",
                   command=self._activar_perfil).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="🗑  Eliminar", style="Secondary.TButton",
                   command=self._eliminar_perfil).pack(side="left", padx=6)

    def _refresh_perfiles(self):
        self.lb_perfiles.delete(0, "end")
        cfg = _leer_config()
        activo_id = cfg.get("active_coord_profile", "")
        perfiles = _leer(COORD_PROFILES_PATH, [])
        activo_nombre = ""
        for p in perfiles:
            marker = " ✓" if p["id"] == activo_id else ""
            self.lb_perfiles.insert("end", f"{p['name']}{marker}")
            if p["id"] == activo_id:
                activo_nombre = p["name"]
                self.lb_perfiles.itemconfig("end", fg=GREEN)
        if activo_nombre:
            self.lbl_activo.config(text=f"Activo: {activo_nombre}")
        else:
            self.lbl_activo.config(text="Sin perfil activo")

    def _nuevo_perfil(self):
        nombre = simpledialog.askstring("Nuevo perfil",
                                        "Nombre del perfil (ej: PC Casa, Laptop):", parent=self)
        if not nombre:
            return
        perfiles = _leer(COORD_PROFILES_PATH, [])
        nuevo = {
            "id": str(uuid.uuid4())[:8],
            "name": nombre.strip(),
            "coords": {k: [0, 0] for k in bot.COORD_KEYS},
        }
        perfiles.append(nuevo)
        _guardar(COORD_PROFILES_PATH, perfiles)
        self._refresh_perfiles()
        messagebox.showinfo("Perfil creado",
                            f"Perfil '{nombre}' creado.\nSelecciónalo y usa 🎯 Calibrar para configurar las coordenadas.")

    def _activar_perfil(self):
        sel = self.lb_perfiles.curselection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un perfil de la lista.")
            return
        perfiles = _leer(COORD_PROFILES_PATH, [])
        if sel[0] >= len(perfiles):
            return
        perfil = perfiles[sel[0]]
        cfg = _leer_config()
        cfg["active_coord_profile"] = perfil["id"]
        _guardar_config(cfg)
        self._refresh_perfiles()

    def _eliminar_perfil(self):
        sel = self.lb_perfiles.curselection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un perfil de la lista.")
            return
        perfiles = _leer(COORD_PROFILES_PATH, [])
        if sel[0] >= len(perfiles):
            return
        perfil = perfiles[sel[0]]
        if not messagebox.askyesno("Confirmar", f"¿Eliminar el perfil '{perfil['name']}'?"):
            return
        perfiles.pop(sel[0])
        _guardar(COORD_PROFILES_PATH, perfiles)
        cfg = _leer_config()
        if cfg.get("active_coord_profile") == perfil["id"]:
            cfg["active_coord_profile"] = ""
            _guardar_config(cfg)
        self._refresh_perfiles()

    def _calibrar_perfil(self):
        sel = self.lb_perfiles.curselection()
        if not sel:
            messagebox.showinfo("Selecciona", "Selecciona un perfil para calibrar.")
            return
        perfiles = _leer(COORD_PROFILES_PATH, [])
        if sel[0] >= len(perfiles):
            return
        perfil = perfiles[sel[0]]
        self._abrir_calibrador(perfil, perfiles)

    def _abrir_calibrador(self, perfil, perfiles):
        import pyautogui as pag

        win = tk.Toplevel(self)
        win.title(f"Calibrar — {perfil['name']}")
        win.geometry("420x300")
        win.configure(bg=BG)
        win.attributes("-topmost", True)
        win.resizable(False, False)

        state = {"step": 0, "coords": dict(perfil.get("coords", {}))}

        # Widgets
        lbl_paso = tk.Label(win, text="", bg=BG, fg=ACCENT,
                            font=("Segoe UI", 10, "bold"))
        lbl_paso.pack(pady=(16, 4), padx=20, anchor="w")

        lbl_instr = tk.Label(win, text="", bg=BG, fg=FG,
                             font=("Segoe UI", 9), justify="left", wraplength=380)
        lbl_instr.pack(padx=20, anchor="w")

        lbl_capturado = tk.Label(win, text="", bg=BG, fg=GREEN,
                                 font=("Segoe UI", 9))
        lbl_capturado.pack(pady=(8, 0))

        lbl_countdown = tk.Label(win, text="", bg=BG, fg=YELLOW,
                                 font=("Segoe UI", 20, "bold"))
        lbl_countdown.pack(pady=4)

        btn_cap = ttk.Button(win, text="🎯  Capturar en 3 seg")
        btn_cap.pack(pady=6)

        lbl_progress = tk.Label(win, text="", bg=BG, fg=FG2,
                                font=("Segoe UI", 8))
        lbl_progress.pack(pady=(0, 4))

        btn_guardar = ttk.Button(win, text="💾  Guardar y cerrar",
                                 state="disabled")
        btn_guardar.pack(pady=4)

        def mostrar_paso():
            step = state["step"]
            if step >= len(CALIB_STEPS):
                lbl_paso.config(text="✅ Calibración completa")
                lbl_instr.config(text="Todas las coordenadas capturadas.")
                btn_cap.config(state="disabled")
                btn_guardar.config(state="normal")
                lbl_progress.config(text="")
                return
            key, nombre, instruccion = CALIB_STEPS[step]
            lbl_paso.config(text=f"Paso {step + 1}/{len(CALIB_STEPS)}: {nombre}")
            lbl_instr.config(text=instruccion)
            lbl_progress.config(text=" → ".join(
                ("✓ " + CALIB_STEPS[i][1]) if i < step else CALIB_STEPS[i][1]
                for i in range(len(CALIB_STEPS))
            ))
            c = state["coords"].get(key, [0, 0])
            if c != [0, 0]:
                lbl_capturado.config(text=f"Actual: {c}")
            else:
                lbl_capturado.config(text="")

        def countdown(n):
            if n > 0:
                lbl_countdown.config(text=str(n))
                win.after(1000, lambda: countdown(n - 1))
            else:
                lbl_countdown.config(text="")
                key = CALIB_STEPS[state["step"]][0]
                x, y = pag.position()
                state["coords"][key] = [x, y]
                lbl_capturado.config(text=f"Capturado: ({x}, {y})")
                state["step"] += 1
                btn_cap.config(state="normal")
                win.after(600, mostrar_paso)

        def capturar():
            btn_cap.config(state="disabled")
            countdown(3)

        def guardar():
            for p in perfiles:
                if p["id"] == perfil["id"]:
                    p["coords"] = state["coords"]
                    break
            _guardar(COORD_PROFILES_PATH, perfiles)
            win.destroy()
            messagebox.showinfo("Guardado", f"Coordenadas de '{perfil['name']}' guardadas.")
            self._refresh_perfiles()

        btn_cap.config(command=capturar)
        btn_guardar.config(command=guardar)
        mostrar_paso()

    # ── Config dialog ─────────────────────────────────────────────────────────
    def _open_config(self):
        cfg = _leer_config()
        win = tk.Toplevel(self)
        win.title("Configuración")
        win.geometry("520x260")
        win.configure(bg=BG)
        win.grab_set()
        win.resizable(False, False)

        def lbl(text):
            tk.Label(win, text=text, bg=BG, fg=FG2,
                     font=("Segoe UI", 8)).pack(pady=(12, 2), padx=20, anchor="w")

        lbl("Ruta del perfil de Chrome (User Data folder)")
        tk.Label(win, text="Ej: C:\\Users\\TuNombre\\AppData\\Local\\Google\\Chrome\\User Data",
                 bg=BG, fg=FG2, font=("Segoe UI", 7)).pack(padx=20, anchor="w")
        e_profile = tk.Entry(win, width=60, font=("Segoe UI", 9),
                             bg=BG3, fg=FG, insertbackground=FG, relief="flat")
        e_profile.insert(0, cfg.get("chrome_profile", ""))
        e_profile.pack(padx=20, ipady=4, fill="x")

        lbl("Nombre del perfil (usualmente 'Default')")
        e_name = tk.Entry(win, width=60, font=("Segoe UI", 9),
                          bg=BG3, fg=FG, insertbackground=FG, relief="flat")
        e_name.insert(0, cfg.get("chrome_profile_name", "Default"))
        e_name.pack(padx=20, ipady=4, fill="x")

        def guardar():
            cfg["chrome_profile"] = e_profile.get().strip()
            cfg["chrome_profile_name"] = e_name.get().strip() or "Default"
            _guardar_config(cfg)
            win.destroy()
            messagebox.showinfo("Guardado", "Configuración guardada correctamente.")

        ttk.Button(win, text="Guardar", command=guardar).pack(pady=16)

    # ── Sync ──────────────────────────────────────────────────────────────────
    def _pull(self):
        self.sync_lbl.config(text="Sincronizando...", fg=YELLOW)
        self.update()
        ok, msg = git_pull()
        if ok:
            self.sync_lbl.config(text="✓ Actualizado", fg=GREEN)
            self.refresh_all()
        else:
            self.sync_lbl.config(text="✗ Error pull", fg=RED)
            messagebox.showerror("Git Pull", msg)

    def _push(self):
        self.sync_lbl.config(text="Subiendo...", fg=YELLOW)
        self.update()
        ok, msg = git_push()
        self.sync_lbl.config(
            text="✓ Push OK" if ok else "✗ Error push",
            fg=GREEN if ok else RED
        )
        if not ok:
            messagebox.showerror("Git Push", msg)

    # ── Refresh all ───────────────────────────────────────────────────────────
    def refresh_all(self):
        self._refresh_dashboard()
        self._refresh_biblioteca()
        self._refresh_contactos()
        self._refresh_perfiles()
        self._refresh_historial()


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
