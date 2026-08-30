# -*- coding: utf-8 -*-
import sys
import os
import json
import traceback
import subprocess
import base64
import customtkinter as ctk
from datetime import datetime, date
from tkinter import messagebox, Toplevel, filedialog
import psycopg2
from psycopg2.extras import RealDictCursor
from tkcalendar import DateEntry

# Ocultar o console/terminal do Windows no momento da execução
if sys.platform.startswith("win"):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def mostrar_erro_fatal(exc_type, exc_value, exc_traceback):
    erro_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    messagebox.showerror("Erro Fatal na Inicialização", f"Ocorreu um erro ao abrir o app:\n\n{erro_msg}")

sys.excepthook = mostrar_erro_fatal

CONFIG_FILE = "config_banco.json"

QUERY_DEFAULT = """SELECT 
    p.fco AS CODIGO,
    CASE 
        WHEN COALESCE(p.fcomplemen, '') <> '' THEN p.fcomplemen 
        ELSE p.fdescricao 
    END AS DESCRICAO,
    STRING_AGG(
        CONCAT('A partir de ', item.qtde_oferta, ' un. R$ ', REPLACE(CAST(item.preco_oferta AS DECIMAL(10,2))::text, '.', ',')),
        ' | ' ORDER BY item.ordem ASC, item.qtde_oferta ASC
    ) AS LINHA_PRECO
FROM encarte_item item
JOIN esprod p ON CAST(p.fco AS TEXT) = LPAD(CAST(item.codigo_prod AS TEXT), 5, '0')
WHERE item.encarte_id = {ID_ENCARTE}
GROUP BY p.fco, p.fcomplemen, p.fdescricao;"""

# ==============================================================================
# FUNÇÕES DE CRIPTOGRAFIA / OFUSCAÇÃO NATIVA (BASE64)
# ==============================================================================
def encriptar_texto(texto):
    if not texto:
        return ""
    try:
        return base64.b64encode(texto.encode('utf-8')).decode('utf-8')
    except Exception:
        return texto

def decriptar_texto(texto_cripto):
    if not texto_cripto:
        return ""
    try:
        return base64.b64decode(texto_cripto.encode('utf-8')).decode('utf-8')
    except Exception:
        return texto_cripto

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "password" in cfg:
                    cfg["password"] = decriptar_texto(cfg["password"])
                if "query_csv" not in cfg or not cfg["query_csv"].strip():
                    cfg["query_csv"] = QUERY_DEFAULT
                return cfg
        except Exception:
            pass
    return {
        "host": "localhost",
        "database": "seu_banco",
        "user": "postgres",
        "password": "",
        "port": "5432",
        "schema": "public",
        "dir_encarte": "",
        "dir_csv": "",
        "dir_jpg": "",
        "path_logo": "",
        "path_logo_whats": "",
        "query_csv": QUERY_DEFAULT
    }

def salvar_config(cfg):
    cfg_copy = cfg.copy()
    if "password" in cfg_copy:
        cfg_copy["password"] = encriptar_texto(cfg_copy["password"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg_copy, f, indent=4)

def get_connection():
    cfg = carregar_config()
    return psycopg2.connect(
        host=cfg.get("host", "localhost"),
        database=cfg.get("database", "seu_banco"),
        user=cfg.get("user", "postgres"),
        password=cfg.get("password", ""),
        port=cfg.get("port", "5432"),
        cursor_factory=RealDictCursor
    )

def get_schema():
    cfg = carregar_config()
    schema = cfg.get("schema", "public").strip()
    return schema if schema else "public"

# ==============================================================================
# JANELA DE PARÂMETROS DA CONEXÃO, DIRETÓRIOS E QUERY SQL
# ==============================================================================
class ParametrosWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Parâmetros do Sistema")
        
        largura, altura = 640, 530
        pos_x = (self.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = max(10, (self.winfo_screenheight() // 2) - (altura // 2) - 30)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        self.grab_set()

        cfg = carregar_config()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=15, pady=10)

        tab_banco = tabview.add("Conexão Banco")
        tab_dirs = tabview.add("Diretórios e Arquivos")
        tab_sql = tabview.add("Query de Geração (CSV)")

        # --- ABA 1: BANCO DE DADOS ---
        ctk.CTkLabel(tab_banco, text="Host / IP:").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.txt_host = ctk.CTkEntry(tab_banco, width=320)
        self.txt_host.insert(0, cfg.get("host", ""))
        self.txt_host.grid(row=0, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Banco de Dados:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.txt_db = ctk.CTkEntry(tab_banco, width=320)
        self.txt_db.insert(0, cfg.get("database", ""))
        self.txt_db.grid(row=1, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Schema:").grid(row=2, column=0, padx=10, pady=6, sticky="w")
        self.txt_schema = ctk.CTkEntry(tab_banco, width=320, placeholder_text="ex: public ou encartes_app")
        self.txt_schema.insert(0, cfg.get("schema", "public"))
        self.txt_schema.grid(row=2, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Usuário:").grid(row=3, column=0, padx=10, pady=6, sticky="w")
        self.txt_user = ctk.CTkEntry(tab_banco, width=320)
        self.txt_user.insert(0, cfg.get("user", ""))
        self.txt_user.grid(row=3, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Senha:").grid(row=4, column=0, padx=10, pady=6, sticky="w")
        self.txt_pass = ctk.CTkEntry(tab_banco, width=320, show="*")
        self.txt_pass.insert(0, cfg.get("password", ""))
        self.txt_pass.grid(row=4, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Porta:").grid(row=5, column=0, padx=10, pady=6, sticky="w")
        self.txt_port = ctk.CTkEntry(tab_banco, width=320)
        self.txt_port.insert(0, cfg.get("port", "5432"))
        self.txt_port.grid(row=5, column=1, padx=10, pady=6)

        # --- ABA 2: DIRETÓRIOS E LOGOS ---
        self.txt_dir_encarte = self._criar_campo_caminho(tab_dirs, "Diretório Encarte:", 0, cfg.get("dir_encarte", ""), pasta=True)
        self.txt_dir_csv = self._criar_campo_caminho(tab_dirs, "Diretório CSV:", 1, cfg.get("dir_csv", ""), pasta=True)
        self.txt_dir_jpg = self._criar_campo_caminho(tab_dirs, "Diretório JPG:", 2, cfg.get("dir_jpg", ""), pasta=True)
        self.txt_logo = self._criar_campo_caminho(tab_dirs, "Logo Principal:", 3, cfg.get("path_logo", ""), pasta=False)
        self.txt_logo_whats = self._criar_campo_caminho(tab_dirs, "Logo WhatsApp:", 4, cfg.get("path_logo_whats", ""), pasta=False)

        # --- ABA 3: QUERY DE GERAÇÃO DO CSV ---
        frame_info_sql = ctk.CTkFrame(tab_sql, fg_color="#1E282C", border_width=1, border_color="#37474F")
        frame_info_sql.pack(fill="x", padx=5, pady=(5, 8))

        info_text = (
            " ❗ REGRAS E ESTRUTURA OBRIGATÓRIA DA QUERY:\n"
            " • Use obrigatoriamente a tag {ID_ENCARTE} onde o ID do encarte deve ser injetado.\n"
            " • A consulta DEVE retornar as seguintes colunas (exatas):\n"
            "   1. CODIGO      -> Código do produto (string formatada ex: 00019)\n"
            "   2. DESCRICAO   -> Nome do produto a ser impresso\n"
            "   3. LINHA_PRECO -> String pronta das faixas ex: 'A partir de 1 un. R$ 5,00 | A partir de 10 un. R$ 4,50'"
        )
        lbl_info = ctk.CTkLabel(frame_info_sql, text=info_text, justify="left", font=ctk.CTkFont(size=11), text_color="#FFF59D")
        lbl_info.pack(padx=8, pady=6, anchor="w")

        self.txt_query_sql = ctk.CTkTextbox(tab_sql, font=ctk.CTkFont(family="Consolas", size=12))
        self.txt_query_sql.pack(fill="both", expand=True, padx=5, pady=5)
        self.txt_query_sql.insert("1.0", cfg.get("query_csv", QUERY_DEFAULT))

        btn_reset_sql = ctk.CTkButton(tab_sql, text="Restaurar SQL Padrão", width=140, fg_color="#455A64", command=self.restaurar_sql_default)
        btn_reset_sql.pack(anchor="w", padx=5, pady=(0, 5))

        btn_salvar = ctk.CTkButton(self, text="Salvar Tudo", fg_color="#1B5E20", font=ctk.CTkFont(weight="bold"), height=35, command=self.salvar)
        btn_salvar.pack(pady=(0, 12))

    def _criar_campo_caminho(self, parent, label_text, row, valor_inicial, pasta=True):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        txt_entry = ctk.CTkEntry(parent, width=280)
        txt_entry.insert(0, valor_inicial)
        txt_entry.grid(row=row, column=1, padx=5, pady=6)

        btn_procurar = ctk.CTkButton(
            parent, text="Buscar", width=60, 
            command=lambda: self._selecionar_caminho(txt_entry, pasta)
        )
        btn_procurar.grid(row=row, column=2, padx=5, pady=6)
        return txt_entry

    def _selecionar_caminho(self, entry_widget, pasta=True):
        if pasta:
            caminho = filedialog.askdirectory(parent=self, title="Selecione a Pasta")
        else:
            caminho = filedialog.askopenfilename(
                parent=self,
                title="Selecione o Arquivo", 
                filetypes=[("Imagens / Executáveis", "*.png *.jpg *.jpeg *.exe"), ("Todos os Arquivos", "*.*")]
            )
        
        if caminho:
            caminho_formatado = caminho.replace("/", "\\")
            entry_widget.delete(0, "end")
            entry_widget.insert(0, caminho_formatado)

    def restaurar_sql_default(self):
        self.txt_query_sql.delete("1.0", "end")
        self.txt_query_sql.insert("1.0", QUERY_DEFAULT)

    def salvar(self):
        query_digitada = self.txt_query_sql.get("1.0", "end").strip()
        if "{ID_ENCARTE}" not in query_digitada:
            messagebox.showwarning("Atenção no SQL", "A sua query SQL precisa conter a tag {ID_ENCARTE}!", parent=self)
            return

        cfg = {
            "host": self.txt_host.get().strip(),
            "database": self.txt_db.get().strip(),
            "schema": self.txt_schema.get().strip(),
            "user": self.txt_user.get().strip(),
            "password": self.txt_pass.get().strip(),
            "port": self.txt_port.get().strip(),
            "dir_encarte": self.txt_dir_encarte.get().strip(),
            "dir_csv": self.txt_dir_csv.get().strip(),
            "dir_jpg": self.txt_dir_jpg.get().strip(),
            "path_logo": self.txt_logo.get().strip(),
            "path_logo_whats": self.txt_logo_whats.get().strip(),
            "query_csv": query_digitada
        }
        salvar_config(cfg)
        messagebox.showinfo("Sucesso", "Todos os parâmetros e a Query SQL foram salvos!", parent=self)
        self.destroy()

# ==============================================================================
# JANELA MODAL DE PESQUISA DE PRODUTO
# ==============================================================================
class PesquisaProdutoModal(ctk.CTkToplevel):
    def __init__(self, parent, callback_selecao):
        super().__init__(parent)
        self.parent = parent
        self.callback_selecao = callback_selecao

        self.title("Pesquisa de Produtos (ESPROD)")
        largura, altura = 700, 460
        pos_x = (self.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = max(10, (self.winfo_screenheight() // 2) - (altura // 2) - 30)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        self.grab_set()

        frame_busca = ctk.CTkFrame(self)
        frame_busca.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(frame_busca, text="Buscar Por:").pack(side="left", padx=5)
        self.txt_busca = ctk.CTkEntry(frame_busca, width=320, placeholder_text="Digite o Código, Descrição ou Complemento...")
        self.txt_busca.pack(side="left", padx=5)
        self.txt_busca.bind("<Return>", lambda e: self.pesquisar())

        btn_buscar = ctk.CTkButton(frame_busca, text="Pesquisar", width=100, command=self.pesquisar)
        btn_buscar.pack(side="left", padx=5)

        self.frame_resultados = ctk.CTkScrollableFrame(self)
        self.frame_resultados.pack(fill="both", expand=True, padx=15, pady=5)

    def pesquisar(self):
        termo = self.txt_busca.get().strip()
        for w in self.frame_resultados.winfo_children():
            w.destroy()

        if not termo:
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            query = """
                SELECT 
                    fco, 
                    CASE 
                        WHEN COALESCE(fcomplemen, '') <> '' THEN fcomplemen 
                        ELSE fdescricao 
                    END AS nome_exibicao
                FROM esprod 
                WHERE COALESCE(CAST(fco AS TEXT), '') || ' ' || COALESCE(fdescricao, '') || ' ' || COALESCE(fcomplemen, '') ILIKE %s
                LIMIT 50
            """
            like_term = f"%{termo}%"
            cur.execute(query, (like_term,))
            produtos = cur.fetchall()
            conn.close()

            if not produtos:
                ctk.CTkLabel(self.frame_resultados, text="Nenhum produto encontrado.", text_color="gray").pack(pady=20)
                return

            for prod in produtos:
                cod_str = str(prod['fco']).zfill(5)
                nome_prod = prod['nome_exibicao'] or ''

                row = ctk.CTkFrame(self.frame_resultados)
                row.pack(fill="x", pady=2, padx=2)

                ctk.CTkLabel(row, text=f"[{cod_str}]", width=80, font=ctk.CTkFont(weight="bold"), text_color="#A5D6A7").pack(side="left", padx=5)
                ctk.CTkLabel(row, text=nome_prod, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

                btn_sel = ctk.CTkButton(row, text="Selecionar", width=80, fg_color="#2E7D32", command=lambda c=cod_str: self.selecionar(c))
                btn_sel.pack(side="right", padx=5)

        except Exception as e:
            messagebox.showerror("Erro na Pesquisa", f"Erro ao consultar esprod:\n{e}", parent=self)

    def selecionar(self, codigo_formatted):
        self.callback_selecao(codigo_formatted)
        self.destroy()

# ==============================================================================
# FORMULÁRIO DE CADASTRO / ALTERAÇÃO DE ENCARTE
# ==============================================================================
class FormEncarteWindow(ctk.CTkToplevel):
    def __init__(self, parent, encarte_id=None, callback_refresh=None):
        super().__init__(parent)
        self.encarte_id = encarte_id
        self.callback_refresh = callback_refresh
        self.itens = []

        self.title("Alteração de Encarte" if encarte_id else "Novo Encarte")
        
        largura, altura = 820, 500
        pos_x = (self.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = max(10, (self.winfo_screenheight() // 2) - (altura // 2) - 40)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")
        self.grab_set()

        self.criar_widgets()
        if self.encarte_id:
            self.carregar_dados()

    def criar_widgets(self):
        frame_top_bar = ctk.CTkFrame(self, fg_color="transparent")
        frame_top_bar.pack(fill="x", padx=15, pady=(5, 2))

        lbl_titulo = ctk.CTkLabel(frame_top_bar, text="Manutenção do Encarte", font=ctk.CTkFont(size=16, weight="bold"))
        lbl_titulo.pack(side="left")

        btn_voltar = ctk.CTkButton(frame_top_bar, text="Voltar", width=70, height=26, fg_color="#455A64", command=self.destroy)
        btn_voltar.pack(side="right")

        frame_head = ctk.CTkFrame(self)
        frame_head.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(frame_head, text="Título:").grid(row=0, column=0, padx=6, pady=3, sticky="w")
        self.txt_titulo = ctk.CTkEntry(frame_head, width=380, placeholder_text="Ex: ENCARTE FARMAX")
        self.txt_titulo.grid(row=0, column=1, columnspan=3, padx=6, pady=3, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Início:").grid(row=1, column=0, padx=6, pady=3, sticky="w")
        self.txt_dt_ini = ctk.CTkEntry(frame_head, width=110, placeholder_text="29/08/2026")
        self.txt_dt_ini.grid(row=1, column=1, padx=(6, 2), pady=3, sticky="w")
        btn_cal_ini = ctk.CTkButton(frame_head, text="Cal", width=35, height=26, command=lambda: self.abrir_calendario(self.txt_dt_ini))
        btn_cal_ini.grid(row=1, column=1, padx=(120, 0), pady=3, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Fim:").grid(row=1, column=2, padx=6, pady=3, sticky="w")
        self.txt_dt_fim = ctk.CTkEntry(frame_head, width=110, placeholder_text="05/09/2026")
        self.txt_dt_fim.grid(row=1, column=3, padx=(6, 2), pady=3, sticky="w")
        btn_cal_fim = ctk.CTkButton(frame_head, text="Cal", width=35, height=26, command=lambda: self.abrir_calendario(self.txt_dt_fim))
        btn_cal_fim.grid(row=1, column=3, padx=(120, 0), pady=3, sticky="w")

        # PAINEL DE INCLUSÃO DE PRODUTO
        frame_prod = ctk.CTkFrame(self)
        frame_prod.pack(fill="x", padx=15, pady=3)

        ctk.CTkLabel(frame_prod, text="Cód. Prod:").grid(row=0, column=0, padx=4, pady=3)
        
        self.txt_p_cod = ctk.CTkEntry(frame_prod, width=75, placeholder_text="00001")
        self.txt_p_cod.grid(row=0, column=1, padx=(4, 2), pady=3)
        self.txt_p_cod.bind("<FocusOut>", self.formatar_codigo_evento)

        btn_lupa = ctk.CTkButton(frame_prod, text="Lupa", width=42, height=26, fg_color="#1976D2", command=self.abrir_lupa)
        btn_lupa.grid(row=0, column=2, padx=(0, 6), pady=3)

        ctk.CTkLabel(frame_prod, text="A partir de:").grid(row=0, column=3, padx=2, pady=3)
        self.txt_p_qtde = ctk.CTkEntry(frame_prod, width=60, placeholder_text="1.00")
        self.txt_p_qtde.insert(0, "1")
        self.txt_p_qtde.grid(row=0, column=4, padx=(2, 2), pady=3)
        ctk.CTkLabel(frame_prod, text="unid.", text_color="gray").grid(row=0, column=5, padx=(0, 6), pady=3)

        ctk.CTkLabel(frame_prod, text="Valor Oferta (R$):").grid(row=0, column=6, padx=2, pady=3)
        self.txt_p_preco = ctk.CTkEntry(frame_prod, width=85, placeholder_text="0.00")
        self.txt_p_preco.grid(row=0, column=7, padx=4, pady=3)

        btn_add = ctk.CTkButton(frame_prod, text="+ Adicionar", width=85, height=28, fg_color="#2E7D32", command=self.adicionar_item)
        btn_add.grid(row=0, column=8, padx=6, pady=3)

        # ÁREA DA LISTA
        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=3)

        # BARRA DE AÇÕES INFERIOR
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=15, pady=(2, 6))

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar no Banco", font=ctk.CTkFont(weight="bold"), fg_color="#1B5E20", height=32, width=130, command=self.salvar_banco)
        btn_salvar.pack(side="right", padx=5)

        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#C62828", height=32, width=100, command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

    def formatar_codigo_5_digitos(self, valor):
        valor_limpo = str(valor).strip()
        if valor_limpo.isdigit():
            return valor_limpo.zfill(5)
        return valor_limpo

    def formatar_codigo_evento(self, event):
        val = self.txt_p_cod.get()
        if val:
            self.txt_p_cod.delete(0, 'end')
            self.txt_p_cod.insert(0, self.formatar_codigo_5_digitos(val))

    def abrir_lupa(self):
        PesquisaProdutoModal(self, callback_selecao=self.definir_codigo_produto)

    def definir_codigo_produto(self, codigo_formatted):
        self.txt_p_cod.delete(0, 'end')
        self.txt_p_cod.insert(0, codigo_formatted)

    def abrir_calendario(self, entry_target):
        top = Toplevel(self)
        top.title("Escolha a Data")
        top.geometry("260x230")
        top.grab_set()

        cal = DateEntry(top, selectmode='day', locale='pt_BR', date_pattern='dd/mm/yyyy')
        cal.pack(pady=20, padx=20)

        def confirmar_data():
            entry_target.delete(0, 'end')
            entry_target.insert(0, cal.get_date().strftime('%d/%m/%Y'))
            top.destroy()

        btn_ok = ctk.CTkButton(top, text="Confirmar", command=confirmar_data)
        btn_ok.pack(pady=10)

    def adicionar_item(self):
        cod_raw = self.txt_p_cod.get().strip()
        qtde_raw = self.txt_p_qtde.get().strip().replace(',', '.')
        preco_raw = self.txt_p_preco.get().strip().replace(',', '.')

        if not cod_raw:
            messagebox.showwarning("Atenção", "Informe o Código do Produto.", parent=self)
            self.txt_p_cod.focus()
            return

        cod_formatted = self.formatar_codigo_5_digitos(cod_raw)

        try:
            qtde_val = float(qtde_raw) if qtde_raw else 1.0
            if qtde_val <= 0:
                qtde_val = 1.0
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.", parent=self)
            self.txt_p_qtde.focus()
            return

        # Validação de Duplicidade
        for item in self.itens:
            if item['codigo_prod'] == cod_formatted and item['qtde_oferta'] == qtde_val:
                messagebox.showwarning(
                    "Produto Duplicado",
                    f"O produto {cod_formatted} já está cadastrado com a quantidade {qtde_val:.2f}.\n\n"
                    "Para incluir o mesmo produto, as quantidades precisam ser diferentes.",
                    parent=self
                )
                self.txt_p_cod.focus()
                return

        if not preco_raw:
            preco_val = 0.0
        else:
            try:
                preco_val = float(preco_raw)
            except ValueError:
                messagebox.showerror("Erro", "Valor de preço inválido.", parent=self)
                self.txt_p_preco.focus()
                return

        self.itens.insert(0, {
            'codigo_prod': cod_formatted, 
            'qtde_oferta': qtde_val, 
            'preco_oferta': preco_val
        })
        self.atualizar_grid()

        self.txt_p_cod.delete(0, 'end')
        self.txt_p_qtde.delete(0, 'end')
        self.txt_p_qtde.insert(0, "1")
        self.txt_p_preco.delete(0, 'end')
        self.txt_p_cod.focus()

    def editar_item(self, index):
        item = self.itens.pop(index)
        self.txt_p_cod.delete(0, 'end')
        self.txt_p_cod.insert(0, item['codigo_prod'])
        
        self.txt_p_qtde.delete(0, 'end')
        self.txt_p_qtde.insert(0, f"{item['qtde_oferta']:.2f}".rstrip('0').rstrip('.'))

        self.txt_p_preco.delete(0, 'end')
        self.txt_p_preco.insert(0, f"{item['preco_oferta']:.2f}")
        
        self.atualizar_grid()

    def atualizar_grid(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        total_itens = len(self.itens)
        for idx, item in enumerate(self.itens):
            f_row = ctk.CTkFrame(self.frame_lista)
            f_row.pack(fill="x", pady=2, padx=5)

            num_exibicao = total_itens - idx
            ctk.CTkLabel(f_row, text=f"#{num_exibicao}", width=40).pack(side="left", padx=5)
            ctk.CTkLabel(f_row, text=f"Código: {item['codigo_prod']}", width=140, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            
            qtde_str = f"{item['qtde_oferta']:.2f}".rstrip('0').rstrip('.')
            ctk.CTkLabel(f_row, text=f"A partir de {qtde_str} un.", width=140, anchor="w", text_color="#81D4FA").pack(side="left", padx=5)

            lbl_preco = f"R$ {item['preco_oferta']:.2f}" if item['preco_oferta'] > 0 else "Preço Atual (R$ 0.00)"
            ctk.CTkLabel(f_row, text=lbl_preco, width=160, text_color="#A5D6A7" if item['preco_oferta'] > 0 else "#FFB74D", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

            btn_del = ctk.CTkButton(f_row, text="X", width=30, height=26, fg_color="#D32F2F", command=lambda i=idx: self.remover_item(i))
            btn_del.pack(side="right", padx=3)

            btn_edit = ctk.CTkButton(f_row, text="Editar", width=60, height=26, fg_color="#1976D2", command=lambda i=idx: self.editar_item(i))
            btn_edit.pack(side="right", padx=3)

    def remover_item(self, index):
        self.itens.pop(index)
        self.atualizar_grid()

    def converter_data_para_br(self, data_obj):
        if hasattr(data_obj, 'strftime'):
            return data_obj.strftime('%d/%m/%Y')
        return str(data_obj)

    def parse_data_para_iso(self, str_data):
        str_data = str_data.strip()
        if '/' in str_data:
            dt = datetime.strptime(str_data, '%d/%m/%Y')
            return dt.strftime('%Y-%m-%d')
        return str_data

    def carregar_dados(self):
        schema = get_schema()
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {schema}.encarte WHERE id = %s", (self.encarte_id,))
            enc = cur.fetchone()

            if enc:
                self.txt_titulo.insert(0, enc['titulo'])
                self.txt_dt_ini.insert(0, self.converter_data_para_br(enc['data_inicio']))
                self.txt_dt_fim.insert(0, self.converter_data_para_br(enc['data_fim']))

                cur.execute(f"SELECT codigo_prod, qtde_oferta, preco_oferta FROM {schema}.encarte_item WHERE encarte_id = %s ORDER BY ordem DESC, id DESC", (self.encarte_id,))
                itens_bd = cur.fetchall()
                self.itens = [{
                    'codigo_prod': self.formatar_codigo_5_digitos(str(i['codigo_prod'])), 
                    'qtde_oferta': float(i.get('qtde_oferta', 1.0)),
                    'preco_oferta': float(i['preco_oferta'])
                } for i in itens_bd]
                self.atualizar_grid()

            conn.close()
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", str(e), parent=self)

    def salvar_banco(self):
        schema = get_schema()
        titulo = self.txt_titulo.get().strip()
        dt_ini_raw = self.txt_dt_ini.get().strip()
        dt_fim_raw = self.txt_dt_fim.get().strip()

        if not titulo or not dt_ini_raw or not dt_fim_raw or not self.itens:
            messagebox.showwarning("Atenção", "Preencha o cabeçalho e insira ao menos 1 produto.", parent=self)
            return

        try:
            dt_ini_iso = self.parse_data_para_iso(dt_ini_raw)
            dt_fim_iso = self.parse_data_para_iso(dt_fim_raw)
        except Exception:
            messagebox.showerror("Data Inválida", "Informe a data no padrão brasileiro DD/MM/AAAA (ex: 29/08/2026).", parent=self)
            return

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.encarte_id:
                cur.execute(f"SELECT id FROM {schema}.encarte WHERE id = %s", (self.encarte_id,))
                existe = cur.fetchone()
                
                if not existe:
                    cur.execute(f"""
                        INSERT INTO {schema}.encarte (titulo, data_inicio, data_fim) 
                        VALUES (%s, %s, %s) RETURNING id
                    """, (titulo, dt_ini_iso, dt_fim_iso))
                    enc_id = cur.fetchone()['id']
                else:
                    cur.execute(f"""
                        UPDATE {schema}.encarte 
                        SET titulo=%s, data_inicio=%s, data_fim=%s 
                        WHERE id=%s
                    """, (titulo, dt_ini_iso, dt_fim_iso, self.encarte_id))
                    
                    cur.execute(f"DELETE FROM {schema}.encarte_item WHERE encarte_id=%s", (self.encarte_id,))
                    enc_id = self.encarte_id
            else:
                cur.execute(f"""
                    INSERT INTO {schema}.encarte (titulo, data_inicio, data_fim) 
                    VALUES (%s, %s, %s) RETURNING id
                """, (titulo, dt_ini_iso, dt_fim_iso))
                enc_id = cur.fetchone()['id']

            for idx, item in enumerate(reversed(self.itens)):
                cur.execute(f"""
                    INSERT INTO {schema}.encarte_item (encarte_id, codigo_prod, qtde_oferta, preco_oferta, ordem) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (enc_id, item['codigo_prod'], item['qtde_oferta'], item['preco_oferta'], idx))

            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Encarte gravado com sucesso!", parent=self)
            if self.callback_refresh:
                self.callback_refresh()
            self.destroy()

        except Exception as e:
            if conn:
                conn.rollback()
                conn.close()
            messagebox.showerror("Erro ao Salvar", f"Falha na transação:\n{e}", parent=self)

# ==============================================================================
# TELA PRINCIPAL DO APLICATIVO
# ==============================================================================
class AppPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestão de Encartes - v2.0")
        
        largura, altura = 800, 500
        pos_x = (self.winfo_screenwidth() // 2) - (largura // 2)
        pos_y = max(10, (self.winfo_screenheight() // 2) - (altura // 2) - 40)
        self.geometry(f"{largura}x{altura}+{pos_x}+{pos_y}")

        frame_topo = ctk.CTkFrame(self)
        frame_topo.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(frame_topo, text="Encartes Cadastrados", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        btn_sair = ctk.CTkButton(frame_topo, text="Sair", fg_color="#C62828", width=70, command=self.destroy)
        btn_sair.pack(side="right", padx=5, pady=5)

        btn_params = ctk.CTkButton(frame_topo, text="Parâmetros", fg_color="#455A64", width=100, command=self.abrir_parametros)
        btn_params.pack(side="right", padx=5, pady=5)

        btn_novo = ctk.CTkButton(frame_topo, text="Novo Encarte", fg_color="#2E7D32", width=110, command=self.novo_encarte)
        btn_novo.pack(side="right", padx=5, pady=5)

        frame_pesquisa = ctk.CTkFrame(self)
        frame_pesquisa.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_pesquisa, text="Buscar Encarte:").pack(side="left", padx=10)
        self.txt_filtro_titulo = ctk.CTkEntry(frame_pesquisa, placeholder_text="Digite o título para filtrar...")
        self.txt_filtro_titulo.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.txt_filtro_titulo.bind("<KeyRelease>", lambda e: self.carregar_encartes())

        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

        self.carregar_encartes()

    def abrir_parametros(self):
        ParametrosWindow(self)

    def carregar_encartes(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        schema = get_schema()
        filtro = self.txt_filtro_titulo.get().strip() if hasattr(self, 'txt_filtro_titulo') else ""

        try:
            conn = get_connection()
            cur = conn.cursor()

            if filtro:
                query = f"SELECT id, titulo, data_inicio, data_fim FROM {schema}.encarte WHERE titulo ILIKE %s ORDER BY id DESC"
                cur.execute(query, (f"%{filtro}%",))
            else:
                query = f"SELECT id, titulo, data_inicio, data_fim FROM {schema}.encarte ORDER BY id DESC"
                cur.execute(query)

            encartes = cur.fetchall()
            conn.close()

            if not encartes:
                ctk.CTkLabel(self.frame_lista, text="Nenhum encarte encontrado.", text_color="gray").pack(pady=20)
                return

            hoje = date.today()

            for enc in encartes:
                row = ctk.CTkFrame(self.frame_lista)
                row.pack(fill="x", pady=4, padx=5)

                dt_ini_obj = enc['data_inicio']
                dt_fim_obj = enc['data_fim']

                dt_ini_str = dt_ini_obj.strftime('%d/%m/%Y') if hasattr(dt_ini_obj, 'strftime') else str(dt_ini_obj)
                dt_fim_str = dt_fim_obj.strftime('%d/%m/%Y') if hasattr(dt_fim_obj, 'strftime') else str(dt_fim_obj)

                if hasattr(dt_fim_obj, 'year'):
                    data_vencimento = dt_fim_obj
                else:
                    try:
                        data_vencimento = datetime.strptime(str(dt_fim_obj), '%Y-%m-%d').date()
                    except Exception:
                        data_vencimento = hoje

                cor_status = "#EF5350" if data_vencimento < hoje else "#66BB6A"

                lbl_info = f"#{enc['id']} - {enc['titulo']} ({dt_ini_str} a {dt_fim_str})"
                ctk.CTkLabel(row, text=lbl_info, anchor="w", font=ctk.CTkFont(weight="bold"), text_color=cor_status).pack(side="left", padx=10, fill="x", expand=True)

                btn_excluir = ctk.CTkButton(
                    row, text="Excluir", width=65, fg_color="#C62828", hover_color="#B71C1C",
                    command=lambda e_id=enc['id'], e_tit=enc['titulo']: self.excluir_encarte(e_id, e_tit)
                )
                btn_excluir.pack(side="right", padx=(2, 5), pady=5)

                btn_editar = ctk.CTkButton(
                    row, text="Editar", width=65, 
                    command=lambda e_id=enc['id']: self.editar_encarte(e_id)
                )
                btn_editar.pack(side="right", padx=2, pady=5)

                btn_gerar_cat = ctk.CTkButton(
                    row, text="🚀 Gerar Catálogo", width=115, fg_color="#E65100", hover_color="#EF6C00",
                    command=lambda e_id=enc['id']: self.processar_geracao_catalogo(e_id)
                )
                btn_gerar_cat.pack(side="right", padx=2, pady=5)

        except Exception as e:
            ctk.CTkLabel(self.frame_lista, text=f"Erro ao consultar o banco de dados:\n{e}", text_color="#EF5350").pack(pady=20)

    def processar_geracao_catalogo(self, encarte_id):
        cfg = carregar_config()

        dir_csv = cfg.get("dir_csv", "").strip()
        dir_encarte = cfg.get("dir_encarte", "").strip()
        query_template = cfg.get("query_csv", "").strip()

        if not dir_csv or not dir_encarte:
            messagebox.showwarning("Parâmetros Incompletos", "Verifique se as pastas de 'Diretório CSV' e 'Diretório Encarte' estão preenchidas nos Parâmetros.", parent=self)
            return

        exe_gerar = os.path.join(dir_encarte, "GERAR_CATALOGO.EXE")
        exe_visualizar = os.path.join(dir_encarte, "VISUALIZAR_CATALOGO.EXE")

        if not os.path.exists(exe_gerar):
            messagebox.showerror("Executável não Encontrado", f"O utilitário GERAR_CATALOGO.EXE não foi localizado na pasta:\n{dir_encarte}", parent=self)
            return

        nome_csv = f"{encarte_id}_ENCARTE.csv"
        caminho_csv = os.path.join(dir_csv, nome_csv)
        caminho_jpg = os.path.join(cfg.get("dir_jpg", dir_csv), f"{encarte_id}_ENCARTE.jpg")

        # 1. GERAR CSV VIA QUERY SQL
        try:
            conn = get_connection()
            cur = conn.cursor()

            query_sql = query_template.replace("{ID_ENCARTE}", str(encarte_id))
            cur.execute(query_sql)
            linhas = cur.fetchall()
            conn.close()

            if not linhas:
                messagebox.showwarning("Sem Dados", f"Nenhum produto retornado na consulta do encarte #{encarte_id}.", parent=self)
                return

            with open(caminho_csv, "w", encoding="utf-8-sig") as f:
                f.write("CODIGO;DESCRICAO;LINHA_PRECO\n")
                for row in linhas:
                    cod = str(row.get('codigo', '')).strip()
                    desc = str(row.get('descricao', '')).strip().replace(';', ' ')
                    preco = str(row.get('linha_preco', '')).strip().replace(';', ' ')
                    f.write(f"{cod};{desc};{preco}\n")

        except Exception as e:
            messagebox.showerror("Erro ao Gerar CSV", f"Falha na execução da query SQL:\n{e}", parent=self)
            return

        # 2. EXECUTAR O GERAR_CATALOGO.EXE PASSANDO O ARQUIVO CSV
        try:
            res = subprocess.run([exe_gerar, nome_csv], cwd=dir_encarte, capture_output=True, text=True)
            if res.returncode != 0 and res.stderr:
                messagebox.showerror("Erro no GERAR_CATALOGO", f"Ocorreu um erro ao gerar a imagem:\n{res.stderr}", parent=self)
                return
        except Exception as e:
            messagebox.showerror("Erro ao Executar GERAR_CATALOGO", str(e), parent=self)
            return

        # 3. EXECUTAR O VISUALIZAR_CATALOGO.EXE
        if os.path.exists(exe_visualizar):
            try:
                subprocess.Popen([exe_visualizar, f"{encarte_id}_ENCARTE.jpg"], cwd=dir_encarte)
            except Exception as e:
                messagebox.showerror("Erro ao Executar VISUALIZAR_CATALOGO", str(e), parent=self)
        else:
            messagebox.showinfo("Sucesso", f"Catálogo #{encarte_id} gerado com sucesso em:\n{caminho_jpg}", parent=self)

    def excluir_encarte(self, encarte_id, titulo):
        schema = get_schema()
        resposta = messagebox.askyesno(
            "Confirmar Exclusão", 
            f"Tem certeza que deseja excluir o encarte #{encarte_id} - '{titulo}'?\n\nEsta ação não poderá ser desfeita!",
            parent=self
        )
        if resposta:
            try:
                conn = get_connection()
                cur = conn.cursor()
                
                cur.execute(f"DELETE FROM {schema}.encarte_item WHERE encarte_id = %s", (encarte_id,))
                cur.execute(f"DELETE FROM {schema}.encarte WHERE id = %s", (encarte_id,))
                
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Sucesso", "Encarte excluído com sucesso!", parent=self)
                self.carregar_encartes()
            except Exception as e:
                messagebox.showerror("Erro ao Excluir", f"Ocorreu um erro ao excluir o encarte:\n{e}", parent=self)

    def novo_encarte(self):
        FormEncarteWindow(self, callback_refresh=self.carregar_encartes)

    def editar_encarte(self, encarte_id):
        FormEncarteWindow(self, encarte_id=encarte_id, callback_refresh=self.carregar_encartes)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = AppPrincipal()
    app.mainloop()
