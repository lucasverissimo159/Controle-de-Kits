#!/usr/bin/env python3
"""
Script para criar a estrutura completa do projeto Kit Control
Cria todos os diretórios e arquivos necessários
"""
import os
import sys

# Estrutura do projeto
PROJECT_STRUCTURE = {
    "kit_control_final": {
        "config": {
            "__init__.py": "",
            "settings.py": None  # Será copiado/criado separadamente
        },
        "models": {
            "__init__.py": "",
            "database.py": None
        },
        "views": {
            "__init__.py": "",
            "main_window.py": None,
            "record_window.py": None,
            "history_dialog.py": None,
            "helpers.py": None,
            "stats_manager.py": None,
            "widgets": {
                "__init__.py": "",
                "scrollable_combobox.py": None,
                "progress_dialog.py": None,
                "tooltip.py": None
            }
        },
        "controllers": {
            "__init__.py": ""
        },
        "utils": {
            "__init__.py": ""
        },
        "resources": {
            "icons": {}
        },
        "arquivos_mensais": {},
        "main.py": None,
        "requirements.txt": None,
        "README.md": None,
        "CHANGELOG.md": None,
        "ESTRUTURA.txt": None,
        "INSTRUCOES_TESTE.md": None,
        "gerar_dados_teste.py": None
    }
}

# Conteúdo dos __init__.py
INIT_CONTENT = '"""Módulo {module}"""\n'

def create_structure(base_path, structure, current_path=""):
    """Cria a estrutura de diretórios e arquivos"""
    for name, content in structure.items():
        full_path = os.path.join(base_path, current_path, name)
        
        if isinstance(content, dict):
            # É um diretório
            if not os.path.exists(full_path):
                os.makedirs(full_path)
                print(f"📁 Criado diretório: {full_path}")
            
            # Criar conteúdo do diretório
            create_structure(base_path, content, os.path.join(current_path, name))
        
        elif content == "":
            # É um __init__.py vazio
            if not os.path.exists(full_path):
                module_name = os.path.basename(os.path.dirname(full_path))
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(INIT_CONTENT.format(module=module_name))
                print(f"📄 Criado arquivo: {full_path}")
        
        elif content is None:
            # Arquivo que deve ser copiado/criado manualmente
            if not os.path.exists(full_path):
                print(f"⚠️  Arquivo pendente: {full_path}")

def main():
    """Função principal"""
    print("="*60)
    print("🏗️  CRIADOR DE ESTRUTURA DO PROJETO")
    print("Sistema de Controle de Kits - MVC")
    print("="*60)
    
    # Diretório base (onde o script está)
    base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Verificar se já existe
    project_path = os.path.join(base_path, "kit_control_final")
    if os.path.exists(project_path):
        resp = input("\n⚠️  Diretório já existe. Continuar? (S/N): ").upper()
        if resp != 'S':
            print("Operação cancelada.")
            return
    
    print("\n📂 Criando estrutura do projeto...\n")
    
    create_structure(base_path, PROJECT_STRUCTURE)
    
    print("\n" + "="*60)
    print("✅ ESTRUTURA CRIADA COM SUCESSO!")
    print("="*60)
    print("""
📋 Próximos passos:

1. Copie os arquivos .py para seus respectivos diretórios:
   - main.py → kit_control_final/
   - settings.py → kit_control_final/config/
   - database.py → kit_control_final/models/
   - main_window.py → kit_control_final/views/
   - record_window.py → kit_control_final/views/
   - history_dialog.py → kit_control_final/views/
   - helpers.py → kit_control_final/views/
   - stats_manager.py → kit_control_final/views/
   - scrollable_combobox.py → kit_control_final/views/widgets/
   - progress_dialog.py → kit_control_final/views/widgets/
   - tooltip.py → kit_control_final/views/widgets/

2. Adicione o ícone (opcional):
   - icon.ico → kit_control_final/resources/icons/

3. Instale as dependências:
   pip install -r requirements.txt

4. Execute o sistema:
   cd kit_control_final
   python main.py

5. Para gerar dados de teste:
   python gerar_dados_teste.py
""")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()