import sys
import os
import csv
import traceback
from PIL import Image, ImageDraw, ImageFont

def hex_to_rgb(hex_str, default=(27, 94, 32)):
    """ Converte cor Hex (#1B5E20) para Tupla RGB """
    if not hex_str or not hex_str.startswith("#"):
        return default
    hex_str = hex_str.lstrip('#')
    if len(hex_str) != 6:
        return default
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def carregar_e_ajustar_imagem(caminho, largura_max, altura_max):
    """ Carrega imagem, converte pra RGBA e redimensiona mantendo proporção """
    if not caminho or not os.path.exists(caminho):
        return None
    try:
        img = Image.open(caminho).convert("RGBA")
        img.thumbnail((largura_max, altura_max), Image.Resampling.LANCZOS)
        return img
    except Exception:
        return None

def gerar_catalogo_completo(config, produtos, caminho_saida):
    COLUNAS = 3
    LARGURA_TOTAL = 1200
    MARGEM_LATERAL = 40
    MARGEM_TOPO = 180
    ESPACO_HORIZ = 20
    ESPACO_VERT = 20
    ALTURA_RODAPE = 100

    # Cores
    cor_topo_rodape = hex_to_rgb(config.get('cor_tit_rodape'), (27, 94, 32))      # Verde escuro padrão
    cor_grid = hex_to_rgb(config.get('cor_grid_fotos'), (211, 47, 47))           # Vermelho padrão

    # Cálculo da grade
    largura_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2) - (ESPACO_HORIZ * (COLUNAS - 1))
    largura_card = largura_util // COLUNAS
    altura_card = 360

    num_produtos = len(produtos)
    linhas = (num_produtos + COLUNAS - 1) // COLUNAS if num_produtos > 0 else 1
    altura_total = MARGEM_TOPO + (linhas * (altura_card + ESPACO_VERT)) + ALTURA_RODAPE + 40

    img = Image.new("RGB", (LARGURA_TOTAL, max(altura_total, 800)), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    # Fontes
    try:
        font_titulo = ImageFont.truetype("arial.ttf", 30)
        font_sub = ImageFont.truetype("arial.ttf", 16)
        font_cod = ImageFont.truetype("arial.ttf", 14)
        font_desc = ImageFont.truetype("arial.ttf", 15)
        font_marca = ImageFont.truetype("arial.ttf", 13)
        font_preco = ImageFont.truetype("arial.ttf", 26)
    except IOError:
        font_titulo = font_sub = font_cod = font_desc = font_marca = font_preco = ImageFont.load_default()

    # 1. CABEÇALHO
    draw.rectangle([0, 0, LARGURA_TOTAL, 140], fill=cor_topo_rodape)
    
    # Logo do Cabeçalho
    logo_img = carregar_e_ajustar_imagem(config.get('cabecalho_logo'), 200, 100)
    pos_x_texto = MARGEM_LATERAL
    if logo_img:
        img.paste(logo_img, (MARGEM_LATERAL, 20), logo_img)
        pos_x_texto += logo_img.width + 20

    # Texto do Título e Validade
    draw.text((pos_x_texto, 30), str(config.get('titulo', 'OFERTAS')).upper(), fill="#FFFFFF", font=font_titulo)
    draw.text((pos_x_texto, 80), str(config.get('validade', '')), fill="#A5D6A7", font=font_sub)

    # 2. CARDS DE PRODUTOS
    for idx, prod in enumerate(produtos):
        coluna = idx % COLUNAS
        linha = idx // COLUNAS

        x = MARGEM_LATERAL + coluna * (largura_card + ESPACO_HORIZ)
        y = MARGEM_TOPO + linha * (altura_card + ESPACO_VERT)

        # Fundo do Card
        draw.rectangle([x, y, x + largura_card, y + altura_card], outline="#DDDDDD", fill="#FAFAFA", width=2)

        # Código & Marca
        cod_str = str(prod.get('codigo', '')).zfill(5)
        marca_str = str(prod.get('marca', '')).upper()
        draw.text((x + 15, y + 12), f"CÓD: {cod_str}", fill="#555555", font=font_cod)
        if marca_str:
            draw.text((x + largura_card - 110, y + 12), marca_str[:12], fill="#777777", font=font_marca)

        # Foto do Produto
        area_foto_x, area_foto_y = x + 15, y + 35
        area_foto_w, area_foto_h = largura_card - 30, 170
        draw.rectangle([area_foto_x, area_foto_y, area_foto_x + area_foto_w, area_foto_y + area_foto_h], outline="#EEEEEE", fill="#FFFFFF")

        foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w - 10, area_foto_h - 10)
        if foto_prod:
            px = area_foto_x + (area_foto_w - foto_prod.width) // 2
            py = area_foto_y + (area_foto_h - foto_prod.height) // 2
            img.paste(foto_prod, (px, py), foto_prod)
        else:
            draw.text((area_foto_x + 80, area_foto_y + 75), "[ SEM FOTO ]", fill="#CCCCCC", font=font_cod)

        # Descrição
        desc = str(prod.get('descricao', 'PRODUTO SEM DESCRIÇÃO'))[:28]
        draw.text((x + 15, y + 215), desc.upper(), fill="#333333", font=font_desc)

        # Etiqueta de Preço
        draw.rectangle([x + 10, y + 270, x + largura_card - 10, y + 340], fill=cor_grid)
        try:
            preco_val = float(str(prod.get('preco', 0)).replace(',', '.'))
        except ValueError:
            preco_val = 0.0
        preco_fmt = f"R$ {preco_val:.2f}".replace('.', ',')
        draw.text((x + 25, y + 288), preco_fmt, fill="#FFFFFF", font=font_preco)

    # 3. RODAPÉ
    y_rodape = altura_total - ALTURA_RODAPE
    draw.rectangle([0, y_rodape, LARGURA_TOTAL, altura_total], fill=cor_topo_rodape)

    # Logo/Ícone do WhatsApp no Rodapé
    ico_whats = carregar_e_ajustar_imagem(config.get('cabecalho_logo_fone'), 35, 35)
    pos_x_rod = MARGEM_LATERAL
    if ico_whats:
        img.paste(ico_whats, (pos_x_rod, y_rodape + 30), ico_whats)
        pos_x_rod += 45

    texto_rodape = f"{config.get('rodape_contato', '')}  |  Fone/Whats: {config.get('rodape_fone', '')}"
    draw.text((pos_x_rod, y_rodape + 35), texto_rodape, fill="#FFFFFF", font=font_sub)

    # Exportação da Imagem
    if not caminho_saida:
        caminho_saida = config.get('saida_jpg', 'CATALOGO_OESTE_PHARMA.JPG')
    
    pasta_dest = os.path.dirname(caminho_saida)
    if pasta_dest and not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest, exist_ok=True)

    img.save(caminho_saida, quality=95)

# --- LEITOR INTELIGENTE DO CSV DUAL-HEADER ---
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

                        # Transição de Configuração -> Tabela de Produtos
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

                    # Lê a tabela de produtos
                    if linhas_produtos:
                        reader = csv.DictReader(linhas_produtos, delimiter=';')
                        for row in reader:
                            produtos.append(row)

            gerar_catalogo_completo(config, produtos, saida_cli)

    except Exception as e:
        with open("erro_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(traceback.format_exc())
