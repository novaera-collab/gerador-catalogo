import sys
import os
import csv
import traceback
from PIL import Image, ImageDraw, ImageFont

# ... [sua função gerar_catalogo_3_colunas continua igual] ...

if __name__ == "__main__":
    try:
        if len(sys.argv) >= 3:
            arquivo_csv = sys.argv[1]
            caminho_saida = sys.argv[2]

            if not os.path.exists(arquivo_csv):
                raise FileNotFoundError(f"O arquivo CSV nao foi encontrado em: {arquivo_csv}")

            produtos = []
            titulo = "OFERTAS DA SEMANA"
            dt_ini = ""
            dt_fim = ""

            # Tenta abrir o CSV com utf-8 ou latin-1
            try:
                with open(arquivo_csv, mode='r', encoding='utf-8-sig') as f:
                    # Tenta detectar se o separador é ';' ou ','
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
            except UnicodeDecodeError:
                with open(arquivo_csv, mode='r', encoding='latin-1') as f:
                    reader = csv.DictReader(f, delimiter=';')
                    for row in reader:
                        produtos.append({
                            'codigo': row.get('codigo', row.get('CODIGO', '')),
                            'descricao': row.get('descricao', row.get('DESCRICAO', '')),
                            'preco': row.get('preco', row.get('PRECO', 0))
                        })

            gerar_catalogo_3_colunas(titulo, dt_ini, dt_fim, produtos, caminho_saida)

    except Exception as e:
        # Se der qualquer erro, grava um arquivo 'erro_log.txt' na mesma pasta
        with open("erro_log.txt", "w", encoding="utf-8") as f_err:
            f_err.write(traceback.format_exc())
