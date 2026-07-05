================================================================
 CONTROL DE ILUMINACION INTELIGENTE EN EL HOGAR
 Instalacion y ejecucion
================================================================
REQUISITOS
- Python 3.8 o superior
- Librerias: numpy y matplotlib

----------------------------------------------------------------
PASO 1: VERIFICAR SI TENES PYTHON
Abri una terminal:
  - Windows: tecla Windows, escribi "cmd" y Enter.
  - Mac: abri la app Terminal (Aplicaciones > Utilidades).
  - Linux: Ctrl + Alt + T.

Escribi y presiona Enter: 
python --version

Si muestra algo como "Python 3.11.5", ya lo tenes: pasa al Paso 3. 
(En Windows, si "python" no funciona, proba con "py --version".)

----------------------------------------------------------------
PASO 2: INSTALAR PYTHON (solo si no lo tenes)
1. Entra a https://www.python.org/downloads/
2. Descarga la ultima version y ejecuta el instalador.
3. IMPORTANTE (Windows): marca la casilla "Add Python to PATH"
   en la primera pantalla del instalador.
4. Termina la instalacion y reinicia la terminal.

----------------------------------------------------------------
PASO 3: INSTALAR LAS LIBRERIAS
Escribi y presiona Enter:
pip install numpy matplotlib

Si "pip" no funciona, proba con:
  - Windows:   py -m pip install numpy matplotlib
  - Mac/Linux: pip3 install numpy matplotlib

----------------------------------------------------------------
PASO 4: DESCARGAR EL PROYECTO
Si lo bajaste como ZIP, descomprimilo en una carpeta fácil de encontrar (por ejemplo, el Escritorio).

----------------------------------------------------------------
PASO 5: EJECUTAR EL TABLERO
1. En la terminal, ubicate en la carpeta del archivo con "cd". Por ejemplo: cd Desktop/tablero-control
2. Ejecuta el programa:
   python tablero_control.py

   (En Windows, si "python" no anda, usa: py tablero_control.py)

Se abrira una ventana con el tablero funcionando.
================================================================
