# bridge.py
from __future__ import annotations
import io
import os
import base64
import traceback
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

import fitz  # PyMuPDF
from PIL import Image
import webview

from engine.pdf_ops import (
    estimate_pdf_page_size,
    estimate_image_pdf_size,
    merge_pages,
)

# ====== Parâmetros herdando seus defaults de thumbs ======
PREVIEW_PDF_DPI = 60    # manter
THUMB_MAX_W = 200
THUMB_MAX_H = 300
THUMB_JPEG_Q = 68

# ====== Estruturas ======
@dataclass
class SrcFile:
    name: str
    mime: str
    data: bytes  # conteúdo como bytes

@dataclass
class PageRef:
    src_id: int
    page_index: int
    is_pdf: bool

class Api:
    """
    Ponte JS <-> Python para o PDF Fácil Desktop (sem servidor).
    """
    def __init__(self) -> None:
        self.src_files: list[SrcFile] = []   # arquivos brutos recebidos
        self.pages: list[PageRef] = []       # índice de páginas (PDFs explodidos e imagens como 1 página)
        self.page_images_cache: dict[Tuple[int,int], bytes] = {}  # cache de imagem RGB (para estimativa/processo)

    # ---------- helpers ----------
    def _b64_to_bytes(self, b64: str) -> bytes:
        return base64.b64decode(b64.encode('ascii'))

    def _img_to_thumb_b64(self, img: Image.Image) -> str:
        # mantém proporção dentro de 200x300 e salva JPEG q=68
        img2 = img.copy()
        img2.thumbnail((THUMB_MAX_W, THUMB_MAX_H))
        bio = io.BytesIO()
        if img2.mode not in ('RGB',):
            img2 = img2.convert('RGB')
        img2.save(bio, format='JPEG', quality=THUMB_JPEG_Q, optimize=True, progressive=True)
        return 'data:image/jpeg;base64,' + base64.b64encode(bio.getvalue()).decode('ascii')

    def _pdf_page_to_image(self, pdf_bytes: bytes, page_index: int, dpi: int = PREVIEW_PDF_DPI) -> Image.Image:
        mat = fitz.Matrix(dpi/72, dpi/72)
        with fitz.open(stream=pdf_bytes, filetype='pdf') as doc:
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            return Image.frombytes('RGB', (pix.width, pix.height), pix.samples)


    def _ensure_page_image(self, ref: PageRef) -> Image.Image:
        """
        Converte PageRef para PIL.Image RGB (sem compressão), com cache.
        """
        key = (ref.src_id, ref.page_index)
        if key in self.page_images_cache:
            return Image.open(io.BytesIO(self.page_images_cache[key]))  # lazy decode
        src = self.src_files[ref.src_id]
        if ref.is_pdf:
            img = self._pdf_page_to_image(src.data, ref.page_index, dpi=300)  # base para compressões
        else:
            img = Image.open(io.BytesIO(src.data))
            if img.mode not in ('RGB',):
                img = img.convert('RGB')
        # guarda cache como PNG (sem perdas internas de cor)
        bio = io.BytesIO()
        img.save(bio, format='PNG', optimize=True)
        self.page_images_cache[key] = bio.getvalue()
        return img

    # ---------- API: PREVIEW ----------
    def preview(self, files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        files: [{ name, type (mime), bytes_b64 }]
        Retorna: { items: [ {src_id,page_index,is_pdf,thumb_b64,filename} ] }
        """
        try:
            # anexa novos arquivos ao fim (carga incremental)
            base_id = len(self.src_files)
            for f in files:
                data = self._b64_to_bytes(f['bytes_b64'])
                self.src_files.append(SrcFile(name=f.get('name') or 'arquivo', mime=f.get('type') or '', data=data))

            # indexa páginas e gera thumbs
            items = []
            for src_id in range(base_id, len(self.src_files)):
                sf = self.src_files[src_id]
                is_pdf = (sf.mime.lower().endswith('/pdf') or sf.name.lower().endswith('.pdf'))
                if is_pdf:
                    with fitz.open(stream=sf.data, filetype='pdf') as doc:
                        for pi in range(doc.page_count):
                            thumb = self._img_to_thumb_b64(self._pdf_page_to_image(sf.data, pi, dpi=PREVIEW_PDF_DPI))
                            self.pages.append(PageRef(src_id=src_id, page_index=pi, is_pdf=True))
                            items.append({
                                'src_id': src_id, 'page_index': pi, 'is_pdf': True,
                                'thumb_b64': thumb, 'filename': sf.name,
                            })
                else:
                    # trata imagem unitária (JPG/PNG/WEBP/TIFF…)
                    img = Image.open(io.BytesIO(sf.data))
                    thumb = self._img_to_thumb_b64(img)
                    self.pages.append(PageRef(src_id=src_id, page_index=0, is_pdf=False))
                    items.append({
                        'src_id': src_id, 'page_index': 0, 'is_pdf': False,
                        'thumb_b64': thumb, 'filename': sf.name,
                    })

            return {'items': items}
        except Exception as e:
            traceback.print_exc()
            return {'error': str(e)}

    # ---------- API: ESTIMATE ----------
    def estimate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: { order, keep, rotate, level_page, level_global }
        Retorna: { total_before_bytes, total_after_bytes }
        Implementação usando pdf_ops: estimativa por página, sem rasterizar tudo em 300dpi.
        """
        try:
            order: List[Dict[str,int]] = payload['order']
            keep:  List[bool]          = payload['keep']
            lvl_pg: List[str]          = payload.get('level_page',[])
            lvl_gl: str                = payload.get('level_global','none')

            def level_of(idx:int) -> str:
                lv = (lvl_pg[idx] if idx < len(lvl_pg) and lvl_pg[idx] in ('none','min','med','max') else None)
                return lv or (lvl_gl if lvl_gl in ('none','min','med','max') else 'none')

            before = 0
            after  = 0

            for i, refd in enumerate(order):
                if not keep[i]:
                    continue
                src_id = refd['src_id']; page_index = refd['page_index']
                sf = self.src_files[src_id]
                is_pdf = (sf.mime.lower().endswith('/pdf') or sf.name.lower().endswith('.pdf'))

                # "Antes" = tamanho estimado copiando 1:1 (level='none')
                if is_pdf:
                    before += estimate_pdf_page_size(sf.data, page_index, 'none')
                    after  += estimate_pdf_page_size(sf.data, page_index, level_of(i))
                else:
                    before += estimate_image_pdf_size(sf.data, 'none')
                    after  += estimate_image_pdf_size(sf.data, level_of(i))

            return {'total_before_bytes': before, 'total_after_bytes': after}
        except Exception as e:
            traceback.print_exc()
            return {'error': str(e)}


    def _is_pdf_src(self, src_id:int) -> bool:
        sf = self.src_files[src_id]
        return (sf.mime.lower().endswith('/pdf') or sf.name.lower().endswith('.pdf'))

    # ---------- API: PROCESS ----------
    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        payload: { order, keep, rotate, level_page, level_global, filename_out }
        Gera o PDF final usando pdf_ops.merge_pages (sem rasterização “à parte”).
        """
        try:
            order: List[Dict[str,int]] = payload['order']
            keep:  List[bool]          = payload['keep']
            rotate:List[int]           = payload['rotate']
            lvl_pg: List[str]          = payload.get('level_page',[])
            lvl_gl: str                = payload.get('level_global','none')
            filename_out: str          = (payload.get('filename_out') or 'arquivo_final.pdf').strip()
            if not filename_out.lower().endswith('.pdf'):
                filename_out += '.pdf'

            def level_of(idx:int) -> str:
                lv = (lvl_pg[idx] if idx < len(lvl_pg) and lvl_pg[idx] in ('none','min','med','max') else None)
                return lv or (lvl_gl if lvl_gl in ('none','min','med','max') else 'none')

            # Monta o "pages_flat" esperado por pdf_ops.merge_pages:
            pages_flat: List[tuple[str, bytes, str, int, str]] = []
            rot_seq: List[int] = []

            for i, refd in enumerate(order):
                if not keep[i]:
                    continue
                src_id = refd['src_id']; page_index = refd['page_index']
                sf = self.src_files[src_id]
                kind = 'pdf' if (sf.mime.lower().endswith('/pdf') or sf.name.lower().endswith('.pdf')) else 'image'
                lev = level_of(i)

                # (name, data, kind, page_idx, level)
                pages_flat.append((sf.name, sf.data, kind, page_index if kind=='pdf' else 0, lev))
                rot_seq.append(int((rotate[i] if i < len(rotate) else 0) or 0))

            # Gera o PDF final com o motor oficial (rápido e com guard-rails)
            out_bytes = merge_pages(pages_flat, rotation_seq=rot_seq)

            # Diálogo de salvar
            dlg = webview.windows[0].create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename=filename_out,
            )
            if not dlg:
                return {'saved': False, 'path': None}

            save_path = dlg if isinstance(dlg, str) else dlg[0]
            if not str(save_path).lower().endswith('.pdf'):
                save_path = str(save_path) + '.pdf'

            with open(save_path, 'wb') as f:
                f.write(out_bytes)

            return {'saved': True, 'path': save_path}
        except Exception as e:
            traceback.print_exc()
            return {'error': str(e)}

