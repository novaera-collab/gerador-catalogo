# -*- coding: utf-8 -*-
import sys
import os
import json
import re
import traceback
import base64
import subprocess
import customtkinter as ctk
from datetime import datetime, date
from tkinter import messagebox, Toplevel, filedialog
import psycopg2
from psycopg2.extras import RealDictCursor
from tkcalendar import DateEntry

if sys.platform.startswith("win"):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def mostrar_erro_fatal(exc_type, exc_value, exc_traceback):
    erro_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    messagebox.showerror("Erro Fatal na Inicialização", f"Ocorreu um erro ao abrir o app:\n\n{erro_msg}")

sys.excepthook = mostrar_erro_fatal

CONFIG_FILE = "config_banco.json"

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
                return cfg
        except Exception:
            pass
    return {
        "host": "localhost",
        "database": "seu_banco",
        "user": "postgres",
        "password": "",
        "port": "5432",
        "schema": "public"
    }

def salvar_config(cfg):
    cfg_copy = cfg.copy()
    if "password" in cfg_copy:
        cfg_copy["password"] = encriptar_texto(cfg_copy["password"])
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg_copy, f, indent=4)

def get_connection():
    cfg = carregar_config()
    conn = psycopg2.connect(
        host=cfg.get("host", "localhost"),
        database=cfg.get("database", "seu_banco"),
        user=cfg.get("user", "postgres"),
        password=cfg.get("password", ""),
        port=cfg.get("port", "5432"),
        cursor_factory=RealDictCursor
    )
    conn.set_client_encoding('LATIN1')
    return conn

def get_schema():
    cfg = carregar_config()
    schema = cfg.get("schema", "public").strip()
    return schema if schema else "public"

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
        "rodape_logo_fone": ""
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
                rodape_logo_fone = %s
            WHERE id = %s
        """
        cur.execute(query, (
            p.get("dir_encarte", ""), p.get("dir_csv", ""), p.get("dir_jpg", ""),
            p.get("cor_tit_rodape", ""), p.get("cor_grid_tarja", ""), p.get("cor_grid_preco", ""),
            p.get("cabecalho_logo", ""), p.get("cabecalho_site", ""), p.get("rodape_logo_fone", ""),
            res["id"]
        ))
    else:
        query = f"""
            INSERT INTO {schema}.encarte_parametros (
                dir_encarte, dir_csv, dir_jpg, cor_tit_rodape, cor_grid_tarja,
                cor_grid_preco, cabecalho_logo, cabecalho_site, rodape_logo_fone
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            p.get("dir_encarte", ""), p.get("dir_csv", ""), p.get("dir_jpg", ""),
            p.get("cor_tit_rodape", ""), p.get("cor_grid_tarja", ""), p.get("cor_grid_preco", ""),
            p.get("cabecalho_logo", ""), p.get("cabecalho_site", ""), p.get("rodape_logo_fone", "")
        ))
    conn.commit()
    conn.close()

class NovoContatoModal(ctk.CTkToplevel):
    def __init__(self, parent, callback_sucesso):
        super().__init__(parent)
        self.callback_sucesso = callback_sucesso
        self.title("Novo Contato")
        self.geometry("380x200")
        self.grab_set()

        ctk.CTkLabel(self, text="Nome:").pack(anchor="w", padx=20, pady=(15, 2))
        self.txt_nome = ctk.CTkEntry(self, width=320)
        self.txt_nome.pack(padx=20, pady=2)

        ctk.CTkLabel(self, text="Telefone:").pack(anchor="w", padx=20, pady=(10, 2))
        self.txt_fone = ctk.CTkEntry(self, width=320, placeholder_text="(45) 99999-9999")
        self.txt_fone.pack(padx=20, pady=2)

        btn_salvar = ctk.CTkButton(self, text="Salvar Contato", fg_color="#2E7D32", command=self.salvar)
        btn_salvar.pack(pady=15)

    def salvar(self):
        nome = self.txt_nome.get().strip()
        fone = self.txt_fone.get().strip()
        schema = get_schema()

        if not nome or not fone:
            messagebox.showwarning("Atenção", "Informe o Nome e o Telefone.", parent=self)
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"INSERT INTO {schema}.encarte_contatos (nome, telefone) VALUES (%s, %s)", (nome, fone))
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", "Contato cadastrado!", parent=self)
            self.callback_sucesso(nome)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar contato:\n{e}", parent=self)

class GerarEncarteModal(ctk.CTkToplevel):
    def __init__(self, parent, encarte_id, encarte_titulo):
        super().__init__(parent)
        self.encarte_id = encarte_id
        self.encarte_titulo = encarte_titulo

        self.title(f"Gerar Encarte #{encarte_id}")
        self.geometry("460x340")
        self.grab_set()

        self.contatos_map = {}

        ctk.CTkLabel(self, text=f"Gerar Encarte: {encarte_titulo}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))

        # Contato
        frame_ct = ctk.CTkFrame(self, fg_color="transparent")
        frame_ct.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_ct, text="Contato:").grid(row=0, column=0, sticky="w", padx=5)
        self.cmb_contato = ctk.CTkComboBox(frame_ct, width=240, values=[])
        self.cmb_contato.grid(row=0, column=1, padx=5)

        btn_novo_contato = ctk.CTkButton(frame_ct, text="+ Novo", width=60, fg_color="#1976D2", command=self.abrir_novo_contato)
        btn_novo_contato.grid(row=0, column=2, padx=5)

        # Tabela de Preço (1, 2 ou 3)
        frame_tb = ctk.CTkFrame(self, fg_color="transparent")
        frame_tb.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_tb, text="Tabela de Preço:").grid(row=0, column=0, sticky="w", padx=5)
        self.cmb_tabela = ctk.CTkComboBox(frame_tb, width=120, values=["1", "2", "3"])
        self.cmb_tabela.set("1")
        self.cmb_tabela.grid(row=0, column=1, sticky="w", padx=5)

        # Saldo (Default: Positivos)
        frame_sd = ctk.CTkFrame(self, fg_color="transparent")
        frame_sd.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_sd, text="Saldo:").grid(row=0, column=0, sticky="w", padx=5)
        self.var_saldo = ctk.StringVar(value="Positivos")
        rb_todos = ctk.CTkRadioButton(frame_sd, text="Todos", variable=self.var_saldo, value="Todos")
        rb_todos.grid(row=0, column=1, padx=15)
        rb_pos = ctk.CTkRadioButton(frame_sd, text="Positivos", variable=self.var_saldo, value="Positivos")
        rb_pos.grid(row=0, column=2, padx=15)

        btn_gerar = ctk.CTkButton(self, text="Confirmar e Gerar Encarte", fg_color="#1B5E20", font=ctk.CTkFont(weight="bold"), height=35, command=self.processar_geracao)
        btn_gerar.pack(pady=20)

        self.carregar_contatos()

    def carregar_contatos(self, selecionar_nome=None):
        schema = get_schema()
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT nome, telefone FROM {schema}.encarte_contatos ORDER BY nome")
            rows = cur.fetchall()
            conn.close()

            self.contatos_map = {r['nome']: r['telefone'] for r in rows}
            nomes = list(self.contatos_map.keys())

            if not nomes:
                nomes = ["NENHUM CONTATO"]

            self.cmb_contato.configure(values=nomes)

            if selecionar_nome and selecionar_nome in self.contatos_map:
                self.cmb_contato.set(selecionar_nome)
            elif nomes:
                self.cmb_contato.set(nomes[0])

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar contatos:\n{e}", parent=self)

    def abrir_novo_contato(self):
        NovoContatoModal(self, callback_sucesso=lambda nome: self.carregar_contatos(selecionar_nome=nome))

    def processar_geracao(self):
        schema = get_schema()
        contato_sel = self.cmb_contato.get()
        tabela_sel = self.cmb_tabela.get()

        params = carregar_parametros_banco()
        dir_encarte = os.path.abspath(os.path.expanduser(os.path.expandvars(params.get("dir_encarte", "").strip())))
        dir_csv = os.path.abspath(os.path.expanduser(os.path.expandvars(params.get("dir_csv", "").strip())))
        dir_jpg = os.path.abspath(os.path.expanduser(os.path.expandvars(params.get("dir_jpg", "").strip())))

        if not dir_encarte or not os.path.exists(dir_encarte):
            messagebox.showerror("Erro de Configuração", f"Diretório Executáveis/Encarte (dir_encarte) inválido:\n{dir_encarte}", parent=self)
            return

        if not dir_csv or not os.path.exists(dir_csv):
            messagebox.showerror("Erro de Configuração", f"Diretório do CSV (dir_csv) inválido:\n{dir_csv}", parent=self)
            return

        if not dir_jpg or not os.path.exists(dir_jpg):
            messagebox.showerror("Erro de Configuração", f"Diretório de JPG (dir_jpg) inválido:\n{dir_jpg}", parent=self)
            return

        path_sql = os.path.join(dir_encarte, "consulta_encarte.sql")
        if not os.path.exists(path_sql):
            messagebox.showerror("Arquivo Ausente", f"O arquivo 'consulta_encarte.sql' não foi encontrado em:\n{dir_encarte}", parent=self)
            return

        filtro_saldo_sql = "" if self.var_saldo.get() == "Todos" else "WHERE fsaldo > 0"

        try:
            try:
                with open(path_sql, "r", encoding="utf-8") as f:
                    sql_template = f.read()
            except UnicodeDecodeError:
                with open(path_sql, "r", encoding="cp1252") as f:
                    sql_template = f.read()

            contato_sanitizado = contato_sel.replace("'", "''")

            sql_final = sql_template.replace("{SCHEMA}", schema) \
                                    .replace("{ID_ENCARTE}", str(self.encarte_id)) \
                                    .replace("{TABELA_PRECO}", tabela_sel) \
                                    .replace("{CONTATO_SEL}", contato_sanitizado) \
                                    .replace("{FILTRO_SALDO}", filtro_saldo_sql)

            conn = get_connection()
            cur = conn.cursor()
            cur.execute(sql_final)
            linhas = cur.fetchall()
            conn.close()

            # Sanitiza o nome do contato para o arquivo CSV
            nome_contato_limpo = re.sub(r'[^\w\s-]', '', contato_sel).strip().replace(" ", "_")
            if not nome_contato_limpo:
                nome_contato_limpo = "geral"

            # Nome dos arquivos CSV e JPG ajustados dinamicamente
            nome_arquivo_csv = f"{self.encarte_id}_encarte_{nome_contato_limpo}.csv"
            nome_arquivo_jpg = f"{self.encarte_id}_DADOS_CATALOGO.jpg"

            path_out_csv = os.path.normpath(os.path.join(dir_csv, nome_arquivo_csv))
            path_out_jpg = os.path.normpath(os.path.join(dir_jpg, nome_arquivo_jpg))

            with open(path_out_csv, "w", encoding="utf-8-sig", errors="replace", newline="") as f_csv:
                for row in linhas:
                    linha_texto = row.get('linha_csv')
                    if linha_texto is not None:
                        f_csv.write(f"{str(linha_texto).strip()}\r\n")

            # Executáveis conforme cadastrados/existentes no diretório de parâmetros
            exe_gerar = os.path.join(dir_encarte, "gerar_catalogo.exe")
            exe_viewer = os.path.join(dir_encarte, "visualizar_catalogo.exe")

            # Chamada dos executáveis parametrizados
            if os.path.exists(exe_gerar):
                subprocess.run([exe_gerar, path_out_csv, path_out_jpg], check=False)
            else:
                messagebox.showwarning("Aviso", f"Executável 'gerar_catalogo.exe' não encontrado em:\n{exe_gerar}", parent=self)

            if os.path.exists(exe_viewer):
                subprocess.Popen([exe_viewer, path_out_jpg])
            else:
                messagebox.showwarning("Aviso", f"Visualizador 'visualizar_catalogo.exe' não encontrado em:\n{exe_viewer}", parent=self)

            messagebox.showinfo("Sucesso", f"Encarte gerado com sucesso!\n\nCSV: {path_out_csv}\nJPG: {path_out_jpg}", parent=self)
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro na Geração", f"Falha ao executar consulta ou gerar arquivo:\n{e}", parent=self)

class ParametrosWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Parâmetros do Sistema")
        self.geometry("640x620")
        self.grab_set()

        cfg = carregar_config()
        params_db = carregar_parametros_banco()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=15, pady=10)

        tab_banco = tabview.add("Conexão com Banco de Dados")
        tab_dirs = tabview.add("Diretórios e Design")

        ctk.CTkLabel(tab_banco, text="Host / IP:").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.txt_host = ctk.CTkEntry(tab_banco, width=280)
        self.txt_host.insert(0, cfg.get("host", ""))
        self.txt_host.grid(row=0, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Banco de Dados:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.txt_db = ctk.CTkEntry(tab_banco, width=280)
        self.txt_db.insert(0, cfg.get("database", ""))
        self.txt_db.grid(row=1, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Schema:").grid(row=2, column=0, padx=10, pady=6, sticky="w")
        self.txt_schema = ctk.CTkEntry(tab_banco, width=280, placeholder_text="ex: public ou dk")
        self.txt_schema.insert(0, cfg.get("schema", "public"))
        self.txt_schema.grid(row=2, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Usuário:").grid(row=3, column=0, padx=10, pady=6, sticky="w")
        self.txt_user = ctk.CTkEntry(tab_banco, width=280)
        self.txt_user.insert(0, cfg.get("user", ""))
        self.txt_user.grid(row=3, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Senha:").grid(row=4, column=0, padx=10, pady=6, sticky="w")
        self.txt_pass = ctk.CTkEntry(tab_banco, width=280, show="*")
        self.txt_pass.insert(0, cfg.get("password", ""))
        self.txt_pass.grid(row=4, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Porta:").grid(row=5, column=0, padx=10, pady=6, sticky="w")
        self.txt_port = ctk.CTkEntry(tab_banco, width=280)
        self.txt_port.insert(0, cfg.get("port", "5432"))
        self.txt_port.grid(row=5, column=1, padx=10, pady=6)

        btn_criar_tabelas = ctk.CTkButton(
            tab_banco, text="Criar Tabelas no Banco de Dados", 
            fg_color="#0288D1", hover_color="#0277BD", 
            font=ctk.CTkFont(weight="bold"), height=35,
            command=self.criar_tabelas_banco
        )
        btn_criar_tabelas.grid(row=6, column=0, columnspan=2, pady=20, padx=10, sticky="ew")

        self.txt_dir_encarte = self._criar_campo_caminho(tab_dirs, "Diretório Executáveis:", 0, params_db.get("dir_encarte", ""), pasta=True)
        self.txt_dir_csv = self._criar_campo_caminho(tab_dirs, "Diretório CSV:", 1, params_db.get("dir_csv", ""), pasta=True)
        self.txt_dir_jpg = self._criar_campo_caminho(tab_dirs, "Diretório JPG:", 2, params_db.get("dir_jpg", ""), pasta=True)
        
        self.txt_cabecalho_logo = self._criar_campo_caminho(tab_dirs, "Cabeçalho Logo:", 3, params_db.get("cabecalho_logo", ""), pasta=False)
        self.txt_rodape_logo_fone = self._criar_campo_caminho(tab_dirs, "Rodapé Logo Fone:", 4, params_db.get("rodape_logo_fone", ""), pasta=False)

        ctk.CTkLabel(tab_dirs, text="Cabeçalho Site:").grid(row=5, column=0, padx=10, pady=6, sticky="w")
        self.txt_cabecalho_site = ctk.CTkEntry(tab_dirs, width=240)
        self.txt_cabecalho_site.insert(0, params_db.get("cabecalho_site", ""))
        self.txt_cabecalho_site.grid(row=5, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab_dirs, text="Cor Título/Rodapé:").grid(row=6, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_tit_rodape = ctk.CTkEntry(tab_dirs, width=240, placeholder_text="#HEX ou Código Cor")
        self.txt_cor_tit_rodape.insert(0, params_db.get("cor_tit_rodape", ""))
        self.txt_cor_tit_rodape.grid(row=6, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab_dirs, text="Cor Grid Tarja:").grid(row=7, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_grid_tarja = ctk.CTkEntry(tab_dirs, width=240)
        self.txt_cor_grid_tarja.insert(0, params_db.get("cor_grid_tarja", ""))
        self.txt_cor_grid_tarja.grid(row=7, column=1, padx=5, pady=6)

        ctk.CTkLabel(tab_dirs, text="Cor Grid Preço:").grid(row=8, column=0, padx=10, pady=6, sticky="w")
        self.txt_cor_grid_preco = ctk.CTkEntry(tab_dirs, width=240)
        self.txt_cor_grid_preco.insert(0, params_db.get("cor_grid_preco", ""))
        self.txt_cor_grid_preco.grid(row=8, column=1, padx=5, pady=6)

        btn_salvar = ctk.CTkButton(self, text="Salvar Tudo", fg_color="#1B5E20", font=ctk.CTkFont(weight="bold"), height=35, command=self.salvar)
        btn_salvar.pack(pady=(0, 15))

    def _criar_campo_caminho(self, parent, label_text, row, valor_inicial, pasta=True):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        txt_entry = ctk.CTkEntry(parent, width=240)
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
                title="Selecione a Imagem", 
                filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp"), ("Todos os Arquivos", "*.*")]
            )
        
        if caminho:
            caminho_formatado = caminho.replace("/", "\\")
            entry_widget.delete(0, "end")
            entry_widget.insert(0, caminho_formatado)

    def criar_tabelas_banco(self):
        self.salvar_apenas_config_json()
        schema = get_schema()
        
        sql_script = f"""
        CREATE SCHEMA IF NOT EXISTS {schema};

        CREATE SEQUENCE IF NOT EXISTS {schema}.encarte_id_seq;
        CREATE SEQUENCE IF NOT EXISTS {schema}.encarte_item_id_seq;
        CREATE SEQUENCE IF NOT EXISTS {schema}.encarte_parametros_id_seq;

        CREATE TABLE IF NOT EXISTS {schema}.encarte
        (
            id integer NOT NULL DEFAULT nextval('{schema}.encarte_id_seq'::regclass),
            titulo character varying(100) COLLATE pg_catalog."default" NOT NULL,
            data_inicio date NOT NULL,
            data_fim date NOT NULL,
            status character varying(20) COLLATE pg_catalog."default" DEFAULT 'ATIVO'::character varying,
            criado_em timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT encarte_pkey PRIMARY KEY (id)
        );

        CREATE TABLE IF NOT EXISTS {schema}.encarte_item
        (
            id integer NOT NULL DEFAULT nextval('{schema}.encarte_item_id_seq'::regclass),
            encarte_id integer,
            codigo_prod character varying(30) COLLATE pg_catalog."default" NOT NULL,
            preco_oferta numeric(12,2) NOT NULL,
            qtde_oferta numeric(12,2) NOT NULL,
            ordem integer DEFAULT 0,
            CONSTRAINT encarte_item_pkey PRIMARY KEY (id)
        );

        CREATE TABLE IF NOT EXISTS {schema}.encarte_contatos
        (
            nome character varying(100),
            telefone character varying(30)
        );

        CREATE TABLE IF NOT EXISTS {schema}.encarte_parametros
        (
            id integer NOT NULL DEFAULT nextval('{schema}.encarte_parametros_id_seq'::regclass),
            dir_encarte character varying(255),
            dir_csv character varying(255),
            dir_jpg character varying(255),
            cor_tit_rodape character varying(50),
            cor_grid_tarja character varying(50),
            cor_grid_preco character varying(50),
            cabecalho_logo character varying(255),
            cabecalho_site character varying(255),
            rodape_logo_fone character varying(255),
            CONSTRAINT encarte_parametros_pkey PRIMARY KEY (id)
        );
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(sql_script)
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", f"Tabelas criadas/verificadas com sucesso no schema '{schema}'!", parent=self)
        except Exception as e:
            messagebox.showerror("Erro ao Criar Tabelas", f"Falha na execução do SQL:\n{e}", parent=self)

    def salvar_apenas_config_json(self):
        cfg = {
            "host": self.txt_host.get().strip(),
            "database": self.txt_db.get().strip(),
            "schema": self.txt_schema.get().strip(),
            "user": self.txt_user.get().strip(),
            "password": self.txt_pass.get().strip(),
            "port": self.txt_port.get().strip()
        }
        salvar_config(cfg)

    def salvar(self):
        self.salvar_apenas_config_json()
        
        params_db = {
            "dir_encarte": self.txt_dir_encarte.get().strip(),
            "dir_csv": self.txt_dir_csv.get().strip(),
            "dir_jpg": self.txt_dir_jpg.get().strip(),
            "cabecalho_logo": self.txt_cabecalho_logo.get().strip(),
            "rodape_logo_fone": self.txt_rodape_logo_fone.get().strip(),
            "cabecalho_site": self.txt_cabecalho_site.get().strip(),
            "cor_tit_rodape": self.txt_cor_tit_rodape.get().strip(),
            "cor_grid_tarja": self.txt_cor_grid_tarja.get().strip(),
            "cor_grid_preco": self.txt_cor_grid_preco.get().strip()
        }
        
        try:
            salvar_parametros_banco(params_db)
            messagebox.showinfo("Sucesso", "Todos os parâmetros foram salvos com sucesso!", parent=self)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar parâmetros na tabela do banco:\n{e}", parent=self)

class PesquisaProdutoModal(ctk.CTkToplevel):
    def __init__(self, parent, callback_selecao):
        super().__init__(parent)
        self.parent = parent
        self.callback_selecao = callback_selecao

        self.title("Pesquisa de Produtos (ESPROD)")
        self.geometry("700x480")
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

class FormEncarteWindow(ctk.CTkToplevel):
    def __init__(self, parent, encarte_id=None, callback_refresh=None):
        super().__init__(parent)
        self.encarte_id = encarte_id
        self.callback_refresh = callback_refresh
        self.itens = []

        self.title("Alteração de Encarte" if encarte_id else "Novo Encarte")
        self.geometry("820x580")
        self.grab_set()

        self.criar_widgets()
        if self.encarte_id:
            self.carregar_dados()

    def criar_widgets(self):
        frame_top_bar = ctk.CTkFrame(self, fg_color="transparent")
        frame_top_bar.pack(fill="x", padx=15, pady=(8, 2))

        lbl_titulo = ctk.CTkLabel(frame_top_bar, text="Manutenção do Encarte", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.pack(side="left")

        btn_voltar = ctk.CTkButton(frame_top_bar, text="Voltar", width=80, height=28, fg_color="#455A64", command=self.destroy)
        btn_voltar.pack(side="right")

        frame_head = ctk.CTkFrame(self)
        frame_head.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_head, text="Título:").grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self.txt_titulo = ctk.CTkEntry(frame_head, width=380, placeholder_text="Ex: ENCARTE FARMAX")
        self.txt_titulo.grid(row=0, column=1, columnspan=3, padx=8, pady=4, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Início:").grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self.txt_dt_ini = ctk.CTkEntry(frame_head, width=110, placeholder_text="29/08/2026")
        self.txt_dt_ini.grid(row=1, column=1, padx=(8, 2), pady=4, sticky="w")
        btn_cal_ini = ctk.CTkButton(frame_head, text="Cal", width=35, height=26, command=lambda: self.abrir_calendario(self.txt_dt_ini))
        btn_cal_ini.grid(row=1, column=1, padx=(122, 0), pady=4, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Fim:").grid(row=1, column=2, padx=8, pady=4, sticky="w")
        self.txt_dt_fim = ctk.CTkEntry(frame_head, width=110, placeholder_text="05/09/2026")
        self.txt_dt_fim.grid(row=1, column=3, padx=(8, 2), pady=4, sticky="w")
        btn_cal_fim = ctk.CTkButton(frame_head, text="Cal", width=35, height=26, command=lambda: self.abrir_calendario(self.txt_dt_fim))
        btn_cal_fim.grid(row=1, column=3, padx=(122, 0), pady=4, sticky="w")

        frame_prod = ctk.CTkFrame(self)
        frame_prod.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_prod, text="Cód. Prod:").grid(row=0, column=0, padx=4, pady=4)
        
        self.txt_p_cod = ctk.CTkEntry(frame_prod, width=75, placeholder_text="00001")
        self.txt_p_cod.grid(row=0, column=1, padx=(4, 2), pady=4)
        self.txt_p_cod.bind("<FocusOut>", self.formatar_codigo_evento)

        btn_lupa = ctk.CTkButton(frame_prod, text="Lupa", width=42, height=26, fg_color="#1976D2", command=self.abrir_lupa)
        btn_lupa.grid(row=0, column=2, padx=(0, 8), pady=4)

        ctk.CTkLabel(frame_prod, text="A partir de:").grid(row=0, column=3, padx=2, pady=4)
        self.txt_p_qtde = ctk.CTkEntry(frame_prod, width=60, placeholder_text="1.00")
        self.txt_p_qtde.insert(0, "1")
        self.txt_p_qtde.grid(row=0, column=4, padx=(2, 2), pady=4)
        ctk.CTkLabel(frame_prod, text="unid.", text_color="gray").grid(row=0, column=5, padx=(0, 8), pady=4)

        ctk.CTkLabel(frame_prod, text="Valor Oferta (R$):").grid(row=0, column=6, padx=2, pady=4)
        self.txt_p_preco = ctk.CTkEntry(frame_prod, width=85, placeholder_text="0.00")
        self.txt_p_preco.grid(row=0, column=7, padx=4, pady=4)

        btn_add = ctk.CTkButton(frame_prod, text="+ Adicionar", width=85, height=28, fg_color="#2E7D32", command=self.adicionar_item)
        btn_add.grid(row=0, column=8, padx=8, pady=4)

        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=15, pady=(2, 10))

        btn_salvar = ctk.CTkButton(frame_botoes, text="Salvar no Banco", font=ctk.CTkFont(weight="bold"), fg_color="#1B5E20", height=36, width=130, command=self.salvar_banco)
        btn_salvar.pack(side="right", padx=5)

        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#C62828", height=36, width=100, command=self.destroy)
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

class AppPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestão de Encartes - v2.0")
        self.geometry("850x600")

        frame_topo = ctk.CTkFrame(self)
        frame_topo.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(frame_topo, text="Encartes Cadastrados", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        btn_sair = ctk.CTkButton(frame_topo, text="Sair", fg_color="#C62828", width=80, command=self.destroy)
        btn_sair.pack(side="right", padx=5, pady=5)

        btn_params = ctk.CTkButton(frame_topo, text="Parâmetros", fg_color="#455A64", width=110, command=self.abrir_parametros)
        btn_params.pack(side="right", padx=5, pady=5)

        btn_novo = ctk.CTkButton(frame_topo, text="Novo Encarte", fg_color="#2E7D32", width=120, command=self.novo_encarte)
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
                row.pack(fill="x", pady=6, padx=5)

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

                vencido = data_vencimento < hoje
                cor_status = "#EF5350" if vencido else "#66BB6A"

                lbl_info = f"#{enc['id']} - {enc['titulo']}\nPeríodo: {dt_ini_str} a {dt_fim_str}"
                ctk.CTkLabel(row, text=lbl_info, anchor="w", font=ctk.CTkFont(weight="bold"), text_color=cor_status, justify="left").pack(side="left", padx=15, pady=8, fill="x", expand=True)

                frame_acoes = ctk.CTkFrame(row, fg_color="transparent")
                frame_acoes.pack(side="right", padx=10, pady=5)

                if not vencido:
                    btn_gerar = ctk.CTkButton(
                        frame_acoes, text="Gerar Encarte", width=110, height=26, fg_color="#2E7D32", hover_color="#1B5E20",
                        command=lambda e_id=enc['id'], e_tit=enc['titulo']: self.gerar_encarte(e_id, e_tit)
                    )
                    btn_gerar.pack(pady=2)

                btn_editar = ctk.CTkButton(
                    frame_acoes, text="Editar", width=110, height=26,
                    command=lambda e_id=enc['id']: self.editar_encarte(e_id)
                )
                btn_editar.pack(pady=2)

                btn_excluir = ctk.CTkButton(
                    frame_acoes, text="Excluir", width=110, height=26, fg_color="#C62828", hover_color="#B71C1C",
                    command=lambda e_id=enc['id'], e_tit=enc['titulo']: self.excluir_encarte(e_id, e_tit)
                )
                btn_excluir.pack(pady=2)

        except Exception as e:
            ctk.CTkLabel(self.frame_lista, text=f"Erro ao consultar o banco de dados:\n{e}", text_color="#EF5350").pack(pady=20)

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

    def gerar_encarte(self, encarte_id, titulo):
        GerarEncarteModal(self, encarte_id=encarte_id, encarte_titulo=titulo)

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = AppPrincipal()
    app.mainloop()
