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
        
        # Cria um fundo branco sólido para remover opacidade/transparência
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
    ALTURA_RODAPE = 110

    # Cores personalizadas do CSV
    cor_topo_rodape = hex_to_rgb(config.get('cor_tit_rodape'), (27, 94, 32))
    cor_card_fundo  = hex_to_rgb(config.get('cor_grid_fotos'), (78, 238, 148))
    cor_preco_bg    = hex_to_rgb(config.get('cor_grid_preco'), (0, 0, 0))

    # Dimensões da grade
    largura_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2) - (ESPACO_HORIZ * (COLUNAS - 1))
    largura_card = largura_util // COLUNAS
    altura_card = 390

    num_produtos = len(produtos)
    linhas = (num_produtos + COLUNAS - 1) // COLUNAS if num_produtos > 0 else 1
    altura_total = MARGEM_TOPO + (linhas * (altura_card + ESPACO_VERT)) + ALTURA_RODAPE + 30

    img = Image.new("RGB", (LARGURA_TOTAL, max(altura_total, 800)), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Carregamento de Fontes Negrito e Regular
    try:
        font_titulo_bold = ImageFont.truetype("arialbd.ttf", 30)
        font_sub_regular  = ImageFont.truetype("arial.ttf", 16)
        font_cod_bold     = ImageFont.truetype("arialbd.ttf", 14)
        font_desc_bold    = ImageFont.truetype("arialbd.ttf", 15)
        font_marca        = ImageFont.truetype("arial.ttf", 13)
        font_preco_bold   = ImageFont.truetype("arialbd.ttf", 26)
        font_rodape       = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font_titulo_bold = font_sub_regular = font_cod_bold = font_desc_bold = font_marca = font_preco_bold = font_rodape = ImageFont.load_default()

    # 1. CABEÇALHO (Logo à esquerda | Título e Site à direita)
    draw.rectangle([0, 0, LARGURA_TOTAL, 140], fill=cor_topo_rodape)
    
    logo_img = carregar_e_ajustar_imagem(config.get('cabecalho_logo'), 260, 100)
    if logo_img:
        img.paste(logo_img, (MARGEM_LATERAL, 20))

    # Alinhamento à direita para Título e Site
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
        draw.text((x_site, 80), texto_site, fill="#E0E0E0", font=font_sub_regular)

    # 2. CARDS DE PRODUTOS
    for idx, prod in enumerate(produtos):
        coluna = idx % COLUNAS
        linha = idx // COLUNAS

        x = MARGEM_LATERAL + coluna * (largura_card + ESPACO_HORIZ)
        y = MARGEM_TOPO + linha * (altura_card + ESPACO_VERT)

        # Fundo do Card
        draw.rectangle([x, y, x + largura_card, y + altura_card], outline="#DDDDDD", fill="#FAFAFA", width=2)

        # Código & Marca (Negrito no Código)
        cod_str = str(prod.get('codigo', '')).zfill(5)
        marca_str = str(prod.get('marca', '')).upper()
        draw.text((x + 15, y + 12), f"CÓD: {cod_str}", fill="#333333", font=font_cod_bold)
        if marca_str:
            draw.text((x + largura_card - 110, y + 12), marca_str[:12], fill="#777777", font=font_marca)

        # Área da Foto Maior (210px de altura)
        area_foto_x, area_foto_y = x + 15, y + 35
        area_foto_w, area_foto_h = largura_card - 30, 210
        draw.rectangle([area_foto_x, area_foto_y, area_foto_x + area_foto_w, area_foto_y + area_foto_h], outline="#EEEEEE", fill="#FFFFFF")

        foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w - 10, area_foto_h - 10)
        if foto_prod:
            px = area_foto_x + (area_foto_w - foto_prod.width) // 2
            py = area_foto_y + (area_foto_h - foto_prod.height) // 2
            img.paste(foto_prod, (px, py))
        else:
            draw.text((area_foto_x + (area_foto_w // 4), area_foto_y + 95), "[ SEM FOTO ]", fill="#CCCCCC", font=font_cod_bold)

        # Descrição (Negrito)
        desc = str(prod.get('descricao', 'PRODUTO SEM DESCRIÇÃO'))[:28]
        draw.text((x + 15, y + 255), desc.upper(), fill="#222222", font=font_desc_bold)

        # Etiqueta de Preço (Negrito)
        draw.rectangle([x + 10, y + 300, x + largura_card - 10, y + 370], fill=cor_preco_bg)
        try:
            preco_val = float(str(prod.get('preco', 0)).replace(',', '.'))
        except ValueError:
            preco_val = 0.0
        preco_fmt = f"R$ {preco_val:.2f}".replace('.', ',')
        draw.text((x + 25, y + 320), preco_fmt, fill="#FFFFFF", font=font_preco_bold)

    # 3. RODAPÉ CENTRALIZADO
    y_rodape = altura_total - ALTURA_RODAPE
    draw.rectangle([0, y_rodape, LARGURA_TOTAL, altura_total], fill=cor_topo_rodape)

    ico_whats = carregar_e_ajustar_imagem(config.get('rodape_logo_fone'), 32, 32)
    
    # Texto unificado do Rodapé (Contato + Fone + Validade)
    partes_rodape = []
    if config.get('rodape_contato'): partes_rodape.append(config.get('rodape_contato'))
    if config.get('rodape_fone'): partes_rodape.append(f"Fone/Whats: {config.get('rodape_fone')}")
    if config.get('rodape_validade'): partes_rodape.append(config.get('rodape_validade'))
    
    texto_rodape_completo = "   |   ".join(partes_rodape)

    bbox_rod = draw.textbbox((0, 0), texto_rodape_completo, font=font_rodape)
    largura_rod_texto = bbox_rod[2] - bbox_rod[0]
    largura_ico = (ico_whats.width + 12) if ico_whats else 0
    
    # Cálculo para centralizar todo o bloco do rodapé na tela
    x_inicio_bloco = (LARGURA_TOTAL - (largura_ico + largura_rod_texto)) // 2

    if ico_whats:
        img.paste(ico_whats, (x_inicio_bloco, y_rodape + 38))
        x_inicio_bloco += largura_ico

    draw.text((x_inicio_bloco, y_rodape + 44), texto_rodape_completo, fill="#FFFFFF", font=font_rodape)

    # 4. SALVAR ARQUIVO JPG
    if not caminho_saida:
        caminho_saida = config.get('saida_jpg', 'CATALOGO.JPG')
    
    pasta_dest = os.path.dirname(caminho_saida)
    if pasta_dest and not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest, exist_ok=True)

    img.save(caminho_saida, quality=95)

# --- EXECUÇÃO VIA TERMINAL ---
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
