"""
Gerenciador da Aba de Rankings
Arquivo: views/ranking_manager.py
"""
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from tkcalendar import Calendar
import csv
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as rl_colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from views.widgets.progress_dialog import ProgressDialog
from views.widgets.scrollable_combobox import ScrollableComboBox
from views.widgets.tooltip import Tooltip


class RankingManager:
    """Gerencia a aba de Rankings"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.cursor = main_window.cursor
        self.conn = main_window.conn
        self.ranking_type = "kits"
        self.show_year_accumulated = False
        self.updating_filters = False
        
        # Variáveis de filtro (MÊS E ANO VIGENTE)
        self.filter_vars = {
            'mes': ctk.StringVar(value=str(datetime.now().month).zfill(2)),
            'ano': ctk.StringVar(value=str(datetime.now().year)),
            'data': ctk.StringVar(value='')
        }
        
        # ADICIONAR TRACE
        self.filter_vars['mes'].trace_add('write', lambda *args: self.on_filter_change())
        self.filter_vars['ano'].trace_add('write', lambda *args: self.on_filter_change())
        self.filter_vars['data'].trace_add('write', lambda *args: self.on_filter_change())
    
    def get_available_years(self):
        """Retorna lista de anos que possuem registros"""
        try:
            self.cursor.execute('''
                SELECT DISTINCT substr(data_inicio, 7, 4) as ano
                FROM registros 
                ORDER BY ano DESC
            ''')
            years = [row[0] for row in self.cursor.fetchall() if row[0]]
            
            if not years:
                years = [str(datetime.now().year)]
            
            return years
        except:
            return [str(datetime.now().year)]
    
    def open_calendar(self, date_entry):
        """Abre calendário para seleção de data"""
        calendar_window = ctk.CTkToplevel(self.main_window.root)
        calendar_window.title("Selecionar Data")
        calendar_window.geometry("300x350")
        calendar_window.grab_set()
        calendar_window.transient(self.main_window.root)
        
        # Centralizar
        calendar_window.update_idletasks()
        x = (calendar_window.winfo_screenwidth() // 2) - 150
        y = (calendar_window.winfo_screenheight() // 2) - 175
        calendar_window.geometry(f"300x350+{x}+{y}")
        
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
        
        # Botão selecionar
        btn_frame = ctk.CTkFrame(calendar_window, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        ctk.CTkButton(btn_frame, text="SELECIONAR DATA", 
                     command=set_date,
                     width=200, height=35,
                     fg_color="#1e88e5", hover_color="#1565c0").pack()
    
    def create_ranking_tab(self, parent_tab):
        """Cria interface da aba"""
        # Container principal
        main_container = ctk.CTkFrame(parent_tab, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # BARRA SUPERIOR (ADAPTÁVEL AO TEMA)
        # Light: Cinza claro, Dark: Escuro
        top_bar = ctk.CTkFrame(main_container, height=60, corner_radius=10)
        top_bar.pack(fill="x", pady=(0, 20))
        top_bar.pack_propagate(False)
        
        # Título (ADAPTÁVEL AO TEMA)
        title_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        title_frame.pack(side="left", padx=20)
        
        # Cor do texto adapta ao tema automaticamente
        self.title_label = ctk.CTkLabel(
            title_frame, 
            text="🏆 RANKINGS",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.title_label.pack()
        
        # Botões de exportação
        export_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        export_frame.pack(side="right", padx=20)
        
        ctk.CTkButton(export_frame, text="📄 EXPORTAR PDF",
                     command=self.export_ranking_pdf,
                     width=150, height=35,
                     fg_color="#8b5cf6", hover_color="#7c3aed",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        ctk.CTkButton(export_frame, text="📊 EXPORTAR CSV",
                     command=self.export_ranking_csv,
                     width=150, height=35,
                     fg_color="#10b981", hover_color="#059669",
                     font=ctk.CTkFont(size=12)).pack(side="left", padx=5)
        
        # SEÇÃO DE FILTROS
        filters_container = ctk.CTkFrame(main_container, corner_radius=10)
        filters_container.pack(fill="x", pady=(0, 20))
        
        # Título
        ctk.CTkLabel(filters_container, text="FILTROS",
                    font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=6, pady=(15, 10), padx=20, sticky="w"
        )
        
        # === LINHA 1: Mês, Ano, Data, Botões ===
        
        # Filtro Mês
        ctk.CTkLabel(filters_container, text="Mês:").grid(
            row=1, column=0, padx=(20, 5), pady=10, sticky="w"
        )
        self.mes_filter = ScrollableComboBox(
            filters_container,
            variable=self.filter_vars['mes'],
            values=[''] + [f"{i:02d}" for i in range(1, 13)],
            width=80,
            max_visible_items=6,
            app=self.main_window
        )
        self.mes_filter.grid(row=1, column=0, padx=(55, 10), pady=10)
        
        # Filtro Ano
        ctk.CTkLabel(filters_container, text="Ano:").grid(
            row=1, column=1, padx=(10, 5), pady=10, sticky="w"
        )
        self.ano_filter = ScrollableComboBox(
            filters_container,
            variable=self.filter_vars['ano'],
            values=self.get_available_years(),
            width=90,
            max_visible_items=6,
            app=self.main_window
        )
        self.ano_filter.grid(row=1, column=1, padx=(50, 10), pady=10)
        
        # Filtro Data
        ctk.CTkLabel(filters_container, text="Data:").grid(
            row=1, column=2, padx=(10, 5), pady=10, sticky="w"
        )
        
        # Frame para data + calendário
        date_frame = ctk.CTkFrame(filters_container, fg_color="transparent")
        date_frame.grid(row=1, column=2, padx=(50, 10), pady=10)
        
        self.date_entry = ctk.CTkEntry(
            date_frame,
            textvariable=self.filter_vars['data'],
            placeholder_text="DD/MM/AAAA",
            width=120
        )
        self.date_entry.pack(side="left")
        
        # Botão Calendário
        calendar_btn = ctk.CTkButton(
            date_frame, text="📅",
            width=30, height=28,
            fg_color="#1e88e5", hover_color="#1565c0",
            command=lambda: self.open_calendar(self.date_entry)
        )
        calendar_btn.pack(side="left", padx=(5, 0))
        
        # Botão Ver Acumulado do Ano
        self.acumulado_btn = ctk.CTkButton(
            filters_container, text="📅 ACUMULADO DO ANO",
            command=self.toggle_year_accumulated,
            width=180, height=35,
            fg_color="#059669", hover_color="#047857",
            font=ctk.CTkFont(size=12)
        )
        self.acumulado_btn.grid(row=1, column=3, padx=(10, 10), pady=10)
        
        # Botão Limpar Filtros
        clear_btn = ctk.CTkButton(
            filters_container, text="LIMPAR FILTROS",
            command=self.clear_filters,
            width=130, height=35,
            fg_color="#475569", hover_color="#334155",
            font=ctk.CTkFont(size=12)
        )
        clear_btn.grid(row=1, column=4, pady=10, padx=(10, 20), sticky="e")
        
        # BOTÕES DE TIPO
        buttons_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(buttons_frame, text="Visualizar:",
                    font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=(0, 10))
        
        btn_kits = ctk.CTkButton(buttons_frame, text="📦 Kits",
                                command=lambda: self.switch_ranking_view("kits"),
                                width=120, height=35)
        btn_kits.pack(side="left", padx=5)
        
        btn_tecnicos = ctk.CTkButton(buttons_frame, text="👷 Técnicos",
                                     command=lambda: self.switch_ranking_view("tecnicos"),
                                     width=120, height=35)
        btn_tecnicos.pack(side="left", padx=5)
        
        btn_locais = ctk.CTkButton(buttons_frame, text="📍 Locais",
                                   command=lambda: self.switch_ranking_view("locais"),
                                   width=120, height=35)
        btn_locais.pack(side="left", padx=5)
        
        self.ranking_buttons = {
            "kits": btn_kits,
            "tecnicos": btn_tecnicos,
            "locais": btn_locais
        }
        
        # TABELA
        table_frame = ctk.CTkFrame(main_container)
        table_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        style = ttk.Style()
        style.configure("Ranking.Treeview", rowheight=30)
        
        cols = ("Posição", "Nome", "Matrícula", "Quantidade", "Porcentagem")
        self.ranking_tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                        yscrollcommand=scrollbar.set, height=20,
                                        style="Ranking.Treeview")
        scrollbar.config(command=self.ranking_tree.yview)
        
        # Larguras padrão (Matrícula oculta - view inicial é kits)
        col_widths = {"Posição": 100, "Nome": 400, "Matrícula": 0, "Quantidade": 150, "Porcentagem": 150}
        for col in cols:
            w = col_widths[col]
            self.ranking_tree.column(col, width=w, minwidth=0 if w == 0 else 50, anchor="center", stretch=(w > 0))
            self.ranking_tree.heading(col, text=col, anchor="center")
        
        # Tags medalhas
        self.ranking_tree.tag_configure('gold', background='#FFD700', foreground='#000000')
        self.ranking_tree.tag_configure('silver', background='#C0C0C0', foreground='#000000')
        self.ranking_tree.tag_configure('bronze', background='#CD7F32', foreground='#FFFFFF')
        self.ranking_tree.tag_configure('copper', background='#B87333', foreground='#FFFFFF')
        
        self.ranking_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Carregar inicial
        self.switch_ranking_view("kits")
    
    def on_filter_change(self):
        """Callback quando filtro muda"""
        if self.updating_filters:
            return
            
        if self.show_year_accumulated:
            self.show_year_accumulated = False
            self.acumulado_btn.configure(text="📅 Ver Acumulado do Ano")
        
        self.switch_ranking_view(self.ranking_type)
    
    def toggle_year_accumulated(self):
        """Alterna modo Acumulado"""
        self.show_year_accumulated = not self.show_year_accumulated
        
        if self.show_year_accumulated:
            self.acumulado_btn.configure(text="📊 Ver Filtrado")
        else:
            self.acumulado_btn.configure(text="📅 Ver Acumulado do Ano")
        
        self.switch_ranking_view(self.ranking_type)
    
    def clear_filters(self):
        """Limpa filtros e volta para mês/ano vigente"""
        self.updating_filters = True
        
        # Valores vigentes
        mes_vigente = str(datetime.now().month).zfill(2)
        ano_vigente = str(datetime.now().year)
        
        # ATUALIZAR VARIÁVEIS
        self.filter_vars['mes'].set(mes_vigente)
        self.filter_vars['ano'].set(ano_vigente)
        self.filter_vars['data'].set('')
        
        # FORÇAR ATUALIZAÇÃO VISUAL
        self.mes_filter.entry_var.set(mes_vigente)
        self.ano_filter.entry_var.set(ano_vigente)
        self.date_entry.delete(0, 'end')
        
        # Desativar modo acumulado
        self.show_year_accumulated = False
        self.acumulado_btn.configure(text="📅 Ver Acumulado do Ano")
        
        # Atualizar lista de anos
        self.ano_filter.configure(values=self.get_available_years())
        
        self.updating_filters = False
        
        # Atualizar tabela
        self.switch_ranking_view(self.ranking_type)
    
    def switch_ranking_view(self, tipo):
        """Alterna visualizações"""
        self.ranking_type = tipo
        
        for key, btn in self.ranking_buttons.items():
            if key == tipo:
                btn.configure(fg_color=("#fe0401", "#fe0401"))
            else:
                btn.configure(fg_color=("#3b8ed0", "#1f6aa5"))
        
        if tipo == "kits":
            self.ranking_tree.heading("Nome", text="Kit")
            self.ranking_tree.column("Matrícula", width=0, minwidth=0, stretch=False)
            self.ranking_tree.column("Nome", width=400, stretch=True)
            self.load_ranking_kits()
        elif tipo == "tecnicos":
            self.ranking_tree.heading("Nome", text="Técnico")
            self.ranking_tree.column("Matrícula", width=130, minwidth=50, stretch=True)
            self.ranking_tree.column("Nome", width=280, stretch=True)
            self.load_ranking_tecnicos()
        elif tipo == "locais":
            self.ranking_tree.heading("Nome", text="Local")
            self.ranking_tree.column("Matrícula", width=0, minwidth=0, stretch=False)
            self.ranking_tree.column("Nome", width=400, stretch=True)
            self.load_ranking_locais()
    
    def get_current_records(self):
        """Obtém registros filtrados"""
        query = "SELECT * FROM registros WHERE 1=1"
        params = []
        
        if self.show_year_accumulated:
            ano = self.filter_vars['ano'].get()
            query += " AND substr(data_inicio, 7, 4) = ?"
            params.append(ano)
        else:
            mes = self.filter_vars['mes'].get()
            ano = self.filter_vars['ano'].get()
            data = self.filter_vars['data'].get()
            
            if data and self.main_window.validate_date(data):
                query += " AND data_inicio = ?"
                params.append(data)
            elif mes and ano:
                query += " AND substr(data_inicio, 4, 2) = ? AND substr(data_inicio, 7, 4) = ?"
                params.extend([mes, ano])
        
        query += " ORDER BY id DESC"
        
        self.cursor.execute(query, params)
        return self.cursor.fetchall()
    
    def _build_tecnico_label_map(self):
        """Retorna {matricula: nome_exibicao}. Nomes duplicados ficam 'NOME (MATRICULA)'."""
        try:
            self.cursor.execute("SELECT matricula, nome FROM tecnicos")
            rows = self.cursor.fetchall()
        except Exception:
            return {}
        from collections import Counter
        nome_count = Counter(nome for _, nome in rows)
        label_map = {}
        for matricula, nome in rows:
            if nome_count[nome] > 1:
                label_map[matricula] = f"{nome} ({matricula})"
            else:
                label_map[matricula] = nome
        return label_map

    def load_ranking_kits(self):
        """Carrega ranking de kits"""
        for item in self.ranking_tree.get_children():
            self.ranking_tree.delete(item)
        
        records = self.get_current_records()
        
        kits_dict = {}
        for r in records:
            if len(r) > 4 and r[4]:
                kits_dict[r[4]] = kits_dict.get(r[4], 0) + 1
        
        if not kits_dict:
            self.ranking_tree.insert('', 'end', values=('', 'Nenhum dado encontrado', '', ''))
            return
        
        kits_sorted = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)
        total = sum(kits_dict.values())
        
        medal_tags = ['gold', 'silver', 'bronze', 'copper']
        medal_icons = ['🥇', '🥈', '🥉', '🏅']
        
        for posicao, (kit, qtd) in enumerate(kits_sorted, 1):
            pct = (qtd / total * 100) if total > 0 else 0
            
            if posicao <= 4:
                pos_text = f"{medal_icons[posicao-1]} {posicao}º"
                tag = medal_tags[posicao-1]
            else:
                pos_text = f"{posicao}º"
                tag = ''
            
            self.ranking_tree.insert('', 'end',
                                    values=(pos_text, kit, '', qtd, f"{pct:.1f}%"),
                                    tags=(tag,))
    
    def load_ranking_tecnicos(self):
        """Carrega ranking de técnicos"""
        for item in self.ranking_tree.get_children():
            self.ranking_tree.delete(item)
        
        records = self.get_current_records()
        label_map = self._build_tecnico_label_map()
        
        # Agrega por matrícula para manter contagens corretas
        tecnicos_dict = {}
        for r in records:
            if len(r) > 3 and r[3]:
                mat = r[3]
                tecnicos_dict[mat] = tecnicos_dict.get(mat, 0) + 1
        
        if not tecnicos_dict:
            self.ranking_tree.insert('', 'end', values=('', 'Nenhum dado encontrado', '', '', ''))
            return
        
        tecnicos_sorted = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)
        total = sum(tecnicos_dict.values())
        
        medal_tags = ['gold', 'silver', 'bronze', 'copper']
        medal_icons = ['🥇', '🥈', '🥉', '🏅']
        
        for posicao, (matricula, qtd) in enumerate(tecnicos_sorted, 1):
            pct = (qtd / total * 100) if total > 0 else 0
            nome = label_map.get(matricula, matricula)
            
            if posicao <= 4:
                pos_text = f"{medal_icons[posicao-1]} {posicao}º"
                tag = medal_tags[posicao-1]
            else:
                pos_text = f"{posicao}º"
                tag = ''
            
            self.ranking_tree.insert('', 'end',
                                    values=(pos_text, nome, matricula, qtd, f"{pct:.1f}%"),
                                    tags=(tag,))
    
    def load_ranking_locais(self):
        """Carrega ranking de locais"""
        for item in self.ranking_tree.get_children():
            self.ranking_tree.delete(item)
        
        records = self.get_current_records()
        
        locais_dict = {}
        for r in records:
            if len(r) > 5 and r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        if not locais_dict:
            self.ranking_tree.insert('', 'end', values=('', 'Nenhum dado encontrado', '', ''))
            return
        
        locais_sorted = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)
        total = sum(locais_dict.values())
        
        medal_tags = ['gold', 'silver', 'bronze', 'copper']
        medal_icons = ['🥇', '🥈', '🥉', '🏅']
        
        for posicao, (local, qtd) in enumerate(locais_sorted, 1):
            pct = (qtd / total * 100) if total > 0 else 0
            
            if posicao <= 4:
                pos_text = f"{medal_icons[posicao-1]} {posicao}º"
                tag = medal_tags[posicao-1]
            else:
                pos_text = f"{posicao}º"
                tag = ''
            
            self.ranking_tree.insert('', 'end',
                                    values=(pos_text, local, '', qtd, f"{pct:.1f}%"),
                                    tags=(tag,))
    
    def export_ranking_csv(self):
        """Exporta CSV"""
        try:
            items = []
            for item in self.ranking_tree.get_children():
                values = self.ranking_tree.item(item)['values']
                items.append(values)
            
            if not items or (len(items) == 1 and items[0][1] == 'Nenhum dado encontrado'):
                messagebox.showwarning("Aviso", "Não há dados!")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"ranking_{self.ranking_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            )
            
            if not filename:
                return
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                tipo_nome = {"kits": "Kit", "tecnicos": "Técnico", "locais": "Local"}[self.ranking_type]
                
                if self.ranking_type == "tecnicos":
                    # values: (posicao, nome, matricula, qtd, pct)
                    writer.writerow(["Posição", "Técnico", "Matrícula", "Quantidade", "Porcentagem"])
                    for item in items:
                        writer.writerow([item[0], item[1], item[2], item[3], item[4]])
                else:
                    # values: (posicao, nome, '', qtd, pct) — ignora campo vazio de matrícula
                    writer.writerow(["Posição", tipo_nome, "Quantidade", "Porcentagem"])
                    for item in items:
                        writer.writerow([item[0], item[1], item[3], item[4]])
            
            messagebox.showinfo("Sucesso", "CSV exportado!")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro: {str(e)}")
    
    def export_ranking_pdf(self):
        """Exporta PDF"""
        try:
            items = []
            for item in self.ranking_tree.get_children():
                values = self.ranking_tree.item(item)['values']
                items.append(values)
            
            if not items or (len(items) == 1 and items[0][1] == 'Nenhum dado encontrado'):
                messagebox.showwarning("Aviso", "Não há dados!")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"ranking_{self.ranking_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
            
            if not filename:
                return
            
            # CORRIGIR: Passar main_window.root ao invés de main_window
            progress = ProgressDialog(self.main_window.root, "Gerando PDF", 100)
            progress.update_progress(10, "Preparando...")
            
            doc = SimpleDocTemplate(filename, pagesize=A4,
                                  leftMargin=2*cm, rightMargin=2*cm,
                                  topMargin=2*cm, bottomMargin=2*cm)
            
            elements = []
            styles = getSampleStyleSheet()
            
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=rl_colors.HexColor('#fe0401'),
                spaceAfter=30,
                alignment=TA_CENTER
            )
            
            tipo_nome = {"kits": "Kits", "tecnicos": "Técnicos", "locais": "Locais"}[self.ranking_type]
            elements.append(Paragraph(f"🏆 Ranking de {tipo_nome}", title_style))
            
            filter_info = self.get_filter_description()
            if filter_info:
                info_style = ParagraphStyle('Info', parent=styles['Normal'],
                                           fontSize=10, alignment=TA_CENTER)
                elements.append(Paragraph(filter_info, info_style))
                elements.append(Spacer(1, 0.5*cm))
            
            progress.update_progress(30, "Criando tabela...")
            
            tipo_col = {"kits": "Kit", "tecnicos": "Técnico", "locais": "Local"}[self.ranking_type]
            
            if self.ranking_type == "tecnicos":
                # values: (posicao, nome, matricula, qtd, pct)
                table_data = [["Posição", "Técnico", "Matrícula", "Quantidade", "Porcentagem"]]
                for item in items:
                    table_data.append([item[0], item[1], item[2], item[3], item[4]])
                table = Table(table_data, colWidths=[3*cm, 6*cm, 3*cm, 3*cm, 3*cm])
            else:
                # values: (posicao, nome, '', qtd, pct) — ignora campo vazio de matrícula
                table_data = [["Posição", tipo_col, "Quantidade", "Porcentagem"]]
                for item in items:
                    table_data.append([item[0], item[1], item[3], item[4]])
                table = Table(table_data, colWidths=[3*cm, 8*cm, 3*cm, 3*cm])
            
            table_style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#fe0401')),
                ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), rl_colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, rl_colors.grey),
            ])
            
            for i in range(1, min(5, len(items) + 1)):
                if i == 1:
                    table_style.add('BACKGROUND', (0, i), (-1, i), rl_colors.HexColor('#FFD700'))
                elif i == 2:
                    table_style.add('BACKGROUND', (0, i), (-1, i), rl_colors.HexColor('#C0C0C0'))
                elif i == 3:
                    table_style.add('BACKGROUND', (0, i), (-1, i), rl_colors.HexColor('#CD7F32'))
                elif i == 4:
                    table_style.add('BACKGROUND', (0, i), (-1, i), rl_colors.HexColor('#B87333'))
            
            table.setStyle(table_style)
            elements.append(table)
            
            progress.update_progress(70, "Salvando...")
            doc.build(elements)
            progress.update_progress(100, "Concluído!")
            progress.close()
            
            messagebox.showinfo("Sucesso", "PDF exportado!")
            
        except Exception as e:
            if 'progress' in locals():
                progress.close()
            messagebox.showerror("Erro", f"Erro ao exportar PDF:\n{str(e)}")
    
    def get_filter_description(self):
        """Descrição dos filtros"""
        mes = self.filter_vars['mes'].get()
        ano = self.filter_vars['ano'].get()
        data = self.filter_vars['data'].get()
        
        if self.show_year_accumulated:
            return f"Acumulado do ano: {ano}"
        elif data:
            return f"Data: {data}"
        elif mes and ano:
            meses = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                    'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
            return f"Período: {meses[int(mes)]}/{ano}"
        
        return "Todos os registros"
    
    def refresh_current_view(self):
        """Atualiza visualização"""
        self.ano_filter.configure(values=self.get_available_years())
        self.switch_ranking_view(self.ranking_type)