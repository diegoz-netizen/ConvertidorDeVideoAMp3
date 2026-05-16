from flask import Flask, request, send_file
import yt_dlp
import os
import static_ffmpeg
static_ffmpeg.add_paths()

app = Flask(__name__)

# Render solo permite escribir en la carpeta /tmp en su plan gratuito
DOWNLOAD_FOLDER = '/tmp' 

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
    
    ydl_opts = {
            'format': 'ba/b',
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'no_cookies': True,  # <--- ESTO OBLIGA A YT-DLP A IGNORAR CUALQUIER ARCHIVO DE COOKIES MALO
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'prefer_ffmpeg': True,
            'keepvideo': False,
            'ignoreerrors': True,
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + '.mp3'
        
        return send_file(mp3_filename, as_attachment=True)
        
    except Exception as e:
        return f"Error al procesar el enlace: {str(e)}", 400

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)