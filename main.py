# main.py
import os
import sys
from pathlib import Path
import webview
from bridge import Api

def app_root() -> Path:
    """
    Retorna a raiz dos arquivos estáticos.
    - Em build PyInstaller one-file: usa a pasta temporária (sys._MEIPASS).
    - Em dev: usa a pasta onde está este arquivo.
    """
    meipass = getattr(sys, "_MEIPASS", None)  # evita aviso do type checker
    if meipass:
        return Path(meipass)
    return Path(__file__).resolve().parent

if __name__ == "__main__":
    root = app_root()
    index_path = root / "index.html"
    index_uri = index_path.as_uri()  # gera "file:///C:/.../index.html"

    api = Api()

    window = webview.create_window(
        title="PDF Fácil — Desktop",
        url=index_uri,           # abre via file://
        width=1100,
        height=800,
        resizable=True,
        js_api=api,
    )

    # nada de http_server_root aqui; só iniciar normalmente
    webview.start(gui="edgechromium", debug=False)



