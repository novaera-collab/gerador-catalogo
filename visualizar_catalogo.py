import sys
import os
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

def ler_metadados_csv(csv_path):
    meta = {'fone': '', 'rodape': '', 'titulo': '', 'saida_jpg': '', 'validade': '', 'logo': ''}
    if not os.path.exists(csv_path):
        return meta

    try:
        with open(csv_path, mode='r', encoding='latin-1') as f:
            linhas = [line.strip() for line in f if line.strip()]
    except:
        return meta

    for linha in linhas:
        colunas = linha.split(';')
        col0 = colunas[0].lower().strip()
        if col0 in ['codigo', 'fco', 'code']:
            break
        if len(colunas) > 1:
            meta[col0] = colunas[1].strip()
            
    return meta

def limpar_numero_whatsapp(fone_raw):
    apenas_numeros = "".join(c for c in fone_raw if c.isdigit())
    if not apenas_numeros:
        return ""
    if len(apenas_numeros) in [10, 11]:
        return "55" + apenas_numeros
    return apenas_numeros

class AppVisualizador:
    def __init__(self, root, csv_path):
        self.root = root
        self.csv_path = csv_path
        self.meta = ler_metadados_csv(csv_path)
        
        self.jpg_path = ""
        if len(sys.argv) > 2 and sys.argv[2].strip():
            self.jpg_path = sys.argv[2].strip()
        elif self.meta.get('saida_jpg'):
            self.jpg_path = self.meta.get('saida_jpg')
        else:
            user_profile = os.environ.get('USERPROFILE', 'C:\\')
            self.jpg_path = os.path.join(user_profile, 'Downloads', 'CATALOGO_OESTE_PHARMA.JPG')

        self.num_whats = limpar_numero_whatsapp(self.meta.get('fone', ''))

        self.root.title("Visualizador de Encarte - Oeste Pharma")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f0f0f0")
        
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

        # MENSAGEM POP-UP MOSTRANDO DIRETÓRIO E ARQUIVO
        diretorio, nome_arquivo = os.path.split(os.path.abspath(self.jpg_path))
        existe = "ENCONTRADO" if os.path.exists(self.jpg_path) else "NÃO ENCONTRADO"
        
        messagebox.showinfo(
            "Abrindo Arquivo",
            f"Diretório:\n{diretorio}\n\n"
            f"Arquivo:\n{nome_arquivo}\n\n"
            f"Status do Arquivo: {existe}"
        )

        # PAINEL SUPERIOR
        frame_topo = tk.Frame(self.root, bg="#22702C")
        frame_topo.pack(fill="x", side="top", ipady=10)

        lbl_titulo = tk.Label(frame_topo, text="Encarte Gerado com Sucesso!", font=("Arial", 14, "bold"), fg="white", bg="#22702C")
        lbl_titulo.pack(side="left", padx=15)

        btn_whats = tk.Button(
            frame_topo, 
            text="📱 Abrir WhatsApp", 
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
            self.canvas.create_text(500, 350, text=f"Arquivo JPG não encontrado em:\n{self.jpg_path}", fill="white", font=("Arial", 14), justify="center")

    def carregar_imagem(self):
        self.pil_img = Image.open(self.jpg_path)
        
        img_w, img_h = self.pil_img.size
        max_w, max_h = 960, 640
        ratio = min(max_w/img_w, max_h/img_h)
        novo_tamanho = (int(img_w * ratio), int(img_h * ratio))

        img_resized = self.pil_img.resize(novo_tamanho, Image.Resampling.LANCZOS)
        self.tk_img = ImageTk.PhotoImage(img_resized)

        self.canvas.create_image(500, 330, image=self.tk_img, anchor="center")

    def abrir_whatsapp(self):
        if not self.num_whats:
            messagebox.showwarning("WhatsApp", "Nenhum número de telefone válido encontrado!")
            return

        mensagem = f"Olá! Segue nosso {self.meta.get('titulo', 'Encarte de Ofertas')}."
        msg_encoded = urllib.parse.quote(mensagem)
        url = f"https://api.whatsapp.com/send?phone={self.num_whats}&text={msg_encoded}"
        webbrowser.open(url)

    def abrir_pasta(self):
        if os.path.exists(self.jpg_path):
            os.system(f'explorer /select,"{os.path.abspath(self.jpg_path)}"')

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else "F:\\UNICO\\ENCARTE\\DADOS_CATALOGO.CSV"

    root = tk.Tk()
    app = AppVisualizador(root, csv_file)
    root.mainloop()
