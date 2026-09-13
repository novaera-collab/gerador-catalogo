import sys
import os
import csv
import glob
import traceback
from PIL import Image, ImageDraw, ImageFont

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

def hex_to_rgb(hex_str, default=(27, 94, 32)):
    if not hex_str or not hex_str.startswith("#"):
        return default
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return default
    try:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    except ValueError:
        return default

def carregar_e_ajustar_imagem(caminho, largura_max, altura_max, fundo_cor=None):
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        img = Image.open(caminho).convert("RGBA")
        img.thumbnail((largura_max, altura_max), Image.Resampling.LANCZOS)
        
        if fundo_cor is not None:
            canvas = Image.new("RGBA", (largura_max, altura_max), fundo_cor)
            px = (largura_max - img.width) // 2
            py = (altura_max - img.height) // 2
            canvas.paste(img, (px, py), img)
            return canvas.convert("RGB")
        else:
            return img
    except Exception:
        return None

def gerar_imagem_qrcode(url_completa, tam_px=110):
    if HAS_QRCODE:
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=4,
                border=1
            )
            qr.add_data(url_completa)
            qr.make(fit=True)
            
            # Matriz binaria para renderizacao direta em RGB sem conversao de paleta
            matrix = qr.get_matrix()
            num_modules = len(matrix)
            
            img_qr = Image.new("RGB", (num_modules, num_modules), (255, 255, 255))
            draw = ImageDraw.Draw(img_qr)
            
            for r in range(num_modules):
                for c in range(num_modules):
                    if matrix[r][c]:
                        draw.point((c, r), fill=(0, 0, 0))
                        
            return img_qr.resize((tam_px, tam_px), Image.Resampling.NEAREST)
        except Exception:
            pass

    # Fallback seguro caso a biblioteca qrcode nao esteja instalada
    img_qr = Image.new("RGB", (tam_px, tam_px), (255, 255, 255))
    d_qr = ImageDraw.Draw(img_qr)
    d_qr.rectangle([2, 2, tam_px-3, tam_px-3], outline=(0, 0, 0), width=2)
    d_qr.text((tam_px//2, tam_px//2), "QR CODE", fill=(0, 0, 0), anchor="mm")
    return img_qr

def criar_card_qrcode_estilizado(url_site, cor_tema_rgb, tam_qr=110):
    url_limpa = str(url_site).strip() if url_site else "www.oestepharma.com.br"
    url_completa = url_limpa if url_limpa.startswith(("http://", "https://")) else "https://" + url_limpa

    # Renderizacao do QR Code
    img_qr = gerar_imagem_qrcode(url_completa, tam_px=tam_qr)

    # Moldura Visual
    w_card, h_card = tam_qr + 30, tam_qr + 85
    card = Image.new("RGBA", (w_card, h_card), (255, 255, 255, 0))
    draw = ImageDraw.Draw(card)

    # Fundo branco arredondado
    draw.rounded_rectangle([0, 0, w_card, h_card], radius=12, fill="#FFFFFF")

    # Header do Card
    draw.rounded_rectangle([8, 5, w_card - 8, 28], radius=8, fill=cor_tema_rgb)
    try:
        font_hdr = ImageFont.truetype("arialbd.ttf", 10)
        font_sub = ImageFont.truetype("arialbd.ttf", 9)
        font_url = ImageFont.truetype("arialbd.ttf", 10)
    except IOError:
        font_hdr = font_sub = font_url = ImageFont.load_default()

    draw.text((w_card // 2, 16), "ACESSE NOSSO SITE", fill="#FFFFFF", font=font_hdr, anchor="mm")

    # Posicionamento do QR Code
    card.paste(img_qr, (15, 33))

    # Detalhes das cantoneiras
    cx1, cy1, cx2, cy2 = 10, 28, w_card - 10, 33 + tam_qr + 5
    draw.arc([cx1, cy1, cx1 + 16, cy1 + 16], start=180, end=270, fill=cor_tema_rgb, width=2)
    draw.arc([cx2 - 16, cy1, cx2, cy1 + 16], start=270, end=360, fill=cor_tema_rgb, width=2)
    draw.arc([cx1, cy2 - 16, cx1 + 16, cy2], start=90, end=180, fill=cor_tema_rgb, width=2)
    draw.arc([cx2 - 16, cy2 - 16, cx2, cy2], start=0, end=90, fill=cor_tema_rgb, width=2)

    # Tarja inferior com a URL do CSV
    y_tarja = 33 + tam_qr + 8
    draw.rounded_rectangle([8, y_tarja, w_card - 8, y_tarja + 20], radius=8, fill=cor_tema_rgb)
    
    site_exibicao = url_limpa.replace("https://", "").replace("http://", "")
    draw.text((w_card // 2, y_tarja + 10), site_exibicao, fill="#FFFFFF", font=font_url, anchor="mm")

    # Legenda inferior
    draw.text((w_card // 2, h_card - 14), "APONTE A CÂMERA DO CELULAR", fill="#333333", font=font_sub, anchor="mm")
    draw.text((w_card // 2, h_card - 5), "E ACESSE AGORA", fill="#333333", font=font_sub, anchor="mm")

    return card

def limpar_jpgs_antigos(caminho_saida_base):
    try:
        pasta_dest = os.path.dirname(caminho_saida_base) or os.getcwd()
        nome_base = os.path.splitext(os.path.basename(caminho_saida_base))[0]
        if '_' in nome_base and nome_base.rsplit('_', 1)[1].isdigit():
            nome_base = nome_base.rsplit('_', 1)[0]

        padrao_busca = os.path.join(pasta_dest, f"{nome_base}*.JPG")
        padrao_busca_lower = os.path.join(pasta_dest, f"{nome_base}*.jpg")
        
        for arq in set(glob.glob(padrao_busca) + glob.glob(padrao_busca_lower)):
            try:
                os.remove(arq)
            except Exception:
                pass
    except Exception:
        pass

def renderizar_catalogo(config, produtos, caminho_saida_base):
    prods_destaque = [p for p in produtos if str(p.get('destaque', '')).strip().upper() == 'S']
    prods_normais = [p for p in produtos if str(p.get('destaque', '')).strip().upper() != 'S']

    LARGURA_TOTAL = 1600
    MARGEM_LATERAL = 40
    ESPACO_HORIZ = 20
    ESPACO_VERT = 20
    ALTURA_RODAPE = 210

    hex_destaque = config.get('cor_fundo_destaque') or config.get('cor_furndo_destaque')
    hex_demais   = config.get('cor_fundo_demais') or config.get('cor_furndo_demais')
    
    # Leitura da cor do rodape via rodape_cor_tema
    hex_rodape = config.get('rodape_cor_tema') or config.get('cor_tit_rodape')

    cor_rodape_bg      = hex_to_rgb(hex_rodape, (20, 54, 31))
    cor_topo_cabecalho = hex_to_rgb(config.get('cor_tit_rodape'), (18, 97, 48))
    cor_tarja_bg       = hex_to_rgb(config.get('cor_grid_tarja'), (92, 179, 137))
    cor_preco_texto    = hex_to_rgb(config.get('cor_grid_preco'), (0, 0, 0))
    cor_fundo_destaque = hex_to_rgb(hex_destaque, (255, 255, 255))
    cor_fundo_demais   = hex_to_rgb(hex_demais, (183, 235, 213))

    try:
        font_sub_titulo     = ImageFont.truetype("arialbd.ttf", 32)
        font_cod_bold       = ImageFont.truetype("arialbd.ttf", 20)
        font_desc_bold      = ImageFont.truetype("arialbd.ttf", 22)
        font_marca          = ImageFont.truetype("arialbd.ttf", 18)
        font_preco_destaque = ImageFont.truetype("arialbd.ttf", 52)
        font_preco_normal   = ImageFont.truetype("arialbd.ttf", 40)
        font_rod_destaque   = ImageFont.truetype("arialbd.ttf", 26)
        font_rod_validade   = ImageFont.truetype("arial.ttf", 20)
        font_rod_tabela     = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_sub_titulo = font_cod_bold = font_desc_bold = font_marca = font_preco_destaque = font_preco_normal = font_rod_destaque = font_rod_validade = font_rod_tabela = ImageFont.load_default()

    cabecalho_path = config.get('cabecalho_tema', '')
    img_cabecalho = None
    if os.path.exists(cabecalho_path):
        try:
            img_cabecalho = Image.open(cabecalho_path).convert("RGB")
            if img_cabecalho.width != LARGURA_TOTAL:
                proporcao = LARGURA_TOTAL / float(img_cabecalho.width)
                nova_altura = int(float(img_cabecalho.height) * proporcao)
                img_cabecalho = img_cabecalho.resize((LARGURA_TOTAL, nova_altura), Image.Resampling.LANCZOS)
        except Exception:
            img_cabecalho = None

    ALTURA_CABECALHO = img_cabecalho.height if img_cabecalho else 270
    MARGEM_TOPO_CONTEUDO = ALTURA_CABECALHO + 30

    if not caminho_saida_base:
        caminho_saida_base = config.get('saida_jpg', 'CATALOGO.JPG')

    pasta_dest = os.path.dirname(caminho_saida_base)
    if pasta_dest and not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest, exist_ok=True)

    limpar_jpgs_antigos(caminho_saida_base)

    nome_base, ext = os.path.splitext(caminho_saida_base)
    if not ext:
        ext = ".JPG"

    queue_dest = list(prods_destaque)
    queue_norm = list(prods_normais)

    pag_num = 1
    MAX_ALTURA_PAGINA = 2400

    cols_destaque_base = 3
    cols_normal_base = 4

    larg_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2)
    larg_card_dest_padrao = (larg_util - (ESPACO_HORIZ * (cols_destaque_base - 1))) // cols_destaque_base
    larg_card_norm_padrao = (larg_util - (ESPACO_HORIZ * (cols_normal_base - 1))) // cols_normal_base

    alt_card_dest = 520
    alt_card_norm = 390

    while queue_dest or queue_norm or pag_num == 1:
        current_dest = []
        if pag_num == 1 and queue_dest:
            n_cap = min(3, len(queue_dest))
            current_dest = queue_dest[:n_cap]
            queue_dest = queue_dest[n_cap:]

        alt_disponivel = MAX_ALTURA_PAGINA - MARGEM_TOPO_CONTEUDO - ALTURA_RODAPE
        if current_dest:
            alt_disponivel -= (alt_card_dest + ESPACO_VERT)

        max_rows_norm = max(1, alt_disponivel // (alt_card_norm + ESPACO_VERT))
        max_items_page = max_rows_norm * cols_normal_base

        current_norm = []
        if queue_norm:
            current_norm = queue_norm[:max_items_page]
            queue_norm = queue_norm[max_items_page:]

        num_rows_norm = (len(current_norm) + cols_normal_base - 1) // cols_normal_base if current_norm else 0
        conteudo_h = (alt_card_dest + ESPACO_VERT if current_dest else 0) + (num_rows_norm * (alt_card_norm + ESPACO_VERT))
        
        ALTURA_TOTAL = MARGEM_TOPO_CONTEUDO + conteudo_h + ALTURA_RODAPE + 10

        img = Image.new("RGB", (LARGURA_TOTAL, ALTURA_TOTAL), color=cor_fundo_demais)
        draw = ImageDraw.Draw(img)

        # 1. Cabecalho
        if img_cabecalho:
            img.paste(img_cabecalho, (0, 0))
        else:
            draw.rectangle([0, 0, LARGURA_TOTAL, ALTURA_CABECALHO], fill=cor_topo_cabecalho)

        titulo_principal = str(config.get('titulo', 'SUPLEMENTOS NUTRICIONAIS')).upper()
        pos_y_titulo = int(ALTURA_CABECALHO * 0.72)
        draw.text((LARGURA_TOTAL // 2, pos_y_titulo), titulo_principal, fill="#FFFFFF", font=font_sub_titulo, anchor="mm")

        # 2. Destaques
        y_cursor = MARGEM_TOPO_CONTEUDO
        if current_dest:
            qtd_d = len(current_dest)
            largura_linha_d = (qtd_d * larg_card_dest_padrao) + ((qtd_d - 1) * ESPACO_HORIZ)
            x_inicial_d = (LARGURA_TOTAL - largura_linha_d) // 2

            for idx, prod in enumerate(current_dest):
                x = x_inicial_d + idx * (larg_card_dest_padrao + ESPACO_HORIZ)
                
                draw.rounded_rectangle([x, y_cursor, x + larg_card_dest_padrao, y_cursor + alt_card_dest], radius=12, outline=cor_tarja_bg, fill=cor_fundo_destaque, width=3)
                
                draw.rounded_rectangle([x + 12, y_cursor + 12, x + 130, y_cursor + 42], radius=6, fill="#D32F2F")
                draw.text((x + 71, y_cursor + 27), "DESTAQUE", fill="#FFFFFF", font=font_marca, anchor="mm")

                cod_str = str(prod.get('codigo', '')).zfill(5)
                marca_str = str(prod.get('marca', '')).upper()
                draw.text((x + larg_card_dest_padrao - 15, y_cursor + 27), f"CÓD: {cod_str}", fill="#555555", font=font_cod_bold, anchor="rm")

                area_foto_x, area_foto_y = x + 15, y_cursor + 50
                area_foto_w, area_foto_h = larg_card_dest_padrao - 30, 260
                
                draw.rounded_rectangle([area_foto_x, area_foto_y, area_foto_x + area_foto_w, area_foto_y + area_foto_h], radius=8, fill="#FFFFFF")

                foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w - 10, area_foto_h - 10)
                if foto_prod:
                    px = area_foto_x + (area_foto_w - foto_prod.width) // 2
                    py = area_foto_y + (area_foto_h - foto_prod.height) // 2
                    img.paste(foto_prod, (px, py), foto_prod if foto_prod.mode == "RGBA" else None)
                else:
                    draw.text((area_foto_x + area_foto_w//2, area_foto_y + area_foto_h//2), "[ SEM FOTO ]", fill="#555555", font=font_cod_bold, anchor="mm")

                desc = str(prod.get('descricao', ''))[:35]
                draw.text((x + larg_card_dest_padrao//2, y_cursor + 335), desc.upper(), fill="#000000", font=font_desc_bold, anchor="mm")
                if marca_str:
                    draw.text((x + larg_card_dest_padrao//2, y_cursor + 365), marca_str, fill="#777777", font=font_marca, anchor="mm")

                tarja_y1 = y_cursor + 398
                tarja_y2 = y_cursor + alt_card_dest - 12
                draw.rounded_rectangle([x + 10, tarja_y1, x + larg_card_dest_padrao - 10, tarja_y2], radius=10, fill=cor_tarja_bg)
                
                preco_fmt = str(prod.get('preco', '')).strip()
                draw.text((x + larg_card_dest_padrao//2, tarja_y1 + (tarja_y2 - tarja_y1)//2), preco_fmt, fill=cor_preco_texto, font=font_preco_destaque, anchor="mm")

            y_cursor += alt_card_dest + ESPACO_VERT

        # 3. Produtos Normais (Calculo por Linha para Centralizar Incompletas)
        if current_norm:
            total_normais = len(current_norm)
            
            for idx, prod in enumerate(current_norm):
                row = idx // cols_normal_base
                col = idx % cols_normal_base

                itens_na_linha = min(cols_normal_base, total_normais - (row * cols_normal_base))

                largura_linha_n = (itens_na_linha * larg_card_norm_padrao) + ((itens_na_linha - 1) * ESPACO_HORIZ)
                x_inicial_n = (LARGURA_TOTAL - largura_linha_n) // 2
                
                x = x_inicial_n + col * (larg_card_norm_padrao + ESPACO_HORIZ)
                y = y_cursor + row * (alt_card_norm + ESPACO_VERT)

                draw.rounded_rectangle([x, y, x + larg_card_norm_padrao, y + alt_card_norm], radius=10, outline="#E0E0E0", fill="#FFFFFF", width=2)

                cod_str = str(prod.get('codigo', '')).zfill(5)
                draw.text((x + 12, y + 15), f"CÓD: {cod_str}", fill="#000000", font=font_cod_bold)

                area_foto_x, area_foto_y = x + 10, y + 38
                area_foto_w, area_foto_h = larg_card_norm_padrao - 20, 190

                draw.rounded_rectangle([area_foto_x, area_foto_y, area_foto_x + area_foto_w, area_foto_y + area_foto_h], radius=6, fill="#FFFFFF")

                foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w - 10, area_foto_h - 10)
                if foto_prod:
                    px = area_foto_x + (area_foto_w - foto_prod.width) // 2
                    py = area_foto_y + (area_foto_h - foto_prod.height) // 2
                    img.paste(foto_prod, (px, py), foto_prod if foto_prod.mode == "RGBA" else None)
                else:
                    draw.text((area_foto_x + area_foto_w//2, area_foto_y + area_foto_h//2), "[ SEM FOTO ]", fill="#555555", font=font_marca, anchor="mm")

                desc = str(prod.get('descricao', ''))[:30]
                draw.text((x + larg_card_norm_padrao//2, y + 242), desc.upper(), fill="#000000", font=font_desc_bold, anchor="mm")

                tarja_y1 = y + 280
                tarja_y2 = y + alt_card_norm - 10
                draw.rounded_rectangle([x + 8, tarja_y1, x + larg_card_norm_padrao - 8, tarja_y2], radius=8, fill=cor_tarja_bg)

                preco_fmt = str(prod.get('preco', '')).strip()
                draw.text((x + larg_card_norm_padrao//2, tarja_y1 + (tarja_y2 - tarja_y1)//2), preco_fmt, fill=cor_preco_texto, font=font_preco_normal, anchor="mm")

        # 4. Rodape com QR Code
        y_rodape = ALTURA_TOTAL - ALTURA_RODAPE
        draw.rectangle([0, y_rodape, LARGURA_TOTAL, ALTURA_TOTAL], fill=cor_rodape_bg)

        site_url = config.get('cabecalho_site') or config.get('rodape_site') or 'www.oestepharma.com.br'
        
        card_qr = criar_card_qrcode_estilizado(site_url, cor_rodape_bg, tam_qr=100)
        qr_x = MARGEM_LATERAL + 10
        qr_y = y_rodape + 10
        img.paste(card_qr, (qr_x, qr_y), card_qr)

        contato_str = str(config.get('rodape_contato', '')).strip()
        fone_str = str(config.get('rodape_fone', '')).strip()
        ico_whats = carregar_e_ajustar_imagem(config.get('rodape_logo_fone'), 36, 36)

        texto_contato = f"{contato_str}   |" if contato_str else ""
        texto_fone = f"{fone_str}" if fone_str else ""

        bbox_c = draw.textbbox((0, 0), texto_contato, font=font_rod_destaque) if texto_contato else (0,0,0,0)
        bbox_f = draw.textbbox((0, 0), texto_fone, font=font_rod_destaque) if texto_fone else (0,0,0,0)

        larg_contato = bbox_c[2] - bbox_c[0]
        larg_fone    = bbox_f[2] - bbox_f[0]
        larg_ico     = (ico_whats.width + 10) if ico_whats else 0

        largura_total_l1 = larg_contato + larg_ico + larg_fone
        x_cursor_r = (LARGURA_TOTAL + 150 - largura_total_l1) // 2
        y_l1 = y_rodape + 35

        if texto_contato:
            draw.text((x_cursor_r, y_l1), texto_contato, fill="#FFFFFF", font=font_rod_destaque)
            x_cursor_r += larg_contato + 10

        if ico_whats:
            img.paste(ico_whats, (x_cursor_r, y_l1 - 2), ico_whats if ico_whats.mode == "RGBA" else None)
            x_cursor_r += larg_ico

        if texto_fone:
            draw.text((x_cursor_r, y_l1), texto_fone, fill="#FFFFFF", font=font_rod_destaque)

        validade_str = str(config.get('rodape_validade', '')).strip()
        if validade_str:
            draw.text(((LARGURA_TOTAL + 150) // 2, y_rodape + 100), f"Preços válidos no período: {validade_str}", fill="#E0E0E0", font=font_rod_validade, anchor="mm")

        tabela_str = str(config.get('rodape_tabela', '')).strip()
        if tabela_str:
            draw.text(((LARGURA_TOTAL + 150) // 2, y_rodape + 140), tabela_str, fill="#CCCCCC", font=font_rod_tabela, anchor="mm")

        caminho_final = f"{nome_base}_{pag_num}{ext}" if pag_num > 1 else f"{nome_base}{ext}"
        img.save(caminho_final, format="JPEG", quality=98)
        pag_num += 1

if __name__ == "__main__":
    try:
        if len(sys.argv) >= 2:
            arquivo_csv = sys.argv[1]
            saida_cli = sys.argv[2] if len(sys.argv) >= 3 else None

            config = {}
            produtos = []

            if os.path.exists(arquivo_csv):
                with open(arquivo_csv, mode='r', encoding='utf-8-sig') as f:
                    linhas = f.readlines()
                    lendo_produtos = False
                    linhas_produtos = []

                    for linha in linhas:
                        linha_str = linha.strip()
                        if not linha_str:
                            continue

                        if linha_str.lower().startswith('codigo;'):
                            lendo_produtos = True
                            linhas_produtos.append(linha_str)
                            continue

                        if not lendo_produtos:
                            partes = linha_str.split(';')
                            if len(partes) >= 2:
                                config[partes[0].strip()] = partes[1].strip()
                        else:
                            linhas_produtos.append(linha_str)

                    if linhas_produtos:
                        reader = csv.DictReader(linhas_produtos, delimiter=';')
                        for row in reader:
                            produtos.append(row)

            renderizar_catalogo(config, produtos, saida_cli)

    except Exception as e:
        with open("erro_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(traceback.format_exc())
