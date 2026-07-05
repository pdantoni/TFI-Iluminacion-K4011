"""
================================================================================
TABLERO DE CONTROL - Control de Iluminación Inteligente en el hogar
Tecnologías para la Automatización - K4011 (UTN-FRBA)
Priscila Sharon D'Antoni  /  Lucrecia Vattimo
================================================================================
Ley de control: Proporcional-Derivativo (PD) POR UMBRAL.
El sistema es de Tipo 0: hay error estacionario admisible.

Requisitos: pip install numpy matplotlib
Ejecutar:   python tablero_control.py     (Windows: py tablero_control.py)
================================================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button, RadioButtons

# ─────────────────────────────────────────────────────────────────────────────
#  PARÁMETROS FÍSICOS Y DE SIMULACIÓN
# ─────────────────────────────────────────────────────────────────────────────
DT_SIM   = 0.1     # paso del "mundo" físico [s] (continuo, no depende del scan)
VENTANA  = 60.0    # segundos visibles en pantalla (ventana deslizante)
MAX_LED  = 1100.0  # lúmenes/lux máx. que emiten las tiras LED (límite físico)
K_PROC   = MAX_LED / 100.0   # ganancia de planta: lux por cada 1% de PWM
GAN_ACT  = 0.05    # factor de integración del actuador (cuánto mueve el PWM)
TAU_LED  = 0.4     # constante de tiempo de la planta [s] (inercia del LED)
# Niveles de setpoint, con su banda de tolerancia (±) por nivel
NIVELES = {
    "Muy baja (100 lux)":  {"sp": 100,  "tol": 20},
    "Baja (250 lux)":      {"sp": 250,  "tol": 40},
    "Media (500 lux)":     {"sp": 500,  "tol": 50},
    "Alta (750 lux)":      {"sp": 750,  "tol": 60},
    "Máxima (1000 lux)":   {"sp": 1000, "tol": 80},
}
# Perturbaciones seleccionables (amplitud por defecto en lux)
PERTURBACIONES = {
    "Vela (+60 lux)":     60,
    "Nube (-120 lux)":   -120,
    "Lámpara (+400 lux)": 400,
}
# Colores por contexto (se usan en gráficos y en el cartel de estado)
C_ESTABLE    = "#71db76"   # verde
C_TRANSIT    = "#ff9940"   # naranja
C_SATURACION = "#ff432e"   # rojo
class Tablero:
    def __init__(self):
        self.nivel_key = "Media (500 lux)"
        self.setpoint  = NIVELES[self.nivel_key]["sp"]
        self.tol       = NIVELES[self.nivel_key]["tol"]
        self.pausado   = False
        self._construir()
        self.reset()
        self.timer = self.fig.canvas.new_timer(interval=100)
        self.timer.add_callback(self._tick)
        self.timer.start()
    # ── Estado ───────────────────────────────────────────────────────────────
    def reset(self, *_):
        self.t         = 0.0
        self.lux_led   = float(self.setpoint)
        self.pwm       = self.setpoint / K_PROC
        self.err_prev  = 0.0
        self.t_scan    = 0.0
        self.u_raw     = 0.0
        self.pulsos    = []
        self.vueltas   = 0
        self.saturado  = False
        self.h_t, self.h_z, self.h_lux = [], [], []
        self.h_err, self.h_pwm, self.h_u = [], [], []
        self._fills = []
        self._dibujar(forzar=True)
    # ── Perturbaciones ───────────────────────────────────────────────────────
    def aplicar_perturbacion(self, *_):
        nombre = self.r_pert.value_selected
        amp    = PERTURBACIONES[nombre]
        dur    = self.s_dur.val
        self.pulsos.append({"t0": self.t, "dur": dur, "amp": amp})
        self.vueltas = 0
    def _perturbacion(self, t):
        return sum(p["amp"] for p in self.pulsos
                   if p["t0"] <= t < p["t0"] + p["dur"])
    # ── Avance temporal ──────────────────────────────────────────────────────
    def _tick(self):
        # Un disparo del timer avanza tantos pasos de física como indique el
        # slider "Velocidad": 1.0 = tiempo normal, 2.0 = el doble, etc.
        if self.pausado:
            return
        pasos = max(1, int(round(self.s_vel.val)))
        for _ in range(pasos):
            self._paso_fisica()
        self._dibujar()
    def _paso_fisica(self):
        self.t += DT_SIM
        # 1) Perturbación externa (se suma a la luz FÍSICA, no a la señal ADC)
        z = self._perturbacion(self.t)
        # 2) Planta con inercia: el LED persigue pwm*K con constante TAU_LED
        self.lux_led += (self.pwm * K_PROC - self.lux_led) * (DT_SIM / TAU_LED)
        self.lux_led  = float(np.clip(self.lux_led, 0, MAX_LED))
        lux_hab = np.clip(self.lux_led + z, 0, 30000)   # luz total del ambiente
        # 3) Medición del LDR (con ruido de sensor) y punto suma
        ruido  = np.random.normal(0, 1.5)
        medido = max(0.0, lux_hab + ruido)
        error  = self.setpoint - medido
        # 4) Controlador PD POR UMBRAL — solo corre cada dt_scan (veloc. de scan)
        dt_scan = self.s_scan.val
        if self.t - self.t_scan >= dt_scan - 1e-9:
            self.t_scan = self.t
            deriv = (error - self.err_prev) / dt_scan
            Kp, Kd = self.s_kp.val, self.s_kd.val
            if abs(error) > self.tol:                 # fuera de banda -> actúa
                self.u_raw = Kp * error + Kd * deriv
                self.pwm   = np.clip(self.pwm + self.u_raw * GAN_ACT, 0, 100)
                self.vueltas += 1
            else:                                     # dentro de banda -> no toca
                self.u_raw = 0.0
            self.err_prev = error
        # 5) Saturación / falla: actuador al límite y aún fuera de banda
        self.saturado = ((self.pwm <= 0.5 or self.pwm >= 99.5)
                         and abs(self.setpoint - lux_hab) > self.tol)
        # 6) Históricos
        err_real = self.setpoint - lux_hab
        for buf, val in [(self.h_t, self.t), (self.h_z, z), (self.h_lux, lux_hab),
                         (self.h_err, err_real), (self.h_pwm, self.pwm),
                         (self.h_u, self.u_raw)]:
            buf.append(val)
        while self.h_t and self.h_t[0] < self.t - VENTANA - 2:
            for buf in (self.h_t, self.h_z, self.h_lux, self.h_err,
                        self.h_pwm, self.h_u):
                buf.pop(0)
                          
    # ── Construcción de la interfaz ──────────────────────────────────────────
    def _construir(self):
        self.fig = plt.figure("Tablero de Control - Iluminación",
                              figsize=(16, 9))
        self.fig.patch.set_facecolor("#eef1f4")
        # 4 gráficos apilados a la derecha
        gs = gridspec.GridSpec(4, 1, left=0.34, right=0.94, top=0.945,
                               bottom=0.065, hspace=0.55)
        self.ax_proc = self.fig.add_subplot(gs[0])
        self.ax_err  = self.fig.add_subplot(gs[1])
        self.ax_z    = self.fig.add_subplot(gs[2])
        self.ax_ctrl = self.fig.add_subplot(gs[3])
        self.ax_u    = self.ax_ctrl.twinx()
        self.ax_proc.set_title("Salida del proceso: luz medida vs. setpoint ",
                               fontsize=10, fontweight="bold", loc="left")
        self.ax_err.set_title("Señal de error  e(t) = setpoint − medición",
                              fontsize=10, fontweight="bold", loc="left")
        self.ax_z.set_title("Perturbación Z(t)",
                            fontsize=10, fontweight="bold", loc="left")
        self.ax_ctrl.set_title("Salida del controlador: PWM [%] y acción u",
                               fontsize=10, fontweight="bold", loc="left")
        self.ax_ctrl.set_xlabel("Tiempo [s]")
        (self.l_lux,) = self.ax_proc.plot([], [], color="#1565C0", lw=1.8,
                                          label="Luz medida (LDR)")
        self.l_ref  = self.ax_proc.axhline(0, color="#c62828", ls="--", lw=1.2,
                                           label="Setpoint")
        self.l_umax = self.ax_proc.axhline(0, color="#e67e22", ls=":", lw=1.1,
                                           label="Umbral máx / mín")
        self.l_umin = self.ax_proc.axhline(0, color="#e67e22", ls=":", lw=1.1)
        self.banda  = None
        self.ax_proc.legend(loc="upper right", fontsize=8, framealpha=.9)
        (self.l_err,) = self.ax_err.plot([], [], color="#c0392b", lw=1.6)
        self.ax_err.axhline(0, color="#444", lw=0.7)
        (self.l_z,) = self.ax_z.plot([], [], color="#6a1b9a", lw=1.6,
                                     drawstyle="steps-post")
        self.ax_z.axhline(0, color="#444", lw=0.7)
        (self.l_pwm,) = self.ax_ctrl.plot([], [], color="#2e7d32", lw=1.8,
                                          drawstyle="steps-post", label="PWM [%]")
        (self.l_u,)   = self.ax_u.plot([], [], color="#e67e22", lw=1.1, ls="--",
                                       drawstyle="steps-post",
                                       label="Acción u (±)")
        self.ax_ctrl.set_ylim(-5, 105)
        self.ax_ctrl.set_ylabel("PWM [%]")
        self.ax_u.set_ylabel("u(t)")
        self.ax_ctrl.legend(loc="upper left", fontsize=8, framealpha=.9)
        self.ax_u.legend(loc="upper right", fontsize=8, framealpha=.9)
        for ax in (self.ax_proc, self.ax_err, self.ax_z, self.ax_ctrl):
            ax.set_facecolor("white")
            ax.grid(True, ls="--", alpha=0.4)
          
        # ============== PANEL DE MANDO ==============
        self.fig.text(0.02, 0.965, "TABLERO", fontsize=13,
                      fontweight="bold", color="#1a2332")
        self.fig.text(0.02, 0.945, "Control de iluminación inteligente en el hogar",
                      fontsize=9, color="#5a6472")
      
        # Setpoint (nivel)
        self.fig.text(0.02, 0.915, "Setpoint", fontsize=9, fontweight="bold")
        ax_niv = self.fig.add_axes([0.02, 0.80, 0.27, 0.105], facecolor="white")
        self.r_nivel = RadioButtons(ax_niv, list(NIVELES.keys()), active=2,
                                    activecolor="#1565C0")
        for lbl in self.r_nivel.labels:
            lbl.set_fontsize(9)
        self.r_nivel.on_clicked(self._cambio_nivel)
      
        # Telemetría en vivo
        self.fig.text(0.02, 0.775, "Estado en vivo", fontsize=9, fontweight="bold")
        ax_tel = self.fig.add_axes([0.02, 0.665, 0.27, 0.095], facecolor="white")
        ax_tel.axis("off")
        for sp in ax_tel.spines.values():
            sp.set_visible(True); sp.set_edgecolor("#c8ccd2")
        self.txt_tel = ax_tel.text(0.03, 0.92, "", va="top", ha="left",
                                   fontsize=8.6, family="monospace",
                                   transform=ax_tel.transAxes)
      
        # Sliders 
        self.fig.text(0.02, 0.635, "Parámetros del controlador",
                      fontsize=9, fontweight="bold")
        def mk_slider(y, label, vmin, vmax, vini, paso, color="#1565C0"):
            self.fig.text(0.02, y + 0.006, label, fontsize=8.5, va="center")
            ax = self.fig.add_axes([0.085, y, 0.16, 0.02], facecolor="#d9dde2")
            s = Slider(ax, "", vmin, vmax, valinit=vini, valstep=paso,
                       color=color)
            s.valtext.set_fontsize(8)
            return s
        self.s_kp   = mk_slider(0.585, "Kp",        0.0, 4.0, 1.75, 0.05)
        self.s_kd   = mk_slider(0.550, "Kd",        0.0, 0.5, 0.05, 0.01)
        self.s_scan = mk_slider(0.515, "Scan [s]",  0.2, 4.0, 1.0,  0.1)
        self.s_vel  = mk_slider(0.480, "Velocidad", 1.0, 6.0, 1.0,  1.0)
      
        # Perturbación
        self.fig.text(0.02, 0.430, "Perturbación", fontsize=9, fontweight="bold")
        ax_p = self.fig.add_axes([0.02, 0.345, 0.27, 0.075], facecolor="white")
        self.r_pert = RadioButtons(ax_p, list(PERTURBACIONES.keys()), active=0,
                                   activecolor="#6a1b9a")
        for lbl in self.r_pert.labels:
            lbl.set_fontsize(8.5)
        self.s_dur = mk_slider(0.300, "Duración [s]", 2, 60, 15, 1, "#6a1b9a")
        ax_iny = self.fig.add_axes([0.02, 0.240, 0.27, 0.04])
        self.b_iny = Button(ax_iny, "APLICAR PERTURBACIÓN", color="#f1c40f",
                            hovercolor="#f4d03f")
        self.b_iny.label.set_fontweight("bold")
        self.b_iny.on_clicked(self.aplicar_perturbacion)
      
        # Pausa / reset
        ax_pau = self.fig.add_axes([0.02, 0.185, 0.13, 0.04])
        self.b_pau = Button(ax_pau, "PAUSAR", color="#cfd4da")
        self.b_pau.on_clicked(self._pausa)
        ax_res = self.fig.add_axes([0.16, 0.185, 0.13, 0.04])
        self.b_res = Button(ax_res, "REINICIAR", color="#cfd4da")
        self.b_res.on_clicked(self.reset)
      
        # Cartel de estado
        self.txt_estado = self.fig.text(
            0.02, 0.125, "  ESTABLE  ", fontsize=12, fontweight="bold",
            color="white",
            bbox=dict(boxstyle="round,pad=0.4", fc=C_ESTABLE, ec="none"))
        self.txt_vueltas = self.fig.text(
            0.02, 0.080, "Vueltas de scan del transitorio: 0", fontsize=8.6)
      
    # ── Callbacks ────────────────────────────────────────────────────────────
    def _cambio_nivel(self, label):
        self.nivel_key = label
        self.setpoint  = NIVELES[label]["sp"]
        self.tol       = NIVELES[label]["tol"]
        self.reset()
    def _pausa(self, *_):
        self.pausado = not self.pausado
        self.b_pau.label.set_text("REANUDAR" if self.pausado else "PAUSAR")
        self.fig.canvas.draw_idle()
      
    # ── Dibujo ───────────────────────────────────────────────────────────────
    def _dibujar(self, forzar=False):
        if not self.h_t and not forzar:
            return
        t = np.array(self.h_t) if self.h_t else np.array([0.0])
        x0, x1 = max(0, self.t - VENTANA), max(VENTANA, self.t)
        self.l_lux.set_data(t, self.h_lux)
        self.l_err.set_data(t, self.h_err)
        self.l_z.set_data(t, self.h_z)
        self.l_pwm.set_data(t, self.h_pwm)
        self.l_u.set_data(t, self.h_u)
        self.l_ref.set_ydata([self.setpoint, self.setpoint])
        self.l_umax.set_ydata([self.setpoint + self.tol]*2)
        self.l_umin.set_ydata([self.setpoint - self.tol]*2)
        if self.banda is not None:
            self.banda.remove()
        self.banda = self.ax_proc.axhspan(self.setpoint - self.tol,
                                          self.setpoint + self.tol,
                                          color="#e67e22", alpha=0.13, zorder=0)
        for ax in (self.ax_proc, self.ax_err, self.ax_z, self.ax_ctrl):
            ax.set_xlim(x0, x1)
        # Auto-zoom sobre la ventana visible
        vis = [i for i, tt in enumerate(self.h_t) if x0 <= tt <= x1]
        def vv(buf):
            return [buf[i] for i in vis] if vis else [0.0]
        ylo = min(min(vv(self.h_lux)), self.setpoint - self.tol * 1.5)
        yhi = max(max(vv(self.h_lux)), self.setpoint + self.tol * 1.5)
        self.ax_proc.set_ylim(max(0, ylo - 40), yhi + 40)
        em = max(self.tol * 2.5, max(abs(v) for v in vv(self.h_err)) * 1.2, 10)
        self.ax_err.set_ylim(-em, em)
        zm = max(80, max(abs(v) for v in vv(self.h_z)) * 1.25)
        self.ax_z.set_ylim(-zm, zm)
        um = max(40, max(abs(v) for v in vv(self.h_u)) * 1.2)
        self.ax_u.set_ylim(-um, um)
        # Telemetría
        if self.h_lux:
            self.txt_tel.set_text(
                f"t        = {self.t:6.1f} s\n"
                f"Medición = {self.h_lux[-1]:7.1f} lux\n"
                f"Error    = {self.h_err[-1]:7.1f} lux\n"
                f"u(t)     = {self.h_u[-1]:7.1f}\n"
                f"PWM      = {self.pwm:6.1f} %")
        # Sombreado por contexto (transitorio / saturación)
        for f in self._fills:
            f.remove()
        self._fills = []
        if len(t) > 1:
            err = np.array(self.h_err)
            pwm = np.array(self.h_pwm)
            sat = (np.abs(err) > self.tol) & ((pwm <= 0.5) | (pwm >= 99.5))
            tra = (np.abs(err) > self.tol) & ~sat
            for ax in (self.ax_proc, self.ax_err, self.ax_ctrl):
                ymin, ymax = ax.get_ylim()
                self._fills.append(ax.fill_between(t, ymin, ymax, where=tra,
                                   facecolor=C_TRANSIT, alpha=0.14, step="mid"))
                self._fills.append(ax.fill_between(t, ymin, ymax, where=sat,
                                   facecolor=C_SATURACION, alpha=0.14,
                                   step="mid"))
                ax.set_ylim(ymin, ymax)
            if sat[-1]:
                self.txt_estado.set_text("  SATURACIÓN (falla física)  ")
                self.txt_estado.get_bbox_patch().set_facecolor(C_SATURACION)
            elif tra[-1]:
                self.txt_estado.set_text("  TRANSITORIO  ")
                self.txt_estado.get_bbox_patch().set_facecolor(C_TRANSIT)
            else:
                self.txt_estado.set_text("  ESTABLE  ")
                self.txt_estado.get_bbox_patch().set_facecolor(C_ESTABLE)
        self.txt_vueltas.set_text(
            f"Vueltas de scan del transitorio: {self.vueltas}")
        self.fig.canvas.draw_idle()
if __name__ == "__main__":
    app = Tablero()
    plt.show()
