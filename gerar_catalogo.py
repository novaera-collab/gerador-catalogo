import sys
import csv
import os
from PIL import Image, ImageDraw, ImageFont

def gerar_jpeg(csv_path, output_jpg):
    if not os.path.exists(csv_path):
        return

    CARD_W, CARD_H = 300, 320
    COLS = 4
    MARGIN = 20
    PADDING = 10
    IMG_SIZE = (220, 180)

    BG_COLOR = (255, 255, 255)
    CARD_BG = (255, 255, 255)
    CARD_BORDER = (220, 220, 220)
    TEXT_COLOR = (30, 30, 30)
    PRICE_BG = (46, 125, 50)
    PRICE_TEXT = (255, 255, 255)

    try:
        font_title = ImageFont.truetype("arial.ttf", 14)
        font_code = ImageFont.truetype("arialbd.ttf", 12)
        font_price = ImageFont.truetype("arialbd.ttf", 16)
    except:
        font_title = font_code = font_price = ImageFont.load_default()

    produtos = []
    with open(csv_path, mode='r', encoding='latin-1') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            produtos.append(row)

    if not produtos:
        return

    total_prods = len(produtos)
    rows = (total_prods + COLS - 1) // COLS
    
    img_w = (COLS * CARD_W) + ((COLS + 1) * MARGIN)
    img_h = (rows * CARD_H) + ((rows + 1) * MARGIN)

    canvas = Image.new('RGB', (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    for idx, prod in enumerate(produtos):
        col = idx % COLS
        row = idx // COLS

        x = MARGIN + col * (CARD_W + MARGIN)
        y = MARGIN + row * (CARD_H + MARGIN)

        draw.rectangle([x, y, x + CARD_W, y + CARD_H], fill=CARD_BG, outline=CARD_BORDER, width=2)

        foto_path = prod.get('foto', '').strip()
        img_obj = None

        if foto_path and os.path.exists(foto_path):
            try:
                img_obj = Image.open(foto_path).convert('RGB')
            except:
                img_obj = None

        if img_obj:
            img_obj.thumbnail(IMG_SIZE, Image.Resampling.LANCZOS)
            img_x = x + (CARD_W - img_obj.width) // 2
            img_y = y + PADDING + (IMG_SIZE[1] - img_obj.height) // 2
            canvas.paste(img_obj, (img_x, img_y))
        else:
            draw.rectangle([x + 40, y + 20, x + CARD_W - 40, y + 160], outline=(200,200,200))
            draw.text((x + 85, y + 80), "SEM FOTO", fill=(150,150,150), font=font_code)

        txt_cod = f"COD: {prod.get('codigo','')} - {prod.get('marca','')}"[:32]
        draw.text((x + PADDING, y + 195), txt_cod, fill=(100,100,100), font=font_code)

        txt_desc = prod.get('descricao','')[:35]
        draw.text((x + PADDING, y + 215), txt_desc, fill=TEXT_COLOR, font=font_title)

        preco_y = y + CARD_H - 45
        draw.rectangle([x + PADDING, preco_y, x + CARD_W - PADDING, preco_y + 35], fill=PRICE_BG)
        
        txt_preco = f"R$ {prod.get('preco','0,00')}"
        draw.text((x + PADDING + 10, preco_y + 7), txt_preco, fill=PRICE_TEXT, font=font_price)

    canvas.save(output_jpg, "JPEG", quality=90)

if __name__ == "__main__":
    if len(sys.argv) > 2:
        gerar_jpeg(sys.argv[1], sys.argv[2])
