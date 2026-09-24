# -*- coding: utf-8 -*-
import sys
import os
import io
import csv
import re
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw

# Biblioteca do Windows para manipular Ã¡rea de transferÃªncia
try:
    import win32clipboard
    WIN32_DISPONIVEL = True
except ImportError:
    WIN32_DISPONIVEL = False

def copiar_imagem_para_clipboard(caminho_img):
    """Copia a imagem para o Clipboard usando somente a API nativa do Windows."""
    if not os.path.exists(caminho_img):
        return False

    abs_path = os.path.abspath(caminho_img)

    if not WIN32_DISPONIVEL:
        return False

    clipboard_aberto = False
    try:
        with Image.open(abs_path) as image:
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]

        win32clipboard.OpenClipboard()
        clipboard_aberto = True
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        return True
    except Exception:
        return False
    finally:
        if clipboard_aberto:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

def ler_metadados_csv(csv_path):
    """LÃª o cabeÃ§alho/metadados do CSV gerado."""
    meta = {'fone': '', 'nome_contato': '', 'titulo': 'Encarte de Ofertas', 'saida_jpg': ''}
    if not os.path.exists(csv_path):
        return meta

    try:
        for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(csv_path, mode='r', encoding=enc) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    if not reader.fieldnames or len(reader.fieldnames) <= 1:
                        f.seek(0)
                        reader = csv.DictReader(f, delimiter=',')
                    
                    if reader.fieldnames:
                        field_map = {col.strip().lower().replace('\ufeff', ''): col for col in reader.fieldnames}
                        
                        first_row = next(reader, None)
                        if first_row:
                            # Busca por qualquer coluna que represente WhatsApp/Contato
                            col_whats = None
                            for key in field_map:
                                if 'whatsapp' in key or 'contato' in key or 'fone' in key or 'celular' in key:
                                    col_whats = field_map[key]
                                    break
                            
                            if col_whats:
                                raw_whatsapp = first_row.get(col_whats, '').strip()
                                if ' - ' in raw_whatsapp:
                                    partes = raw_whatsapp.split(' - ', 1)
                                    meta['nome_contato'] = partes[0].strip()
                                    meta['fone'] = partes[1].strip()
                                else:
                                    meta['fone'] = raw_whatsapp
                            break
            except Exception:
                continue
    except Exception:
        pass

    return meta

def limpar_numero_whatsapp(fone_raw):
    """Remove caracteres especiais e garante o DDD 55 (Brasil)"""
    apenas_numeros = "".join(c for c in fone_raw if c.isdigit())
    if not apenas_numeros:
        return ""
    if len(apenas_numeros) in [10, 11]:
        return "55" + apenas_numeros
    return apenas_numeros


EXTENSOES_IMAGEM = (".jpg", ".jpeg", ".png", ".bmp")


def localizar_arquivo_encarte(pasta):
    """Localiza a primeira imagem cujo nome contenha a palavra 'encarte'."""
    pasta = os.path.abspath(pasta or os.getcwd())
    if not os.path.isdir(pasta):
        return ""

    candidatos = []
    for nome in os.listdir(pasta):
        caminho = os.path.join(pasta, nome)
        nome_minusculo = nome.lower()
        if (os.path.isfile(caminho)
                and "encarte" in nome_minusculo
                and nome_minusculo.endswith(EXTENSOES_IMAGEM)):
            candidatos.append(caminho)

    def ordem_natural(caminho):
        nome = os.path.basename(caminho).lower()
        return [int(parte) if parte.isdigit() else parte
                for parte in re.split(r"(\d+)", nome)]

    candidatos.sort(key=ordem_natural)
    return candidatos[0] if candidatos else ""

class AppVisualizador:
    TEMAS = {
        "claro": {
            "fundo": "#F4F6F8",
            "superficie": "#FFFFFF",
            "superficie_alt": "#F8FAFC",
            "texto": "#172033",
            "texto_suave": "#667085",
            "borda": "#DDE3EA",
            "primaria": "#D91675",
            "primaria_ativa": "#B90F61",
            "primaria_texto": "#FFFFFF",
            "secundaria": "#EEF2F6",
            "secundaria_ativa": "#E2E8F0",
            "verde": "#1F9D68",
            "canvas": "#E9EDF2",
            "erro": "#C72C41",
        },
        "escuro": {
            "fundo": "#11151C",
            "superficie": "#191F29",
            "superficie_alt": "#202733",
            "texto": "#F4F7FB",
            "texto_suave": "#A8B2C1",
            "borda": "#303A49",
            "primaria": "#F02B8C",
            "primaria_ativa": "#C91D72",
            "primaria_texto": "#FFFFFF",
            "secundaria": "#293240",
            "secundaria_ativa": "#364254",
            "verde": "#35C98B",
            "canvas": "#0C1016",
            "erro": "#FF6678",
        },
    }

    def __init__(self, root, pasta_parametros="", jpg_path=""):
        self.root = root
        self.jpg_path = jpg_path
        self.lista_paginas = []
        self.indice_atual = 0
        self.zoom_fator = 2.0
        self.tema_atual = "escuro"
        self.widgets_tema = []
        self.logo_tk = None
        self.icones_tk = {}

        base_path = os.path.splitext(self.jpg_path)[0] if self.jpg_path else ""
        self.csv_path = f"{base_path}.csv" if base_path else ""
        self.meta = ler_metadados_csv(self.csv_path)
        self.num_whats = limpar_numero_whatsapp(self.meta.get('fone', ''))

        self.root.title("ZÃ© do Encarte - Visualizador de Ofertas")
        try:
            self.root.state('zoomed')
        except Exception:
            self.root.geometry("1280x850")
        self.root.minsize(960, 620)

        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        self.root.bind("<Left>", lambda event: self.pagina_anterior())
        self.root.bind("<Right>", lambda event: self.proxima_pagina())
        self.root.bind("<F5>", lambda event: self.atualizar_paginas())
        self.root.bind("<Control-plus>", lambda event: self.aumentar_zoom())
        self.root.bind("<Control-minus>", lambda event: self.diminuir_zoom())

        self._montar_interface()
        self.aplicar_tema()
        self.root.after(100, self.atualizar_paginas)

    def _registrar_tema(self, widget, papel, **opcoes):
        self.widgets_tema.append((widget, papel, opcoes))
        return widget

    def _criar_botao(self, pai, texto, comando, papel="secundario", largura=None):
        btn = tk.Button(
            pai,
            text=texto,
            command=comando,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            relief="flat",
            padx=13,
            pady=8,
            cursor="hand2",
            takefocus=True,
        )
        if largura:
            btn.config(width=largura)
        self._registrar_tema(btn, papel)
        return btn

    def _diretorio_executavel(self):
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _carregar_logo(self):
        nome_logo = "logo-ze2.jpg" if self.tema_atual == "escuro" else "logo-ze.jpg"
        caminho_logo = os.path.join(self._diretorio_executavel(), nome_logo)
        if not os.path.isfile(caminho_logo):
            return None
        try:
            logo = Image.open(caminho_logo).convert("RGB")
            logo.thumbnail((280, 78), Image.Resampling.LANCZOS)
            self.logo_tk = ImageTk.PhotoImage(logo)
            return self.logo_tk
        except Exception:
            return None

    def _atualizar_logo_tema(self):
        logo = self._carregar_logo()
        if logo:
            self.lbl_logo.config(image=logo, text="")
        else:
            self.lbl_logo.config(image="", text="ZÃ© do Encarte")

    def _criar_icone(self, nome, cor="#FFFFFF", tamanho=18):
        """Cria Ã­cones simples sem depender de caracteres especiais da fonte."""
        chave = (nome, cor, tamanho)
        if chave in self.icones_tk:
            return self.icones_tk[chave]

        img = Image.new("RGBA", (tamanho, tamanho), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        w = max(1, tamanho // 10)
        c = cor

        if nome == "pasta":
            d.rounded_rectangle((1, 5, tamanho - 1, tamanho - 2), radius=2, outline=c, width=w)
            d.line((3, 5, 3, 3, tamanho // 2, 3, tamanho // 2 + 2, 5), fill=c, width=w)
        elif nome == "atualizar":
            d.arc((2, 2, tamanho - 2, tamanho - 2), 35, 310, fill=c, width=w)
            d.polygon([(tamanho - 2, 3), (tamanho - 2, tamanho // 2), (tamanho // 2 + 2, 5)], fill=c)
        elif nome == "copiar":
            d.rounded_rectangle((5, 2, tamanho - 2, tamanho - 5), radius=2, outline=c, width=w)
            d.rounded_rectangle((2, 5, tamanho - 5, tamanho - 2), radius=2, outline=c, width=w)
        elif nome == "tema":
            d.ellipse((2, 2, tamanho - 2, tamanho - 2), outline=c, width=w)
            d.pieslice((2, 2, tamanho - 2, tamanho - 2), 90, 270, fill=c)
        elif nome == "anterior":
            d.line((tamanho - 5, 3, 5, tamanho // 2, tamanho - 5, tamanho - 3), fill=c, width=max(2, w))
        elif nome == "proximo":
            d.line((5, 3, tamanho - 5, tamanho // 2, 5, tamanho - 3), fill=c, width=max(2, w))

        foto = ImageTk.PhotoImage(img)
        self.icones_tk[chave] = foto
        return foto

    def _carregar_icone_whatsapp(self):
        """Procura ico-whats ao lado do executÃ¡vel e aceita formatos comuns."""
        pasta = self._diretorio_executavel()
        candidatos = ["ico-whats.png", "ico-whats.ico", "ico-whats.jpg", "ico-whats.jpeg"]
        for nome in candidatos:
            caminho = os.path.join(pasta, nome)
            if not os.path.isfile(caminho):
                continue
            try:
                imagem = Image.open(caminho).convert("RGBA")
                imagem.thumbnail((34, 34), Image.Resampling.LANCZOS)
                foto = ImageTk.PhotoImage(imagem)
                self.icones_tk["whatsapp"] = foto
                return foto
            except Exception:
                continue
        return None

    def _definir_icone_botao(self, botao, nome, cor="#FFFFFF", composto=True):
        icone = self._criar_icone(nome, cor)
        botao.config(image=icone, compound="left" if composto else "center")

    def _montar_interface(self):
        self.frame_topo = tk.Frame(self.root, bd=0, height=98)
        self.frame_topo.pack(fill="x", side="top")
        self.frame_topo.pack_propagate(False)
        self._registrar_tema(self.frame_topo, "superficie")

        frame_marca = tk.Frame(self.frame_topo, bd=0)
        frame_marca.pack(side="left", fill="y", padx=(20, 10))
        self._registrar_tema(frame_marca, "superficie")

        logo = self._carregar_logo()
        if logo:
            self.lbl_logo = tk.Label(frame_marca, image=logo, bd=0)
            self.lbl_logo.pack(side="left", pady=8)
            self._registrar_tema(self.lbl_logo, "superficie")
        else:
            self.lbl_logo = tk.Label(
                frame_marca, text="ZÃ© do Encarte", font=("Segoe UI", 20, "bold"), anchor="w"
            )
            self.lbl_logo.pack(side="left", pady=18)
            self._registrar_tema(self.lbl_logo, "titulo")

        frame_acoes = tk.Frame(self.frame_topo, bd=0)
        frame_acoes.pack(side="right", fill="y", padx=(8, 20))
        self._registrar_tema(frame_acoes, "superficie")

        self.btn_tema = self._criar_botao(frame_acoes, "Tema claro", self.alternar_tema)
        self._definir_icone_botao(self.btn_tema, "tema", "#0EA5E9")
        self.btn_tema.pack(side="right", padx=(7, 0), pady=27)

        self.btn_whats = self._criar_botao(frame_acoes, "", self.abrir_whatsapp, "whatsapp", largura=4)
        icone_whats = self._carregar_icone_whatsapp()
        if icone_whats:
            self.btn_whats.config(image=icone_whats, compound="center", padx=10, pady=4)
        else:
            self.btn_whats.config(text="WhatsApp", width=10)
        self.btn_whats.pack(side="right", padx=7, pady=27)

        self.btn_copiar = self._criar_botao(frame_acoes, "Copiar imagem", self.apenas_copiar_imagem, "azul")
        self._definir_icone_botao(self.btn_copiar, "copiar")
        self.btn_copiar.pack(side="right", padx=4, pady=27)

        self.btn_atualizar = self._criar_botao(frame_acoes, "Atualizar  F5", self.atualizar_paginas)
        self._definir_icone_botao(self.btn_atualizar, "atualizar", "#0EA5E9")
        self.btn_atualizar.pack(side="right", padx=4, pady=27)

        self.btn_arquivo = self._criar_botao(frame_acoes, "Abrir arquivo", self.abrir_arquivo)
        self._definir_icone_botao(self.btn_arquivo, "arquivo", "#0EA5E9")
        self.btn_arquivo.pack(side="right", padx=4, pady=27)

        self.btn_pasta = self._criar_botao(frame_acoes, "Abrir pasta", self.abrir_pasta)
        self._definir_icone_botao(self.btn_pasta, "pasta", "#0EA5E9")
        self.btn_pasta.pack(side="right", padx=4, pady=27)

        self.frame_nav = tk.Frame(self.root, bd=0, height=54)
        self.frame_nav.pack(fill="x", side="top")
        self.frame_nav.pack_propagate(False)
        self._registrar_tema(self.frame_nav, "superficie_alt")

        frame_controles_direita = tk.Frame(self.frame_nav, bd=0)
        frame_controles_direita.pack(side="right", padx=20, pady=8)
        self._registrar_tema(frame_controles_direita, "superficie_alt")

        frame_paginacao = tk.Frame(frame_controles_direita, bd=0)
        frame_paginacao.pack(side="left", padx=(0, 14))
        self._registrar_tema(frame_paginacao, "superficie_alt")

        self.btn_ant = self._criar_botao(frame_paginacao, "<", self.pagina_anterior, largura=3)
        self.btn_ant.config(font=("Segoe UI", 13, "bold"), padx=4, pady=3, state="disabled")
        self.btn_ant.pack(side="left", padx=(0, 5))

        self.lbl_paginacao = tk.Label(
            frame_paginacao, text="P\u00e1gina 0 a 0", font=("Segoe UI", 10, "bold"), width=14
        )
        self.lbl_paginacao.pack(side="left", padx=3)
        self._registrar_tema(self.lbl_paginacao, "texto")

        self.btn_prox = self._criar_botao(frame_paginacao, ">", self.proxima_pagina, largura=3)
        self.btn_prox.config(font=("Segoe UI", 13, "bold"), padx=4, pady=3, state="disabled")
        self.btn_prox.pack(side="left", padx=(5, 0))

        frame_controles = tk.Frame(frame_controles_direita, bd=0)
        frame_controles.pack(side="left")
        self._registrar_tema(frame_controles, "superficie_alt")

        self.btn_zoom_out = self._criar_botao(frame_controles, "-", self.diminuir_zoom, largura=3)
        self.btn_zoom_out.config(font=("Segoe UI", 13, "bold"), padx=4, pady=3)
        self.btn_zoom_out.pack(side="left", padx=2)

        self.lbl_zoom = tk.Label(frame_controles, text="200%", font=("Segoe UI", 10, "bold"), width=7)
        self.lbl_zoom.pack(side="left", padx=3)
        self._registrar_tema(self.lbl_zoom, "texto")

        self.btn_zoom_in = self._criar_botao(frame_controles, "+", self.aumentar_zoom, largura=3)
        self.btn_zoom_in.config(font=("Segoe UI", 13, "bold"), padx=4, pady=3)
        self.btn_zoom_in.pack(side="left", padx=2)

        self.container_canvas = tk.Frame(self.root, bd=0)
        self.container_canvas.pack(fill="both", expand=True, padx=18, pady=(14, 18))
        self._registrar_tema(self.container_canvas, "canvas")

        self.v_scrollbar = tk.Scrollbar(self.container_canvas, orient="vertical", bd=0)
        self.v_scrollbar.pack(side="right", fill="y")
        self.h_scrollbar = tk.Scrollbar(self.container_canvas, orient="horizontal", bd=0)
        self.h_scrollbar.pack(side="bottom", fill="x")

        self.canvas = tk.Canvas(
            self.container_canvas,
            highlightthickness=1,
            yscrollcommand=self.v_scrollbar.set,
            xscrollcommand=self.h_scrollbar.set,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self._registrar_tema(self.canvas, "canvas")

        self.v_scrollbar.config(command=self.canvas.yview)
        self.h_scrollbar.config(command=self.canvas.xview)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def aplicar_tema(self):
        t = self.TEMAS[self.tema_atual]
        self.root.configure(bg=t["fundo"])

        for widget, papel, extras in self.widgets_tema:
            try:
                if papel == "superficie":
                    widget.config(bg=t["superficie"])
                elif papel == "superficie_alt":
                    widget.config(bg=t["superficie_alt"])
                elif papel == "titulo":
                    widget.config(bg=t["superficie"], fg=t["texto"])
                elif papel == "status":
                    widget.config(bg=t["superficie"], fg=t["verde"])
                elif papel == "texto":
                    widget.config(bg=t["superficie_alt"], fg=t["texto"])
                elif papel == "canvas":
                    widget.config(bg=t["canvas"], highlightbackground=t["borda"])
                elif papel == "azul":
                    widget.config(
                        bg="#38BDF8" if self.tema_atual == "escuro" else "#0EA5E9",
                        fg="#07111F" if self.tema_atual == "escuro" else "#FFFFFF",
                        activebackground="#7DD3FC", activeforeground="#07111F",
                        disabledforeground=t["texto_suave"],
                    )
                elif papel == "whatsapp":
                    widget.config(
                        bg="#25D366", fg="#FFFFFF",
                        activebackground="#1FB457", activeforeground="#FFFFFF",
                        disabledforeground=t["texto_suave"],
                    )
                elif papel == "primario":
                    widget.config(
                        bg=t["primaria"], fg=t["primaria_texto"],
                        activebackground=t["primaria_ativa"], activeforeground=t["primaria_texto"],
                        disabledforeground=t["texto_suave"],
                    )
                elif papel == "secundario":
                    widget.config(
                        bg=t["secundaria"], fg=t["texto"],
                        activebackground=t["secundaria_ativa"], activeforeground=t["texto"],
                        disabledforeground=t["texto_suave"],
                    )
                if extras:
                    widget.config(**extras)
            except tk.TclError:
                pass

        self.btn_tema.config(text="Tema escuro" if self.tema_atual == "claro" else "Tema claro")
        self._atualizar_logo_tema()
        self.atualizar_visualizacao()

    def alternar_tema(self):
        self.tema_atual = "escuro" if self.tema_atual == "claro" else "claro"
        self.aplicar_tema()

    def _on_mousewheel(self, event):
        if event.state & 0x0004:
            if event.delta > 0:
                self.aumentar_zoom()
            else:
                self.diminuir_zoom()
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def aumentar_zoom(self):
        if self.zoom_fator < 3.0:
            self.zoom_fator = round(self.zoom_fator + 0.2, 1)
            self.lbl_zoom.config(text=f"{int(self.zoom_fator * 100)}%")
            self.atualizar_visualizacao()

    def diminuir_zoom(self):
        if self.zoom_fator > 0.4:
            self.zoom_fator = round(self.zoom_fator - 0.2, 1)
            self.lbl_zoom.config(text=f"{int(self.zoom_fator * 100)}%")
            self.atualizar_visualizacao()

    def resetar_zoom(self):
        self.zoom_fator = 2.0
        self.lbl_zoom.config(text="200%")
        self.atualizar_visualizacao()

    def localizar_paginas_geradas(self, caminho_base):
        if not caminho_base:
            return []

        nome_sem_ext = os.path.splitext(caminho_base)[0]
        nome_limpo = re.sub(r'_\d+$', '', nome_sem_ext)
        pasta = os.path.dirname(caminho_base) or os.getcwd()

        arquivos_encontrados = []
        if os.path.exists(pasta):
            for f in os.listdir(pasta):
                if f.lower().endswith(EXTENSOES_IMAGEM):
                    caminho_completo = os.path.join(pasta, f)
                    sem_ext = os.path.splitext(caminho_completo)[0]
                    if sem_ext == nome_limpo or sem_ext.startswith(nome_limpo + "_"):
                        arquivos_encontrados.append(caminho_completo)

        def extrair_ordem(caminho):
            base = os.path.splitext(caminho)[0]
            match = re.search(r'_(\d+)$', base)
            return int(match.group(1)) if match else 0

        arquivos_encontrados.sort(key=extrair_ordem)
        resultado_final = []
        for item in arquivos_encontrados:
            if item not in resultado_final:
                resultado_final.append(item)
        return resultado_final

    def atualizar_paginas(self):
        self.lista_paginas = self.localizar_paginas_geradas(self.jpg_path)
        if self.indice_atual >= len(self.lista_paginas):
            self.indice_atual = max(0, len(self.lista_paginas) - 1)
        self.atualizar_visualizacao()

    def atualizar_visualizacao(self):
        self.canvas.delete("all")
        t = self.TEMAS[self.tema_atual]
        w_canv = self.canvas.winfo_width()
        h_canv = self.canvas.winfo_height()

        if not self.lista_paginas:
            cx = w_canv // 2 if w_canv > 50 else 590
            cy = h_canv // 2 if h_canv > 50 else 350
            self.canvas.create_text(
                cx, cy,
                text=(
                    f"Aguardando o encarte informado\n{self.jpg_path}\n\nPressione F5 para atualizar."
                    if self.jpg_path
                    else "Nenhuma imagem aberta.\n\nClique em Abrir arquivo para selecionar uma imagem."
                ),
                fill=t["texto_suave"], font=("Segoe UI", 12), justify="center"
            )
            self.lbl_paginacao.config(text="P\u00e1gina 0 a 0")
            self.btn_ant.config(state="disabled")
            self.btn_prox.config(state="disabled")
            return

        total = len(self.lista_paginas)
        self.lbl_paginacao.config(text=f"P\u00e1gina {self.indice_atual + 1} a {total}")
        self.btn_ant.config(state="normal" if self.indice_atual > 0 else "disabled")
        self.btn_prox.config(state="normal" if self.indice_atual < total - 1 else "disabled")

        caminho_atual = self.lista_paginas[self.indice_atual]
        try:
            self.pil_img = Image.open(caminho_atual)
            img_w, img_h = self.pil_img.size
            max_w = max(300, w_canv - 60) if w_canv > 60 else 1050
            max_h = max(300, h_canv - 40) if h_canv > 40 else 650
            base_ratio = min(max_w / img_w, max_h / img_h)
            final_w = max(1, int(img_w * base_ratio * self.zoom_fator))
            final_h = max(1, int(img_h * base_ratio * self.zoom_fator))
            img_resized = self.pil_img.resize((final_w, final_h), Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img_resized)
            pos_x = max(w_canv // 2, final_w // 2 + 10)
            pos_y = max(h_canv // 2, final_h // 2 + 10)
            self.canvas.create_image(pos_x, pos_y, image=self.tk_img, anchor="center")
            self.canvas.config(scrollregion=(0, 0, max(w_canv, final_w + 40), max(h_canv, final_h + 40)))
        except Exception as e:
            cx = w_canv // 2 if w_canv > 50 else 590
            cy = h_canv // 2 if h_canv > 50 else 350
            self.canvas.create_text(
                cx, cy, text=f"Erro ao carregar imagem:\n{e}", fill=t["erro"], font=("Segoe UI", 12)
            )

    def pagina_anterior(self):
        if self.indice_atual > 0:
            self.indice_atual -= 1
            self.atualizar_visualizacao()

    def proxima_pagina(self):
        if self.indice_atual < len(self.lista_paginas) - 1:
            self.indice_atual += 1
            self.atualizar_visualizacao()

    def apenas_copiar_imagem(self):
        if not self.lista_paginas:
            return
        caminho_atual = self.lista_paginas[self.indice_atual]
        copiou = copiar_imagem_para_clipboard(caminho_atual)
        if copiou:
            messagebox.showinfo(
                "Imagem copiada",
                f"A pÃ¡gina {self.indice_atual + 1} foi copiada.\n\nPressione CTRL + V para colar."
            )
        else:
            messagebox.showerror("Erro ao copiar", "NÃ£o foi possÃ­vel copiar a imagem.")

    def abrir_whatsapp(self):
        if not self.lista_paginas:
            return
        caminho_atual = self.lista_paginas[self.indice_atual]
        copiou = copiar_imagem_para_clipboard(caminho_atual)
        self.meta = ler_metadados_csv(self.csv_path)
        self.num_whats = limpar_numero_whatsapp(self.meta.get('fone', ''))
        nome_contato = self.meta.get('nome_contato', '')
        saudacao = f"OlÃ¡ {nome_contato}!" if nome_contato else "OlÃ¡!"
        mensagem = f"{saudacao} Segue nosso {self.meta.get('titulo', 'Encarte de Ofertas')}."
        msg_encoded = urllib.parse.quote(mensagem)
        if self.num_whats:
            url = f"https://api.whatsapp.com/send?phone={self.num_whats}&text={msg_encoded}"
        else:
            url = f"https://web.whatsapp.com/send?text={msg_encoded}"
        webbrowser.open(url)
        if copiou:
            messagebox.showinfo(
                "PÃ¡gina copiada",
                f"A pÃ¡gina {self.indice_atual + 1} foi copiada.\n\nNo WhatsApp, pressione CTRL + V para colar."
            )

    def abrir_arquivo(self):
        pasta_inicial = os.path.dirname(self.jpg_path) if self.jpg_path else os.getcwd()
        if not os.path.isdir(pasta_inicial):
            pasta_inicial = os.getcwd()

        caminho = filedialog.askopenfilename(
            parent=self.root,
            title="Abrir imagem do encarte",
            initialdir=pasta_inicial,
            filetypes=[
                ("Imagens", "*.jpg *.jpeg *.png *.bmp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("Bitmap", "*.bmp"),
                ("Todos os arquivos", "*.*"),
            ],
        )
        if not caminho:
            return

        self.jpg_path = os.path.abspath(caminho)
        self.csv_path = os.path.splitext(self.jpg_path)[0] + ".csv"
        self.meta = ler_metadados_csv(self.csv_path)
        self.num_whats = limpar_numero_whatsapp(self.meta.get("fone", ""))
        self.indice_atual = 0
        self.atualizar_paginas()

    def abrir_pasta(self):
        caminho_target = self.lista_paginas[self.indice_atual] if self.lista_paginas else self.jpg_path
        if caminho_target:
            pasta = caminho_target if os.path.isdir(caminho_target) else os.path.dirname(caminho_target)
        else:
            pasta = os.getcwd()
        if pasta and os.path.isdir(pasta):
            try:
                os.startfile(os.path.abspath(pasta))
            except (AttributeError, OSError):
                messagebox.showerror("Erro ao abrir pasta", "NÃ£o foi possÃ­vel abrir a pasta do encarte.")

if __name__ == "__main__":
    args = sys.argv[1:]

    if len(args) >= 2:
        pasta_param = args[0]
        arquivo_jpg = args[1]
    elif len(args) == 1:
        param1 = args[0]
        if param1.lower().endswith(EXTENSOES_IMAGEM):
            arquivo_jpg = param1
            pasta_param = os.path.dirname(param1) or os.getcwd()
        else:
            pasta_param = param1
            arquivo_jpg = localizar_arquivo_encarte(pasta_param)
    else:
        pasta_param = os.getcwd()
        arquivo_jpg = localizar_arquivo_encarte(pasta_param)

    # Sem parÃ¢metros ou sem um encarte localizado, abre o visualizador vazio.
    # O usuÃ¡rio poderÃ¡ escolher livremente uma imagem em "Abrir arquivo".
    root = tk.Tk()
    app = AppVisualizador(root, pasta_parametros=pasta_param, jpg_path=arquivo_jpg)
    root.mainloop()

