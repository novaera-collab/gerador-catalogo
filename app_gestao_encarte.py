# -*- coding: utf-8 -*-
import sys
import os
import json
import traceback
import subprocess
import psycopg2
import psycopg2.extras
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog, QComboBox, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

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

def salvar_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

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

class ThreadCarregarEncartes(QThread):
    sucesso = pyqtSignal(list)
    erro = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        try:
            query = """
                SELECT id, titulo, data_inicio, data_fim, ativo
                FROM encarte
                ORDER BY id DESC
            """
            dados = self.db.executar_consulta(query)
            self.sucesso.emit(dados)
        except Exception as e:
            self.erro.emit(str(e))

class ModalGerarEncarte(QDialog):
    def __init__(self, encarte_id, encarte_titulo, dt_inicio, dt_fim, config, db, parent=None):
        super().__init__(parent)
        self.encarte_id = encarte_id
        self.encarte_titulo = encarte_titulo
        self.validade_texto = f"Precos validos no periodo de {dt_inicio} a {dt_fim}" if dt_inicio else ""
        self.config = config
        self.db = db

        self.setWindowTitle(f"Gerando Encarte #{encarte_id}")
        self.setFixedSize(420, 320)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("<b>Nome do Contato (Rodapé):</b>"))
        self.txt_nome = QLineEdit()
        self.txt_nome.setText("JOSE")
        layout.addWidget(self.txt_nome)

        layout.addWidget(QLabel("<b>Contato WhatsApp:</b>"))
        self.txt_whatsapp = QLineEdit()
        self.txt_whatsapp.setText("(45) 99905-1999")
        layout.addWidget(self.txt_whatsapp)

        layout.addWidget(QLabel("<b>Tabela de Preço:</b>"))
        self.combo_tabela = QComboBox()
        self.combo_tabela.addItems(["Tabela 1", "Tabela 2", "Tabela 3"])
        self.combo_tabela.setCurrentIndex(2)  # Padrão: Tabela 3
        layout.addWidget(self.combo_tabela)

        self.chk_saldo = QCheckBox("Somente produtos com saldo > 0")
        self.chk_saldo.setChecked(True)
        layout.addWidget(self.chk_saldo)

        layout.addSpacing(15)

        btn_executar = QPushButton("🚀 Executar Geração")
        btn_executar.setStyleSheet("background-color: #22702C; color: white; font-weight: bold; padding: 8px;")
        btn_executar.clicked.connect(self.executar_geracao)
        layout.addWidget(btn_executar)

        self.setLayout(layout)

    def executar_geracao(self):
        nome_contato = self.txt_nome.text().strip()
        whatsapp = self.txt_whatsapp.text().strip()
        tabela_opcao = str(self.combo_tabela.currentIndex() + 1)
        filtro_saldo = "AND e.fsaldo > 0" if self.chk_saldo.isChecked() else ""

        caminho_sql = os.path.join(os.getcwd(), "consulta_catalogo.sql")
        if not os.path.exists(caminho_sql):
            QMessageBox.critical(self, "Erro", f"Arquivo 'consulta_catalogo.sql' não foi encontrado na pasta raiz.")
            return

        try:
            with open(caminho_sql, "r", encoding="utf-8") as f:
                query = f.read()

            # Substituição dos parâmetros dinâmicos na SQL
            query = query.replace("{SCHEMA}", self.config.get("schema", "dk"))
            query = query.replace("{ID_ENCARTE}", str(self.encarte_id))
            query = query.replace("{TABELA_PRECO}", tabela_opcao)
            query = query.replace("{FILTRO_SALDO}", filtro_saldo)

            rows = self.db.executar_consulta(query)

            if not rows:
                QMessageBox.warning(self, "Aviso", "Nenhum produto encontrado para o encarte selecionado.")
                return

            pasta_saida = self.config.get("diretorio_retorno", os.getcwd())
            if not os.path.exists(pasta_saida):
                os.makedirs(pasta_saida, exist_ok=True)

            caminho_csv = os.path.join(pasta_saida, "DADOS_CATALOGO.CSV")
            caminho_jpg = os.path.join(pasta_saida, "CATALOGO_OESTE_PHARMA.JPG")

            # Gravação do CSV com Bloco de Metadados no topo
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

            # Executa Gerar_catalogo.exe para processar o JPG
            exe_gerar = os.path.join(os.getcwd(), "Gerar_catalogo.exe")
            if os.path.exists(exe_gerar):
                subprocess.run([exe_gerar, caminho_csv], check=True)

            # Executa visualizar_catalogo.exe
            exe_visualizar = os.path.join(os.getcwd(), "visualizar_catalogo.exe")
            if os.path.exists(exe_visualizar):
                subprocess.Popen([exe_visualizar, caminho_csv, caminho_jpg])

            self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Falha na Geração", f"Ocorreu um erro ao processar o encarte:\n{e}\n\n{traceback.format_exc()}")

class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = carregar_config()
        self.db = DBConnection(self.config)

        self.setWindowTitle("Gestão de Encartes - Oeste Pharma")
        self.setGeometry(100, 100, 900, 550)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout()
        widget_central.setLayout(layout_principal)

        # Painel de Topo
        frame_topo = QFrame()
        frame_topo.setStyleSheet("background-color: #22702C;")
        layout_topo = QHBoxLayout(frame_topo)

        lbl_titulo = QLabel("Painel de Gestão de Encartes")
        lbl_titulo.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout_topo.addWidget(lbl_titulo)

        btn_atualizar = QPushButton("🔄 Atualizar Lista")
        btn_atualizar.setStyleSheet("background-color: white; font-weight: bold;")
        btn_atualizar.clicked.connect(self.carregar_encartes)
        layout_topo.addWidget(btn_atualizar, alignment=Qt.AlignRight)

        layout_principal.addWidget(frame_topo)

        # Tabela de Encartes
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["ID", "Título do Encarte", "Data Início", "Data Fim", "Status", "Ação"])
        self.tabela.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        layout_principal.addWidget(self.tabela)

        self.carregar_encartes()

    def carregar_encartes(self):
        self.thread_carregar = ThreadCarregarEncartes(self.db)
        self.thread_carregar.sucesso.connect(self.preencher_tabela)
        self.thread_carregar.erro.connect(lambda msg: QMessageBox.critical(self, "Erro de Conexão", f"Erro ao consultar encartes:\n{msg}"))
        self.thread_carregar.start()

    def preencher_tabela(self, encartes):
        self.tabela.setRowCount(0)
        for i, row in enumerate(encartes):
            self.tabela.insertRow(i)
            self.tabela.setItem(i, 0, QTableWidgetItem(str(row["id"])))
            self.tabela.setItem(i, 1, QTableWidgetItem(str(row["titulo"])))
            
            dt_inicio = row["data_inicio"].strftime("%d/%m/%Y") if row.get("data_inicio") else ""
            dt_fim = row["data_fim"].strftime("%d/%m/%Y") if row.get("data_fim") else ""
            
            self.tabela.setItem(i, 2, QTableWidgetItem(dt_inicio))
            self.tabela.setItem(i, 3, QTableWidgetItem(dt_fim))
            
            status = "Ativo" if row.get("ativo") else "Inativo"
            self.tabela.setItem(i, 4, QTableWidgetItem(status))

            btn_gerar = QPushButton("⚡ Gerar")
            btn_gerar.setStyleSheet("background-color: #25D366; color: white; font-weight: bold;")
            btn_gerar.clicked.connect(lambda _, r=row, di=dt_inicio, df=dt_fim: self.abrir_modal_gerar(r["id"], r["titulo"], di, df))
            self.tabela.setCellWidget(i, 5, btn_gerar)

    def abrir_modal_gerar(self, encarte_id, titulo, dt_inicio, dt_fim):
        modal = ModalGerarEncarte(encarte_id, titulo, dt_inicio, dt_fim, self.config, self.db, self)
        modal.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec_())
