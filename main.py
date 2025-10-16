# main.py
import os
import webview
from bridge import Api

def _html_path():
    return os.path.abspath('index.html')

if __name__ == '__main__':
    api = Api()
    window = webview.create_window(
        title='PDF Fácil — Desktop',
        url=_html_path(),
        width=1100, height=800,
        resizable=True,
        easy_drag=False,
        js_api=api,              # ← AQUI (exposição pro JS)
    )
    # start sem js_api aqui
    webview.start(gui='edgechromium', debug=False, http_server=False)

