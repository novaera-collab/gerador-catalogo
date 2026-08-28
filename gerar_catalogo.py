import sys
import csv
import os
from PIL import Image, ImageDraw, ImageFont

def resolver_caminho_foto(foto_raw):
    foto_path = foto_raw.strip()
    if not foto_path:
        return None
    
    if os.path.exists(foto_path):
        return foto_path

    extensoes = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP']
    for ext in extensoes:
        caminho_teste = foto_path + ext
        if os.path.exists(caminho_teste):
            return caminho_teste

    return None

def centralizar_texto(draw, text, font, x_start, y_start, width, fill_color):
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    x = x_start + (width - text_w) // 2
    draw.text((x, y_start), text, fill=fill_color, font=font)

def gerar_jpeg(csv_path, output_jpg):
    if not os.path.exists(csv_path):
        return

    CARD_W, CARD_H = 300, 320
    COLS = 4
    MARGIN = 20
    PADDING = 10
    HEADER_H = 80
    FOOTER_H = 60
    IMG_SIZE = (200, 160)

    # Cores Oeste Pharma
    COLOR_DARK_GREEN = (34, 112, 44)
    COLOR_LIGHT_GREEN = (228, 243, 227)
    BG_COLOR = (245, 245, 245)
    CARD_BG = (255, 255, 255)
    CARD_BORDER = (220, 220, 220)
    TEXT_DARK = (20, 20, 20)
    TEXT_WHITE = (255, 255, 255)

    try:
        font_header_title = ImageFont.truetype("arialbd.ttf", 18)
        font_header_sub = ImageFont.truetype("arial.ttf", 12)
        font_code = ImageFont.truetype("arialbd.ttf", 11)
        font_title = ImageFont.truetype("arialbd.ttf", 12)
        font_label = ImageFont.truetype("arialbd.ttf", 10)
        font_price = ImageFont.truetype("arialbd.ttf", 18)
        font_footer = ImageFont.truetype("arialbd.ttf", 16)
    except:
        font_header_title = font_header_sub = font_code = font_title = font_label = font_price = font_footer = ImageFont.load_default()

    # Leitura e Metadados do CSV
    meta = {
        'titulo': 'ENCARTE DE PRODUTOS SUJEITO A ALTERAÇÕES DE PREÇOS',
        'logo': r'f:\unico\logo\oeste.jpg',
        'logo_fone': r'f:\unico\logo\ico-whats.bmp',
        'rodape': '',
        'fone': ''
    }

    produtos = []
    with open(csv_path, mode='r', encoding='latin-1') as f:
        linhas = [line.strip() for line in f if line.strip()]

    is_produtos = False
    for linha in linhas:
        colunas = linha.split(';')
        col0 = colunas[0].lower().strip()

        # Identifica a transição de Metadados para os Produtos
        if col0 in ['codigo', 'fco', 'code']:
            is_produtos = True
            continue

        if not is_produtos:
            if col0 == 'titulo': meta['titulo'] = colunas[1].strip()
            elif col0 in ['logo', 'logo_empresa']: meta['logo'] = colunas[1].strip()
            elif col0 in ['logo_fone', 'logo_whats']: meta['logo_fone'] = colunas[1].strip()
            elif col0 in ['rodape', 'contato']: meta['rodape'] = colunas[1].strip()
            elif col0 == 'fone': meta['fone'] = colunas[1].strip()
            elif len(colunas) >= 5: # CSV sem linha de cabeçalho 'codigo'
                is_produtos = True

        if is_produtos and len(colunas) >= 5:
            produtos.append({
                'codigo': colunas[0].strip(),
                'descricao': colunas[1].strip(),
                'marca': colunas[2].strip(),
                'preco': colunas[3].strip(),
                'foto': colunas[4].strip()
            })

    if not produtos:
        return

    total_prods = len(produtos)
    rows = (total_prods + COLS - 1) // COLS

    img_w = (COLS * CARD_W) + ((COLS + 1) * MARGIN)
    grid_h = (rows * CARD_H) + ((rows + 1) * MARGIN)
    img_h = HEADER_H + grid_h + FOOTER_H

    canvas = Image.new('RGB', (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # --- CABEÇALHO ---
    draw.rectangle([0, 0, img_w, HEADER_H], fill=COLOR_DARK_GREEN)

    # Logo da Empresa
    path_logo = resolver_caminho_foto(meta['logo'])
    if path_logo:
        try:
            logo = Image.open(path_logo).convert('RGBA')
            logo.thumbnail((180, 60), Image.Resampling.LANCZOS)
            canvas.paste(logo, (MARGIN, (HEADER_H - logo.height) // 2), logo)
        except:
            draw.text((MARGIN, 25), "Oeste Pharma", fill=TEXT_WHITE, font=font_header_title)
    else:
        draw.text((MARGIN, 25), "Oeste Pharma", fill=TEXT_WHITE, font=font_header_title)

    # Título do Encarte
    txt_titulo = meta['titulo']
    draw.text((img_w - 550, 22), txt_titulo, fill=TEXT_WHITE, font=font_header_title)
    draw.text((img_w - 220, 48), "www.oestepharma.com.br", fill=TEXT_WHITE, font=font_header_sub)

    # --- CARDS DE PRODUTOS ---
    start_y = HEADER_H + MARGIN

    for idx, prod in enumerate(produtos):
        col = idx % COLS
        row = idx // COLS

        x = MARGIN + col * (CARD_W + MARGIN)
        y = start_y + row * (CARD_H + MARGIN)

        draw.rectangle([x, y, x + CARD_W, y + CARD_H], fill=CARD_BG, outline=CARD_BORDER, width=2)

        foto_path = resolver_caminho_foto(prod.get('foto', ''))
        if foto_path:
            try:
                img_obj = Image.open(foto_path).convert('RGB')
                img_obj.thumbnail(IMG_SIZE, Image.Resampling.LANCZOS)
                img_x = x + (CARD_W - img_obj.width) // 2
                img_y = y + 10 + (IMG_SIZE[1] - img_obj.height) // 2
                canvas.paste(img_obj, (img_x, img_y))
            except:
                draw.rectangle([x + 50, y + 20, x + CARD_W - 50, y + 150], outline=(220,220,220))
                centralizar_texto(draw, "SEM FOTO", font_code, x, y + 85, CARD_W, (150,150,150))
        else:
            draw.rectangle([x + 50, y + 20, x + CARD_W - 50, y + 150], outline=(220,220,220))
            centralizar_texto(draw, "SEM FOTO", font_code, x, y + 85, CARD_W, (150,150,150))

        # Faixa Código
        draw.rectangle([x + 10, y + 175, x + CARD_W - 10, y + 195], fill=COLOR_LIGHT_GREEN)
        txt_cod = f"COD: {prod.get('codigo','')} - {prod.get('marca','')}"[:36]
        centralizar_texto(draw, txt_cod, font_code, x, y + 179, CARD_W, COLOR_DARK_GREEN)

        # Descrição
        txt_desc = prod.get('descricao','')[:38]
        centralizar_texto(draw, txt_desc, font_title, x, y + 202, CARD_W, TEXT_DARK)

        # Preço
        price_y = y + 230
        draw.rectangle([x + 10, price_y, x + CARD_W - 10, price_y + 42], fill=COLOR_DARK_GREEN)
        centralizar_texto(draw, "PREÇO", font_label, x, price_y + 4, CARD_W, TEXT_WHITE)
        txt_preco = f"R$ {prod.get('preco','0,00')}"
        centralizar_texto(draw, txt_preco, font_price, x, price_y + 18, CARD_W, TEXT_WHITE)

    # --- RODAPÉ ---
    footer_y = img_h - FOOTER_H
    draw.rectangle([0, footer_y, img_w, img_h], fill=COLOR_DARK_GREEN)

    txt_rodape = meta['rodape'] if meta['rodape'] else "Entre em contato conosco"
    txt_fone = meta['fone']

    texto_completo = f"{txt_rodape}  |  Fone/Whats: {txt_fone}" if txt_fone else txt_rodape
    centralizar_texto(draw, texto_completo, font_footer, 0, footer_y + 18, img_w, TEXT_WHITE)

    # Ícone do Whats
    path_whats = resolver_caminho_foto(meta['logo_fone'])
    if path_whats:
        try:
            ico_w = Image.open(path_whats).convert('RGBA')
            ico_w.thumbnail((30, 30), Image.Resampling.LANCZOS)
            canvas.paste(ico_w, (img_w - 100, footer_y + 15), ico_w)
        except:
            pass

    canvas.save(output_jpg, "JPEG", quality=92)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        gerar_jpeg(sys.argv[1], sys.argv[2])
