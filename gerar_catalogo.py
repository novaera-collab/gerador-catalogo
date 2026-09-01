import sys
import os
import csv
import glob
import traceback
import subprocess
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

def limpar_jpgs_antigos(caminho_saida_base):
    """Apaga todas as imagens antigas do encarte no diretório de destino antes de gerar novas."""
    try:
        pasta_dest = os.path.dirname(caminho_saida_base)
        if not pasta_dest:
            pasta_dest = os.getcwd()
            
        nome_base = os.path.splitext(os.path.basename(caminho_saida_base))[0]
        # Remove sufixos numéricos caso a base já venha com '_1'
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

def renderizar_paginas_jpg(config, produtos, caminho_saida_base):
    # Limite fixo de 9 produtos por página para manter alta definição no WhatsApp
    PRODUTOS_POR_PAGINA = 9
    COLUNAS = 3
    LARGURA_TOTAL = 1600
    ALTURA_TOTAL = 2000
    MARGEM_LATERAL = 50
    MARGEM_TOPO = 220
    ESPACO_HORIZ = 25
    ESPACO_VERT = 25
    ALTURA_CABECALHO = 170
    ALTURA_RODAPE = 160

    # Configuração de Cores
    cor_topo_rodape  = hex_to_rgb(config.get('cor_tit_rodape'), (27, 94, 32))
    cor_tarja_bg     = hex_to_rgb(config.get('cor_grid_tarja'), (78, 238, 148))
    cor_preco_texto  = hex_to_rgb(config.get('cor_grid_preco'), (0, 0, 0))

    largura_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2) - (ESPACO_HORIZ * (COLUNAS - 1))
    largura_card = largura_util // COLUNAS
    altura_card = 460

    # Carregamento de Fontes
    try:
        font_titulo_bold  = ImageFont.truetype("arialbd.ttf", 40)
        font_sub_regular   = ImageFont.truetype("arial.ttf", 22)
        font_cod_bold      = ImageFont.truetype("arialbd.ttf", 20)
        font_desc_bold     = ImageFont.truetype("arialbd.ttf", 22)
        font_marca         = ImageFont.truetype("arialbd.ttf", 18)
        font_preco_bold    = ImageFont.truetype("arialbd.ttf", 38)
        font_rod_destaque  = ImageFont.truetype("arialbd.ttf", 26)
        font_rod_validade  = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        font_titulo_bold = font_sub_regular = font_cod_bold = font_desc_bold = font_marca = font_preco_bold = font_rod_destaque = font_rod_validade = ImageFont.load_default()

    total_produtos = len(produtos)
    total_paginas = (total_produtos + PRODUTOS_POR_PAGINA - 1) // PRODUTOS_POR_PAGINA if total_produtos > 0 else 1

    if not caminho_saida_base:
        caminho_saida_base = config.get('saida_jpg', 'CATALOGO.JPG')

    pasta_dest = os.path.dirname(caminho_saida_base)
    if not pasta_dest:
        pasta_dest = os.getcwd()
    elif not os.path.exists(pasta_dest):
        os.makedirs(pasta_dest, exist_ok=True)

    # 🧹 1. EXCLUSÃO PRÉVIA DOS ARQUIVOS JPG ANTIGOS
    limpar_jpgs_antigos(caminho_saida_base)

    nome_base, ext = os.path.splitext(caminho_saida_base)
    if not ext:
        ext = ".JPG"

    # Geração de cada página JPG
    for num_pag in range(total_paginas):
        prods_pagina = produtos[num_pag * PRODUTOS_POR_PAGINA : (num_pag + 1) * PRODUTOS_POR_PAGINA]

        img = Image.new("RGB", (LARGURA_TOTAL, ALTURA_TOTAL), color="#FFFFFF")
        draw = ImageDraw.Draw(img)

        # 1. CABEÇALHO
        draw.rectangle([0, 0, LARGURA_TOTAL, ALTURA_CABECALHO], fill=cor_topo_rodape)
        
        logo_img = carregar_e_ajustar_imagem(config.get('cabecalho_logo'), 340, 130)
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

        draw.text((x_titulo, 40), texto_titulo, fill="#FFFFFF", font=font_titulo_bold)
        if texto_site:
            draw.text((x_site, 100), texto_site, fill="#E0E0E0", font=font_sub_regular)

        # 2. CARDS DE PRODUTOS
        for idx, prod in enumerate(prods_pagina):
            coluna = idx % COLUNAS
            linha = idx // COLUNAS

            x = MARGEM_LATERAL + coluna * (largura_card + ESPACO_HORIZ)
            y = MARGEM_TOPO + linha * (altura_card + ESPACO_VERT)

            draw.rectangle([x, y, x + largura_card, y + altura_card], outline="#BBBBBB", fill="#FAFAFA", width=3)

            cod_str = str(prod.get('codigo', '')).zfill(5)
            marca_str = str(prod.get('marca', '')).upper()
            draw.text((x + 20, y + 16), f"CÓD: {cod_str}", fill="#000000", font=font_cod_bold)
            if marca_str:
                draw.text((x + largura_card - 140, y + 16), marca_str[:12], fill="#555555", font=font_marca)

            area_foto_x, area_foto_y = x + 20, y + 48
            area_foto_w, area_foto_h = largura_card - 40, 270
            draw.rectangle([area_foto_x, area_foto_y, area_foto_x + area_foto_w, area_foto_y + area_foto_h], outline="#E0E0E0", fill="#FFFFFF")

            foto_prod = carregar_e_ajustar_imagem(prod.get('foto'), area_foto_w - 10, area_foto_h - 10)
            if foto_prod:
                px = area_foto_x + (area_foto_w - foto_prod.width) // 2
                py = area_foto_y + (area_foto_h - foto_prod.height) // 2
                img.paste(foto_prod, (px, py))
            else:
                draw.text((area_foto_x + (area_foto_w // 4), area_foto_y + 110), "[ SEM FOTO ]", fill="#CCCCCC", font=font_cod_bold)

            desc = str(prod.get('descricao', 'PRODUTO SEM DESCRIÇÃO'))[:28]
            draw.text((x + 20, y + 335), desc.upper(), fill="#000000", font=font_desc_bold)

            tarja_x1, tarja_y1 = x + 12, y + 380
            tarja_x2, tarja_y2 = x + largura_card - 12, y + 448
            draw.rectangle([tarja_x1, tarja_y1, tarja_x2, tarja_y2], fill=cor_tarja_bg)

            try:
                preco_val = float(str(prod.get('preco', 0)).replace(',', '.'))
            except ValueError:
                preco_val = 0.0
            preco_fmt = f"R$ {preco_val:.2f}".replace('.', ',')

            bbox_p = draw.textbbox((0, 0), preco_fmt, font=font_preco_bold)
            largura_p = bbox_p[2] - bbox_p[0]
            altura_p = bbox_p[3] - bbox_p[1]

            x_preco = tarja_x1 + ((tarja_x2 - tarja_x1) - largura_p) // 2
            y_preco = tarja_y1 + ((tarja_y2 - tarja_y1) - altura_p) // 2 - 4

            draw.text((x_preco, y_preco), preco_fmt, fill=cor_preco_texto, font=font_preco_bold)

        # 3. RODAPÉ
        y_rodape = ALTURA_TOTAL - ALTURA_RODAPE
        draw.rectangle([0, y_rodape, LARGURA_TOTAL, ALTURA_TOTAL], fill=cor_topo_rodape)

        contato_str = str(config.get('rodape_contato', '')).strip()
        fone_str = str(config.get('rodape_fone', '')).strip()
        ico_whats = carregar_e_ajustar_imagem(config.get('rodape_logo_fone'), 42, 42)

        texto_contato = f"{contato_str}   |" if contato_str else ""
        texto_fone = f"{fone_str}" if fone_str else ""

        bbox_c = draw.textbbox((0, 0), texto_contato, font=font_rod_destaque) if texto_contato else (0,0,0,0)
        bbox_f = draw.textbbox((0, 0), texto_fone, font=font_rod_destaque) if texto_fone else (0,0,0,0)

        larg_contato = bbox_c[2] - bbox_c[0]
        larg_fone    = bbox_f[2] - bbox_f[0]
        larg_ico     = (ico_whats.width + 15) if ico_whats else 0

        largura_total_l1 = larg_contato + larg_ico + larg_fone
        x_cursor = (LARGURA_TOTAL - largura_total_l1) // 2
        y_l1 = y_rodape + 30

        if texto_contato:
            draw.text((x_cursor, y_l1), texto_contato, fill="#FFFFFF", font=font_rod_destaque)
            x_cursor += larg_contato + 15

        if ico_whats:
            img.paste(ico_whats, (x_cursor, y_l1 - 4))
            x_cursor += larg_ico

        if texto_fone:
            draw.text((x_cursor, y_l1), texto_fone, fill="#FFFFFF", font=font_rod_destaque)

        validade_str = str(config.get('rodape_validade', '')).strip()
        if total_paginas > 1:
            validade_str += f"   (Página {num_pag + 1} de {total_paginas})"

        if validade_str:
            bbox_val = draw.textbbox((0, 0), validade_str, font=font_rod_validade)
            larg_val = bbox_val[2] - bbox_val[0]
            x_val = (LARGURA_TOTAL - larg_val) // 2
            y_l2 = y_rodape + 95
            draw.text((x_val, y_l2), validade_str, fill="#E0E0E0", font=font_rod_validade)

        # Definindo o nome de saída da página .JPG
        if total_paginas > 1:
            caminho_final_jpg = f"{nome_base}_{num_pag + 1}{ext}"
        else:
            caminho_final_jpg = f"{nome_base}{ext}"

        # 🔄 2. SALVA E FORÇA O FECHAMENTO DO BUFFER
        img.save(caminho_final_jpg, format="JPEG", quality=98)

    # 3. CHAMA O VISUALIZADOR SOMENTE APÓS TODAS AS PÁGINAS SEREM SALVAS
    try:
        caminho_vis = os.path.join(pasta_dest, "VISUALIZAR_CATALOGO.exe")
        primeira_pag = f"{nome_base}_1{ext}" if total_paginas > 1 else f"{nome_base}{ext}"
        
        if os.path.exists(caminho_vis):
            # Dispara o visualizador garantindo que o lote todo já foi gravado
            subprocess.Popen([caminho_vis, pasta_dest, primeira_pag])
    except Exception:
        pass

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

            renderizar_paginas_jpg(config, produtos, saida_cli)

    except Exception as e:
        with open("erro_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(traceback.format_exc())
