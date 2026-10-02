# -*- coding: utf-8 -*-
import sys
import os
import json
import re
import traceback
import base64
import subprocess
import getpass
import customtkinter as ctk
from datetime import datetime, date
from tkinter import messagebox, Toplevel, filedialog, colorchooser
import psycopg2
from psycopg2.extras import RealDictCursor
from tkcalendar import DateEntry
from PIL import Image

if sys.platform.startswith("win"):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def resolver_caminho(caminho_raw):
    """Trata caminhos genéricos como C:\Downloads redirecionando para a pasta do usuário logado."""
    if not caminho_raw:
        return ""
    
    caminho_str = str(caminho_raw).strip()
    caminho_normalizado = caminho_str.replace('/', '\\').rstrip('\\')
    if caminho_normalizado.lower() == r"c:\downloads":
        try:
            usuario = getpass.getuser()
            caminho_str = os.path.join(os.environ.get("SystemDrive", "C:"), "\\Users", usuario, "Downloads")
        except Exception:
            caminho_str = os.path.expanduser("~/Downloads")

    caminho_expandido = os.path.expanduser(os.path.expandvars(caminho_str))
    return os.path.abspath(caminho_expandido)

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

def centralizar_no_topo_da_principal(modal, largura, altura):
    modal.update_idletasks()
    root = modal.winfo_toplevel()
    while root.master:
        root = root.master.winfo_toplevel()

    main_x = root.winfo_x()
    main_y = root.winfo_y()
    main_w = root.winfo_width()

    screen_h = modal.winfo_screenheight()
    altura_efetiva = min(altura, screen_h - 120)

    pos_x = main_x + max(0, (main_w - largura) // 2)
    pos_y = max(20, main_y + 30)

    modal.geometry(f"{largura}x{altura_efetiva}+{pos_x}+{pos_y}")
    modal.transient(root)
    modal.grab_set()
    modal.focus_force()

def obter_descricao_produto(codigo):
    """Consulta a descrição do produto na tabela esprod considerando o schema do banco."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        query = f"""
            SELECT 
                CASE 
                    WHEN COALESCE(fcomplemen, '') <> '' THEN fcomplemen 
                    ELSE fdescricao 
                END AS nome_exibicao
            FROM esprod 
            WHERE CAST(fco AS TEXT) = %s 
               OR CAST(fco AS TEXT) = %s 
               OR CAST(fco AS TEXT) = %s
            LIMIT 1
        """
        cod_str = str(codigo).strip()
        cod_clean = cod_str.lstrip('0')
        if not cod_clean:
            cod_clean = "0"
            
        cur.execute(query, (cod_str, cod_clean, cod_str.zfill(5)))
        res = cur.fetchone()
        conn.close()
        if res and res.get('nome_exibicao'):
            return res['nome_exibicao'].strip()
    except Exception:
        pass
    return ""

def eh_cor_valida(hex_code):
    """Verifica se uma string de cor é válida (ex: #FFFFFF ou #FFF)."""
    if not hex_code or not isinstance(hex_code, str):
        return False
    hex_code = hex_code.strip()
    return bool(re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", hex_code))

def escolher_cor_dialog(entry_widget, color_preview_box, parent=None):
    """Abre a paleta de cores (colorpicker), atualiza o campo com o código #HEX e a caixa de preview."""
    cor_inicial = entry_widget.get().strip()
    if not eh_cor_valida(cor_inicial):
        cor_inicial = "#FFFFFF"
    try:
        rgb, hex_code = colorchooser.askcolor(color=cor_inicial, parent=parent, title="Selecione a Cor")
        if hex_code:
            hex_upper = hex_code.upper()
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, hex_upper)
            color_preview_box.configure(fg_color=hex_upper)
    except Exception as e:
        messagebox.showerror("Erro Paleta de Cores", f"Não foi possível abrir a paleta de cores:\n{e}", parent=parent)

class ConfiguraDesignModal(ctk.CTkToplevel):
    """Modal de Configuração de Design/Cores específico para um Encarte."""
    def __init__(self, parent, dados_design_atuais, callback_confirmar):
        super().__init__(parent)
        self.callback_confirmar = callback_confirmar
        self.title("Configura Design do Encarte")

        ctk.CTkLabel(self, text="🌐 Configuração de Design & Cores Personalizadas", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        frame_form = ctk.CTkFrame(self)
        frame_form.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. Cor Título/Rodapé
        self.txt_cor_tit_rodape = self._criar_campo_cor(frame_form, "Cor Título/Rodapé:", 0, dados_design_atuais.get("ec_cor_tit_rodape", ""))
        # 2. Cor Grid Tarja
        self.txt_cor_grid_tarja = self._criar_campo_cor(frame_form, "Cor Grid Tarja:", 1, dados_design_atuais.get("ec_cor_grid_tarja", ""))
        # 3. Cor Grid Preço
        self.txt_cor_grid_preco = self._criar_campo_cor(frame_form, "Cor Grid Preço:", 2, dados_design_atuais.get("ec_cor_grid_preco", ""))
        # 4. Cor Fundo Destaque
        self.txt_cor_fundo_destaque = self._criar_campo_cor(frame_form, "Cor Fundo Destaque:", 3, dados_design_atuais.get("ec_cor_fundo_destaque", ""))
        # 5. Cor Fundo Demais
        self.txt_cor_fundo_demais = self._criar_campo_cor(frame_form, "Cor Fundo Demais:", 4, dados_design_atuais.get("ec_cor_fundo_demais", ""))
        # 6. Cor Fundo Rodapé
        self.txt_cor_fundo_rodape = self._criar_campo_cor(frame_form, "Cor Fundo Rodapé:", 5, dados_design_atuais.get("ec_cor_fundo_rodape", ""))

        # Tema do Encarte
        ctk.CTkLabel(frame_form, text="Tema do Cabeçalho:").grid(row=6, column=0, padx=10, pady=6, sticky="w")
        self.txt_encarte_tema = ctk.CTkEntry(frame_form, width=220, placeholder_text="Caminho da imagem do tema...")
        self.txt_encarte_tema.insert(0, dados_design_atuais.get("encarte_tema", ""))
        self.txt_encarte_tema.grid(row=6, column=1, padx=5, pady=6)
        
        btn_busca_tema = ctk.CTkButton(frame_form, text="📁 Buscar", width=80, command=self._buscar_tema)
        btn_busca_tema.grid(row=6, column=2, columnspan=2, padx=5, pady=6)

        frame_bottom_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_bottom_btn.pack(pady=15)

        btn_preview = ctk.CTkButton(frame_bottom_btn, text="👁️ Preview", fg_color="#37474F", hover_color="#263238", font=ctk.CTkFont(weight="bold"), height=36, width=120, command=self._abrir_preview)
        btn_preview.pack(side="left", padx=10)

        btn_confirmar = ctk.CTkButton(frame_bottom_btn, text="✔ Aplicar Design", fg_color="#0288D1", hover_color="#0277BD", font=ctk.CTkFont(weight="bold"), height=36, width=150, command=self._confirmar)
        btn_confirmar.pack(side="left", padx=10)

        centralizar_no_topo_da_principal(self, 580, 470)

    def _criar_campo_cor(self, parent, label_text, row, valor_inicial):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        txt_entry = ctk.CTkEntry(parent, width=220, placeholder_text="#HEX ex: #FF0000")
        txt_entry.insert(0, valor_inicial)
        txt_entry.grid(row=row, column=1, padx=5, pady=6)

        # Caixa visual para amostragem da cor selecionada ao lado
        cor_preview = valor_inicial if eh_cor_valida(valor_inicial) else "#FFFFFF"
        box_preview = ctk.CTkFrame(parent, width=28, height=28, fg_color=cor_preview, corner_radius=4, border_width=1, border_color="#555555")
        box_preview.grid(row=row, column=2, padx=(5, 2), pady=6)

        txt_entry.bind("<KeyRelease>", lambda e, entry=txt_entry, box=box_preview: self._atualizar_box_cor(entry, box))

        btn_palette = ctk.CTkButton(
            parent, text="🎨", width=36, fg_color="#37474F", hover_color="#263238",
            command=lambda entry=txt_entry, box=box_preview: escolher_cor_dialog(entry, box, self)
        )
        btn_palette.grid(row=row, column=3, padx=5, pady=6)
        return txt_entry

    def _atualizar_box_cor(self, entry, box):
        cor = entry.get().strip()
        if eh_cor_valida(cor):
            box.configure(fg_color=cor)

    def _buscar_tema(self):
        caminho = filedialog.askopenfilename(
            parent=self,
            title="Selecione o Tema do Encarte",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.txt_encarte_tema.delete(0, 'end')
            self.txt_encarte_tema.insert(0, caminho.replace("/", "\\"))

    def _abrir_preview(self):
        """Abre uma tela simulando o layout final do encarte com as cores selecionadas."""
        c_tit = self.txt_cor_tit_rodape.get().strip() or "#008040"
        c_tarja = self.txt_cor_grid_tarja.get().strip() or "#FAFEAF"
        c_preco = self.txt_cor_grid_preco.get().strip() or "#000000"
        c_destaque = self.txt_cor_fundo_destaque.get().strip() or "#FB9F68"
        c_demais = self.txt_cor_fundo_demais.get().strip() or "#BA4EE9"
        c_rodape = self.txt_cor_fundo_rodape.get().strip() or "#24A62E"

        top_prev = Toplevel(self)
        top_prev.title("Visualização Prévia (Preview) de Modelo de Cores")
        top_prev.geometry("450x580")
        top_prev.configure(bg="#1E1E1E")

        # Cabeçalho do Encarte
        f_head = ctk.CTkFrame(top_prev, fg_color=c_tit if eh_cor_valida(c_tit) else "#008040", height=60, corner_radius=0)
        f_head.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(f_head, text="CABEÇALHO DO ENCARTE", text_color="#FFFFFF", font=ctk.CTkFont(size=14, weight="bold")).pack(expand=True)

        # Fundo do Encarte / Área dos Produtos
        f_corpo = ctk.CTkFrame(top_prev, fg_color="#2A2A2A")
        f_corpo.pack(fill="both", expand=True, padx=10, pady=5)

        # Grid Destaque
        f_item_dest = ctk.CTkFrame(f_corpo, fg_color=c_destaque if eh_cor_valida(c_destaque) else "#FB9F68", corner_radius=6)
        f_item_dest.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_item_dest, text="⭐ ITEM DESTAQUE", text_color="#000000", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(4, 0))
        
        f_tarja_d = ctk.CTkFrame(f_item_dest, fg_color=c_tarja if eh_cor_valida(c_tarja) else "#FAFEAF", height=24)
        f_tarja_d.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(f_tarja_d, text="Descrição do Produto Destaque", text_color="#000000", font=ctk.CTkFont(size=10)).pack(expand=True)
        
        f_prc_d = ctk.CTkFrame(f_item_dest, fg_color=c_preco if eh_cor_valida(c_preco) else "#000000", height=30)
        f_prc_d.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(f_prc_d, text="R$ 19,90", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold")).pack(expand=True)

        # Grid Demais Itens
        f_item_demais = ctk.CTkFrame(f_corpo, fg_color=c_demais if eh_cor_valida(c_demais) else "#BA4EE9", corner_radius=6)
        f_item_demais.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(f_item_demais, text="ITEM COMUM", text_color="#000000", font=ctk.CTkFont(size=11, weight="bold")).pack(pady=(4, 0))

        f_tarja_m = ctk.CTkFrame(f_item_demais, fg_color=c_tarja if eh_cor_valida(c_tarja) else "#FAFEAF", height=24)
        f_tarja_m.pack(fill="x", padx=8, pady=4)
        ctk.CTkLabel(f_tarja_m, text="Descrição do Produto Demais", text_color="#000000", font=ctk.CTkFont(size=10)).pack(expand=True)

        f_prc_m = ctk.CTkFrame(f_item_demais, fg_color=c_preco if eh_cor_valida(c_preco) else "#000000", height=30)
        f_prc_m.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(f_prc_m, text="R$ 9,90", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold")).pack(expand=True)

        # Rodapé
        f_rodape = ctk.CTkFrame(top_prev, fg_color=c_rodape if eh_cor_valida(c_rodape) else "#24A62E", height=45, corner_radius=0)
        f_rodape.pack(fill="x", padx=10, pady=(5, 10))
        ctk.CTkLabel(f_rodape, text="RODAPÉ DO ENCARTE", text_color="#FFFFFF", font=ctk.CTkFont(size=12, weight="bold")).pack(expand=True)

    def _confirmar(self):
        dados_design = {
            "ec_cor_tit_rodape": self.txt_cor_tit_rodape.get().strip(),
            "ec_cor_grid_tarja": self.txt_cor_grid_tarja.get().strip(),
            "ec_cor_grid_preco": self.txt_cor_grid_preco.get().strip(),
            "ec_cor_fundo_destaque": self.txt_cor_fundo_destaque.get().strip(),
            "ec_cor_fundo_demais": self.txt_cor_fundo_demais.get().strip(),
            "ec_cor_fundo_rodape": self.txt_cor_fundo_rodape.get().strip(),
            "encarte_tema": self.txt_encarte_tema.get().strip()
        }
        self.callback_confirmar(dados_design)
        self.destroy()

class NovoContatoModal(ctk.CTkToplevel):
    def __init__(self, parent, callback_sucesso):
        super().__init__(parent)
        self.callback_sucesso = callback_sucesso
        self.contato_edicao_id = None
        self.title("Gerenciar Contatos")

        frame_form = ctk.CTkFrame(self)
        frame_form.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(frame_form, text="Nome:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.txt_nome = ctk.CTkEntry(frame_form, width=220)
        self.txt_nome.grid(row=0, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_form, text="Telefone:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.txt_fone = ctk.CTkEntry(frame_form, width=220, placeholder_text="(45) 99999-9999")
        self.txt_fone.grid(row=1, column=1, padx=5, pady=5)

        self.btn_salvar = ctk.CTkButton(frame_form, text="➕ Adicionar", fg_color="#2E7D32", hover_color="#1B5E20", command=self.salvar)
        self.btn_salvar.grid(row=2, column=0, columnspan=2, pady=10)

        self.btn_cancelar_edit = ctk.CTkButton(frame_form, text="Cancelar Edição", fg_color="#455A64", hover_color="#37474F", width=110, command=self.limpar_formulario)

        ctk.CTkLabel(self, text="Contatos Cadastrados:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
        
        self.frame_lista = ctk.CTkScrollableFrame(self, height=200)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.carregar_lista_contatos()
        centralizar_no_topo_da_principal(self, 460, 480)

    def carregar_lista_contatos(self):
        for child in self.frame_lista.winfo_children():
            child.destroy()

        schema = get_schema()
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT id, nome, telefone FROM {schema}.encarte_contatos ORDER BY nome")
            contatos = cur.fetchall()
            conn.close()

            if not contatos:
                ctk.CTkLabel(self.frame_lista, text="Nenhum contato encontrado.", text_color="gray").pack(pady=10)
                return

            for c in contatos:
                row = ctk.CTkFrame(self.frame_lista)
                row.pack(fill="x", pady=2, padx=2)

                lbl_texto = f"{c['nome']} - {c['telefone']}"
                ctk.CTkLabel(row, text=lbl_texto, anchor="w").pack(side="left", fill="x", expand=True, padx=8)

                btn_del = ctk.CTkButton(row, text="🗑️", width=32, height=28, fg_color="#C62828", hover_color="#B71C1C", command=lambda item=c: self.excluir(item))
                btn_del.pack(side="right", padx=2)

                btn_edit = ctk.CTkButton(row, text="✏️", width=32, height=28, fg_color="#1976D2", hover_color="#0D47A1", command=lambda item=c: self.preparar_edicao(item))
                btn_edit.pack(side="right", padx=2)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao listar contatos:\n{e}", parent=self)

    def preparar_edicao(self, contato):
        self.contato_edicao_id = contato['id']
        self.txt_nome.delete(0, 'end')
        self.txt_nome.insert(0, contato['nome'])
        self.txt_fone.delete(0, 'end')
        self.txt_fone.insert(0, contato['telefone'])

        self.btn_salvar.configure(text="🔄 Atualizar", fg_color="#1976D2", hover_color="#0D47A1")
        self.btn_cancelar_edit.grid(row=2, column=1, sticky="e", padx=5, pady=10)

    def limpar_formulario(self):
        self.contato_edicao_id = None
        self.txt_nome.delete(0, 'end')
        self.txt_fone.delete(0, 'end')
        self.btn_salvar.configure(text="➕ Adicionar", fg_color="#2E7D32", hover_color="#1B5E20")
        self.btn_cancelar_edit.grid_forget()

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

            if self.contato_edicao_id:
                cur.execute(f"UPDATE {schema}.encarte_contatos SET nome = %s, telefone = %s WHERE id = %s", (nome, fone, self.contato_edicao_id))
                conn.commit()
                messagebox.showinfo("Sucesso", "Contato atualizado com sucesso!", parent=self)
            else:
                cur.execute(f"SELECT id FROM {schema}.encarte_contatos WHERE nome ILIKE %s", (nome,))
                if cur.fetchone():
                    messagebox.showwarning("Atenção", f"O contato '{nome}' já existe!", parent=self)
                    conn.close()
                    return

                cur.execute(f"INSERT INTO {schema}.encarte_contatos (nome, telefone) VALUES (%s, %s)", (nome, fone))
                conn.commit()
                messagebox.showinfo("Sucesso", "Contato cadastrado com sucesso!", parent=self)

            conn.close()
            self.limpar_formulario()
            self.carregar_lista_contatos()
            self.callback_sucesso(nome)

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar contato:\n{e}", parent=self)

    def excluir(self, contato):
        confirma = messagebox.askyesno("Confirmar Exclusão", f"Deseja realmente excluir '{contato['nome']}'?", parent=self)
        if not confirma:
            return

        schema = get_schema()
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {schema}.encarte_contatos WHERE id = %s", (contato['id'],))
            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Contato excluído!", parent=self)
            self.limpar_formulario()
            self.carregar_lista_contatos()
            self.callback_sucesso(None)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir contato:\n{e}", parent=self)

class GerarEncarteModal(ctk.CTkToplevel):
    def __init__(self, parent, encarte_id, encarte_titulo):
        super().__init__(parent)
        self.encarte_id = encarte_id
        self.encarte_titulo = encarte_titulo

        self.title(f"Gerar Encarte #{encarte_id}")
        self.contatos_map = {}

        ctk.CTkLabel(self, text=f"⚡ Gerar Encarte: {encarte_titulo}", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 10))

        frame_ct = ctk.CTkFrame(self, fg_color="transparent")
        frame_ct.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_ct, text="Contato:").grid(row=0, column=0, sticky="w", padx=5)
        self.cmb_contato = ctk.CTkComboBox(frame_ct, width=240, values=[])
        self.cmb_contato.grid(row=0, column=1, padx=5)

        btn_novo_contato = ctk.CTkButton(frame_ct, text="👤 Novo / Gerenciar", width=120, fg_color="#1976D2", hover_color="#0D47A1", command=self.abrir_novo_contato)
        btn_novo_contato.grid(row=0, column=2, padx=5)

        frame_tb = ctk.CTkFrame(self, fg_color="transparent")
        frame_tb.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_tb, text="Tabela de Preço:").grid(row=0, column=0, sticky="w", padx=5)
        self.cmb_tabela = ctk.CTkComboBox(frame_tb, width=120, values=["1", "2", "3"])
        self.cmb_tabela.set("1")
        self.cmb_tabela.grid(row=0, column=1, sticky="w", padx=5)

        frame_sd = ctk.CTkFrame(self, fg_color="transparent")
        frame_sd.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_sd, text="Saldo:").grid(row=0, column=0, sticky="w", padx=5)
        self.var_saldo = ctk.StringVar(value="Positivos")
        rb_todos = ctk.CTkRadioButton(frame_sd, text="Todos", variable=self.var_saldo, value="Todos")
        rb_todos.grid(row=0, column=1, padx=15)
        rb_pos = ctk.CTkRadioButton(frame_sd, text="Positivos", variable=self.var_saldo, value="Positivos")
        rb_pos.grid(row=0, column=2, padx=15)

        btn_gerar = ctk.CTkButton(self, text="⚡ Confirmar e Gerar Encarte", fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(weight="bold"), height=38, command=self.processar_geracao)
        btn_gerar.pack(pady=20)

        self.carregar_contatos()
        centralizar_no_topo_da_principal(self, 520, 340)

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
        
        dir_encarte = resolver_caminho(params.get("dir_encarte", ""))
        dir_csv     = resolver_caminho(params.get("dir_csv", ""))
        dir_jpg     = resolver_caminho(params.get("dir_jpg", ""))

        if not dir_encarte or not os.path.exists(dir_encarte):
            messagebox.showerror("Erro de Configuração", f"Diretório Executáveis/Encarte (dir_encarte) inválido:\n{dir_encarte}", parent=self)
            return

        if not dir_csv or not os.path.exists(dir_csv):
            messagebox.showerror("Erro de Configuração", f"Diretório do CSV (dir_csv) inválido:\n{dir_csv}", parent=self)
            return

        if not dir_jpg or not os.path.exists(dir_jpg):
            try:
                os.makedirs(dir_jpg, exist_ok=True)
            except Exception:
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

            nome_contato_limpo = re.sub(r'[^\w\s-]', '', contato_sel).strip().replace(" ", "_")
            if not nome_contato_limpo:
                nome_contato_limpo = "geral"

            nome_arquivo_csv = f"{self.encarte_id}_encarte_{nome_contato_limpo}.csv"
            nome_arquivo_jpg = f"{self.encarte_id}_DADOS_CATALOGO.jpg"

            path_out_csv = os.path.normpath(os.path.join(dir_csv, nome_arquivo_csv))
            path_out_jpg = os.path.normpath(os.path.join(dir_jpg, nome_arquivo_jpg))

            with open(path_out_csv, "w", encoding="utf-8-sig", errors="replace", newline="") as f_csv:
                for row in linhas:
                    linha_texto = row.get('linha_csv')
                    if linha_texto is not None:
                        f_csv.write(f"{str(linha_texto).strip()}\r\n")

            exe_gerar = os.path.join(dir_encarte, "gerar_catalogo.exe")
            exe_viewer = os.path.join(dir_encarte, "visualizar_catalogo.exe")

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

        cfg = carregar_config()
        params_db = carregar_parametros_banco()

        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=15, pady=10)

        tab_banco = tabview.add("Conexão com Banco de Dados")
        tab_dirs = tabview.add("Diretórios e Design")

        ctk.CTkLabel(tab_banco, text="Host / IP:").grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self.txt_host = ctk.CTkEntry(tab_banco, width=320)
        self.txt_host.insert(0, cfg.get("host", ""))
        self.txt_host.grid(row=0, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Banco de Dados:").grid(row=1, column=0, padx=10, pady=6, sticky="w")
        self.txt_db = ctk.CTkEntry(tab_banco, width=320)
        self.txt_db.insert(0, cfg.get("database", ""))
        self.txt_db.grid(row=1, column=1, padx=10, pady=6)

        ctk.CTkLabel(tab_banco, text="Schema:").grid(row=2, column=0, padx=10, pady=6, sticky="w")
        self.txt_schema = ctk.CTkEntry(tab_banco, width=320, placeholder_text="ex: public ou dk")
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

        btn_criar_tabelas = ctk.CTkButton(
            tab_banco, text="🛠️ Criar Tabelas no Banco de Dados", 
            fg_color="#0288D1", hover_color="#0277BD", 
            font=ctk.CTkFont(weight="bold"), height=35,
            command=self.criar_tabelas_banco
        )
        btn_criar_tabelas.grid(row=6, column=0, columnspan=2, pady=20, padx=10, sticky="ew")

        # Rótulos no formulário de Diretórios e Design
        self.txt_dir_encarte = self._criar_campo_caminho(tab_dirs, "Diretório Executáveis:", 0, params_db.get("dir_encarte", ""), pasta=True)
        self.txt_dir_csv = self._criar_campo_caminho(tab_dirs, "Diretório CSV:", 1, params_db.get("dir_csv", ""), pasta=True)
        self.txt_dir_jpg = self._criar_campo_caminho(tab_dirs, "Diretório Salva JPG:", 2, params_db.get("dir_jpg", ""), pasta=True)
        
        self.txt_cabecalho_logo = self._criar_campo_caminho(tab_dirs, "Cabeçalho Logo:", 3, params_db.get("cabecalho_logo", ""), pasta=False)
        self.txt_rodape_logo_fone = self._criar_campo_caminho(tab_dirs, "Rodapé Logo Fone:", 4, params_db.get("rodape_logo_fone", ""), pasta=False)

        ctk.CTkLabel(tab_dirs, text="Rodapé Site:").grid(row=5, column=0, padx=10, pady=6, sticky="w")
        self.txt_cabecalho_site = ctk.CTkEntry(tab_dirs, width=220)
        self.txt_cabecalho_site.insert(0, params_db.get("cabecalho_site", ""))
        self.txt_cabecalho_site.grid(row=5, column=1, padx=5, pady=6)

        # Campos de cores com Botão de Seleção de Cores (Paleta) e Box de Amostra
        self.txt_cor_tit_rodape = self._criar_campo_cor(tab_dirs, "Cor Título/Rodapé:", 6, params_db.get("cor_tit_rodape", ""))
        self.txt_cor_grid_tarja = self._criar_campo_cor(tab_dirs, "Cor Grid Tarja:", 7, params_db.get("cor_grid_tarja", ""))
        self.txt_cor_grid_preco = self._criar_campo_cor(tab_dirs, "Cor Grid Preço:", 8, params_db.get("cor_grid_preco", ""))
        self.txt_cor_fundo_destaque = self._criar_campo_cor(tab_dirs, "Cor Fundo Destaque:", 9, params_db.get("cor_fundo_destaque", ""))
        self.txt_cor_fundo_demais = self._criar_campo_cor(tab_dirs, "Cor Fundo Demais:", 10, params_db.get("cor_fundo_demais", ""))
        self.txt_cor_fundo_rodape = self._criar_campo_cor(tab_dirs, "Cor Fundo Rodapé:", 11, params_db.get("cor_fundo_rodape", ""))

        self.txt_cabecalho_tema = self._criar_campo_caminho(tab_dirs, "Tema do Cabeçalho:", 12, params_db.get("cabecalho_tema", ""), pasta=False)

        btn_salvar = ctk.CTkButton(self, text="💾 Salvar Parâmetros", fg_color="#2E7D32", hover_color="#1B5E20", font=ctk.CTkFont(weight="bold"), height=38, command=self.salvar)
        btn_salvar.pack(pady=(0, 15))

        centralizar_no_topo_da_principal(self, 720, 660)

    def _criar_campo_cor(self, parent, label_text, row, valor_inicial):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        txt_entry = ctk.CTkEntry(parent, width=220, placeholder_text="#HEX ou Código Cor")
        txt_entry.insert(0, valor_inicial)
        txt_entry.grid(row=row, column=1, padx=5, pady=6)

        cor_preview = valor_inicial if eh_cor_valida(valor_inicial) else "#FFFFFF"
        box_preview = ctk.CTkFrame(parent, width=28, height=28, fg_color=cor_preview, corner_radius=4, border_width=1, border_color="#555555")
        box_preview.grid(row=row, column=2, padx=(5, 2), pady=6)

        txt_entry.bind("<KeyRelease>", lambda e, entry=txt_entry, box=box_preview: self._atualizar_box_cor(entry, box))

        btn_color = ctk.CTkButton(
            parent, text="🎨", width=36, fg_color="#37474F", hover_color="#263238",
            command=lambda entry=txt_entry, box=box_preview: escolher_cor_dialog(entry, box, self)
        )
        btn_color.grid(row=row, column=3, padx=5, pady=6)
        return txt_entry

    def _atualizar_box_cor(self, entry, box):
        cor = entry.get().strip()
        if eh_cor_valida(cor):
            box.configure(fg_color=cor)

    def _criar_campo_caminho(self, parent, label_text, row, valor_inicial, pasta=True):
        ctk.CTkLabel(parent, text=label_text).grid(row=row, column=0, padx=10, pady=6, sticky="w")
        txt_entry = ctk.CTkEntry(parent, width=220)
        txt_entry.insert(0, valor_inicial)
        txt_entry.grid(row=row, column=1, padx=5, pady=6)

        btn_procurar = ctk.CTkButton(
            parent, text="📁 Buscar", width=80, 
            command=lambda: self._selecionar_caminho(txt_entry, pasta)
        )
        btn_procurar.grid(row=row, column=2, columnspan=2, padx=5, pady=6)
        return txt_entry

    def _selecionar_caminho(self, entry_widget, pasta=True):
        if pasta:
            caminho = filedialog.askdirectory(parent=self, title="Selecione a Pasta")
        else:
            caminho = filedialog.askopenfilename(
                parent=self,
                title="Selecione o Arquivo", 
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
            encarte_tema character varying(255),
            ec_cor_tit_rodape character varying(50),
            ec_cor_grid_tarja character varying(50),
            ec_cor_grid_preco character varying(50),
            ec_cor_fundo_destaque character varying(50),
            ec_cor_fundo_demais character varying(50),
            ec_cor_fundo_rodape character varying(50),
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
            destaque character(1) DEFAULT 'N',
            item_foto character varying(255),
            CONSTRAINT encarte_item_pkey PRIMARY KEY (id)
        );

        CREATE TABLE IF NOT EXISTS {schema}.encarte_contatos
        (
            id SERIAL PRIMARY KEY,
            nome character varying(100) NOT NULL UNIQUE,
            telefone character varying(30) NOT NULL
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
            cor_fundo_destaque character varying(50),
            cor_fundo_demais character varying(50),
            cor_fundo_rodape character varying(50),
            cabecalho_tema character varying(255),
            CONSTRAINT encarte_parametros_pkey PRIMARY KEY (id)
        );

        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS encarte_tema character varying(255);
        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS ec_cor_tit_rodape character varying(50);
        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS ec_cor_grid_tarja character varying(50);
        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS ec_cor_grid_preco character varying(50);
        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS ec_cor_fundo_destaque character varying(50);
        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS ec_cor_fundo_demais character varying(50);
        ALTER TABLE {schema}.encarte ADD COLUMN IF NOT EXISTS ec_cor_fundo_rodape character varying(50);

        ALTER TABLE {schema}.encarte_item ADD COLUMN IF NOT EXISTS destaque character(1) DEFAULT 'N';
        ALTER TABLE {schema}.encarte_item ADD COLUMN IF NOT EXISTS item_foto character varying(255);

        ALTER TABLE {schema}.encarte_parametros ADD COLUMN IF NOT EXISTS cor_fundo_destaque character varying(50);
        ALTER TABLE {schema}.encarte_parametros ADD COLUMN IF NOT EXISTS cor_fundo_demais character varying(50);
        ALTER TABLE {schema}.encarte_parametros ADD COLUMN IF NOT EXISTS cor_fundo_rodape character varying(50);
        ALTER TABLE {schema}.encarte_parametros ADD COLUMN IF NOT EXISTS cabecalho_tema character varying(255);
        """
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(sql_script)
            conn.commit()
            conn.close()
            messagebox.showinfo("Sucesso", f"Tabelas e colunas de cores criadas/verificadas com sucesso no schema '{schema}'!", parent=self)
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
            "cor_grid_preco": self.txt_cor_grid_preco.get().strip(),
            "cor_fundo_destaque": self.txt_cor_fundo_destaque.get().strip(),
            "cor_fundo_demais": self.txt_cor_fundo_demais.get().strip(),
            "cor_fundo_rodape": self.txt_cor_fundo_rodape.get().strip(),
            "cabecalho_tema": self.txt_cabecalho_tema.get().strip()
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

        frame_busca = ctk.CTkFrame(self)
        frame_busca.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(frame_busca, text="Buscar Por:").pack(side="left", padx=5)
        self.txt_busca = ctk.CTkEntry(frame_busca, width=380, placeholder_text="Digite o Código, Descrição ou Complemento...")
        self.txt_busca.pack(side="left", padx=5)
        self.txt_busca.bind("<Return>", lambda e: self.pesquisar())

        btn_buscar = ctk.CTkButton(frame_busca, text="🔍 Pesquisar", width=110, fg_color="#1976D2", hover_color="#0D47A1", command=self.pesquisar)
        btn_buscar.pack(side="left", padx=5)

        self.frame_resultados = ctk.CTkScrollableFrame(self)
        self.frame_resultados.pack(fill="both", expand=True, padx=15, pady=5)

        centralizar_no_topo_da_principal(self, 780, 500)

    def pesquisar(self):
        termo = self.txt_busca.get().strip()
        for w in self.frame_resultados.winfo_children():
            w.destroy()

        if not termo:
            return
            
        try:
            conn = get_connection()
            cur = conn.cursor()

            query = f"""
                SELECT 
                    fco, 
                    CASE 
                        WHEN COALESCE(fcomplemen, '') <> '' THEN fcomplemen 
                        ELSE fdescricao 
                    END AS nome_exibicao
                FROM esprod 
                WHERE COALESCE(CAST(fco AS TEXT), '') || ' ' || COALESCE(fdescricao, '') || ' ' || COALESCE(fcomplemen, '') ILIKE %s
                AND fRegAtivo='S'
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

                ctk.CTkLabel(row, text=f"[{cod_str}]", width=80, font=ctk.CTkFont(weight="bold"), text_color=("#2E7D32", "#A5D6A7")).pack(side="left", padx=5)
                ctk.CTkLabel(row, text=nome_prod, anchor="w").pack(side="left", fill="x", expand=True, padx=5)

                btn_sel = ctk.CTkButton(row, text="✔ Selecionar", width=100, fg_color="#2E7D32", hover_color="#1B5E20", command=lambda c=cod_str: self.selecionar(c))
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
        self.index_edicao = None

        # Dicionário interno com o design personalizado do encarte
        self.design_encarte = {
            "ec_cor_tit_rodape": "",
            "ec_cor_grid_tarja": "",
            "ec_cor_grid_preco": "",
            "ec_cor_fundo_destaque": "",
            "ec_cor_fundo_demais": "",
            "ec_cor_fundo_rodape": "",
            "encarte_tema": ""
        }

        self.title("Alteração de Encarte" if encarte_id else "Novo Encarte")

        self.criar_widgets()
        if self.encarte_id:
            self.carregar_dados()

        centralizar_no_topo_da_principal(self, 980, 560)

    def criar_widgets(self):
        frame_top_bar = ctk.CTkFrame(self, fg_color="transparent")
        frame_top_bar.pack(fill="x", padx=15, pady=(8, 2))

        lbl_titulo = ctk.CTkLabel(frame_top_bar, text="📋 Manutenção do Encarte", font=ctk.CTkFont(size=18, weight="bold"))
        lbl_titulo.pack(side="left")

        btn_voltar = ctk.CTkButton(frame_top_bar, text="⬅️ Voltar", width=90, height=30, fg_color="#455A64", hover_color="#37474F", command=self.destroy)
        btn_voltar.pack(side="right")

        frame_head = ctk.CTkFrame(self)
        frame_head.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_head, text="Título:").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        self.txt_titulo = ctk.CTkEntry(frame_head, width=380, placeholder_text="Ex: ENCARTE FARMAX")
        self.txt_titulo.grid(row=0, column=1, columnspan=2, padx=8, pady=6, sticky="w")

        # Botão CONFIGURA DESIGN
        btn_config_design = ctk.CTkButton(
            frame_head, text="🎨 CONFIGURA DESIGN", fg_color="#00A2E8", hover_color="#0086C0", 
            text_color="white", font=ctk.CTkFont(weight="bold"), height=32,
            command=self.abrir_configura_design
        )
        btn_config_design.grid(row=0, column=3, columnspan=2, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Início:").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        self.txt_dt_ini = ctk.CTkEntry(frame_head, width=120, placeholder_text="29/08/2026")
        self.txt_dt_ini.grid(row=1, column=1, padx=(8, 2), pady=6, sticky="w")
        btn_cal_ini = ctk.CTkButton(frame_head, text="📅", width=36, height=28, fg_color="#37474F", hover_color="#263238", command=lambda: self.abrir_calendario(self.txt_dt_ini))
        btn_cal_ini.grid(row=1, column=1, padx=(132, 0), pady=6, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Fim:").grid(row=1, column=2, padx=8, pady=6, sticky="w")
        self.txt_dt_fim = ctk.CTkEntry(frame_head, width=120, placeholder_text="05/09/2026")
        self.txt_dt_fim.grid(row=1, column=3, padx=(8, 2), pady=6, sticky="w")
        btn_cal_fim = ctk.CTkButton(frame_head, text="📅", width=36, height=28, fg_color="#37474F", hover_color="#263238", command=lambda: self.abrir_calendario(self.txt_dt_fim))
        btn_cal_fim.grid(row=1, column=3, padx=(132, 0), pady=6, sticky="w")

        frame_prod = ctk.CTkFrame(self)
        frame_prod.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_prod, text="Cód. Prod:").grid(row=0, column=0, padx=4, pady=6, sticky="w")
        self.txt_p_cod = ctk.CTkEntry(frame_prod, width=75, placeholder_text="00001")
        self.txt_p_cod.grid(row=0, column=1, padx=(4, 2), pady=6)
        self.txt_p_cod.bind("<FocusOut>", self.formatar_codigo_evento)

        btn_lupa = ctk.CTkButton(frame_prod, text="🔍", width=36, height=28, fg_color="#1976D2", hover_color="#0D47A1", command=self.abrir_lupa)
        btn_lupa.grid(row=0, column=2, padx=(0, 6), pady=6)

        ctk.CTkLabel(frame_prod, text="A partir de:").grid(row=0, column=3, padx=2, pady=6, sticky="w")
        self.txt_p_qtde = ctk.CTkEntry(frame_prod, width=55, placeholder_text="1.00")
        self.txt_p_qtde.insert(0, "1")
        self.txt_p_qtde.grid(row=0, column=4, padx=(2, 2), pady=6)

        ctk.CTkLabel(frame_prod, text="Preço (R$):").grid(row=0, column=5, padx=2, pady=6, sticky="w")
        self.txt_p_preco = ctk.CTkEntry(frame_prod, width=80, placeholder_text="0.00")
        self.txt_p_preco.grid(row=0, column=6, padx=4, pady=6)

        self.chk_destaque = ctk.CTkCheckBox(frame_prod, text="Destaque")
        self.chk_destaque.grid(row=0, column=7, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(frame_prod, text="Foto:").grid(row=0, column=8, padx=2, pady=6, sticky="w")
        self.txt_p_foto = ctk.CTkEntry(frame_prod, width=120, placeholder_text="Caminho foto...")
        self.txt_p_foto.grid(row=0, column=9, padx=2, pady=6)
        btn_foto = ctk.CTkButton(frame_prod, text="🖼", width=36, height=28, command=self.buscar_foto_item)
        btn_foto.grid(row=0, column=10, padx=(2, 6), pady=6)

        self.btn_add = ctk.CTkButton(frame_prod, text="➕ Adicionar", width=100, height=30, fg_color="#2E7D32", hover_color="#1B5E20", command=self.adicionar_item)
        self.btn_add.grid(row=0, column=11, padx=6, pady=6)

        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

        frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        frame_botoes.pack(fill="x", padx=15, pady=(2, 4))

        btn_salvar = ctk.CTkButton(frame_botoes, text="💾 Salvar no Banco", font=ctk.CTkFont(weight="bold"), fg_color="#2E7D32", hover_color="#1B5E20", height=32, width=150, command=self.salvar_banco)
        btn_salvar.pack(side="right", padx=5)

        btn_cancelar = ctk.CTkButton(frame_botoes, text="❌ Cancelar", fg_color="#C62828", hover_color="#B71C1C", height=32, width=110, command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

    def abrir_configura_design(self):
        ConfiguraDesignModal(
            self, 
            dados_design_atuais=self.design_encarte, 
            callback_confirmar=self.atualizar_design_local
        )

    def atualizar_design_local(self, novos_dados):
        self.design_encarte.update(novos_dados)

    def buscar_foto_item(self):
        caminho = filedialog.askopenfilename(
            parent=self,
            title="Selecione a Foto do Produto",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp"), ("Todos os Arquivos", "*.*")]
        )
        if caminho:
            self.txt_p_foto.delete(0, 'end')
            self.txt_p_foto.insert(0, caminho.replace("/", "\\"))

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
        is_destaque = 'S' if self.chk_destaque.get() == 1 else 'N'
        foto_path = self.txt_p_foto.get().strip()

        if not cod_raw:
            messagebox.showwarning("Atenção", "Informe o Código do Produto.", parent=self)
            self.txt_p_cod.focus()
            return

        cod_formatted = self.formatar_codigo_5_digitos(cod_raw)

        # Regra de Destaques Únicos por CÓDIGO
        codigos_destaque_atuais = set()
        for idx, item in enumerate(self.itens):
            if idx == self.index_edicao:
                continue
            if item.get('destaque') == 'S':
                codigos_destaque_atuais.add(item['codigo_prod'])

        # Se for marcar destaque e esse código ainda não era um dos destaques
        if is_destaque == 'S' and cod_formatted not in codigos_destaque_atuais:
            if len(codigos_destaque_atuais) >= 3:
                messagebox.showwarning("Limite Atingido", "Você pode marcar no máximo 3 CÓDIGOS DE PRODUTOS diferentes como destaque por encarte.", parent=self)
                return

        try:
            qtde_val = float(qtde_raw) if qtde_raw else 1.0
            if qtde_val <= 0:
                qtde_val = 1.0
        except ValueError:
            messagebox.showerror("Erro", "Quantidade inválida.", parent=self)
            self.txt_p_qtde.focus()
            return

        for idx, item in enumerate(self.itens):
            if idx != self.index_edicao and item['codigo_prod'] == cod_formatted and item['qtde_oferta'] == qtde_val:
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

        desc_prod = obter_descricao_produto(cod_formatted)

        novo_item = {
            'codigo_prod': cod_formatted, 
            'descricao_prod': desc_prod,
            'qtde_oferta': qtde_val, 
            'preco_oferta': preco_val,
            'destaque': is_destaque,
            'item_foto': foto_path
        }

        if self.index_edicao is not None:
            self.itens[self.index_edicao] = novo_item
            self.index_edicao = None
            self.btn_add.configure(text="➕ Adicionar", fg_color="#2E7D32", hover_color="#1B5E20")
        else:
            self.itens.insert(0, novo_item)

        # Atualiza para que todos os itens do mesmo código sincronizem o status de Destaque
        for item in self.itens:
            if item['codigo_prod'] == cod_formatted:
                item['destaque'] = is_destaque

        self.atualizar_grid()

        self.txt_p_cod.delete(0, 'end')
        self.txt_p_qtde.delete(0, 'end')
        self.txt_p_qtde.insert(0, "1")
        self.txt_p_preco.delete(0, 'end')
        self.txt_p_foto.delete(0, 'end')
        self.chk_destaque.deselect()
        self.txt_p_cod.focus()

    def editar_item(self, index):
        self.index_edicao = index
        item = self.itens[index]

        self.txt_p_cod.delete(0, 'end')
        self.txt_p_cod.insert(0, item['codigo_prod'])
        
        self.txt_p_qtde.delete(0, 'end')
        self.txt_p_qtde.insert(0, f"{item['qtde_oferta']:.2f}".rstrip('0').rstrip('.'))

        self.txt_p_preco.delete(0, 'end')
        self.txt_p_preco.insert(0, f"{item['preco_oferta']:.2f}")

        self.txt_p_foto.delete(0, 'end')
        if item.get('item_foto'):
            self.txt_p_foto.insert(0, item['item_foto'])

        if item.get('destaque') == 'S':
            self.chk_destaque.select()
        else:
            self.chk_destaque.deselect()

        self.btn_add.configure(text="🔄 Atualizar", fg_color="#1976D2", hover_color="#0D47A1")

    def atualizar_grid(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        total_itens = len(self.itens)
        for idx, item in enumerate(self.itens):
            f_row = ctk.CTkFrame(self.frame_lista)
            f_row.pack(fill="x", pady=2, padx=5)

            num_exibicao = total_itens - idx
            ctk.CTkLabel(f_row, text=f"#{num_exibicao}", width=30).pack(side="left", padx=(5, 2))
            
            desc_original = item.get('descricao_prod') or 'SEM DESCRIÇÃO'
            if len(desc_original) > 36:
                desc_texto = desc_original[:33] + "..."
            else:
                desc_texto = desc_original
                
            lbl_desc = ctk.CTkLabel(
                f_row, 
                text=desc_texto, 
                anchor="w", 
                width=270,
                font=ctk.CTkFont(size=12, weight="bold"), 
                text_color=("#333333", "#4CAF50" if item.get('descricao_prod') else "#888888")
            )
            lbl_desc.pack(side="left", padx=(2, 5))

            lbl_cod = ctk.CTkLabel(f_row, text=f"[Cód: {item['codigo_prod']}]", anchor="w", width=85, font=ctk.CTkFont(weight="bold"), text_color="gray")
            lbl_cod.pack(side="left", padx=2)
            
            txt_destaque = "⭐ [DESTAQUE]" if item.get('destaque') == 'S' else ""
            ctk.CTkLabel(f_row, text=txt_destaque, width=105, anchor="w", font=ctk.CTkFont(weight="bold"), text_color=("#FF8F00", "#FFD54F")).pack(side="left", padx=2)

            qtde_str = f"{item['qtde_oferta']:.2f}".rstrip('0').rstrip('.')
            ctk.CTkLabel(f_row, text=f"A partir de {qtde_str} un.", width=110, anchor="w", text_color=("#000000", "#81D4FA")).pack(side="left", padx=2)

            cor_preco = ("#2E7D32", "#A5D6A7") if item['preco_oferta'] > 0 else ("#E65100", "#FFB74D")
            lbl_preco = f"R$ {item['preco_oferta']:.2f}" if item['preco_oferta'] > 0 else "Preço Atual"
            ctk.CTkLabel(f_row, text=lbl_preco, width=95, text_color=cor_preco, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=2)

            foto_text = f"🖼️ {os.path.basename(item['item_foto'])}" if item.get('item_foto') else "Sem foto ind."
            ctk.CTkLabel(f_row, text=foto_text, width=100, text_color="gray", anchor="w").pack(side="left", padx=2)

            btn_del = ctk.CTkButton(f_row, text="🗑️", width=32, height=28, fg_color="#C62828", hover_color="#B71C1C", command=lambda i=idx: self.remover_item(i))
            btn_del.pack(side="right", padx=2)

            btn_edit = ctk.CTkButton(f_row, text="✏️️", width=32, height=28, fg_color="#1976D2", hover_color="#0D47A1", command=lambda i=idx: self.editar_item(i))
            btn_edit.pack(side="right", padx=2)

    def remover_item(self, index):
        if self.index_edicao == index:
            self.index_edicao = None
            self.btn_add.configure(text="➕ Adicionar", fg_color="#2E7D32", hover_color="#1B5E20")
            self.txt_p_cod.delete(0, 'end')
            self.txt_p_qtde.delete(0, 'end')
            self.txt_p_qtde.insert(0, "1")
            self.txt_p_preco.delete(0, 'end')
            self.txt_p_foto.delete(0, 'end')
            self.chk_destaque.deselect()
        elif self.index_edicao is not None and index < self.index_edicao:
            self.index_edicao -= 1

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
                
                # Carrega o design e as cores específicas do encarte
                self.design_encarte = {
                    "ec_cor_tit_rodape": enc.get('ec_cor_tit_rodape', '') or '',
                    "ec_cor_grid_tarja": enc.get('ec_cor_grid_tarja', '') or '',
                    "ec_cor_grid_preco": enc.get('ec_cor_grid_preco', '') or '',
                    "ec_cor_fundo_destaque": enc.get('ec_cor_fundo_destaque', '') or '',
                    "ec_cor_fundo_demais": enc.get('ec_cor_fundo_demais', '') or '',
                    "ec_cor_fundo_rodape": enc.get('ec_cor_fundo_rodape', '') or '',
                    "encarte_tema": enc.get('encarte_tema', '') or ''
                }

                cur.execute(f"SELECT codigo_prod, qtde_oferta, preco_oferta, destaque, item_foto FROM {schema}.encarte_item WHERE encarte_id = %s ORDER BY ordem DESC, id DESC", (self.encarte_id,))
                itens_bd = cur.fetchall()
                
                self.itens = []
                for i in itens_bd:
                    cod_fmt = self.formatar_codigo_5_digitos(str(i['codigo_prod']))
                    desc = obter_descricao_produto(cod_fmt)
                    self.itens.append({
                        'codigo_prod': cod_fmt, 
                        'descricao_prod': desc,
                        'qtde_oferta': float(i.get('qtde_oferta', 1.0)),
                        'preco_oferta': float(i['preco_oferta']),
                        'destaque': i.get('destaque', 'N') or 'N',
                        'item_foto': i.get('item_foto', '') or ''
                    })
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

        d = self.design_encarte

        conn = None
        try:
            conn = get_connection()
            cur = conn.cursor()

            if self.encarte_id:
                cur.execute(f"SELECT id FROM {schema}.encarte WHERE id = %s", (self.encarte_id,))
                existe = cur.fetchone()
                
                if not existe:
                    cur.execute(f"""
                        INSERT INTO {schema}.encarte (
                            titulo, data_inicio, data_fim, encarte_tema,
                            ec_cor_tit_rodape, ec_cor_grid_tarja, ec_cor_grid_preco,
                            ec_cor_fundo_destaque, ec_cor_fundo_demais, ec_cor_fundo_rodape
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                    """, (
                        titulo, dt_ini_iso, dt_fim_iso, d.get("encarte_tema", ""),
                        d.get("ec_cor_tit_rodape", ""), d.get("ec_cor_grid_tarja", ""), d.get("ec_cor_grid_preco", ""),
                        d.get("ec_cor_fundo_destaque", ""), d.get("ec_cor_fundo_demais", ""), d.get("ec_cor_fundo_rodape", "")
                    ))
                    enc_id = cur.fetchone()['id']
                else:
                    cur.execute(f"""
                        UPDATE {schema}.encarte 
                        SET titulo=%s, data_inicio=%s, data_fim=%s, encarte_tema=%s,
                            ec_cor_tit_rodape=%s, ec_cor_grid_tarja=%s, ec_cor_grid_preco=%s,
                            ec_cor_fundo_destaque=%s, ec_cor_fundo_demais=%s, ec_cor_fundo_rodape=%s
                        WHERE id=%s
                    """, (
                        titulo, dt_ini_iso, dt_fim_iso, d.get("encarte_tema", ""),
                        d.get("ec_cor_tit_rodape", ""), d.get("ec_cor_grid_tarja", ""), d.get("ec_cor_grid_preco", ""),
                        d.get("ec_cor_fundo_destaque", ""), d.get("ec_cor_fundo_demais", ""), d.get("ec_cor_fundo_rodape", ""),
                        self.encarte_id
                    ))
                    
                    cur.execute(f"DELETE FROM {schema}.encarte_item WHERE encarte_id=%s", (self.encarte_id,))
                    enc_id = self.encarte_id
            else:
                cur.execute(f"""
                    INSERT INTO {schema}.encarte (
                        titulo, data_inicio, data_fim, encarte_tema,
                        ec_cor_tit_rodape, ec_cor_grid_tarja, ec_cor_grid_preco,
                        ec_cor_fundo_destaque, ec_cor_fundo_demais, ec_cor_fundo_rodape
                    ) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                """, (
                    titulo, dt_ini_iso, dt_fim_iso, d.get("encarte_tema", ""),
                    d.get("ec_cor_tit_rodape", ""), d.get("ec_cor_grid_tarja", ""), d.get("ec_cor_grid_preco", ""),
                    d.get("ec_cor_fundo_destaque", ""), d.get("ec_cor_fundo_demais", ""), d.get("ec_cor_fundo_rodape", "")
                ))
                enc_id = cur.fetchone()['id']

            for idx, item in enumerate(reversed(self.itens)):
                cur.execute(f"""
                    INSERT INTO {schema}.encarte_item (encarte_id, codigo_prod, qtde_oferta, preco_oferta, ordem, destaque, item_foto) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (enc_id, item['codigo_prod'], item['qtde_oferta'], item['preco_oferta'], idx, item.get('destaque', 'N'), item.get('item_foto', '')))

            conn.commit()
            conn.close()

            messagebox.showinfo("Sucesso", "Encarte e configurações de design gravados com sucesso!", parent=self)
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
        
        self.geometry("1100x640+50+30")
        self.minsize(1000, 580)

        frame_topo = ctk.CTkFrame(self)
        frame_topo.pack(fill="x", padx=15, pady=(10, 5))

        self.lbl_logo = ctk.CTkLabel(frame_topo, text="")
        self.lbl_logo.pack(side="left", padx=15, pady=8)

        btn_sair = ctk.CTkButton(frame_topo, text="🚪 Sair", fg_color="#C62828", hover_color="#B71C1C", width=90, height=32, command=self.destroy)
        btn_sair.pack(side="right", padx=6, pady=8)

        btn_tema = ctk.CTkButton(frame_topo, text="🌓 Tema", fg_color="#455A64", hover_color="#37474F", width=90, height=32, command=self.alternar_tema)
        btn_tema.pack(side="right", padx=6, pady=8)

        btn_params = ctk.CTkButton(frame_topo, text="⚙️ Parâmetros", fg_color="#455A64", hover_color="#37474F", width=120, height=32, command=self.abrir_parametros)
        btn_params.pack(side="right", padx=6, pady=8)

        btn_novo = ctk.CTkButton(frame_topo, text="➕ Novo Encarte", fg_color="#2E7D32", hover_color="#1B5E20", width=130, height=32, command=self.novo_encarte)
        btn_novo.pack(side="right", padx=6, pady=8)

        frame_pesquisa = ctk.CTkFrame(self)
        frame_pesquisa.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(frame_pesquisa, text="🔍 Buscar:").pack(side="left", padx=12, pady=8)
        self.txt_filtro_titulo = ctk.CTkEntry(frame_pesquisa, placeholder_text="Digite o título do encarte para filtrar...")
        self.txt_filtro_titulo.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.txt_filtro_titulo.bind("<KeyRelease>", lambda e: self.carregar_encartes())

        self.frame_lista = ctk.CTkScrollableFrame(self)
        self.frame_lista.pack(fill="both", expand=True, padx=15, pady=5)

        self.atualizar_logo_topo()
        self.carregar_encartes()

    def atualizar_logo_topo(self):
        modo_atual = ctk.get_appearance_mode()
        
        if modo_atual.lower() == "dark":
            nome_img = "logo-ze2.jpg"
        else:
            nome_img = "logo-ze.jpg"

        caminho_img = os.path.join("encarte_imagens", nome_img)

        if os.path.exists(caminho_img):
            try:
                pil_img = Image.open(caminho_img)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(180, 45))
                self.lbl_logo.configure(image=ctk_img, text="")
            except Exception:
                self.lbl_logo.configure(image="", text="📋 Gestão de Encartes", font=ctk.CTkFont(size=18, weight="bold"))
        else:
            self.lbl_logo.configure(image="", text="📋 Gestão de Encartes", font=ctk.CTkFont(size=18, weight="bold"))

    def alternar_tema(self):
        modo_atual = ctk.get_appearance_mode()
        if modo_atual == "Dark":
            ctk.set_appearance_mode("Light")
        else:
            ctk.set_appearance_mode("Dark")
        self.atualizar_logo_topo()

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
                row.pack(fill="x", pady=5, padx=5)

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
                
                if vencido:
                    cor_status = "#EF5350"
                else:
                    cor_status = ("#000000", "#FFFFFF")

                lbl_info = f"#{enc['id']} - {enc['titulo']}\nPeríodo: {dt_ini_str} a {dt_fim_str}"
                ctk.CTkLabel(row, text=lbl_info, anchor="w", font=ctk.CTkFont(size=13, weight="bold"), text_color=cor_status, justify="left").pack(side="left", padx=15, pady=10, fill="x", expand=True)

                frame_acoes = ctk.CTkFrame(row, fg_color="transparent")
                frame_acoes.pack(side="right", padx=10, pady=5)

                if not vencido:
                    btn_gerar = ctk.CTkButton(
                        frame_acoes, text="⚡ Gerar Encarte", width=125, height=32, fg_color="#2E7D32", hover_color="#1B5E20",
                        command=lambda e_id=enc['id'], e_tit=enc['titulo']: self.gerar_encarte(e_id, e_tit)
                    )
                    btn_gerar.pack(side="left", padx=4)

                btn_editar = ctk.CTkButton(
                    frame_acoes, text="✏️ Editar", width=95, height=32, fg_color="#1976D2", hover_color="#0D47A1",
                    command=lambda e_id=enc['id']: self.editar_encarte(e_id)
                )
                btn_editar.pack(side="left", padx=4)

                btn_excluir = ctk.CTkButton(
                    frame_acoes, text="🗑️ Excluir", width=95, height=32, fg_color="#C62828", hover_color="#B71C1C",
                    command=lambda e_id=enc['id'], e_tit=enc['titulo']: self.excluir_encarte(e_id, e_tit)
                )
                btn_excluir.pack(side="right", padx=4)

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
