import csv
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, Frame, PageTemplate
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.lib.colors import HexColor, white, black, gray
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from PIL import Image as PILImage

class GeradorEncartePromocional:
    def __init__(self, csv_path, output_path):
        self.csv_path = csv_path
        self.output_path = output_path
        self.doc = SimpleDocTemplate(
            output_path, 
            pagesize=A4,
            rightMargin=0.8*cm, 
            leftMargin=0.8*cm, 
            topMargin=0.5*cm, 
            bottomMargin=0.5*cm
        )
        self.story = []
        self.config = {}
        
        # Estilos de texto reutilizáveis
        styles = getSampleStyleSheet()
        self.style_titulo_destaque = ParagraphStyle(
            'TituloDestaque', parent=styles['Normal'], 
            fontSize=9, fontName='Helvetica-Bold', leading=10, spaceAfter=2
        )
        self.style_marca_destaque = ParagraphStyle(
            'MarcaDestaque', parent=styles['Normal'], 
            fontSize=7, fontName='Helvetica', textColor=gray, leading=8
        )
        self.style_preco_por = ParagraphStyle(
            'PrecoPor', parent=styles['Normal'], 
            fontSize=16, fontName='Helvetica-Bold', textColor=white, leading=16
        )
        self.style_codigo = ParagraphStyle(
            'Codigo', parent=styles['Normal'], 
            fontSize=7, fontName='Helvetica', textColor=gray
        )

    def carregar_configuracoes(self):
        """Lê as primeiras linhas do CSV para pegar configurações"""
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if ';' not in line or i > 15: break
                parts = line.strip().split(';')
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    self.config[key] = value

    def carregar_produtos(self):
        destaques = []
        normais = []
        header_encontrado = False
        
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                # Ignora linhas de configuração que possam ter sido lidas como produto
                if 'codigo' not in row or not row['codigo'].isdigit():
                    continue
                    
                produto = {
                    'codigo': row.get('codigo', ''),
                    'descricao': row.get('descricao', ''),
                    'marca': row.get('marca', ''),
                    'preco': row.get('preco', 'R$ 0,00'),
                    'foto': row.get('foto', ''),
                    'destaque': row.get('destaque', 'N').strip().upper()
                }
                
                if produto['destaque'] == 'S':
                    destaques.append(produto)
                else:
                    normais.append(produto)
                    
        return destaques[:3], normais  # Limita a 3 destaques conforme layout

    def criar_foto_placeholder(self, width, height):
        """Cria um placeholder cinza caso a foto não exista"""
        from io import BytesIO
        img = PILImage.new('RGB', (int(width), int(height)), color='#E0E0E0')
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        return Image(buffer, width=width, height=height)

    def criar_card_destaque(self, produto):
        """Cria o card grande do produto em destaque"""
        elements = []
        
        # Cabeçalho do card (Código + Marca)
        header_text = f"<b>{produto['codigo']}</b> &nbsp;&nbsp;&nbsp; {produto['marca']}"
        elements.append(Paragraph(header_text, self.style_codigo))
        elements.append(Spacer(1, 0.2*cm))
        
        # Foto
        foto_path = produto['foto']
        if os.path.exists(foto_path):
            try:
                img = Image(foto_path, width=5*cm, height=5*cm)
                img.hAlign = 'CENTER'
                elements.append(img)
            except Exception:
                elements.append(self.criar_foto_placeholder(5*cm, 5*cm))
        else:
            elements.append(self.criar_foto_placeholder(5*cm, 5*cm))
            
        elements.append(Spacer(1, 0.3*cm))
        
        # Descrição
        elements.append(Paragraph(produto['descricao'], self.style_titulo_destaque))
        elements.append(Paragraph(produto['marca'], self.style_marca_destaque))
        elements.append(Spacer(1, 0.3*cm))
        
        # Tarja de Preço
        cor_tarja = HexColor(self.config.get('cor_grid_preco', '#000000'))
        preco_limpo = produto['preco'].replace('R$', '').strip()
        
        # Simula a tarja com fundo colorido
        tarja_style = ParagraphStyle(
            'Tarja', parent=self.style_preco_por, 
            backColor=cor_tarja, borderColor=cor_tarja, borderWidth=0,
            borderRadius=5, padding=8, alignment=TA_CENTER
        )
        elements.append(Paragraph(f"POR {preco_limpo}", tarja_style))
        
        # Envolva tudo em um Frame/Table cell com borda sutil
        cell_content = Table([[elements]], colWidths=[6*cm])
        cell_style = TableStyle([
            ('BOX', (0,0), (-1,-1), 1, HexColor('#CCCCCC')),
            ('BACKGROUND', (0,0), (-1,-1), white),
            ('PADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ])
        cell_content.setStyle(cell_style)
        return cell_content

    def criar_card_normal(self, produto):
        """Cria o card menor para produtos normais"""
        elements = []
        
        # Foto pequena
        foto_path = produto['foto']
        if os.path.exists(foto_path):
            try:
                img = Image(foto_path, width=3*cm, height=3*cm)
                img.hAlign = 'CENTER'
                elements.append(img)
            except Exception:
                elements.append(self.criar_foto_placeholder(3*cm, 3*cm))
        else:
            elements.append(self.criar_foto_placeholder(3*cm, 3*cm))
            
        elements.append(Spacer(1, 0.2*cm))
        
        # Descrição curta
        desc_style = ParagraphStyle('DescNormal', parent=self.style_titulo_destaque, fontSize=7)
        elements.append(Paragraph(produto['descricao'][:40] + '...', desc_style))
        
        # Preço simples
        cor_tarja = HexColor(self.config.get('cor_grid_tarja', '#70AA87'))
        preco_limpo = produto['preco'].replace('R$', '').strip()
        preco_style = ParagraphStyle(
            'PrecoNormal', parent=self.style_preco_por, 
            fontSize=12, backColor=cor_tarja, padding=4, alignment=TA_CENTER
        )
        elements.append(Paragraph(preco_limpo, preco_style))
        
        cell = Table([[elements]], colWidths=[4*cm])
        cell.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, HexColor('#DDDDDD')),
            ('PADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        return cell

    def criar_cabecalho(self):
        titulo = self.config.get('titulo', 'OFERTAS DA SEMANA')
        cor_header = HexColor(self.config.get('cor_tit_rodape', '#1B5E20'))
        
        logo_path = self.config.get('cabecalho_logo', '')
        site = self.config.get('cabecalho_site', '')
        
        header_elements = []
        
        # Logo à esquerda
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, height=1.8*cm)
                header_elements.append([logo, '', ''])
            except:
                header_elements.append(['', '', ''])
        else:
            header_elements.append(['', '', ''])
            
        # Título centralizado
        title_style = ParagraphStyle(
            'HeaderTitle', fontSize=22, fontName='Helvetica-Bold', 
            textColor=white, alignment=TA_CENTER, leading=24
        )
        header_elements[0][1] = Paragraph(titulo.upper(), title_style)
        
        # Site à direita
        site_style = ParagraphStyle(
            'HeaderSite', fontSize=9, fontName='Helvetica', 
            textColor=white, alignment=TA_RIGHT
        )
        header_elements[0][2] = Paragraph(site, site_style)
        
        header_table = Table(header_elements, colWidths=[4*cm, 10*cm, 5*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_header),
            ('PADDING', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        return header_table

    def criar_rodape(self):
        cor_footer = HexColor(self.config.get('cor_tit_rodape', '#1B5E20'))
        contato = self.config.get('rodape_contato', '')
        fone = self.config.get('rodape_fone', '')
        validade = self.config.get('rodape_validade', '')
        tabela = self.config.get('rodape_tabela', '')
        
        footer_text = f"{contato} | {fone}<br/>{validade} | {tabela}"
        footer_style = ParagraphStyle(
            'Footer', fontSize=8, fontName='Helvetica', 
            textColor=white, alignment=TA_CENTER, leading=12
        )
        
        footer_table = Table([[Paragraph(footer_text, footer_style)]], colWidths=[19*cm])
        footer_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), cor_footer),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        return footer_table

    def gerar(self):
        self.carregar_configuracoes()
        destaques, normais = self.carregar_produtos()
        
        # 1. Cabeçalho
        self.story.append(self.criar_cabecalho())
        self.story.append(Spacer(1, 0.5*cm))
        
        # 2. Destaques (máx 3)
        if destaques:
            cards_destaque = [self.criar_card_destaque(p) for p in destaques]
            # Preenche com espaços vazios se tiver menos de 3
            while len(cards_destaque) < 3:
                cards_destaque.append(Spacer(1, 0))
                
            t_destaque = Table([cards_destaque], colWidths=[6.2*cm, 6.2*cm, 6.2*cm])
            t_destaque.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            self.story.append(t_destaque)
            self.story.append(Spacer(1, 0.5*cm))
        
        # 3. Produtos Normais em Grid de 4 colunas
        if normais:
            rows = []
            current_row = []
            for prod in normais:
                current_row.append(self.criar_card_normal(prod))
                if len(current_row) == 4:
                    rows.append(current_row)
                    current_row = []
            if current_row:
                # Completa a última linha com espaços
                while len(current_row) < 4:
                    current_row.append(Spacer(1, 0))
                rows.append(current_row)
                
            t_normais = Table(rows, colWidths=[4.5*cm, 4.5*cm, 4.5*cm, 4.5*cm])
            t_normais.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
            self.story.append(t_normais)
        
        self.story.append(Spacer(1, 1*cm))
        
        # 4. Rodapé
        self.story.append(self.criar_rodape())
        
        # Gera o PDF
        self.doc.build(self.story)
        print(f"✅ Encarte gerado com sucesso: {self.output_path}")


# === EXECUÇÃO ===
if __name__ == "__main__":
    CSV_PATH = "encarte_agosto_2026.csv"  # Ajuste o caminho do seu CSV
    OUTPUT_PATH = "encarte_promocional.pdf"
    
    if os.path.exists(CSV_PATH):
        gerador = GeradorEncartePromocional(CSV_PATH, OUTPUT_PATH)
        gerador.gerar()
    else:
        print(f"❌ Arquivo CSV não encontrado: {CSV_PATH}")
