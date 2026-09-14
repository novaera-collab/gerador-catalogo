import os
import glob
from PIL import Image, ImageDraw, ImageFont

# --- CONSTANTES DE DIAGRAMAÇÃO ---
ALTURA_TOTAL_FIXA = 1920
MARGEM_TOPO_CONTEUDO = 300
ALTURA_RODAPE = 150
ESPACO_VERT = 30


def limpar_jpgs_antigos(caminho_saida_base):
    """Remove páginas antigas geradas no mesmo diretório para evitar conflitos."""
    abs_path = os.path.abspath(caminho_saida_base)
    diretorio, nome_arquivo = os.path.split(abs_path)
    nome_base, _ = os.path.splitext(nome_arquivo)
    
    padrao = os.path.join(diretorio, f"{nome_base}*.jpg")
    for arquivo in glob.glob(padrao):
        try:
            os.remove(arquivo)
        except OSError as e:
            print(f"Aviso: Não foi possível remover o arquivo antigo {arquivo}: {e}")


def desenhar_cabecalho_e_rodape(img, pag_num):
    """Gera elementos visuais padrão de cada página."""
    draw = ImageDraw.Draw(img)
    
    # Exemplo de Cabeçalho (Fundo azul escuro)
    draw.rectangle([0, 0, img.width, 250], fill=(20, 40, 80))
    draw.text((50, 80), "CATÁLOGO DE PRODUTOS", fill=(255, 255, 255))
    
    # Exemplo de Rodapé
    draw.rectangle([0, img.height - ALTURA_RODAPE, img.width, img.height], fill=(240, 240, 240))
    draw.text((img.width - 200, img.height - 80), f"Página {pag_num}", fill=(100, 100, 100))


def desenhar_card_produto(img, produto, x, y, largura, altura):
    """Desenha o card individual do produto no canvas."""
    draw = ImageDraw.Draw(img)
    
    # Fundo do card
    cor_fundo = (255, 245, 230) if produto.get('destaque') == 'S' else (245, 245, 245)
    draw.rectangle([x, y, x + largura, y + altura], fill=cor_fundo, outline=(200, 200, 200))
    
    # Texto do Produto
    nome = produto.get('nome', 'Produto Sem Nome')
    preco = f"R$ {produto.get('preco', 0.0):.2f}"
    
    draw.text((x + 15, y + 15), nome, fill=(0, 0, 0))
    draw.text((x + 15, y + altura - 35), preco, fill=(0, 128, 0))


def renderizar_catalogo(config, produtos, caminho_saida_base):
    """Renderiza todas as páginas do catálogo e salva os arquivos JPG."""
    if not produtos:
        print("Erro: A lista de produtos está vazia. Nenhum arquivo foi gerado.")
        return

    # Garante que o diretório de destino exista
    caminho_abs = os.path.abspath(caminho_saida_base)
    diretorio_destinatario = os.path.dirname(caminho_abs)
    if diretorio_destinatario and not os.path.exists(diretorio_destinatario):
        os.makedirs(diretorio_destinatario, exist_ok=True)

    limpar_jpgs_antigos(caminho_saida_base)

    # Configurações de dimensão
    largura_canvas = config.get('largura', 1080)
    altura_canvas = config.get('altura', ALTURA_TOTAL_FIXA)
    alt_card_norm = config.get('altura_card', 200)
    largura_card = config.get('largura_card', 1000)
    
    # Cálculo seguro da área utilizável para evitar loop infinito
    espaco_util_altura = altura_canvas - MARGEM_TOPO_CONTEUDO - ALTURA_RODAPE
    passo_altura = alt_card_norm + ESPACO_VERT
    
    max_items_page = max(1, espaco_util_altura // passo_altura)

    fuga_produtos = list(produtos)  # Cópia de trabalho da lista
    pag_num = 1
    nome_base, ext = os.path.splitext(caminho_abs)
    extensao = ext if ext else ".jpg"

    while fuga_produtos:
        # Cria uma nova imagem em branco para a página atual
        img = Image.new("RGB", (largura_canvas, altura_canvas), (255, 255, 255))
        desenhar_cabecalho_e_rodape(img, pag_num)

        pos_y = MARGEM_TOPO_CONTEUDO
        pos_x = (largura_canvas - largura_card) // 2
        itens_na_pagina = 0

        # Preenche a página até atingir o limite de itens por página
        while fuga_produtos and itens_na_pagina < max_items_page:
            prod = fuga_produtos.pop(0)
            desenhar_card_produto(img, prod, pos_x, pos_y, largura_card, alt_card_norm)
            
            pos_y += passo_altura
            itens_na_pagina += 1

        # Definição e salvamento do arquivo JPG
        caminho_final = f"{nome_base}_pag_{pag_num}{extensao}" if pag_num > 1 else f"{nome_base}{extensao}"
        
        try:
            img.save(caminho_final, format="JPEG", quality=95)
            print(f"[Sucesso] Arquivo salvo em: {caminho_final}")
        except Exception as e:
            print(f"[Erro] Falha ao gravar a imagem {caminho_final}: {e}")

        pag_num += 1


# --- BLOCO DE TESTE ---
if __name__ == "__main__":
    config_app = {
        'largura': 1080,
        'altura': 1920,
        'altura_card': 220,
        'largura_card': 980
    }

    # Dados de exemplo para validar a renderização
    produtos_mock = [
        {"nome": f"Produto Exemplo {i}", "preco": 29.90 + (i * 5), "destaque": "S" if i % 4 == 0 else "N"}
        for i in range(1, 18)
    ]

    renderizar_catalogo(config_app, produtos_mock, "saida/CATALOGO_FINAL.JPG")
