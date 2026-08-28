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

        jpg_out_path = ""
        if len(sys.argv) > 2 and sys.argv[2].strip():
            jpg_out_path = sys.argv[2].strip()
        elif metadados.get('saida_jpg'):
            jpg_out_path = metadados.get('saida_jpg')
        else:
            user_profile = os.environ.get('USERPROFILE', 'C:\\')
            jpg_out_path = os.path.join(user_profile, 'Downloads', 'CATALOGO_OESTE_PHARMA.JPG')

        out_dir = os.path.dirname(jpg_out_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        W, H = 1080, 1920
        img = Image.new('RGB', (W, H), color='#FFFFFF')
        draw = ImageDraw.Draw(img)

        try:
            font_titulo = ImageFont.truetype("arialbd.ttf", 38)
            font_site = ImageFont.truetype("arial.ttf", 22)
            font_sub = ImageFont.truetype("arial.ttf", 24)
            font_prod = ImageFont.truetype("arialbd.ttf", 22)
            font_preco = ImageFont.truetype("arialbd.ttf", 40)
        except:
            font_titulo = font_site = font_sub = font_prod = font_preco = ImageFont.load_default()

        # CABEÇALHO VERDE
        draw.rectangle([(0, 0), (W, 180)], fill='#22702C')

        # Desenhar Logo
        logo_path = metadados.get('logo', '')
        if logo_path and os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path).convert("RGBA")
                logo_img.thumbnail((260, 140))
                img.paste(logo_img, (40, 20), logo_img)
            except:
                pass

        # Título à direita e Site abaixo
        titulo = metadados.get('titulo', 'OESTE PHARMA - ENCARTE DE OFERTAS')
        draw.text((W - 40, 45), titulo.upper(), fill='white', font=font_titulo, anchor="ra")
        draw.text((W - 40, 105), "www.oestepharma.com.br", fill='#E0E0E0', font=font_site, anchor="ra")

        # GRID DE PRODUTOS (2 colunas x 4 linhas)
        cols = 2
        margin_x = 35
        start_y = 200
        box_w = 485
        box_h = 380
        gap_x = 40
        gap_y = 20

        for i, p in enumerate(produtos[:8]):
            r = i // cols
            c = i % cols
            x = margin_x + c * (box_w + gap_x)
            y = start_y + r * (box_h + gap_y)

            draw.rectangle([(x, y), (x + box_w, y + box_h)], outline='#CCCCCC', width=2, fill='#FAFAFA')

            desc = p.get('descricao', p.get('nome', 'PRODUTO')).upper()
            preco = p.get('preco', p.get('valor', '0,00'))

            palavras = desc.split()
            l1, l2 = "", ""
            for pal in palavras:
                if len(l1 + " " + pal) <= 24:
                    l1 += (" " if l1 else "") + pal
                else:
                    l2 += (" " if l2 else "") + pal
            
            draw.text((x + 15, y + 15), l1, fill='#111111', font=font_prod)
            if l2:
                draw.text((x + 15, y + 42), l2[:24], fill='#111111', font=font_prod)

            img_p_path = p.get('foto', p.get('imagem', ''))
            if img_p_path and os.path.exists(img_p_path):
                try:
                    p_img = Image.open(img_p_path).convert("RGBA")
                    p_img.thumbnail((240, 200))
                    img.paste(p_img, (x + 120, y + 80), p_img)
                except:
                    pass

            # Tarja de preço: Verde bem claro, letras/números em PRETO e centralizado
            draw.rectangle([(x + 15, y + box_h - 70), (x + box_w - 15, y + box_h - 15)], fill='#E8F5E9')
            draw.text((x + (box_w // 2), y + box_h - 60), f"R$ {preco}", fill='#000000', font=font_preco, anchor="mm")

        # RODAPÉ VERDE
        draw.rectangle([(0, H - 110), (W, H)], fill='#22702C')
        
        # Validade no meio do rodapé
        validade = metadados.get('validade', '')
        if validade:
            draw.text((W // 2, H - 75), validade.upper(), fill='white', font=font_sub, anchor="mm")

        # Contato e fone
        rodape_txt = metadados.get('rodape', '')
        fone_txt = metadados.get('fone', '')
        info_contato = f"Contato: {rodape_txt}  -  {fone_txt}".strip(" -")
        if info_contato:
            draw.text((W // 2, H - 35), info_contato, fill='#E0E0E0', font=font_site, anchor="mm")

        img.save(jpg_out_path, "JPEG", quality=95)

    except Exception as e:
        log_erro(traceback.format_exc())

if __name__ == "__main__":
    gerar()
