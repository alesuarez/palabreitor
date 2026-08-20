# Palabreitor

Extrae el guion hablado de un video de clase (español) a un archivo de texto con marcas de tiempo.

## Instalación

### 1. Requisitos previos

- **Python 3.8+** — verificar con: `python --version`
- **ffmpeg** — necesario para extraer el audio del video.

Instalar ffmpeg en Windows:
```powershell
winget install Gyan.FFmpeg -e
```
Cierra y reabre la terminal para que el PATH se actualice. Verificar: `ffmpeg -version`

### 2. Tarjeta de video (opcional pero recomendado)

Si tienes una **GPU NVIDIA**, la transcripción es mucho más rápida. Solo necesitas:

- **Driver NVIDIA** actualizado (incluye las librerías CUDA de bajo nivel).
- Tu GPU debe soportar CUDA (serie GTX 900 o superior).

El programa **no requiere instalar CUDA Toolkit ni cuDNN manualmente**: las dependencias de NVIDIA (cuBLAS y cuDNN) se instalan automáticamente como paquetes de Python en el paso siguiente.

Sin GPU NVIDIA, el programa funciona igual pero en CPU (más lento: ~5-10x).

### 3. Instalar el programa

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Si la ejecución de `Activate.ps1` está bloqueada por la política de ejecución:
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

## Ejecución

### Opción 1: Doble clic (recomendada)

Haz **doble clic** en `ejecutar.cmd`. Se abrirá una ventana donde escribes la ruta del video
o lo **arrastras** a la ventana. También puedes arrastrar el video **directamente sobre** `ejecutar.cmd`.

### Opción 2: Línea de comandos

Con el entorno activado (`.\.venv\Scripts\Activate.ps1`):

```powershell
python palabreitor.py -i clase.mp4 -o clase_script.txt
```

> Importante: el video debe estar en español. La aplicación usa el modelo `large-v3-turbo` (alta precisión) con filtro de silencios.

### Argumentos

| Argumento | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `-i, --input` | Video de entrada (mp4, mkv, etc.) | obligatorio |
| `-o, --output` | Archivo de texto de salida (.txt) | obligatorio |
| `--device` | `auto` (detecta GPU NVIDIA), `cuda` o `cpu` | `auto` |

### Ejemplo

```powershell
python palabreitor.py -i "clases/clase_3_pitagoras.mp4" -o "apuntes/clase_3_pitagoras.txt"
```

### Salida

```
[00:00:00] Buenos días, hoy veremos el teorema de Pitágoras...
[00:03:12] Recuerden que la hipotenusa es el lado más largo...
```

### Notas

- La **primera ejecución** descarga el modelo (~1.6 GB) y se guarda en caché para las siguientes.
- Una clase de 1 hora tarda aproximadamente **2-5 minutos** en GPU (más en CPU).
- Si el venv se borra, reinstalar con: `py -m venv .venv && .\.venv\Scripts\Activate.ps1 && pip install -r requirements.txt`