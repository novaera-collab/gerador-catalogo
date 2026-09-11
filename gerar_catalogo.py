import sys
import os
import csv
import glob
import traceback
from PIL import Image, ImageDraw, ImageFont

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

def carregar_e_ajustar_imagem(caminho, largura_max, altura_max):
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        img = Image.open(caminho).convert("RGBA")
        img.thumbnail((largura_max, altura_max), Image.Resampling.LANCZOS)
        
        fundo_branco = Image.new("RGBA", img.size, (255, 255, 255, 255))
        fundo_branco.paste(img, (0, 0), img)
        return fundo_branco.convert("RGB")
    except Exception:
        return None

def criar_imagem_mulher_farmaceutica():
    img = Image.new("RGBA", (220, 250), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([60, 20, 160, 120], fill=(240, 210, 190))
    draw.rectangle([40, 110, 180, 250], fill=(255, 255, 255))
    draw.polygon([(40, 110), (110, 170), (180, 110)], fill=(200, 230, 220))
    return img

def limpar_jpgs_antigos(caminho_saida_base):
    try:
        pasta_dest = os.path.dirname(caminho_saida_base)
        if not pasta_dest:
            pasta_dest = os.getcwd()
            
        nome_base = os.path.splitext(os.path.basename(caminho_saida_base))[0]
        if '_' in nome_base and nome_base.rsplit('_', 1)[1].isdigit():
            nome_base = nome_base.rsplit('_', 1)[0]

        padrao_busca = os.path.join(pasta_dest, f"{nome_base}*.JPG")
        padrao_busca_lower = os.path.join(pasta_dest, f"{nome_base}*.jpg")
        
        arquivos = glob.glob(padrao_busca) + glob.glob(padrao_busca_lower)
        for arq in set(arquivos):
            try:
                os.remove(arq)
            except Exception:
                pass
    except Exception:
        pass

def renderizar_catalogo(config, produtos, caminho_saida_base):
    # Separar produtos por Destaque (S vs N)
    prods_destaque = [p for p in produtos if str(p.get('destaque', '')).strip().upper() == 'S']
    prods_normais = [p for p in produtos if str(p.get('destaque', '')).strip().upper() != 'S']

    # Se nenhum produto tiver 'S', pega atÃ© os 3 primeiros como destaque por padrÃ£o
    if not prods_destaque and len(produtos) > 0:
        prods_destaque = produtos[:min(3, len(produtos))]
        prods_normais = produtos[min(3, len(produtos)):]

    LARGURA_TOTAL = 1600
    MARGEM_LATERAL = 40
    MARGEM_TOPO_CONTEUDO = 300
    ESPACO_HORIZ = 20
    ESPACO_VERT = 20
    ALTURA_CABECALHO = 270
    ALTURA_RODAPE = 160

    cor_topo_rodape  = hex_to_rgb(config.get('cor_tit_rodape'), (27, 94, 32))
    cor_tarja_bg     = hex_to_rgb(config.get('cor_grid_tarja'), (112, 170, 135))
    cor_preco_texto  = hex_to_rgb(config.get('cor_grid_preco'), (0, 0, 0))

    try:
        font_titulo_encarte = ImageFont.truetype("arialbd.ttf", 52)
        font_sub_titulo     = ImageFont.truetype("arialbd.ttf", 28)
        font_site           = ImageFont.truetype("arial.ttf", 22)
        font_cod_bold       = ImageFont.truetype("arialbd.ttf", 22)
        font_desc_bold      = ImageFont.truetype("arialbd.ttf", 22)
        font_marca          = ImageFont.truetype("arialbd.ttf", 18)
        font_preco_destaque = ImageFont.truetype("arialbd.ttf", 52)
        font_preco_normal   = ImageFont.truetype("arialbd.ttf", 40)
        font_rod_destaque   = ImageFont.truetype("arialbd.ttf", 28)
        font_rod_validade   = ImageFont.truetype("arial.ttf", 20)
        font_rod_tabela     = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_titulo_encarte = font_sub_titulo = font_site = font_cod_bold = font_desc_bold = font_marca = font_preco_destaque = font_preco_normal = font_rod_destaque = font_rod_validade = font_rod_tabela = ImageFont.load_default()

    larg_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2)
    
    # Grid Destaque: 3 produtos no topo, maior destaque
    cols_destaque = 3
    larg_card_dest = (larg_util - (ESPACO_HORIZ * 2)) // cols_destaque
    alt_card_dest = 520

    # Grid Normal: 4 colunas abaixo
    cols_normal = 4
    larg_card_norm = (larg_util - (ESPACO_HORIZ * (cols_normal - 1))) // cols_normal
    alt_card_norm = 390

    if not caminho_saida_base:
        caminho_saida_base = config.get('saida_jpg', 'CATALOGO.JPG')

    pasta_dest = os.path.dirname(caminho_saida_base)
    if pasta_dest and not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest, exist_ok=True)

    limpar_jpgs_antigos(caminho_saida_base)

    nome_base, ext = os.path.splitext(caminho_saida_base)
    if not ext:
        ext = ".JPG"

    # Fila de itens para distribuir em pÃ¡ginas
    queue_dest = list(prods_destaque)
    queue_norm = list(prods_normais)

    pag_num = 1
    MAX_ALTURA_PAGINA = 2400

    while queue_dest or queue_norm or pag_num == 1:
        current_dest = []
        if pag_num == 1 and queue_dest:
            current_dest = queue_dest[:3]
            queue_dest = queue_dest[3:]

        current_norm = []
        alt_disponivel = MAX_ALTURA_PAGINA - MARGEM_TOPO_CONTEUDO - ALTURA_RODAPE
        if current_dest:
            alt_disponivel -= (alt_card_dest + ESPACO_VERT)

        max_rows_norm = max(1, alt_disponivel // (alt_card_norm + ESPACO_VERT))
        max_items_page = max_rows_norm * cols_normal

        if queue_norm:
            current_norm = queue_norm[:max_items_page]
            queue_norm = queue_norm[max_items_page:]

        # CÃ¡lculo de Altura DinÃ¢mica da PÃ¡gina (para nÃ£o ter espaÃ§o em branco excessivo quando hÃ¡ poucos produtos)
        num_rows_norm = (len(current_norm) + cols_normal - 1) // cols_normal if current_norm else 0
        conteudo_h = (alt_card_dest + ESPACO_VERT if current_dest else 0) + (num_rows_norm * (alt_card_norm + ESPACO_VERT))
        
        ALTURA_TOTAL = MARGEM_TOPO_CONTEUDO + conteudo_h + ALTURA_RODAPE + 10
        ALTURA_TOTAL = max(1100, ALTURA_TOTAL) # Altura mÃ­nima proporcional

        img = Image.new("RGB", (LARGURA_TOTAL, ALTURA_TOTAL), color="#FFFFFF")
        draw = ImageDraw.Draw(img)

        # 1. CABEÃ‡ALHO (Estilo Encarte Farma com Banner Verde)
        draw.rectangle([0, 0, LARGURA_TOTAL, ALTURA_CABECALHO], fill=cor_topo_rodape)
        draw.rectangle([0, ALTURA_CABECALHO - 12, LARGURA_TOTAL, ALTURA_CABECALHO], fill=cor_tarja_bg)

        # Logo no lado esquerdo
        logo_img = carregar_e_ajustar_imagem(config.get('cabecalho_logo'), 350, 180)
        if logo_img:
            img.paste(logo_img, (MARGEM_LATERAL + 10, (ALTURA_CABECALHO - logo_img.height) // 2 - 10))

        # TÃ­tulo Central "ENCARTE" + SubtÃ­tulo
        titulo_principal = str(config.get('titulo', 'SUPLEMENTOS NUTRICIONAIS')).upper()
        
        # InsÃ­gnia / Banner ENCARTE
        draw.rounded_rectangle([LARGURA_TOTAL // 2 - 200, 20, LARGURA_TOTAL // 2 + 200, 90], radius=15, fill="#FFFFFF")
        draw.text((LARGURA_TOTAL // 2, 55), "E N C A R T E", fill=cor_topo_rodape, font=font_titulo_encarte, anchor="mm")

        # SubtÃ­tulo
        draw.text((LARGURA_TOTAL // 2, 130), titulo_principal, fill="#FFFFFF", font=font_sub_titulo, anchor="mm")
        
        site_str = str(config.get('cabecalho_site', '')).strip()
        if site_str:
            draw.text((LARGURA_TOTAL // 2, 180), site_str, fill="#E0E0E0", font=font_site, anchor="mm")

        # Imagem da Mulher / FarmacÃªutica no lado direito
        mulher_path = config.get('cabecalho_mulher', r'f:\unico\logo\mulher.jpg')
        mulher_img = carregar_e_ajustar_imagem(mulher_path, 220, 250)
        if not mulher_img:
            mulher_img = criar_imagem_mulher_farmaceutica()
        if mulher_img:
            px = LARGURA_TOTAL - MARGEM_LATERAL - 220
            py = ALTURA_CABECALHO - mulher_img.height
            img.paste(mulher_img, (px, py))

        # 2. SEÃ‡ÃƒO DE DESTAQUES (Topo - 3 Produtos Maiores)
        y_cursor = MARGEM_TOPO_CONTEUDO
        if current_dest:
            for idx, prod in enumerate(current_dest):
                x = MARGEM_LATERAL + idx * (larg_card_dest + ESPACO_HORIZ)
                
                # Card Background
                draw.rounded_rectangle([x, y_cursor, x + larg_card_dest, y_cursor + alt_card_dest], radius=12, outline=cor_tarja_bg, fill="#FFFFFF", width=3)
                
                # Tag Destaque
                draw.rounded_rectangle([x + 12, y_cursor + 12, x + 130, y_cursor + 42], radius=6, fill="#D32F2F")
                draw.text((x + 71, y_cursor + 27), "DESTAQUE", fill="#FFFFFF", font=font_marca, anchor="mm")

                # CÃ³d e Marca
                cod_str = str(prod.get('codigo', '')).zfill(5)
                marca_str = str(prod.get('marca', '')).upper()
                draw.text((x + larg_card_dest - 15, y_cursor + 27), f"CÃ“D: {cod_str}", fill="#555555", font=font_cod_bold, anchor="rm")

                # Foto
                area_foto_x, area_foto_y = x + 15, y_cursor + 50
                area_foto_w, area_foto_h = larg_card_dest - 30, 260
                foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w, area_foto_h)
                if foto_prod:
                    px = area_foto_x + (area_foto_w - foto_prod.width) // 2
                    py = area_foto_y + (area_foto_h - foto_prod.height) // 2
                    img.paste(foto_prod, (px, py))
                else:
                    draw.text((area_foto_x + area_foto_w//2, area_foto_y + area_foto_h//2), "[ SEM FOTO ]", fill="#CCCCCC", font=font_cod_bold, anchor="mm")

                # DescriÃ§Ã£o
                desc = str(prod.get('descricao', ''))[:32]
                draw.text((x + larg_card_dest//2, y_cursor + 335), desc.upper(), fill="#000000", font=font_desc_bold, anchor="mm")
                if marca_str:
                    draw.text((x + larg_card_dest//2, y_cursor + 365), marca_str, fill="#777777", font=font_marca, anchor="mm")

                # Tarja de PreÃ§o
                tarja_y1 = y_cursor + 398
                tarja_y2 = y_cursor + alt_card_dest - 12
                draw.rounded_rectangle([x + 10, tarja_y1, x + larg_card_dest - 10, tarja_y2], radius=10, fill=cor_tarja_bg)
                
                preco_fmt = str(prod.get('preco', '')).strip()
                draw.text((x + larg_card_dest//2, tarja_y1 + (tarja_y2 - tarja_y1)//2), preco_fmt, fill=cor_preco_texto, font=font_preco_destaque, anchor="mm")

            y_cursor += alt_card_dest + ESPACO_VERT

        # 3. SEÃ‡ÃƒO DE PRODUTOS NORMAIS (Grid 4 colunas)
        if current_norm:
            for idx, prod in enumerate(current_norm):
                col = idx % cols_normal
                row = idx // cols_normal

                x = MARGEM_LATERAL + col * (larg_card_norm + ESPACO_HORIZ)
                y = y_cursor + row * (alt_card_norm + ESPACO_VERT)

                # Card
                draw.rounded_rectangle([x, y, x + larg_card_norm, y + alt_card_norm], radius=10, outline="#D0D0D0", fill="#FFFFFF", width=2)

                # CÃ³d
                cod_str = str(prod.get('codigo', '')).zfill(5)
                draw.text((x + 12, y + 15), f"CÃ“D: {cod_str}", fill="#666666", font=font_marca)

                # Foto
                area_foto_x, area_foto_y = x + 10, y + 38
                area_foto_w, area_foto_h = larg_card_norm - 20, 190
                foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w, area_foto_h)
                if foto_prod:
                    px = area_foto_x + (area_foto_w - foto_prod.width) // 2
                    py = area_foto_y + (area_foto_h - foto_prod.height) // 2
                    img.paste(foto_prod, (px, py))
                else:
                    draw.text((area_foto_x + area_foto_w//2, area_foto_y + area_foto_h//2), "[ SEM FOTO ]", fill="#CCCCCC", font=font_marca, anchor="mm")

                # DescriÃ§Ã£o
                desc = str(prod.get('descricao', ''))[:26]
                draw.text((x + larg_card_norm//2, y + 242), desc.upper(), fill="#000000", font=font_desc_bold, anchor="mm")

                # Tarja PreÃ§o
                tarja_y1 = y + 280
                tarja_y2 = y + alt_card_norm - 10
                draw.rounded_rectangle([x + 8, tarja_y1, x + larg_card_norm - 8, tarja_y2], radius=8, fill=cor_tarja_bg)

                preco_fmt = str(prod.get('preco', '')).strip()
                draw.text((x + larg_card_norm//2, tarja_y1 + (tarja_y2 - tarja_y1)//2), preco_fmt, fill=cor_preco_texto, font=font_preco_normal, anchor="mm")

        # 4. RODAPÃ‰
        y_rodape = ALTURA_TOTAL - ALTURA_RODAPE
        draw.rectangle([0, y_rodape, LARGURA_TOTAL, ALTURA_TOTAL], fill=cor_topo_rodape)

        contato_str = str(config.get('rodape_contato', '')).strip()
        fone_str = str(config.get('rodape_fone', '')).strip()
        ico_whats = carregar_e_ajustar_imagem(config.get('rodape_logo_fone'), 40, 40)

        texto_contato = f"{contato_str}   |" if contato_str else ""
        texto_fone = f"{fone_str}" if fone_str else ""

        bbox_c = draw.textbbox((0, 0), texto_contato, font=font_rod_destaque) if texto_contato else (0,0,0,0)
        bbox_f = draw.textbbox((0, 0), texto_fone, font=font_rod_destaque) if texto_fone else (0,0,0,0)

        larg_contato = bbox_c[2] - bbox_c[0]
        larg_fone    = bbox_f[2] - bbox_f[0]
        larg_ico     = (ico_whats.width + 15) if ico_whats else 0

        largura_total_l1 = larg_contato + larg_ico + larg_fone
        x_cursor_r = (LARGURA_TOTAL - largura_total_l1) // 2
        y_l1 = y_rodape + 20

        if texto_contato:
            draw.text((x_cursor_r, y_l1), texto_contato, fill="#FFFFFF", font=font_rod_destaque)
            x_cursor_r += larg_contato + 15

        if ico_whats:
            img.paste(ico_whats, (x_cursor_r, y_l1 - 2))
            x_cursor_r += larg_ico

        if texto_fone:
            draw.text((x_cursor_r, y_l1), texto_fone, fill="#FFFFFF", font=font_rod_destaque)

        validade_str = str(config.get('rodape_validade', '')).strip()
        if validade_str:
            draw.text((LARGURA_TOTAL // 2, y_rodape + 75), f"PreÃ§os vÃ¡lidos no perÃ­odo: {validade_str}", fill="#E0E0E0", font=font_rod_validade, anchor="mm")

        tabela_str = str(config.get('rodape_tabela', '')).strip()
        if tabela_str:
            draw.text((LARGURA_TOTAL // 2, y_rodape + 115), tabela_str, fill="#CCCCCC", font=font_rod_tabela, anchor="mm")

        # Salvar arquivo JPG
        if pag_num > 1:
            caminho_final = f"{nome_base}_{pag_num}{ext}"
        else:
            caminho_final = f"{nome_base}{ext}"

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
