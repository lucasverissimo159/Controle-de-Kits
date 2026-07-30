# 🧪 Como Testar o Sistema Completo

## Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

---

## Passo a Passo

### 1️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

**Dependências instaladas:**
- customtkinter (interface moderna)
- tkcalendar (seletor de data)
- matplotlib (gráficos)
- plotly (gráficos interativos)
- openpyxl (Excel)
- Pillow (imagens)
- reportlab (PDF)
- numpy (cálculos)

---

### 2️⃣ Gerar dados de teste

```bash
python gerar_dados_teste.py
```

**O que acontece:**
- ✅ Cria banco de dados SQLite
- ✅ Cadastra 10 técnicos
- ✅ Cadastra 10 locais
- ✅ Cadastra 20 kits
- ✅ Gera ~300-400 registros (Nov-Dez/2024 + Jan-Nov/2025)
- ✅ Cria arquivos JSON mensais
- ✅ Alguns registros de Novembro/2025 ficam incompletos (sem data/hora fim)

---

### 3️⃣ Executar o sistema

```bash
python main.py
```

---

## 4️⃣ Testar funcionalidades

### ✅ Janela Principal
- Veja os registros carregados
- Teste os filtros:
  - Por **Data** (digite ou use o calendário 📅)
  - Por **Técnico**
  - Por **Nº Kit**
  - Por **Local**
- Clique no botão **ℹ️ INFO** para ver histórico de um registro
- Clique em **NOVO REGISTRO** para criar um novo
- Clique em **EDITAR** para modificar um existente

---

### ✅ Gerenciar Técnicos/Locais/Kits
- Navegue pelas abas correspondentes
- **Adicione** novos itens
- **Edite** itens existentes (selecione e clique Editar)
- **Exclua** itens (selecione e clique Excluir)
- Observe que os valores são convertidos para MAIÚSCULAS automaticamente

---

### ✅ Registros Antigos
- Veja dados de meses anteriores (arquivos JSON)
- Teste filtros por **Mês/Ano**
- Teste filtro por **Data específica**
- Teste filtros por **Técnico/Kit/Local**
- Clique em **ℹ️ INFO** para ver histórico

---

### ✅ Estatísticas
- Veja os **KPIs** coloridos no topo:
  - Total de Visitas
  - Visitas Concluídas
  - Técnicos Ativos
  - Locais Visitados
  - Taxa de Conclusão
- Veja o **gráfico de evolução temporal** (Plotly interativo)
- Veja **Top 5 Kits** (gráfico de barras)
- Veja **Top 5 Rankings** (Técnicos e Locais)
- Veja **Métricas de Performance** (barras de progresso)

---

### ✅ Exportações
- Clique em **📄 EXPORTAR PDF** para gerar relatório completo
- Clique em **📄 EXPORTAR CSV** para exportar dados

---

### ✅ Tema
- Clique no botão **TEMA ESCURO/CLARO** no canto superior direito
- Observe as cores se adaptarem em toda a interface

---

## 📊 O que você vai ver

### Estatísticas incluem:
- 📈 Gráficos Plotly interativos (hover para detalhes)
- 📊 Gráficos Matplotlib estáticos
- 🎯 KPIs visuais com cores
- 📉 Evolução temporal
- 🏆 Top 5 técnicos, locais e kits
- ⏱️ Duração média das tarefas

### Arquivos Criados:
```
kit_control_final/
├── kit_control.db          (banco de dados SQLite)
└── arquivos_mensais/
    ├── registros_11_2024.json
    ├── registros_12_2024.json
    ├── registros_01_2025.json
    ├── registros_02_2025.json
    ├── ...
    └── registros_11_2025.json
```

---

## 🎯 Recursos para Testar

| Recurso | Como Testar |
|---------|-------------|
| **Filtros** | Combine diferentes filtros na aba principal |
| **Calendário** | Clique no ícone 📅 ao lado do campo de data |
| **Gráficos** | Passe o mouse sobre os gráficos Plotly |
| **Exportações** | Exporte PDF e CSV na aba Estatísticas |
| **Histórico** | Selecione um registro e clique INFO |
| **Temas** | Alterne entre claro/escuro no cabeçalho |
| **Arquivos** | Navegue por diferentes meses em Registros Antigos |
| **CRUD** | Adicione, edite e exclua itens em Gerenciar |

---

## 💡 Dicas

### Limpar dados e começar do zero:
```bash
python gerar_dados_teste.py
# Responda "S" quando perguntar se quer limpar dados
```

### Adicionar mais dados:
```bash
python gerar_dados_teste.py
# Responda "N" para manter dados existentes
```

### Testar filtros:
- Use diferentes combinações de Mês/Ano
- Filtre por data específica
- Combine filtros de Técnico + Local

### Ver detalhes de um registro:
1. Selecione o registro na tabela
2. Clique no botão **ℹ️ INFO**
3. Veja o histórico de criação e alterações

### Testar validações:
- Tente salvar registro com campos obrigatórios vazios
- Tente inserir data inválida (ex: 32/13/2025)
- Tente inserir horário inválido (ex: 25:99)

---

## 🐛 Resolução de Problemas

### Erro de importação de módulo:
```bash
# Certifique-se de estar no diretório correto
cd kit_control_final
python main.py
```

### Erro de dependência:
```bash
pip install --upgrade -r requirements.txt
```

### Banco de dados corrompido:
```bash
# Delete o arquivo e gere novamente
rm kit_control.db
python gerar_dados_teste.py
```

### Gráficos não aparecem:
```bash
# Reinstale matplotlib
pip install --upgrade matplotlib
```

---

## 📝 Checklist de Testes

- [ ] Instalar dependências
- [ ] Gerar dados de teste
- [ ] Executar sistema
- [ ] Testar filtros na aba principal
- [ ] Criar novo registro
- [ ] Editar registro existente
- [ ] Ver histórico de registro
- [ ] Navegar por Registros Antigos
- [ ] Ver estatísticas e gráficos
- [ ] Exportar PDF
- [ ] Exportar CSV
- [ ] Alternar tema claro/escuro
- [ ] Gerenciar técnicos
- [ ] Gerenciar locais
- [ ] Gerenciar kits

---

**Divirta-se testando! 🎉**