import sys
import os
import csv
import traceback
from PIL import Image, ImageDraw, ImageFont

def log_erro(mensagem):
    try:
        with open("erro_gerador.log", "a", encoding="utf-8") as f:
            f.write(mensagem + "\n")
    except:
        pass

def gerar():
    try:
        csv_path = sys.argv[1] if len(sys.argv) > 1 else "F:\\UNICO\\ENCARTE\\DADOS_CATALOGO.CSV"
        
        if not os.path.exists(csv_path):
            log_erro(f"Arquivo CSV nao encontrado: {csv_path}")
            return

        # Ler metadados e produtos
        metadados = {}
        produtos = []

        linhas = []
        try:
            with open(csv_path, mode='r', encoding='latin-1') as f:
                linhas = [l.strip() for l in f if l.strip()]
        except:
            with open(csv_path, mode='r', encoding='utf-8') as f:
                linhas = [l.strip() for l in f if l.strip()]

        lendo_produtos = False
        headers = []

        for linha in linhas:
            colunas = [c.strip() for c in linha.split(';')]
            if not colunas:
                continue

            col0 = colunas[0].lower()
            if col0 in ['codigo', 'fco', 'code']:
                lendo_produtos = True
                headers = [c.lower() for c in colunas]
                continue

            if not lendo_produtos:
                if len(colunas) >= 2:
                    metadados[col0] = colunas[1]
            else:
                prod = {}
                for idx, val in enumerate(colunas):
                    if idx < len(headers):
                        prod[headers[idx]] = val
                produtos.append(prod)

        # Define caminho do JPG (veio no CSV ou usa fallback para 2º argumento ou Downloads)
        jpg_out_path = metadados.get('saida_jpg', '')
        if not jpg_out_path and len(sys.argv) > 2:
            jpg_out_path = sys.argv[2]
        if not jpg_out_path:
            user_profile = os.environ.get('USERPROFILE', 'C:\\')
            jpg_out_path = os.path.join(user_profile, 'Downloads', 'CATALOGO_OESTE_PHARMA.JPG')

        # Garantir pasta de destino
        out_dir = os.path.dirname(jpg_out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Dimensões da Imagem
        W, H = 1200, 1600
        img = Image.new('RGB', (W, H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)

        # Cabeçalho Verde
        draw.rectangle([(0, 0), (W, 180)], fill='#22702C')
        
        titulo = metadados.get('titulo', 'OESTE PHARMA - OFERTAS')
        fone = metadados.get('fone', '')
        rodape = metadados.get('rodape', '')

        try:
            font_titulo = ImageFont.truetype("arial.ttf", 48)
            font_sub = ImageFont.truetype("arial.ttf", 28)
            font_prod = ImageFont.truetype("arial.ttf", 22)
            font_preco = ImageFont.truetype("arial.ttf", 36)
        except:
            font_titulo = font_sub = font_prod = font_preco = ImageFont.load_default()

        draw.text((40, 40), titulo, fill='white', font=font_titulo)
        if fone:
            draw.text((40, 110), f"Contato: {fone}", fill='#E0E0E0', font=font_sub)

        # Grade de Produtos
        cols = 3
        margin_x = 40
        start_y = 220
        box_w = 360
        box_h = 320
        gap_x = 20
        gap_y = 20

        for i, p in enumerate(produtos[:12]):
            r = i // cols
            c = i % cols
            x = margin_x + c * (box_w + gap_x)
            y = start_y + r * (box_h + gap_y)

            draw.rectangle([(x, y), (x + box_w, y + box_h)], outline='#DDDDDD', width=2, fill='#FAFAFA')

            desc = p.get('descricao', p.get('nome', 'Produto'))
            preco = p.get('preco', p.get('valor', '0,00'))

            draw.text((x + 15, y + 15), desc[:25], fill='#333333', font=font_prod)
            
            img_p_path = p.get('imagem', p.get('foto', ''))
            if img_p_path and os.path.exists(img_p_path):
                try:
                    p_img = Image.open(img_p_path).convert("RGBA")
                    p_img.thumbnail((180, 180))
                    img.paste(p_img, (x + 90, y + 60), p_img)
                except:
                    pass

            draw.rectangle([(x + 20, y + box_h - 70), (x + box_w - 20, y + box_h - 15)], fill='#22702C')
            draw.text((x + 40, y + box_h - 65), f"R$ {preco}", fill='white', font=font_preco)

        # Rodapé Verde
        draw.rectangle([(0, H - 80), (W, H)], fill='#22702C')
        if rodape:
            draw.text((40, H - 55), rodape, fill='white', font=font_sub)

        img.save(jpg_out_path, "JPEG", quality=90)

    except Exception as e:
        log_erro(traceback.format_exc())

if __name__ == "__main__":
    gerar()
