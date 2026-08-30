import sys
import os
import io
import csv
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
        # Fallback usando PowerShell se pywin32 não estiver instalado
        try:
            cmd = f'powershell -command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Clipboard]::SetImage([System.Drawing.Image]::FromFile(\'{caminho_img}\'))"'
            os.system(cmd)
            return True
        except Exception:
            return False

def ler_metadados_csv(csv_path):
    """
    Lê o cabeçalho/metadados do CSV gerado.
    Identifica o campo 'contato_whatsapp' da consulta SQL.
    """
    meta = {'fone': '', 'nome_contato': '', 'titulo': 'Encarte de Ofertas', 'saida_jpg': ''}
    if not os.path.exists(csv_path):
        return meta

    try:
        # Tenta ler em UTF-8 (padrão) ou Latin-1 como fallback
        for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
            try:
                with open(csv_path, mode='r', encoding=enc) as f:
                    reader = csv.DictReader(f, delimiter=',')
                    # Limpa espaços e lowercase nos nomes das colunas
                    if reader.fieldnames:
                        field_map = {col.strip().lower().replace('\ufeff', ''): col for col in reader.fieldnames}
                        
                        first_row = next(reader, None)
                        if first_row and 'contato_whatsapp' in field_map:
                            raw_whatsapp = first_row.get(field_map['contato_whatsapp'], '').strip()
                            
                            # Trata formato "Nome - (XX) 99999-9999" ou apenas "(XX) 99999-9999"
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
        
        # Define caminho do CSV associado para ler os metadados de contato
        base_path = os.path.splitext(self.jpg_path)[0] if self.jpg_path else ""
        self.csv_path = f"{base_path}.csv" if base_path else ""

        self.meta = ler_metadados_csv(self.csv_path)
        self.num_whats = limpar_numero_whatsapp(self.meta.get('fone', ''))

        self.root.title("Visualizador de Encarte - Oeste Pharma")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f0f0f0")
        
        # Traz a janela para frente
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        # PAINEL SUPERIOR
        frame_topo = tk.Frame(self.root, bg="#22702C")
        frame_topo.pack(fill="x", side="top", ipady=10)

        lbl_titulo = tk.Label(frame_topo, text="Encarte Gerado com Sucesso!", font=("Arial", 14, "bold"), fg="white", bg="#22702C")
        lbl_titulo.pack(side="left", padx=15)

        btn_whats = tk.Button(
            frame_topo, 
            text="📱 Copiar Imagem e Abrir WhatsApp", 
            font=("Arial", 11, "bold"), 
            bg="#25D366", 
            fg="white", 
            activebackground="#1EBE5D",
            cursor="hand2",
            command=self.abrir_whatsapp
        )
        btn_whats.pack(side="right", padx=15)

        btn_pasta = tk.Button(
            frame_topo, 
            text="📁 Abrir Pasta", 
            font=("Arial", 11), 
            bg="#ffffff", 
            fg="#333333", 
            cursor="hand2",
            command=self.abrir_pasta
        )
        btn_pasta.pack(side="right", padx=5)

        # PAINEL CENTRAL
        self.canvas = tk.Canvas(self.root, bg="#333333")
        self.canvas.pack(fill="both", expand=True)

        if os.path.exists(self.jpg_path):
            self.carregar_imagem()
        else:
            self.canvas.create_text(
                500, 350, 
                text=f"Arquivo JPG não encontrado em:\n{self.jpg_path}", 
                fill="white", 
                font=("Arial", 14), 
                justify="center"
            )

    def carregar_imagem(self):
        self.pil_img = Image.open(self.jpg_path)
        
        img_w, img_h = self.pil_img.size
        max_w, max_h = 960, 640
        ratio = min(max_w / img_w, max_h / img_h)
        novo_tamanho = (int(img_w * ratio), int(img_h * ratio))

        img_resized = self.pil_img.resize(novo_tamanho, Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img_resized)

        self.canvas.create_image(500, 330, image=self.tk_img, anchor="center")

    def abrir_whatsapp(self):
        # 1. Copia a imagem para a área de transferência do Windows (CTRL+V)
        copiou = copiar_imagem_para_clipboard(self.jpg_path)

        if copiou:
            messagebox.showinfo(
                "Imagem Copiada!", 
                "A imagem do encarte foi COPIADA para a memória!\n\n"
                "Ao abrir o WhatsApp, basta pressionar CTRL + V na conversa para colar a imagem!"
            )

        # 2. Abre a conversa direta no WhatsApp
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
        if os.path.exists(self.jpg_path):
            os.system(f'explorer /select,"{os.path.abspath(self.jpg_path)}"')
        elif os.path.exists(os.path.dirname(self.jpg_path)):
            os.system(f'explorer "{os.path.abspath(os.path.dirname(self.jpg_path))}"')

if __name__ == "__main__":
    # Tratamento dos argumentos da chamada de sistema:
    # arg 1: Pasta de parâmetros / saída
    # arg 2: Caminho completo do arquivo JPG gerado
    pasta_param = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    arquivo_jpg = sys.argv[2] if len(sys.argv) > 2 else os.path.join(pasta_param, "catalogo_encarte.jpg")

    root = tk.Tk()
    app = AppVisualizador(root, pasta_parametros=pasta_param, jpg_path=arquivo_jpg)
    root.mainloop()
