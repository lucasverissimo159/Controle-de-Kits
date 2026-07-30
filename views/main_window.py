"""
Janela principal do sistema - COMPLETA com TODAS as funcionalidades
Inclui: Janela Principal, Gerenciar, Registros Antigos, ESTATÍSTICAS COMPLETA
"""
import customtkinter as ctk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
import os
import json
import re
import sys
from tkcalendar import Calendar, DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from collections import Counter
import numpy as np
import plotly.graph_objects as go
import tempfile
import webbrowser
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment  
from PIL import Image, ImageGrab
from plotly.subplots import make_subplots
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from views.widgets.scrollable_combobox import ScrollableComboBox
from views.widgets.tooltip import Tooltip
from views.history_dialog import HistoryDialog
from views.record_window import RecordWindow
from models.database import Database as HistoryDB

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        # Executando como .exe (PyInstaller)
        return os.path.join(sys._MEIPASS, relative_path)
    # Executando como script Python
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class KitControlApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Sistema de Controle de Kits de Informática")
        self.root.geometry("1500x900")
        
        # Maximizar após a janela ser criada
        self.root.after(10, lambda: self.root.state('zoomed'))

        # Definir ícone da janela principal
        self.set_window_icon(self.root)
        
        # Tema atual
        self.current_theme = "light"
        
        # Inicializar banco de dados
        self.init_database()
        self.history_db = HistoryDB()
        
        # Variáveis de filtro
        self.filter_vars = {
            'data': ctk.StringVar(),
            'tecnico': ctk.StringVar(value="Todos"),
            'matricula': ctk.StringVar(value="Todos"),
            'kit': ctk.StringVar(value="Todos"),
            'local': ctk.StringVar(value="Todos")
        }
        
        # Variáveis para registros antigos (ARQUIVOS)
        self.archive_filter_vars = {
            'mes': ctk.StringVar(value=str(datetime.now().month).zfill(2)),
            'ano': ctk.StringVar(value=str(datetime.now().year)),
            'tecnico': ctk.StringVar(value="Todos"),
            'matricula': ctk.StringVar(value="Todos"),
            'kit': ctk.StringVar(value="Todos"),
            'local': ctk.StringVar(value="Todos"),
            'data': ctk.StringVar()  # ← ADICIONE ESTA LINHA
        }

        # Variáveis para filtros de estatísticas
        self.stats_filter_vars = {
            'mes': ctk.StringVar(value=str(datetime.now().month).zfill(2)),
            'ano': ctk.StringVar(value=str(datetime.now().year)),
            'data': ctk.StringVar()
        }
        
        # Criar interface
        self.create_widgets()
        
        # Carregar dados
        self.load_main_data()
        
        # Verificar arquivamento mensal
        self.check_monthly_archive()
        
        # Vincular eventos de filtro automático
        self.bind_filter_events()
        
        # Vincular eventos de filtro automático para registros antigos
        self.bind_archive_filter_events()
        # bind_stats_filter_events() será chamado pelo StatsManager

        # Encerramento controlado: garante que o clique no X sempre
        # finalize o processo, independentemente do tempo de execução.
        self._closing = False
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_window_icon(self, window):
        """Define o ícone para uma janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                window.iconbitmap(icon_path)
                # Para Windows - também define na barra de tarefas
                window.after(200, lambda: window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")

    def init_database(self):
        """Inicializa conexão com banco (tabelas criadas por Database)"""
        from models.database import Database
        db = Database('kit_control.db')  # Isso cria as tabelas se não existirem
        self.conn = db.conn
        self.cursor = db.cursor
        
        # Configurar timeout para evitar "database is locked"
        self.conn.execute("PRAGMA busy_timeout = 30000")  # 30 segundos
        # Usar WAL mode para melhor concorrência
        self.conn.execute("PRAGMA journal_mode = WAL")
        
    def create_widgets(self):
        """Cria a interface principal"""
        # Container principal
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Cabeçalho com botão de tema
        header = ctk.CTkFrame(main_container, corner_radius=10)
        header.pack(fill="x", pady=(0, 20))
        
        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="x", padx=20, pady=20)
        
        title = ctk.CTkLabel(header_content, text="CONTROLE DE KITS DE INFORMÁTICA", 
                            font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(side="left")
        
        # Botão de tema
        self.theme_btn = ctk.CTkButton(header_content, text="TEMA ESCURO", 
                                       command=self.toggle_theme,
                                       fg_color="#6b7280", hover_color="#4b5563",
                                       width=130, height=35)
        self.theme_btn.pack(side="right")
        
        # Sistema de Abas
        self.tabview = ctk.CTkTabview(main_container, corner_radius=10)
        self.tabview.pack(fill="both", expand=True)
        
        # Criar abas
        self.tabview.add("Janela Principal")
        self.tabview.add("Gerenciar Técnicos")
        self.tabview.add("Gerenciar Locais")
        self.tabview.add("Gerenciar Kits")
        self.tabview.add("Registros Antigos")
        self.tabview.add("Estatísticas")
        self.tabview.add("Ranking")
        
        # Configurar cada aba
        self.create_main_tab()
        self.create_manage_tab("tecnicos")
        self.create_manage_tab("locais")
        self.create_manage_tab("kits")
        self.create_archive_tab()
        self.create_stats_tab()
        self.create_ranking_tab()
        
        # Vincular evento de mudança de aba
        self.tabview.configure(command=self.on_tab_changed)
        
    def on_tab_changed(self):
        """Executado quando a aba é alterada"""
        current_tab = self.tabview.get()
        if current_tab == "Janela Principal":
            # Reaplicar os filtros ativos (preserva o que o usuário configurou)
            self.apply_filters()
        elif current_tab == "Registros Antigos":
            # Recarregar dados E ordenar por Data Início ao entrar na aba
            self.load_archive_data()
        elif current_tab == "Estatísticas":
            if hasattr(self, 'stats_manager'):
                self.stats_manager.update_statistics()
        
    def bind_filter_events(self):
        """Vincula eventos para filtro automático"""
        self.filter_vars['data'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['tecnico'].trace_add('write', lambda *args: self.on_tecnico_filter_change())
        self.filter_vars['matricula'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['kit'].trace_add('write', lambda *args: self.apply_filters())
        self.filter_vars['local'].trace_add('write', lambda *args: self.apply_filters())
        
    def toggle_theme(self):
        """Alterna entre tema claro e escuro"""
        if self.current_theme == "dark":
            ctk.set_appearance_mode("light")
            self.current_theme = "light"
            self.theme_btn.configure(text="TEMA ESCURO")
        else:
            ctk.set_appearance_mode("dark")
            self.current_theme = "dark"
            self.theme_btn.configure(text="TEMA CLARO")
        
        # Atualizar cores de todas as tabelas
        self.update_all_table_styles()
    
    def update_all_table_styles(self):
        """Atualiza o estilo de todas as tabelas"""
        self.update_table_style()
        self.update_manage_table_styles()
    
    def update_table_style(self):
        """Atualiza o estilo da tabela principal conforme o tema"""
        style = ttk.Style()
        
        if self.current_theme == "dark":
            style.theme_use('default')
            style.configure("Treeview", 
                           background="#2b2b2b",
                           foreground="white",
                           fieldbackground="#2b2b2b",
                           rowheight=30,
                           borderwidth=0)
            style.configure("Treeview.Heading",
                           background="#1a1a1a",
                           foreground="white",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#3b3b3b")
            style.map("Treeview", 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
        else:
            style.theme_use('default')
            style.configure("Treeview", 
                           background="white",
                           foreground="black",
                           fieldbackground="white",
                           rowheight=30,
                           borderwidth=0)
            style.configure("Treeview.Heading",
                           background="#e5e5e5",
                           foreground="black",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#d4d4d4")
            style.map("Treeview", 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
    
    def update_manage_table_styles(self):
        """Atualiza o estilo das tabelas de gerenciamento"""
        for tipo in ["tecnicos", "locais", "kits"]:
            if hasattr(self, f'{tipo}_listbox'):
                listbox = getattr(self, f'{tipo}_listbox')
                style = ttk.Style()
                if self.current_theme == "dark":
                    style.theme_use('default')
                    style.configure(f"{tipo}.Treeview", 
                                   background="#2b2b2b",
                                   foreground="white",
                                   fieldbackground="#2b2b2b",
                                   rowheight=30,
                                   borderwidth=0)
                    style.configure(f"{tipo}.Treeview.Heading",
                                   background="#1a1a1a",
                                   foreground="white",
                                   relief="flat",
                                   borderwidth=1,
                                   bordercolor="#3b3b3b")
                    style.map(f"{tipo}.Treeview", 
                             background=[('selected', '#3b82f6')],
                             foreground=[('selected', 'white')])
                else:
                    style.theme_use('default')
                    style.configure(f"{tipo}.Treeview", 
                                   background="white",
                                   foreground="black",
                                   fieldbackground="white",
                                   rowheight=30,
                                   borderwidth=0)
                    style.configure(f"{tipo}.Treeview.Heading",
                                   background="#e5e5e5",
                                   foreground="black",
                                   relief="flat",
                                   borderwidth=1,
                                   bordercolor="#d4d4d4")
                    style.map(f"{tipo}.Treeview", 
                             background=[('selected', '#3b82f6')],
                             foreground=[('selected', 'white')])
                listbox.configure(style=f"{tipo}.Treeview")
    
    def create_main_tab(self):
        """Cria aba principal"""
        tab = self.tabview.tab("Janela Principal")
        
        # Frame de filtros
        filter_frame = ctk.CTkFrame(tab, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15))

        filter_title = ctk.CTkLabel(filter_frame, text="FILTROS",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        filter_title.pack(anchor="w", padx=20, pady=(15, 10))

        # Linha de filtros em pack horizontal
        filters_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        filters_row.pack(fill="x", padx=20, pady=(0, 15))

        # — Data —
        f_data = ctk.CTkFrame(filters_row, fg_color="transparent")
        f_data.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_data, text="Data:").pack(side="left", padx=(0, 5))
        date_inner = ctk.CTkFrame(f_data, fg_color="transparent")
        date_inner.pack(side="left")
        date_entry = ctk.CTkEntry(date_inner, textvariable=self.filter_vars['data'],
                                  placeholder_text="DD/MM/AAAA", width=150)
        date_entry.pack(side="left")
        date_entry.bind('<KeyRelease>', self.format_date_input)
        ctk.CTkButton(date_inner, text="📅", width=30, height=30,
                      command=lambda: self.open_calendar(date_entry)).pack(side="left", padx=(5, 0))

        # — Técnico —
        f_tec = ctk.CTkFrame(filters_row, fg_color="transparent")
        f_tec.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_tec, text="Técnico:").pack(side="left", padx=(0, 5))
        self.tecnico_combo = ScrollableComboBox(f_tec, variable=self.filter_vars['tecnico'],
                                                values=self.get_unique_tecnicos(),
                                                width=190, max_visible_items=6, app=self)
        self.tecnico_combo.pack(side="left")

        # — Matrícula —
        f_mat = ctk.CTkFrame(filters_row, fg_color="transparent")
        f_mat.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_mat, text="Matrícula:").pack(side="left", padx=(0, 5))
        self.matricula_combo = ScrollableComboBox(f_mat, variable=self.filter_vars['matricula'],
                                                  values=["Todos"],
                                                  width=190, max_visible_items=6, app=self)
        self.matricula_combo.pack(side="left")

        # — Local —
        f_local = ctk.CTkFrame(filters_row, fg_color="transparent")
        f_local.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_local, text="Local:").pack(side="left", padx=(0, 5))
        self.local_filter = ScrollableComboBox(f_local, variable=self.filter_vars['local'],
                                               values=["Todos"] + self.get_items("locais"),
                                               width=190, max_visible_items=6, app=self)
        self.local_filter.pack(side="left")

        # — Nº Kit —
        f_kit = ctk.CTkFrame(filters_row, fg_color="transparent")
        f_kit.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_kit, text="Nº Kit:").pack(side="left", padx=(0, 5))
        self.kit_filter = ScrollableComboBox(f_kit, variable=self.filter_vars['kit'],
                                             values=["Todos"] + self.get_items("kits", "numero"),
                                             width=140, max_visible_items=6, app=self)
        self.kit_filter.pack(side="left")
        
        # Frame de botões
        action_frame = ctk.CTkFrame(tab, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 10))
        
        btn_novo = ctk.CTkButton(action_frame, text="NOVO REGISTRO", 
                                command=self.new_record,
                                fg_color="#10b981", hover_color="#059669",
                                width=150, height=40)
        btn_novo.pack(side="left", padx=5)
        
        btn_editar = ctk.CTkButton(action_frame, text="EDITAR", 
                                  command=self.edit_record,
                                  fg_color="#f59e0b", hover_color="#d97706",
                                  width=150, height=40)
        btn_editar.pack(side="left", padx=5)
        
        btn_info = ctk.CTkButton(action_frame, text="ℹ️ INFO", 
                     command=self.show_record_history,
                     fg_color="#3b82f6", hover_color="#2563eb",
                     width=120, height=40)
        btn_info.pack(side="left", padx=5)

        # Botão de limpar filtros
        btn_clear = ctk.CTkButton(action_frame, text="LIMPAR FILTROS", 
                                 command=self.clear_filters,
                                 fg_color="#475569", hover_color="#334155",
                                 width=150, height=35)
        btn_clear.pack(side="left", padx=5)
        
        '''btn_excluir = ctk.CTkButton(action_frame, text="EXCLUIR", 
                                   command=self.delete_record,
                                   fg_color="#ef4444", hover_color="#dc2626",
                                   width=150, height=40)
        btn_excluir.pack(side="left", padx=5)'''
        
        # Label informativo sobre o limite de 20 registros
        info_label = ctk.CTkLabel(action_frame, 
                                 text="📌 Exibindo os últimos 20 registros mais recentes",
                                 font=ctk.CTkFont(size=12),
                                 text_color="#60a5fa")
        info_label.pack(side="right", padx=20)
        
        # Frame da tabela
        table_frame = ctk.CTkFrame(tab, corner_radius=10)
        table_frame.pack(fill="both", expand=True)
        
        # Configurar estilo da tabela
        self.update_table_style()
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=(0, 10), pady=10)
        
        # Tabela
        columns = ("ID", "Data Início", "Data Fim", "Técnico", "Matrícula", "Nº Kit", "Local", 
                  "Horário Início", "Horário Fim")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.tree.yview)
        
        # Configurar colunas
        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Data Início", width=120, anchor="center")
        self.tree.column("Data Fim", width=120, anchor="center")
        self.tree.column("Técnico", width=150, anchor="center")
        self.tree.column("Matrícula", width=100, anchor="center")
        self.tree.column("Nº Kit", width=100, anchor="center")
        self.tree.column("Local", width=200, anchor="center")
        self.tree.column("Horário Início", width=120, anchor="center")
        self.tree.column("Horário Fim", width=120, anchor="center")
        
        # Configurar cabeçalhos com função de ordenação
        for col in columns:
            self.tree.heading(col, text=col, anchor="center", 
                            command=lambda c=col: self.sort_treeview(self.tree, c, False))
        
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
    
    def create_archive_tab(self):
        """Cria aba de registros antigos com filtros"""
        tab = self.tabview.tab("Registros Antigos")
        
        # Frame de filtros
        filter_frame = ctk.CTkFrame(tab, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 15), padx=20)

        # Título
        filter_title = ctk.CTkLabel(filter_frame, text="FILTROS - REGISTROS CONCLUÍDOS",
                                    font=ctk.CTkFont(size=16, weight="bold"))
        filter_title.pack(anchor="w", padx=20, pady=(15, 10))

        # === LINHA 1: Mês, Ano, Técnico, Matrícula, Nº Kit ===
        row1 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(0, 5))

        # — Mês —
        f_mes = ctk.CTkFrame(row1, fg_color="transparent")
        f_mes.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_mes, text="Mês:").pack(side="left", padx=(0, 5))
        self.archive_mes_filter = ScrollableComboBox(f_mes,
            variable=self.archive_filter_vars['mes'],
            values=[f"{i:02d}" for i in range(1, 13)],
            width=80, max_visible_items=6, app=self)
        self.archive_mes_filter.pack(side="left")

        # — Ano —
        f_ano = ctk.CTkFrame(row1, fg_color="transparent")
        f_ano.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_ano, text="Ano:").pack(side="left", padx=(0, 5))
        self.archive_ano_filter = ScrollableComboBox(f_ano,
            variable=self.archive_filter_vars['ano'],
            values=self.get_available_years(),
            width=90, max_visible_items=6, app=self)
        self.archive_ano_filter.pack(side="left")

        # — Técnico —
        f_tec = ctk.CTkFrame(row1, fg_color="transparent")
        f_tec.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_tec, text="Técnico:").pack(side="left", padx=(0, 5))
        self.archive_tecnico_combo = ScrollableComboBox(f_tec,
            variable=self.archive_filter_vars['tecnico'],
            values=self.get_unique_tecnicos(),
            width=190, max_visible_items=6, app=self)
        self.archive_tecnico_combo.pack(side="left")

        # — Matrícula —
        f_mat = ctk.CTkFrame(row1, fg_color="transparent")
        f_mat.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_mat, text="Matrícula:").pack(side="left", padx=(0, 5))
        self.archive_matricula_combo = ScrollableComboBox(f_mat,
            variable=self.archive_filter_vars['matricula'],
            values=["Todos"],
            width=190, max_visible_items=6, app=self)
        self.archive_matricula_combo.pack(side="left")

        # — Nº Kit —
        f_kit = ctk.CTkFrame(row1, fg_color="transparent")
        f_kit.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_kit, text="Nº Kit:").pack(side="left", padx=(0, 5))
        self.archive_kit_filter = ScrollableComboBox(f_kit,
            variable=self.archive_filter_vars['kit'],
            values=["Todos"] + self.get_items("kits", "numero"),
            width=140, max_visible_items=6, app=self)
        self.archive_kit_filter.pack(side="left")

        # === LINHA 2: Local, Data, INFO, Limpar Filtros ===
        row2 = ctk.CTkFrame(filter_frame, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 5))

        # — Local —
        f_local = ctk.CTkFrame(row2, fg_color="transparent")
        f_local.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_local, text="Local:").pack(side="left", padx=(0, 5))
        self.archive_local_filter = ScrollableComboBox(f_local,
            variable=self.archive_filter_vars['local'],
            values=["Todos"] + self.get_items("locais"),
            width=190, max_visible_items=6, app=self)
        self.archive_local_filter.pack(side="left")

        # — Data —
        f_data = ctk.CTkFrame(row2, fg_color="transparent")
        f_data.pack(side="left", padx=(0, 20))
        ctk.CTkLabel(f_data, text="Data:").pack(side="left", padx=(0, 5))
        archive_date_entry = ctk.CTkEntry(f_data,
            textvariable=self.archive_filter_vars['data'],
            placeholder_text="DD/MM/AAAA", width=110)
        archive_date_entry.pack(side="left")
        ctk.CTkButton(f_data, text="📅", width=30, height=30,
                      command=lambda: self.open_calendar(archive_date_entry)).pack(side="left", padx=(5, 0))

        # — Botão INFO —
        ctk.CTkButton(row2, text="ℹ️ INFO",
                      command=self.show_archive_history,
                      fg_color="#3b82f6", hover_color="#2563eb",
                      width=100, height=30).pack(side="left", padx=(20, 20))

        # — Limpar Filtros —
        ctk.CTkButton(row2, text="LIMPAR FILTROS",
                      command=self.clear_archive_filters,
                      fg_color="#475569", hover_color="#334155",
                      width=140, height=35).pack(side="left")

        # === Label informativo ===
        ctk.CTkLabel(filter_frame,
                     text="💡 Mostrando apenas registros com Data Fim e Horário Fim preenchidos",
                     text_color="#6b7280",
                     font=ctk.CTkFont(size=11)).pack(anchor="w", padx=20, pady=(5, 15))
        
        # === TABELA ===
        
        table_frame = ctk.CTkFrame(tab, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        # Tabela
        columns = ("ID", "Data Início", "Data Fim", "Técnico", "Matrícula", "Nº Kit", "Local", 
                "Horário Início", "Horário Fim")
        self.archive_tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                                        yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.archive_tree.yview)
        
        # Configurar colunas
        self.archive_tree.column("ID", width=50, anchor="center")
        self.archive_tree.column("Data Início", width=120, anchor="center")
        self.archive_tree.column("Data Fim", width=120, anchor="center")
        self.archive_tree.column("Técnico", width=150, anchor="center")
        self.archive_tree.column("Matrícula", width=100, anchor="center")
        self.archive_tree.column("Nº Kit", width=100, anchor="center")
        self.archive_tree.column("Local", width=200, anchor="center")
        self.archive_tree.column("Horário Início", width=120, anchor="center")
        self.archive_tree.column("Horário Fim", width=120, anchor="center")
        
        # Configurar cabeçalhos
        for col in columns:
            self.archive_tree.heading(col, text=col, anchor="center", 
                                    command=lambda c=col: self.sort_treeview(self.archive_tree, c, False))
        
        self.archive_tree.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Carregar dados iniciais
        self.load_archive_data()
    
    # Estatísticas gerenciadas por StatsManager
    def create_stats_tab(self):
        """Cria aba de estatísticas"""
        from views.stats_manager import StatsManager
        tab = self.tabview.tab("Estatísticas")
        self.stats_manager = StatsManager(self)
        self.stats_manager.create_stats_tab(tab)

    # Estatísticas gerenciadas por RankingManager
    def create_ranking_tab(self):
        """Cria aba de ranking"""
        from views.ranking_manager import RankingManager
        tab = self.tabview.tab("Ranking")
        self.ranking_manager = RankingManager(self)
        self.ranking_manager.create_ranking_tab(tab)

    def bind_archive_filter_events(self):
        """Vincula eventos para filtro automático da aba de arquivos"""
        self.archive_filter_vars['mes'].trace_add('write', self.on_archive_mes_ano_changed)
        self.archive_filter_vars['ano'].trace_add('write', self.on_archive_mes_ano_changed)
        self.archive_filter_vars['tecnico'].trace_add('write', lambda *args: self.on_archive_tecnico_filter_change())
        self.archive_filter_vars['matricula'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['kit'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['local'].trace_add('write', lambda *args: self.load_archive_data())
        self.archive_filter_vars['data'].trace_add('write', self.on_archive_data_changed)
    
    
    def get_unique_tecnicos(self):
        """Retorna nomes ÚNICOS de técnicos (sem duplicatas)"""
        self.cursor.execute('SELECT DISTINCT nome FROM tecnicos ORDER BY nome')
        nomes = [row[0] for row in self.cursor.fetchall()]
        return ["Todos"] + nomes

    def on_tecnico_filter_change(self):
        """Quando filtro de TÉCNICO muda, atualiza opções de MATRÍCULA"""
        nome_selecionado = self.filter_vars['tecnico'].get()
        if hasattr(self, 'matricula_combo'):
            self.update_matricula_combobox(nome_selecionado, self.matricula_combo)
        # Resetar matrícula para "Todos" ao trocar de técnico
        self.filter_vars['matricula'].set("Todos")
        self.apply_filters()

    def on_archive_tecnico_filter_change(self):
        """Quando filtro de TÉCNICO muda nos Registros Antigos"""
        nome_selecionado = self.archive_filter_vars['tecnico'].get()
        if hasattr(self, 'archive_matricula_combo'):
            self.update_archive_matricula_combobox(nome_selecionado, self.archive_matricula_combo)
        # Resetar matrícula para "Todos" ao trocar de técnico
        self.archive_filter_vars['matricula'].set("Todos")
        self.load_archive_data()

    def get_all_matriculas(self):
        """Retorna todas as matrículas cadastradas"""
        self.cursor.execute("SELECT matricula FROM tecnicos ORDER BY matricula")
        return [row[0] for row in self.cursor.fetchall()]

    def update_matricula_combobox(self, nome_tecnico, combobox_widget):
        """Atualiza opções de matrícula baseado no nome selecionado.
        - Nenhum técnico selecionado (Todos): mostra todas as matrículas.
        - Técnico selecionado: mostra só a(s) matrícula(s) daquele nome.
        """
        if nome_tecnico == "Todos":
            opcoes = ["Todos"] + self.get_all_matriculas()
        else:
            self.cursor.execute(
                "SELECT matricula FROM tecnicos WHERE nome = ? ORDER BY matricula",
                (nome_tecnico,)
            )
            matriculas = [row[0] for row in self.cursor.fetchall()]
            opcoes = ["Todos"] + matriculas
        combobox_widget.configure(values=opcoes)

    def update_archive_matricula_combobox(self, nome_tecnico, combobox_widget):
        """Atualiza opções de matrícula para Registros Antigos.
        - Nenhum técnico selecionado (Todos): mostra todas as matrículas.
        - Técnico selecionado: mostra só a(s) matrícula(s) daquele nome.
        """
        if nome_tecnico == "Todos":
            opcoes = ["Todos"] + self.get_all_matriculas()
        else:
            self.cursor.execute(
                "SELECT matricula FROM tecnicos WHERE nome = ? ORDER BY matricula",
                (nome_tecnico,)
            )
            matriculas = [row[0] for row in self.cursor.fetchall()]
            opcoes = ["Todos"] + matriculas
        combobox_widget.configure(values=opcoes)

    def on_archive_mes_ano_changed(self, *args):
        """Callback quando mês ou ano mudam em Registros Antigos"""
        # Limpar filtro de data quando mês/ano são alterados
        if self.archive_filter_vars['data'].get():
            self.archive_filter_vars['data'].set("")
        self.load_archive_data()
    
    def on_archive_data_changed(self, *args):
        """Callback quando data específica muda em Registros Antigos"""
        data = self.archive_filter_vars['data'].get()
        if data:  # Só atualiza se data não estiver vazia
            self.load_archive_data()
    
    def get_available_years(self):
        """Retorna lista de anos que possuem registros concluídos"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT substr(data_inicio, 7, 4) as ano
                FROM registros 
                WHERE data_fim IS NOT NULL AND horario_fim IS NOT NULL
                  AND data_fim != '' AND horario_fim != ''
                ORDER BY ano DESC
            ''')
            years = [row[0] for row in self.cursor.fetchall() if row[0]]
            
            # Se não houver anos, retornar o ano atual
            if not years:
                years = [str(datetime.now().year)]
            
            return years
        except:
            return [str(datetime.now().year)]
    
    def clear_archive_filters(self):
        """Limpa todos os filtros da aba de arquivos"""
        self.archive_filter_vars['mes'].set(str(datetime.now().month).zfill(2))
        self.archive_filter_vars['ano'].set(str(datetime.now().year))
        self.archive_filter_vars['data'].set("")
        self.archive_filter_vars['tecnico'].set("Todos")
        self.archive_filter_vars['matricula'].set("Todos")
        self.archive_filter_vars['kit'].set("Todos")
        self.archive_filter_vars['local'].set("Todos")
        if hasattr(self, 'archive_matricula_combo'):
            self.update_archive_matricula_combobox("Todos", self.archive_matricula_combo)
    
    def update_archive_filters(self):
        """Atualiza os valores dos filtros da aba de arquivos"""
        tecnicos = self.get_unique_tecnicos()
        kits = ["Todos"] + self.get_items("kits", "numero")
        locais = ["Todos"] + self.get_items("locais")
        years = self.get_available_years()
        
        if hasattr(self, 'archive_tecnico_combo'):
            self.archive_tecnico_combo.configure(values=tecnicos)
        if hasattr(self, 'archive_kit_filter'):
            self.archive_kit_filter.configure(values=kits)
        if hasattr(self, 'archive_local_filter'):
            self.archive_local_filter.configure(values=locais)
        if hasattr(self, 'archive_ano_filter'):
            self.archive_ano_filter.configure(values=years)
    
    def load_archive_data(self):
        """Carrega dados de registros CONCLUÍDOS com filtros aplicados"""
        # Limpar tabela
        for item in self.archive_tree.get_children():
            self.archive_tree.delete(item)
        
        # Obter valores dos filtros
        mes = self.archive_filter_vars['mes'].get()
        ano = self.archive_filter_vars['ano'].get()
        data_especifica = self.archive_filter_vars['data'].get()
        tecnico = self.archive_filter_vars['tecnico'].get()
        matricula_filtro = self.archive_filter_vars['matricula'].get()
        kit = self.archive_filter_vars['kit'].get()
        local = self.archive_filter_vars['local'].get()
        
        # Construir query - buscar apenas registros CONCLUÍDOS (COM JOIN)
        query = '''
            SELECT r.id, r.data_inicio, r.data_fim, t.nome as tecnico_nome, 
                r.num_kit, r.local, r.horario_inicio, r.horario_fim,
                t.matricula
            FROM registros r
            JOIN tecnicos t ON r.matricula_tecnico = t.matricula
            WHERE r.data_fim IS NOT NULL 
            AND r.horario_fim IS NOT NULL
            AND r.data_fim != ''
            AND r.horario_fim != ''
        '''
        params = []
        
        # Filtrar por data específica se preenchida
        if data_especifica and self.validate_date(data_especifica):
            query += " AND r.data_inicio = ?"
            params.append(data_especifica)
        # Senão, filtrar por mês/ano
        elif mes and ano:
            query += " AND substr(r.data_inicio, 4, 2) = ? AND substr(r.data_inicio, 7, 4) = ?"
            params.extend([mes, ano])
        
        # Filtros adicionais
        if tecnico != "Todos":
            query += " AND t.nome = ?"
            params.append(tecnico)
        
        if matricula_filtro != "Todos":
            query += " AND t.matricula = ?"
            params.append(matricula_filtro)
        
        if kit != "Todos":
            query += " AND r.num_kit = ?"
            params.append(kit)
        
        if local != "Todos":
            query += " AND r.local = ?"
            params.append(local)
        
        # SEMPRE ordenar por Data Início DECRESCENTE (convertendo DD/MM/AAAA para formato ordenável)
        query += '''
            ORDER BY 
                substr(data_inicio, 7, 4) || '-' || 
                substr(data_inicio, 4, 2) || '-' || 
                substr(data_inicio, 1, 2) DESC,
                horario_inicio DESC
        '''
        
        try:
            self.cursor.execute(query, params)
            records = self.cursor.fetchall()
            
            for record in records:
                # Extrair dados do JOIN (record tem: r.*, t.nome, t.matricula)
                tecnico_nome = record[3] if len(record) > 3 else "N/A"
                matricula_valor = record[8] if len(record) > 8 else ""
                
                # Inserir na ordem CORRETA das colunas
                self.archive_tree.insert('', 'end', values=(
                    record[0],  # ID
                    record[1],  # Data Início  
                    record[2] if record[2] else "EM ANDAMENTO",  # Data Fim
                    tecnico_nome,  # Técnico (do JOIN)
                    matricula_valor,  # Matrícula (do JOIN)
                    record[4],  # Nº Kit
                    record[5],  # Local
                    record[6],  # Horário Início
                    record[7] if record[7] else "-"  # Horário Fim
                ))
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar registros: {str(e)}")

    def sort_archive_by_date_inicio(self):
        """Ordena a tabela de registros antigos por Data Início (decrescente)"""
        if not hasattr(self, 'archive_tree'):
            return
        
        # Obter todos os itens
        items = [(self.archive_tree.set(item, 'Data Início'), item) 
                 for item in self.archive_tree.get_children('')]
        
        # Ordenar por data (formato DD/MM/AAAA)
        def date_key(date_str):
            try:
                return datetime.strptime(date_str, "%d/%m/%Y")
            except:
                return datetime.min
        
        items.sort(key=lambda x: date_key(x[0]), reverse=True)
        
        # Reorganizar itens
        for index, (_, item) in enumerate(items):
            self.archive_tree.move(item, '', index)
    
    def open_calendar(self, date_entry):
        """Abre o calendário para seleção de data"""
        calendar_window = ctk.CTkToplevel(self.root)
        calendar_window.title("Selecionar Data")
        calendar_window.geometry("300x300")
        calendar_window.grab_set()
        calendar_window.transient(self.root)
        
        # Calendário
        cal = Calendar(calendar_window, selectmode='day', 
                      year=datetime.now().year, 
                      month=datetime.now().month, 
                      day=datetime.now().day,
                      date_pattern='dd/mm/yyyy')
        cal.pack(padx=20, pady=20, fill="both", expand=True)
        
        def set_date():
            selected_date = cal.get_date()
            date_entry.delete(0, 'end')
            date_entry.insert(0, selected_date)
            calendar_window.destroy()
        
        # Botão para confirmar
        btn_confirm = ctk.CTkButton(calendar_window, text="SELECIONAR DATA", 
                                   command=set_date,
                                   fg_color="#10b981", hover_color="#059669")
        btn_confirm.pack(pady=10)
    
    def sort_treeview(self, tree, col, reverse):
        """Ordena a treeview pela coluna clicada"""
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        # Tenta converter para data se for uma coluna de data
        if "Data" in col:
            try:
                data.sort(key=lambda x: datetime.strptime(x[0], "%d/%m/%Y") if x[0] else datetime.min, reverse=reverse)
            except:
                data.sort(reverse=reverse)
        # Tenta converter para número se for ID ou Nº Kit
        elif col in ["ID", "Nº Kit"]:
            try:
                data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'), reverse=reverse)
            except:
                data.sort(reverse=reverse)
        else:
            data.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(data):
            tree.move(item, '', index)
        
        # Inverte a ordem para a próxima vez
        tree.heading(col, command=lambda: self.sort_treeview(tree, col, not reverse))
    
    def sort_manage_treeview(self, tree, col, reverse, tipo):
        """Ordena a treeview de gerenciamento pela coluna clicada"""
        data = [(tree.set(item, col), item) for item in tree.get_children('')]
        
        # Tenta converter para número se for ID
        if col == "ID":
            try:
                data.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'), reverse=reverse)
            except:
                data.sort(reverse=reverse)
        else:
            data.sort(reverse=reverse)
        
        for index, (val, item) in enumerate(data):
            tree.move(item, '', index)
        
        # Inverte a ordem para a próxima vez
        tree.heading(col, command=lambda: self.sort_manage_treeview(tree, col, not reverse, tipo))
    
    def format_date_input(self, event):
        """Formata automaticamente a data enquanto o usuário digita"""
        widget = event.widget
        content = widget.get()
        
        # Remove qualquer caractere não numérico
        numbers = re.sub(r'[^\d]', '', content)
        
        # Limita a 8 dígitos (DDMMAAAA)
        if len(numbers) > 8:
            numbers = numbers[:8]
        
        # Formata a data
        formatted = ""
        if len(numbers) > 0:
            formatted = numbers[0:2]
        if len(numbers) >= 3:
            formatted += "/" + numbers[2:4]
        if len(numbers) >= 5:
            formatted += "/" + numbers[4:8]
        
        # Atualiza o campo
        if content != formatted:
            widget.delete(0, 'end')
            widget.insert(0, formatted)
    
    def format_time_input(self, event):
        """Formata automaticamente o horário enquanto o usuário digita"""
        widget = event.widget
        content = widget.get()
        
        # Remove qualquer caractere não numérico
        numbers = re.sub(r'[^\d]', '', content)
        
        # Limita a 4 dígitos (HHMM)
        if len(numbers) > 4:
            numbers = numbers[:4]
        
        # Formata o horário
        formatted = ""
        if len(numbers) > 0:
            formatted = numbers[0:2]
        if len(numbers) >= 3:
            formatted += ":" + numbers[2:4]
        
        # Atualiza o campo
        if content != formatted:
            widget.delete(0, 'end')
            widget.insert(0, formatted)
    
    def auto_uppercase(self, event):
        """Converte automaticamente para maiúsculas enquanto digita"""
        widget = event.widget
        content = widget.get()
        upper_content = content.upper()
        
        if content != upper_content:
            cursor_pos = widget.index('insert')
            widget.delete(0, 'end')
            widget.insert(0, upper_content)
            widget.icursor(cursor_pos)
    
    def validate_date(self, date_string):
        """Valida se a data é válida"""
        try:
            datetime.strptime(date_string, "%d/%m/%Y")
            return True
        except ValueError:
            return False
    
    def validate_time(self, time_string):
        """Valida se o horário é válido"""
        try:
            datetime.strptime(time_string, "%H:%M")
            return True
        except ValueError:
            return False
    
    def make_uppercase(self, event):
        """Converte o texto para maiúsculas automaticamente"""
        widget = event.widget
        content = widget.get()
        if content != content.upper():
            widget.delete(0, 'end')
            widget.insert(0, content.upper())
    
    def create_manage_tab(self, tipo):
        """Cria aba de gerenciamento"""
        if tipo == "tecnicos":
            tab_name = "Gerenciar Técnicos"
            label = "TÉCNICOS"
        elif tipo == "locais":
            tab_name = "Gerenciar Locais"
            label = "LOCAIS"
        else:
            tab_name = "Gerenciar Kits"
            label = "KITS"
            
        tab = self.tabview.tab(tab_name)
        
        # Container
        container = ctk.CTkFrame(tab, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        title = ctk.CTkLabel(container, text=f"GERENCIAR {label}",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(0, 30))
        
        # Frame de botões (sem campo de entrada)
        input_frame = ctk.CTkFrame(container, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 20))
        
        btn_add = ctk.CTkButton(input_frame, text="ADICIONAR", 
                               command=lambda: self.add_item(tipo),
                               fg_color="#10b981", hover_color="#059669",
                               width=150, height=40)
        btn_add.pack(side="left", padx=(0, 10))

        btn_editar = ctk.CTkButton(input_frame, text="EDITAR", 
                                  command=lambda: self.edit_item(tipo),
                                  fg_color="#f59e0b", hover_color="#d97706",
                                  width=150, height=40)
        btn_editar.pack(side="left")
        
        # ===== BUSCADOR (lado direito) =====
        search_frame = ctk.CTkFrame(input_frame, fg_color="transparent")
        search_frame.pack(side="right")
        
        ctk.CTkLabel(search_frame, text="🔍", font=ctk.CTkFont(size=16)).pack(side="left", padx=(0, 5))
        
        if not hasattr(self, f'{tipo}_search_var'):
            setattr(self, f'{tipo}_search_var', ctk.StringVar())
        
        search_var = getattr(self, f'{tipo}_search_var')
        search_var.trace_add('write', lambda *args, t=tipo: self.filter_manage_list(t))
        
        search_placeholder = "Buscar por matrícula ou nome..." if tipo == "tecnicos" else "Buscar..."
        search_entry = ctk.CTkEntry(search_frame, textvariable=search_var,
                                placeholder_text=search_placeholder,
                                width=180 if tipo == "tecnicos" else 150,
                                height=35)
        search_entry.pack(side="left")
        
        # Frame da lista
        list_frame = ctk.CTkFrame(container, corner_radius=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        # Treeview para lista
        # Definir colunas baseado no tipo
        if tipo == "tecnicos":
            columns = ("ID", "Nome", "Matrícula")
        else:
            columns = ("ID", "Nome" if tipo != "kits" else "Número")
        listbox = ttk.Treeview(list_frame, columns=columns, show="headings",
                              yscrollcommand=scrollbar.set, height=12)
        scrollbar.config(command=listbox.yview)
        
        # Configurar larguras das colunas
        if tipo == "tecnicos":
            listbox.column("ID", width=80, anchor="center")
            listbox.column("Nome", width=250, anchor="center")
            listbox.column("Matrícula", width=150, anchor="center")
        else:
            listbox.column("ID", width=80, anchor="center")
            listbox.column(columns[1], width=400, anchor="center")
        
        # Configurar cabeçalhos com função de ordenação
        if tipo == "tecnicos":
            listbox.heading("ID", text="ID", anchor="center", 
                           command=lambda: self.sort_manage_treeview(listbox, "ID", False, tipo))
            listbox.heading("Nome", text="Nome", anchor="center",
                           command=lambda: self.sort_manage_treeview(listbox, "Nome", False, tipo))
            listbox.heading("Matrícula", text="Matrícula", anchor="center",
                           command=lambda: self.sort_manage_treeview(listbox, "Matrícula", False, tipo))
        else:
            listbox.heading("ID", text="ID", anchor="center", 
                           command=lambda: self.sort_manage_treeview(listbox, "ID", False, tipo))
            listbox.heading(columns[1], text=columns[1], anchor="center",
                           command=lambda: self.sort_manage_treeview(listbox, columns[1], False, tipo))
        
        listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configurar estilo da lista
        style_name = f"{tipo}.Treeview"
        style = ttk.Style()
        if self.current_theme == "dark":
            style.theme_use('default')
            style.configure(style_name, 
                           background="#2b2b2b",
                           foreground="white",
                           fieldbackground="#2b2b2b",
                           rowheight=30,
                           borderwidth=0)
            style.configure(style_name + ".Heading",
                           background="#1a1a1a",
                           foreground="white",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#3b3b3b")
            style.map(style_name, 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
        else:
            style.theme_use('default')
            style.configure(style_name, 
                           background="white",
                           foreground="black",
                           fieldbackground="white",
                           rowheight=30,
                           borderwidth=0)
            style.configure(style_name + ".Heading",
                           background="#e5e5e5",
                           foreground="black",
                           relief="flat",
                           borderwidth=1,
                           bordercolor="#d4d4d4")
            style.map(style_name, 
                     background=[('selected', '#3b82f6')],
                     foreground=[('selected', 'white')])
        
        listbox.configure(style=style_name)
        
        # Guardar referência
        setattr(self, f'{tipo}_listbox', listbox)
        
        # Botões de ação
        btn_frame = ctk.CTkFrame(container, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        '''btn_editar = ctk.CTkButton(btn_frame, text="EDITAR SELECIONADO", 
                                  command=lambda: self.edit_item(tipo),
                                  fg_color="#f59e0b", hover_color="#d97706",
                                  width=180, height=40)
        btn_editar.pack(side="left", padx=(0, 10))'''
        
        '''btn_excluir = ctk.CTkButton(btn_frame, text="EXCLUIR SELECIONADO", 
                                   command=lambda: self.delete_item(tipo),
                                   fg_color="#ef4444", hover_color="#dc2626",
                                   width=180, height=40)
        btn_excluir.pack(side="left")'''
        
        # Carregar dados
        self.load_manage_data(tipo)
    
    def get_items(self, tipo, campo="nome"):
        """Retorna lista de itens cadastrados"""
        self.cursor.execute(f"SELECT {campo} FROM {tipo} ORDER BY {campo}")
        return [row[0] for row in self.cursor.fetchall()]
    
    def load_main_data(self):
        """Carrega dados na tabela principal - LIMITA A 20 REGISTROS MAIS RECENTES"""
        # Atualizar combo de matrícula com todas as matrículas se técnico for "Todos"
        if hasattr(self, 'matricula_combo'):
            if self.filter_vars['tecnico'].get() == "Todos":
                self.update_matricula_combobox("Todos", self.matricula_combo)
        if hasattr(self, 'archive_matricula_combo'):
            if self.archive_filter_vars['tecnico'].get() == "Todos":
                self.update_archive_matricula_combobox("Todos", self.archive_matricula_combo)

        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Buscar os últimos 20 registros ordenados por data de início decrescente (COM JOIN)
        self.cursor.execute('''
            SELECT r.id, r.data_inicio, r.data_fim, t.nome as tecnico_nome, 
                r.num_kit, r.local, r.horario_inicio, r.horario_fim,
                t.matricula
            FROM registros r
            JOIN tecnicos t ON r.matricula_tecnico = t.matricula
            ORDER BY 
                substr(r.data_inicio, 7, 4) || '-' || 
                substr(r.data_inicio, 4, 2) || '-' || 
                substr(r.data_inicio, 1, 2) DESC,
                r.horario_inicio DESC
            LIMIT 20
        ''')

        registros = self.cursor.fetchall()
        
        for reg in registros:
            # Extrair dados do JOIN
            tecnico_nome = reg[3]  # Nome do técnico
            matricula = reg[8]  # Matrícula
            
            # Inserir na tabela
            item_id = self.tree.insert("", "end", values=(
                reg[0],  # ID
                reg[1],  # Data Início
                reg[2] if reg[2] else "EM ANDAMENTO",  # Data Fim
                tecnico_nome,  # Técnico
                matricula,  # Matrícula
                reg[4],  # Nº Kit
                reg[5],  # Local
                reg[6],  # Horário Início
                reg[7] if reg[7] else "-"  # Horário Fim
            ))
            
            data_fim = reg[2]
            horario_fim = reg[7]
            
            if not data_fim or not horario_fim:
                try:
                    data_inicio = datetime.strptime(reg[1], "%d/%m/%Y")
                    dias_diferenca = (datetime.now() - data_inicio).days
                    
                    if dias_diferenca > 2:
                        self.tree.item(item_id, tags=('vermelho',))
                    else:
                        self.tree.item(item_id, tags=('amarelo',))
                except ValueError:
                    # Se houver erro na conversão da data, não aplica cor
                    pass
        
        # Configurar cores das tags
        if self.current_theme == "dark":
            self.tree.tag_configure('amarelo', background='#fbbf24', foreground='black')
            self.tree.tag_configure('vermelho', background='#ef4444', foreground='white')
        else:
            self.tree.tag_configure('amarelo', background='#fbbf24', foreground='black')
            self.tree.tag_configure('vermelho', background='#ef4444', foreground='black')

    def apply_filters(self, *args):
        """Aplica filtros na tabela automaticamente - LIMITA A 20 REGISTROS"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Buscar registros com JOIN
        data_filtro = self.filter_vars['data'].get()
        nome_tecnico = self.filter_vars['tecnico'].get()
        matricula = self.filter_vars['matricula'].get()
        kit = self.filter_vars['kit'].get()
        local = self.filter_vars['local'].get()
        
        # Construir query com JOIN
        query = """
            SELECT r.*, t.nome as tecnico_nome, t.matricula
            FROM registros r
            JOIN tecnicos t ON r.matricula_tecnico = t.matricula
            WHERE 1=1
        """
        params = []
        
        # Filtro de data
        if data_filtro:
            query += " AND r.data_inicio = ?"
            params.append(data_filtro)
        
        # Filtro de técnico (por NOME)
        if nome_tecnico != "Todos":
            query += " AND t.nome = ?"
            params.append(nome_tecnico)
        
        # Filtro de matrícula
        if matricula != "Todos":
            query += " AND t.matricula = ?"
            params.append(matricula)
        
        # Filtro de kit
        if kit != "Todos":
            query += " AND r.num_kit = ?"
            params.append(kit)
        
        # Filtro de local
        if local != "Todos":
            query += " AND r.local = ?"
            params.append(local)
        
        # Ordenar por data de início decrescente
        query += """
            ORDER BY 
                substr(r.data_inicio, 7, 4) || '-' || 
                substr(r.data_inicio, 4, 2) || '-' || 
                substr(r.data_inicio, 1, 2) DESC,
                r.horario_inicio DESC
            LIMIT 20
        """
        
        self.cursor.execute(query, params)
        registros = self.cursor.fetchall()
        
        for reg in registros:
            # Extrair dados do JOIN
            tecnico_nome = reg[-2]  # Nome do técnico
            matricula_valor = reg[-1]  # Matrícula
            
            # Inserir na tabela
            item_id = self.tree.insert("", "end", values=(
                reg[0],  # ID
                reg[1],  # Data Início
                reg[2] if reg[2] else "EM ANDAMENTO",  # Data Fim
                tecnico_nome,  # Técnico
                matricula_valor,  # Matrícula
                reg[4],  # Nº Kit
                reg[5],  # Local
                reg[6],  # Horário Início
                reg[7] if reg[7] else "-"  # Horário Fim
            ))
            
            data_fim = reg[2]
            horario_fim = reg[7]
            
            if not data_fim or not horario_fim:
                try:
                    data_inicio = datetime.strptime(reg[1], "%d/%m/%Y")
                    dias_diferenca = (datetime.now() - data_inicio).days
                    
                    if dias_diferenca > 2:
                        self.tree.item(item_id, tags=('vermelho',))
                    else:
                        self.tree.item(item_id, tags=('amarelo',))
                except ValueError:
                    # Se houver erro na conversão da data, não aplica cor
                    pass
        
        # Configurar cores das tags
        if self.current_theme == "dark":
            self.tree.tag_configure('amarelo', background='#fbbf24', foreground='black')
            self.tree.tag_configure('vermelho', background='#ef4444', foreground='white')
        else:
            self.tree.tag_configure('amarelo', background='#fbbf24', foreground='black')
            self.tree.tag_configure('vermelho', background='#ef4444', foreground='black')
    
    def filter_manage_list(self, tipo):
        """Filtra lista de gerenciamento por busca"""
        search_var = getattr(self, f'{tipo}_search_var', None)
        if not search_var:
            return
        
        search = search_var.get().upper()
        listbox = getattr(self, f'{tipo}_listbox')
        
        # Limpar lista
        for item in listbox.get_children():
            listbox.delete(item)
        
        if tipo == "tecnicos":
            # Buscar por matrícula OU nome
            if search:
                self.cursor.execute('''
                    SELECT id, nome, matricula FROM tecnicos 
                    WHERE UPPER(nome) LIKE ? OR UPPER(matricula) LIKE ?
                    ORDER BY nome
                ''', (f'%{search}%', f'%{search}%'))
            else:
                self.cursor.execute("SELECT id, nome, matricula FROM tecnicos ORDER BY nome")
        else:
            # Buscar por nome/numero
            campo = "numero" if tipo == "kits" else "nome"
            if search:
                self.cursor.execute(f'''
                    SELECT id, {campo} FROM {tipo}
                    WHERE UPPER({campo}) LIKE ?
                    ORDER BY {campo}
                ''', (f'%{search}%',))
            else:
                self.cursor.execute(f"SELECT id, {campo} FROM {tipo} ORDER BY {campo}")
        
        for row in self.cursor.fetchall():
            listbox.insert("", "end", values=row)
    
    def load_manage_data(self, tipo):
        """Carrega dados na lista de gerenciamento"""
        listbox = getattr(self, f'{tipo}_listbox')
        
        # Limpar
        for item in listbox.get_children():
            listbox.delete(item)
        
        # Buscar dados
        if tipo == "tecnicos":
            # Para técnicos, buscar ID, nome E matrícula
            self.cursor.execute("SELECT id, nome, matricula FROM tecnicos ORDER BY nome")
        else:
            campo = "numero" if tipo == "kits" else "nome"
            self.cursor.execute(f"SELECT id, {campo} FROM {tipo} ORDER BY {campo}")
        
        for row in self.cursor.fetchall():
            listbox.insert("", "end", values=row)
    
    def clear_filters(self):
        """Limpa os filtros"""
        self.filter_vars['data'].set("")
        self.filter_vars['tecnico'].set("Todos")
        self.filter_vars['matricula'].set("Todos")
        self.filter_vars['kit'].set("Todos")
        self.filter_vars['local'].set("Todos")
        if hasattr(self, 'matricula_combo'):
            self.update_matricula_combobox("Todos", self.matricula_combo)
        self.load_main_data()
    
    def new_record(self):
        """Abre janela para novo registro"""
        RecordWindow(self, mode="new")
    
    def edit_record(self):
        """Abre janela para editar registro"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para editar")
            return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        RecordWindow(self, mode="edit", record_id=record_id)
    
    def delete_record(self):
        """Exclui registro selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para excluir")
            return
        
        if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
            item = self.tree.item(selected[0])
            record_id = item['values'][0]
            
            self.cursor.execute("DELETE FROM registros WHERE id = ?", (record_id,))
            self.conn.commit()
            self.load_main_data()
            messagebox.showinfo("Sucesso", "Registro excluído com sucesso")
    
    def add_item(self, tipo):
        """Adiciona novo item"""
        if tipo == "tecnicos":
            self.add_tecnico_window()
        elif tipo == "kits":
            self.add_kit_window()
        elif tipo == "locais":
            self.add_local_window()
    
    def add_kit_window(self):
        """Abre janela para adicionar novo kit"""
        add_window = ctk.CTkToplevel(self.root)
        add_window.title("Adicionar Kit")
        add_window.geometry("400x250")
        add_window.grab_set()
        add_window.transient(self.root)
        
        # Centralizar
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - 200
        y = (add_window.winfo_screenheight() // 2) - 125
        add_window.geometry(f"400x250+{x}+{y}")
        
        # Conteúdo
        ctk.CTkLabel(add_window, text="ADICIONAR KIT", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        # Número
        ctk.CTkLabel(add_window, text="Número do Kit:").pack(anchor="w", padx=30, pady=(10,5))
        numero_var = ctk.StringVar()
        numero_entry = ctk.CTkEntry(add_window, textvariable=numero_var, width=340, height=35)
        numero_entry.pack(padx=30, pady=(0,20))
        numero_entry.bind('<KeyRelease>', self.auto_uppercase)
        numero_entry.focus()
        
        def salvar_kit():
            numero = numero_var.get().strip().upper()
            
            if not numero:
                messagebox.showwarning("Aviso", "Preencha o número do kit!")
                return
            
            # Verificar se já existe
            self.cursor.execute("SELECT id FROM kits WHERE numero = ?", (numero,))
            if self.cursor.fetchone():
                messagebox.showerror("Erro", f"Kit {numero} já existe no sistema!")
                return
            
            try:
                self.cursor.execute("INSERT INTO kits (numero) VALUES (?)", (numero,))
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Kit adicionado com sucesso!")
                add_window.destroy()
                self.load_manage_data("kits")
                self.update_filters()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Erro ao adicionar kit!")
                self.conn.rollback()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar: {str(e)}")
                self.conn.rollback()
        
        # Botões
        btn_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="SALVAR", command=salvar_kit,
                     fg_color="#10b981", hover_color="#059669", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="CANCELAR", command=add_window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563", width=150).pack(side="left", padx=5)
    
    def add_local_window(self):
        """Abre janela para adicionar novo local"""
        add_window = ctk.CTkToplevel(self.root)
        add_window.title("Adicionar Local")
        add_window.geometry("400x250")
        add_window.grab_set()
        add_window.transient(self.root)
        
        # Centralizar
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - 200
        y = (add_window.winfo_screenheight() // 2) - 125
        add_window.geometry(f"400x250+{x}+{y}")
        
        # Conteúdo
        ctk.CTkLabel(add_window, text="ADICIONAR LOCAL", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        # Nome
        ctk.CTkLabel(add_window, text="Nome do Local:").pack(anchor="w", padx=30, pady=(10,5))
        nome_var = ctk.StringVar()
        nome_entry = ctk.CTkEntry(add_window, textvariable=nome_var, width=340, height=35)
        nome_entry.pack(padx=30, pady=(0,20))
        nome_entry.bind('<KeyRelease>', self.auto_uppercase)
        nome_entry.focus()
        
        def salvar_local():
            nome = nome_var.get().strip().upper()
            
            if not nome:
                messagebox.showwarning("Aviso", "Preencha o nome do local!")
                return
            
            # Verificar se já existe
            self.cursor.execute("SELECT id FROM locais WHERE nome = ?", (nome,))
            if self.cursor.fetchone():
                messagebox.showerror("Erro", f"Local {nome} já existe no sistema!")
                return
            
            try:
                self.cursor.execute("INSERT INTO locais (nome) VALUES (?)", (nome,))
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Local adicionado com sucesso!")
                add_window.destroy()
                self.load_manage_data("locais")
                self.update_filters()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Erro ao adicionar local!")
                self.conn.rollback()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar: {str(e)}")
                self.conn.rollback()
        
        # Botões
        btn_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="SALVAR", command=salvar_local,
                     fg_color="#10b981", hover_color="#059669", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="CANCELAR", command=add_window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563", width=150).pack(side="left", padx=5)
    
    def add_tecnico_window(self):
        """Abre janela para adicionar novo técnico"""
        add_window = ctk.CTkToplevel(self.root)
        add_window.title("Adicionar Técnico")
        add_window.geometry("400x320")
        add_window.grab_set()
        add_window.transient(self.root)
        
        # Centralizar
        add_window.update_idletasks()
        x = (add_window.winfo_screenwidth() // 2) - 200
        y = (add_window.winfo_screenheight() // 2) - 160
        add_window.geometry(f"400x320+{x}+{y}")
        
        # Conteúdo
        ctk.CTkLabel(add_window, text="ADICIONAR TÉCNICO", 
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        
        # Nome
        ctk.CTkLabel(add_window, text="Nome:").pack(anchor="w", padx=30, pady=(10,5))
        nome_var = ctk.StringVar()
        nome_entry = ctk.CTkEntry(add_window, textvariable=nome_var, width=340, height=35)
        nome_entry.pack(padx=30, pady=(0,15))
        nome_entry.bind('<KeyRelease>', self.auto_uppercase)
        
        # Matrícula
        ctk.CTkLabel(add_window, text="Matrícula:").pack(anchor="w", padx=30, pady=(10,5))
        matricula_var = ctk.StringVar()
        matricula_entry = ctk.CTkEntry(add_window, textvariable=matricula_var, width=340, height=35)
        matricula_entry.pack(padx=30, pady=(0,20))
        matricula_entry.bind('<KeyRelease>', self.auto_uppercase)
        
        def salvar_tecnico():
            nome = nome_var.get().strip().upper()
            matricula = matricula_var.get().strip().upper()
            
            if not nome or not matricula:
                messagebox.showwarning("Aviso", "Preencha todos os campos!")
                return
            
            # Verificar se matrícula já existe
            self.cursor.execute("SELECT id FROM tecnicos WHERE matricula = ?", (matricula,))
            if self.cursor.fetchone():
                messagebox.showerror("Erro", f"Matrícula {matricula} já está em uso!")
                return
            
            try:
                self.cursor.execute(
                    "INSERT INTO tecnicos (nome, matricula) VALUES (?, ?)", 
                    (nome, matricula)
                )
                self.conn.commit()
                messagebox.showinfo("Sucesso", "Técnico adicionado com sucesso!")
                add_window.destroy()
                self.load_manage_data("tecnicos")
                self.update_filters()
            except sqlite3.IntegrityError:
                messagebox.showerror("Erro", "Erro ao adicionar técnico!")
                self.conn.rollback()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao adicionar: {str(e)}")
                self.conn.rollback()
        
        # Botões
        btn_frame = ctk.CTkFrame(add_window, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="SALVAR", command=salvar_tecnico,
                     fg_color="#10b981", hover_color="#059669", width=150).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="CANCELAR", command=add_window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563", width=150).pack(side="left", padx=5)
    
    def edit_item(self, tipo):
        """Edita item selecionado"""
        listbox = getattr(self, f'{tipo}_listbox')
        selection = listbox.selection()
        
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um item para editar!")
            return
        
        item = listbox.item(selection[0])
        item_id = item['values'][0]
        
        if tipo == "tecnicos":
            # Para técnicos, buscar nome E matrícula atuais
            self.cursor.execute("SELECT nome, matricula FROM tecnicos WHERE id = ?", (item_id,))
            result = self.cursor.fetchone()
            if not result:
                return
            
            nome_atual, matricula_atual = result
            
            # Criar janela personalizada para edição
            edit_window = ctk.CTkToplevel(self.root)
            edit_window.title("Editar Técnico")
            edit_window.geometry("450x380")  # Aumentado para garantir visibilidade
            edit_window.grab_set()
            edit_window.transient(self.root)
            
            # Centralizar
            edit_window.update_idletasks()
            x = (edit_window.winfo_screenwidth() // 2) - 225
            y = (edit_window.winfo_screenheight() // 2) - 190
            edit_window.geometry(f"450x380+{x}+{y}")
            
            # Frame com scroll para garantir que tudo apareça
            main_frame = ctk.CTkFrame(edit_window, fg_color="transparent")
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Conteúdo
            ctk.CTkLabel(main_frame, text="EDITAR TÉCNICO", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))
            
            # Nome
            ctk.CTkLabel(main_frame, text="Nome:").pack(anchor="w", padx=10, pady=(10,5))
            nome_var = ctk.StringVar(value=nome_atual)
            nome_entry = ctk.CTkEntry(main_frame, textvariable=nome_var, width=380, height=35)
            nome_entry.pack(padx=10, pady=(0,15))
            nome_entry.bind('<KeyRelease>', self.auto_uppercase)
            
            # Matrícula
            ctk.CTkLabel(main_frame, text="Matrícula:").pack(anchor="w", padx=10, pady=(10,5))
            matricula_var = ctk.StringVar(value=matricula_atual)
            matricula_entry = ctk.CTkEntry(main_frame, textvariable=matricula_var, width=380, height=35)
            matricula_entry.pack(padx=10, pady=(0,20))
            matricula_entry.bind('<KeyRelease>', self.auto_uppercase)
            
            def salvar_edicao():
                novo_nome = nome_var.get().strip().upper()
                nova_matricula = matricula_var.get().strip().upper()
                
                if not novo_nome or not nova_matricula:
                    messagebox.showwarning("Aviso", "Preencha todos os campos!")
                    return
                
                # Verificar se houve alteração
                if novo_nome == nome_atual and nova_matricula == matricula_atual:
                    messagebox.showinfo("Info", "Nenhuma alteração foi feita.")
                    edit_window.destroy()
                    return
                
                # Verificar se matrícula mudou e se nova matrícula já existe
                if nova_matricula != matricula_atual:
                    self.cursor.execute("SELECT id FROM tecnicos WHERE matricula = ?", (nova_matricula,))
                    if self.cursor.fetchone():
                        messagebox.showerror("Erro", f"Matrícula {nova_matricula} já está em uso!")
                        return
                    
                    # Contar quantos registros serão afetados pela mudança de matrícula
                    self.cursor.execute("SELECT COUNT(*) FROM registros WHERE matricula_tecnico = ?", 
                                       (matricula_atual,))
                    total_registros = self.cursor.fetchone()[0]
                    
                    if total_registros > 0:
                        msg = f"A matrícula está sendo alterada de '{matricula_atual}' para '{nova_matricula}'.\n\n"
                        msg += f"Isso afetará {total_registros} registro(s) no banco de dados.\n\n"
                        msg += "Deseja continuar?"
                        
                        if not messagebox.askyesno("Confirmar Alteração de Matrícula", msg):
                            return
                
                try:
                    # Atualizar técnico
                    self.cursor.execute(
                        "UPDATE tecnicos SET nome = ?, matricula = ? WHERE id = ?",
                        (novo_nome, nova_matricula, item_id)
                    )
                    
                    # Se matrícula mudou, atualizar registros que a referenciam
                    if nova_matricula != matricula_atual:
                        self.cursor.execute(
                            "UPDATE registros SET matricula_tecnico = ? WHERE matricula_tecnico = ?",
                            (nova_matricula, matricula_atual)
                        )
                        
                        # Atualizar arquivos JSON se necessário
                        # (JSON usa nome do técnico, não matrícula, mas vamos atualizar para consistência)
                        registros_json = self.update_json_files('matricula_tecnico', matricula_atual, nova_matricula)
                    
                    self.conn.commit()
                    
                    # Mensagem de sucesso
                    if nova_matricula != matricula_atual:
                        msg_sucesso = f"✅ Técnico atualizado com sucesso!\n\n"
                        msg_sucesso += f"📊 Total de registros atualizados: {total_registros}"
                        messagebox.showinfo("Sucesso", msg_sucesso)
                    else:
                        messagebox.showinfo("Sucesso", "Técnico atualizado com sucesso!")
                    
                    edit_window.destroy()
                    self.load_manage_data(tipo)
                    self.update_filters()
                    
                    # Recarregar também a aba de Registros Antigos
                    if hasattr(self, 'archive_tree'):
                        self.load_archive_data()
                    
                except sqlite3.IntegrityError:
                    messagebox.showerror("Erro", f"Matrícula {nova_matricula} já está em uso!")
                    self.conn.rollback()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao atualizar: {str(e)}")
                    self.conn.rollback()
            
            # Botões - garantir que apareçam no main_frame
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(pady=20, expand=False)
            
            ctk.CTkButton(btn_frame, text="SALVAR", command=salvar_edicao,
                         fg_color="#10b981", hover_color="#059669", width=160, height=45,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="CANCELAR", command=edit_window.destroy,
                         fg_color="#6b7280", hover_color="#4b5563", width=160, height=45,
                         font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)
            
        else:
            # Para outros tipos (kits, locais) - janela personalizada COM CAPS AUTOMÁTICO
            valor_atual = item['values'][1]
            
            # Criar janela personalizada
            edit_simple_window = ctk.CTkToplevel(self.root)
            edit_simple_window.title(f"Editar {tipo[:-1].title()}")
            edit_simple_window.geometry("400x250")
            edit_simple_window.grab_set()
            edit_simple_window.transient(self.root)
            
            # Centralizar
            edit_simple_window.update_idletasks()
            x = (edit_simple_window.winfo_screenwidth() // 2) - 200
            y = (edit_simple_window.winfo_screenheight() // 2) - 125
            edit_simple_window.geometry(f"400x250+{x}+{y}")
            
            # Conteúdo
            tipo_singular = "Kit" if tipo == "kits" else "Local"
            ctk.CTkLabel(edit_simple_window, text=f"EDITAR {tipo_singular.upper()}", 
                        font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
            
            # Campo de edição
            label_text = "Número:" if tipo == "kits" else "Nome:"
            ctk.CTkLabel(edit_simple_window, text=label_text).pack(anchor="w", padx=30, pady=(10,5))
            
            valor_var = ctk.StringVar(value=valor_atual)
            valor_entry = ctk.CTkEntry(edit_simple_window, textvariable=valor_var, width=340, height=35)
            valor_entry.pack(padx=30, pady=(0,20))
            valor_entry.bind('<KeyRelease>', self.auto_uppercase)
            valor_entry.focus()
            # Selecionar todo o texto (customtkinter usa select_range)
            edit_simple_window.after(100, lambda: valor_entry.select_range(0, 'end'))
            
            def salvar_edicao_simples():
                novo_valor = valor_var.get().strip().upper()
                
                if not novo_valor:
                    messagebox.showwarning("Aviso", "Preencha o campo!")
                    return
                
                # Verificar se o valor realmente mudou
                if novo_valor == valor_atual:
                    messagebox.showinfo("Info", "Nenhuma alteração foi feita.")
                    edit_simple_window.destroy()
                    return
                
                try:
                    # 1. Verificar se novo valor já existe (para evitar duplicação)
                    campo = "numero" if tipo == "kits" else "nome"
                    self.cursor.execute(f"SELECT id FROM {tipo} WHERE {campo} = ?", (novo_valor,))
                    if self.cursor.fetchone():
                        messagebox.showerror("Erro", f"Este {tipo[:-1]} já existe no sistema!")
                        return
                    
                    # 2. Contar quantos registros serão afetados
                    campo_registro = "num_kit" if tipo == "kits" else "local"
                    self.cursor.execute(f"SELECT COUNT(*) FROM registros WHERE {campo_registro} = ?", 
                                       (valor_atual,))
                    total_registros = self.cursor.fetchone()[0]
                    
                    # 3. Confirmar com o usuário
                    if total_registros > 0:
                        msg = f"Essa alteração afetará {total_registros} registro(s) no banco de dados.\n\n"
                        msg += "ATENÇÃO: Os registros arquivados (JSON) também serão atualizados.\n\n"
                        msg += f"Deseja continuar e alterar '{valor_atual}' para '{novo_valor}'?"
                        
                        if not messagebox.askyesno("Confirmar Alteração", msg):
                            return
                    
                    # 4. Atualizar tabela principal (kits ou locais)
                    self.cursor.execute(f"UPDATE {tipo} SET {campo} = ? WHERE id = ?",
                                      (novo_valor, item_id))
                    
                    # 5. Atualizar TODOS os registros que referenciam o valor antigo
                    self.cursor.execute(f"UPDATE registros SET {campo_registro} = ? WHERE {campo_registro} = ?",
                                      (novo_valor, valor_atual))
                    
                    self.conn.commit()
                    
                    # 6. Atualizar arquivos JSON mensais
                    registros_json = self.update_json_files(campo_registro, valor_atual, novo_valor)
                    
                    # 7. Recarregar dados
                    self.load_manage_data(tipo)
                    self.update_filters()
                    
                    # Recarregar também a aba de Registros Antigos
                    if hasattr(self, 'archive_tree'):
                        self.load_archive_data()
                    
                    # 8. Feedback ao usuário
                    msg_sucesso = f"✅ Atualização concluída com sucesso!\n\n"
                    msg_sucesso += f"📊 Banco de dados: {total_registros} registro(s) atualizado(s)\n"
                    msg_sucesso += f"📁 Arquivos JSON: {registros_json} registro(s) atualizado(s)"
                    messagebox.showinfo("Sucesso", msg_sucesso)
                    
                    edit_simple_window.destroy()
                    
                except sqlite3.IntegrityError:
                    messagebox.showerror("Erro", f"Este {tipo[:-1]} já existe no sistema!")
                    self.conn.rollback()
                except Exception as e:
                    messagebox.showerror("Erro", f"Erro ao atualizar: {str(e)}")
                    self.conn.rollback()
            
            # Botões
            btn_frame = ctk.CTkFrame(edit_simple_window, fg_color="transparent")
            btn_frame.pack(pady=20)
            
            ctk.CTkButton(btn_frame, text="SALVAR", command=salvar_edicao_simples,
                         fg_color="#10b981", hover_color="#059669", width=150).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="CANCELAR", command=edit_simple_window.destroy,
                         fg_color="#6b7280", hover_color="#4b5563", width=150).pack(side="left", padx=5)
    

    def update_json_files(self, campo, old_value, new_value):
        """
        Atualiza todos os arquivos JSON mensais com o novo valor
        
        Args:
            campo: 'tecnico', 'local' ou 'num_kit'
            old_value: Valor antigo (ex: "JOÃO SILVA")
            new_value: Novo valor (ex: "JOÃO CARLOS SILVA")
        
        Returns:
            int: Número total de registros atualizados em todos os arquivos
        """
        arquivos_dir = 'arquivos_mensais'
        total_updated = 0
        
        # Verificar se pasta existe
        if not os.path.exists(arquivos_dir):
            print(f"⚠️ Pasta {arquivos_dir} não existe")
            return 0
        
        # Percorrer todos os arquivos JSON
        json_files = [f for f in os.listdir(arquivos_dir) if f.endswith('.json')]
        
        if not json_files:
            print(f"⚠️ Nenhum arquivo JSON encontrado em {arquivos_dir}")
            return 0
        
        print(f"\n🔄 Atualizando arquivos JSON...")
        print(f"Campo: {campo}")
        print(f"De: {old_value} → Para: {new_value}\n")
        
        for filename in json_files:
            filepath = os.path.join(arquivos_dir, filename)
            
            try:
                # Ler arquivo
                with open(filepath, 'r', encoding='utf-8') as f:
                    registros = json.load(f)
                
                # Contar e atualizar registros
                count_file = 0
                for registro in registros:
                    if registro.get(campo) == old_value:
                        registro[campo] = new_value
                        count_file += 1
                
                # Salvar se houve alteração
                if count_file > 0:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(registros, f, indent=2, ensure_ascii=False)
                    
                    total_updated += count_file
                    print(f"✅ {filename}: {count_file} registro(s) atualizado(s)")
                else:
                    print(f"⚪ {filename}: Nenhuma alteração")
            
            except json.JSONDecodeError:
                print(f"❌ Erro ao ler {filename}: JSON inválido")
                continue
            except Exception as e:
                print(f"❌ Erro ao processar {filename}: {e}")
                continue
        
        print(f"\n📊 Total: {total_updated} registro(s) atualizado(s) em {len(json_files)} arquivo(s)")
        return total_updated
    
    def update_filters(self):
        """Atualiza os filtros com novos dados"""
        self.tecnico_combo.configure(values=self.get_unique_tecnicos())
        self.local_filter.configure(values=["Todos"] + self.get_items("locais"))
        self.kit_filter.configure(values=["Todos"] + self.get_items("kits", "numero"))
        # Atualizar também os filtros da aba de arquivos
        self.update_archive_filters()
    
    
    def check_monthly_archive(self):
        """Verifica se precisa arquivar dados do mês anterior"""
        self.cursor.execute("SELECT valor FROM config WHERE chave = 'ultimo_mes_arquivado'")
        result = self.cursor.fetchone()
        
        mes_atual = datetime.now().strftime("%Y-%m")
        
        if not result or result[0] != mes_atual:
            mes_anterior = (datetime.now().replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
            self.archive_month(mes_anterior)
            
            self.cursor.execute('''
                INSERT OR REPLACE INTO config (chave, valor) 
                VALUES ('ultimo_mes_arquivado', ?)
            ''', (mes_atual,))
            self.conn.commit()
    
    def archive_month(self, mes):
        """Arquiva dados de um mês específico em JSON (backup).
        Os dados permanecem no SQLite como fonte principal de consulta."""
        if not os.path.exists("arquivos_mensais"):
            os.makedirs("arquivos_mensais")
        
        self.cursor.execute('''
            SELECT * FROM registros 
            WHERE strftime('%Y-%m', substr(data_inicio, 7, 4) || '-' || 
                  substr(data_inicio, 4, 2)) = ?
        ''', (mes,))
        
        registros = self.cursor.fetchall()
        
        if registros:
            arquivo = f"arquivos_mensais/registros_{mes}.json"
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(registros, f, indent=4, ensure_ascii=False)
    
    def on_closing(self):
        """Encerramento controlado da aplicação (graceful shutdown).

        Garante que o clique no X SEMPRE finalize o processo, independentemente
        do tempo de execução. Fecha figuras do matplotlib e as conexões de banco
        (com checkpoint do WAL) e encerra o processo. O os._exit final é a
        garantia de que nenhum recurso preso (loops 'after' do Tcl/CustomTkinter,
        backend do matplotlib, conexão WAL, etc.) mantenha o processo vivo.
        """
        if getattr(self, "_closing", False):
            return
        self._closing = True

        # 1. Fechar todas as figuras do matplotlib
        try:
            import matplotlib.pyplot as plt
            plt.close('all')
        except Exception:
            pass

        # 2. Consolidar o WAL e fechar as conexões de banco
        try:
            if getattr(self, "conn", None) is not None:
                try:
                    self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except Exception:
                    pass
                self.conn.close()
        except Exception:
            pass
        try:
            hdb = getattr(self, "history_db", None)
            if hdb is not None and hasattr(hdb, "close"):
                hdb.close()
        except Exception:
            pass

        # 3. Encerrar o loop e destruir a janela
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

        # 4. Garantia final: encerra o processo imediatamente
        os._exit(0)

    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()
        # Fallback caso o loop termine sem passar por on_closing
        try:
            self.conn.close()
        except Exception:
            pass

    def show_record_history(self):
        """Mostra histórico do registro selecionado"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para ver o histórico")
            return
        
        item = self.tree.item(selected[0])
        record_id = item['values'][0]
        HistoryDialog(self.root, self.history_db, record_id)
    
    def show_archive_history(self):
        """Mostra histórico de registro arquivado"""
        selected = self.archive_tree.selection()
        if not selected:
            messagebox.showwarning("Atenção", "Selecione um registro para ver o histórico")
            return
        
        item = self.archive_tree.item(selected[0])
        record_id = item['values'][0]
        HistoryDialog(self.root, self.history_db, record_id)