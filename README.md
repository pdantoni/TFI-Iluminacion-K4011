# Control de Iluminación Inteligente en el hogar

Simulador interactivo de un sistema de control de iluminación en lazo cerrado, con controlador Proporcional-Derivativo (PD) por umbral.

**Materia:** Tecnologías para la Automatización - K4011 (UTN-FRBA)
**Autoras:** Priscila D'Antoni / Lucrecia Vattimo

---

## ¿Qué hace este programa?

Simula en tiempo real cómo un sistema de control mantiene la iluminación de una habitación en un valor deseado (setpoint), corrigiendo automáticamente las perturbaciones (una vela, una nube que tapa el sol, una lámpara que se enciende).

El tablero muestra cuatro gráficos en vivo:
- **Salida del proceso:** la luz medida comparada con el setpoint y su banda de tolerancia.
- **Señal de error:** la diferencia entre el valor deseado y el medido.
- **Perturbación Z(t):** las alteraciones externas aplicadas.
- **Salida del controlador:** el PWM y la acción de control.

Y permite ajustar en vivo los parámetros del controlador, aplicar perturbaciones
y controlar la velocidad de la simulación.

---
## Requisitos previos
Necesitás tener instalado:
1. **Python 3.8 o superior**
2. Dos librerías: **numpy** y **matplotlib**

---
## Paso 1: verificar si tenés Python instalado
Abrí una terminal:
- **Windows:** apretá la tecla `Windows`, escribí `cmd` y presioná Enter.
- **Mac:** abrí la app `Terminal` (está en Aplicaciones → Utilidades).
- **Linux:** apretá `Ctrl` + `Alt` + `T`.

En la terminal, escribí este comando y presioná Enter: `python --version`. Si te muestra algo como `Python 3.11.5`, ya lo tenés. Pasá al Paso 3.
> **Nota para Windows:** si `python` no funciona, probá con `py --version`.

---
## Paso 2: Instalar Python (solo si no lo tenés)
1. Entrá a **https://www.python.org/downloads/**
2. Descargá la última versión y ejecutá el instalador.
3. **IMPORTANTE (Windows):** en la primera pantalla del instalador, marcá la casilla que dice **"Add Python to PATH"** antes de continuar. 
4. Completá la instalación y reiniciá la terminal.

---
## Paso 3: Instalar las librerías necesarias
En la terminal, escribí este comando y presioná Enter: `pip install numpy matplotlib`. 

> **Si `pip` no funciona**, probá con:
> - Windows: `py -m pip install numpy matplotlib`
> - Mac/Linux: `pip3 install numpy matplotlib`

---
## Paso 4: Descargar el proyecto
Si descargaste este proyecto como archivo ZIP, descomprimilo en una carpeta fácil de encontrar (por ejemplo, el Escritorio).

---
## Paso 5: Ejecutar el tablero
1. En la terminal, ubicate en la carpeta donde está el archivo. Usá el comando `cd` seguido de la ruta. `Por ejemplo: cd Desktop/tablero-control`

2. Ejecutá el programa: `python tablero_control.py`
 > En Windows, si `python` no anda, usá: `py tablero_control.py`

Se va a abrir una ventana con el tablero funcionando.

---

## Cómo usar el tablero
**Panel de mando (izquierda):**

| Control | Qué hace |
|---------|----------|
| **Setpoint** | Elegí el nivel de luz deseado (de 100 a 1000 lux) |
| **Estado en vivo** | Muestra los valores actuales: tiempo, medición, error, PWM |
| **Kp** | Ganancia proporcional: cuánto reacciona el controlador al error |
| **Kd** | Ganancia derivativa: cuánto reacciona a la velocidad del cambio |
| **Scan [s]** | Cada cuánto el controlador lee el sensor y actúa |
| **Velocidad** | Qué tan rápido avanza la simulación (1 = normal, 6 = muy rápido) |
| **Perturbación** | Elegí el tipo: vela, nube o lámpara |
| **Duración [s]** | Cuánto dura la perturbación al aplicarla |
| **APLICAR PERTURBACIÓN** | Inyecta la perturbación elegida en ese momento |
| **PAUSAR** | Congela la simulación (volvé a apretar para reanudar) |
| **REINICIAR** | Vuelve todo al estado inicial |

**Cartel de estado (colores):**
- 🟢 **Verde (ESTABLE):** el error está dentro de la banda permitida.
- 🟠 **Naranja (TRANSITORIO):** el sistema está corrigiendo una perturbación.
- 🔴 **Rojo (SATURACIÓN):** el actuador llegó a su límite físico y no puede corregir del todo.
