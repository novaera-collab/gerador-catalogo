import sys
import os
import csv
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

def gerar_catalogo_completo(config, produtos, caminho_saida):
    COLUNAS = 3
    LARGURA_TOTAL = 1200
    MARGEM_LATERAL = 40
    MARGEM_TOPO = 180
    ESPACO_HORIZ = 20
    ESPACO_VERT = 20
    ALTURA_RODAPE = 130

    # Mapeamento atualizado do CSV
    cor_topo_rodape  = hex_to_rgb(config.get('cor_tit_rodape'), (27, 94, 32))
    cor_tarja_bg     = hex_to_rgb(config.get('cor_grid_tarja'), (0, 0, 0))       # Cor do fundo do preço
    cor_preco_texto  = hex_to_rgb(config.get('cor_grid_preco'), (255, 255, 255)) # Cor da escrita do preço

    largura_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2) - (ESPACO_HORIZ * (COLUNAS - 1))
    largura_card = largura_util // COLUNAS
    altura_card = 410

    num_produtos = len(produtos)
    linhas = (num_produtos + COLUNAS - 1) // COLUNAS if num_produtos > 0 else 1
    altura_total = MARGEM_TOPO + (linhas * (altura_card + ESPACO_VERT)) + ALTURA_RODAPE + 30

    img = Image.new("RGB", (LARGURA_TOTAL, max(altura_total, 800)), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Fontes com Destaque Extra
    try:
        font_titulo_bold  = ImageFont.truetype("arialbd.ttf", 32)
        font_sub_regular   = ImageFont.truetype("arial.ttf", 16)
        font_cod_bold      = ImageFont.truetype("arialbd.ttf", 16)
        font_desc_bold     = ImageFont.truetype("arialbd.ttf", 16)
        font_marca         = ImageFont.truetype("arialbd.ttf", 14)
        font_preco_bold    = ImageFont.truetype("arialbd.ttf", 28)
        font_rod_destaque  = ImageFont.truetype("arialbd.ttf", 20)
        font_rod_validade  = ImageFont.truetype("arial.ttf", 14)
    except IOError:
        font_titulo_bold = font_sub_regular = font_cod_bold = font_desc_bold = font_marca = font_preco_bold = font_rod_destaque = font_rod_validade = ImageFont.load_default()

    # 1. CABEÇALHO
    draw.rectangle([0, 0, LARGURA_TOTAL, 140], fill=cor_topo_rodape)
    
    logo_img = carregar_e_ajustar_imagem(config.get('cabecalho_logo'), 260, 100)
    if logo_img:
        img.paste(logo_img, (MARGEM_LATERAL, 20))

    texto_titulo = str(config.get('titulo', 'ENCARTE')).upper()
    texto_site   = str(config.get('cabecalho_site', ''))

    bbox_tit = draw.textbbox((0, 0), texto_titulo, font=font_titulo_bold)
    largura_tit = bbox_tit[2] - bbox_tit[0]

    bbox_site = draw.textbbox((0, 0), texto_site, font=font_sub_regular)
    largura_site = bbox_site[2] - bbox_site[0]

    x_titulo = LARGURA_TOTAL - MARGEM_LATERAL - largura_tit
    x_site   = LARGURA_TOTAL - MARGEM_LATERAL - largura_site

    draw.text((x_titulo, 35), texto_titulo, fill="#FFFFFF", font=font_titulo_bold)
    if texto_site:
        draw.text((x_site, 85), texto_site, fill="#E0E0E0", font=font_sub_regular)

    # 2. CARDS DE PRODUTOS
    for idx, prod in enumerate(produtos):
        coluna = idx % COLUNAS
        linha = idx // COLUNAS

        x = MARGEM_LATERAL + coluna * (largura_card + ESPACO_HORIZ)
        y = MARGEM_TOPO + linha * (altura_card + ESPACO_VERT)

        draw.rectangle([x, y, x + largura_card, y + altura_card], outline="#CCCCCC", fill="#FAFAFA", width=2)

        # Código & Marca
        cod_str = str(prod.get('codigo', '')).zfill(5)
        marca_str = str(prod.get('marca', '')).upper()
        draw.text((x + 15, y + 12), f"CÓD: {cod_str}", fill="#000000", font=font_cod_bold)
        if marca_str:
            draw.text((x + largura_card - 110, y + 12), marca_str[:12], fill="#555555", font=font_marca)

        # Área da Foto Maior
        area_foto_x, area_foto_y = x + 15, y + 38
        area_foto_w, area_foto_h = largura_card - 30, 225
        draw.rectangle([area_foto_x, area_foto_y, area_foto_x + area_foto_w, area_foto_y + area_foto_h], outline="#E0E0E0", fill="#FFFFFF")

        foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w - 6, area_foto_h - 6)
        if foto_prod:
            px = area_foto_x + (area_foto_w - foto_prod.width) // 2
            py = area_foto_y + (area_foto_h - foto_prod.height) // 2
            img.paste(foto_prod, (px, py))
        else:
            draw.text((area_foto_x + (area_foto_w // 4), area_foto_y + 100), "[ SEM FOTO ]", fill="#CCCCCC", font=font_cod_bold)

        # Descrição com Destaque
        desc = str(prod.get('descricao', 'PRODUTO SEM DESCRIÇÃO'))[:28]
        draw.text((x + 15, y + 273), desc.upper(), fill="#000000", font=font_desc_bold)

        # Tarja de Preço
        tarja_x1, tarja_y1 = x + 10, y + 320
        tarja_x2, tarja_y2 = x + largura_card - 10, y + 390
        draw.rectangle([tarja_x1, tarja_y1, tarja_x2, tarja_y2], fill=cor_tarja_bg)

        try:
            preco_val = float(str(prod.get('preco', 0)).replace(',', '.'))
        except ValueError:
            preco_val = 0.0
        preco_fmt = f"R$ {preco_val:.2f}".replace('.', ',')

        # CENTRALIZAÇÃO PERFEITA DO PREÇO
        bbox_p = draw.textbbox((0, 0), preco_fmt, font=font_preco_bold)
        largura_p = bbox_p[2] - bbox_p[0]
        altura_p = bbox_p[3] - bbox_p[1]

        x_preco = tarja_x1 + ((tarja_x2 - tarja_x1) - largura_p) // 2
        y_preco = tarja_y1 + ((tarja_y2 - tarja_y1) - altura_p) // 2 - 3

        draw.text((x_preco, y_preco), preco_fmt, fill=cor_preco_texto, font=font_preco_bold)

    # 3. RODAPÉ EM 2 LINHAS
    y_rodape = altura_total - ALTURA_RODAPE
    draw.rectangle([0, y_rodape, LARGURA_TOTAL, altura_total], fill=cor_topo_rodape)

    # LINHA 1: Contato | Whats Logo + Fone
    contato_str = str(config.get('rodape_contato', '')).strip()
    fone_str = str(config.get('rodape_fone', '')).strip()
    ico_whats = carregar_e_ajustar_imagem(config.get('rodape_logo_fone'), 32, 32)

    texto_contato = f"{contato_str}   |" if contato_str else ""
    texto_fone = f"{fone_str}" if fone_str else ""

    bbox_c = draw.textbbox((0, 0), texto_contato, font=font_rod_destaque) if texto_contato else (0,0,0,0)
    bbox_f = draw.textbbox((0, 0), texto_fone, font=font_rod_destaque) if texto_fone else (0,0,0,0)

    larg_contato = bbox_c[2] - bbox_c[0]
    larg_fone    = bbox_f[2] - bbox_f[0]
    larg_ico     = (ico_whats.width + 12) if ico_whats else 0

    largura_total_l1 = larg_contato + larg_ico + larg_fone
    x_cursor = (LARGURA_TOTAL - largura_total_l1) // 2
    y_l1 = y_rodape + 25

    if texto_contato:
        draw.text((x_cursor, y_l1), texto_contato, fill="#FFFFFF", font=font_rod_destaque)
        x_cursor += larg_contato + 12

    if ico_whats:
        img.paste(ico_whats, (x_cursor, y_l1 - 3))
        x_cursor += larg_ico

    if texto_fone:
        draw.text((x_cursor, y_l1), texto_fone, fill="#FFFFFF", font=font_rod_destaque)

    # LINHA 2: Validade Menor
    validade_str = str(config.get('rodape_validade', '')).strip()
    if validade_str:
        bbox_val = draw.textbbox((0, 0), validade_str, font=font_rod_validade)
        larg_val = bbox_val[2] - bbox_val[0]
        x_val = (LARGURA_TOTAL - larg_val) // 2
        y_l2 = y_rodape + 75
        draw.text((x_val, y_l2), validade_str, fill="#E0E0E0", font=font_rod_validade)

    # 4. SALVAR ARQUIVO JPG
    if not caminho_saida:
        caminho_saida = config.get('saida_jpg', 'CATALOGO.JPG')
    
    pasta_dest = os.path.dirname(caminho_saida)
    if pasta_dest and not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest, exist_ok=True)

    img.save(caminho_saida, quality=95)

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

            gerar_catalogo_completo(config, produtos, saida_cli)

    except Exception as e:
        with open("erro_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(traceback.format_exc())
