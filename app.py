from flask import Flask, request, send_file
import yt_dlp
import os
import static_ffmpeg
import tempfile
import platform
import glob
import shutil
static_ffmpeg.add_paths()

app = Flask(__name__)

# Detectar OS y usar carpeta apropiada
if platform.system() == 'Windows':
    # En Windows, usar AppData temporal
    DOWNLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'mp3_converter')
else:
    # En Linux/Render, usar /tmp
    DOWNLOAD_FOLDER = '/tmp/mp3_converter'

# Crear carpeta si no existe
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True) 

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mi Descargador Musical</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; text-align: center; padding: 40px 20px; background-color: #121212; color: #ffffff; }
            .container { max-width: 500px; margin: 0 auto; background: #1e1e1e; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
            h2 { color: #ff4757; }
            input[type="text"] { width: 100%; padding: 12px; margin: 20px 0; border: 1px solid #333; border-radius: 6px; background: #2f3542; color: white; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background-color: #ff4757; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; font-weight: bold; }
            button:hover { background-color: #e84118; }
            .footer { margin-top: 20px; font-size: 12px; color: #747d8c; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Descargar MP3</h2>
            <p>Pega el link de YouTube para bajar tu audio directamente al celular</p>
            <form action="/download" method="POST">
                <input type="text" name="url" placeholder="https://www.youtube.com/watch?v=..." required>
                <button type="submit">Convertir y Descargar</button>
            </form>
            <div class="footer">Desarrollado para uso personal</div>
        </div>
    </body>
    </html>
    '''

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form.get('url')
    
    if not video_url:
        return "Error: No se proporcionó URL", 400
    
    # Parche para evitar el bug de proxies de yt-dlp
    os.environ['HTTP_PROXY'] = ''
    os.environ['HTTPS_PROXY'] = ''
    
    # Crear carpeta única para esta descarga
    download_session = os.path.join(DOWNLOAD_FOLDER, f"session_{os.getpid()}")
    os.makedirs(download_session, exist_ok=True)
    
    mp3_file = None
    
    try:
        ydl_opts = {
            'format': 'ba/b',
            'outtmpl': os.path.join(download_session, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'ignoreerrors': False,
            'quiet': False,
            'no_warnings': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            base_filename = ydl.prepare_filename(info)
            
            # Buscar archivo MP3 generado
            mp3_files = glob.glob(os.path.join(download_session, '*.mp3'))
            if not mp3_files:
                raise Exception("No se pudo generar el archivo MP3")
            
            mp3_file = mp3_files[0]
        
        # Enviar archivo
        return send_file(
            mp3_file,
            as_attachment=True,
            download_name=os.path.basename(mp3_file),
            mimetype='audio/mpeg'
        )
        
    except Exception as e:
        error_msg = f"Error al procesar el enlace: {str(e)}"
        return error_msg, 400
    
    finally:
        # Limpiar archivos temporales
        try:
            if os.path.exists(download_session):
                shutil.rmtree(download_session)
        except Exception as cleanup_error:
            print(f"Error al limpiar archivos: {cleanup_error}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)