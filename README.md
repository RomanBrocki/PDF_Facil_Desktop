# 💻 PDF Fácil Desktop

Versão **local e offline** do PDF Fácil — construída em **Python** com uma ponte **HTML + WebView** para oferecer a mesma experiência da versão web, porém **sem precisar de internet ou servidor**.  
Tudo roda **diretamente no computador**, com performance superior e total privacidade dos arquivos.

Criado por **Roman Brocki** em Python, com suporte do **ChatGPT-5** no desenvolvimento.

---

## 🚀 Funcionalidades

- **Unir PDFs e imagens** em um único documento.  
- **Converter JPG, JPEG, PNG, WEBP e TIFF/ → PDF**, com compressão inteligente opcional.  
- **Comprimir PDFs** com 4 níveis:
  - **Nenhuma** — mantém como está.  
  - **Mínima** — comprime imagens que já eram rasterizadas.  
  - **Média** — converte páginas inteiras em imagem para reduzir o tamanho.  
  - **Máxima** — mesma lógica da média, porém com compressão mais agressiva (mantendo legibilidade).  
- **Estimativa de tamanho** (antes/depois) para prever ganho de compressão.  
- **Reordenar páginas** (manualmente ou por critérios: Original, Nome, Tipo).  
- **Girar páginas** (90°, 180°, 270°).  
- **Dividir PDFs** (selecionar páginas específicas e gerar um novo arquivo).  
- **Conversão automática** de imagens WEBP e TIFF (caso compatíveis).  
- **Guard-rails de eficiência:** o app só aplica compressão quando há ganho real — nunca produz um PDF maior que o original.

---

## 🧠 Como funciona

O aplicativo é dividido em duas camadas:

1. **Interface HTML (`index.html`)**  
   Roda localmente no navegador embutido (WebView), exibindo o painel visual e recebendo comandos do usuário.  

2. **Engine Python (camada lógica)**  
   - `main.py` — inicializa o servidor local, abre a interface no navegador embutido e gerencia o ciclo de vida do app.  
   - `bridge.py` — ponte entre JavaScript e Python (recebe ações do front-end e aciona o motor).  
   - `engine/pdf_ops.py` — motor de manipulação de PDFs e imagens (compressão, merge, rotação, split, etc.).  
   - `engine/engine_config.py` — define presets, níveis de compressão e parâmetros de heurística.  

Tudo roda **localmente**, sem dependência de rede ou APIs externas.

---

## ⚙️ Estrutura do Projeto

```
📁 PDF_Facil_Desktop/
├── main.py                # Lança o app local (WebView)
├── bridge.py              # Ponte entre front-end e motor
├── index.html             # Interface local (frontend)
├── engine/
    ├── pdf_ops.py         # Motor principal (compressão, merge, etc.)
    └── engine_config.py   # Parâmetros e presets


---

## 🖥️ Uso Padrão

### 🔹 Rodar localmente (modo desenvolvedor)

```bash
python main.py
```

O app abrirá automaticamente em uma janela local (WebView).  
Os arquivos processados são temporários — nada é enviado para fora do computador.

### 🔹 Gerar o executável (.exe)

Para empacotar tudo em um único arquivo executável (Windows):

```bash
pyinstaller main.py --onefile --noconsole --clean ^
  --exclude-module jupyter --exclude-module notebook --exclude-module ipykernel ^
  --exclude-module ipywidgets --exclude-module jupyterlab
```

O EXE será criado na pasta `dist/` e pode ser distribuído livremente.  
Nenhuma dependência de Python será necessária no computador do usuário.

---

## 🔒 Privacidade e Segurança

- **100% offline:** não há conexões externas, nem mesmo para telemetria.  
- **Sem envio de dados:** todos os arquivos permanecem em memória ou em pastas temporárias locais.  
- **Sessão descartável:** ao fechar o app, nada é persistido.

---

## 🧩 Dependências Essenciais

A versão Desktop utiliza apenas:

- **pywebview** — janela local embutida com navegador interno  
- **PyMuPDF (fitz)** — renderização, rotação e compressão de páginas  
- **Pillow (PIL)** — manipulação de imagens  
- **img2pdf** — conversão de imagens para PDF  
- **pypdf** — merge, split e reorganização de PDFs  

---

## 🧱 Como o motor de compressão funciona

O `engine/pdf_ops.py` executa compressões de forma adaptativa:
- Analisa o tamanho e tipo de cada página.
- Define o nível de recompressão conforme o preset global ou individual.
- Aplica JPEG progressivo, otimização e subsampling automático.
- Mantém qualidade visual priorizando eficiência.  
- Se a versão comprimida não for menor — o original é mantido.

---

## ▶️ Recursos avançados

- **Estimativa de ganho:** compara o tamanho final projetado com o original.  
- **Heurísticas customizáveis:** níveis e limiares definidos em `engine_config.py`.  
- **Rotação não destrutiva:** usa metadados de orientação, preservando conteúdo.  
- **Compatibilidade:** PDFs e imagens (JPG, PNG, WEBP, TIFF).  

---
## 📜 Licenças e Créditos

Este projeto utiliza bibliotecas open source sob licenças permissivas.  
Em especial:

- **PyMuPDF (AGPL-3.0)** — © Artifex Software, Inc.  
  Uso permitido em software aberto; este projeto mantém seu código-fonte público conforme os termos da AGPL.  
- **Demais bibliotecas** (Pillow, img2pdf, pypdf, pywebview, etc.) — sob licenças MIT, BSD ou Apache 2.0.  

O código-fonte completo está disponível publicamente, cumprindo todas as exigências de licenciamento.

---

## ✨ Créditos

Desenvolvido por **Roman Brocki**  
Assistência técnica e documentação: **ChatGPT-5**  

