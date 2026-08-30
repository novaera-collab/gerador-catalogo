import sys
import os
import json
import traceback
from datetime import datetime, date
from tkinter import messagebox, Toplevel

# Ocultar o console/terminal do Windows no momento da execução
if sys.platform.startswith("win"):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# 1. CAPTURA DE ERRO FATAL NA INICIALIZAÇÃO
def mostrar_erro_fatal(exc_type, exc_value, exc_traceback):
    erro_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    messagebox.showerror("Erro Fatal na Inicialização", f"Ocorreu um erro ao abrir o app:\n\n{erro_msg}")

sys.excepthook = mostrar_erro_fatal

# 2. IMPORTAÇÕES PRINCIPAIS
import psycopg2
from psycopg2.extras import RealDictCursor
import customtkinter as ctk
from tkcalendar import DateEntry

CONFIG_FILE = "config_banco.json"

def carregar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "host": "localhost",
        "database": "seu_banco",
        "user": "postgres",
        "password": "sua_senha",
        "port": "5432"
    }

def salvar_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

# ==============================================================================
# CONEXÃO COM O BANCO DE DADOS POSTGRESQL
# ==============================================================================
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

# ==============================================================================
# JANELA DE PARÂMETROS DA CONEXÃO E DIRETÓRIOS
# ==============================================================================
class ParametrosWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Parâmetros do Sistema")
        self.geometry("560x520")
        self.grab_set()

        cfg = carregar_config()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=15, pady=10)

        tab_banco = tabview.add("Conexão com Banco de Dados")
        tab_dirs = tabview.add("Diretórios e Arquivos")

        # --- ABA 1: BANCO DE DADOS ---
        ctk.CTkLabel(tab_banco, text="Host / IP:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.txt_host = ctk.CTkEntry(tab_banco, width=280)
        self.txt_host.insert(0, cfg.get("host", ""))
        self.txt_host.grid(row=0, column=1, padx=10, pady=8)

        ctk.CTkLabel(tab_banco, text="Banco de Dados:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.txt_db = ctk.CTkEntry(tab_banco, width=280)
        self.txt_db.insert(0, cfg.get("database", ""))
        self.txt_db.grid(row=1, column=1, padx=10, pady=8)

        ctk.CTkLabel(tab_banco, text="Usuário:").grid(row=2, column=0, padx=10, pady=8, sticky="w")
        self.txt_user = ctk.CTkEntry(tab_banco, width=280)
        self.txt_user.insert(0, cfg.get("user", ""))
        self.txt_user.grid(row=2, column=1, padx=10, pady=8)

        ctk.CTkLabel(tab_banco, text="Senha:").grid(row=3, column=0, padx=10, pady=8, sticky="w")
        self.txt_pass = ctk.CTkEntry(tab_banco, width=280, show="*")
        self.txt_pass.insert(0, cfg.get("password", ""))
        self.txt_pass.grid(row=3, column=1, padx=10, pady=8)

        ctk.CTkLabel(tab_banco, text="Porta:").grid(row=4, column=0, padx=10, pady=8, sticky="w")
        self.txt_port = ctk.CTkEntry(tab_banco, width=280)
        self.txt_port.insert(0, cfg.get("port", "5432"))
        self.txt_port.grid(row=4, column=1, padx=10, pady=8)

        # --- ABA 2: DIRETÓRIOS E LOGOS ---
        self.txt_dir_encarte = self._criar_campo_caminho(tab_dirs, "Diretório Encarte:", 0, cfg.get("dir_encarte", ""), pasta=True)
        self.txt_dir_csv = self._criar_campo_caminho(tab_dirs, "Diretório CSV:", 1, cfg.get("dir_csv", ""), pasta=True)
        self.txt_dir_jpg = self._criar_campo_caminho(tab_dirs, "Diretório JPG:", 2, cfg.get("dir_jpg", ""), pasta=True)
        self.txt_logo = self._criar_campo_caminho(tab_dirs, "Logo Principal:", 3, cfg.get("path_logo", ""), pasta=False)
        self.txt_logo_whats = self._criar_campo_caminho(tab_dirs, "Logo WhatsApp:", 4, cfg.get("path_logo_whats", ""), pasta=False)

        btn_salvar = ctk.CTkButton(self, text="Salvar Tudo", fg_color="#1B5E20", font=ctk.CTkFont(weight="bold"), height=35, command=self.salvar)
        btn_salvar.pack(pady=(0, 15))

    def _criar_campo_caminho(self, parent, label_text, row, valor_inicial, pasta=True):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        txt_entry = ctk.CTkEntry(parent, width=260)
        txt_entry.insert(0, valor_inicial)
        txt_entry.grid(row=row, column=1, padx=5, pady=6)

        btn_procurar = ctk.CTkButton(
            parent, text="...", width=35, 
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
                filetypes=[("Arquivos de Imagem", "*.png *.jpg *.jpeg"), ("Todos os Arquivos", "*.*")]
            )
        
        if caminho:
            # Padroniza as barras no formato Windows (ex: F:\UNICO)
            caminho_formatado = caminho.replace("/", "\\")
            entry_widget.delete(0, "end")
            entry_widget.insert(0, caminho_formatado)
            self.lift()

    def salvar(self):
        cfg = {
            "host": self.txt_host.get().strip(),
            "database": self.txt_db.get().strip(),
            "user": self.txt_user.get().strip(),
            "password": self.txt_pass.get().strip(),
            "port": self.txt_port.get().strip(),
            "dir_encarte": self.txt_dir_encarte.get().strip(),
            "dir_csv": self.txt_dir_csv.get().strip(),
            "dir_jpg": self.txt_dir_jpg.get().strip(),
            "path_logo": self.txt_logo.get().strip(),
            "path_logo_whats": self.txt_logo_whats.get().strip()
        }
        salvar_config(cfg)
        messagebox.showinfo("Sucesso", "Todos os parâmetros foram salvos!")
        self.destroy()

# ==============================================================================
# JANELA MODAL DE PESQUISA DE PRODUTO (LUPA EM ESPROD CONCATENADA)
# ==============================================================================
class PesquisaProdutoModal(ctk.CTkToplevel):
    def __init__(self, parent, callback_selecao):
        super().__init__(parent)
        self.parent = parent
        self.callback_selecao = callback_selecao

        self.title("?? Pesquisa de Produtos (ESPROD)")
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
            messagebox.showerror("Erro na Pesquisa", f"Erro ao consultar esprod:\n{e}")

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
        self.geometry("800x650")
        self.grab_set()

        self.criar_widgets()
        if self.encarte_id:
            self.carregar_dados()

    def criar_widgets(self):
        # Cabeçalho com botão Voltar
        frame_top_bar = ctk.CTkFrame(self, fg_color="transparent")
        frame_top_bar.pack(fill="x", padx=20, pady=(10, 0))

        lbl_titulo = ctk.CTkLabel(frame_top_bar, text="Manutenção do Encarte", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.pack(side="left")

        btn_voltar = ctk.CTkButton(frame_top_bar, text="?? Voltar", width=90, fg_color="#455A64", command=self.destroy)
        btn_voltar.pack(side="right")

        frame_head = ctk.CTkFrame(self)
        frame_head.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_head, text="Título:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.txt_titulo = ctk.CTkEntry(frame_head, width=380, placeholder_text="Ex: ENCARTE FARMAX")
        self.txt_titulo.grid(row=0, column=1, columnspan=3, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Início:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.txt_dt_ini = ctk.CTkEntry(frame_head, width=120, placeholder_text="29/08/2026")
        self.txt_dt_ini.grid(row=1, column=1, padx=(10, 2), pady=8, sticky="w")
        btn_cal_ini = ctk.CTkButton(frame_head, text="??", width=35, command=lambda: self.abrir_calendario(self.txt_dt_ini))
        btn_cal_ini.grid(row=1, column=1, padx=(135, 0), pady=8, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Fim:").grid(row=1, column=2, padx=10, pady=8, sticky="w")
        self.txt_dt_fim = ctk.CTkEntry(frame_head, width=120, placeholder_text="05/09/2026")
        self.txt_dt_fim.grid(row=1, column=3, padx=(10, 2), pady=8, sticky="w")
        btn_cal_fim = ctk.CTkButton(frame_head, text="??", width=35, command=lambda: self.abrir_calendario(self.txt_dt_fim))
        btn_cal_fim.grid(row=1, column=3, padx=(135, 0), pady=8, sticky="w")

        frame_prod = ctk.CTkFrame(self)
        frame_prod.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_prod, text="Cód. Prod:").grid(row=0, column=0, padx=5, pady=5)
        
        self.txt_p_cod = ctk.CTkEntry(frame_prod, width=90, placeholder_text="00001")
        self.txt_p_cod.grid(row=0, column=1, padx=(5, 2), pady=5)
        self.txt_p_cod.bind("<FocusOut>", self.formatar_codigo_evento)

        btn_lupa = ctk.CTkButton(frame_prod, text="??", width=35, fg_color="#1976D2", command=self.abrir_lupa)
        btn_lupa.grid(row=0, column=2, padx=(0, 10), pady=5)

        ctk.CTkLabel(frame_prod, text="Preço Oferta (R$):").grid(row=0, column=3, padx=5, pady=5)
        self.txt_p_preco = ctk.CTkEntry(frame_prod, width=110, placeholder_text="0.00")
        self.txt_p_preco.grid(row=0, column=4, padx=5, pady=5)

        btn_add = ctk.CTkButton(frame_prod, text="+ Adicionar", width=100, fg_color="#2E7D32", command=self.adicionar_item)
        btn_add.grid(row=0, column=5, padx=15, pady=5)

        self.frame_lista = ctk.CTkScrollableFrame(self, height=220)
        self.frame_lista.pack(fill="both", expand=True, padx=20, pady=5)

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=20, pady=10)

        btn_salvar = ctk.CTkButton(frame_botoes, text="?? Salvar no Banco", font=ctk.CTkFont(weight="bold"), fg_color="#1B5E20", height=40, command=self.salvar_banco)
        btn_salvar.pack(side="right", padx=5)

        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#C62828", height=40, command=self.destroy)
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
        preco_raw = self.txt_p_preco.get().strip().replace(',', '.')

        if not cod_raw:
            messagebox.showwarning("Atenção", "Informe o Código do Produto.")
            return

        cod_formatted = self.formatar_codigo_5_digitos(cod_raw)

        if not preco_raw:
            preco_val = 0.0
        else:
            try:
                preco_val = float(preco_raw)
            except ValueError:
                messagebox.showerror("Erro", "Valor de preço inválido.")
                return

        self.itens.append({'codigo_prod': cod_formatted, 'preco_oferta': preco_val})
        self.atualizar_grid()

        self.txt_p_cod.delete(0, 'end')
        self.txt_p_preco.delete(0, 'end')

    def editar_item(self, index):
        item = self.itens.pop(index)
        self.txt_p_cod.delete(0, 'end')
        self.txt_p_cod.insert(0, item['codigo_prod'])
        
        self.txt_p_preco.delete(0, 'end')
        self.txt_p_preco.insert(0, f"{item['preco_oferta']:.2f}")
        
        self.atualizar_grid()

    def atualizar_grid(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        for idx, item in enumerate(self.itens):
            f_row = ctk.CTkFrame(self.frame_lista)
            f_row.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(f_row, text=f"#{idx+1}", width=50).pack(side="left", padx=5)
            ctk.CTkLabel(f_row, text=f"Código: {item['codigo_prod']}", width=180, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            
            lbl_preco = f"R$ {item['preco_oferta']:.2f}" if item['preco_oferta'] > 0 else "Preço Atual (R$ 0.00)"
            ctk.CTkLabel(f_row, text=lbl_preco, width=180, text_color="#A5D6A7" if item['preco_oferta'] > 0 else "#FFB74D", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

            btn_del = ctk.CTkButton(f_row, text="X", width=30, fg_color="#D32F2F", command=lambda i=idx: self.remover_item(i))
            btn_del.pack(side="right", padx=3)

            btn_edit = ctk.CTkButton(f_row, text="?? Editar", width=70, fg_color="#1976D2", command=lambda i=idx: self.editar_item(i))
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
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM encarte WHERE id = %s", (self.encarte_id,))
            enc = cur.fetchone()

            if enc:
                self.txt_titulo.insert(0, enc['titulo'])
                self.txt_dt_ini.insert(0, self.converter_data_para_br(enc['data_inicio']))
                self.txt_dt_fim.insert(0, self.converter_data_para_br(enc['data_fim']))

                cur.execute("SELECT codigo_prod, preco_oferta FROM encarte_item WHERE encarte_id = %s ORDER BY ordem, id", (self.encarte_id,))
                itens_bd = cur.fetchall()
                self.itens = [{'codigo_prod': self.formatar_codigo_5_digitos(str(i['codigo_prod'])), 'preco_oferta': float(i['preco_oferta'])} for i in itens_bd]
                self.atualizar_grid()

            conn.close()
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", str(e))

    def salvar_banco(self):
        titulo = self.txt_titulo.get().strip()
        dt_ini_raw = self.txt_dt_ini.get().strip()
        dt_fim_raw = self.txt_dt_fim.get().strip()

        if not titulo or not dt_ini_raw or not dt_fim_raw or not self.itens:
            messagebox.showwarning("Atenção", "Preencha o cabeçalho e insira ao menos 1 produto.")
            return

        try:
            dt_ini_iso = self.parse_data_para_iso(dt_ini_raw)
            dt_fim_iso = self.parse_data_para_iso(dt_fim_raw)
        except Exception:
            messagebox.showerror("Data Inválida", "Informe a data no padrão brasileiro DD/MM/AAAA (ex: 29/08/2026).")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.encarte_id:
                cur.execute("""
                    UPDATE encarte 
                    SET titulo=%s, data_inicio=%s, data_fim=%s 
                    WHERE id=%s
                """, (titulo, dt_ini_iso, dt_fim_iso, self.encarte_id))
                
                cur.execute("DELETE FROM encarte_item WHERE encarte_id=%s", (self.encarte_id,))
                enc_id = self.encarte_id
            else:
                cur.execute("""
                    INSERT INTO encarte (titulo, data_inicio, data_fim) 
                    VALUES (%s, %s, %s) RETURNING id
                """, (titulo, dt_ini_iso, dt_fim_iso))
                enc_id = cur.fetchone()['id']

            for idx, item in enumerate(self.itens):
                cur.execute("""
                    INSERT INTO encarte_item (encarte_id, codigo_prod, preco_oferta, ordem) 
                    VALUES (%s, %s, %s, %s)
                """, (enc_id, item['codigo_prod'], item['preco_oferta'], idx))

            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Encarte gravado com sucesso!")
            if self.callback_refresh:
                self.callback_refresh()
            self.destroy()

        except Exception as e:
            messagebox.showerror("Erro ao Salvar", str(e))

# ==============================================================================
# TELA PRINCIPAL DO APLICATIVO
# ==============================================================================
class AppPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gestão de Encartes - v2.0 (Atualizado)")
        self.geometry("750x520")

        # Cabeçalho Superior
        frame_topo = ctk.CTkFrame(self)
        frame_topo.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(frame_topo, text="Encartes Cadastrados", font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)
        
        btn_sair = ctk.CTkButton(frame_topo, text="? Sair", fg_color="#C62828", width=80, command=self.destroy)
        btn_sair.pack(side="right", padx=5, pady=5)

        btn_params = ctk.CTkButton(frame_topo, text="?? Parâmetros", fg_color="#455A64", width=110, command=self.abrir_parametros)
        btn_params.pack(side="right", padx=5, pady=5)

        btn_novo = ctk.CTkButton(frame_topo, text="? Novo Encarte", fg_color="#2E7D32", width=120, command=self.novo_encarte)
        btn_novo.pack(side="right", padx=5, pady=5)

        # BARRA DE PESQUISA POR TÍTULO
        frame_pesquisa = ctk.CTkFrame(self)
        frame_pesquisa.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_pesquisa, text="?? Buscar Encarte:").pack(side="left", padx=10)
        self.txt_filtro_titulo = ctk.CTkEntry(frame_pesquisa, placeholder_text="Digite o título para filtrar...")
        self.txt_filtro_titulo.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        self.txt_filtro_titulo.bind("<KeyRelease>", lambda e: self.carregar_encartes())

        # Lista de Encartes
        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

        self.carregar_encartes()

    def abrir_parametros(self):
        ParametrosWindow(self)

    def carregar_encartes(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        filtro = self.txt_filtro_titulo.get().strip() if hasattr(self, 'txt_filtro_titulo') else ""

        try:
            conn = get_connection()
            cur = conn.cursor()

            if filtro:
                query = "SELECT id, titulo, data_inicio, data_fim FROM encarte WHERE titulo ILIKE %s ORDER BY id DESC"
                cur.execute(query, (f"%{filtro}%",))
            else:
                query = "SELECT id, titulo, data_inicio, data_fim FROM encarte ORDER BY id DESC"
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

                btn_editar = ctk.CTkButton(row, text="?? Editar", width=70, command=lambda e_id=enc['id']: self.editar_encarte(e_id))
                btn_editar.pack(side="right", padx=5, pady=5)

        except Exception as e:
            ctk.CTkLabel(self.frame_lista, text=f"Erro ao consultar o banco de dados:\n{e}", text_color="#EF5350").pack(pady=20)

    def novo_encarte(self):
        FormEncarteWindow(self, callback_refresh=self.carregar_encartes)

    def editar_encarte(self, encarte_id):
        FormEncarteWindow(self, encarte_id=encarte_id, callback_refresh=self.carregar_encartes)

# ==============================================================================
# INICIALIZAÇÃO DA APLICAÇÃO
# ==============================================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = AppPrincipal()
    app.mainloop()
