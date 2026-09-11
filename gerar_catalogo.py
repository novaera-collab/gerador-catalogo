import sys
import io
# Correção segura para encoding UTF-8 em Windows/PyInstaller
if sys.stdout is not None:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except AttributeError:
        pass

if sys.stderr is not None:
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        pass

import csv
import os
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black, gray
from PIL import Image as PILImage

class GeradorEncarteJPG:
    def __init__(self, csv_path, output_folder="encartes_jpg"):
        self.csv_path = csv_path
        self.output_folder = output_folder
        self.config = {}
        
        # Tamanho ideal para WhatsApp Feed (4:5 ratio) - Alta resolução
        self.LARGURA = 1080
        self.ALTURA = 1350
        
        os.makedirs(output_folder, exist_ok=True)

    def carregar_configuracoes(self):
        """Lê as configurações das primeiras linhas do CSV"""
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if ';' not in line or i > 20: 
                    break
                parts = line.strip().split(';')
                if len(parts) == 2:
                    self.config[parts[0].strip()] = parts[1].strip()

    def carregar_produtos(self):
        """Separa produtos em Destaques (S) e Normais (N)"""
        destaques, normais = [], []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                # Ignora linhas que não são produtos válidos
                if 'codigo' not in row or not row['codigo'].strip().isdigit(): 
                    continue
                    
                produto = {k: v.strip() for k, v in row.items()}
                
                if produto.get('destaque', 'N').upper() == 'S':
                    destaques.append(produto)
                else:
                    normais.append(produto)
                    
        # Limita a 3 destaques por página para manter o layout limpo
        return destaques[:3], normais

    def desenhar_card_destaque(self, c, x, y, largura, altura, produto):
        """Desenha um card grande de produto em destaque"""
        cor_tarja = HexColor(self.config.get('cor_grid_preco', '#000000'))
        
        # Fundo branco com borda suave
        c.setFillColor(white)
        c.setStrokeColor(HexColor('#CCCCCC'))
        c.rect(x, y, largura, altura, fill=1, stroke=1)
        
        # Foto centralizada na parte superior
        foto_y = y + altura - 350
        foto_w, foto_h = 300, 300
        foto_x = x + (largura - foto_w) / 2
        
        if os.path.exists(produto['foto']):
            try:
                c.drawImage(produto['foto'], foto_x, foto_y, foto_w, foto_h, preserveAspectRatio=True)
            except Exception: 
                pass
        else:
            # Placeholder cinza se a foto não existir
            c.setFillColor(gray)
            c.rect(foto_x, foto_y, foto_w, foto_h, fill=1)
            
        # Código e Marca no topo do card
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(black)
        c.drawString(x + 30, y + altura - 60, f"CÓD: {produto['codigo']}")
        
        c.setFont("Helvetica", 18)
        c.setFillColor(gray)
        c.drawRightString(x + largura - 30, y + altura - 60, produto['marca'])
        
        # Descrição do produto
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(black)
        desc = produto['descricao'][:60] + "..." if len(produto['descricao']) > 60 else produto['descricao']
        c.drawString(x + 30, y + 250, desc)
        
        # Tarja de Preço arredondada
        tarja_h = 90
        c.setFillColor(cor_tarja)
        c.roundRect(x + 20, y + 40, largura - 40, tarja_h, 15, fill=1)
        
        preco_limpo = produto['preco'].replace('R$', '').strip()
        c.setFont("Helvetica-Bold", 42)
        c.setFillColor(white)
        c.drawCentredString(x + largura/2, y + 40 + tarja_h/2 - 12, f"POR {preco_limpo}")

    def desenhar_card_normal(self, c, x, y, largura, altura, produto):
        """Desenha card menor para produtos da grade secundária"""
        cor_tarja = HexColor(self.config.get('cor_grid_tarja', '#70AA87'))
        
        c.setFillColor(white)
        c.setStrokeColor(HexColor('#DDDDDD'))
        c.rect(x, y, largura, altura, fill=1, stroke=1)
        
        # Foto pequena
        foto_w, foto_h = 180, 180
        foto_x = x + (largura - foto_w) / 2
        foto_y = y + altura - 120
        
        if os.path.exists(produto['foto']):
            try:
                c.drawImage(produto['foto'], foto_x, foto_y, foto_w, foto_h, preserveAspectRatio=True)
            except Exception: 
                pass
            
        # Descrição curta
        c.setFont("Helvetica", 16)
        c.setFillColor(black)
        desc = produto['descricao'][:40] + "..." if len(produto['descricao']) > 40 else produto['descricao']
        c.drawString(x + 15, y + 200, desc)
        
        # Tarja de preço menor
        tarja_h = 55
        c.setFillColor(cor_tarja)
        c.roundRect(x + 10, y + 20, largura - 20, tarja_h, 8, fill=1)
        
        preco_limpo = produto['preco'].replace('R$', '').strip()
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(white)
        c.drawCentredString(x + largura/2, y + 20 + tarja_h/2 - 6, preco_limpo)

    def desenhar_cabecalho(self, c):
        """Desenha a faixa superior verde com logo e título"""
        cor_header = HexColor(self.config.get('cor_tit_rodape', '#1B5E20'))
        c.setFillColor(cor_header)
        c.rect(0, self.ALTURA - 200, self.LARGURA, 200, fill=1)
        
        # Logo à esquerda
        logo_path = self.config.get('cabecalho_logo', '')
        if os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, 40, self.ALTURA - 160, 140, 140, preserveAspectRatio=True)
            except Exception: 
                pass
            
        # Título centralizado
        c.setFont("Helvetica-Bold", 48)
        c.setFillColor(white)
        titulo = self.config.get('titulo', 'OFERTAS DA SEMANA').upper()
        c.drawCentredString(self.LARGURA / 2, self.ALTURA - 100, titulo)
        
        # Site à direita
        c.setFont("Helvetica", 22)
        site = self.config.get('cabecalho_site', '')
        c.drawRightString(self.LARGURA - 40, self.ALTURA - 100, site)

    def desenhar_rodape(self, c):
        """Desenha a faixa inferior com contatos e validade"""
        cor_footer = HexColor(self.config.get('cor_tit_rodape', '#1B5E20'))
        rodape_h = 140
        c.setFillColor(cor_footer)
        c.rect(0, 0, self.LARGURA, rodape_h, fill=1)
        
        contato = self.config.get('rodape_contato', '')
        fone = self.config.get('rodape_fone', '')
        validade = self.config.get('rodape_validade', '')
        tabela = self.config.get('rodape_tabela', '')
        
        texto_principal = f"{contato} | {fone}"
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(white)
        c.drawCentredString(self.LARGURA / 2, rodape_h - 40, texto_principal)
        
        subtexto = f"{validade} | {tabela}"
        c.setFont("Helvetica", 16)
        c.drawCentredString(self.LARGURA / 2, rodape_h - 75, subtexto)

    def gerar_pagina(self, destaques, normais, pagina_num):
        """Monta e salva uma única página JPG"""
        nome_arquivo = os.path.join(self.output_folder, f"encarte_pag{pagina_num}.jpg")
        c = canvas.Canvas(nome_arquivo, pagesize=(self.LARGURA, self.ALTURA))
        
        # Fundo branco base
        c.setFillColor(white)
        c.rect(0, 0, self.LARGURA, self.ALTURA, fill=1)
        
        self.desenhar_cabecalho(c)
        
        # --- Área de Destaques (Topo) ---
        y_destaque = self.ALTURA - 280
        card_largura = 340
        espacamento = 30
        # Centraliza horizontalmente os 3 cards
        x_inicio = (self.LARGURA - (3 * card_largura + 2 * espacamento)) / 2
        
        for i, prod in enumerate(destaques):
            x = x_inicio + i * (card_largura + espacamento)
            self.desenhar_card_destaque(c, x, y_destaque, card_largura, 550, prod)
            
        # --- Área de Produtos Normais (Grid 3x3 abaixo) ---
        y_normal_start = y_destaque - 600
        card_norm_largura = 340
        card_norm_altura = 350
        
        idx = 0
        # Gera até 3 linhas de 3 produtos (9 produtos por página secundária)
        for row in range(3):
            for col in range(3):
                if idx < len(normais):
                    x = x_inicio + col * (card_norm_largura + espacamento)
                    y = y_normal_start - row * (card_norm_altura + 30)
                    self.desenhar_card_normal(c, x, y, card_norm_largura, card_norm_altura, normais[idx])
                    idx += 1
                    
        self.desenhar_rodape(c)
        c.save()
        print(f"[OK] Página {pagina_num} gerada: {nome_arquivo}")

    def gerar(self):
        """Ponto de entrada principal do gerador"""
        if not os.path.exists(self.csv_path):
            print(f"[ERRO] Arquivo CSV não encontrado: {self.csv_path}")
            return

        self.carregar_configuracoes()
        destaques, normais = self.carregar_produtos()
        
        # A primeira página sempre tem os destaques + primeiros 9 normais
        produtos_por_pagina = 9
        total_paginas = max(1, (len(normais) + produtos_por_pagina - 1) // produtos_por_pagina)
        
        for p in range(total_paginas):
            inicio = p * produtos_por_pagina
            fim = inicio + produtos_por_pagina
            
            # Destaques só aparecem na primeira página
            destaques_pagina = destaques if p == 0 else []
            
            self.gerar_pagina(destaques_pagina, normais[inicio:fim], p + 1)
            
        print("\n[SUCESSO] Todos os encartes foram gerados na pasta 'encartes_jpg'!")


# === EXECUÇÃO ===
if __name__ == "__main__":
    CSV_PATH = "encarte_agosto_2026.csv" 
    
    gerador = GeradorEncarteJPG(CSV_PATH)
    gerador.gerar()
