import os
import configparser
import psycopg2
from psycopg2.extras import RealDictCursor
import customtkinter as ctk
from tkinter import messagebox

# Configurações do Tema Visual Moderno
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

CONFIG_FILE = "config.ini"

# ==============================================================================
# GESTOR DE CONFIGURAÇÃO (CONFIG.INI) E BANCO DE DADOS
# ==============================================================================
def carregar_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        config["POSTGRESQL"] = {
            "host": "localhost",
            "port": "5432",
            "database": "seu_banco",
            "user": "postgres",
            "password": "sua_senha"
        }
        with open(CONFIG_FILE, "w") as f:
            config.write(f)
    else:
        config.read(CONFIG_FILE)
    return config["POSTGRESQL"]

def salvar_config(host, port, dbname, user, password):
    config = configparser.ConfigParser()
    config["POSTGRESQL"] = {
        "host": host,
        "port": port,
        "database": dbname,
        "user": user,
        "password": password
    }
    with open(CONFIG_FILE, "w") as f:
        config.write(f)

def get_connection():
    cfg = carregar_config()
    return psycopg2.connect(
        host=cfg["host"],
        port=cfg["port"],
        database=cfg["database"],
        user=cfg["user"],
        password=cfg["password"],
        cursor_factory=RealDictCursor
    )

# ==============================================================================
# JANELA DE CONFIGURAÇÃO DO BANCO DE DADOS
# ==============================================================================
class ConfigDBWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configurar Conexão PostgreSQL")
        self.geometry("400x420")
        self.grab_set()

        cfg = carregar_config()

        ctk.CTkLabel(self, text="Parâmetros do PostgreSQL", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        self.txt_host = self.criar_campo("Host / IP:", cfg.get("host", "localhost"))
        self.txt_port = self.criar_campo("Porta:", cfg.get("port", "5432"))
        self.txt_db = self.criar_campo("Banco de Dados:", cfg.get("database", ""))
        self.txt_user = self.criar_campo("Usuário:", cfg.get("user", "postgres"))
        self.txt_pass = self.criar_campo("Senha:", cfg.get("password", ""), show="*")

        btn_salvar = ctk.CTkButton(self, text="💾 Salvar Configurações", fg_color="#1B5E20", command=self.salvar)
        btn_salvar.pack(pady=20)

    def criar_campo(self, label, valor, show=None):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame, text=label, width=120, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(frame, show=show)
        entry.insert(0, valor)
        entry.pack(side="right", fill="x", expand=True)
        return entry

    def salvar(self):
        salvar_config(
            self.txt_host.get().strip(),
            self.txt_port.get().strip(),
            self.txt_db.get().strip(),
            self.txt_user.get().strip(),
            self.txt_pass.get().strip()
        )
        messagebox.showinfo("Sucesso", "Configurações salvas!")
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
        self.geometry("750x600")
        self.grab_set()

        self.criar_widgets()
        if self.encarte_id:
            self.carregar_dados()

    def criar_widgets(self):
        # Cabeçalho
        lbl_titulo = ctk.CTkLabel(self, text="Manutenção do Encarte", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.pack(pady=10, padx=20, anchor="w")

        frame_head = ctk.CTkFrame(self)
        frame_head.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_head, text="Título:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.txt_titulo = ctk.CTkEntry(frame_head, width=320, placeholder_text="Ex: ENCARTE FARMAX")
        self.txt_titulo.grid(row=0, column=1, columnspan=3, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Início (AAAA-MM-DD):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.txt_dt_ini = ctk.CTkEntry(frame_head, width=140)
        self.txt_dt_ini.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Fim (AAAA-MM-DD):").grid(row=1, column=2, padx=10, pady=5, sticky="w")
        self.txt_dt_fim = ctk.CTkEntry(frame_head, width=140)
        self.txt_dt_fim.grid(row=1, column=3, padx=10, pady=5, sticky="w")

        # Entrada de Itens
        frame_prod = ctk.CTkFrame(self)
        frame_prod.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_prod, text="Cód. Prod:").grid(row=0, column=0, padx=5, pady=5)
        self.txt_p_cod = ctk.CTkEntry(frame_prod, width=120)
        self.txt_p_cod.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_prod, text="Preço Oferta (R$):").grid(row=0, column=2, padx=5, pady=5)
        self.txt_p_preco = ctk.CTkEntry(frame_prod, width=120)
        self.txt_p_preco.grid(row=0, column=3, padx=5, pady=5)

        btn_add = ctk.CTkButton(frame_prod, text="+ Adicionar", width=100, fg_color="#2E7D32", command=self.adicionar_item)
        btn_add.grid(row=0, column=4, padx=15, pady=5)

        # Grade de Itens Adicionados
        self.frame_lista = ctk.CTkScrollableFrame(self, height=220)
        self.frame_lista.pack(fill="both", expand=True, padx=20, pady=5)

        # Botões de Ação
        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=20, pady=10)

        btn_salvar = ctk.CTkButton(frame_botoes, text="💾 Salvar no Banco", font=ctk.CTkFont(weight="bold"), fg_color="#1B5E20", height=40, command=self.salvar_banco)
        btn_salvar.pack(side="right", padx=5)

        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#C62828", height=40, command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

    def adicionar_item(self):
        cod = self.txt_p_cod.get().strip()
        preco = self.txt_p_preco.get().strip().replace(',', '.')

        if not cod or not preco:
            messagebox.showwarning("Atenção", "Informe o Código do Produto e o Preço.")
            return

        try:
            preco_val = float(preco)
        except ValueError:
            messagebox.showerror("Erro", "Valor de preço inválido.")
            return

        self.itens.append({'codigo_prod': cod, 'preco_oferta': preco_val})
        self.atualizar_grid()

        self.txt_p_cod.delete(0, 'end')
        self.txt_p_preco.delete(0, 'end')

    def atualizar_grid(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        for idx, item in enumerate(self.itens):
            f_row = ctk.CTkFrame(self.frame_lista)
            f_row.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(f_row, text=f"Ordem #{idx+1}", width=80).pack(side="left", padx=5)
            ctk.CTkLabel(f_row, text=f"Código: {item['codigo_prod']}", width=200, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(f_row, text=f"Preço: R$ {item['preco_oferta']:.2f}", width=150, text_color="#A5D6A7", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

            btn_del = ctk.CTkButton(f_row, text="X", width=30, fg_color="#D32F2F", command=lambda i=idx: self.remover_item(i))
            btn_del.pack(side="right", padx=5)

    def remover_item(self, index):
        self.itens.pop(index)
        self.atualizar_grid()

    def carregar_dados(self):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM public.encarte WHERE id = %s", (self.encarte_id,))
            enc = cur.fetchone()

            if enc:
                self.txt_titulo.insert(0, enc['titulo'])
                self.txt_dt_ini.insert(0, str(enc['data_inicio']))
                self.txt_dt_fim.insert(0, str(enc['data_fim']))

                cur.execute("SELECT codigo_prod, preco_oferta FROM public.encarte_item WHERE encarte_id = %s ORDER BY ordem, id", (self.encarte_id,))
                self.itens = cur.fetchall()
                self.atualizar_grid()

            conn.close()
        except Exception as e:
            messagebox.showerror("Erro ao Carregar", str(e))

    def salvar_banco(self):
        titulo = self.txt_titulo.get().strip()
        dt_ini = self.txt_dt_ini.get().strip()
        dt_fim = self.txt_dt_fim.get().strip()

        if not titulo or not dt_ini or not dt_fim or not self.itens:
            messagebox.showwarning("Atenção", "Preencha o cabeçalho e insira ao menos 1 produto.")
            return

        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.encarte_id:
                cur.execute("""
                    UPDATE public.encarte 
                    SET titulo=%s, data_inicio=%s, data_fim=%s 
                    WHERE id=%s
                """, (titulo, dt_ini, dt_fim, self.encarte_id))
                
                cur.execute("DELETE FROM public.encarte_item WHERE encarte_id=%s", (self.encarte_id,))
                enc_id = self.encarte_id
            else:
                cur.execute("""
                    INSERT INTO public.encarte (titulo, data_inicio, data_fim) 
                    VALUES (%s, %s, %s) RETURNING id
                """, (titulo, dt_ini, dt_fim))
                enc_id = cur.fetchone()['id']

            for idx, item in enumerate(self.itens):
                cur.execute("""
                    INSERT INTO public.encarte_item (encarte_id, codigo_prod, preco_oferta, ordem) 
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
# TELA PRINCIPAL (LISTAGEM E MANUTENÇÃO)
# ==============================================================================
class AppMain(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Encartes - PostgreSQL")
        self.geometry("900x600")

        self.criar_layout()
        self.carregar_encartes()

    def criar_layout(self):
        # Header Topo
        frame_top = ctk.CTkFrame(self, height=65, fg_color="#1B5E20")
        frame_top.pack(fill="x", side="top")

        lbl_app_title = ctk.CTkLabel(frame_top, text="📋 Gestão de Encartes", font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
        lbl_app_title.pack(side="left", padx=20, pady=15)

        btn_config = ctk.CTkButton(frame_top, text="⚙️ Parâmetros DB", fg_color="#333333", width=120, command=self.abrir_config)
        btn_config.pack(side="right", padx=10, pady=15)

        btn_novo = ctk.CTkButton(frame_top, text="+ Novo Encarte", font=ctk.CTkFont(weight="bold"), fg_color="#2E7D32", command=self.abrir_novo)
        btn_novo.pack(side="right", padx=10, pady=15)

        # Scroll / Lista
        self.scroll_cards = ctk.CTkScrollableFrame(self)
        self.scroll_cards.pack(fill="both", expand=True, padx=20, pady=20)

    def carregar_encartes(self):
        for w in self.scroll_cards.winfo_children():
            w.destroy()

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM public.encarte ORDER BY id DESC")
            encartes = cur.fetchall()
            conn.close()

            if not encartes:
                ctk.CTkLabel(self.scroll_cards, text="Nenhum encarte cadastrado no banco.", font=ctk.CTkFont(size=16)).pack(pady=40)
                return

            for enc in encartes:
                self.criar_card(enc)

        except Exception as e:
            ctk.CTkLabel(self.scroll_cards, text=f"Erro de Conexão com o PostgreSQL:\n{e}\n\nClique em '⚙️ Parâmetros DB' no topo.", text_color="#FF5252").pack(pady=40)

    def criar_card(self, enc):
        card = ctk.CTkFrame(self.scroll_cards)
        card.pack(fill="x", pady=5, padx=5)

        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", padx=15, pady=10)

        ctk.CTkLabel(info_frame, text=f"SEQ: #{enc['id']:06d} - {enc['titulo']}", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w")
        
        d_ini = enc['data_inicio'].strftime('%d/%m/%Y') if hasattr(enc['data_inicio'], 'strftime') else str(enc['data_inicio'])
        d_fim = enc['data_fim'].strftime('%d/%m/%Y') if hasattr(enc['data_fim'], 'strftime') else str(enc['data_fim'])
        ctk.CTkLabel(info_frame, text=f"Período: {d_ini} a {d_fim} | Status: {enc['status']}", text_color="gray").pack(anchor="w")

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=15, pady=10)

        btn_edit = ctk.CTkButton(btn_frame, text="✏️ Alterar", width=80, fg_color="#1976D2", command=lambda e_id=enc['id']: self.abrir_editar(e_id))
        btn_edit.pack(side="left", padx=5)

        btn_del = ctk.CTkButton(btn_frame, text="🗑️ Excluir", width=80, fg_color="#D32F2F", command=lambda e_id=enc['id']: self.excluir(e_id))
        btn_del.pack(side="left", padx=5)

    def abrir_config(self):
        ConfigDBWindow(self)

    def abrir_novo(self):
        FormEncarteWindow(self, callback_refresh=self.carregar_encartes)

    def abrir_editar(self, encarte_id):
        FormEncarteWindow(self, encarte_id=encarte_id, callback_refresh=self.carregar_encartes)

    def excluir(self, encarte_id):
        if messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente excluir o Encarte #{encarte_id}?"):
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("DELETE FROM public.encarte WHERE id = %s", (encarte_id,))
                conn.commit()
                conn.close()
                self.carregar_encartes()
            except Exception as e:
                messagebox.showerror("Erro ao Excluir", str(e))

if __name__ == "__main__":
    app = AppMain()
    app.mainloop()
