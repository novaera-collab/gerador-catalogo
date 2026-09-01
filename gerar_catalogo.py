import sys
import os
import io
import csv
import glob
import math
import subprocess
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw, ImageFont

def limpar_encartes_antigos(pasta_destino, nome_prefixo="CATALOGO_OESTE_PHARMA"):
    """Apaga todas as imagens de encartes gerados anteriormente para não misturar páginas."""
    if not os.path.exists(pasta_destino):
        return
    
    # Procura arquivos com o prefixo do encarte (.jpg, .jpeg, .png)
    padrao = os.path.join(pasta_destino, f"{nome_prefixo}*.*")
    for arquivo in glob.glob(padrao):
        if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
            try:
                os.remove(arquivo)
            except Exception:
                pass

def carregar_dados_csv(caminho_csv):
    """Lê o arquivo CSV exportado pelo ERP com os produtos e metadados."""
    produtos = []
    meta = {'fone': '', 'nome_contato': '', 'titulo': 'ENCARTE DE OFERTAS'}
    
    if not os.path.exists(caminho_csv):
        return produtos, meta

    for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            with open(caminho_csv, mode='r', encoding=enc) as f:
                reader = csv.DictReader(f, delimiter=';')
                if not reader.fieldnames:
                    reader = csv.DictReader(f, delimiter=',')
                
                if reader.fieldnames:
                    field_map = {col.strip().lower().replace('\ufeff', ''): col for col in reader.fieldnames}
                    
                    for row in reader:
                        # Lê metadados na primeira linha válida
                        if not meta['fone'] and 'contato_whatsapp' in field_map:
                            meta['fone'] = row.get(field_map['contato_whatsapp'], '').strip()
                        if 'titulo_encarte' in field_map and row.get(field_map['titulo_encarte']):
                            meta['titulo'] = row.get(field_map['titulo_encarte'], '').strip()

                        # Lê dados do produto
                        prod = {
                            'codigo': row.get(field_map.get('codigo', ''), '').strip(),
                            'descricao': row.get(field_map.get('descricao', ''), '').strip(),
                            'fabricante': row.get(field_map.get('fabricante', ''), '').strip(),
                            'preco': row.get(field_map.get('preco', ''), '').strip(),
                            'imagem': row.get(field_map.get('imagem', ''), '').strip()
                        }
                        if prod['descricao'] or prod['codigo']:
                            produtos.append(prod)
                    break
        except Exception:
            continue

    return produtos, meta

def gerar_encarte_completo(caminho_csv, caminho_saida_base):
    """Gera todas as páginas do encarte em JPG e aciona o visualizador."""
    pasta_destino = os.path.dirname(caminho_saida_base) or os.getcwd()
    nome_base_limpo = os.path.splitext(os.path.basename(caminho_saida_base))[0]

    # 1. 🧹 LIMPEZA PRÉVIA: Apaga imagens antigas antes de gerar as novas
    limpar_encartes_antigos(pasta_destino, nome_prefixo=nome_base_limpo)

    # 2. Carrega produtos do CSV
    produtos, meta = carregar_dados_csv(caminho_csv)
    if not produtos:
        messagebox.showerror("Erro", f"Nenhum produto encontrado no CSV:\n{caminho_csv}")
        return

    # Configurações de layout (Grid de 3 colunas x 3 linhas = 9 produtos por página)
    PRODS_POR_PAGINA = 9
    LARGURA_PAGINA = 1200
    ALTURA_PAGINA = 1600
    total_paginas = math.ceil(len(produtos) / PRODS_POR_PAGINA)

    font_titulo = ImageFont.load_default()
    font_prod = ImageFont.load_default()

    # 3. Renderiza cada página
    for pag in range(total_paginas):
        img_pagina = Image.new("RGB", (LARGURA_PAGINA, ALTURA_PAGINA), "white")
        draw = ImageDraw.Draw(img_pagina)

        # Cabeçalho
        draw.rectangle([(0, 0), (LARGURA_PAGINA, 120)], fill="#22702C")
        draw.text((30, 40), meta['titulo'].upper(), fill="white", font=font_titulo)

        # Produtos da página atual
        inicio_idx = pag * PRODS_POR_PAGINA
        prods_pagina = produtos[inicio_idx:inicio_idx + PRODS_POR_PAGINA]

        for idx, prod in enumerate(prods_pagina):
            col = idx % 3
            lin = idx // 3
            
            x = 40 + col * 380
            y = 150 + lin * 450

            # Card do Produto
            draw.rectangle([(x, y), (x + 360, y + 430)], outline="#cccccc", width=2)
            
            # Tenta carregar imagem do produto
            if prod['imagem'] and os.path.exists(prod['imagem']):
                try:
                    img_p = Image.open(prod['imagem'])
                    img_p.thumbnail((300, 220))
                    img_pagina.paste(img_p, (x + 30, y + 20))
                except Exception:
                    draw.text((x + 50, y + 100), "[SEM IMAGEM]", fill="#888888", font=font_prod)
            else:
                draw.text((x + 50, y + 100), "[SEM IMAGEM]", fill="#888888", font=font_prod)

            # Texto do Produto
            draw.text((x + 15, y + 250), f"CÓD: {prod['codigo']}", fill="#333333", font=font_prod)
            draw.text((x + 15, y + 280), prod['descricao'][:30], fill="#000000", font=font_prod)
            
            # Preço
            draw.rectangle([(x + 15, y + 360), (x + 345, y + 410)], fill="#22702C")
            draw.text((x + 100, y + 372), f"R$ {prod['preco']}", fill="white", font=font_titulo)

        # Rodapé
        draw.text((LARGURA_PAGINA - 200, ALTURA_PAGINA - 30), f"Página {pag + 1} de {total_paginas}", fill="#666666", font=font_prod)

        # 4. Salva o arquivo JPG da página (ex: CATALOGO_OESTE_PHARMA_1.JPG)
        if total_paginas > 1:
            nome_arquivo_pag = f"{nome_base_limpo}_{pag + 1}.JPG"
        else:
            nome_arquivo_pag = f"{nome_base_limpo}_1.JPG"
            
        caminho_final_jpg = os.path.join(pasta_destino, nome_arquivo_pag)
        img_pagina.save(caminho_final_jpg, "JPEG", quality=90)

    # 5. Chama o Visualizador APÓS garantir a gravação completa no disco
    caminho_vis = os.path.join(pasta_destino, "VISUALIZAR_CATALOGO.exe")
    primeira_pagina_jpg = os.path.join(pasta_destino, f"{nome_base_limpo}_1.JPG")

    if os.path.exists(caminho_vis):
        subprocess.Popen([caminho_vis, pasta_destino, primeira_pagina_jpg])

if __name__ == "__main__":
    # Suporta receber o caminho do CSV por argumento ou padrão
    caminho_csv_param = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "Downloads", "CATALOGO_OESTE_PHARMA.csv")
    caminho_jpg_param = os.path.splitext(caminho_csv_param)[0] + ".JPG"

    gerar_encarte_completo(caminho_csv_param, caminho_jpg_param)
