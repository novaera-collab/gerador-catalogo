import sys
import os
import csv
import traceback
from PIL import Image, ImageDraw, ImageFont

# 1. NOME DA FUNÇÃO DEFINIDO AQUI:
def gerar_catalogo_3_colunas(titulo, dt_ini, dt_fim, produtos, caminho_saida):
    COLUNAS = 3
    LARGURA_TOTAL = 1200
    MARGEM_LATERAL = 40
    MARGEM_TOPO = 180
    ESPACO_HORIZ = 20
    ESPACO_VERT = 20

    largura_util = LARGURA_TOTAL - (MARGEM_LATERAL * 2) - (ESPACO_HORIZ * (COLUNAS - 1))
    largura_card = largura_util // COLUNAS
    altura_card = 360

    num_produtos = len(produtos)
    linhas = (num_produtos + COLUNAS - 1) // COLUNAS if num_produtos > 0 else 1
    altura_total = MARGEM_TOPO + linhas * (altura_card + ESPACO_VERT) + 50

    img = Image.new("RGB", (LARGURA_TOTAL, max(altura_total, 800)), color="#FFFFFF")
    draw = ImageDraw.Draw(img)

    try:
        font_titulo = ImageFont.truetype("arial.ttf", 34)
        font_sub = ImageFont.truetype("arial.ttf", 20)
        font_cod = ImageFont.truetype("arial.ttf", 16)
        font_desc = ImageFont.truetype("arial.ttf", 18)
        font_preco = ImageFont.truetype("arial.ttf", 28)
    except IOError:
        font_titulo = font_sub = font_cod = font_desc = font_preco = ImageFont.load_default()

    # Cabeçalho
    draw.rectangle([0, 0, LARGURA_TOTAL, 140], fill="#1B5E20")
    draw.text((MARGEM_LATERAL, 30), str(titulo).upper(), fill="#FFFFFF", font=font_titulo)
    draw.text((MARGEM_LATERAL, 85), f"OFERTAS VÁLIDAS DE {dt_ini} ATÉ {dt_fim}", fill="#A5D6A7", font=font_sub)

    # Renderização dos Cards
    for idx, prod in enumerate(produtos):
        coluna = idx % COLUNAS
        linha = idx // COLUNAS

        x = MARGEM_LATERAL + coluna * (largura_card + ESPACO_HORIZ)
        y = MARGEM_TOPO + linha * (altura_card + ESPACO_VERT)

        draw.rectangle([x, y, x + largura_card, y + altura_card], outline="#DDDDDD", fill="#FAFAFA", width=2)

        cod_str = str(prod.get('codigo', '')).zfill(5)
        draw.text((x + 15, y + 15), f"CÓD: {cod_str}", fill="#555555", font=font_cod)

        draw.rectangle([x + 20, y + 45, x + largura_card - 20, y + 210], outline="#EEEEEE", fill="#FFFFFF")
        draw.text((x + (largura_card // 4), y + 115), "[ FOTO ]", fill="#CCCCCC", font=font_cod)

        desc = str(prod.get('descricao', 'PRODUTO SEM DESCRIÇÃO'))[:24]
        draw.text((x + 15, y + 225), desc.upper(), fill="#333333", font=font_desc)

        draw.rectangle([x + 10, y + 270, x + largura_card - 10, y + 340], fill="#D32F2F")
        try:
            preco_val = float(str(prod.get('preco', 0)).replace(',', '.'))
        except ValueError:
            preco_val = 0.0
        preco_fmt = f"R$ {preco_val:.2f}".replace('.', ',')
        draw.text((x + 25, y + 288), preco_fmt, fill="#FFFFFF", font=font_preco)

    pasta_destino = os.path.dirname(caminho_saida)
    if pasta_destino and not os.path.exists(pasta_destino):
        os.makedirs(pasta_destino, exist_ok=True)

    img.save(caminho_saida, quality=95)


# 2. EXECUÇÃO PRINCIPAL
if __name__ == "__main__":
    try:
        if len(sys.argv) >= 3:
            arquivo_csv = sys.argv[1]
            caminho_saida = sys.argv[2]

            produtos = []
            titulo = "OFERTAS DA SEMANA"
            dt_ini = ""
            dt_fim = ""

            if os.path.exists(arquivo_csv):
                with open(arquivo_csv, mode='r', encoding='utf-8-sig') as f:
                    primeira_linha = f.readline()
                    f.seek(0)
                    delim = ';' if ';' in primeira_linha else ','
                    
                    reader = csv.DictReader(f, delimiter=delim)
                    for row in reader:
                        produtos.append({
                            'codigo': row.get('codigo', row.get('CODIGO', '')),
                            'descricao': row.get('descricao', row.get('DESCRICAO', '')),
                            'preco': row.get('preco', row.get('PRECO', 0))
                        })

            # MESMO NOME CHAMADO AQUI:
            gerar_catalogo_3_colunas(titulo, dt_ini, dt_fim, produtos, caminho_saida)

    except Exception as e:
        with open("erro_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(traceback.format_exc())
