# -*- coding: utf-8 -*-
import os
import sys
import json
import psycopg2
from psycopg2.extras import RealDictCursor
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Configuração de Aparência e Tema do CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# ----------------------------------------------------------------------
# CONEXÃO E CONFIGURAÇÕES DO BANCO DE DADOS
# ----------------------------------------------------------------------
def carregar_config_db():
    json_path = os.path.join(os.path.dirname(__file__), "bd_config.json")
    if not os.path.exists(json_path):
        return {
            "host": "localhost",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": "",
            "schema": "public"
        }
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "host": "localhost",
            "port": 5432,
            "database": "postgres",
            "user": "postgres",
            "password": "",
            "schema": "public"
        }


def get_connection():
    cfg = carregar_config_db()
    return psycopg2.connect(
        host=cfg.get("host", "localhost"),
        port=cfg.get("port", 5432),
        database=cfg.get("database", "postgres"),
        user=cfg.get("user", "postgres"),
        password=cfg.get("password", ""),
        cursor_factory=RealDictCursor
    )


def get_schema():
    cfg = carregar_config_db()
    return cfg.get("schema", "public")


def carregar_parametros_banco():
    schema = get_schema()
    params_padrao = {
        "dir_encarte": "",
        "dir_csv": "",
        "dir_jpg": "",
        "cor_tit_rodape": "",
        "cor_grid_tarja": "",
        "cor_grid_preco": "",
        "cabecalho_logo": "",
        "cabecalho_site": "",
        "rodape_logo_fone": "",
        "cor_fundo_destaque": "",
        "cor_fundo_demais": "",
        "cor_fundo_rodape": "",
        "cabecalho_tema": ""
    }
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {schema}.encarte_parametros LIMIT 1;")
        res = cur.fetchone()
        conn.close()
        if res:
            for k in params_padrao.keys():
                params_padrao[k] = res.get(k, "") or ""
    except Exception:
        pass
    return params_padrao


def salvar_parametros_banco(p):
    schema = get_schema()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM {schema}.encarte_parametros LIMIT 1;")
    res = cur.fetchone()
    
    if res:
        query = f"""
            UPDATE {schema}.encarte_parametros SET
                dir_encarte = %s,
                dir_csv = %s,
                dir_jpg = %s,
                cor_tit_rodape = %s,
                cor_grid_tarja = %s,
                cor_grid_preco = %s,
                cabecalho_logo = %s,
                cabecalho_site = %s,
                rodape_logo_fone = %s,
                cor_fundo_destaque = %s,
                cor_fundo_demais = %s,
                cor_fundo_rodape = %s,
                cabecalho_tema = %s
            WHERE id = %s
        """
        cur.execute(query, (
            p.get("dir_encarte", ""), p.get("dir_csv", ""), p.get("dir_jpg", ""),
            p.get("cor_tit_rodape", ""), p.get("cor_grid_tarja", ""), p.get("cor_grid_preco", ""),
            p.get("cabecalho_logo", ""), p.get("cabecalho_site", ""), p.get("rodape_logo_fone", ""),
            p.get("cor_fundo_destaque", ""), p.get("cor_fundo_demais", ""), p.get("cor_fundo_rodape", ""),
            p.get("cabecalho_tema", ""), res["id"]
        ))
    else:
        query = f"""
            INSERT INTO {schema}.encarte_parametros (
                dir_encarte, dir_csv, dir_jpg, cor_tit_rodape, cor_grid_tarja,
                cor_grid_preco, cabecalho_logo, cabecalho_site, rodape_logo_fone,
                cor_fundo_destaque, cor_fundo_demais, cor_fundo_rodape, cabecalho_tema
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            p.get("dir_encarte", ""), p.get("dir_csv", ""), p.get("dir_jpg", ""),
            p.get("cor_tit_rodape", ""), p.get("cor_grid_tarja", ""), p.get("cor_grid_preco", ""),
            p.get("cabecalho_logo", ""), p.get("cabecalho_site", ""), p.get("rodape_logo_fone", ""),
            p.get("cor_fundo_destaque", ""), p.get("cor_fundo_demais", ""), p.get("cor_fundo_rodape", ""),
            p.get("cabecalho_tema", "")
        ))
    conn.commit()
    conn.close()


# ----------------------------------------------------------------------
# JANELA DE PARÂMETROS E CONFIGURAÇÕES
# ----------------------------------------------------------------------
class ParametrosWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Parâmetros do Sistema e Banco de Dados")
        self.geometry("750x600")
        self.grab_set()

        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        tab_db = self.tabview.add("Conexão Banco")
        tab_dirs = self.tabview.add("Diretórios e Design")

        self.setup_tab_db(tab_db)
        self.setup_tab_dirs(tab_dirs)

    def setup_tab_db(self, tab):
        cfg = carregar_config_db()
        fields = [
            ("Host:", "host"), ("Porta:", "port"),
            ("Banco de Dados:", "database"), ("Usuário:", "user"),
            ("Senha:", "password"), ("Schema:", "schema")
        ]
        self.entries_db = {}
        for idx, (label_text, key) in enumerate(fields):
            ctk.CTkLabel(tab, text=label_text).grid(row=idx, column=0, padx=10, pady=8, sticky="w")
            ent = ctk.CTkEntry(tab, width=300, show="*" if key == "password" else "")
            ent.insert(0, str(cfg.get(key, "")))
            ent.grid(row=idx, column=1, padx=10, pady=8)
            self.entries_db[key] = ent

        btn_frame = ctk.CTkFrame(tab)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)

        ctk.CTkButton(btn_frame, text="Testar Conexão", command=self.testar_conexao).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Criar / Atualizar Tabelas", command=self.criar_tabelas_banco).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Salvar Conexão BD", command=self.salvar_db_config).pack(side="left", padx=5)

    def setup_tab_dirs(self, tab):
        params_db = carregar_parametros_banco()

        self.txt_dir_encarte = self._criar_campo_caminho(tab, "Pasta dos Encartes:", 0, params_db.get("dir_encarte", ""))
        self.txt_dir_csv = self._criar_campo_caminho(tab, "Pasta Exportação CSV:", 1, params_db.get("dir_csv", ""))
        self.txt_dir_jpg = self._criar_campo_caminho(tab, "Pasta Encartes JPG:", 2, params_db.get("dir_jpg", ""))
        
        self.txt_cabecalho_logo = self._criar_campo_caminho(tab, "Logo do Cabeçalho:", 3, params_db.get("cabecalho_logo", ""), pasta=False)
        self.txt_rodape_logo_fone = self._criar_campo_caminho(tab, "Logo / Telefone Rodapé:", 4, params_db.get("rodape_logo_fone", ""), pasta=False)

        ctk.CTkLabel(tab, text="Texto do Site (Cabeçalho):").grid(row=5, column=0, padx=10, pady=6, sticky="w")
        self.txt_cabecalho_site = ctk.CTkEntry(tab, width=280)
        self.txt_cabecalho_site.insert(0, params_db.get("cabecalho_site", ""))
        self.txt_cabecalho_site.grid(row=5, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab, text="Cor Título Rodapé:").grid(row=6, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_tit_rodape = ctk.CTkEntry(tab, width=280)
        self.txt_cor_tit_rodape.insert(0, params_db.get("cor_tit_rodape", ""))
        self.txt_cor_tit_rodape.grid(row=6, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab, text="Cor Tarja Grid:").grid(row=7, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_grid_tarja = ctk.CTkEntry(tab, width=280)
        self.txt_cor_grid_tarja.insert(0, params_db.get("cor_grid_tarja", ""))
        self.txt_cor_grid_tarja.grid(row=7, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab, text="Cor Preço Grid:").grid(row=8, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_grid_preco = ctk.CTkEntry(tab, width=280)
        self.txt_cor_grid_preco.insert(0, params_db.get("cor_grid_preco", ""))
        self.txt_cor_grid_preco.grid(row=8, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab, text="Cor Fundo Destaque:").grid(row=9, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_fundo_destaque = ctk.CTkEntry(tab, width=280)
        self.txt_cor_fundo_destaque.insert(0, params_db.get("cor_fundo_destaque", ""))
        self.txt_cor_fundo_destaque.grid(row=9, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab, text="Cor Fundo Demais:").grid(row=10, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_fundo_demais = ctk.CTkEntry(tab, width=280)
        self.txt_cor_fundo_demais.insert(0, params_db.get("cor_fundo_demais", ""))
        self.txt_cor_fundo_demais.grid(row=10, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab, text="Cor Fundo Rodapé:").grid(row=11, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_fundo_rodape = ctk.CTkEntry(tab, width=280)
        self.txt_cor_fundo_rodape.insert(0, params_db.get("cor_fundo_rodape", ""))
        self.txt_cor_fundo_rodape.grid(row=11, column=1, padx=5, pady=6)

        self.txt_cabecalho_tema = self._criar_campo_caminho(tab, "Tema do Cabeçalho:", 12, params_db.get("cabecalho_tema", ""), pasta=False)

        btn_salvar = ctk.CTkButton(tab, text="Salvar Parâmetros no BD", command=self.salvar_parametros)
        btn_salvar.grid(row=13, column=0, columnspan=3, pady=15)

    def _criar_campo_caminho(self, tab, label, row, valor_inicial="", pasta=True):
        ctk.CTkLabel(tab, text=label).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        entry = ctk.CTkEntry(tab, width=280)
        entry.insert(0, valor_inicial)
        entry.grid(row=row, column=1, padx=5, pady=6)

        def selecionar():
            path = filedialog.askdirectory() if pasta else filedialog.askopenfilename()
            if path:
                entry.delete(0, "end")
                entry.insert(0, path)

        ctk.CTkButton(tab, text="...", width=40, command=selecionar).grid(row=row, column=2, padx=5, pady=6)
        return entry

    def testar_conexao(self):
        try:
            conn = psycopg2.connect(
                host=self.entries_db["host"].get().strip(),
                port=int(self.entries_db["port"].get().strip()),
                database=self.entries_db["database"].get().strip(),
                user=self.entries_db["user"].get().strip(),
                password=self.entries_db["password"].get().strip()
            )
            conn.close()
            messagebox.showinfo("Sucesso", "Conexão estabelecida com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Falha ao conectar:\n{str(e)}")

    def salvar_db_config(self):
        config = {k: ent.get().strip() for k, ent in self.entries_db.items()}
        try:
            config["port"] = int(config["port"])
        except ValueError:
            config["port"] = 5432

        json_path = os.path.join(os.path.dirname(__file__), "bd_config.json")
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            messagebox.showinfo("Sucesso", "Configurações de BD salvas em bd_config.json!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar arquivo JSON:\n{str(e)}")

    def criar_tabelas_banco(self):
        try:
            schema = self.entries_db["schema"].get().strip() or "public"
            conn = psycopg2.connect(
                host=self.entries_db["host"].get().strip(),
                port=int(self.entries_db["port"].get().strip()),
                database=self.entries_db["database"].get().strip(),
                user=self.entries_db["user"].get().strip(),
                password=self.entries_db["password"].get().strip()
            )
            cur = conn.cursor()
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema};")

            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.encarte_parametros (
                    id SERIAL PRIMARY KEY,
                    dir_encarte VARCHAR(255),
                    dir_csv VARCHAR(255),
                    dir_jpg VARCHAR(255),
                    cor_tit_rodape VARCHAR(50),
                    cor_grid_tarja VARCHAR(50),
                    cor_grid_preco VARCHAR(50),
                    cabecalho_logo VARCHAR(255),
                    cabecalho_site VARCHAR(255),
                    rodape_logo_fone VARCHAR(255),
                    cor_fundo_destaque VARCHAR(50),
                    cor_fundo_demais VARCHAR(50),
                    cor_fundo_rodape VARCHAR(50),
                    cabecalho_tema VARCHAR(255)
                );
            """)

            # Atualização de Schema se a coluna `cor_fundo_rodape` ainda não existir
            cur.execute(f"ALTER TABLE {schema}.encarte_parametros ADD COLUMN IF NOT EXISTS cor_fundo_rodape character varying(50);")

            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.encarte_cabecalho (
                    id SERIAL PRIMARY KEY,
                    num_encarte INTEGER NOT NULL,
                    dt_inicio DATE NOT NULL,
                    dt_fim DATE NOT NULL,
                    cabecalho_tema VARCHAR(255),
                    titulo_rodape VARCHAR(255),
                    comentarios TEXT,
                    dt_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {schema}.encarte_itens (
                    id SERIAL PRIMARY KEY,
                    encarte_id INTEGER REFERENCES {schema}.encarte_cabecalho(id) ON DELETE CASCADE,
                    codigo_prod INTEGER NOT NULL,
                    destaque CHAR(1) DEFAULT 'N',
                    qtde_oferta NUMERIC(10,2) DEFAULT 1.00,
                    preco_oferta NUMERIC(10,2) DEFAULT 0.00,
                    item_foto VARCHAR(255),
                    ordem INTEGER DEFAULT 0
                );
            """)

            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", f"Estruturas e tabelas criadas no schema '{schema}'!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar tabelas no banco:\n{str(e)}")

    def salvar_parametros(self):
        params_db = {
            "dir_encarte": self.txt_dir_encarte.get().strip(),
            "dir_csv": self.txt_dir_csv.get().strip(),
            "dir_jpg": self.txt_dir_jpg.get().strip(),
            "cabecalho_logo": self.txt_cabecalho_logo.get().strip(),
            "rodape_logo_fone": self.txt_rodape_logo_fone.get().strip(),
            "cabecalho_site": self.txt_cabecalho_site.get().strip(),
            "cor_tit_rodape": self.txt_cor_tit_rodape.get().strip(),
            "cor_grid_tarja": self.txt_cor_grid_tarja.get().strip(),
            "cor_grid_preco": self.txt_cor_grid_preco.get().strip(),
            "cor_fundo_destaque": self.txt_cor_fundo_destaque.get().strip(),
            "cor_fundo_demais": self.txt_cor_fundo_demais.get().strip(),
            "cor_fundo_rodape": self.txt_cor_fundo_rodape.get().strip(),
            "cabecalho_tema": self.txt_cabecalho_tema.get().strip()
        }
        try:
            salvar_parametros_banco(params_db)
            messagebox.showinfo("Sucesso", "Parâmetros salvos com sucesso no Banco de Dados!")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar parâmetros:\n{str(e)}")


# ----------------------------------------------------------------------
# FORMULÁRIO DE CRIAÇÃO E EDIÇÃO DE ENCARTE
# ----------------------------------------------------------------------
class FormEncarteWindow(ctk.CTkToplevel):
    def __init__(self, parent, encarte_id=None):
        super().__init__(parent)
        self.encarte_id = encarte_id
        self.parent = parent
        self.title("Novo Encarte" if not encarte_id else f"Editar Encarte #{encarte_id}")
        self.geometry("850x700")
        self.grab_set()

        self.itens = []
        self.item_edit_index = None

        self.setup_ui()
        if self.encarte_id:
            self.carregar_dados_encarte()

    def setup_ui(self):
        # Frame do Cabeçalho do Encarte
        f_cab = ctk.CTkFrame(self)
        f_cab.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_cab, text="Nº Encarte:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ent_num = ctk.CTkEntry(f_cab, width=100)
        self.ent_num.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_cab, text="Data Início (AAAA-MM-DD):").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.ent_dt_inicio = ctk.CTkEntry(f_cab, width=120)
        self.ent_dt_inicio.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_cab, text="Data Fim:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ent_dt_fim = ctk.CTkEntry(f_cab, width=120)
        self.ent_dt_fim.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_cab, text="Título Rodapé:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ent_tit_rodape = ctk.CTkEntry(f_cab, width=300)
        self.ent_tit_rodape.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_cab, text="Tema Cabeçalho:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.ent_tema = ctk.CTkEntry(f_cab, width=300)
        self.ent_tema.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="w")
        btn_busca_tema = ctk.CTkButton(f_cab, text="...", width=30, command=self.selecionar_tema)
        btn_busca_tema.grid(row=2, column=4, padx=5, pady=5, sticky="w")

        ctk.CTkLabel(f_cab, text="Comentários:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.ent_coment = ctk.CTkEntry(f_cab, width=500)
        self.ent_coment.grid(row=3, column=1, columnspan=5, padx=5, pady=5, sticky="w")

        # Frame de Adição de Itens
        f_item = ctk.CTkFrame(self)
        f_item.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(f_item, text="Cód. Prod:").grid(row=0, column=0, padx=4, pady=5)
        self.ent_item_cod = ctk.CTkEntry(f_item, width=90)
        self.ent_item_cod.grid(row=0, column=1, padx=4, pady=5)

        self.chk_destaque = ctk.CTkCheckBox(f_item, text="Destaque")
        self.chk_destaque.grid(row=0, column=2, padx=4, pady=5)

        ctk.CTkLabel(f_item, text="Qtde Oferta:").grid(row=0, column=3, padx=4, pady=5)
        self.ent_item_qtde = ctk.CTkEntry(f_item, width=80)
        self.ent_item_qtde.insert(0, "1.00")
        self.ent_item_qtde.grid(row=0, column=4, padx=4, pady=5)

        ctk.CTkLabel(f_item, text="Preço Oferta:").grid(row=0, column=5, padx=4, pady=5)
        self.ent_item_preco = ctk.CTkEntry(f_item, width=90)
        self.ent_item_preco.insert(0, "0.00")
        self.ent_item_preco.grid(row=0, column=6, padx=4, pady=5)

        self.ent_item_foto = ctk.CTkEntry(f_item, width=120, placeholder_text="Foto Indiv.")
        self.ent_item_foto.grid(row=0, column=7, padx=4, pady=5)
        ctk.CTkButton(f_item, text="...", width=30, command=self.selecionar_foto_item).grid(row=0, column=8, padx=2, pady=5)

        self.btn_add_item = ctk.CTkButton(f_item, text="Adicionar Item", fg_color="#2E7D32", hover_color="#1B5E20", command=self.adicionar_ou_atualizar_item)
        self.btn_add_item.grid(row=0, column=9, padx=8, pady=5)

        # Frame da Lista Scrollável de Itens
        self.frame_lista = ctk.CTkScrollableFrame(self, height=280)
        self.frame_lista.pack(fill="both", expand=True, padx=10, pady=5)

        # Botão Salvar
        btn_salvar_encarte = ctk.CTkButton(self, text="Salvar Encarte Completo", height=40, font=ctk.CTkFont(size=14, weight="bold"), command=self.salvar_encarte)
        btn_salvar_encarte.pack(fill="x", padx=10, pady=10)

    def selecionar_tema(self):
        path = filedialog.askopenfilename()
        if path:
            self.ent_tema.delete(0, "end")
            self.ent_tema.insert(0, path)

    def selecionar_foto_item(self):
        path = filedialog.askopenfilename()
        if path:
            self.ent_item_foto.delete(0, "end")
            self.ent_item_foto.insert(0, path)

    def adicionar_ou_atualizar_item(self):
        cod = self.ent_item_cod.get().strip()
        if not cod:
            messagebox.showwarning("Aviso", "Informe o Código do Produto!")
            return

        try:
            codigo_prod = int(cod)
            qtde = float(self.ent_item_qtde.get().strip().replace(",", "."))
            preco = float(self.ent_item_preco.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Código, Quantidade e Preço devem ser numéricos!")
            return

        item_data = {
            "codigo_prod": codigo_prod,
            "destaque": "S" if self.chk_destaque.get() else "N",
            "qtde_oferta": qtde,
            "preco_oferta": preco,
            "item_foto": self.ent_item_foto.get().strip()
        }

        if self.item_edit_index is not None:
            self.itens[self.item_edit_index] = item_data
            self.item_edit_index = None
            self.btn_add_item.configure(text="Adicionar Item", fg_color="#2E7D32")
        else:
            self.itens.insert(0, item_data)

        self.limpar_campos_item()
        self.atualizar_grid()

    def limpar_campos_item(self):
        self.ent_item_cod.delete(0, "end")
        self.chk_destaque.deselect()
        self.ent_item_qtde.delete(0, "end")
        self.ent_item_qtde.insert(0, "1.00")
        self.ent_item_preco.delete(0, "end")
        self.ent_item_preco.insert(0, "0.00")
        self.ent_item_foto.delete(0, "end")

    def editar_item(self, idx):
        item = self.itens[idx]
        self.item_edit_index = idx

        self.ent_item_cod.delete(0, "end")
        self.ent_item_cod.insert(0, str(item["codigo_prod"]))

        if item.get("destaque") == "S":
            self.chk_destaque.select()
        else:
            self.chk_destaque.deselect()

        self.ent_item_qtde.delete(0, "end")
        self.ent_item_qtde.insert(0, str(item["qtde_oferta"]))

        self.ent_item_preco.delete(0, "end")
        self.ent_item_preco.insert(0, str(item["preco_oferta"]))

        self.ent_item_foto.delete(0, "end")
        self.ent_item_foto.insert(0, item.get("item_foto", ""))

        self.btn_add_item.configure(text="Atualizar Item", fg_color="#1565C0")

    def remover_item(self, idx):
        del self.itens[idx]
        self.atualizar_grid()

    def atualizar_grid(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        total_itens = len(self.itens)
        for idx, item in enumerate(self.itens):
            f_row = ctk.CTkFrame(self.frame_lista)
            f_row.pack(fill="x", pady=2, padx=5)

            # Posição
            num_exibicao = total_itens - idx
            ctk.CTkLabel(f_row, text=f"#{num_exibicao}", width=35).pack(side="left", padx=5)
            
            # Código do Produto (largura fixa)
            ctk.CTkLabel(
                f_row, 
                text=f"Código: {item['codigo_prod']}", 
                width=110, 
                anchor="w", 
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=5)

            # Marcador de Destaque (largura fixa para manter o alinhamento das colunas seguintes)
            lbl_destaque = "⭐ [DESTAQUE]" if item.get('destaque') == 'S' else ""
            ctk.CTkLabel(
                f_row, 
                text=lbl_destaque, 
                width=110, 
                anchor="w", 
                font=ctk.CTkFont(weight="bold"), 
                text_color=("#FF8F00", "#FFD54F")
            ).pack(side="left", padx=5)
            
            # Quantidade
            qtde_str = f"{item['qtde_oferta']:.2f}".rstrip('0').rstrip('.')
            ctk.CTkLabel(
                f_row, 
                text=f"A partir de {qtde_str} un.", 
                width=120, 
                anchor="w", 
                text_color=("#000000", "#81D4FA")
            ).pack(side="left", padx=5)

            # Preço
            cor_preco = ("#2E7D32", "#A5D6A7") if item['preco_oferta'] > 0 else ("#E65100", "#FFB74D")
            lbl_preco = f"R$ {item['preco_oferta']:.2f}" if item['preco_oferta'] > 0 else "Preço Atual"
            ctk.CTkLabel(
                f_row, 
                text=lbl_preco, 
                width=100, 
                anchor="w",
                text_color=cor_preco, 
                font=ctk.CTkFont(weight="bold")
            ).pack(side="left", padx=5)

            # Foto
            foto_text = f"📷 {os.path.basename(item['item_foto'])}" if item.get('item_foto') else "Sem foto ind."
            ctk.CTkLabel(
                f_row, 
                text=foto_text, 
                width=130, 
                text_color="gray", 
                anchor="w"
            ).pack(side="left", padx=5)

            # Botões de Ação
            btn_del = ctk.CTkButton(f_row, text="❌", width=36, height=28, fg_color="#C62828", hover_color="#B71C1C", command=lambda i=idx: self.remover_item(i))
            btn_del.pack(side="right", padx=3)

            btn_edit = ctk.CTkButton(f_row, text="✏️", width=36, height=28, fg_color="#1976D2", hover_color="#0D47A1", command=lambda i=idx: self.editar_item(i))
            btn_edit.pack(side="right", padx=3)

    def carregar_dados_encarte(self):
        schema = get_schema()
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT * FROM {schema}.encarte_cabecalho WHERE id = %s;", (self.encarte_id,))
            cab = cur.fetchone()
            if cab:
                self.ent_num.insert(0, str(cab["num_encarte"]))
                self.ent_dt_inicio.insert(0, str(cab["dt_inicio"]))
                self.ent_dt_fim.insert(0, str(cab["dt_fim"]))
                self.ent_tit_rodape.insert(0, cab.get("titulo_rodape", "") or "")
                self.ent_tema.insert(0, cab.get("cabecalho_tema", "") or "")
                self.ent_coment.insert(0, cab.get("comentarios", "") or "")

            cur.execute(f"SELECT * FROM {schema}.encarte_itens WHERE encarte_id = %s ORDER BY ordem DESC, id DESC;", (self.encarte_id,))
            itens_db = cur.fetchall()
            for it in itens_db:
                self.itens.append({
                    "codigo_prod": it["codigo_prod"],
                    "destaque": it["destaque"],
                    "qtde_oferta": float(it["qtde_oferta"]),
                    "preco_oferta": float(it["preco_oferta"]),
                    "item_foto": it.get("item_foto", "") or ""
                })
            conn.close()
            self.atualizar_grid()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar encarte:\n{str(e)}")

    def salvar_encarte(self):
        num = self.ent_num.get().strip()
        dt_in = self.ent_dt_inicio.get().strip()
        dt_fi = self.ent_dt_fim.get().strip()

        if not num or not dt_in or not dt_fi:
            messagebox.showwarning("Aviso", "Número e Datas do Encarte são obrigatórios!")
            return

        schema = get_schema()
        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.encarte_id:
                cur.execute(f"""
                    UPDATE {schema}.encarte_cabecalho SET
                        num_encarte = %s, dt_inicio = %s, dt_fim = %s,
                        titulo_rodape = %s, cabecalho_tema = %s, comentarios = %s
                    WHERE id = %s;
                """, (int(num), dt_in, dt_fi, self.ent_tit_rodape.get().strip(),
                      self.ent_tema.get().strip(), self.ent_coment.get().strip(), self.encarte_id))
                
                cur.execute(f"DELETE FROM {schema}.encarte_itens WHERE encarte_id = %s;", (self.encarte_id,))
                enc_id = self.encarte_id
            else:
                cur.execute(f"""
                    INSERT INTO {schema}.encarte_cabecalho (
                        num_encarte, dt_inicio, dt_fim, titulo_rodape, cabecalho_tema, comentarios
                    ) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                """, (int(num), dt_in, dt_fi, self.ent_tit_rodape.get().strip(),
                      self.ent_tema.get().strip(), self.ent_coment.get().strip()))
                enc_id = cur.fetchone()["id"]

            total_itens = len(self.itens)
            for idx, item in enumerate(self.itens):
                ordem = total_itens - idx
                cur.execute(f"""
                    INSERT INTO {schema}.encarte_itens (
                        encarte_id, codigo_prod, destaque, qtde_oferta, preco_oferta, item_foto, ordem
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                """, (enc_id, item["codigo_prod"], item["destaque"], item["qtde_oferta"],
                      item["preco_oferta"], item["item_foto"], ordem))

            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Encarte gravado com sucesso!")
            if hasattr(self.parent, "carregar_lista_encartes"):
                self.parent.carregar_lista_encartes()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar encarte no banco:\n{str(e)}")


# ----------------------------------------------------------------------
# TELA PRINCIPAL DO SISTEMA DE GESTÃO DE ENCARTES
# ----------------------------------------------------------------------
class AppGestaoEncarte(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Gestão de Encartes")
        self.geometry("950x600")

        self.setup_ui()
        self.carregar_lista_encartes()

    def setup_ui(self):
        # Barra Superior
        f_top = ctk.CTkFrame(self)
        f_top.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(f_top, text="Gestão de Encartes Promo", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left", padx=10)
        
        btn_param = ctk.CTkButton(f_top, text="⚙️ Parâmetros", command=self.abrir_parametros)
        btn_param.pack(side="right", padx=5)

        btn_novo = ctk.CTkButton(f_top, text="➕ Novo Encarte", fg_color="#2E7D32", hover_color="#1B5E20", command=self.novo_encarte)
        btn_novo.pack(side="right", padx=5)

        # Filtros de Pesquisa
        f_filtro = ctk.CTkFrame(self)
        f_filtro.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(f_filtro, text="Filtrar por Nº Encarte:").pack(side="left", padx=5)
        self.ent_busca_num = ctk.CTkEntry(f_filtro, width=120)
        self.ent_busca_num.pack(side="left", padx=5)

        btn_buscar = ctk.CTkButton(f_filtro, text="🔍 Buscar", width=80, command=self.carregar_lista_encartes)
        btn_buscar.pack(side="left", padx=5)

        btn_limpar = ctk.CTkButton(f_filtro, text="Limpar", width=80, fg_color="gray", command=self.limpar_busca)
        btn_limpar.pack(side="left", padx=5)

        # Lista Scrollável de Encartes
        self.frame_encartes = ctk.CTkScrollableFrame(self)
        self.frame_encartes.pack(fill="both", expand=True, padx=10, pady=10)

    def abrir_parametros(self):
        ParametrosWindow(self)

    def novo_encarte(self):
        FormEncarteWindow(self)

    def limpar_busca(self):
        self.ent_busca_num.delete(0, "end")
        self.carregar_lista_encartes()

    def carregar_lista_encartes(self):
        for w in self.frame_encartes.winfo_children():
            w.destroy()

        schema = get_schema()
        filtro_num = self.ent_busca_num.get().strip()

        try:
            conn = get_connection()
            cur = conn.cursor()

            if filtro_num:
                cur.execute(f"SELECT * FROM {schema}.encarte_cabecalho WHERE num_encarte = %s ORDER BY id DESC;", (int(filtro_num),))
            else:
                cur.execute(f"SELECT * FROM {schema}.encarte_cabecalho ORDER BY id DESC;")

            encartes = cur.fetchall()
            conn.close()

            if not encartes:
                ctk.CTkLabel(self.frame_encartes, text="Nenhum encarte cadastrado ou encontrado.").pack(pady=20)
                return

            for enc in encartes:
                self.renderizar_card_encarte(enc)

        except Exception as e:
            ctk.CTkLabel(self.frame_encartes, text=f"Erro ao carregar dados do banco:\n{str(e)}").pack(pady=20)

    def renderizar_card_encarte(self, enc):
        f_card = ctk.CTkFrame(self.frame_encartes)
        f_card.pack(fill="x", pady=5, padx=5)

        info_text = f"Encarte #{enc['num_encarte']} | Período: {enc['dt_inicio']} até {enc['dt_fim']}"
        if enc.get("titulo_rodape"):
            info_text += f" | Título: {enc['titulo_rodape']}"

        ctk.CTkLabel(f_card, text=info_text, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)

        btn_excluir = ctk.CTkButton(f_card, text="🗑️ Excluir", fg_color="#C62828", hover_color="#B71C1C", width=80, command=lambda e_id=enc["id"]: self.excluir_encarte(e_id))
        btn_excluir.pack(side="right", padx=5, pady=10)

        btn_editar = ctk.CTkButton(f_card, text="✏️ Editar", fg_color="#1976D2", hover_color="#0D47A1", width=80, command=lambda e_id=enc["id"]: self.editar_encarte(e_id))
        btn_editar.pack(side="right", padx=5, pady=10)

    def editar_encarte(self, enc_id):
        FormEncarteWindow(self, encarte_id=enc_id)

    def excluir_encarte(self, enc_id):
        if messagebox.askyesno("Confirmação", "Deseja realmente excluir este encarte e todos os seus itens?"):
            schema = get_schema()
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute(f"DELETE FROM {schema}.encarte_cabecalho WHERE id = %s;", (enc_id,))
                conn.commit()
                conn.close()
                messagebox.showinfo("Sucesso", "Encarte excluído!")
                self.carregar_lista_encartes()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir encarte:\n{str(e)}")


if __name__ == "__main__":
    app = AppGestaoEncarte()
    app.mainloop()
