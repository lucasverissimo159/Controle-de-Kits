"""
Janela de cadastro/edição de registros
CORRIGIDO: Matrícula mostra APENAS código (sem nome)
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import re
import os
import sys
import json
import sqlite3
from views.widgets.scrollable_combobox import ScrollableComboBox

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class RecordWindow:
    def __init__(self, parent, mode="new", record_id=None):
        self.parent = parent
        self.mode = mode
        self.record_id = record_id
        
        self.window = ctk.CTkToplevel(parent.root)
        self.window.title("Novo Registro" if mode == "new" else "Editar Registro")
        self.window.geometry("515x550")
        self.window.grab_set()
        self.window.transient(parent.root)

        # Centralizar janela
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 257
        y = (self.window.winfo_screenheight() // 2) - 300
        self.window.geometry(f"515x550+{x}+{y}")

        # Definir ícone da janela
        self.set_window_icon()
        
        # Variáveis
        self.vars = {
            'data_inicio': ctk.StringVar(value=datetime.now().strftime("%d/%m/%Y")),
            'data_fim': ctk.StringVar(),
            'matricula': ctk.StringVar(),
            'tecnico': ctk.StringVar(),
            'num_kit': ctk.StringVar(),
            'local': ctk.StringVar(),
            'horario_inicio': ctk.StringVar(value=datetime.now().strftime("%H:%M")),
            'horario_fim': ctk.StringVar()
        }
        
        # Guardar valores originais para comparação no histórico
        self.original_values = {}
        
        # Mapa matrícula → nome do técnico (para tooltip)
        self._matricula_to_nome = {}
        
        if mode == "edit":
            self.load_record()
        
        self.create_widgets()

    def set_window_icon(self):
        """Define o ícone para a janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")
    
    def load_record(self):
        """Carrega dados do registro para edição"""
        # Query com JOIN para pegar matrícula
        self.parent.cursor.execute("""
            SELECT r.*, t.matricula, t.nome
            FROM registros r
            JOIN tecnicos t ON r.matricula_tecnico = t.matricula
            WHERE r.id = ?
        """, (self.record_id,))
        record = self.parent.cursor.fetchone()
        
        if record:
            self.vars['data_inicio'].set(record[1])
            self.vars['data_fim'].set(record[2] or "")
            self.vars['matricula'].set(record[8])  # matricula do JOIN
            self.vars['tecnico'].set(record[9])    # nome do JOIN
            self.vars['num_kit'].set(record[4])
            self.vars['local'].set(record[5])
            self.vars['horario_inicio'].set(record[6])
            self.vars['horario_fim'].set(record[7] or "")
            
            # Guardar valores originais para comparação
            self.original_values = {
                'data_inicio': record[1] or "",
                'data_fim': record[2] or "",
                'matricula': record[8] or "",
                'tecnico': record[9] or "",
                'num_kit': record[4] or "",
                'local': record[5] or "",
                'horario_inicio': record[6] or "",
                'horario_fim': record[7] or ""
            }
    
    def on_matricula_change(self, *args):
        """Quando matrícula muda, atualiza campo de técnico automaticamente"""
        matricula = self.vars['matricula'].get()
        
        if not matricula:
            self.vars['tecnico'].set("")
            return
        
        # Buscar nome do técnico pela matrícula
        self.parent.cursor.execute("""
            SELECT nome FROM tecnicos WHERE matricula = ?
        """, (matricula,))
        
        result = self.parent.cursor.fetchone()
        if result:
            self.vars['tecnico'].set(result[0])
        else:
            self.vars['tecnico'].set("")
    
    def on_matricula_enter_pressed(self, valor_digitado=None):
        """Quando ENTER é pressionado no campo de matrícula (ou leitor de crachá).
        
        Suporta:
        - Digitação manual + ENTER
        - Leitor de crachá (que envia ENTER automaticamente)
        
        Lógica:
        - Se matrícula existe no banco → preenche técnico automaticamente
        - Se não existe → exibe aviso e limpa o campo
        """
        if valor_digitado:
            matricula = valor_digitado.strip().upper()
        else:
            matricula = self.vars['matricula'].get().strip().upper()
        
        if not matricula:
            return
        
        # Buscar técnico pela matrícula
        self.parent.cursor.execute("""
            SELECT nome FROM tecnicos WHERE matricula = ?
        """, (matricula,))
        result = self.parent.cursor.fetchone()
        
        if result:
            self.vars['matricula'].set(matricula)
            self.vars['tecnico'].set(result[0])
        else:
            messagebox.showwarning(
                "Matrícula não encontrada",
                f"A matrícula '{matricula}' não está cadastrada no sistema."
            )
            self.vars['matricula'].set("")
            self.vars['tecnico'].set("")
    
    def get_matriculas_disponiveis(self):
        """Retorna lista de matrículas disponíveis (APENAS MATRÍCULA)"""
        self.parent.cursor.execute("""
            SELECT matricula, nome FROM tecnicos ORDER BY nome, matricula
        """)
        rows = self.parent.cursor.fetchall()
        
        # Popular mapa matrícula → nome para uso no tooltip
        self._matricula_to_nome = {row[0]: row[1] for row in rows if row[0]}
        
        # Retornar APENAS a matrícula, sem o nome
        matriculas = [row[0] for row in rows]
        return matriculas
    
    def get_matricula_tecnico_tooltip(self, matricula):
        """Retorna texto do tooltip com o nome do técnico associado à matrícula."""
        if not matricula:
            return None
        nome = self._matricula_to_nome.get(matricula.strip())
        if nome:
            return f"👷 Técnico: {nome}"
        return None
    
    def create_widgets(self):
        """Cria interface da janela de registro"""
        # Frame principal com scroll
        main_frame = ctk.CTkScrollableFrame(self.window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        title = ctk.CTkLabel(main_frame, 
                            text="NOVO REGISTRO" if self.mode == "new" else "EDITAR REGISTRO",
                            font=ctk.CTkFont(size=20, weight="bold"))
        title.pack(pady=(0, 30))
        
        # Data Início
        ctk.CTkLabel(main_frame, text="Data Início *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        data_inicio_entry = ctk.CTkEntry(main_frame, textvariable=self.vars['data_inicio'], 
                    placeholder_text="Ex: 25/12/2023",
                    height=40)
        data_inicio_entry.pack(fill="x", pady=(0, 15))
        data_inicio_entry.bind('<KeyRelease>', self.parent.format_date_input)
        
        # Horário Início
        ctk.CTkLabel(main_frame, text="Horário Início *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        horario_inicio_entry = ctk.CTkEntry(main_frame, textvariable=self.vars['horario_inicio'], 
                    placeholder_text="Ex: 14:30",
                    height=40)
        horario_inicio_entry.pack(fill="x", pady=(0, 15))
        horario_inicio_entry.bind('<KeyRelease>', self.parent.format_time_input)
        
        # Matrícula (CORRIGIDO - APENAS MATRÍCULA)
        ctk.CTkLabel(main_frame, text="Matrícula do Técnico *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        
        matriculas_disponiveis = self.get_matriculas_disponiveis()
        
        self.matricula_combo = ScrollableComboBox(main_frame, 
                       variable=self.vars['matricula'],
                       values=matriculas_disponiveis,  # APENAS matrícula
                       height=40,
                       max_visible_items=6,
                       app=self.parent,
                       on_enter_callback=self.on_matricula_enter_pressed,
                       numeric_only=True,
                       item_tooltip_callback=self.get_matricula_tecnico_tooltip)
        self.matricula_combo.pack(fill="x", pady=(0, 15))
        
        # Vincular evento de mudança de matrícula
        self.vars['matricula'].trace_add('write', self.on_matricula_change)
        
        # Técnico (SEGUNDO - somente leitura)
        ctk.CTkLabel(main_frame, text="Nome do Técnico (automático)", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        tecnico_entry = ctk.CTkEntry(main_frame, 
                    textvariable=self.vars['tecnico'],
                    height=40,
                    state="readonly",
                    fg_color="#374151",
                    text_color="#d1d5db")
        tecnico_entry.pack(fill="x", pady=(0, 15))
        
        # Nº Kit
        ctk.CTkLabel(main_frame, text="Nº Kit *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        num_kit_combo = ScrollableComboBox(main_frame, 
                       variable=self.vars['num_kit'],
                       values=self.parent.get_items("kits", "numero"), 
                       height=40,
                       max_visible_items=6,
                       app=self.parent)
        num_kit_combo.pack(fill="x", pady=(0, 15))
        
        # Local
        ctk.CTkLabel(main_frame, text="Local *", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        local_combo = ScrollableComboBox(main_frame, 
                       variable=self.vars['local'],
                       values=self.parent.get_items("locais"), 
                       height=40,
                       max_visible_items=6,
                       app=self.parent)
        local_combo.pack(fill="x", pady=(0, 15))
        
        # Separador
        separator = ctk.CTkFrame(main_frame, height=2, fg_color="#475569")
        separator.pack(fill="x", pady=20)
        
        # Data Fim
        ctk.CTkLabel(main_frame, text="Data Fim (preencher ao finalizar)", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        data_fim_entry = ctk.CTkEntry(main_frame, textvariable=self.vars['data_fim'], 
                    placeholder_text="Ex: 26/12/2023",
                    height=40)
        data_fim_entry.pack(fill="x", pady=(0, 15))
        data_fim_entry.bind('<KeyRelease>', self.parent.format_date_input)
        
        # Horário Fim
        ctk.CTkLabel(main_frame, text="Horário Fim (preencher ao finalizar)", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 5))
        horario_fim_entry = ctk.CTkEntry(main_frame, textvariable=self.vars['horario_fim'], 
                    placeholder_text="Ex: 16:45",
                    height=40)
        horario_fim_entry.pack(fill="x", pady=(0, 20))
        horario_fim_entry.bind('<KeyRelease>', self.parent.format_time_input)
        
        # Frame de validação
        validation_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        validation_frame.pack(fill="x", pady=(0, 20))
        
        validation_label = ctk.CTkLabel(validation_frame, 
                                       text="⚠️ Verifique se a data e horário finais são válidos",
                                       text_color="#f59e0b",
                                       font=ctk.CTkFont(size=12))
        validation_label.pack(anchor="w")
        
        # Botões
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        ctk.CTkButton(btn_frame, text="SALVAR REGISTRO", 
                     command=self.save_record,
                     fg_color="#10b981", hover_color="#059669",
                     height=50, font=ctk.CTkFont(size=14, weight="bold")).pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(btn_frame, text="CANCELAR", 
                     command=self.window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563",
                     height=45).pack(fill="x")
    
    def save_record(self):
        """Salva ou atualiza registro"""
        # Validações
        if not self.vars['data_inicio'].get():
            messagebox.showwarning("Aviso", "Preencha a Data de Início!")
            return
        
        if not self.vars['horario_inicio'].get():
            messagebox.showwarning("Aviso", "Preencha o Horário de Início!")
            return
        
        # Matrícula (já é apenas o código)
        matricula = self.vars['matricula'].get()
        if not matricula:
            messagebox.showwarning("Aviso", "Selecione a Matrícula do Técnico!")
            return
        
        if not self.vars['num_kit'].get():
            messagebox.showwarning("Aviso", "Selecione o Nº do Kit!")
            return
        
        if not self.vars['local'].get():
            messagebox.showwarning("Aviso", "Selecione o Local!")
            return
        
        # Validar formato de data
        if not re.match(r'^\d{2}/\d{2}/\d{4}$', self.vars['data_inicio'].get()):
            messagebox.showerror("Erro", "Data de Início inválida! Use o formato DD/MM/AAAA")
            return
        
        # Validar formato de horário
        if not re.match(r'^\d{2}:\d{2}$', self.vars['horario_inicio'].get()):
            messagebox.showerror("Erro", "Horário de Início inválido! Use o formato HH:MM")
            return
        
        # Se data fim foi preenchida, validar
        if self.vars['data_fim'].get():
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', self.vars['data_fim'].get()):
                messagebox.showerror("Erro", "Data Fim inválida! Use o formato DD/MM/AAAA")
                return
        
        # Se horário fim foi preenchido, validar
        if self.vars['horario_fim'].get():
            if not re.match(r'^\d{2}:\d{2}$', self.vars['horario_fim'].get()):
                messagebox.showerror("Erro", "Horário Fim inválido! Use o formato HH:MM")
                return
        
        # Validação de data/hora fim vs início
        if self.vars['data_fim'].get() and self.vars['horario_fim'].get():
            try:
                # Converter datas para comparação
                data_inicio = datetime.strptime(self.vars['data_inicio'].get(), "%d/%m/%Y")
                data_fim = datetime.strptime(self.vars['data_fim'].get(), "%d/%m/%Y")
                
                # Verificar se data fim é menor que data início
                if data_fim < data_inicio:
                    messagebox.showerror("Erro", "Data Fim não pode ser anterior à Data de Início!")
                    return
                
                # Se as datas são iguais, validar horários
                if data_fim == data_inicio:
                    horario_inicio = datetime.strptime(self.vars['horario_inicio'].get(), "%H:%M")
                    horario_fim = datetime.strptime(self.vars['horario_fim'].get(), "%H:%M")
                    
                    if horario_fim <= horario_inicio:
                        messagebox.showerror("Erro", 
                            "Quando as datas são iguais, o Horário Fim deve ser posterior ao Horário de Início!")
                        return
            except ValueError as e:
                messagebox.showerror("Erro", f"Erro ao validar datas/horários: {str(e)}")
                return
        
        try:
            if self.mode == "new":
                # Inserir novo registro (com MATRÍCULA)
                self.parent.cursor.execute("""
                    INSERT INTO registros 
                    (data_inicio, data_fim, matricula_tecnico, num_kit, local, 
                     horario_inicio, horario_fim)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.vars['data_inicio'].get(),
                    self.vars['data_fim'].get() or None,
                    matricula,
                    self.vars['num_kit'].get(),
                    self.vars['local'].get(),
                    self.vars['horario_inicio'].get(),
                    self.vars['horario_fim'].get() or None
                ))
                
                self.parent.conn.commit()
                messagebox.showinfo("Sucesso", "Registro salvo com sucesso!")
                self.window.destroy()
                
            else:
                # Atualizar registro existente
                self.parent.cursor.execute("""
                    UPDATE registros SET
                        data_inicio = ?,
                        data_fim = ?,
                        matricula_tecnico = ?,
                        num_kit = ?,
                        local = ?,
                        horario_inicio = ?,
                        horario_fim = ?
                    WHERE id = ?
                """, (
                    self.vars['data_inicio'].get(),
                    self.vars['data_fim'].get() or None,
                    matricula,
                    self.vars['num_kit'].get(),
                    self.vars['local'].get(),
                    self.vars['horario_inicio'].get(),
                    self.vars['horario_fim'].get() or None,
                    self.record_id
                ))
                
                # Registrar alterações no histórico
                self.register_changes(matricula)
                
                # IMPORTANTE: Fechar janela ANTES do commit para liberar recursos
                self.window.destroy()
                
                # Commit após fechar janela
                self.parent.conn.commit()
                messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
            
            # Recarregar dados na janela principal
            if hasattr(self.parent, 'load_main_data'):
                self.parent.load_main_data()
            elif hasattr(self.parent, 'apply_filters'):
                self.parent.apply_filters()
        
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                # Tentar novamente após pequeno delay
                self.window.after(500, lambda: self._retry_save(matricula))
            else:
                messagebox.showerror("Erro", f"Erro ao salvar registro: {str(e)}")
                self.parent.conn.rollback()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar registro: {str(e)}")
            self.parent.conn.rollback()
    
    def _retry_save(self, matricula):
        """Tenta salvar novamente após database locked"""
        try:
            if self.mode == "edit":
                self.parent.cursor.execute("""
                    UPDATE registros SET
                        data_inicio = ?,
                        data_fim = ?,
                        matricula_tecnico = ?,
                        num_kit = ?,
                        local = ?,
                        horario_inicio = ?,
                        horario_fim = ?
                    WHERE id = ?
                """, (
                    self.vars['data_inicio'].get(),
                    self.vars['data_fim'].get() or None,
                    matricula,
                    self.vars['num_kit'].get(),
                    self.vars['local'].get(),
                    self.vars['horario_inicio'].get(),
                    self.vars['horario_fim'].get() or None,
                    self.record_id
                ))
                
                self.register_changes(matricula)
                self.parent.conn.commit()
                messagebox.showinfo("Sucesso", "Registro atualizado com sucesso!")
                
                if hasattr(self.parent, 'load_main_data'):
                    self.parent.load_main_data()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar após retry: {str(e)}")
    
    def register_changes(self, matricula):
        """Registra alterações no histórico usando a mesma conexão"""
        changes = []
        
        # Comparar valores
        current_values = {
            'data_inicio': self.vars['data_inicio'].get(),
            'data_fim': self.vars['data_fim'].get() or "",
            'matricula': matricula,
            'tecnico': self.vars['tecnico'].get(),
            'num_kit': self.vars['num_kit'].get(),
            'local': self.vars['local'].get(),
            'horario_inicio': self.vars['horario_inicio'].get(),
            'horario_fim': self.vars['horario_fim'].get() or ""
        }
        
        for field, current_value in current_values.items():
            original_value = self.original_values.get(field, "")
            if str(current_value) != str(original_value):
                changes.append((field, original_value, current_value))
        
        # Registrar no histórico usando a MESMA conexão do parent
        for field, old_value, new_value in changes:
            try:
                self.parent.cursor.execute('''
                    INSERT INTO registro_historico 
                    (registro_id, campo_alterado, valor_anterior, valor_novo, 
                     data_alteracao, tipo_operacao)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    self.record_id,
                    field,
                    str(old_value),
                    str(new_value),
                    datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                    "UPDATE"
                ))
            except Exception as e:
                print(f"Erro ao registrar histórico: {e}")  # Log mas não falha a operação