import tkinter as tk
from tkinter import ttk
import math
import random

# ==============================================================================
# UNIVERSIDAD AUTÓNOMA DE NUEVO LEÓN (UANL)
# FACULTAD DE INGENIERÍA MECÁNICA Y ELÉCTRICA (FIME)
# Química General - Producto Integrador de Aprendizaje (PIA)
# Protocolo: Baterías de Flujo Redox Orgánico (Quinonas / Derivados de Lignina)
#
# Equipo: 07 | Grupo: 051 | Docente: Dra. Laura Imelda García Ortiz
# Integrantes:
#   - Sebastián García Rodríguez (2326689)
#   - Héctor Daniel Aranda Facundo (2161992)
#   - Mayela Monserrat Arteaga Ríos (2233999)
#   - Luis Eduardo Hernández de los Santos (2229603)
#   - Ulises Rodríguez Quintero (2247060)
#   - David Anton García Arellano (2326489)
# ==============================================================================


class SimuladorBateriaRedoxOrg:
    """
    Simulador interactivo en Tkinter de una Batería de Flujo Redox Orgánico.
    Incluye:
      1. Diagrama animado del Stack (RFcell), Colectores de Grafito, Electrodos
         de Fieltro de Carbono y Membrana de Intercambio Iónico (flujo de H+).
      2. Conector de Corriente y Convertidor Bidireccional (PMS) + Supervisor (BMS).
      3. Tanque Catolito (+) y Tanque Anolito (-) con nivel de líquido ajustable
         (20 L a 200 L), cambio de color según Estado de Carga (SoC) y degradación
         progresiva (oscurecimiento y partículas por descomposición molecular).
      4. Bombas hidráulicas con rotación animada y flujo de electrolito en tuberías.
      5. Gráficas en tiempo real de Voltaje (V) vs Tiempo y Retención de Capacidad
         (%) durante la prueba experimental de 50 ciclos del protocolo.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(
            "Simulador de Batería de Flujo Redox Orgánico | UANL FIME - Equipo 07"
        )
        self.root.geometry("1320x820")
        self.root.minsize(1100, 700)
        self.root.configure(bg="#080d1a")

        # ----------------------------------------------------------------------
        # 1. VARIABLES DE ESTADO ELECTROQUÍMICO INTERNO
        # ----------------------------------------------------------------------
        self.mode = "IDLE"            # "IDLE", "CHARGE", "DISCHARGE", "AUTOCYCLE"
        self.auto_dir = 1             # 1 = Cargando, -1 = Descargando en Auto-Ciclado
        self.soc = 50.0               # Estado de Carga (%)
        self.voltage = 1.214          # Voltaje en terminales de la celda (V)
        self.v_nernst = 1.214         # Potencial de equilibrio de Nernst (V)
        self.v_deg_loss = 0.0         # Caída de voltaje por degradación (V)
        self.v_overpot = 0.0          # Sobrepotencial óhmico / polarización (V)
        self.deg_cat = 0.0            # Degradación acumulada en Catolito (+) (%)
        self.deg_ano = 0.0            # Degradación acumulada en Anolito (-) (%)
        self.cycles = 0               # Ciclos completados
        self.target_cycles = 50       # Meta de 50 ciclos del protocolo experimental
        self.pump_angle = 0.0         # Ángulo de rotación de las bombas (grados)
        self.anim_phase = 0.0         # Fase de animación para partículas (0.0 a 1.0)

        # ----------------------------------------------------------------------
        # 2. VARIABLES VINCULADAS A CONTROLES DEL USUARIO
        # ----------------------------------------------------------------------
        # Capacidades totales de líquido de cada tanque (Litros escritos en recuadro)
        self.vol_catolito = tk.DoubleVar(value=120.0)
        self.vol_anolito = tk.DoubleVar(value=120.0)
        self.str_vol_cat = tk.StringVar(value="120")
        self.str_vol_ano = tk.StringVar(value="120")
        self.conc_molar = tk.DoubleVar(value=1.5)

        # Parámetros eléctricos, hidráulicos y de envejecimiento
        self.current_amp = tk.DoubleVar(value=2.5)   # Corriente en el conector (A)
        self.flow_rate = tk.DoubleVar(value=60.0)    # Caudal de las bombas (mL/min)
        self.deg_factor = tk.DoubleVar(value=5.0)    # Multiplicador de degradación
        self.sim_speed = tk.DoubleVar(value=4.0)     # Velocidad de simulación

        # Historiales para las 2 gráficas científicas inferiores
        self.max_time_pts = 110
        self.time_history = [
            {"v": 1.214, "soc": 50.0} for _ in range(30)
        ]
        # Historial por ciclo: (ciclo, retencion_capacidad_%, eficiencia_energetica_%)
        self.cycle_history = [(0, 100.0, 84.2)]

        # Semillas de partículas de precipitado/turbidez dentro de los tanques
        random.seed(7)
        self.precip_seeds = [
            (random.uniform(0.08, 0.92), random.uniform(0.10, 0.90), random.uniform(2.0, 4.0))
            for _ in range(35)
        ]

        # Construir interfaz gráfica y arrancar bucle de simulación
        self._construir_interfaz()
        self._actualizar_bucle()

    # ==========================================================================
    # CONSTRUCCIÓN DE LA INTERFAZ GRÁFICA (TKINTER)
    # ==========================================================================
    def _construir_interfaz(self):
        # Barra Superior (Encabezado UANL - FIME)
        header = tk.Frame(self.root, bg="#0f172a", padx=14, pady=8)
        header.pack(fill=tk.X, side=tk.TOP)

        badge = tk.Label(
            header,
            text=" UANL • FIME • PIA QUÍMICA GENERAL ",
            bg="#065f46",
            fg="#6ee7b7",
            font=("Segoe UI", 9, "bold"),
            padx=6,
            pady=2,
        )
        badge.pack(side=tk.LEFT, padx=(0, 10))

        title_lbl = tk.Label(
            header,
            text="Simulador de Batería de Flujo Redox Orgánico (Quinonas / Lignina) — Equipo 07",
            bg="#0f172a",
            fg="#f8fafc",
            font=("Segoe UI", 13, "bold"),
        )
        title_lbl.pack(side=tk.LEFT)

        sub_lbl = tk.Label(
            header,
            text="Grupo 051 • Dra. Laura Imelda García Ortiz",
            bg="#0f172a",
            fg="#94a3b8",
            font=("Consolas", 9),
        )
        sub_lbl.pack(side=tk.RIGHT)

        # Cinta Superior de Indicadores Rápidos (KPIs en vivo)
        kpi_bar = tk.Frame(self.root, bg="#080d1a", padx=12, pady=6)
        kpi_bar.pack(fill=tk.X, side=tk.TOP)

        self.kpi_mode = self._crear_tarjeta_kpi(
            kpi_bar, "MODO DEL SISTEMA", "EN ESPERA (STANDBY)", "Bombas: APAGADAS", "#38bdf8"
        )
        self.kpi_volt = self._crear_tarjeta_kpi(
            kpi_bar, "VOLTAJE CELDA (RFcell)", "1.214 V", "Potencial Nernst: 1.214 V", "#22d3ee"
        )
        self.kpi_soc = self._crear_tarjeta_kpi(
            kpi_bar, "ESTADO DE CARGA (SoC)", "50.0 %", "Corriente: 0.00 A", "#34d399"
        )
        self.kpi_deg_cat = self._crear_tarjeta_kpi(
            kpi_bar, "DEGRADACIÓN CATOLITO (+)", "0.00 %", "Pureza Lignina/Q: 100.0%", "#fbbf24"
        )
        self.kpi_deg_ano = self._crear_tarjeta_kpi(
            kpi_bar, "DEGRADACIÓN ANOLITO (-)", "0.00 %", "Pureza AQDS: 100.0%", "#c084fc"
        )
        self.kpi_cycles = self._crear_tarjeta_kpi(
            kpi_bar, "CICLADO (META 50 CICLOS)", "Ciclo 0 / 50", "Retención Cap.: 100.0%", "#2dd4bf"
        )

        # Contenedor Central (Izquierda: Lienzo Esquemático + Gráficas | Derecha: Controles)
        workspace = tk.Frame(self.root, bg="#080d1a", padx=12, pady=4)
        workspace.pack(fill=tk.BOTH, expand=True)

        # Lienzo (Canvas) principal a la izquierda
        canvas_container = tk.Frame(
            workspace, bg="#0f172a", bd=1, relief=tk.SOLID, padx=2, pady=2
        )
        canvas_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.canvas = tk.Canvas(
            canvas_container,
            bg="#070b16",
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Panel de Control a la derecha (con barra de desplazamiento por si la pantalla es pequeña)
        right_outer = tk.Frame(workspace, bg="#0f172a", width=395, bd=1, relief=tk.SOLID)
        right_outer.pack(side=tk.RIGHT, fill=tk.Y)
        right_outer.pack_propagate(False)

        self.ctrl_canvas = tk.Canvas(
            right_outer, bg="#0f172a", highlightthickness=0, width=375
        )
        scrollbar = ttk.Scrollbar(
            right_outer, orient="vertical", command=self.ctrl_canvas.yview
        )
        self.panel = tk.Frame(self.ctrl_canvas, bg="#0f172a", padx=12, pady=10)

        self.panel.bind(
            "<Configure>",
            lambda e: self.ctrl_canvas.configure(scrollregion=self.ctrl_canvas.bbox("all")),
        )
        self.ctrl_canvas.create_window((0, 0), window=self.panel, anchor="nw", width=373)
        self.ctrl_canvas.configure(yscrollcommand=scrollbar.set)

        self.ctrl_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ======================================================================
        # SECCIÓN 1 DEL PANEL: CAPACIDAD DE LÍQUIDO (CATOLITO Y ANOLITO)
        # ======================================================================
        cap_frame = tk.LabelFrame(
            self.panel,
            text=" 💧 CAPACIDAD DE LÍQUIDO: CATOLITO Y ANOLITO ",
            bg="#131c31",
            fg="#38bdf8",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID,
        )
        cap_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            cap_frame,
            text="Escribe la cantidad total de líquido (L) para cada tanque:",
            bg="#131c31",
            fg="#94a3b8",
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(0, 6))

        # Recuadro para escribir la cantidad total de Tanque Catolito (+)
        row_cat = tk.Frame(cap_frame, bg="#090d16", padx=8, pady=6, bd=1, relief=tk.SOLID)
        row_cat.pack(fill=tk.X, pady=(0, 6))

        top_cat = tk.Frame(row_cat, bg="#090d16")
        top_cat.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            top_cat,
            text="Cantidad Total Catolito (+):",
            bg="#090d16",
            fg="#fbbf24",
            font=("Segoe UI", 8, "bold"),
        ).pack(side=tk.LEFT)
        self.lbl_vol_cat_val = tk.Label(
            top_cat,
            text="120.0 L (60% Nivel)",
            bg="#090d16",
            fg="#fef08a",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_vol_cat_val.pack(side=tk.RIGHT)

        input_cat_row = tk.Frame(row_cat, bg="#090d16")
        input_cat_row.pack(fill=tk.X)
        self.entry_vol_cat = tk.Entry(
            input_cat_row,
            textvariable=self.str_vol_cat,
            bg="#1e293b",
            fg="#fef08a",
            insertbackground="#fef08a",
            font=("Consolas", 11, "bold"),
            justify=tk.RIGHT,
            bd=1,
            relief=tk.SOLID,
        )
        self.entry_vol_cat.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.entry_vol_cat.bind("<KeyRelease>", self.aplicar_capacidades_escritas)
        self.entry_vol_cat.bind("<Return>", self.aplicar_capacidades_escritas)
        tk.Label(
            input_cat_row,
            text=" Litros (L)",
            bg="#090d16",
            fg="#cbd5e1",
            font=("Consolas", 9, "bold"),
        ).pack(side=tk.RIGHT, padx=(6, 0))

        # Recuadro para escribir la cantidad total de Tanque Anolito (-)
        row_ano = tk.Frame(cap_frame, bg="#090d16", padx=8, pady=6, bd=1, relief=tk.SOLID)
        row_ano.pack(fill=tk.X, pady=(0, 6))

        top_ano = tk.Frame(row_ano, bg="#090d16")
        top_ano.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            top_ano,
            text="Cantidad Total Anolito (-):",
            bg="#090d16",
            fg="#c084fc",
            font=("Segoe UI", 8, "bold"),
        ).pack(side=tk.LEFT)
        self.lbl_vol_ano_val = tk.Label(
            top_ano,
            text="120.0 L (60% Nivel)",
            bg="#090d16",
            fg="#e9d5ff",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_vol_ano_val.pack(side=tk.RIGHT)

        input_ano_row = tk.Frame(row_ano, bg="#090d16")
        input_ano_row.pack(fill=tk.X)
        self.entry_vol_ano = tk.Entry(
            input_ano_row,
            textvariable=self.str_vol_ano,
            bg="#1e293b",
            fg="#e9d5ff",
            insertbackground="#e9d5ff",
            font=("Consolas", 11, "bold"),
            justify=tk.RIGHT,
            bd=1,
            relief=tk.SOLID,
        )
        self.entry_vol_ano.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.entry_vol_ano.bind("<KeyRelease>", self.aplicar_capacidades_escritas)
        self.entry_vol_ano.bind("<Return>", self.aplicar_capacidades_escritas)
        tk.Label(
            input_ano_row,
            text=" Litros (L)",
            bg="#090d16",
            fg="#cbd5e1",
            font=("Consolas", 9, "bold"),
        ).pack(side=tk.RIGHT, padx=(6, 0))

        # Botón para confirmar/aplicar manualmente y validar
        tk.Button(
            cap_frame,
            text="✔ Aplicar Cantidades Totales Escritas",
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            pady=4,
            cursor="hand2",
            command=self.confirmar_capacidades_boton,
        ).pack(fill=tk.X, pady=(0, 6))

        # Slider Concentración Molar Activa (mol/L)
        top_conc = tk.Frame(cap_frame, bg="#131c31")
        top_conc.pack(fill=tk.X)
        tk.Label(
            top_conc,
            text="Concentración Activa (C):",
            bg="#131c31",
            fg="#cbd5e1",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT)
        self.lbl_conc_val = tk.Label(
            top_conc,
            text="1.50 mol/L",
            bg="#131c31",
            fg="#38bdf8",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_conc_val.pack(side=tk.RIGHT)

        tk.Scale(
            cap_frame,
            variable=self.conc_molar,
            from_=0.5,
            to=2.5,
            resolution=0.1,
            orient=tk.HORIZONTAL,
            showvalue=False,
            bg="#131c31",
            troughcolor="#090d16",
            activebackground="#38bdf8",
            highlightthickness=0,
        ).pack(fill=tk.X, pady=(2, 6))

        # Resumen de Capacidad Energética y Botón Igualar Tanques
        cap_summary = tk.Frame(cap_frame, bg="#090d16", padx=8, pady=6)
        cap_summary.pack(fill=tk.X, pady=(2, 4))

        self.lbl_energy_wh = tk.Label(
            cap_summary,
            text="Capacidad Total: 5,980 Wh",
            bg="#090d16",
            fg="#34d399",
            font=("Consolas", 8, "bold"),
        )
        self.lbl_energy_wh.pack(anchor="w")

        self.lbl_limiting_tank = tk.Label(
            cap_summary,
            text="Balance Hidráulico: Balanceado (120 L)",
            bg="#090d16",
            fg="#38bdf8",
            font=("Consolas", 8),
        )
        self.lbl_limiting_tank.pack(anchor="w")

        tk.Button(
            cap_frame,
            text="⚖ Igualar Capacidad de Ambos Tanques (120 L)",
            bg="#1e293b",
            fg="#38bdf8",
            activebackground="#334155",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            pady=4,
            cursor="hand2",
            command=self.igualar_tanques,
        ).pack(fill=tk.X, pady=(4, 0))

        # ======================================================================
        # SECCIÓN 2 DEL PANEL: CONECTOR DE CORRIENTE Y MODOS DE OPERACIÓN
        # ======================================================================
        mode_frame = tk.LabelFrame(
            self.panel,
            text=" ⚡ CONECTOR DE CORRIENTE Y BOMBAS ",
            bg="#131c31",
            fg="#34d399",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID,
        )
        mode_frame.pack(fill=tk.X, pady=(0, 10))

        btn_style = {
            "font": ("Segoe UI", 9, "bold"),
            "bd": 0,
            "pady": 6,
            "cursor": "hand2",
        }

        self.btn_charge = tk.Button(
            mode_frame,
            text="⚡ MODO CARGA (Conectar Fuente DC a Batería)",
            bg="#059669",
            fg="white",
            activebackground="#10b981",
            command=lambda: self.cambiar_modo("CHARGE"),
            **btn_style,
        )
        self.btn_charge.pack(fill=tk.X, pady=2)

        self.btn_discharge = tk.Button(
            mode_frame,
            text="💡 MODO DESCARGA (Entregar Energía a Carga)",
            bg="#d97706",
            fg="white",
            activebackground="#f59e0b",
            command=lambda: self.cambiar_modo("DISCHARGE"),
            **btn_style,
        )
        self.btn_discharge.pack(fill=tk.X, pady=2)

        self.btn_autocycle = tk.Button(
            mode_frame,
            text="🔄 AUTO-CICLADO (Prueba Experimental 50 Ciclos)",
            bg="#0284c7",
            fg="white",
            activebackground="#38bdf8",
            command=lambda: self.cambiar_modo("AUTOCYCLE"),
            **btn_style,
        )
        self.btn_autocycle.pack(fill=tk.X, pady=2)

        row_actions = tk.Frame(mode_frame, bg="#131c31")
        row_actions.pack(fill=tk.X, pady=(4, 0))

        tk.Button(
            row_actions,
            text="⏸ Pausar / Apagar",
            bg="#334155",
            fg="#e2e8f0",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            pady=5,
            cursor="hand2",
            command=lambda: self.cambiar_modo("IDLE"),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        tk.Button(
            row_actions,
            text="🧪 Regenerar Líquidos",
            bg="#881337",
            fg="#fecdd3",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.regenerar_electrolitos,
        ).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(3, 0))

        # ======================================================================
        # SECCIÓN 3 DEL PANEL: PARÁMETROS OPERATIVOS Y DEGRADACIÓN
        # ======================================================================
        param_frame = tk.LabelFrame(
            self.panel,
            text=" 🎛 PARÁMETROS ELECTROQUÍMICOS Y BOMBAS ",
            bg="#131c31",
            fg="#fbbf24",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID,
        )
        param_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_curr_val = self._crear_control_slider(
            param_frame,
            "Corriente del Conector (I):",
            self.current_amp,
            0.5,
            5.0,
            0.25,
            "2.50 A (50 mA/cm²)",
            "#34d399",
        )
        self.lbl_flow_val = self._crear_control_slider(
            param_frame,
            "Caudal Bombas Hidráulicas (Q):",
            self.flow_rate,
            20.0,
            120.0,
            5.0,
            "60 mL/min",
            "#22d3ee",
        )
        self.lbl_deg_val = self._crear_control_slider(
            param_frame,
            "Factor Degradación de Líquidos:",
            self.deg_factor,
            1.0,
            30.0,
            1.0,
            "5x (Visible)",
            "#fbbf24",
        )
        self.lbl_spd_val = self._crear_control_slider(
            param_frame,
            "Velocidad de Simulación:",
            self.sim_speed,
            1.0,
            25.0,
            1.0,
            "4x",
            "#c084fc",
        )

        tk.Button(
            param_frame,
            text="+ Simular Pico de Desgaste Químico (Catolito y Anolito)",
            bg="#451a03",
            fg="#fcd34d",
            activebackground="#78350f",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            bd=0,
            pady=5,
            cursor="hand2",
            command=self.simular_pico_desgaste,
        ).pack(fill=tk.X, pady=(6, 0))

        # ======================================================================
        # SECCIÓN 4 DEL PANEL: DIAGNÓSTICO DE COLORIMETRÍA Y BMS
        # ======================================================================
        diag_frame = tk.LabelFrame(
            self.panel,
            text=" 🔬 COLORIMETRÍA Y TELEMETRÍA BMS ",
            bg="#131c31",
            fg="#a7f3d0",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8,
            bd=1,
            relief=tk.SOLID,
        )
        diag_frame.pack(fill=tk.X)

        swatch_row = tk.Frame(diag_frame, bg="#131c31")
        swatch_row.pack(fill=tk.X, pady=(0, 6))

        # Muestra de color Catolito (+)
        cat_box = tk.Frame(swatch_row, bg="#090d16", padx=6, pady=5)
        cat_box.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        self.swatch_cat = tk.Frame(cat_box, bg="#d97706", width=22, height=22, bd=1, relief=tk.SOLID)
        self.swatch_cat.pack(side=tk.LEFT, padx=(0, 6))
        self.lbl_swatch_cat = tk.Label(
            cat_box,
            text="Catolito (+)\nLimpio",
            bg="#090d16",
            fg="#e2e8f0",
            font=("Consolas", 7),
            justify=tk.LEFT,
        )
        self.lbl_swatch_cat.pack(side=tk.LEFT)

        # Muestra de color Anolito (-)
        ano_box = tk.Frame(swatch_row, bg="#090d16", padx=6, pady=5)
        ano_box.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(3, 0))
        self.swatch_ano = tk.Frame(ano_box, bg="#7c3aed", width=22, height=22, bd=1, relief=tk.SOLID)
        self.swatch_ano.pack(side=tk.LEFT, padx=(0, 6))
        self.lbl_swatch_ano = tk.Label(
            ano_box,
            text="Anolito (-)\nLimpio",
            bg="#090d16",
            fg="#e2e8f0",
            font=("Consolas", 7),
            justify=tk.LEFT,
        )
        self.lbl_swatch_ano.pack(side=tk.LEFT)

        # Tabla de parámetros electroquímicos internos
        self.lbl_diag_table = tk.Label(
            diag_frame,
            text="",
            bg="#090d16",
            fg="#cbd5e1",
            font=("Consolas", 8),
            justify=tk.LEFT,
             anchor="w",
            padx=8,
            pady=6,
        )
        self.lbl_diag_table.pack(fill=tk.X, pady=(0, 6))

        # Mensaje dinámico del BMS Supervisor
        self.lbl_bms_msg = tk.Label(
            diag_frame,
            text="BMS Supervisor: Sistema en espera. Selecciona Modo Carga o Descarga.",
            bg="#064e3b",
            fg="#a7f3d0",
            font=("Segoe UI", 8),
            wraplength=325,
            justify=tk.LEFT,
            padx=8,
            pady=6,
        )
        self.lbl_bms_msg.pack(fill=tk.X)

    def _crear_tarjeta_kpi(self, parent, titulo, valor_ini, sub_ini, color_acento):
        card = tk.Frame(
            parent, bg="#0f172a", bd=1, relief=tk.SOLID, padx=8, pady=5
        )
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=3)

        tk.Label(
            card,
            text=titulo,
            bg="#0f172a",
            fg="#94a3b8",
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w")

        lbl_val = tk.Label(
            card,
            text=valor_ini,
            bg="#0f172a",
            fg=color_acento,
            font=("Consolas", 12, "bold"),
        )
        lbl_val.pack(anchor="w", pady=(1, 1))

        lbl_sub = tk.Label(
            card,
            text=sub_ini,
            bg="#0f172a",
            fg="#cbd5e1",
            font=("Consolas", 7),
        )
        lbl_sub.pack(anchor="w")
        return {"val": lbl_val, "sub": lbl_sub}

    def _crear_control_slider(
        self, parent, texto, variable, minimo, maximo, paso, val_inicial, color_val
    ):
        top = tk.Frame(parent, bg="#131c31")
        top.pack(fill=tk.X, pady=(2, 0))
        tk.Label(
            top, text=texto, bg="#131c31", fg="#cbd5e1", font=("Segoe UI", 8)
        ).pack(side=tk.LEFT)
        lbl_val = tk.Label(
            top,
            text=val_inicial,
            bg="#131c31",
            fg=color_val,
            font=("Consolas", 8, "bold"),
        )
        lbl_val.pack(side=tk.RIGHT)

        tk.Scale(
            parent,
            variable=variable,
            from_=minimo,
            to=maximo,
            resolution=paso,
            orient=tk.HORIZONTAL,
            showvalue=False,
            bg="#131c31",
            troughcolor="#090d16",
            activebackground=color_val,
            highlightthickness=0,
        ).pack(fill=tk.X, pady=(0, 4))
        return lbl_val

    # ==========================================================================
    # ACCIONES Y EVENTOS DEL USUARIO
    # ==========================================================================
    def aplicar_capacidades_escritas(self, event=None):
        """
        Lee en tiempo real los valores numéricos escritos por el usuario en los
        recuadros de texto de Catolito (+) y Anolito (-).
        """
        try:
            val_c = float(self.str_vol_cat.get().strip())
            if val_c > 0:
                self.vol_catolito.set(max(1.0, min(5000.0, val_c)))
        except ValueError:
            pass

        try:
            val_a = float(self.str_vol_ano.get().strip())
            if val_a > 0:
                self.vol_anolito.set(max(1.0, min(5000.0, val_a)))
        except ValueError:
            pass

    def confirmar_capacidades_boton(self):
        self.aplicar_capacidades_escritas()
        v_cat = self.vol_catolito.get()
        v_ano = self.vol_anolito.get()
        self.str_vol_cat.set(f"{v_cat:g}")
        self.str_vol_ano.set(f"{v_ano:g}")
        self.lbl_bms_msg.config(
            text=f"BMS Supervisor: Capacidad actualizada a {v_cat:g} L en Catolito (+) y {v_ano:g} L en Anolito (-)."
        )

    def cambiar_modo(self, nuevo_modo: str):
        self.mode = nuevo_modo
        if nuevo_modo == "AUTOCYCLE":
            self.auto_dir = 1 if self.soc < 92.0 else -1

    def igualar_tanques(self):
        self.vol_catolito.set(120.0)
        self.vol_anolito.set(120.0)
        self.str_vol_cat.set("120")
        self.str_vol_ano.set("120")
        self.lbl_bms_msg.config(
            text="BMS Supervisor: Capacidad de líquido igualada a 120 L (60% de nivel) en los tanques de Catolito y Anolito."
        )

    def regenerar_electrolitos(self):
        self.mode = "IDLE"
        self.soc = 50.0
        self.deg_cat = 0.0
        self.deg_ano = 0.0
        self.cycles = 0
        self.cycle_history = [(0, 100.0, 84.2)]
        self.lbl_bms_msg.config(
            text="BMS Supervisor: Electrolitos de Catolito (+) y Anolito (-) purificados y regenerados al 100% de pureza inicial."
        )

    def simular_pico_desgaste(self):
        self.deg_cat = min(60.0, self.deg_cat + 4.5)
        self.deg_ano = min(60.0, self.deg_ano + 4.0)
        retencion = max(20.0, 100.0 - (self.deg_cat + self.deg_ano) * 0.85)
        eficiencia = max(52.0, 84.5 - (self.deg_cat + self.deg_ano) * 0.32)
        self.cycles = min(50, self.cycles + 2)
        self.cycle_history.append((self.cycles, retencion, eficiencia))
        self.lbl_bms_msg.config(
            text="Alerta BMS: Se simuló estrés oxidativo. Observa el oscurecimiento del líquido en los tanques de Catolito y Anolito y la caída en el voltaje."
        )

    # ==========================================================================
    # MODELO ELECTROQUÍMICO Y COLORIMÉTRICO
    # ==========================================================================
    def _obtener_modo_activo(self) -> str:
        if self.mode == "AUTOCYCLE":
            return "CHARGE" if self.auto_dir == 1 else "DISCHARGE"
        return self.mode

    @staticmethod
    def _mezclar_rgb(rgb1, rgb2, t: float):
        t = max(0.0, min(1.0, t))
        return (
            int(rgb1[0] + (rgb2[0] - rgb1[0]) * t),
            int(rgb1[1] + (rgb2[1] - rgb1[1]) * t),
            int(rgb1[2] + (rgb2[2] - rgb1[2]) * t),
        )

    @staticmethod
    def _rgb_a_hex(rgb) -> str:
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def _calcular_colores_electrolitos(self):
        """
        Calcula el color hexadecimal del Catolito (+) y del Anolito (-)
        en función tanto del Estado de Carga (SoC %) como del porcentaje
        de degradación molecular (oscurecimiento por descomposición).
        """
        s = self.soc / 100.0

        # CATOLITO (+): Derivado de Lignina / Par Quinona (Q) - Hidroquinona (QH2)
        # Descargado (0% SoC): Ámbar claro (245, 190, 65)
        # Cargado (100% SoC): Naranja-Rojizo intenso (215, 55, 25)
        # Degradado: Marrón oscuro turbio (48, 30, 18)
        cat_limpio = self._mezclar_rgb((245, 190, 65), (215, 55, 25), s)
        cat_final = self._mezclar_rgb(cat_limpio, (48, 30, 18), min(0.88, self.deg_cat / 45.0))

        # ANOLITO (-): Antraquinona-2,7-disulfonato (AQDS / AQDSH2)
        # Descargado (0% SoC): Violeta profundo (125, 55, 220)
        # Cargado (100% SoC): Verde esmeralda intenso (16, 195, 125)
        # Degradado: Gris oliva oscuro (45, 52, 44)
        ano_limpio = self._mezclar_rgb((125, 55, 220), (16, 195, 125), s)
        ano_final = self._mezclar_rgb(ano_limpio, (45, 52, 44), min(0.88, self.deg_ano / 45.0))

        return self._rgb_a_hex(cat_final), self._rgb_a_hex(ano_final)

    def _paso_fisicoquimico(self):
        dt = 0.04 * self.sim_speed.get()
        corriente = self.current_amp.get()
        caudal = self.flow_rate.get()
        mult_deg = self.deg_factor.get()
        v_cat = self.vol_catolito.get()
        v_ano = self.vol_anolito.get()
        conc = self.conc_molar.get()

        modo_activo = self._obtener_modo_activo()
        deg_total = self.deg_cat + self.deg_ano
        retencion_cap = max(20.0, 100.0 - deg_total * 0.85)

        # El tanque con menor volumen actúa como reactivo limitante
        vol_limitante = min(v_cat, v_ano)
        escala_volumen = (120.0 / max(20.0, vol_limitante)) * (1.5 / conc)

        if modo_activo in ("CHARGE", "DISCHARGE"):
            # Girar impulsores de las bombas y mover electrones/protones/fluido
            self.pump_angle = (self.pump_angle + 14.0 * (caudal / 60.0)) % 360.0
            self.anim_phase = (self.anim_phase + 0.045 * math.sqrt(self.sim_speed.get())) % 1.0

            # Variación del Estado de Carga (SoC)
            delta_soc = (corriente * 0.45 * dt) * (100.0 / retencion_cap) * escala_volumen

            # Tasa de degradación en carga y descarga (menor volumen cicla más rápido)
            estres_vol_cat = (120.0 / max(30.0, v_cat)) ** 0.35
            estres_vol_ano = (120.0 / max(30.0, v_ano)) ** 0.35
            tasa_deg_base = 0.005 * mult_deg * (corriente / 2.5) * dt

            if modo_activo == "CHARGE":
                self.soc = min(100.0, self.soc + delta_soc)
                estres_alto_soc = 1.65 if self.soc > 82.0 else 1.0
                self.deg_cat = min(
                    60.0, self.deg_cat + tasa_deg_base * 1.18 * estres_alto_soc * estres_vol_cat
                )
                self.deg_ano = min(
                    60.0, self.deg_ano + tasa_deg_base * 0.92 * estres_vol_ano
                )

                if self.soc >= 99.4:
                    if self.mode == "AUTOCYCLE":
                        self.auto_dir = -1
                    else:
                        self.mode = "IDLE"
                        self.lbl_bms_msg.config(
                            text="BMS Supervisor: Batería cargada al 100%. Bombas detenidas automáticamente."
                        )

            elif modo_activo == "DISCHARGE":
                self.soc = max(0.0, self.soc - delta_soc)
                estres_bajo_soc = 1.55 if self.soc < 18.0 else 1.0
                self.deg_cat = min(
                    60.0, self.deg_cat + tasa_deg_base * 0.94 * estres_vol_cat
                )
                self.deg_ano = min(
                    60.0, self.deg_ano + tasa_deg_base * 1.22 * estres_bajo_soc * estres_vol_ano
                )

                if self.soc <= 0.8:
                    if self.mode == "AUTOCYCLE":
                        self.cycles += 1
                        nueva_ret = max(20.0, 100.0 - (self.deg_cat + self.deg_ano) * 0.85)
                        nueva_eff = max(
                            52.0,
                            84.5 - (self.deg_cat + self.deg_ano) * 0.32 - (corriente - 2.0) * 1.4,
                        )
                        self.cycle_history.append((self.cycles, nueva_ret, nueva_eff))

                        if self.cycles >= self.target_cycles:
                            self.mode = "IDLE"
                            self.lbl_bms_msg.config(
                                text="BMS Supervisor: Prueba experimental de 50 ciclos finalizada. Revisa la gráfica inferior derecha."
                            )
                        else:
                            self.auto_dir = 1
                    else:
                        self.mode = "IDLE"
                        self.lbl_bms_msg.config(
                            text="BMS Supervisor: Descarga completada (SoC agotado). Activa Modo Carga para recargar los tanques."
                        )

        # Ecuación de Nernst + Sobrepotencial + Caída de Voltaje por Degradación
        s_clamped = max(0.015, min(0.985, self.soc / 100.0))
        self.v_nernst = 1.24 + 0.052 * math.log(s_clamped / (1.0 - s_clamped))
        self.v_deg_loss = ((self.deg_cat + self.deg_ano) / 100.0) * 0.31

        factor_flujo = max(0.3, caudal / 60.0)
        r_interna = (0.028 / (factor_flujo ** 0.35)) + ((self.deg_cat + self.deg_ano) / 100.0) * 0.045

        if modo_activo == "CHARGE":
            self.v_overpot = +corriente * r_interna
            self.voltage = min(1.62, self.v_nernst + self.v_overpot - self.v_deg_loss * 0.35)
        elif modo_activo == "DISCHARGE":
            self.v_overpot = -corriente * r_interna
            self.voltage = max(0.62, self.v_nernst + self.v_overpot - self.v_deg_loss)
        else:
            self.v_overpot = 0.0
            self.voltage = max(0.72, self.v_nernst - self.v_deg_loss * 0.65)

        # Guardar punto en el historial de tiempo real
        if modo_activo != "IDLE" or random.random() < 0.2:
            self.time_history.append({"v": self.voltage, "soc": self.soc})
            if len(self.time_history) > self.max_time_pts:
                self.time_history.pop(0)

    # ==========================================================================
    # ACTUALIZACIÓN DE INDICADORES EN PANEL Y TARJETAS KPI
    # ==========================================================================
    def _actualizar_etiquetas_ui(self):
        modo_activo = self._obtener_modo_activo()
        hex_cat, hex_ano = self._calcular_colores_electrolitos()

        v_cat = self.vol_catolito.get()
        v_ano = self.vol_anolito.get()
        cap_max_ref = max(200.0, v_cat, v_ano)
        pct_cat = int(round((v_cat / cap_max_ref) * 100))
        pct_ano = int(round((v_ano / cap_max_ref) * 100))

        conc = self.conc_molar.get()
        corriente = self.current_amp.get()
        caudal = int(self.flow_rate.get())

        # Etiquetas de los recuadros de Capacidad de Tanques
        self.lbl_vol_cat_val.config(text=f"{v_cat:g} L ({pct_cat}% Nivel)")
        self.lbl_vol_ano_val.config(text=f"{v_ano:g} L ({pct_ano}% Nivel)")
        self.lbl_conc_val.config(text=f"{conc:.2f} mol/L")

        # Etiquetas de los sliders de parámetros
        self.lbl_curr_val.config(text=f"{corriente:.2f} A ({int(corriente * 20)} mA/cm²)")
        self.lbl_flow_val.config(text=f"{caudal} mL/min")
        self.lbl_deg_val.config(text=f"{int(self.deg_factor.get())}x")
        self.lbl_spd_val.config(text=f"{int(self.sim_speed.get())}x")

        # Cálculo de energía almacenada (Wh) y tanque limitante
        deg_total = self.deg_cat + self.deg_ano
        retencion = max(20.0, 100.0 - deg_total * 0.85)
        vol_lim = min(v_cat, v_ano)
        energia_wh = int(vol_lim * (conc / 1.5) * 49.8 * (retencion / 100.0))

        self.lbl_energy_wh.config(text=f"Capacidad Total: {energia_wh:,} Wh")
        if abs(v_cat - v_ano) < 1:
            self.lbl_limiting_tank.config(
                text=f"Balance Hidráulico: Balanceado ({vol_lim} L)", fg="#38bdf8"
            )
        elif v_cat < v_ano:
            self.lbl_limiting_tank.config(
                text=f"Reactivo Limitante: Catolito ({v_cat} L)", fg="#fbbf24"
            )
        else:
            self.lbl_limiting_tank.config(
                text=f"Reactivo Limitante: Anolito ({v_ano} L)", fg="#c084fc"
            )

        # Actualizar tarjetas superiores KPI
        if modo_activo == "CHARGE":
            txt_m = "AUTO-CICLADO (CARGA)" if self.mode == "AUTOCYCLE" else "MODO CARGA ACTIVO"
            self.kpi_mode["val"].config(text=txt_m, fg="#34d399")
            self.kpi_mode["sub"].config(text=f"Bombas: ON ({caudal} mL/min)")
        elif modo_activo == "DISCHARGE":
            txt_m = "AUTO-CICLADO (DESCARGA)" if self.mode == "AUTOCYCLE" else "MODO DESCARGA ACTIVO"
            self.kpi_mode["val"].config(text=txt_m, fg="#fbbf24")
            self.kpi_mode["sub"].config(text=f"Bombas: ON ({caudal} mL/min)")
        else:
            self.kpi_mode["val"].config(text="EN ESPERA (STANDBY)", fg="#94a3b8")
            self.kpi_mode["sub"].config(text="Bombas: APAGADAS (0 mL/min)")

        delta_str = "▲ Subiendo" if modo_activo == "CHARGE" else ("▼ Disminuyendo" if modo_activo == "DISCHARGE" else "OCV")
        self.kpi_volt["val"].config(text=f"{self.voltage:.3f} V ({delta_str})")
        self.kpi_volt["sub"].config(text=f"Nernst: {self.v_nernst:.3f} V | Pérdida: -{self.v_deg_loss:.3f} V")

        i_str = f"+{corriente:.2f} A" if modo_activo == "CHARGE" else (f"-{corriente:.2f} A" if modo_activo == "DISCHARGE" else "0.00 A")
        self.kpi_soc["val"].config(text=f"{self.soc:.1f} %")
        self.kpi_soc["sub"].config(text=f"Corriente Conector: {i_str}")

        self.kpi_deg_cat["val"].config(text=f"{self.deg_cat:.2f} %")
        self.kpi_deg_cat["sub"].config(text=f"Pureza Catolito: {100.0 - self.deg_cat:.1f}%")

        self.kpi_deg_ano["val"].config(text=f"{self.deg_ano:.2f} %")
        self.kpi_deg_ano["sub"].config(text=f"Pureza Anolito: {100.0 - self.deg_ano:.1f}%")

        eficiencia_e = max(52.0, 84.5 - deg_total * 0.32 - (corriente - 2.0) * 1.4)
        self.kpi_cycles["val"].config(text=f"Ciclo {self.cycles} / 50 (η={eficiencia_e:.1f}%)")
        self.kpi_cycles["sub"].config(text=f"Retención Capacidad: {retencion:.1f}%")

        # Actualizar Muestras de Colorimetría y Tabla de Diagnóstico
        self.swatch_cat.config(bg=hex_cat)
        self.swatch_ano.config(bg=hex_ano)
        turb_cat = "Turbio" if self.deg_cat > 12 else "Limpio"
        turb_ano = "Turbio" if self.deg_ano > 12 else "Limpio"
        self.lbl_swatch_cat.config(text=f"Catolito (+)\n{turb_cat} ({self.deg_cat:.1f}%)")
        self.lbl_swatch_ano.config(text=f"Anolito (-)\n{turb_ano} ({self.deg_ano:.1f}%)")

        dens_energia = 29.5 * (conc / 1.5) * (retencion / 100.0) * (self.voltage / 1.24)
        eff_coulomb = max(88.0, 99.1 - deg_total * 0.12)
        potencia_w = 0.0 if modo_activo == "IDLE" else self.voltage * corriente

        texto_tabla = (
            f"Potencial Equilibrio (Nernst): {self.v_nernst:6.3f} V\n"
            f"Caída por Degradación (ΔVdeg): -{self.v_deg_loss:5.3f} V\n"
            f"Sobrepotencial Óhmico/Bombas : {self.v_overpot:+6.3f} V\n"
            f"Potencia Eléctrica en PMS    : {potencia_w:6.2f} W\n"
            f"Densidad Energía Estimada    : {dens_energia:6.1f} Wh/L\n"
            f"Eficiencia Coulómbica (ηC)   : {eff_coulomb:6.1f} %"
        )
        self.lbl_diag_table.config(text=texto_tabla)

    # ==========================================================================
    # DIBUJO DEL ESQUEMA INTERACTIVO Y GRÁFICAS EN EL CANVAS
    # ==========================================================================
    @staticmethod
    def _punto_en_polilinea(pts, frac: float):
        frac = max(0.0, min(1.0, frac))
        longitudes = []
        total = 0.0
        for i in range(len(pts) - 1):
            d = math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            longitudes.append(d)
            total += d
        objetivo = frac * total
        for i, seg in enumerate(longitudes):
            if objetivo <= seg or i == len(longitudes) - 1:
                t = 0.0 if seg == 0 else objetivo / seg
                x = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
                y = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
                return x, y
            objetivo -= seg
        return pts[0]

    def _dibujar_todo(self):
        c = self.canvas
        c.delete("all")

        W = max(680, c.winfo_width())
        H = max(560, c.winfo_height())

        # Dividimos la altura del Canvas:
        # 70% superior -> Diagrama Esquemático (PMS, BMS, Stack RFcell, Tanques y Bombas)
        # 30% inferior -> 2 Gráficas Científicas (Voltaje en vivo y 50 Ciclos)
        H_esq = int(H * 0.69)
        modo_activo = self._obtener_modo_activo()
        bombas_activas = modo_activo in ("CHARGE", "DISCHARGE")
        hex_cat, hex_ano = self._calcular_colores_electrolitos()

        # 1. Cuadrícula técnica de fondo
        for gx in range(0, W, 32):
            c.create_line(gx, 0, gx, H_esq, fill="#0f172a")
        for gy in range(0, H_esq, 32):
            c.create_line(0, gy, W, gy, fill="#0f172a")

        # Coordenadas proporcionales del esquema (fiel a la pág. 6 del Protocolo)
        pms_w, pms_h = W * 0.32, H_esq * 0.15
        pms_x, pms_y = (W - pms_w) * 0.47, H_esq * 0.06

        bms_w, bms_h = W * 0.17, H_esq * 0.13
        bms_x, bms_y = W * 0.80, H_esq * 0.16

        cell_w, cell_h = W * 0.27, H_esq * 0.43
        cell_x = pms_x + (pms_w - cell_w) / 2
        cell_y = H_esq * 0.33

        tank_w, tank_h = W * 0.18, H_esq * 0.41
        ltank_x, rtank_x = W * 0.055, W * 0.725
        tank_y = H_esq * 0.35

        pump_y = H_esq * 0.885
        lpump_x = ltank_x + tank_w * 0.5
        rpump_x = rtank_x + tank_w * 0.5
        pump_r = min(W, H_esq) * 0.042

        col_w = cell_w * 0.11
        mem_w = max(8, cell_w * 0.045)
        comp_w = (cell_w - 2 * col_w - mem_w) / 2

        lcomp_cx = cell_x + col_w + comp_w * 0.5
        rcomp_cx = cell_x + col_w + comp_w + mem_w + comp_w * 0.5

        # ----------------------------------------------------------------------
        # A. TUBERÍAS HIDRÁULICAS Y FLUJO DE LÍQUIDO (CATOLITO Y ANOLITO)
        # ----------------------------------------------------------------------
        pipe_l_bot = [(lpump_x, tank_y + tank_h), (lpump_x, pump_y), (lcomp_cx, pump_y), (lcomp_cx, cell_y + cell_h)]
        pipe_l_top = [(lcomp_cx, cell_y), (lcomp_cx, H_esq * 0.25), (lpump_x, H_esq * 0.25), (lpump_x, tank_y)]
        pipe_r_bot = [(rpump_x, tank_y + tank_h), (rpump_x, pump_y), (rcomp_cx, pump_y), (rcomp_cx, cell_y + cell_h)]
        pipe_r_top = [(rcomp_cx, cell_y), (rcomp_cx, H_esq * 0.25), (rpump_x, H_esq * 0.25), (rpump_x, tank_y)]

        for pts, color_hex in [
            (pipe_l_bot, hex_cat),
            (pipe_l_top, hex_cat),
            (pipe_r_bot, hex_ano),
            (pipe_r_top, hex_ano),
        ]:
            flat = [coord for pt in pts for coord in pt]
            c.create_line(*flat, fill="#334155", width=13, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            c.create_line(*flat, fill=color_hex, width=8, capstyle=tk.ROUND, joinstyle=tk.ROUND)
            if bombas_activas:
                for k in range(6):
                    frac = (self.anim_phase + k / 6.0) % 1.0
                    px, py = self._punto_en_polilinea(pts, frac)
                    c.create_oval(px - 3, py - 3, px + 3, py + 3, fill="#f8fafc", outline="")

        # ----------------------------------------------------------------------
        # B. TANQUES EXTERNOS: TANQUE CATOLITO (+) Y TANQUE ANOLITO (-)
        # ----------------------------------------------------------------------
        cap_max_tanque = max(200.0, self.vol_catolito.get(), self.vol_anolito.get())
        self._dibujar_tanque(
            c,
            ltank_x,
            tank_y,
            tank_w,
            tank_h,
            hex_cat,
            self.deg_cat,
            self.vol_catolito.get(),
            cap_max_tanque,
            "TANQUE CATOLITO (+)",
            "Lignina / Quinona",
            f"Q / QH₂ ({self.soc:.0f}%)",
            bombas_activas,
        )
        self._dibujar_tanque(
            c,
            rtank_x,
            tank_y,
            tank_w,
            tank_h,
            hex_ano,
            self.deg_ano,
            self.vol_anolito.get(),
            cap_max_tanque,
            "TANQUE ANOLITO (-)",
            "Antraquinona (AQDS)",
            f"AQDSH₂ ({self.soc:.0f}%)",
            bombas_activas,
        )

        # ----------------------------------------------------------------------
        # C. BOMBAS HIDRÁULICAS (BOMBA 1 CATOLITO Y BOMBA 2 ANOLITO)
        # ----------------------------------------------------------------------
        for px, nombre in [(lpump_x, "Bomba Catolito"), (rpump_x, "Bomba Anolito")]:
            color_borde = "#10b981" if bombas_activas else "#475569"
            c.create_oval(
                px - pump_r, pump_y - pump_r, px + pump_r, pump_y + pump_r,
                fill="#0f172a", outline=color_borde, width=3
            )
            rad = math.radians(self.pump_angle)
            for b in range(4):
                ang = rad + b * (math.pi / 2)
                c.create_line(
                    px, pump_y,
                    px + math.cos(ang) * pump_r * 0.72,
                    pump_y + math.sin(ang) * pump_r * 0.72,
                    fill="#34d399" if bombas_activas else "#64748b",
                    width=3,
                )
            c.create_oval(px - 5, pump_y - 5, px + 5, pump_y + 5, fill=color_borde, outline="")
            c.create_text(
                px + pump_r + 8, pump_y - 5,
                text=nombre, fill="#6ee7b7" if bombas_activas else "#94a3b8",
                font=("Segoe UI", 8, "bold"), anchor="w"
            )
            estado_b = f"ON ({int(self.flow_rate.get())} mL/m)" if bombas_activas else "APAGADA"
            c.create_text(
                px + pump_r + 8, pump_y + 8,
                text=estado_b, fill="#cbd5e1", font=("Consolas", 7), anchor="w"
            )

        # ----------------------------------------------------------------------
        # D. STACK / CELDA ELECTROQUÍMICA CENTRAL (RFcell)
        # ----------------------------------------------------------------------
        lcol_x = cell_x
        lcomp_x = lcol_x + col_w
        mem_x = lcomp_x + comp_w
        rcomp_x = mem_x + mem_w
        rcol_x = rcomp_x + comp_w

        # Compartimentos con electrodos porosos de fieltro de carbono
        c.create_rectangle(lcomp_x, cell_y, lcomp_x + comp_w, cell_y + cell_h, fill=hex_cat, outline="#334155")
        c.create_rectangle(rcomp_x, cell_y, rcomp_x + comp_w, cell_y + cell_h, fill=hex_ano, outline="#334155")

        # Textura porosa del fieltro de carbono
        for fy in range(int(cell_y + 14), int(cell_y + cell_h - 10), 18):
            for fx in range(int(lcomp_x + 10), int(lcomp_x + comp_w - 8), 18):
                c.create_rectangle(fx, fy, fx + 3, fy + 3, fill="#0f172a", outline="")
            for fx in range(int(rcomp_x + 10), int(rcomp_x + comp_w - 8), 18):
                c.create_rectangle(fx, fy, fx + 3, fy + 3, fill="#0f172a", outline="")

        # Colectores de corriente de grafito (+ y -)
        c.create_rectangle(lcol_x, cell_y - 4, lcol_x + col_w, cell_y + cell_h + 4, fill="#ea580c", outline="#fdba74", width=2)
        c.create_rectangle(rcol_x, cell_y - 4, rcol_x + col_w, cell_y + cell_h + 4, fill="#ea580c", outline="#fdba74", width=2)
        c.create_text(lcol_x + col_w / 2, cell_y + 18, text="+", fill="white", font=("Consolas", 13, "bold"))
        c.create_text(rcol_x + col_w / 2, cell_y + 18, text="−", fill="white", font=("Consolas", 13, "bold"))
        c.create_text(lcol_x + col_w / 2, cell_y + cell_h * 0.55, text="e⁻", fill="#fef08a", font=("Consolas", 9, "bold"))
        c.create_text(rcol_x + col_w / 2, cell_y + cell_h * 0.55, text="e⁻", fill="#fef08a", font=("Consolas", 9, "bold"))

        # Membrana de Intercambio Iónico central
        c.create_rectangle(mem_x, cell_y - 6, mem_x + mem_w, cell_y + cell_h + 6, fill="#fde047", outline="#ca8a04", width=1)
        c.create_text(cell_x + cell_w / 2, cell_y - 14, text="RFcell (Stack Electroquímico)", fill="#f8fafc", font=("Segoe UI", 10, "bold"))

        c.create_text(lcomp_x + comp_w / 2, cell_y + 26, text="QH₂ ⇌ Q", fill="white", font=("Consolas", 9, "bold"))
        c.create_text(rcomp_x + comp_w / 2, cell_y + 26, text="AQDS ⇌ AQDSH₂", fill="white", font=("Consolas", 9, "bold"))

        # Protones H+ cruzando la membrana
        mem_cx = mem_x + mem_w / 2
        for idx, y_frac in enumerate([0.25, 0.45, 0.65, 0.82]):
            py = cell_y + cell_h * y_frac
            desp_x = 0.0
            if modo_activo == "CHARGE":
                f = (self.anim_phase + idx * 0.25) % 1.0
                desp_x = (f - 0.5) * (comp_w * 0.85)
            elif modo_activo == "DISCHARGE":
                f = (self.anim_phase + idx * 0.25) % 1.0
                desp_x = (0.5 - f) * (comp_w * 0.85)

            c.create_line(mem_cx - 22, py, mem_cx + 22, py, fill="#94a3b8", dash=(2, 2))
            c.create_oval(mem_cx + desp_x - 8, py - 8, mem_cx + desp_x + 8, py + 8, fill="white", outline="#0284c7", width=2)
            c.create_text(mem_cx + desp_x, py, text="H+", fill="#0f172a", font=("Consolas", 7, "bold"))

        c.create_text(
            cell_x + cell_w / 2, cell_y + cell_h + 18,
            text="Membrana de Intercambio Iónico + Electrodos de Fieltro de Carbono",
            fill="#fde047", font=("Segoe UI", 8, "bold")
        )

        # ----------------------------------------------------------------------
        # E. CONECTOR DE CORRIENTE, CABLES ELÉCTRICOS Y PMS / BMS
        # ----------------------------------------------------------------------
        lwire_x = lcol_x + col_w / 2
        rwire_x = rcol_x + col_w / 2
        wire_l = [(lwire_x, cell_y - 4), (lwire_x, pms_y + pms_h * 0.5), (pms_x, pms_y + pms_h * 0.5)]
        wire_r = [(pms_x + pms_w, pms_y + pms_h * 0.5), (rwire_x, pms_y + pms_h * 0.5), (rwire_x, cell_y - 4)]

        c.create_line(*[coord for pt in wire_l for coord in pt], fill="#f97316", width=4)
        c.create_line(*[coord for pt in wire_r for coord in pt], fill="#38bdf8", width=4)

        # Electrones animados (e-) circulando por el circuito eléctrico externo
        if bombas_activas:
            circuito_total = wire_l + wire_r
            for k in range(10):
                frac = (self.anim_phase + k / 10.0) % 1.0
                if modo_activo == "DISCHARGE":
                    frac = 1.0 - frac
                ex, ey = self._punto_en_polilinea(circuito_total, frac)
                c.create_oval(ex - 4, ey - 4, ex + 4, ey + 4, fill="#fde047", outline="#ca8a04")

        # Caja PMS (Convertidor Bidireccional DC/AC + Conector de Corriente)
        borde_pms = "#10b981" if modo_activo == "CHARGE" else ("#f59e0b" if modo_activo == "DISCHARGE" else "#64748b")
        c.create_rectangle(pms_x, pms_y, pms_x + pms_w, pms_y + pms_h, fill="#1e293b", outline=borde_pms, width=2)
        c.create_text(
            pms_x + pms_w / 2, pms_y + pms_h * 0.28,
            text="PMS (Convertidor Bidireccional DC/AC)",
            fill="#fbbf24", font=("Segoe UI", 9, "bold")
        )
        pot_w = 0.0 if modo_activo == "IDLE" else self.voltage * self.current_amp.get()
        c.create_text(
            pms_x + pms_w / 2, pms_y + pms_h * 0.58,
            text=f"V = {self.voltage:.3f} V  |  P = {pot_w:.2f} W",
            fill="#f8fafc", font=("Consolas", 9, "bold")
        )
        txt_flujo_e = (
            "⚡ Conector: CARGANDO BATERÍA (e⁻ ➔)"
            if modo_activo == "CHARGE"
            else ("💡 Conector: DESCARGANDO A CARGA (⬅ e⁻)" if modo_activo == "DISCHARGE" else "🔌 Conector: ABIERTO (EN ESPERA)")
        )
        c.create_text(
            pms_x + pms_w / 2, pms_y + pms_h * 0.84,
            text=txt_flujo_e,
            fill="#34d399" if modo_activo == "CHARGE" else ("#fcd34d" if modo_activo == "DISCHARGE" else "#94a3b8"),
            font=("Segoe UI", 8, "bold")
        )

        # Caja BMS (Supervisor del Sistema a la derecha)
        c.create_rectangle(bms_x, bms_y, bms_x + bms_w, bms_y + bms_h, fill="#1e293b", outline="#eab308", width=2)
        c.create_text(bms_x + bms_w / 2, bms_y + bms_h * 0.30, text="BMS (Supervisor)", fill="#fde047", font=("Segoe UI", 9, "bold"))
        c.create_text(bms_x + bms_w / 2, bms_y + bms_h * 0.60, text=f"SoC: {self.soc:.1f}%", fill="#cbd5e1", font=("Consolas", 8, "bold"))
        c.create_text(bms_x + bms_w / 2, bms_y + bms_h * 0.83, text=f"Ciclo: {self.cycles}/50", fill="#34d399", font=("Consolas", 8))

        # ----------------------------------------------------------------------
        # F. DOS GRÁFICAS CIENTÍFICAS EN LA PARTE INFERIOR DEL CANVAS
        # ----------------------------------------------------------------------
        g_top = H_esq + 8
        g_bot = H - 10
        g_mid_x = W // 2

        self._dibujar_grafica_voltaje(c, 14, g_top, g_mid_x - 8, g_bot)
        self._dibujar_grafica_ciclos(c, g_mid_x + 8, g_top, W - 14, g_bot)

    def _dibujar_tanque(
        self, c, tx, ty, tw, th, color_liq, deg_pct, vol_litros, cap_max_tanque, titulo, subtitulo, especie_txt, activo
    ):
        # Contorno del tanque graduado
        c.create_rectangle(tx, ty, tx + tw, ty + th, fill="#0f172a", outline="#64748b", width=2)

        # Nivel dinámico de líquido según la cantidad total escrita en el recuadro
        pct_llenado = (vol_litros / cap_max_tanque) * 100.0
        frac_nivel = max(0.08, min(0.88, (vol_litros / cap_max_tanque) * 0.85))
        liq_top_y = ty + th * (1.0 - frac_nivel)

        c.create_rectangle(tx + 3, liq_top_y, tx + tw - 3, ty + th - 3, fill=color_liq, outline="")

        # Onda superficial del líquido
        pts_ola = [tx + 3, liq_top_y + 6]
        for wx in range(0, int(tw - 6), 12):
            wy = liq_top_y + math.sin((wx / 16.0) + math.radians(self.pump_angle * 2)) * (3.0 if activo else 1.0)
            pts_ola.extend([tx + 3 + wx, wy])
        pts_ola.extend([tx + tw - 3, liq_top_y + 6])
        if len(pts_ola) >= 6:
            c.create_line(*pts_ola, fill="#f8fafc", width=2)

        # Partículas en suspensión por degradación del electrolito
        if deg_pct > 0.4:
            num_part = min(len(self.precip_seeds), int(deg_pct * 0.8) + 1)
            for i in range(num_part):
                sx, sy, sr = self.precip_seeds[i]
                px = tx + 8 + sx * (tw - 16)
                desp_y = (sy + (self.anim_phase * 0.5 if activo else 0.0)) % 0.85
                py = liq_top_y + 8 + desp_y * max(10.0, (th * frac_nivel) - 16)
                c.create_oval(px - sr, py - sr, px + sr, py + sr, fill="#1c1917", outline="")

        # Marcas de graduación dinámicas en Litros (25%, 50%, 75%, 100% de cap_max_tanque)
        for m in range(1, 5):
            my = ty + th - (m * th * 0.21)
            marca_l = int(round((m / 4.0) * cap_max_tanque))
            c.create_line(tx + tw - 10, my, tx + tw - 2, my, fill="#94a3b8")
            c.create_text(tx + tw - 13, my, text=f"{marca_l}L", fill="#94a3b8", font=("Consolas", 6), anchor="e")

        # Textos del tanque
        c.create_text(tx + tw / 2, ty + 14, text=titulo, fill="#f8fafc", font=("Segoe UI", 8, "bold"))
        c.create_text(
            tx + tw / 2, ty + 28,
            text=f"Total: {vol_litros:g} L ({int(round(pct_llenado))}%)",
            fill="#38bdf8", font=("Consolas", 8, "bold")
        )
        c.create_text(tx + tw / 2, ty + th * 0.54, text=especie_txt, fill="white", font=("Consolas", 9, "bold"))
        c.create_text(tx + tw / 2, ty + th * 0.66, text=subtitulo, fill="#e2e8f0", font=("Segoe UI", 7))

        # Etiqueta inferior de Degradación dentro del tanque
        c.create_rectangle(tx + 8, ty + th - 24, tx + tw - 8, ty + th - 6, fill="#090d16", outline="#334155")
        c.create_text(
            tx + tw / 2, ty + th - 15,
            text=f"Degradación: {deg_pct:.1f}%",
            fill="#fda4af" if deg_pct > 15 else "#6ee7b7",
            font=("Consolas", 8, "bold")
        )

    def _dibujar_grafica_voltaje(self, c, x1, y1, x2, y2):
        c.create_rectangle(x1, y1, x2, y2, fill="#0b1324", outline="#1e293b", width=1)
        c.create_text(
            x1 + 10, y1 + 12,
            text="Curva en Tiempo Real: Voltaje de Celda (V) y SoC (%)",
            fill="#38bdf8", font=("Segoe UI", 8, "bold"), anchor="w"
        )

        pad_l, pad_r, pad_t, pad_b = 42, 36, 26, 20
        pw = max(50, (x2 - x1) - pad_l - pad_r)
        ph = max(40, (y2 - y1) - pad_t - pad_b)
        gx0, gy0 = x1 + pad_l, y1 + pad_t

        # Líneas de referencia (0.6 V a 1.6 V)
        for i in range(5):
            v_ref = 1.6 - i * 0.25
            yy = gy0 + (i / 4.0) * ph
            c.create_line(gx0, yy, gx0 + pw, yy, fill="#1e293b")
            c.create_text(gx0 - 4, yy, text=f"{v_ref:.2f}V", fill="#38bdf8", font=("Consolas", 7), anchor="e")
            c.create_text(gx0 + pw + 4, yy, text=f"{100 - i*25}%", fill="#34d399", font=("Consolas", 7), anchor="w")

        if len(self.time_history) < 2:
            return

        pts_v = []
        pts_soc = []
        n_max = max(2, self.max_time_pts - 1)
        for idx, item in enumerate(self.time_history):
            px = gx0 + (idx / n_max) * pw
            py_v = gy0 + (1.0 - (item["v"] - 0.6) / 1.0) * ph
            py_s = gy0 + (1.0 - item["soc"] / 100.0) * ph
            pts_v.extend([px, max(gy0, min(gy0 + ph, py_v))])
            pts_soc.extend([px, max(gy0, min(gy0 + ph, py_s))])

        if len(pts_soc) >= 4:
            c.create_line(*pts_soc, fill="#10b981", width=1, dash=(3, 3))
        if len(pts_v) >= 4:
            c.create_line(*pts_v, fill="#22d3ee", width=2)

    def _dibujar_grafica_ciclos(self, c, x1, y1, x2, y2):
        c.create_rectangle(x1, y1, x2, y2, fill="#0b1324", outline="#1e293b", width=1)
        c.create_text(
            x1 + 10, y1 + 12,
            text="Fase 3 y 4: Retención de Capacidad (%) vs 50 Ciclos",
            fill="#34d399", font=("Segoe UI", 8, "bold"), anchor="w"
        )

        pad_l, pad_r, pad_t, pad_b = 42, 16, 26, 20
        pw = max(50, (x2 - x1) - pad_l - pad_r)
        ph = max(40, (y2 - y1) - pad_t - pad_b)
        gx0, gy0 = x1 + pad_l, y1 + pad_t

        for i in range(5):
            pct = 100 - i * 20
            yy = gy0 + (i / 4.0) * ph
            c.create_line(gx0, yy, gx0 + pw, yy, fill="#1e293b")
            c.create_text(gx0 - 4, yy, text=f"{pct}%", fill="#94a3b8", font=("Consolas", 7), anchor="e")

        # Línea de Meta de Hipótesis del Protocolo (>75% de eficiencia)
        y_75 = gy0 + ((100.0 - 75.0) / 80.0) * ph
        c.create_line(gx0, y_75, gx0 + pw, y_75, fill="#f59e0b", dash=(4, 4))
        c.create_text(gx0 + pw - 4, y_75 - 6, text="Meta Hipótesis (>75%)", fill="#fbbf24", font=("Consolas", 7), anchor="e")

        pts_ret = []
        pts_eff = []
        for cyc, ret, eff in self.cycle_history:
            px = gx0 + (cyc / 50.0) * pw
            py_r = gy0 + ((100.0 - max(20.0, ret)) / 80.0) * ph
            py_e = gy0 + ((100.0 - max(20.0, eff)) / 80.0) * ph
            pts_ret.extend([px, py_r])
            pts_eff.extend([px, py_e])
            c.create_oval(px - 2.5, py_r - 2.5, px + 2.5, py_r + 2.5, fill="#10b981", outline="")

        if len(pts_ret) >= 4:
            c.create_line(*pts_ret, fill="#10b981", width=2)
        if len(pts_eff) >= 4:
            c.create_line(*pts_eff, fill="#38bdf8", width=2)

    # ==========================================================================
    # BUCLE PRINCIPAL DE ANIMACIÓN (25 FPS)
    # ==========================================================================
    def _actualizar_bucle(self):
        self._paso_fisicoquimico()
        self._actualizar_etiquetas_ui()
        self._dibujar_todo()
        self.root.after(40, self._actualizar_bucle)


if __name__ == "__main__":
    ventana = tk.Tk()
    app = SimuladorBateriaRedoxOrg(ventana)
    ventana.mainloop()