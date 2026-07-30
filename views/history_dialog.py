"""
Diálogo para exibir histórico de alterações
"""
import customtkinter as ctk
from tkinter import ttk
import sys
import os

def get_resource_path(relative_path):
    """Obtém o caminho correto para recursos (funciona com PyInstaller)"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), relative_path)

class HistoryDialog:
    """Diálogo de histórico"""
    
    def __init__(self, parent, db, record_id):
        self.parent = parent
        self.db = db
        self.record_id = record_id
        
        self.window = ctk.CTkToplevel(parent)
        self.window.title(f"Histórico - Registro #{record_id}")
        self.window.geometry("800x500")
        self.window.grab_set()
        self.window.transient(parent)
        
        # Centralizar
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 400
        y = (self.window.winfo_screenheight() // 2) - 250
        self.window.geometry(f"800x500+{x}+{y}")

        # Definir ícone da janela
        self.set_window_icon()
        
        self.create_widgets()
        self.load_history()

    def set_window_icon(self):
        """Define o ícone para a janela"""
        try:
            icon_path = get_resource_path(os.path.join("resources", "icons", "icon.ico"))
            if os.path.exists(icon_path):
                self.window.after(200, lambda: self.window.iconbitmap(icon_path))
        except Exception as e:
            print(f"Aviso: Não foi possível carregar o ícone: {e}")
    
    def create_widgets(self):
        """Criar interface"""
        main = ctk.CTkFrame(self.window, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(main, text=f"📋 Histórico de Alterações",
                    font=ctk.CTkFont(size=18, weight="bold")).pack(pady=(0, 20))
        
        # Tabela
        table_frame = ctk.CTkFrame(main)
        table_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)
        
        cols = ("Tipo", "Campo", "Anterior", "Novo", "Data/Hora")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings",
                                yscrollcommand=scrollbar.set, height=15)
        scrollbar.config(command=self.tree.yview)
        
        # Configurar colunas
        widths = [100, 120, 150, 150, 150]
        for col, width in zip(cols, widths):
            self.tree.column(col, width=width, anchor="center")
            self.tree.heading(col, text=col, anchor="center")
        
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Botão fechar
        ctk.CTkButton(main, text="FECHAR", command=self.window.destroy,
                     fg_color="#6b7280", hover_color="#4b5563",
                     height=40, width=150).pack()
    
    def load_history(self):
        """Carregar histórico"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        history = self.db.get_history(self.record_id)
        
        if not history:
            self.tree.insert('', 'end', 
                           values=('', '', 'Nenhuma alteração', '', ''))
            return
        
        for campo, anterior, novo, data, tipo in history:
            tipo_icon = {'CRIAÇÃO': '✨', 'EDIÇÃO': '✏️', 'EXCLUSÃO': '🗑️'}.get(tipo, '•')
            self.tree.insert('', 'end',
                           values=(f"{tipo_icon} {tipo}", campo, 
                                  anterior or '-', novo or '-', data))
