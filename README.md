# 🖥️ Sistema de Controle de Kits de Informática

Sistema desktop para gerenciamento de kits de informática, técnicos e locais de atendimento.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![CustomTkinter](https://img.shields.io/badge/CustomTkinter-5.2+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

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

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

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