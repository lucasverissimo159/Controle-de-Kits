"""
Gerenciador da aba de Estatísticas COMPLETA
Contém todos os gráficos, KPIs, exportações
OTIMIZADO: Fechamento correto de figuras matplotlib + Tela de progresso
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog, Toplevel
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
import numpy as np
import plotly.graph_objects as go
from collections import Counter
from plotly.subplots import make_subplots
import tempfile
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from views.widgets.tooltip import Tooltip
from views.widgets.scrollable_combobox import ScrollableComboBox


class StatsManager:
    """Gerencia todas as funcionalidades de estatísticas"""
    
    def __init__(self, app):
        self.app = app
        self.cursor = app.cursor
        self.conn = app.conn
        self.root = app.root
        self.stats_filter_vars = app.stats_filter_vars
        self.current_theme = app.current_theme
        self.stats_container = None
        self.active_figures = []
        self.last_filter_changed = 'mes_ano'  # Rastreia qual filtro foi alterado por último
        self.current_registros = []  # Armazena registros para popup
        self.show_year_accumulated = False  # Modo acumulado do ano
        self.updating_filters = False  # Flag para evitar loop de callbacks
    
    def _build_tecnico_label_map(self):
        """
        Retorna dict {matricula: label_exibicao}.
        Se houver dois técnicos com o mesmo nome, exibe "NOME (MATRÍCULA)".
        """
        try:
            self.cursor.execute("SELECT matricula, nome FROM tecnicos")
            rows = self.cursor.fetchall()
        except Exception:
            return {}

        # Contar quantas vezes cada nome aparece
        from collections import Counter
        nome_count = Counter(nome for _, nome in rows)

        label_map = {}
        for matricula, nome in rows:
            if nome_count[nome] > 1:
                label_map[matricula] = f"{nome} ({matricula})"
            else:
                label_map[matricula] = nome
        return label_map

    def _resolve_tecnico_labels(self, registros):
        """
        Retorna uma lista de labels de técnico para cada registro,
        na mesma ordem de registros. r[3] é a matrícula.
        """
        label_map = self._build_tecnico_label_map()
        return [label_map.get(r[3], r[3]) if r[3] else "" for r in registros]

    def _build_tecnico_dict_by_label(self, registros):
        """
        Agrega contagem de visitas por label de exibição do técnico.
        Retorna dict {label: count}.
        """
        label_map = self._build_tecnico_label_map()
        tecnicos_dict = {}
        for r in registros:
            mat = r[3]
            if mat:
                label = label_map.get(mat, mat)
                tecnicos_dict[label] = tecnicos_dict.get(label, 0) + 1
        return tecnicos_dict

    def get_export_filename_prefix(self):
        """Gera prefixo do nome do arquivo baseado no último filtro alterado"""
        mes = self.stats_filter_vars['mes'].get()
        ano = self.stats_filter_vars['ano'].get()
        data_especifica = self.stats_filter_vars['data'].get()
        
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Usar o último filtro que foi alterado
        if self.last_filter_changed == 'data' and data_especifica and self.validate_date(data_especifica):
            # Converter DD/MM/AAAA para AAAAMMDD
            parts = data_especifica.split('/')
            date_str = f"{parts[2]}{parts[1]}{parts[0]}"
            return f"estatisticas_{date_str}_{timestamp}"
        elif self.last_filter_changed == 'mes_ano' and mes and ano:
            return f"estatisticas_{ano}{mes}_{timestamp}"
        elif mes and ano:
            # Fallback para mês/ano se nenhum filtro específico
            return f"estatisticas_{ano}{mes}_{timestamp}"
        else:
            return f"estatisticas_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def validate_date(self, date_str):
        return self.app.validate_date(date_str)
    
    def format_date_input(self, event):
        return self.app.format_date_input(event)
    
    def open_calendar(self, entry):
        return self.app.open_calendar(entry)
    
    def cleanup_figures(self):
        """Fecha todas as figuras matplotlib ativas"""
        for fig in self.active_figures:
            try:
                plt.close(fig)
            except:
                pass
        self.active_figures.clear()
        plt.close('all')
    
    def create_stats_tab(self, tab):
        """Cria aba de estatísticas com design moderno"""
        tab = tab
        
        main_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title = ctk.CTkLabel(header_frame, text="📊 ESTATÍSTICAS E RELATÓRIOS", 
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=("black"))
        title.pack(side="left")
        
        export_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        export_frame.pack(side="right")
        
        btn_export_png = ctk.CTkButton(export_frame, text="📄 EXPORTAR PDF",
                                       command=self.export_stats_pdf,
                                       fg_color="#8b5cf6", hover_color="#7c3aed",
                                       width=150, height=35)
        btn_export_png.pack(side="left", padx=5)
        
        btn_export_csv = ctk.CTkButton(export_frame, text="📊 EXPORTAR CSV",
                                       command=self.export_stats_csv,
                                       fg_color="#10b981", hover_color="#059669",
                                       width=150, height=35)
        btn_export_csv.pack(side="left", padx=5)
        
        filter_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 20))
        
        filter_title = ctk.CTkLabel(filter_frame, text="FILTROS", 
                                    font=ctk.CTkFont(size=16, weight="bold"))
        filter_title.grid(row=0, column=0, columnspan=4, pady=(15, 10), padx=20, sticky="w")
        
        ctk.CTkLabel(filter_frame, text="Mês:").grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")
        self.stats_mes_filter = ScrollableComboBox(filter_frame, 
                                                   variable=self.stats_filter_vars['mes'],
                                                   values=[f"{i:02d}" for i in range(1, 13)], 
                                                   width=120,
                                                   max_visible_items=6,
                                                   app=self)
        self.stats_mes_filter.grid(row=1, column=0, padx=(70, 20), pady=10)
        
        ctk.CTkLabel(filter_frame, text="Ano:").grid(row=1, column=1, padx=(20, 5), pady=10, sticky="w")
        self.stats_ano_filter = ScrollableComboBox(filter_frame,
                                                   variable=self.stats_filter_vars['ano'],
                                                   values=self.get_available_years_stats(), 
                                                   width=120,
                                                   max_visible_items=6,
                                                   app=self)
        self.stats_ano_filter.grid(row=1, column=1, padx=(65, 20), pady=10)
        
        ctk.CTkLabel(filter_frame, text="Data:").grid(row=1, column=2, padx=(20, 5), pady=10, sticky="w")
        
        date_stats_frame = ctk.CTkFrame(filter_frame, fg_color="transparent")
        date_stats_frame.grid(row=1, column=2, padx=(70, 20), pady=10)
        
        stats_date_entry = ctk.CTkEntry(date_stats_frame, 
                                        textvariable=self.stats_filter_vars['data'], 
                                        placeholder_text="DD/MM/AAAA",
                                        width=110)
        stats_date_entry.pack(side="left")
        stats_date_entry.bind('<KeyRelease>', self.format_date_input)
        
        stats_calendar_btn = ctk.CTkButton(date_stats_frame, text="📅", 
                                          width=30, height=30,
                                          command=lambda: self.open_calendar(stats_date_entry))
        stats_calendar_btn.pack(side="left", padx=(5, 0))
        
        clear_btn = ctk.CTkButton(filter_frame, text="LIMPAR FILTROS", 
                                 command=self.clear_stats_filters,
                                 fg_color="#475569", hover_color="#334155",
                                 width=150, height=35)
        clear_btn.grid(row=1, column=3, pady=(0, 15), padx=20)
        
        # Botão Acumulado do Ano
        self.acumulado_btn = ctk.CTkButton(filter_frame, text="📅 ACUMULADO DO ANO",
                                           command=self.toggle_year_accumulated,
                                           fg_color="#059669", hover_color="#047857",
                                           width=180, height=35)
        self.acumulado_btn.grid(row=1, column=4, pady=(0, 15), padx=(0, 20))
        
        info_label = ctk.CTkLabel(filter_frame, 
                                 text="💡 Estatísticas do mês vigente por padrão. Selecione mês/ano para comparar. Clique nos gráficos para ampliar.",
                                 text_color="#6b7280",
                                 font=ctk.CTkFont(size=11))
        info_label.grid(row=2, column=0, columnspan=4, pady=(0, 15), padx=20, sticky="w")
        
        self.stats_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.stats_container.pack(fill="both", expand=True)
        
        self.update_statistics()
        self.bind_stats_filter_events()

    def bind_stats_filter_events(self):
        self.stats_filter_vars['mes'].trace_add('write', self.on_mes_ano_changed)
        self.stats_filter_vars['ano'].trace_add('write', self.on_mes_ano_changed)
        self.stats_filter_vars['data'].trace_add('write', self.on_data_changed)
    
    def on_mes_ano_changed(self, *args):
        """Callback quando mês ou ano mudam"""
        if self.updating_filters:
            return
        self.last_filter_changed = 'mes_ano'
        # Sair do modo acumulado ao trocar filtros
        if self.show_year_accumulated:
            self.show_year_accumulated = False
            self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO")
        # Limpar filtro de data quando mês/ano são alterados
        if self.stats_filter_vars['data'].get():
            self.stats_filter_vars['data'].set("")
        self.update_statistics()
    
    def on_data_changed(self, *args):
        """Callback quando data específica muda"""
        if self.updating_filters:
            return
        data = self.stats_filter_vars['data'].get()
        if data:  # Só atualiza se data não estiver vazia
            self.last_filter_changed = 'data'
            # Sair do modo acumulado ao trocar filtros
            if self.show_year_accumulated:
                self.show_year_accumulated = False
                self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO")
        self.update_statistics()
    
    # ==================== POPUP DE DESTAQUE ====================
    
    def open_chart_popup(self, chart_type, registros, title):
        """Abre uma janela popup com o gráfico em destaque"""
        popup = Toplevel(self.root)
        popup.title(f"📊 {title}")
        popup.geometry("1280x700")
        popup.configure(bg="#2b2b2b")
        
        # Centralizar janela
        popup.update_idletasks()
        width = popup.winfo_width()
        height = popup.winfo_height()
        x = (popup.winfo_screenwidth() // 2) - (width // 2)
        y = (popup.winfo_screenheight() // 2) - (height // 2)
        popup.geometry(f"+{x}+{y}")
        
        # Frame principal
        main_frame = ctk.CTkFrame(popup, fg_color="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text=title, 
                                   font=ctk.CTkFont(size=20, weight="bold"),
                                   text_color="white")
        title_label.pack(pady=(10, 20))
        
        # Frame do gráfico
        chart_frame = ctk.CTkFrame(main_frame, fg_color="#cfcfcf", corner_radius=15)
        chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Renderizar gráfico baseado no tipo
        self._render_popup_chart(chart_type, registros, chart_frame)
        
        # Botão fechar
        close_btn = ctk.CTkButton(main_frame, text="✕ Fechar", 
                                  command=popup.destroy,
                                  fg_color="#ef4444", hover_color="#dc2626",
                                  width=120, height=35)
        close_btn.pack(pady=(15, 5))
        
        popup.transient(self.root)
        popup.grab_set()
    
    def _render_popup_chart(self, chart_type, registros, parent):
        """Renderiza o gráfico no popup com tamanho maior"""
        if chart_type == "temporal":
            self._popup_temporal(registros, parent)
        elif chart_type == "locais":
            self._popup_bar_chart(registros, parent, "locais", "📍 Locais Visitados", 5)
        elif chart_type == "tecnicos":
            self._popup_bar_chart(registros, parent, "tecnicos", "👥 Visitas por Técnico", 3)
        elif chart_type == "kits_bar":
            self._popup_bar_chart(registros, parent, "kits", "📦 Kits Usados", 4)
        elif chart_type == "duracao":
            self._popup_duracao(registros, parent)
        elif chart_type == "kits_pie":
            self._popup_pie_chart(registros, parent, "kits", "📦 Distribuição de Kits", 4)
        elif chart_type == "tecnicos_pie":
            self._popup_pie_chart(registros, parent, "tecnicos", "👥 Distribuição de Técnicos", 3)
        elif chart_type == "locais_pie":
            self._popup_pie_chart(registros, parent, "locais", "📍 Distribuição de Locais", 5)
        elif chart_type == "top5_tecnicos":
            self._popup_top5(registros, parent, "tecnicos", "🏆 Top 5 Técnicos", 3)
        elif chart_type == "top5_locais":
            self._popup_top5(registros, parent, "locais", "🏆 Top 5 Locais", 5)

    def _popup_temporal(self, registros, parent):
        """Gráfico temporal em popup"""
        datas_dict = {}
        for r in registros:
            if r[1]:
                datas_dict[r[1]] = datas_dict.get(r[1], 0) + 1
        
        if not datas_dict:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        datas_ordenadas = sorted(datas_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        
        if self.show_year_accumulated:
            # Agrupar por mês — exibe total do mês (sem acumulado)
            meses_dict = {}
            for d in datas_ordenadas:
                mes_ano = d[3:]  # "MM/AAAA"
                meses_dict[mes_ano] = meses_dict.get(mes_ano, 0) + datas_dict[d]
            eixo_x = sorted(meses_dict.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores = [meses_dict[m] for m in eixo_x]
            ylabel = 'Visitas por Mês'
        else:
            eixo_x = datas_ordenadas
            valores = [datas_dict[d] for d in datas_ordenadas]
            ylabel = 'Visitas'
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        max_y = max(valores) if valores else 1
        
        line, = ax.plot(range(len(eixo_x)), valores, color='#fe0401', linewidth=3, 
                marker='o', markersize=10, markerfacecolor='#fe0401')
        ax.fill_between(range(len(eixo_x)), valores, alpha=0.3, color='#fe0401')
        
        for i, (x, y) in enumerate(zip(range(len(eixo_x)), valores)):
            ax.text(x, y + max_y*0.03, str(y), ha='center', va='bottom', 
                   fontsize=11, fontweight='bold')
        
        ax.set_ylim(0, max_y * 1.15)
        ax.set_xticks(range(len(eixo_x)))
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=10)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        _valores = valores
        _datas = eixo_x
        _acumulado = self.show_year_accumulated
        
        # Hover
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                cont, ind = line.contains(event)
                if cont:
                    idx = ind["ind"][0]
                    annot.xy = (idx, _valores[idx])
                    label = "Visitas do Mês" if _acumulado else "Visitas"
                    annot.set_text(f"{_datas[idx]}\n{label}: {_valores[idx]}")
                    annot.get_bbox_patch().set_facecolor('#fe0401')
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_bar_chart(self, registros, parent, tipo, titulo, idx):
        """Gráfico de barras genérico em popup - TODOS os dados"""
        if tipo == "tecnicos":
            data_dict = self._build_tecnico_dict_by_label(registros)
        else:
            data_dict = {}
            for r in registros:
                if len(r) > idx and r[idx]:
                    data_dict[r[idx]] = data_dict.get(r[idx], 0) + 1
        
        if not data_dict:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        nomes = [d[0] for d in sorted_data]
        valores = [d[1] for d in sorted_data]
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.bar(range(len(nomes)), valores, color=colors, width=0.7, edgecolor='white', linewidth=1.5)
        
        max_y = max(valores) if valores else 1
        ax.set_ylim(0, max_y * 1.15)
        
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_y*0.02,
                   str(valor), ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        ax.set_xticks(range(len(nomes)))
        ax.set_xticklabels(nomes, rotation=45, ha='right', fontsize=9)
        ax.set_ylabel('Quantidade', fontsize=12)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.tick_params(left=False)
        
        # Hover
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height())
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        annot.set_text(f"{nomes[i]}\nQtd: {valores[i]} ({pct:.1f}%)")
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_duracao(self, registros, parent):
        """Gráfico de duração em popup - TODOS os dados"""
        duracoes_por_local = {}
        for r in registros:
            if r[2] and r[6] and r[7]:
                try:
                    inicio = datetime.strptime(f"{r[1]} {r[6]}", "%d/%m/%Y %H:%M")
                    fim = datetime.strptime(f"{r[2]} {r[7]}", "%d/%m/%Y %H:%M")
                    duracao = (fim - inicio).total_seconds() / 3600
                    local = r[5]
                    if local not in duracoes_por_local:
                        duracoes_por_local[local] = []
                    duracoes_por_local[local].append(duracao)
                except:
                    pass
        
        if not duracoes_por_local:
            ctk.CTkLabel(parent, text="Sem dados completos").pack(pady=100)
            return
        
        medias = {local: np.mean(durs) for local, durs in duracoes_por_local.items()}
        medias_sorted = sorted(medias.items(), key=lambda x: x[1], reverse=True)
        locais = [m[0] for m in medias_sorted]
        valores = [round(m[1], 1) for m in medias_sorted]
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(locais)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(locais)), valores, color=colors, height=0.7, edgecolor='white', linewidth=1.5)
        
        max_x = max(valores) if valores else 1
        ax.set_xlim(0, max_x * 1.15)
        
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_x*0.01, bar.get_y() + bar.get_height()/2,
                   f'{valor}h', ha='left', va='center', fontsize=10, fontweight='bold')
        
        ax.set_yticks(range(len(locais)))
        ax.set_yticklabels(locais, fontsize=9)
        ax.set_xlabel('Horas', fontsize=12)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        
        # Hover
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_width(), bar.get_y() + bar.get_height()/2)
                        annot.set_text(f"{locais[i]}\nDuração: {valores[i]}h")
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_pie_chart(self, registros, parent, tipo, titulo, idx):
        """Gráfico de pizza genérico em popup - TODOS os dados"""
        if tipo == "tecnicos":
            data_dict = self._build_tecnico_dict_by_label(registros)
        else:
            data_dict = {}
            for r in registros:
                if len(r) > idx and r[idx]:
                    data_dict[r[idx]] = data_dict.get(r[idx], 0) + 1
        
        if not data_dict:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        sorted_data = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [d[0] for d in sorted_data]
        valores = [d[1] for d in sorted_data]
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        colors = []
        for i in range(n_colors):
            ratio = i / max(n_colors - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90, pctdistance=0.75,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(10)
            autotext.set_fontweight('bold')
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        # Hover
        annot = ax.annotate("", xy=(0,0), xytext=(0,0), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    cont, _ = wedge.contains(event)
                    if cont:
                        annot.xy = (event.xdata, event.ydata)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        annot.set_text(f"{labels[i]}\nQtd: {valores[i]} ({pct:.1f}%)")
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def _popup_top5(self, registros, parent, tipo, titulo, idx):
        """Gráfico Top 5 em popup"""
        if tipo == "tecnicos":
            data_dict = self._build_tecnico_dict_by_label(registros)
        else:
            data_dict = {}
            for r in registros:
                if len(r) > idx and r[idx]:
                    data_dict[r[idx]] = data_dict.get(r[idx], 0) + 1
        
        top5 = sorted(data_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top5:
            ctk.CTkLabel(parent, text="Sem dados").pack(pady=100)
            return
        
        nomes = [t[0] for t in top5]
        valores = [t[1] for t in top5]
        
        fig, ax = plt.subplots(figsize=(12, 7), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(nomes)), valores, color=colors, height=0.6, edgecolor='white', linewidth=1.5)
        
        max_val = max(valores)
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val*0.02, bar.get_y() + bar.get_height()/2,
                    str(valor), ha='left', va='center', fontsize=12, fontweight='bold')
        
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes, fontsize=11)
        ax.set_xlim(0, max_val * 1.2)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        ax.invert_yaxis()
        
        # Hover
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_width(), bar.get_y() + bar.get_height()/2)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        annot.set_text(f"{nomes[i]}\nVisitas: {valores[i]} ({pct:.1f}%)")
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
    

    def get_available_years_stats(self):
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
    
    def toggle_year_accumulated(self):
        """Alterna entre modo filtrado e acumulado do ano"""
        self.show_year_accumulated = not self.show_year_accumulated
        if self.show_year_accumulated:
            self.acumulado_btn.configure(text="📊 VER FILTRADO")
        else:
            self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO")
        self.update_statistics()

    def clear_stats_filters(self):
        self.updating_filters = True
        self.stats_filter_vars['mes'].set(str(datetime.now().month).zfill(2))
        self.stats_filter_vars['ano'].set(str(datetime.now().year))
        self.stats_filter_vars['data'].set("")
        # Desativar modo acumulado
        self.show_year_accumulated = False
        self.acumulado_btn.configure(text="📅 ACUMULADO DO ANO")
        self.updating_filters = False
        self.update_statistics()


    def create_matplotlib_kits_bar_chart(self, registros, parent):
        """Gráfico de barras - Kits Usados (TODOS os dados + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="📦 Kits Usados",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        # Contar kits - TODOS
        kits_dict = {}
        for r in registros:
            if len(r) > 4 and r[4]:
                kits_dict[r[4]] = kits_dict.get(r[4], 0) + 1
        
        if not kits_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        # TODOS os kits ordenados
        kits = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)
        nomes = [k[0] for k in kits]
        valores = [k[1] for k in kits]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.bar(range(len(nomes)), valores, color=colors, width=0.7, edgecolor='white', linewidth=1.5)
        
        max_y = max(valores) if valores else 1
        ax.set_ylim(0, max_y * 1.15)
        
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_y*0.02,
                    str(valor), ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xticks(range(len(nomes)))
        ax.set_xticklabels(nomes, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Quantidade', fontsize=9)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(left=False)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height())
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\nQtd: {valores[i]} ({pct:.1f}%)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.9)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("kits_bar", registros, "📦 Kits Usados"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("kits_bar", registros, "📦 Kits Usados"))

    def create_matplotlib_kits_pie_chart(self, registros, parent):
        """Gráfico de pizza - Distribuição de Kits (TODOS + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="📦 Distribuição de Kits",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        # Contar kits - TODOS
        kits_dict = {}
        for r in registros:
            if len(r) > 4 and r[4]:
                kits_dict[r[4]] = kits_dict.get(r[4], 0) + 1
        
        if not kits_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        # TODOS os kits
        kits_sorted = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [k[0] for k in kits_sorted]
        valores = [k[1] for k in kits_sorted]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        colors = []
        for i in range(n_colors):
            ratio = i / max(n_colors - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.85,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(8)
            text.set_fontweight('normal')
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(0,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    cont, ind = wedge.contains(event)
                    if cont:
                        annot.xy = (event.xdata, event.ydata)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"$\\mathbf{{{labels[i]}}}$\n■ $\\mathbf{{{pct:.1f}\\%}}$: {valores[i]}"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.95)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("kits_pie", registros, "📦 Distribuição de Kits"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("kits_pie", registros, "📦 Distribuição de Kits"))

    def create_matplotlib_tecnicos_pie_chart(self, registros, parent):
        """Gráfico de pizza - Distribuição de Técnicos (TODOS + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="👥 Distribuição de Técnicos",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        # Contar técnicos - TODOS
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        if not tecnicos_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        labels = list(tecnicos_dict.keys())
        valores = list(tecnicos_dict.values())
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        colors = []
        for i in range(n_colors):
            ratio = i / max(n_colors - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.85,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(8)
            text.set_fontweight('normal')
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(0,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    cont, ind = wedge.contains(event)
                    if cont:
                        annot.xy = (event.xdata, event.ydata)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"$\\mathbf{{{labels[i]}}}$\n■ $\\mathbf{{{pct:.1f}\\%}}$: {valores[i]}"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.95)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("tecnicos_pie", registros, "👥 Distribuição de Técnicos"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("tecnicos_pie", registros, "👥 Distribuição de Técnicos"))

    def create_matplotlib_locais_pie_chart(self, registros, parent):
        """Gráfico de pizza - Distribuição de Locais (TODOS + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="📍 Distribuição de Locais",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        # Contar locais - TODOS
        locais_dict = {}
        for r in registros:
            if len(r) > 5 and r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        if not locais_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        labels = list(locais_dict.keys())
        valores = list(locais_dict.values())
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        colors = []
        for i in range(n_colors):
            ratio = i / max(n_colors - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.85,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(8)
            text.set_fontweight('normal')
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(0,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, wedge in enumerate(wedges):
                    cont, ind = wedge.contains(event)
                    if cont:
                        annot.xy = (event.xdata, event.ydata)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"$\\mathbf{{{labels[i]}}}$\n■ $\\mathbf{{{pct:.1f}\\%}}$: {valores[i]}"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.95)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("locais_pie", registros, "📍 Distribuição de Locais"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("locais_pie", registros, "📍 Distribuição de Locais"))

    def create_matplotlib_top5_tecnicos_chart(self, registros, parent):
        """Gráfico Top 5 Técnicos (hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="🏆 Top 5 Técnicos",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        top_tecnicos = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top_tecnicos:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        nomes = [t[0] for t in top_tecnicos]
        valores = [t[1] for t in top_tecnicos]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(nomes)), valores, color=colors,
                       height=0.6, edgecolor='white', linewidth=1.5)
        
        max_val = max(valores)
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val*0.02, bar.get_y() + bar.get_height()/2,
                    str(valor), ha='left', va='center', fontsize=9, fontweight='bold')
        
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes, fontsize=8)
        ax.set_xlim(0, max_val * 1.2)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.tick_params(bottom=False)
        ax.invert_yaxis()
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_width(), bar.get_y() + bar.get_height()/2)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\nVisitas: {valores[i]} ({pct:.1f}%)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.9)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("top5_tecnicos", registros, "🏆 Top 5 Técnicos"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("top5_tecnicos", registros, "🏆 Top 5 Técnicos"))

    def create_matplotlib_top5_locais_chart(self, registros, parent):
        """Gráfico Top 5 Locais (hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="🏆 Top 5 Locais",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        locais_dict = {}
        for r in registros:
            if len(r) > 5 and r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        top_locais = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top_locais:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        nomes = [l[0] for l in top_locais]
        valores = [l[1] for l in top_locais]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(nomes)), valores, color=colors,
                       height=0.6, edgecolor='white', linewidth=1.5)
        
        max_val = max(valores)
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_width() + max_val*0.02, bar.get_y() + bar.get_height()/2,
                    str(valor), ha='left', va='center', fontsize=9, fontweight='bold')
        
        ax.set_yticks(range(len(nomes)))
        ax.set_yticklabels(nomes, fontsize=8)
        ax.set_xlim(0, max_val * 1.2)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.tick_params(bottom=False)
        ax.invert_yaxis()
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_width(), bar.get_y() + bar.get_height()/2)
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\nVisitas: {valores[i]} ({pct:.1f}%)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.9)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("top5_locais", registros, "🏆 Top 5 Locais"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("top5_locais", registros, "🏆 Top 5 Locais"))

    def export_stats_pdf(self):
        """Exporta estatísticas como PDF - OTIMIZADO com progresso"""
        from views.widgets.progress_dialog import ProgressDialog
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile=f"{self.get_export_filename_prefix()}.pdf"
            )
            
            if not filename:
                return
            
            mes = self.stats_filter_vars['mes'].get()
            ano = self.stats_filter_vars['ano'].get()
            data_especifica = self.stats_filter_vars['data'].get()
            
            query = "SELECT * FROM registros WHERE 1=1"
            params = []
            
            if self.show_year_accumulated:
                if ano:
                    query += " AND substr(data_inicio, 7, 4) = ?"
                    params.append(ano)
            elif data_especifica and self.validate_date(data_especifica):
                query += " AND data_inicio = ?"
                params.append(data_especifica)
            elif mes and ano:
                query += " AND substr(data_inicio, 4, 2) = ? AND substr(data_inicio, 7, 4) = ?"
                params.extend([mes, ano])
            
            self.cursor.execute(query, params)
            registros = self.cursor.fetchall()
            
            if not registros:
                messagebox.showwarning("Aviso", "Nenhum registro encontrado para exportar")
                return
            
            progress = ProgressDialog(self.root, "Gerando PDF...", total_steps=14)
            
            try:
                progress.update_progress(1, "Inicializando PDF...")
                
                c = canvas.Canvas(filename, pagesize=landscape(A4))
                page_width, page_height = landscape(A4)
                margin = 0.5 * inch
                
                # PÁGINA 1: TÍTULO E KPIs
                c.setFont("Helvetica-Bold", 24)
                c.drawString(margin, page_height - margin, "Estatísticas - Sistema de Controle de Kits")
                
                c.setFont("Helvetica", 12)
                if self.show_year_accumulated:
                    periodo = f"Período: {ano if ano else str(datetime.now().year)}"
                elif data_especifica:
                    periodo = f"Data: {data_especifica}"
                else:
                    periodo = f"Período: {mes}/{ano}"
                c.drawString(margin, page_height - margin - 25, periodo)
                
                c.setFont("Helvetica", 10)
                c.drawString(margin, page_height - margin - 45, 
                            f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
                current_y = page_height - margin - 90
                
                progress.update_progress(2, "Gerando KPIs...")
                
                c.setFont("Helvetica-Bold", 18)
                c.drawString(margin, current_y, "📊 Indicadores Principais (KPIs)")
                current_y -= 30
                
                total_visitas = len(registros)
                concluidos = sum(1 for r in registros if r[2] and r[7])
                tecnicos_unicos = len(set([r[3] for r in registros if r[3]]))
                locais_unicos = len(set([r[5] for r in registros if r[5]]))
                taxa_conclusao = int((concluidos / total_visitas * 100)) if total_visitas > 0 else 0
                
                kpis = [
                    ("Total de Visitas", str(total_visitas), "#ec4899"),
                    ("Visitas Concluídas", str(concluidos), "#10b981"),
                    ("Técnicos Ativos", str(tecnicos_unicos), "#3b82f6"),
                    ("Locais Visitados", str(locais_unicos), "#f59e0b"),
                    ("Taxa de Conclusão", f"{taxa_conclusao}%", "#8b5cf6")
                ]
                
                card_width = (page_width - 2*margin - 40) / 5
                card_height = 60
                card_x = margin
                
                for titulo, valor, cor in kpis:
                    cor_rgb = tuple(int(cor[i:i+2], 16)/255 for i in (1, 3, 5))
                    c.setFillColorRGB(*cor_rgb)
                    c.roundRect(card_x, current_y - card_height, card_width, card_height, 10, fill=1)
                    c.setFillColorRGB(1, 1, 1)
                    c.setFont("Helvetica", 9)
                    c.drawCentredString(card_x + card_width/2, current_y - 18, titulo)
                    c.setFont("Helvetica-Bold", 24)
                    c.drawCentredString(card_x + card_width/2, current_y - 45, valor)
                    card_x += card_width + 10
                
                c.setFillColorRGB(0, 0, 0)
                current_y -= card_height + 40
                
                # MÉTRICAS DE PERFORMANCE
                progress.update_progress(3, "Gerando métricas de performance...")
                
                c.setFont("Helvetica-Bold", 18)
                c.drawString(margin, current_y, "📈 Métricas de Performance")
                current_y -= 25
                
                # Função para interpolar cores entre vermelho e amarelo
                def get_color_gradient(index, total_count):
                    if total_count == 1:
                        return "#fe0401"
                    
                    # Interpolação entre #fe0401 (vermelho) e #f5b618 (amarelo)
                    ratio = index / (total_count - 1)
                    
                    # Componentes RGB iniciais e finais
                    r1, g1, b1 = 0xfe, 0x04, 0x01  # vermelho
                    r2, g2, b2 = 0xf5, 0xb6, 0x18  # amarelo
                    
                    # Calcular componentes interpolados
                    r = int(r1 + (r2 - r1) * ratio)
                    g = int(g1 + (g2 - g1) * ratio)
                    b = int(b1 + (b2 - b1) * ratio)
                    
                    return f"#{r:02x}{g:02x}{b:02x}"
                
                tecnicos_dict = self._build_tecnico_dict_by_label(registros)
                
                # Ordenar TODOS os técnicos
                todos_tecnicos = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)
                
                metricas = [("Taxa de Conclusão", concluidos, total_visitas, "#10b981")]
                
                # Adicionar todos os técnicos com cores gradientes
                for idx, (nome, qtd) in enumerate(todos_tecnicos):
                    cor = get_color_gradient(idx, len(todos_tecnicos))
                    metricas.append((f"Técnico: {nome}", qtd, total_visitas, cor))
                
                bar_width = page_width - 2*margin - 100
                bar_height = 20
                
                for nome, qtd, total_val, cor in metricas:
                    # Verificar se precisa criar nova página
                    if current_y - bar_height - 35 < margin:
                        c.showPage()
                        current_y = page_height - margin
                        c.setFont("Helvetica-Bold", 18)
                        c.drawString(margin, current_y, "📈 Métricas de Performance (continuação)")
                        current_y -= 25
                    
                    percentual = qtd / total_val if total_val > 0 else 0
                    cor_rgb = tuple(int(cor[i:i+2], 16)/255 for i in (1, 3, 5))
                    
                    c.setFont("Helvetica-Bold", 10)
                    c.setFillColorRGB(0, 0, 0)
                    c.drawString(margin, current_y - 5, nome)
                    
                    c.setFont("Helvetica", 10)
                    c.drawRightString(page_width - margin, current_y - 5, f"{qtd}/{total_val} ({int(percentual*100)}%)")
                    
                    current_y -= 15
                    
                    c.setFillColorRGB(0.9, 0.9, 0.9)
                    c.roundRect(margin, current_y - bar_height, bar_width, bar_height, 5, fill=1)
                    
                    c.setFillColorRGB(*cor_rgb)
                    if percentual > 0:
                        c.roundRect(margin, current_y - bar_height, bar_width * percentual, bar_height, 5, fill=1)
                    
                    current_y -= bar_height + 15
                
                c.setFillColorRGB(0, 0, 0)
                
                # GRÁFICOS
                graficos = [
                    ("📈 Evolução Temporal de Visitas", self.render_temporal_chart_to_image, 4),
                    ("📍 Locais Visitados", self.render_locais_chart_to_image, 5),
                    ("👥 Visitas por Técnico", self.render_tecnicos_chart_to_image, 6),
                    ("📦 Kits Usados", self.render_kits_bar_to_image, 7),
                    ("⏱️ Duração Média de Visitas", self.render_duracao_chart_to_image, 8),
                    ("📦 Distribuição de Kits", self.render_kits_pie_to_image, 9),
                    ("👥 Distribuição de Técnicos", self.render_tecnicos_pie_to_image, 10),
                    ("📍 Distribuição de Locais", self.render_locais_pie_to_image, 11),
                    ("🏆 Top 5 Técnicos", self.render_top5_tecnicos_to_image, 12),
                    ("🏆 Top 5 Locais", self.render_top5_locais_to_image, 13)
                ]
                
                i = 0
                while i < len(graficos):
                    titulo, render_func, step = graficos[i]
                    progress.update_progress(step, f"Gerando gráfico: {titulo}...")
                    
                    try:
                        # Verificar se é Top 5 e tem próximo também Top 5
                        is_top5_tec = "Top 5 Técnicos" in titulo
                        is_top5_loc = "Top 5 Locais" in titulo
                        
                        if is_top5_tec and i+1 < len(graficos) and "Top 5 Locais" in graficos[i+1][0]:
                            # Renderizar os dois Top 5 juntos
                            img_path_tec = render_func(registros)
                            
                            titulo_loc, render_func_loc, step_loc = graficos[i+1]
                            progress.update_progress(step_loc, f"Gerando gráfico: {titulo_loc}...")
                            img_path_loc = render_func_loc(registros)
                            
                            if img_path_tec and img_path_loc and os.path.exists(img_path_tec) and os.path.exists(img_path_loc):
                                from PIL import Image as PILImage
                                
                                with PILImage.open(img_path_tec) as img:
                                    img_width, img_height = img.size
                                
                                aspect_ratio = img_width / img_height
                                target_width = page_width - (2 * margin)
                                target_height = target_width / aspect_ratio
                                
                                # Verificar se cabem os dois (2x target_height + espaço entre)
                                total_height = (2 * target_height) + 80
                                if current_y - total_height < margin:
                                    c.showPage()
                                    current_y = page_height - margin
                                
                                # Título único "Top 5"
                                c.setFont("Helvetica-Bold", 16)
                                c.drawString(margin, current_y, "🏆 Top 5")
                                current_y -= 25
                                
                                # Desenhar Top 5 Técnicos
                                c.drawImage(img_path_tec, margin, current_y - target_height,
                                        width=target_width, height=target_height)
                                current_y -= (target_height + 20)
                                
                                # Desenhar Top 5 Locais
                                c.drawImage(img_path_loc, margin, current_y - target_height,
                                        width=target_width, height=target_height)
                                current_y -= (target_height + 40)
                                
                                try:
                                    os.unlink(img_path_tec)
                                    os.unlink(img_path_loc)
                                except:
                                    pass
                            
                            i += 2  # Pular os dois
                            continue
                        
                        # Gráfico normal (não Top 5 ou Top 5 sem par)
                        img_path = render_func(registros)
                        
                        if img_path and os.path.exists(img_path):
                            from PIL import Image as PILImage
                            
                            with PILImage.open(img_path) as img:
                                img_width, img_height = img.size
                            
                            aspect_ratio = img_width / img_height
                            target_width = page_width - (2 * margin)
                            target_height = target_width / aspect_ratio
                            
                            if current_y - target_height - 50 < margin:
                                c.showPage()
                                current_y = page_height - margin
                            
                            c.setFont("Helvetica-Bold", 16)
                            c.drawString(margin, current_y, titulo)
                            current_y -= 25
                            
                            c.drawImage(img_path, margin, current_y - target_height,
                                    width=target_width, height=target_height)
                            
                            current_y -= (target_height + 40)
                            
                            try:
                                os.unlink(img_path)
                            except:
                                pass
                            
                    except Exception as e:
                        print(f"Erro ao renderizar {titulo}: {e}")
                    
                    i += 1
                
                progress.update_progress(10, "Finalizando PDF...")
                c.save()
                
                self.cleanup_figures()
                
                progress.close()
                messagebox.showinfo("Sucesso", f"PDF exportado para:\n{filename}")
                
            except Exception as e:
                progress.close()
                self.cleanup_figures()
                raise e
            
        except Exception as e:
            self.cleanup_figures()
            messagebox.showerror("Erro", f"Erro ao exportar PDF: {str(e)}")

    def render_temporal_chart_to_image(self, registros):
        """Renderiza gráfico temporal como imagem"""
        datas_dict = {}
        for r in registros:
            if r[1]:
                datas_dict[r[1]] = datas_dict.get(r[1], 0) + 1
        
        if not datas_dict:
            return None

        if self.show_year_accumulated:
            # Agrupar por mês
            meses_dict = {}
            for d, v in datas_dict.items():
                mes_ano = d[3:]  # "MM/AAAA"
                meses_dict[mes_ano] = meses_dict.get(mes_ano, 0) + v
            eixo_x = sorted(meses_dict.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores = [meses_dict[m] for m in eixo_x]
            titulo_grafico = "<b>📈 Evolução de Visitas por Mês (Ano)</b>"
            ylabel = "Visitas do Mês"
        else:
            eixo_x = sorted(datas_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
            valores = [datas_dict[d] for d in eixo_x]
            titulo_grafico = "<b>📈 Evolução Temporal de Visitas</b>"
            ylabel = "Visitas"
            
        max_y = max(valores) * 1.25
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eixo_x, y=valores,
            mode='lines+markers+text',
            text=[f"<b>{v}</b>" for v in valores],
            textposition='top center',
            textfont=dict(size=14, color="#000000"),
            line=dict(color='#fe0401', width=3),
            marker=dict(size=10, color='#fe0401'),
            fill='tozeroy',
            fillcolor='rgba(254, 4, 1, 0.2)'
        ))
        
        num_pontos = len(eixo_x)
        padding = 0.8
        
        fig.update_layout(
            title=dict(text=titulo_grafico, font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=80, r=80, t=80, b=100),
            yaxis=dict(range=[0, max_y]),
            xaxis=dict(tickangle=45, range=[-padding, num_pontos - 1 + padding], tickmode='array',
                      tickvals=list(range(num_pontos)), ticktext=eixo_x)
        )
        
        fig.data[0].x = list(range(num_pontos))
        
        img_path = os.path.join(tempfile.gettempdir(), f"chart_temporal_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path

    def render_locais_chart_to_image(self, registros):
        """Renderiza gráfico de locais como imagem - TODOS os dados"""
        locais_dict = {}
        for r in registros:
            if r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        if not locais_dict:
            return None
            
        # TODOS os locais
        locais = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)
        nomes = [l[0] for l in locais]
        valores = [l[1] for l in locais]
        max_y = max(valores) * 1.20
        
        n_items = len(nomes)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=nomes, y=valores,
            marker=dict(color=colors, cornerradius=15),
            text=[f"<b>{v}</b>" for v in valores],
            textposition='outside',
            textfont=dict(size=14, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>📍 Locais Visitados</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=50, r=50, t=80, b=120),
            yaxis=dict(range=[0, max_y])
        )
        
        img_path = os.path.join(tempfile.gettempdir(), f"chart_locais_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path

    def render_tecnicos_chart_to_image(self, registros):
        """Renderiza gráfico de técnicos como imagem - TODOS os dados"""
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        if not tecnicos_dict:
            return None
            
        # TODOS os técnicos
        tecnicos = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)
        nomes = [t[0] for t in tecnicos]
        valores = [t[1] for t in tecnicos]
        max_y = max(valores) * 1.20
        
        n_items = len(nomes)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=nomes, y=valores,
            marker=dict(color=colors, cornerradius=15),
            text=[f"<b>{v}</b>" for v in valores],
            textposition='outside',
            textfont=dict(size=14, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>👥 Visitas por Técnico</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=50, r=50, t=80, b=120),
            yaxis=dict(range=[0, max_y])
        )
        
        img_path = os.path.join(tempfile.gettempdir(), f"chart_tecnicos_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path

    def render_kits_chart_to_image(self, registros):
        """Renderiza gráfico de kits como imagem"""
        kits_dict = {}
        for r in registros:
            if r[4]:
                kits_dict[r[4]] = kits_dict.get(r[4], 0) + 1
        
        if not kits_dict:
            return None
            
        kits = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [k[0] for k in kits]
        valores = [k[1] for k in kits]
        
        colors = [f'rgb({int(254 + (245-254)*i/7)},{int(4 + (182-4)*i/7)},{int(1 + (24-1)*i/7)})' 
                for i in range(len(labels))]
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=labels, values=valores,
            marker=dict(colors=colors),
            hole=0.3,
            textinfo='percent',
            textfont=dict(size=14, color='black', family='Arial Black'),
            insidetextfont=dict(size=12, color='black', family='Arial Black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>🖥️ Distribuição de Kits</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=50, r=50, t=80, b=50)
        )
        
        img_path = os.path.join(tempfile.gettempdir(), f"chart_kits_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path

    def render_duracao_chart_to_image(self, registros):
        """Renderiza gráfico de duração - TODOS os dados"""
        duracoes = {}
        for r in registros:
            if r[2] and r[6] and r[7]:
                try:
                    inicio = datetime.strptime(f"{r[1]} {r[6]}", "%d/%m/%Y %H:%M")
                    fim = datetime.strptime(f"{r[2]} {r[7]}", "%d/%m/%Y %H:%M")
                    duracao = (fim - inicio).total_seconds() / 3600
                    local = r[5]
                    if local not in duracoes:
                        duracoes[local] = []
                    duracoes[local].append(duracao)
                except:
                    pass
        
        if not duracoes:
            return None
            
        medias = {k: np.mean(v) for k, v in duracoes.items()}
        # TODOS os locais
        sorted_medias = sorted(medias.items(), key=lambda x: x[1], reverse=True)
        locais = [m[0] for m in sorted_medias]
        valores = [round(m[1], 1) for m in sorted_medias]
        max_x = max(valores) * 1.20
        
        n_items = len(locais)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=valores, y=locais,
            orientation='h',
            marker=dict(color=colors, cornerradius=15),
            text=[f"<b>{v}h</b>" for v in valores],
            textposition='outside',
            textfont=dict(size=14, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>⏱️ Duração Média de Visitas (por Local)</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=180, r=100, t=80, b=50),
            xaxis=dict(range=[0, max_x])
        )
        
        img_path = os.path.join(tempfile.gettempdir(), f"chart_duracao_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path

    def render_top5_chart_to_image(self, registros):
        """Renderiza painel top 5 como imagem"""
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        locais_dict = {}
        
        for r in registros:
            if r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        top_tec = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        top_loc = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        if not top_tec and not top_loc:
            return None
        
        fig = make_subplots(rows=1, cols=2, subplot_titles=("<b>Top 5 Técnicos</b>", "<b>Top 5 Locais</b>"))
        
        if top_tec:
            nomes_tec = [t[0] for t in top_tec]
            valores_tec = [t[1] for t in top_tec]
            max_tec = max(valores_tec) * 1.20
            
            fig.add_trace(go.Bar(
                x=valores_tec, y=nomes_tec,
                orientation='h',
                marker=dict(color='#fe0401', cornerradius=15),
                text=[f"<b>{v}</b>" for v in valores_tec],
                textposition='outside',
                textfont=dict(size=14, color='black')
            ), row=1, col=1)
            
            fig.update_xaxes(range=[0, max_tec], row=1, col=1)
        
        if top_loc:
            nomes_loc = [l[0] for l in top_loc]
            valores_loc = [l[1] for l in top_loc]
            max_loc = max(valores_loc) * 1.20
            
            fig.add_trace(go.Bar(
                x=valores_loc, y=nomes_loc,
                orientation='h',
                marker=dict(color='#f5b618', cornerradius=15),
                text=[f"<b>{v}</b>" for v in valores_loc],
                textposition='outside',
                textfont=dict(size=14, color='black')
            ), row=1, col=2)
            
            fig.update_xaxes(range=[0, max_loc], row=1, col=2)
        
        fig.update_layout(
            title=dict(text="<b>🏆 Top 5 Rankings</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=150, r=150, t=100, b=50),
            showlegend=False
        )
        
        img_path = os.path.join(tempfile.gettempdir(), f"chart_top5_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path
    

    def render_kits_bar_to_image(self, registros):
        """Renderiza gráfico de Kits Usados (barras) - TODOS os dados"""
        kits_dict = {}
        for r in registros:
            if r[4]:
                kits_dict[r[4]] = kits_dict.get(r[4], 0) + 1
        
        if not kits_dict:
            return None
            
        # TODOS os kits
        kits = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [k[0] for k in kits]
        valores = [k[1] for k in kits]
        max_y = max(valores) * 1.20
        
        n_items = len(labels)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=labels, y=valores,
            marker=dict(color=colors, cornerradius=15),
            text=[f"<b>{v}</b>" for v in valores],
            textposition='outside',
            textfont=dict(size=14, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>📦 Kits Usados</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=450,
            margin=dict(l=50, r=50, t=80, b=120),
            yaxis=dict(range=[0, max_y])
        )
        
        import tempfile, os
        from datetime import datetime
        img_path = os.path.join(tempfile.gettempdir(), f"chart_kits_bar_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=450)
        return img_path

    def render_kits_pie_to_image(self, registros):
        """Renderiza gráfico de pizza - Distribuição de Kits (PIZZA, não donut) - TODOS + legenda com %"""
        kits_dict = {}
        for r in registros:
            if r[4]:
                kits_dict[r[4]] = kits_dict.get(r[4], 0) + 1
        
        if not kits_dict:
            return None
            
        kits = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)
        labels = [k[0] for k in kits]
        valores = [k[1] for k in kits]
        total = sum(valores)
        
        n_items = len(labels)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        # Criar labels para legenda com nome e percentual
        legend_labels = [f"{labels[i]} - {valores[i]/total*100:.1f}%" for i in range(len(labels))]
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=legend_labels, 
            values=valores,
            marker=dict(colors=colors),
            hole=0,  # Pizza (não donut)
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=11, color='black'),
            insidetextfont=dict(size=10, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>📦 Distribuição de Kits</b>", font=dict(size=18, color='black'), x=0.5),
            width=1200, height=500,
            margin=dict(l=50, r=350, t=80, b=50),
            showlegend=True,
            legend=dict(x=1.02, y=0.5, font=dict(size=11), 
                       title=dict(text="<b>Kit - Percentual</b>", font=dict(size=12)))
        )
        
        import tempfile, os
        from datetime import datetime
        img_path = os.path.join(tempfile.gettempdir(), f"chart_kits_pie_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1200, height=500)
        return img_path

    def render_tecnicos_pie_to_image(self, registros):
        """Renderiza gráfico de pizza - Distribuição de Técnicos (PIZZA, não donut) - TODOS + legenda com %"""
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        if not tecnicos_dict:
            return None
            
        labels = list(tecnicos_dict.keys())
        valores = list(tecnicos_dict.values())
        total = sum(valores)
        
        n_items = len(labels)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        legend_labels = [f"{labels[i]} - {valores[i]/total*100:.1f}%" for i in range(len(labels))]
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=legend_labels, 
            values=valores,
            marker=dict(colors=colors),
            hole=0,  # Pizza (não donut)
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=11, color='black'),
            insidetextfont=dict(size=10, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>👥 Distribuição de Técnicos</b>", font=dict(size=18, color='black'), x=0.5),
            width=1200, height=500,
            margin=dict(l=50, r=350, t=80, b=50),
            showlegend=True,
            legend=dict(x=1.02, y=0.5, font=dict(size=11),
                       title=dict(text="<b>Técnico - Percentual</b>", font=dict(size=12)))
        )
        
        import tempfile, os
        from datetime import datetime
        img_path = os.path.join(tempfile.gettempdir(), f"chart_tecnicos_pie_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1200, height=500)
        return img_path

    def render_locais_pie_to_image(self, registros):
        """Renderiza gráfico de pizza - Distribuição de Locais (PIZZA, não donut) - TODOS + legenda com %"""
        locais_dict = {}
        for r in registros:
            if r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        if not locais_dict:
            return None
            
        labels = list(locais_dict.keys())
        valores = list(locais_dict.values())
        total = sum(valores)
        
        n_items = len(labels)
        colors = [f'rgb({int(254 + (245-254)*i/max(n_items-1,1))},{int(4 + (182-4)*i/max(n_items-1,1))},{int(1 + (24-1)*i/max(n_items-1,1))})' 
                for i in range(n_items)]
        
        legend_labels = [f"{labels[i]} - {valores[i]/total*100:.1f}%" for i in range(len(labels))]
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=legend_labels, 
            values=valores,
            marker=dict(colors=colors),
            hole=0,  # Pizza (não donut)
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=11, color='black'),
            insidetextfont=dict(size=10, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>📍 Distribuição de Locais</b>", font=dict(size=18, color='black'), x=0.5),
            width=1200, height=500,
            margin=dict(l=50, r=350, t=80, b=50),
            showlegend=True,
            legend=dict(x=1.02, y=0.5, font=dict(size=11),
                       title=dict(text="<b>Local - Percentual</b>", font=dict(size=12)))
        )
        
        import tempfile, os
        from datetime import datetime
        img_path = os.path.join(tempfile.gettempdir(), f"chart_locais_pie_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1200, height=500)
        return img_path

    def render_top5_tecnicos_to_image(self, registros):
        """Renderiza gráfico Top 5 Técnicos"""
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        if not tecnicos_dict:
            return None
            
        top = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        nomes = [t[0] for t in top]
        valores = [t[1] for t in top]
        max_x = max(valores) * 1.20
        
        colors = [f'rgb({int(254 + (245-254)*i/4)},{int(4 + (182-4)*i/4)},{int(1 + (24-1)*i/4)})' 
                for i in range(len(nomes))]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=valores, y=nomes,
            orientation='h',
            marker=dict(color=colors, cornerradius=15),
            text=[f"<b>{v}</b>" for v in valores],
            textposition='outside',
            textfont=dict(size=14, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>🏆 Top 5 Técnicos</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=300,
            margin=dict(l=150, r=50, t=80, b=50),
            xaxis=dict(range=[0, max_x])
        )
        
        import tempfile, os
        from datetime import datetime
        img_path = os.path.join(tempfile.gettempdir(), f"chart_top5_tec_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=300)
        return img_path

    def render_top5_locais_to_image(self, registros):
        """Renderiza gráfico Top 5 Locais"""
        locais_dict = {}
        for r in registros:
            if r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        if not locais_dict:
            return None
            
        top = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        nomes = [l[0] for l in top]
        valores = [l[1] for l in top]
        max_x = max(valores) * 1.20
        
        colors = [f'rgb({int(254 + (245-254)*i/4)},{int(4 + (182-4)*i/4)},{int(1 + (24-1)*i/4)})' 
                for i in range(len(nomes))]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=valores, y=nomes,
            orientation='h',
            marker=dict(color=colors, cornerradius=15),
            text=[f"<b>{v}</b>" for v in valores],
            textposition='outside',
            textfont=dict(size=14, color='black')
        ))
        
        fig.update_layout(
            title=dict(text="<b>🏆 Top 5 Locais</b>", font=dict(size=18, color='black'), x=0.5),
            width=1000, height=300,
            margin=dict(l=150, r=50, t=80, b=50),
            xaxis=dict(range=[0, max_x])
        )
        
        import tempfile, os
        from datetime import datetime
        img_path = os.path.join(tempfile.gettempdir(), f"chart_top5_loc_{datetime.now().strftime('%H%M%S%f')}.png")
        fig.write_image(img_path, width=1000, height=300)
        return img_path

    def export_stats_csv(self):
        """Exporta estatísticas como Excel formatado (.xlsx)"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx"), ("CSV", "*.csv")],
                initialfile=f"{self.get_export_filename_prefix()}.xlsx"
            )
            
            if not filename:
                return
            
            mes = self.stats_filter_vars['mes'].get()
            ano = self.stats_filter_vars['ano'].get()
            data_especifica = self.stats_filter_vars['data'].get()
            
            query = "SELECT * FROM registros WHERE 1=1"
            params = []
            
            if self.show_year_accumulated:
                if ano:
                    query += " AND substr(data_inicio, 7, 4) = ?"
                    params.append(ano)
            elif data_especifica and self.validate_date(data_especifica):
                query += " AND data_inicio = ?"
                params.append(data_especifica)
            elif mes and ano:
                query += " AND substr(data_inicio, 4, 2) = ? AND substr(data_inicio, 7, 4) = ?"
                params.extend([mes, ano])
            
            self.cursor.execute(query, params)
            registros = self.cursor.fetchall()
            
            # Montar mapa matricula -> nome de exibicao para resolver tecnicos
            label_map = self._build_tecnico_label_map()

            wb = Workbook()
            ws = wb.active
            ws.title = "Estatísticas"

            # Linha de período
            if self.show_year_accumulated:
                periodo_texto = f"Período: {ano if ano else str(datetime.now().year)}"
            elif data_especifica:
                periodo_texto = f"Data: {data_especifica}"
            elif mes and ano:
                meses_nomes = ['', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
                               'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
                periodo_texto = f"Período: {meses_nomes[int(mes)]}/{ano}"
            else:
                periodo_texto = "Todos os registros"
            ws.append([periodo_texto])
            ws.append([f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}"])
            ws.append([])

            headers = ['ID', 'Data Início', 'Data Fim', 'Matrícula', 'Técnico',
                       'Nº Kit', 'Local', 'Horário Início', 'Horário Fim']
            ws.append(headers)

            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")

            for registro in registros:
                # registro: (id, data_inicio, data_fim, matricula_tecnico, num_kit, local, horario_inicio, horario_fim)
                matricula = registro[3] or ""
                nome_tecnico = label_map.get(matricula, matricula)
                linha = (
                    registro[0],   # ID
                    registro[1],   # Data Início
                    registro[2],   # Data Fim
                    matricula,     # Matrícula (nova coluna)
                    nome_tecnico,  # Técnico (nome resolvido)
                    registro[4],   # Nº Kit
                    registro[5],   # Local
                    registro[6],   # Horário Início
                    registro[7],   # Horário Fim
                )
                ws.append(linha)

            # Ajustar largura das colunas corretamente (converte tudo para str)
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        cell_len = len(str(cell.value)) if cell.value is not None else 0
                        if cell_len > max_length:
                            max_length = cell_len
                    except Exception:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length + 4, 50)

            wb.save(filename)
            messagebox.showinfo("Sucesso", f"Dados exportados para:\n{filename}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar: {str(e)}")
    
    def update_statistics(self):
        """Atualiza as estatísticas com design moderno"""
        self.cleanup_figures()
        
        for widget in self.stats_container.winfo_children():
            widget.destroy()
        
        try:
            mes = self.stats_filter_vars['mes'].get()
            ano = self.stats_filter_vars['ano'].get()
            data_especifica = self.stats_filter_vars['data'].get()
            
            query = "SELECT * FROM registros WHERE 1=1"
            params = []
            
            if self.show_year_accumulated:
                # Modo acumulado: buscar todos os registros do ano selecionado
                if ano:
                    query += " AND substr(data_inicio, 7, 4) = ?"
                    params.append(ano)
            elif data_especifica and self.validate_date(data_especifica):
                query += " AND data_inicio = ?"
                params.append(data_especifica)
            elif mes and ano:
                query += " AND substr(data_inicio, 4, 2) = ? AND substr(data_inicio, 7, 4) = ?"
                params.extend([mes, ano])
            
            self.cursor.execute(query, params)
            registros = self.cursor.fetchall()
            
            if not registros:
                ctk.CTkLabel(self.stats_container, 
                            text="🔭 Nenhum registro encontrado para o período selecionado",
                            font=ctk.CTkFont(size=16)).pack(pady=100)
                return
            
            # KPIs MODERNOS NO TOPO
            kpis_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            kpis_frame.pack(fill="x", pady=(0, 25))
            self.create_modern_kpis(kpis_frame, registros)
            
            # LINHA 1: Evolução Temporal + Locais Visitados
            row1_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row1_frame.pack(fill="x", pady=10)
            
            temporal_frame = ctk.CTkFrame(row1_frame, corner_radius=15)
            temporal_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_temporal_chart(registros, temporal_frame)
            
            locais_frame = ctk.CTkFrame(row1_frame, corner_radius=15)
            locais_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_locais_chart(registros, locais_frame)
            
            # LINHA 2: Visitas por Técnico + Kits Usados (novo - barras)
            row2_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row2_frame.pack(fill="x", pady=10)
            
            tecnicos_frame = ctk.CTkFrame(row2_frame, corner_radius=15)
            tecnicos_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_tecnicos_chart(registros, tecnicos_frame)
            
            kits_bar_frame = ctk.CTkFrame(row2_frame, corner_radius=15)
            kits_bar_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_kits_bar_chart(registros, kits_bar_frame)
            
            # LINHA 3: Duração Média + Distribuição de Kits (novo - pizza)
            row3_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row3_frame.pack(fill="x", pady=10)
            
            duracao_frame = ctk.CTkFrame(row3_frame, corner_radius=15)
            duracao_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_duracao_chart(registros, duracao_frame)
            
            kits_pie_frame = ctk.CTkFrame(row3_frame, corner_radius=15)
            kits_pie_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_kits_pie_chart(registros, kits_pie_frame)
            
            # LINHA 4: Distribuição de Técnicos (pizza) + Distribuição de Locais (pizza)
            row4_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row4_frame.pack(fill="x", pady=10)
            
            tecnicos_pie_frame = ctk.CTkFrame(row4_frame, corner_radius=15)
            tecnicos_pie_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_tecnicos_pie_chart(registros, tecnicos_pie_frame)
            
            locais_pie_frame = ctk.CTkFrame(row4_frame, corner_radius=15)
            locais_pie_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_locais_pie_chart(registros, locais_pie_frame)
            
            # LINHA 5: Top 5 Técnicos + Top 5 Locais
            row5_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row5_frame.pack(fill="x", pady=10)
            
            top5_tec_frame = ctk.CTkFrame(row5_frame, corner_radius=15)
            top5_tec_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_top5_tecnicos_chart(registros, top5_tec_frame)
            
            top5_loc_frame = ctk.CTkFrame(row5_frame, corner_radius=15)
            top5_loc_frame.pack(side="left", fill="both", expand=True, padx=8)
            self.create_matplotlib_top5_locais_chart(registros, top5_loc_frame)

            # Métricas de Performance
            row6_frame = ctk.CTkFrame(self.stats_container, fg_color="transparent")
            row6_frame.pack(fill="x", pady=10)
            self.create_progress_charts(registros, row6_frame)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar estatísticas: {str(e)}")

    def create_matplotlib_temporal_chart(self, registros, parent):
        """Gráfico de linha temporal embutido (hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        if self.show_year_accumulated:
            chart_title = "📈 Evolução de Visitas por Mês (Ano)"
        else:
            chart_title = "📈 Evolução Temporal de Visitas"
        
        title = ctk.CTkLabel(frame, text=chart_title,
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        datas_dict = {}
        for r in registros:
            data = r[1]
            if data:
                datas_dict[data] = datas_dict.get(data, 0) + 1
        
        if not datas_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        datas_ordenadas = sorted(datas_dict.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
        
        if self.show_year_accumulated:
            # Agrupar por mês — exibe total do mês (sem acumulado)
            meses_dict = {}
            for d in datas_ordenadas:
                mes_ano = d[3:]  # "MM/AAAA"
                meses_dict[mes_ano] = meses_dict.get(mes_ano, 0) + datas_dict[d]
            eixo_x = sorted(meses_dict.keys(), key=lambda x: datetime.strptime(x, "%m/%Y"))
            valores = [meses_dict[m] for m in eixo_x]
            ylabel = 'Visitas por Mês'
        else:
            eixo_x = datas_ordenadas
            valores = [datas_dict[d] for d in datas_ordenadas]
            ylabel = 'Visitas'
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='none')
        self.active_figures.append(fig)
        
        max_y = max(valores) if valores else 1
        
        line, = ax.plot(range(len(eixo_x)), valores, color='#fe0401', linewidth=3, 
                marker='o', markersize=8, markerfacecolor='#fe0401')
        ax.fill_between(range(len(eixo_x)), valores, alpha=0.3, color='#fe0401')
        
        for i, (x, y) in enumerate(zip(range(len(eixo_x)), valores)):
            ax.text(x, y + max_y*0.03, str(y), ha='center', va='bottom', 
                   fontsize=9, fontweight='bold', color="#030000")
        
        ax.set_ylim(0, max_y * 1.15)
        ax.set_xticks(range(len(eixo_x)))
        ax.set_xticklabels(eixo_x, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        _valores = valores
        _datas = eixo_x
        _acumulado = self.show_year_accumulated
        
        def hover(event):
            if event.inaxes == ax:
                cont, ind = line.contains(event)
                if cont:
                    idx = ind["ind"][0]
                    annot.xy = (idx, _valores[idx])
                    label = "Visitas do Mês" if _acumulado else "Visitas"
                    text = f"{_datas[idx]}\n{label}: {_valores[idx]}"
                    annot.set_text(text)
                    annot.get_bbox_patch().set_facecolor('#fe0401')
                    annot.get_bbox_patch().set_alpha(0.9)
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                    return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup — passa o modo acumulado para o popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("temporal", registros, chart_title))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("temporal", registros, chart_title))

    def create_matplotlib_locais_chart(self, registros, parent):
        """Gráfico de barras verticais - Locais (TODOS + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="📍 Locais Visitados",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        locais_dict = {}
        for r in registros:
            local = r[5]
            if local:
                locais_dict[local] = locais_dict.get(local, 0) + 1
        
        if not locais_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        # TODOS os locais
        locais_sorted = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)
        nomes = [l[0] for l in locais_sorted]
        valores = [l[1] for l in locais_sorted]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.bar(range(len(nomes)), valores, color=colors, width=0.7, edgecolor='white', linewidth=1.5)
        
        max_y = max(valores) if valores else 1
        ax.set_ylim(0, max_y * 1.15)
        
        for i, (bar, valor) in enumerate(zip(bars, valores)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_y*0.02,
                   str(valor), ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xticks(range(len(nomes)))
        ax.set_xticklabels(nomes, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Visitas', fontsize=9)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(left=False)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height())
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\nVisitas: {valores[i]} ({pct:.1f}%)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.9)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("locais", registros, "📍 Locais Visitados"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("locais", registros, "📍 Locais Visitados"))

    def create_matplotlib_tecnicos_chart(self, registros, parent):
        """Gráfico de barras verticais - Técnicos (TODOS + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="👥 Visitas por Técnico",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        if not tecnicos_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        # TODOS os técnicos
        tecnicos_sorted = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)
        nomes = [t[0] for t in tecnicos_sorted]
        valores = [t[1] for t in tecnicos_sorted]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(nomes)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.bar(range(len(nomes)), valores, color=colors, width=0.7, edgecolor='white', linewidth=1.5)
        
        max_y = max(valores) if valores else 1
        ax.set_ylim(0, max_y * 1.15)
        
        for i, (bar, valor) in enumerate(zip(bars, valores)):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max_y*0.02,
                   str(valor), ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax.set_xticks(range(len(nomes)))
        ax.set_xticklabels(nomes, rotation=45, ha='right', fontsize=8)
        ax.set_ylabel('Visitas', fontsize=9)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_color('#cccccc')
        ax.tick_params(left=False)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_x() + bar.get_width()/2, bar.get_height())
                        total = sum(valores)
                        pct = (valores[i] / total * 100) if total > 0 else 0
                        text = f"{nomes[i]}\nVisitas: {valores[i]} ({pct:.1f}%)"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.9)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("tecnicos", registros, "👥 Visitas por Técnico"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("tecnicos", registros, "👥 Visitas por Técnico"))

    def create_matplotlib_kits_chart(self, registros, parent):
        """Gráfico de pizza - Distribuição de Kits"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="🖥️ Distribuição de Kits",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        kits_dict = {}
        for r in registros:
            kit = r[4]
            if kit:
                kits_dict[kit] = kits_dict.get(kit, 0) + 1
        
        if not kits_dict:
            ctk.CTkLabel(frame, text="Sem dados").pack(pady=50)
            return
        
        kits_sorted = sorted(kits_dict.items(), key=lambda x: x[1], reverse=True)[:8]
        labels = [k[0] for k in kits_sorted]
        valores = [k[1] for k in kits_sorted]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_colors = len(labels)
        colors = []
        for i in range(n_colors):
            ratio = i / max(n_colors - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        wedges, texts, autotexts = ax.pie(valores, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           pctdistance=0.85,
                                           wedgeprops=dict(edgecolor='white', linewidth=2))
        
        for text in texts:
            text.set_fontsize(8)
            text.set_fontweight('normal')
        for autotext in autotexts:
            autotext.set_color('black')
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
        
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def create_matplotlib_duracao_chart(self, registros, parent):
        """Gráfico de barras horizontais - Duração Média (TODOS + hover + click)"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401",
                            cursor="hand2")
        frame.pack(side="left", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="⏱️ Duração Média de Visitas",
                           font=ctk.CTkFont(size=14, weight="bold"))
        title.pack(pady=(15, 5))
        
        duracoes_por_local = {}
        for r in registros:
            if r[2] and r[6] and r[7]:
                try:
                    inicio = datetime.strptime(f"{r[1]} {r[6]}", "%d/%m/%Y %H:%M")
                    fim = datetime.strptime(f"{r[2]} {r[7]}", "%d/%m/%Y %H:%M")
                    duracao = (fim - inicio).total_seconds() / 3600
                    local = r[5]
                    if local not in duracoes_por_local:
                        duracoes_por_local[local] = []
                    duracoes_por_local[local].append(duracao)
                except:
                    pass
        
        if not duracoes_por_local:
            ctk.CTkLabel(frame, text="Sem dados completos").pack(pady=50)
            return
        
        medias = {local: np.mean(durs) for local, durs in duracoes_por_local.items()}
        # TODOS os locais
        medias_sorted = sorted(medias.items(), key=lambda x: x[1], reverse=True)
        locais = [m[0] for m in medias_sorted]
        valores = [round(m[1], 1) for m in medias_sorted]
        
        fig, ax = plt.subplots(figsize=(6, 3), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        n_bars = len(locais)
        colors = []
        for i in range(n_bars):
            ratio = i / max(n_bars - 1, 1)
            r = (254 + (245 - 254) * ratio) / 255
            g = (4 + (182 - 4) * ratio) / 255
            b = (1 + (24 - 1) * ratio) / 255
            colors.append((r, g, b))
        
        bars = ax.barh(range(len(locais)), valores, color=colors, height=0.7, edgecolor='white', linewidth=1.5)
        
        max_x = max(valores) if valores else 1
        ax.set_xlim(0, max_x * 1.15)
        
        for i, (bar, valor) in enumerate(zip(bars, valores)):
            ax.text(bar.get_width() + max_x*0.01, bar.get_y() + bar.get_height()/2,
                   f'{valor}h', ha='left', va='center', fontsize=9, fontweight='bold')
        
        ax.set_yticks(range(len(locais)))
        ax.set_yticklabels(locais, fontsize=8)
        ax.set_xlabel('Horas', fontsize=9)
        ax.set_facecolor('#cfcfcf')
        fig.patch.set_facecolor('#cfcfcf')
        
        ax.grid(False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_visible(False)
        ax.tick_params(bottom=False)
        
        # Hover tooltip
        annot = ax.annotate("", xy=(0,0), xytext=(-50,0),
                            textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="white", alpha=0.9),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
        
        def hover(event):
            if event.inaxes == ax:
                for i, bar in enumerate(bars):
                    cont, _ = bar.contains(event)
                    if cont:
                        annot.xy = (bar.get_width(), bar.get_y() + bar.get_height()/2)
                        text = f"{locais[i]}\nDuração Média: {valores[i]}h"
                        annot.set_text(text)
                        annot.get_bbox_patch().set_facecolor(colors[i])
                        annot.get_bbox_patch().set_alpha(0.9)
                        annot.set_visible(True)
                        fig.canvas.draw_idle()
                        return
            annot.set_visible(False)
            fig.canvas.draw_idle()
        
        fig.canvas.mpl_connect("motion_notify_event", hover)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Click para abrir popup
        frame.bind("<Button-1>", lambda e: self.open_chart_popup("duracao", registros, "⏱️ Duração Média de Visitas"))
        canvas_widget.bind("<Button-1>", lambda e: self.open_chart_popup("duracao", registros, "⏱️ Duração Média de Visitas"))

    def create_matplotlib_top5_chart(self, registros, parent):
        """Painel com Top 5 Técnicos e Top 5 Locais"""
        frame = ctk.CTkFrame(parent, corner_radius=20, border_width=2, border_color="#fe0401")
        frame.pack(side="right", fill="both", expand=True, padx=0)
        
        title = ctk.CTkLabel(frame, text="🏆 Top 5 Rankings",
                           font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(15, 10))
        
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        locais_dict = {}
        
        for r in registros:
            if r[5]:
                locais_dict[r[5]] = locais_dict.get(r[5], 0) + 1
        
        top_tecnicos = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        top_locais = sorted(locais_dict.items(), key=lambda x: x[1], reverse=True)[:5]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6, 4), facecolor='#cfcfcf')
        self.active_figures.append(fig)
        
        if top_tecnicos:
            nomes_tec = [t[0] for t in top_tecnicos]
            valores_tec = [t[1] for t in top_tecnicos]
            max_tec = max(valores_tec) if valores_tec else 1
            
            bars1 = ax1.barh(range(len(nomes_tec)), valores_tec, color='#fe0401', 
                            height=0.6, edgecolor='white', linewidth=1.5)
            ax1.set_xlim(0, max_tec * 1.15)
            
            for i, (bar, valor) in enumerate(zip(bars1, valores_tec)):
                ax1.text(bar.get_width() + max_tec*0.01, bar.get_y() + bar.get_height()/2,
                        str(valor), ha='left', va='center', fontsize=9, fontweight='bold')
            
            ax1.set_yticks(range(len(nomes_tec)))
            ax1.set_yticklabels(nomes_tec, fontsize=9)
            ax1.set_title('Top 5 Técnicos', fontsize=10, fontweight='bold', pad=10)
            ax1.set_facecolor('none')
            ax1.grid(False)
            ax1.spines['top'].set_visible(False)
            ax1.spines['right'].set_visible(False)
            ax1.spines['left'].set_color('#cccccc')
            ax1.spines['bottom'].set_visible(False)
            ax1.tick_params(bottom=False)
        
        if top_locais:
            nomes_loc = [l[0] for l in top_locais]
            valores_loc = [l[1] for l in top_locais]
            max_loc = max(valores_loc) if valores_loc else 1
            
            bars2 = ax2.barh(range(len(nomes_loc)), valores_loc, color='#f5b618', 
                            height=0.6, edgecolor='white', linewidth=1.5)
            ax2.set_xlim(0, max_loc * 1.15)
            
            for i, (bar, valor) in enumerate(zip(bars2, valores_loc)):
                ax2.text(bar.get_width() + max_loc*0.01, bar.get_y() + bar.get_height()/2,
                        str(valor), ha='left', va='center', fontsize=9, fontweight='bold')
            
            ax2.set_yticks(range(len(nomes_loc)))
            ax2.set_yticklabels(nomes_loc, fontsize=9)
            ax2.set_title('Top 5 Locais', fontsize=10, fontweight='bold', pad=10)
            ax2.set_facecolor('none')
            ax2.grid(False)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color('#cccccc')
            ax2.spines['bottom'].set_visible(False)
            ax2.tick_params(bottom=False)
        
        fig.patch.set_facecolor('#cfcfcf')
        ax1.set_facecolor('#cfcfcf')
        ax2.set_facecolor('#cfcfcf')
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    def create_modern_kpis(self, parent, registros):
        """Cria KPIs modernos com tooltips informativos"""
        total_visitas = len(registros)
        concluidos = sum(1 for r in registros if r[2] and r[7])
        tecnicos_unicos = len(set([r[3] for r in registros]))
        locais_unicos = len(set([r[5] for r in registros]))
        taxa_conclusao = int((concluidos / total_visitas * 100)) if total_visitas > 0 else 0
        
        kpis_data = [
            ("📊", str(total_visitas), "Total de Visitas Registradas", "#ec4899"),
            ("✅", str(concluidos), "Visitas Concluídas com Sucesso", "#10b981"),
            ("👥", str(tecnicos_unicos), "Técnicos Ativos no Período", "#3b82f6"),
            ("📍", str(locais_unicos), "Locais Diferentes Visitados", "#f59e0b"),
            ("📈", f"{taxa_conclusao}%", "Taxa de Conclusão (%)", "#8b5cf6")
        ]
        
        for icon, value, tooltip_text, color in kpis_data:
            kpi_card = ctk.CTkFrame(parent, fg_color=color, corner_radius=15, 
                                   width=180, height=120)
            kpi_card.pack(side="left", fill="both", expand=True, padx=5)
            kpi_card.pack_propagate(False)
            
            icon_label = ctk.CTkLabel(kpi_card, text=icon, font=ctk.CTkFont(size=32))
            icon_label.pack(pady=(15, 5))
            
            value_label = ctk.CTkLabel(kpi_card, text=value, 
                                      font=ctk.CTkFont(size=36, weight="bold"),
                                      text_color="white")
            value_label.pack(pady=2)
            
            Tooltip(kpi_card, tooltip_text)

    def create_progress_charts(self, registros, parent):
        """Cria gráficos de progresso/taxa de uso"""
        frame = ctk.CTkFrame(parent, corner_radius=15)
        frame.pack(fill="x", padx=8)
        
        title = ctk.CTkLabel(frame, text="📊 Métricas de Performance",
                        font=ctk.CTkFont(size=16, weight="bold"))
        title.pack(pady=(20, 15))
        
        progress_container = ctk.CTkFrame(frame, fg_color="transparent")
        progress_container.pack(fill="x", padx=30, pady=10)
        
        total = len(registros)
        concluidos = sum(1 for r in registros if r[2] and r[7])
        
        tecnicos_dict = self._build_tecnico_dict_by_label(registros)
        
        # Ordenar todos os técnicos por quantidade
        todos_tecnicos = sorted(tecnicos_dict.items(), key=lambda x: x[1], reverse=True)
        
        # Função para interpolar cores entre vermelho e amarelo
        def get_color_gradient(index, total_count):
            if total_count == 1:
                return "#fe0401"
            
            # Interpolação entre #fe0401 (vermelho) e #f5b618 (amarelo)
            ratio = index / (total_count - 1)
            
            # Componentes RGB iniciais e finais
            r1, g1, b1 = 0xfe, 0x04, 0x01  # vermelho
            r2, g2, b2 = 0xf5, 0xb6, 0x18  # amarelo
            
            # Calcular componentes interpolados
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            
            return f"#{r:02x}{g:02x}{b:02x}"
        
        progress_data = [
            ("Taxa de Conclusão", concluidos, total, "#10b981"),
        ]
        
        # Adicionar todos os técnicos com cores gradientes
        for idx, (nome, qtd) in enumerate(todos_tecnicos):
            cor = get_color_gradient(idx, len(todos_tecnicos))
            progress_data.append((f"Técnico: {nome}", qtd, total, cor))
        
        for nome, qtd, total_val, cor in progress_data:
            bar_frame = ctk.CTkFrame(progress_container, fg_color="transparent")
            bar_frame.pack(fill="x", pady=10)
            
            info_frame = ctk.CTkFrame(bar_frame, fg_color="transparent")
            info_frame.pack(fill="x")
            
            ctk.CTkLabel(info_frame, text=nome, font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")
            ctk.CTkLabel(info_frame, text=f"{qtd}/{total_val} ({int(qtd/total_val*100)}%)", 
                        font=ctk.CTkFont(size=11)).pack(side="right")
            
            progress_bg = ctk.CTkFrame(bar_frame, height=25, fg_color="#e5e5e5")
            progress_bg.pack(fill="x", pady=(5, 0))
            
            progress_fill = ctk.CTkFrame(progress_bg, height=25, fg_color=cor,
                                        width=int((qtd/total_val) * progress_bg.winfo_reqwidth()))
            progress_fill.place(relx=0, rely=0, relheight=1, relwidth=qtd/total_val)
        
        ctk.CTkLabel(frame, text="").pack(pady=10)