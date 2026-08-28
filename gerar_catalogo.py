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
            log_erro(f"CSV nao encontrado: {csv_path}")
            return

        metadados = {}
        produtos = []

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

        jpg_out_path = metadados.get('saida_jpg', '')
        if not jpg_out_path and len(sys.argv) > 2:
            jpg_out_path = sys.argv[2]
        if not jpg_out_path:
            user_profile = os.environ.get('USERPROFILE', 'C:\\')
            jpg_out_path = os.path.join(user_profile, 'Downloads', 'CATALOGO_OESTE_PHARMA.JPG')

        out_dir = os.path.dirname(jpg_out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        # Resolução HD Vertical para WhatsApp (1080 x 1920)
        W, H = 1080, 1920
        img = Image.new('RGB', (W, H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)

        # Carregar Fontes
        try:
            font_titulo = ImageFont.truetype("arialbd.ttf", 46)
            font_sub = ImageFont.truetype("arial.ttf", 26)
            font_prod = ImageFont.truetype("arialbd.ttf", 24)
            font_rs = ImageFont.truetype("arialbd.ttf", 22)
            font_preco = ImageFont.truetype("arialbd.ttf", 44)
        except:
            font_titulo = font_sub = font_prod = font_rs = font_preco = ImageFont.load_default()

        # Header Verde Superior
        draw.rectangle([(0, 0), (W, 180)], fill='#22702C')
        titulo = metadados.get('titulo', 'OESTE PHARMA - OFERTAS')
        fone = metadados.get('fone', '')
        rodape = metadados.get('rodape', '')

        draw.text((40, 35), titulo.upper(), fill='white', font=font_titulo)
        if fone:
            draw.text((40, 115), f"WhatsApp: {fone}", fill='#E0E0E0', font=font_sub)

        # Layout Mobile: Grid 2 Colunas x 4 Linhas (8 produtos de destaque)
        cols = 2
        margin_x = 35
        start_y = 210
        box_w = 485
        box_h = 380
        gap_x = 40
        gap_y = 25

        for i, p in enumerate(produtos[:8]):
            r = i // cols
            c = i % cols
            x = margin_x + c * (box_w + gap_x)
            y = start_y + r * (box_h + gap_y)

            # Card com linha tracejada / borda suave
            draw.rectangle([(x, y), (x + box_w, y + box_h)], outline='#CCCCCC', width=2, fill='#FAFAFA')

            desc = p.get('descricao', p.get('nome', 'PRODUTO')).upper()
            preco = p.get('preco', p.get('valor', '0,00'))

            # Nome do Produto (Quebra em 2 linhas)
            palavras = desc.split()
            l1, l2 = "", ""
            for pal in palavras:
                if len(l1 + " " + pal) <= 24:
                    l1 += (" " if l1 else "") + pal
                else:
                    l2 += (" " if l2 else "") + pal
            
            draw.text((x + 20, y + 15), l1, fill='#111111', font=font_prod)
            if l2:
                draw.text((x + 20, y + 45), l2[:24], fill='#111111', font=font_prod)

            # Imagem do Produto
            img_p_path = p.get('imagem', p.get('foto', ''))
            if img_p_path and os.path.exists(img_p_path):
                try:
                    p_img = Image.open(img_p_path).convert("RGBA")
                    p_img.thumbnail((230, 210))
                    img.paste(p_img, (x + 125, y + 85), p_img)
                except:
                    pass

            # Tag Estilo Pílula Verde para o Preço (estilo encarte farmacêutico)
            badge_x1, badge_y1 = x + 30, y + box_h - 75
            badge_x2, badge_y2 = x + box_w - 30, y + box_h - 15
            
            # Desenha fundo verde arredondado/preenchido
            draw.rectangle([(badge_x1, badge_y1), (badge_x2, badge_y2)], fill='#25D366')
            
            # Formata preço
            draw.text((badge_x1 + 30, badge_y1 + 15), "R$", fill='white', font=font_rs)
            draw.text((badge_x1 + 75, badge_y1 + 5), f"{preco}", fill='white', font=font_preco)

        # Rodapé Verde Inferior
        draw.rectangle([(0, H - 90), (W, H)], fill='#22702C')
        if rodape:
            draw.text((40, H - 60), rodape.upper(), fill='white', font=font_sub)

        img.save(jpg_out_path, "JPEG", quality=95)

    except Exception as e:
        log_erro(traceback.format_exc())

if __name__ == "__main__":
    gerar()
