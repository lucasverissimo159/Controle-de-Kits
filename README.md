# 🖥️ IT Kits Control System

Desktop system for managing IT kits, technicians, and service locations.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)
![License](https://img.shields.io/badge/License-View--Only-red.svg)

---

> ⚠️ **Repository provided for portfolio purposes only.** The code can
> be viewed, but **cannot** be copied, downloaded, used, or
> reused in other projects. See the [License](#-license) section and the
> [`LICENSE`](./LICENSE) file.

---

## 📋 Features

### Main Window
- ✅ Registration of records (visits/maintenance)
- ✅ Editing records
- ✅ Change history
- ✅ Filters by date, technician, kit, and location
- ✅ Integrated calendar
- ✅ Display of the last 20 records

### Management
- ✅ Registration of technicians
- ✅ Registration of locations
- ✅ Registration of kits
- ✅ Editing and deleting items

### Old Records
- ✅ Automatic monthly archiving
- ✅ Viewing historical data (JSON)
- ✅ Filters by month/year

### Statistics
- ✅ Visual KPIs (Total, Completed, Technicians, Locations, Rate)
- ✅ Time evolution chart (Plotly)
- ✅ Top 5 most used Kits
- ✅ Top 5 Technicians and Locations
- ✅ Performance metrics
- ✅ PDF Export
- ✅ CSV/Excel Export

### Interface
- ✅ Light and dark theme
- ✅ Modern interface (CustomTkinter)
- ✅ Informative tooltips
- ✅ ComboBox with scroll

---

## 🚀 Installation

### 1. Clone or download the project
```bash
git clone <repository-url>
cd kit_control_final
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the system
```bash
python main.py
```

---

## 📦 Dependencies

| Package | Version | Description |
|---------|---------|-------------|
| customtkinter | ≥5.2.0 | Modern interface |
| tkcalendar | ≥1.6.1 | Date picker |
| matplotlib | ≥3.7.0 | Charts |
| plotly | ≥5.15.0 | Interactive charts |
| openpyxl | ≥3.1.2 | Excel export |
| Pillow | ≥10.0.0 | Image manipulation |
| reportlab | ≥4.0.0 | PDF generation |
| numpy | ≥1.24.0 | Numerical calculations |

---

## 📁 Project Structure

```
kit_control_final/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md              # This file
│
├── config/
│   └── settings.py        # Settings
│
├── models/
│   └── database.py        # Database
│
├── views/
│   ├── main_window.py     # Main window
│   ├── record_window.py   # Record form
│   ├── history_dialog.py  # History dialog
│   ├── helpers.py         # Helper functions
│   ├── stats_manager.py   # Statistics
│   └── widgets/
│       ├── scrollable_combobox.py
│       ├── progress_dialog.py
│       └── tooltip.py
│
├── resources/
│   └── icons/
│       └── icon.ico       # App icon
│
└── arquivos_mensais/      # Monthly JSON files
```

---

## 🧪 Test Data

To test with dummy data:

```bash
python gerar_dados_teste.py
```

This will:
- Register 10 technicians
- Register 10 locations
- Register 20 kits
- Generate ~300-400 records
- Create monthly JSON files

---

## 🖼️ Screenshots

### Main Window
- Table with records
- Filters at the top
- Action buttons

### Statistics
- Colorful KPIs
- Interactive charts
- Rankings

### Management
- Editable lists
- Add/Edit/Delete

---

## 🗄️ Database

The system uses **SQLite** with the following tables:

| Table | Description |
|-------|-------------|
| `registros` | Records of visits/maintenance |
| `tecnicos` | Registration of technicians |
| `locais` | Registration of locations |
| `kits` | Registration of kits |
| `config` | System settings |
| `registro_historico` | Change history |

---

## 📊 Monthly Archiving

The system automatically archives the previous month's records into JSON files:

```
arquivos_mensais/
├── registros_01_2025.json
├── registros_02_2025.json
└── ...
```

---

## ⚙️ Settings

Edit `config/settings.py` to customize:

```python
DATABASE_NAME = 'kit_control.db'  # Database name
DEFAULT_THEME = "light"           # Default theme: "light" or "dark"
```

---

## 🎨 Themes

Switch between light and dark themes by clicking the **THEME** button in the header.

| Theme | Description |
|-------|-------------|
| Light | White background, black text |
| Dark | Dark background, light text |

---

## 📤 Exports

### PDF
- Complete report with charts
- Statistical data
- A4 landscape format

### CSV/Excel
- Tabulated data
- Excel compatible
- .xlsx format

---

## 🔧 Development

### MVC Architecture
- **Model:** `models/database.py`
- **View:** `views/*.py`
- **Controller:** Integrated in views

### Add new functionality
1. Create the widget in `views/widgets/`
2. Import in `views/main_window.py`
3. Add to TabView or wherever necessary

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for change history.

---

## 📄 License

This repository is **not open source**. It is made publicly available
only for portfolio/technical demonstration purposes.

- ✅ Allowed: viewing the code through the GitHub interface.
- ❌ Prohibited: copying, downloading, cloning for reuse, using, modifying, executing
  or redistributing this code, in whole or in part, without prior written
  authorization from the author.

All rights reserved. See full terms in
[`LICENSE`](./LICENSE).

---

## 👨‍💻 Author

Developed with ❤️ for efficient IT kits management.

---

## 🆘 Support

If you encounter any problems:
1. Check if dependencies are installed
2. Make sure you are in the correct directory
3. Try deleting `kit_control.db` and running again

```bash
rm kit_control.db
python main.py
```

---

**IT Kits Control System v2.0.0** 🖥️

---

# 🖥️ Sistema de Controle de Kits de Informática

Sistema desktop para gerenciamento de kits de informática, técnicos e locais de atendimento.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)
![License](https://img.shields.io/badge/License-View--Only-red.svg)

---

> ⚠️ **Repositório disponibilizado apenas para portfólio.** O código pode
> ser visualizado, mas **não** pode ser copiado, baixado, usado ou
> reaproveitado em outros projetos. Veja a seção [Licença](#-licença) e o
> arquivo [`LICENSE`](./LICENSE).

---

## 📋 Funcionalidades

### Janela Principal
- ✅ Cadastro de registros (visitas/manutenções)
- ✅ Edição de registros
- ✅ Histórico de alterações
- ✅ Filtros por data, técnico, kit e local
- ✅ Calendário integrado
- ✅ Exibição dos últimos 20 registros

### Gerenciamento
- ✅ Cadastro de técnicos
- ✅ Cadastro de locais
- ✅ Cadastro de kits
- ✅ Edição e exclusão de itens

### Registros Antigos
- ✅ Arquivamento mensal automático
- ✅ Visualização de dados históricos (JSON)
- ✅ Filtros por mês/ano

### Estatísticas
- ✅ KPIs visuais (Total, Concluídos, Técnicos, Locais, Taxa)
- ✅ Gráfico de evolução temporal (Plotly)
- ✅ Top 5 Kits mais utilizados
- ✅ Top 5 Técnicos e Locais
- ✅ Métricas de performance
- ✅ Exportação PDF
- ✅ Exportação CSV/Excel

### Interface
- ✅ Tema claro e escuro
- ✅ Interface moderna (CustomTkinter)
- ✅ Tooltips informativos
- ✅ ComboBox com scroll

---

## 🚀 Instalação

### 1. Clone ou baixe o projeto
```bash
git clone <url-do-repositorio>
cd kit_control_final
```

### 2. Crie um ambiente virtual (recomendado)
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Execute o sistema
```bash
python main.py
```

---

## 📦 Dependências

| Pacote | Versão | Descrição |
|--------|--------|-----------|
| customtkinter | ≥5.2.0 | Interface moderna |
| tkcalendar | ≥1.6.1 | Seletor de data |
| matplotlib | ≥3.7.0 | Gráficos |
| plotly | ≥5.15.0 | Gráficos interativos |
| openpyxl | ≥3.1.2 | Exportação Excel |
| Pillow | ≥10.0.0 | Manipulação de imagens |
| reportlab | ≥4.0.0 | Geração de PDF |
| numpy | ≥1.24.0 | Cálculos numéricos |

---

## 📁 Estrutura do Projeto

```
kit_control_final/
├── main.py                 # Ponto de entrada
├── requirements.txt        # Dependências
├── README.md              # Este arquivo
│
├── config/
│   └── settings.py        # Configurações
│
├── models/
│   └── database.py        # Banco de dados
│
├── views/
│   ├── main_window.py     # Janela principal
│   ├── record_window.py   # Formulário de registro
│   ├── history_dialog.py  # Diálogo de histórico
│   ├── helpers.py         # Funções auxiliares
│   ├── stats_manager.py   # Estatísticas
│   └── widgets/
│       ├── scrollable_combobox.py
│       ├── progress_dialog.py
│       └── tooltip.py
│
├── resources/
│   └── icons/
│       └── icon.ico       # Ícone do app
│
└── arquivos_mensais/      # Arquivos JSON mensais
```

---

## 🧪 Dados de Teste

Para testar com dados fictícios:

```bash
python gerar_dados_teste.py
```

Isso irá:
- Cadastrar 10 técnicos
- Cadastrar 10 locais
- Cadastrar 20 kits
- Gerar ~300-400 registros
- Criar arquivos JSON mensais

---

## 🖼️ Screenshots

### Janela Principal
- Tabela com registros
- Filtros no topo
- Botões de ação

### Estatísticas
- KPIs coloridos
- Gráficos interativos
- Rankings

### Gerenciamento
- Listas editáveis
- Adicionar/Editar/Excluir

---

## 🗄️ Banco de Dados

O sistema usa **SQLite** com as seguintes tabelas:

| Tabela | Descrição |
|--------|-----------|
| `registros` | Registros de visitas/manutenções |
| `tecnicos` | Cadastro de técnicos |
| `locais` | Cadastro de locais |
| `kits` | Cadastro de kits |
| `config` | Configurações do sistema |
| `registro_historico` | Histórico de alterações |

---

## 📊 Arquivamento Mensal

O sistema arquiva automaticamente os registros do mês anterior em arquivos JSON:

```
arquivos_mensais/
├── registros_01_2025.json
├── registros_02_2025.json
└── ...
```

---

## ⚙️ Configurações

Edite `config/settings.py` para personalizar:

```python
DATABASE_NAME = 'kit_control.db'  # Nome do banco
DEFAULT_THEME = "light"           # Tema padrão: "light" ou "dark"
```

---

## 🎨 Temas

Alterne entre tema claro e escuro clicando no botão **TEMA** no cabeçalho.

| Tema | Descrição |
|------|-----------|
| Claro | Fundo branco, texto preto |
| Escuro | Fundo escuro, texto claro |

---

## 📤 Exportações

### PDF
- Relatório completo com gráficos
- Dados estatísticos
- Formato A4 paisagem

### CSV/Excel
- Dados tabulados
- Compatível com Excel
- Formato .xlsx

---

## 🔧 Desenvolvimento

### Arquitetura MVC
- **Model:** `models/database.py`
- **View:** `views/*.py`
- **Controller:** Integrado nas views

### Adicionar nova funcionalidade
1. Crie o widget em `views/widgets/`
2. Importe em `views/main_window.py`
3. Adicione ao TabView ou onde necessário

---

## 📝 Changelog

Veja [CHANGELOG.md](CHANGELOG.md) para histórico de alterações.

---

## 📄 Licença

Este repositório **não é open source**. Ele é disponibilizado publicamente
apenas para fins de portfólio/demonstração técnica.

- ✅ Permitido: visualizar o código pela interface do GitHub.
- ❌ Proibido: copiar, baixar, clonar para reuso, usar, modificar, executar
  ou redistribuir este código, no todo ou em parte, sem autorização prévia
  e por escrito do autor.

Todos os direitos são reservados. Veja os termos completos em
[`LICENSE`](./LICENSE).

---

## 👨‍💻 Autor

Desenvolvido com ❤️ para gerenciamento eficiente de kits de informática.

---

## 🆘 Suporte

Se encontrar algum problema:
1. Verifique se as dependências estão instaladas
2. Verifique se está no diretório correto
3. Tente deletar `kit_control.db` e executar novamente

```bash
rm kit_control.db
python main.py
```

---

**Sistema de Controle de Kits v2.0.0** 🖥️