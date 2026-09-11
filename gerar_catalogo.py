import csv
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black, gray
from PIL import Image as PILImage
from io import BytesIO

class GeradorEncarteJPG:
    def __init__(self, csv_path, output_folder="encartes_jpg"):
        self.csv_path = csv_path
        self.output_folder = output_folder
        self.config = {}
        
        # Tamanho ideal para WhatsApp Feed (4:5 ratio)
        self.LARGURA = 1080
        self.ALTURA = 1350
        
        os.makedirs(output_folder, exist_ok=True)

    def carregar_configuracoes(self):
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if ';' not in line or i > 15: break
                parts = line.strip().split(';')
                if len(parts) == 2:
                    self.config[parts[0].strip()] = parts[1].strip()

    def carregar_produtos(self):
        destaques, normais = [], []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                if 'codigo' not in row or not row['codigo'].isdigit(): continue
                produto = {k: v.strip() for k, v in row.items()}
                if produto.get('destaque', 'N').upper() == 'S':
                    destaques.append(produto)
                else:
                    normais.append(produto)
        return destaques[:3], normais

    def desenhar_card_destaque(self, c, x, y, largura, altura, produto):
        """Desenha um card de destaque no canvas"""
        cor_tarja = HexColor(self.config.get('cor_grid_preco', '#000000'))
        
        # Fundo branco com borda
        c.setFillColor(white)
        c.setStrokeColor(HexColor('#CCCCCC'))
        c.rect(x, y, largura, altura, fill=1, stroke=1)
        
        # Foto centralizada
        foto_y = y + altura - 100
        foto_w, foto_h = 200, 200
        foto_x = x + (largura - foto_w) / 2
        
        if os.path.exists(produto['foto']):
            try:
                c.drawImage(produto['foto'], foto_x, foto_y, foto_w, foto_h, preserveAspectRatio=True)
            except: pass
        else:
            c.setFillColor(gray)
            c.rect(foto_x, foto_y, foto_w, foto_h, fill=1)
            
        # Código e Marca
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(black)
        c.drawString(x + 20, y + altura - 40, f"CÓD: {produto['codigo']}")
        
        c.setFont("Helvetica", 12)
        c.setFillColor(gray)
        c.drawRightString(x + largura - 20, y + altura - 40, produto['marca'])
        
        # Descrição
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(black)
        desc = produto['descricao'][:50] + "..." if len(produto['descricao']) > 50 else produto['descricao']
        c.drawString(x + 20, y + 180, desc)
        
        # Tarja de Preço
        tarja_h = 70
        c.setFillColor(cor_tarja)
        c.roundRect(x + 10, y + 20, largura - 20, tarja_h, 10, fill=1)
        
        preco_limpo = produto['preco'].replace('R$', '').strip()
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(white)
        c.drawCentredString(x + largura/2, y + 20 + tarja_h/2 - 10, f"POR {preco_limpo}")

    def desenhar_card_normal(self, c, x, y, largura, altura, produto):
        """Desenha card menor para produtos normais"""
        cor_tarja = HexColor(self.config.get('cor_grid_tarja', '#70AA87'))
        
        c.setFillColor(white)
        c.setStrokeColor(HexColor('#DDDDDD'))
        c.rect(x, y, largura, altura, fill=1, stroke=1)
        
        # Foto
        foto_w, foto_h = 120, 120
        foto_x = x + (largura - foto_w) / 2
        foto_y = y + altura - 80
        
        if os.path.exists(produto['foto']):
            try:
                c.drawImage(produto['foto'], foto_x, foto_y, foto_w, foto_h, preserveAspectRatio=True)
            except: pass
            
        # Descrição curta
        c.setFont("Helvetica", 11)
        c.setFillColor(black)
        desc = produto['descricao'][:30] + "..." if len(produto['descricao']) > 30 else produto['descricao']
        c.drawString(x + 10, y + 140, desc)
        
        # Preço
        tarja_h = 40
        c.setFillColor(cor_tarja)
        c.roundRect(x + 5, y + 10, largura - 10, tarja_h, 5, fill=1)
        
        preco_limpo = produto['preco'].replace('R$', '').strip()
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(white)
        c.drawCentredString(x + largura/2, y + 10 + tarja_h/2 - 5, preco_limpo)

    def desenhar_cabecalho(self, c):
        cor_header = HexColor(self.config.get('cor_tit_rodape', '#1B5E20'))
        c.setFillColor(cor_header)
        c.rect(0, self.ALTURA - 150, self.LARGURA, 150, fill=1)
        
        # Logo
        logo_path = self.config.get('cabecalho_logo', '')
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, 30, self.ALTURA - 120, 100, 100, preserveAspectRatio=True)
            except: pass
            
        # Título
        c.setFont("Helvetica-Bold", 36)
        c.setFillColor(white)
        titulo = self.config.get('titulo', 'OFERTAS DA SEMANA').upper()
        c.drawCentredString(self.LARGURA / 2, self.ALTURA - 75, titulo)
        
        # Site
        c.setFont("Helvetica", 16)
        site = self.config.get('cabecalho_site', '')
        c.drawRightString(self.LARGURA - 30, self.ALTURA - 75, site)

    def desenhar_rodape(self, c):
        cor_footer = HexColor(self.config.get('cor_tit_rodape', '#1B5E20'))
        rodape_h = 100
        c.setFillColor(cor_footer)
        c.rect(0, 0, self.LARGURA, rodape_h, fill=1)
        
        contato = self.config.get('rodape_contato', '')
        fone = self.config.get('rodape_fone', '')
        validade = self.config.get('rodape_validade', '')
        tabela = self.config.get('rodape_tabela', '')
        
        texto = f"{contato} | {fone}"
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(white)
        c.drawCentredString(self.LARGURA / 2, rodape_h - 30, texto)
        
        subtexto = f"{valididade} | {tabela}"
        c.setFont("Helvetica", 12)
        c.drawCentredString(self.LARGURA / 2, rodape_h - 55, subtexto)

    def gerar_pagina(self, destaques, normais, pagina_num):
        nome_arquivo = os.path.join(self.output_folder, f"encarte_pag{pagina_num}.jpg")
        c = canvas.Canvas(nome_arquivo, pagesize=(self.LARGURA, self.ALTURA))
        
        # Fundo branco
        c.setFillColor(white)
        c.rect(0, 0, self.LARGURA, self.ALTURA, fill=1)
        
        self.desenhar_cabecalho(c)
        
        # Destaques (3 cards na linha superior)
        y_destaque = self.ALTURA - 200
        card_largura = 340
        espacamento = 30
        x_inicio = (self.LARGURA - (3 * card_largura + 2 * espacamento)) / 2
        
        for i, prod in enumerate(destaques):
            x = x_inicio + i * (card_largura + espacamento)
            self.desenhar_card_destaque(c, x, y_destaque, card_largura, 450, prod)
            
        # Produtos Normais (Grid 3x3 abaixo dos destaques)
        y_normal_start = y_destaque - 500
        card_norm_largura = 340
        card_norm_altura = 280
        
        idx = 0
        for row in range(3):
            for col in range(3):
                if idx < len(normais):
                    x = x_inicio + col * (card_norm_largura + espacamento)
                    y = y_normal_start - row * (card_norm_altura + 20)
                    self.desenhar_card_normal(c, x, y, card_norm_largura, card_norm_altura, normais[idx])
                    idx += 1
                    
        self.desenhar_rodape(c)
        c.save()
        print(f"✅ Página {pagina_num} gerada: {nome_arquivo}")

    def gerar(self):
        self.carregar_configuracoes()
        destaques, normais = self.carregar_produtos()
        
        # Divide normais em páginas de 9 produtos cada
        produtos_por_pagina = 9
        total_paginas = max(1, (len(normais) + produtos_por_pagina - 1) // produtos_por_pagina)
        
        for p in range(total_paginas):
            inicio = p * produtos_por_pagina
            fim = inicio + produtos_por_pagina
            self.gerar_pagina(destaques if p == 0 else [], normais[inicio:fim], p + 1)


# === EXECUÇÃO ===
if __name__ == "__main__":
    CSV_PATH = "encarte_agosto_2026.csv"
    
    if os.path.exists(CSV_PATH):
        gerador = GeradorEncarteJPG(CSV_PATH)
        gerador.gerar()
    else:
        print(f"❌ CSV não encontrado: {CSV_PATH}")
