# -*- coding: utf-8 -*-
import sys
import os
import json
import traceback
import subprocess
import psycopg2
import psycopg2.extras
import tkinter as tk
from tkinter import ttk, messagebox

CONFIG_FILE = "config.json"

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "host": "localhost",
        "port": "5432",
        "dbname": "unicodb",
        "user": "postgres",
        "password": "",
        "schema": "dk",
        "diretorio_retorno": os.getcwd()
    }

class DBConnection:
    def __init__(self, config):
        self.config = config

    def get_connection(self):
        return psycopg2.connect(
            host=self.config.get("host", "localhost"),
            port=self.config.get("port", "5432"),
            dbname=self.config.get("dbname", "unicodb"),
            user=self.config.get("user", "postgres"),
            password=self.config.get("password", ""),
            options=f"-c search_path={self.config.get('schema', 'dk')}"
        )

    def executar_consulta(self, query):
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        finally:
            conn.close()

class JanelaModalGerar:
    def __init__(self, parent, encarte_id, encarte_titulo, dt_inicio, dt_fim, config, db):
        self.win = tk.Toplevel(parent)
        self.win.title(f"Gerando Encarte #{encarte_id}")
        self.win.geometry("420x360")
        self.win.resizable(False, False)
        self.win.grab_set()

        self.encarte_id = encarte_id
        self.encarte_titulo = encarte_titulo
        self.validade_texto = f"Precos validos no periodo de {dt_inicio} a {dt_fim}" if dt_inicio else ""
        self.config = config
        self.db = db

        tk.Label(self.win, text="Nome do Contato (Rodapé):", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(15, 2))
        self.txt_nome = tk.Entry(self.win, width=45)
        self.txt_nome.insert(0, "JOSE")
        self.txt_nome.pack(padx=15, pady=2)

        tk.Label(self.win, text="Contato WhatsApp:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
        self.txt_whatsapp = tk.Entry(self.win, width=45)
        self.txt_whatsapp.insert(0, "(45) 99905-1999")
        self.txt_whatsapp.pack(padx=15, pady=2)

        tk.Label(self.win, text="Tabela de Preço:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15, pady=(8, 2))
        self.combo_tabela = ttk.Combobox(self.win, values=["Tabela 1", "Tabela 2", "Tabela 3"], state="readonly", width=42)
        self.combo_tabela.current(2)
        self.combo_tabela.pack(padx=15, pady=2)

        self.var_saldo = tk.BooleanVar(value=True)
        self.chk_saldo = tk.Checkbutton(self.win, text="Somente produtos com saldo > 0", variable=self.var_saldo)
        self.chk_saldo.pack(anchor="w", padx=15, pady=10)

        btn_executar = tk.Button(
            self.win, 
            text="🚀 Executar Geração", 
            bg="#22702C", 
            fg="white", 
            font=("Arial", 10, "bold"), 
            command=self.executar_geracao, 
            height=2,
            cursor="hand2"
        )
        btn_executar.pack(fill="x", padx=15, pady=10)

    def executar_geracao(self):
        nome_contato = self.txt_nome.get().strip()
        whatsapp = self.txt_whatsapp.get().strip()
        tabela_opcao = str(self.combo_tabela.current() + 1)
        filtro_saldo = "AND e.fsaldo > 0" if self.var_saldo.get() else ""

        caminho_sql = os.path.join(os.getcwd(), "consulta_catalogo.sql")
        if not os.path.exists(caminho_sql):
            messagebox.showerror("Erro", "Arquivo 'consulta_catalogo.sql' não foi encontrado na pasta do sistema.")
            return

        try:
            with open(caminho_sql, "r", encoding="utf-8") as f:
                query = f.read()

            # Substituição das variáveis na instrução SQL
            query = query.replace("{SCHEMA}", self.config.get("schema", "dk"))
            query = query.replace("{ID_ENCARTE}", str(self.encarte_id))
            query = query.replace("{TABELA_PRECO}", tabela_opcao)
            query = query.replace("{FILTRO_SALDO}", filtro_saldo)

            rows = self.db.executar_consulta(query)

            if not rows:
                messagebox.showwarning("Aviso", "Nenhum produto foi encontrado para o encarte selecionado.")
                return

            pasta_saida = self.config.get("diretorio_retorno", os.getcwd())
            os.makedirs(pasta_saida, exist_ok=True)

            caminho_csv = os.path.join(pasta_saida, "DADOS_CATALOGO.CSV")
            caminho_jpg = os.path.join(pasta_saida, "CATALOGO_OESTE_PHARMA.JPG")

            # Escreve os Metadados no topo do CSV + Lista de Produtos
            with open(caminho_csv, "w", encoding="latin-1", newline="", errors="ignore") as f:
                f.write(f"titulo;{self.encarte_titulo}\n")
                f.write(f"logo;{os.path.join(os.getcwd(), 'logo', 'oeste.jpg')}\n")
                f.write(f"logo_fone;{os.path.join(os.getcwd(), 'logo', 'ico-whats.bmp')}\n")
                f.write(f"rodape;{nome_contato}\n")
                f.write(f"fone;{whatsapp}\n")
                f.write(f"validade;{self.validade_texto}\n")
                f.write(f"saida_jpg;{caminho_jpg}\n")
                f.write("codigo;descricao;foto;linha_preco\n")

                for r in rows:
                    codigo = str(r.get('codigo', '')).strip()
                    desc = str(r.get('descricao', '')).strip()
                    foto = str(r.get('foto', '')).strip()
                    preco = str(r.get('linha_preco', '')).strip()
                    f.write(f"{codigo};{desc};{foto};{preco}\n")

            # 1. Executa Gerar_catalogo.exe (gera a imagem JPG)
            exe_gerar = os.path.join(os.getcwd(), "Gerar_catalogo.exe")
            if os.path.exists(exe_gerar):
                subprocess.run([exe_gerar, caminho_csv], check=True)

            # 2. Executa visualizar_catalogo.exe (abre a interface de envio)
            exe_visualizar = os.path.join(os.getcwd(), "visualizar_catalogo.exe")
            if os.path.exists(exe_visualizar):
                subprocess.Popen([exe_visualizar, pasta_saida, caminho_jpg])

            self.win.destroy()

        except Exception as e:
            messagebox.showerror("Falha na Geração", f"Ocorreu um erro ao processar o encarte:\n{e}\n\n{traceback.format_exc()}")

class AppPrincipal:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestão de Encartes - Oeste Pharma")
        self.root.geometry("850x520")

        self.config = carregar_config()
        self.db = DBConnection(self.config)

        # Cabeçalho Superior
        frame_topo = tk.Frame(self.root, bg="#22702C", height=50)
        frame_topo.pack(fill="x", side="top")

        lbl_titulo = tk.Label(frame_topo, text="Painel de Gestão de Encartes", font=("Arial", 14, "bold"), fg="white", bg="#22702C")
        lbl_titulo.pack(side="left", padx=15, pady=10)

        btn_atualizar = tk.Button(frame_topo, text="🔄 Atualizar Lista", font=("Arial", 9, "bold"), bg="white", command=self.carregar_encartes, cursor="hand2")
        btn_atualizar.pack(side="right", padx=15, pady=10)

        # Tabela de Encartes (Treeview)
        frame_tabela = tk.Frame(self.root)
        frame_tabela.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(frame_tabela, columns=("id", "titulo", "inicio", "fim", "status"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("titulo", text="Título do Encarte")
        self.tree.heading("inicio", text="Data Início")
        self.tree.heading("fim", text="Data Fim")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("titulo", width=380)
        self.tree.column("inicio", width=110, anchor="center")
        self.tree.column("fim", width=110, anchor="center")
        self.tree.column("status", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill="both", expand=True, side="left")
        scrollbar.pack(side="right", fill="y")

        # Botão de Ação Inferior
        btn_gerar = tk.Button(
            self.root, 
            text="⚡ Gerar Encarte Selecionado", 
            font=("Arial", 11, "bold"), 
            bg="#25D366", 
            fg="white", 
            command=self.abrir_modal,
            height=2,
            cursor="hand2"
        )
        btn_gerar.pack(fill="x", padx=10, pady=10)

        self.encartes_cache = []
        self.carregar_encartes()

    def carregar_encartes(self):
        try:
            query = "SELECT id, titulo, data_inicio, data_fim, ativo FROM encarte ORDER BY id DESC"
            self.encartes_cache = self.db.executar_consulta(query)
            
            for item in self.tree.get_children():
                self.tree.delete(item)

            for row in self.encartes_cache:
                dt_ini = row["data_inicio"].strftime("%d/%m/%Y") if row.get("data_inicio") else ""
                dt_fim = row["data_fim"].strftime("%d/%m/%Y") if row.get("data_fim") else ""
                status = "Ativo" if row.get("ativo") else "Inativo"
                
                self.tree.insert("", "end", iid=row["id"], values=(row["id"], row["titulo"], dt_ini, dt_fim, status))
        except Exception as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao banco de dados PostgreSQL:\n{e}")

    def abrir_modal(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione um encarte na tabela para realizar a geração.")
            return

        encarte_id = int(selected[0])
        row = next((item for item in self.encartes_cache if item["id"] == encarte_id), None)
        if row:
            dt_ini = row["data_inicio"].strftime("%d/%m/%Y") if row.get("data_inicio") else ""
            dt_fim = row["data_fim"].strftime("%d/%m/%Y") if row.get("data_fim") else ""
            JanelaModalGerar(self.root, row["id"], row["titulo"], dt_ini, dt_fim, self.config, self.db)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppPrincipal(root)
    root.mainloop()
