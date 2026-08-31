import sys
import os
import io
import csv
import re
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# Biblioteca do Windows para manipular área de transferência
try:
    import win32clipboard
    WIN32_DISPONIVEL = True
except ImportError:
    WIN32_DISPONIVEL = False

def copiar_imagem_para_clipboard(caminho_img):
    """Copia o arquivo JPG diretamente para a memória do Windows (CTRL+V)"""
    if not os.path.exists(caminho_img):
        return False

    if WIN32_DISPONIVEL:
        try:
            image = Image.open(caminho_img)
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()

            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            return True
        except Exception:
            return False
    else:
        try:
            cmd = f'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile(\'{caminho_img}\'))"'
            os.system(cmd)
            return True
        except Exception:
            return False

def ler_metadados_csv(csv_path):
    """Lê o cabeçalho/metadados do CSV gerado."""
    meta = {'fone': '', 'nome_contato': '', 'titulo': 'Encarte de Ofertas', 'saida_jpg': ''}
    if not os.path.exists(csv_path):
        return meta

    try:
        for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(csv_path, mode='r', encoding=enc) as f:
                    reader = csv.DictReader(f, delimiter=';')
                    if not reader.fieldnames:
                        reader = csv.DictReader(f, delimiter=',')
                    
                    if reader.fieldnames:
                        field_map = {col.strip().lower().replace('\ufeff', ''): col for col in reader.fieldnames}
                        
                        first_row = next(reader, None)
                        if first_row and 'contato_whatsapp' in field_map:
                            raw_whatsapp = first_row.get(field_map['contato_whatsapp'], '').strip()
                            
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

class AppVisualizador:
    def __init__(self, root, pasta_parametros="", jpg_path=""):
        self.root = root
        self.jpg_path = jpg_path
        
        # Mapeamento automático de páginas geradas
        self.lista_paginas = self.localizar_paginas_geradas(self.jpg_path)
        self.indice_atual = 0

        # Define caminho do CSV associado para ler os metadados de contato
        base_path = os.path.splitext(self.jpg_path)[0] if self.jpg_path else ""
        self.csv_path = f"{base_path}.csv" if base_path else ""

        self.meta = ler_metadados_csv(self.csv_path)
        self.num_whats = limpar_numero_whatsapp(self.meta.get('fone', ''))

        self.root.title("Visualizador de Encarte - Oeste Pharma")
        self.root.geometry("1050x800")
        self.root.configure(bg="#f0f0f0")
        
        # Traz a janela para a frente
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        # Atalhos do teclado para mudar de página
        self.root.bind("<Left>", lambda event: self.pagina_anterior())
        self.root.bind("<Right>", lambda event: self.proxima_pagina())

        # PAINEL SUPERIOR (MENU E WHATSAPP)
        frame_topo = tk.Frame(self.root, bg="#22702C")
        frame_topo.pack(fill="x", side="top", ipady=8)

        lbl_titulo = tk.Label(frame_topo, text="Encarte Gerado com Sucesso!", font=("Arial", 13, "bold"), fg="white", bg="#22702C")
        lbl_titulo.pack(side="left", padx=15)

        btn_whats = tk.Button(
            frame_topo, 
            text="📱 Copiar Página Atual e Abrir WhatsApp", 
            font=("Arial", 10, "bold"), 
            bg="#25D366", 
            fg="white", 
            activebackground="#1EBE5D",
            cursor="hand2",
            command=self.abrir_whatsapp
        )
        btn_whats.pack(side="right", padx=15)

        btn_pasta = tk.Button(
            frame_topo, 
            text="📁 Abrir Pasta das Imagens", 
            font=("Arial", 10), 
            bg="#ffffff", 
            fg="#333333", 
            cursor="hand2",
            command=self.abrir_pasta
        )
        btn_pasta.pack(side="right", padx=5)

        # BARRA DE NAVEGAÇÃO DE PÁGINAS (ANTERIOR / PRÓXIMO)
        frame_nav = tk.Frame(self.root, bg="#1B5E20")
        frame_nav.pack(fill="x", side="top", ipady=4)

        self.btn_ant = tk.Button(
            frame_nav, text="◀ Anterior", font=("Arial", 10, "bold"), bg="#ffffff", fg="#1B5E20",
            state="disabled", command=self.pagina_anterior, cursor="hand2"
        )
        self.btn_ant.pack(side="left", padx=15)

        self.lbl_paginacao = tk.Label(
            frame_nav, text="Página 0 de 0", font=("Arial", 11, "bold"), fg="white", bg="#1B5E20"
        )
        self.lbl_paginacao.pack(side="left", expand=True)

        self.btn_prox = tk.Button(
            frame_nav, text="Próximo ▶", font=("Arial", 10, "bold"), bg="#ffffff", fg="#1B5E20",
            state="disabled", command=self.proxima_pagina, cursor="hand2"
        )
        self.btn_prox.pack(side="right", padx=15)

        # PAINEL CENTRAL (VISUALIZAÇÃO DA IMAGEM)
        self.canvas = tk.Canvas(self.root, bg="#333333")
        self.canvas.pack(fill="both", expand=True)

        self.atualizar_visualizacao()

    def localizar_paginas_geradas(self, caminho_base):
        """Captura TODAS as páginas salvas (base e numeradas) sem limitar quantidade."""
        if not caminho_base:
            return []

        # Remove extensão e sufixos numéricos para descobrir o NOME LIMPO BASE
        nome_sem_ext = os.path.splitext(caminho_base)[0]
        nome_limpo = re.sub(r'_\d+$', '', nome_sem_ext)
        pasta = os.path.dirname(caminho_base) or os.getcwd()

        arquivos_encontrados = []
        if os.path.exists(pasta):
            for f in os.listdir(pasta):
                if f.lower().endswith(('.jpg', '.jpeg')):
                    caminho_completo = os.path.join(pasta, f)
                    sem_ext = os.path.splitext(caminho_completo)[0]
                    
                    # Captura se for exatamente o nome limpo ou se começar com 'NOME_LIMPO_'
                    if sem_ext == nome_limpo or sem_ext.startswith(nome_limpo + "_"):
                        arquivos_encontrados.append(caminho_completo)

        # Função para ordenar: Arquivo base sem número fica por último ou em 1º, 
        # e arquivos com _1, _2, _3 entram na ordem numérica exata.
        def extrair_ordem(caminho):
            base = os.path.splitext(caminho)[0]
            match = re.search(r'_(\d+)$', base)
            if match:
                return int(match.group(1))
            return 0  # Caso seja o arquivo base sem sufixo_N

        arquivos_encontrados.sort(key=extrair_ordem)
        
        # Remove duplicados mantendo a ordem
        resultado_final = []
        for item in arquivos_encontrados:
            if item not in resultado_final:
                resultado_final.append(item)

        return resultado_final

    def atualizar_visualizacao(self):
        """Redesenha a tela conforme a página selecionada"""
        self.canvas.delete("all")

        if not self.lista_paginas:
            self.canvas.create_text(
                525, 350, 
                text=f"Nenhum arquivo JPG encontrado em:\n{self.jpg_path}", 
                fill="white", font=("Arial", 13), justify="center"
            )
            self.lbl_paginacao.config(text="Página 0 de 0")
            self.btn_ant.config(state="disabled")
            self.btn_prox.config(state="disabled")
            return

        total = len(self.lista_paginas)
        self.lbl_paginacao.config(text=f"Página {self.indice_atual + 1} de {total}")

        # Atualiza estado dos botões de navegação
        self.btn_ant.config(state="normal" if self.indice_atual > 0 else "disabled")
        self.btn_prox.config(state="normal" if self.indice_atual < total - 1 else "disabled")

        # Carrega a imagem da página atual
        caminho_atual = self.lista_paginas[self.indice_atual]
        try:
            self.pil_img = Image.open(caminho_atual)
            img_w, img_h = self.pil_img.size
            
            # Ajuste de proporção na tela
            max_w, max_h = 1000, 650
            ratio = min(max_w / img_w, max_h / img_h)
            novo_tamanho = (int(img_w * ratio), int(img_h * ratio))

            img_resized = self.pil_img.resize(novo_tamanho, Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img_resized)

            self.canvas.create_image(525, 330, image=self.tk_img, anchor="center")
        except Exception as e:
            self.canvas.create_text(
                525, 350, text=f"Erro ao carregar a imagem:\n{e}", fill="red", font=("Arial", 12)
            )

    def pagina_anterior(self):
        if self.indice_atual > 0:
            self.indice_atual -= 1
            self.atualizar_visualizacao()

    def proxima_pagina(self):
        if self.indice_atual < len(self.lista_paginas) - 1:
            self.indice_atual += 1
            self.atualizar_visualizacao()

    def abrir_whatsapp(self):
        if not self.lista_paginas:
            return

        # Copia a página selecionada no momento para o Clipboard
        caminho_atual = self.lista_paginas[self.indice_atual]
        copiou = copiar_imagem_para_clipboard(caminho_atual)

        total_paginas = len(self.lista_paginas)
        msg_extra = ""
        if total_paginas > 1:
            msg_extra = f"\n\n💡 Seu encarte possui {total_paginas} páginas! Esta é a PÁGINA {self.indice_atual + 1}. Você pode folhear as páginas usando as setas do programa para copiar as outras também."

        if copiou:
            messagebox.showinfo(
                "Página Copiada!", 
                f"A Página {self.indice_atual + 1} foi COPIADA para a memória!\n\n"
                "Ao abrir o WhatsApp, pressione CTRL + V no campo de mensagem para colar a imagem."
                f"{msg_extra}"
            )

        # Abre conversa no WhatsApp
        nome_contato = self.meta.get('nome_contato', '')
        saudacao = f"Olá {nome_contato}!" if nome_contato else "Olá!"
        mensagem = f"{saudacao} Segue nosso {self.meta.get('titulo', 'Encarte de Ofertas')}."
        msg_encoded = urllib.parse.quote(mensagem)

        if self.num_whats:
            url = f"https://api.whatsapp.com/send?phone={self.num_whats}&text={msg_encoded}"
            webbrowser.open(url)
        else:
            webbrowser.open("https://web.whatsapp.com")

    def abrir_pasta(self):
        caminho_target = self.lista_paginas[self.indice_atual] if self.lista_paginas else self.jpg_path
        if os.path.exists(caminho_target):
            os.system(f'explorer /select,"{os.path.abspath(caminho_target)}"')
        elif os.path.exists(os.path.dirname(caminho_target)):
            os.system(f'explorer "{os.path.abspath(os.path.dirname(caminho_target))}"')

if __name__ == "__main__":
    param1 = sys.argv[1] if len(sys.argv) > 1 else ""
    param2 = sys.argv[2] if len(sys.argv) > 2 else ""

    if param1 and param2:
        pasta_param = param1
        arquivo_jpg = param2
    elif param1:
        if param1.lower().endswith(('.jpg', '.jpeg')):
            arquivo_jpg = param1
            pasta_param = os.path.dirname(param1)
        else:
            pasta_param = param1
            arquivo_jpg = os.path.join(pasta_param, "CATALOGO_OESTE_PHARMA.JPG")
    else:
        pasta_param = os.getcwd()
        arquivo_jpg = os.path.join(pasta_param, "CATALOGO_OESTE_PHARMA.JPG")

    root = tk.Tk()
    app = AppVisualizador(root, pasta_parametros=pasta_param, jpg_path=arquivo_jpg)
    root.mainloop()
