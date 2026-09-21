import sys
import os
import io
import csv
import re
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk, ImageDraw

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

def criar_imagem_degrade(largura, altura, cor_topo="#120024", cor_fim="#5B0098"):
    """Gera uma imagem de fundo em degradê vertical para o Tkinter"""
    base = Image.new("RGB", (largura, altura))
    draw = ImageDraw.Draw(base)
    
    r1, g1, b1 = int(cor_topo[1:3], 16), int(cor_topo[3:5], 16), int(cor_topo[5:7], 16)
    r2, g2, b2 = int(cor_fim[1:3], 16), int(cor_fim[3:5], 16), int(cor_fim[5:7], 16)

    for y in range(altura):
        r = int(r1 + (r2 - r1) * (y / altura))
        g = int(g1 + (g2 - g1) * (y / altura))
        b = int(b1 + (b2 - b1) * (y / altura))
        draw.line([(0, y), (largura, y)], fill=(r, g, b))
        
    return ImageTk.PhotoImage(base)

class AppVisualizador:
    def __init__(self, root, pasta_parametros="", jpg_path=""):
        self.root = root
        self.jpg_path = jpg_path
        
        # Mapeamento de páginas geradas
        self.lista_paginas = []
        self.indice_atual = 0

        # Define caminho do CSV associado para ler os metadados
        base_path = os.path.splitext(self.jpg_path)[0] if self.jpg_path else ""
        self.csv_path = f"{base_path}.csv" if base_path else ""

        self.meta = ler_metadados_csv(self.csv_path)
        self.num_whats = limpar_numero_whatsapp(self.meta.get('fone', ''))

        self.root.title("Zé do Encarte - Visualizador e Gerador de Ofertas")
        self.root.geometry("1180x800")
        self.root.configure(bg="#120024")
        
        # Traz a janela para a frente
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        # Atalhos do teclado
        self.root.bind("<Left>", lambda event: self.pagina_anterior())
        self.root.bind("<Right>", lambda event: self.proxima_pagina())
        self.root.bind("<F5>", lambda event: self.atualizar_paginas())

        # PAINEL SUPERIOR (TEMA ROXO/PINK ZÉ DO ENCARTE)
        self.frame_topo = tk.Frame(self.root, bg="#120024")
        self.frame_topo.pack(fill="x", side="top", ipady=6)

        # Título da Marca em Pink Neon
        lbl_marca = tk.Label(
            self.frame_topo, text="Zé do Encarte", font=("Segoe UI", 16, "bold"), 
            fg="#FF007F", bg="#120024"
        )
        lbl_marca.pack(side="left", padx=(15, 5))

        lbl_status = tk.Label(
            self.frame_topo, text="• Encarte Gerado!", font=("Segoe UI", 10, "bold"), 
            fg="#00FF88", bg="#120024"
        )
        lbl_status.pack(side="left", padx=5)

        # BOTÕES HARMONIZADOS COM A PALETA
        btn_whats = tk.Button(
            self.frame_topo, 
            text="💬 Copiar e Abrir Whats", 
            font=("Segoe UI", 9, "bold"), 
            bg="#FF007F", 
            fg="white", 
            activebackground="#E0006F",
            activeforeground="white",
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_whatsapp
        )
        btn_whats.pack(side="right", padx=8)

        btn_copiar = tk.Button(
            self.frame_topo, 
            text="📋 Apenas Copiar", 
            font=("Segoe UI", 9, "bold"), 
            bg="#3B0066", 
            fg="#FFB6C1", 
            activebackground="#FF007F",
            activeforeground="white",
            bd=1,
            relief="solid",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.apenas_copiar_imagem
        )
        btn_copiar.pack(side="right", padx=4)

        btn_atualizar = tk.Button(
            self.frame_topo, 
            text="🔄 Atualizar (F5)", 
            font=("Segoe UI", 9, "bold"), 
            bg="#3B0066", 
            fg="#FFFFFF", 
            activebackground="#FF007F",
            activeforeground="white",
            bd=1,
            relief="solid",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.atualizar_paginas
        )
        btn_atualizar.pack(side="right", padx=4)

        btn_pasta = tk.Button(
            self.frame_topo, 
            text="📁 Abrir Pasta", 
            font=("Segoe UI", 9), 
            bg="#2A0042", 
            fg="#E0E0E0", 
            activebackground="#3B0066",
            activeforeground="white",
            bd=1,
            relief="solid",
            padx=8,
            pady=3,
            cursor="hand2",
            command=self.abrir_pasta
        )
        btn_pasta.pack(side="right", padx=4)

        # BARRA DE NAVEGAÇÃO DE PÁGINAS (ROXO ESCURO / INTERMÉDIO)
        frame_nav = tk.Frame(self.root, bg="#1D0036")
        frame_nav.pack(fill="x", side="top", ipady=3)

        self.btn_ant = tk.Button(
            frame_nav, text="◀ Anterior", font=("Segoe UI", 9, "bold"), bg="#3B0066", fg="#FFFFFF",
            activebackground="#FF007F", activeforeground="white", bd=0, padx=10,
            state="disabled", command=self.pagina_anterior, cursor="hand2"
        )
        self.btn_ant.pack(side="left", padx=15)

        self.lbl_paginacao = tk.Label(
            frame_nav, text="Carregando...", font=("Segoe UI", 10, "bold"), fg="#FFB6C1", bg="#1D0036"
        )
        self.lbl_paginacao.pack(side="left", expand=True)

        self.btn_prox = tk.Button(
            frame_nav, text="Próximo ▶", font=("Segoe UI", 9, "bold"), bg="#3B0066", fg="#FFFFFF",
            activebackground="#FF007F", activeforeground="white", bd=0, padx=10,
            state="disabled", command=self.proxima_pagina, cursor="hand2"
        )
        self.btn_prox.pack(side="right", padx=15)

        # PAINEL CENTRAL DE VISUALIZAÇÃO COM CANVAS
        self.canvas = tk.Canvas(self.root, bg="#120024", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.redimensionar_fundo)

        self.fundo_img_tk = None

        # CORREÇÃO DO BUG: Força atualização automática ao inicializar a interface
        self.root.after(100, self.atualizar_paginas)

    def redimensionar_fundo(self, event):
        """Atualiza o fundo degradê quando a janela é redimensionada"""
        w, h = event.width, event.height
        if w > 10 and h > 10:
            self.fundo_img_tk = criar_imagem_degrade(w, h, cor_topo="#120024", cor_fim="#4A0078")
            self.atualizar_visualizacao()

    def localizar_paginas_geradas(self, caminho_base):
        """Captura todas as páginas e fallback inteligente se não encontrar pelo nome exato."""
        if not caminho_base:
            return []

        nome_sem_ext = os.path.splitext(caminho_base)[0]
        nome_limpo = re.sub(r'_\d+$', '', nome_sem_ext)
        pasta = os.path.dirname(caminho_base) or os.getcwd()

        arquivos_encontrados = []
        if os.path.exists(pasta):
            for f in os.listdir(pasta):
                if f.lower().endswith(('.jpg', '.jpeg')):
                    caminho_completo = os.path.join(pasta, f)
                    sem_ext = os.path.splitext(caminho_completo)[0]
                    
                    if sem_ext == nome_limpo or sem_ext.startswith(nome_limpo + "_"):
                        arquivos_encontrados.append(caminho_completo)

            # FALLBACK: Se não achar pelo nome do parâmetro, pega os JPGs recentes da pasta
            if not arquivos_encontrados:
                for f in os.listdir(pasta):
                    if f.lower().endswith(('.jpg', '.jpeg')):
                        arquivos_encontrados.append(os.path.join(pasta, f))

        def extrair_ordem(caminho):
            base = os.path.splitext(caminho)[0]
            match = re.search(r'_(\d+)$', base)
            if match:
                return int(match.group(1))
            return 0

        arquivos_encontrados.sort(key=extrair_ordem)
        
        resultado_final = []
        for item in arquivos_encontrados:
            if item not in resultado_final:
                resultado_final.append(item)

        return resultado_final

    def atualizar_paginas(self):
        """Recarrega a lista de imagens da pasta e atualiza a exibição"""
        novas_paginas = self.localizar_paginas_geradas(self.jpg_path)
        self.lista_paginas = novas_paginas
        
        if self.indice_atual >= len(self.lista_paginas):
            self.indice_atual = max(0, len(self.lista_paginas) - 1)
            
        self.atualizar_visualizacao()

    def atualizar_visualizacao(self):
        """Redesenha a tela conforme a página selecionada"""
        self.canvas.delete("all")

        # Desenha o fundo degradê
        w_canv = self.canvas.winfo_width()
        h_canv = self.canvas.winfo_height()
        
        if self.fundo_img_tk:
            self.canvas.create_image(0, 0, image=self.fundo_img_tk, anchor="nw")

        if not self.lista_paginas:
            cx = w_canv // 2 if w_canv > 50 else 590
            cy = h_canv // 2 if h_canv > 50 else 350
            self.canvas.create_text(
                cx, cy, 
                text=f"Aguardando arquivo de encarte em:\n{self.jpg_path}\n\nPressione F5 para atualizar.", 
                fill="#FFB6C1", font=("Segoe UI", 12), justify="center"
            )
            self.lbl_paginacao.config(text="Página 0 de 0")
            self.btn_ant.config(state="disabled")
            self.btn_prox.config(state="disabled")
            return

        total = len(self.lista_paginas)
        self.lbl_paginacao.config(text=f"Página {self.indice_atual + 1} de {total}")

        self.btn_ant.config(state="normal" if self.indice_atual > 0 else "disabled")
        self.btn_prox.config(state="normal" if self.indice_atual < total - 1 else "disabled")

        caminho_atual = self.lista_paginas[self.indice_atual]
        try:
            self.pil_img = Image.open(caminho_atual)
            img_w, img_h = self.pil_img.size
            
            max_w = max(300, w_canv - 60) if w_canv > 60 else 1050
            max_h = max(300, h_canv - 40) if h_canv > 40 else 650
            
            ratio = min(max_w / img_w, max_h / img_h)
            novo_tamanho = (int(img_w * ratio), int(img_h * ratio))

            img_resized = self.pil_img.resize(novo_tamanho, Image.Resampling.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img_resized)

            cx = w_canv // 2 if w_canv > 50 else 590
            cy = h_canv // 2 if h_canv > 50 else 330
            self.canvas.create_image(cx, cy, image=self.tk_img, anchor="center")
        except Exception as e:
            cx = w_canv // 2 if w_canv > 50 else 590
            cy = h_canv // 2 if h_canv > 50 else 350
            self.canvas.create_text(
                cx, cy, text=f"Erro ao carregar imagem:\n{e}", fill="#FF007F", font=("Segoe UI", 12)
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
        """Apenas copia a página atual para a área de transferência."""
        if not self.lista_paginas:
            return

        caminho_atual = self.lista_paginas[self.indice_atual]
        copiou = copiar_imagem_para_clipboard(caminho_atual)

        if copiou:
            messagebox.showinfo(
                "Imagem Copiada!", 
                f"A Página {self.indice_atual + 1} foi copiada!\n\n"
                "Pressione CTRL + V em qualquer conversa para colar."
            )

    def abrir_whatsapp(self):
        if not self.lista_paginas:
            return

        caminho_atual = self.lista_paginas[self.indice_atual]
        copiou = copiar_imagem_para_clipboard(caminho_atual)

        if self.indice_atual == 0:
            total_paginas = len(self.lista_paginas)
            msg_extra = ""
            if total_paginas > 1:
                msg_extra = f"\n\n💡 O encarte possui {total_paginas} páginas. Navegue no programa e copie as demais!"

            if copiou:
                messagebox.showinfo(
                    "Página 1 Copiada!", 
                    "A Página 1 foi copiada para a memória!\n\n"
                    "O WhatsApp será aberto. Pressione CTRL + V para colar a imagem."
                    f"{msg_extra}"
                )

            nome_contato = self.meta.get('nome_contato', '')
            saudacao = f"Olá {nome_contato}!" if nome_contato else "Olá!"
            mensagem = f"{saudacao} Segue nosso {self.meta.get('titulo', 'Encarte de Ofertas')}."
            msg_encoded = urllib.parse.quote(mensagem)

            if self.num_whats:
                url = f"https://api.whatsapp.com/send?phone={self.num_whats}&text={msg_encoded}"
                webbrowser.open(url)
            else:
                webbrowser.open("https://web.whatsapp.com")
        else:
            if copiou:
                messagebox.showinfo(
                    "Página Copiada!", 
                    f"A Página {self.indice_atual + 1} foi copiada!\n\n"
                    "Cole (CTRL+V) diretamente na conversa do WhatsApp."
                )

    def abrir_pasta(self):
        caminho_target = self.lista_paginas[self.indice_atual] if self.lista_paginas else self.jpg_path
        if os.path.exists(caminho_target):
            os.system(f'explorer /select,"{os.path.abspath(caminho_target)}"')
        elif os.path.exists(os.path.dirname(caminho_target)):
            os.system(f'explorer "{os.path.abspath(os.path.dirname(caminho_target))}"')

if __name__ == "__main__":
    param1 = sys.argv[1] if len(sys.argv) > 1 else ""
    param2 = sys.argv[2] if len(sys.argv) > 1 and sys.argv[2] != "" else ""

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
