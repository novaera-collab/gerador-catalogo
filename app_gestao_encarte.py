import sys
import os
import traceback
from datetime import datetime
from tkinter import messagebox, Toplevel
import psycopg2
from psycopg2.extras import RealDictCursor
import customtkinter as ctk
from tkcalendar import DateEntry
# ==============================================================================
# CONEXÃO COM O BANCO DE DADOS POSTGRESQL (COLE AQUI!)
# ==============================================================================
def get_connection():
    return psycopg2.connect(
        host="seu_host_aqui",       # Substitua com os dados reais do seu banco
        database="seu_banco_aqui",
        user="seu_usuario_aqui",
        password="sua_senha_aqui",
        port="5432",
        cursor_factory=RealDictCursor
    )

from datetime import datetime
from tkinter import messagebox, Toplevel

# 1. CAPTURA DE ERRO FATAL (Deve ficar antes de criar as janelas do Tkinter)
def mostrar_erro_fatal(exc_type, exc_value, exc_traceback):
    erro_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    messagebox.showerror("Erro Fatal na Inicialização", f"Ocorreu um erro ao abrir o app:\n\n{erro_msg}")

sys.excepthook = mostrar_erro_fatal

# 2. DEMAIS IMPORTAÇÕES
import psycopg2
from psycopg2.extras import RealDictCursor
import customtkinter as ctk
from tkcalendar import DateEntry

# ==============================================================================
# JANELA MODAL DE PESQUISA DE PRODUTO (LUPA EM ESPROD)
# ==============================================================================
class PesquisaProdutoModal(ctk.CTkToplevel):
    def __init__(self, parent, callback_selecao):
        super().__init__(parent)
        self.parent = parent
        self.callback_selecao = callback_selecao

        self.title("🔍 Pesquisa de Produtos (ESPROD)")
        self.geometry("700x480")
        self.grab_set()

        # Barra de Pesquisa
        frame_busca = ctk.CTkFrame(self)
        frame_busca.pack(fill="x", padx=15, pady=10)

        ctk.CTkLabel(frame_busca, text="Buscar Por:").pack(side="left", padx=5)
        self.txt_busca = ctk.CTkEntry(frame_busca, width=320, placeholder_text="Digite o Código, Nome ou Descrição...")
        self.txt_busca.pack(side="left", padx=5)
        self.txt_busca.bind("<Return>", lambda e: self.pesquisar())

        btn_buscar = ctk.CTkButton(frame_busca, text="Pesquisar", width=100, command=self.pesquisar)
        btn_buscar.pack(side="left", padx=5)

        # Grade/Lista de Resultados
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
                SELECT fco, fde, fdescricao 
                FROM public.esprod 
                WHERE CAST(fco AS TEXT) ILIKE %s 
                   OR fde ILIKE %s 
                   OR fdescricao ILIKE %s
                LIMIT 50
            """
            like_term = f"%{termo}%"
            cur.execute(query, (like_term, like_term, like_term))
            produtos = cur.fetchall()
            conn.close()

            if not produtos:
                ctk.CTkLabel(self.frame_resultados, text="Nenhum produto encontrado.", text_color="gray").pack(pady=20)
                return

            for prod in produtos:
                cod_str = str(prod['fco']).zfill(5)
                nome_prod = prod['fde'] or prod['fdescricao'] or ''

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
        lbl_titulo = ctk.CTkLabel(self, text="Manutenção do Encarte", font=ctk.CTkFont(size=20, weight="bold"))
        lbl_titulo.pack(pady=10, padx=20, anchor="w")

        frame_head = ctk.CTkFrame(self)
        frame_head.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(frame_head, text="Título:").grid(row=0, column=0, padx=10, pady=8, sticky="w")
        self.txt_titulo = ctk.CTkEntry(frame_head, width=380, placeholder_text="Ex: ENCARTE FARMAX")
        self.txt_titulo.grid(row=0, column=1, columnspan=3, padx=10, pady=8, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Início:").grid(row=1, column=0, padx=10, pady=8, sticky="w")
        self.txt_dt_ini = ctk.CTkEntry(frame_head, width=120, placeholder_text="29/08/2026")
        self.txt_dt_ini.grid(row=1, column=1, padx=(10, 2), pady=8, sticky="w")
        btn_cal_ini = ctk.CTkButton(frame_head, text="📅", width=35, command=lambda: self.abrir_calendario(self.txt_dt_ini))
        btn_cal_ini.grid(row=1, column=1, padx=(135, 0), pady=8, sticky="w")

        ctk.CTkLabel(frame_head, text="Data Fim:").grid(row=1, column=2, padx=10, pady=8, sticky="w")
        self.txt_dt_fim = ctk.CTkEntry(frame_head, width=120, placeholder_text="05/09/2026")
        self.txt_dt_fim.grid(row=1, column=3, padx=(10, 2), pady=8, sticky="w")
        btn_cal_fim = ctk.CTkButton(frame_head, text="📅", width=35, command=lambda: self.abrir_calendario(self.txt_dt_fim))
        btn_cal_fim.grid(row=1, column=3, padx=(135, 0), pady=8, sticky="w")

        frame_prod = ctk.CTkFrame(self)
        frame_prod.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(frame_prod, text="Cód. Prod:").grid(row=0, column=0, padx=5, pady=5)
        
        self.txt_p_cod = ctk.CTkEntry(frame_prod, width=90, placeholder_text="00001")
        self.txt_p_cod.grid(row=0, column=1, padx=(5, 2), pady=5)
        self.txt_p_cod.bind("<FocusOut>", self.formatar_codigo_evento)

        btn_lupa = ctk.CTkButton(frame_prod, text="🔍", width=35, fg_color="#1976D2", command=self.abrir_lupa)
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

        btn_salvar = ctk.CTkButton(frame_botoes, text="💾 Salvar no Banco", font=ctk.CTkFont(weight="bold"), fg_color="#1B5E20", height=40, command=self.salvar_banco)
        btn_salvar.pack(side="right", padx=5)

        btn_cancelar = ctk.CTkButton(frame_botoes, text="Cancelar", fg_color="#C62828", height=40, command=self.destroy)
        btn_cancelar.pack(side="right", padx=5)

    def formatar_codigo_5_digitos(self, valor):
        valor_limpo = valor.strip()
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
        preco = self.txt_p_preco.get().strip().replace(',', '.')

        if not cod_raw or not preco:
            messagebox.showwarning("Atenção", "Informe o Código do Produto e o Preço.")
            return

        cod_formatted = self.formatar_codigo_5_digitos(cod_raw)

        try:
            preco_val = float(preco)
        except ValueError:
            messagebox.showerror("Erro", "Valor de preço inválido.")
            return

        self.itens.append({'codigo_prod': cod_formatted, 'preco_oferta': preco_val})
        self.atualizar_grid()

        self.txt_p_cod.delete(0, 'end')
        self.txt_p_preco.delete(0, 'end')

    def atualizar_grid(self):
        for w in self.frame_lista.winfo_children():
            w.destroy()

        for idx, item in enumerate(self.itens):
            f_row = ctk.CTkFrame(self.frame_lista)
            f_row.pack(fill="x", pady=2, padx=5)

            ctk.CTkLabel(f_row, text=f"#{idx+1}", width=50).pack(side="left", padx=5)
            ctk.CTkLabel(f_row, text=f"Código: {item['codigo_prod']}", width=180, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)
            ctk.CTkLabel(f_row, text=f"Preço: R$ {item['preco_oferta']:.2f}", width=150, text_color="#A5D6A7", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

            btn_del = ctk.CTkButton(f_row, text="X", width=30, fg_color="#D32F2F", command=lambda i=idx: self.remover_item(i))
            btn_del.pack(side="right", padx=5)

    def remover_item(self, index):
        self.itens.pop(index)
        self.atualizar_grid()

    def converter_data_para_br(self, data_obj):
        if isinstance(data_obj, (datetime, datetime.date)):
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
            cur.execute("SELECT * FROM public.encarte WHERE id = %s", (self.encarte_id,))
            enc = cur.fetchone()

            if enc:
                self.txt_titulo.insert(0, enc['titulo'])
                self.txt_dt_ini.insert(0, self.converter_data_para_br(enc['data_inicio']))
                self.txt_dt_fim.insert(0, self.converter_data_para_br(enc['data_fim']))

                cur.execute("SELECT codigo_prod, preco_oferta FROM public.encarte_item WHERE encarte_id = %s ORDER BY ordem, id", (self.encarte_id,))
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
                    UPDATE public.encarte 
                    SET titulo=%s, data_inicio=%s, data_fim=%s 
                    WHERE id=%s
                """, (titulo, dt_ini_iso, dt_fim_iso, self.encarte_id))
                
                cur.execute("DELETE FROM public.encarte_item WHERE encarte_id=%s", (self.encarte_id,))
                enc_id = self.encarte_id
            else:
                cur.execute("""
                    INSERT INTO public.encarte (titulo, data_inicio, data_fim) 
                    VALUES (%s, %s, %s) RETURNING id
                """, (titulo, dt_ini_iso, dt_fim_iso))
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
# EXECUÇÃO PRINCIPAL DO APLICATIVO
# ==============================================================================
if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("Gestão de Encartes")
    root.geometry("400x200")

    # Botão principal para abrir a janela de encartes
    btn_abrir = ctk.CTkButton(
        root, 
        text="➕ Gerenciar Encartes", 
        command=lambda: FormEncarteWindow(root)
    )
    btn_abrir.pack(expand=True)

    root.mainloop()    
