# 📝 Changelog - Sistema de Controle de Kits

## Versão 2.0.0 (Novembro 2025)

### ✨ Nova Arquitetura MVC

O sistema foi completamente refatorado para uma arquitetura MVC (Model-View-Controller) limpa e modular.

---

## 🏗️ Mudanças Estruturais

### Database Centralizado
Agora **TODAS** as tabelas são criadas automaticamente pelo `models/database.py`:

- ✅ `registros` - Registros de visitas/manutenções
- ✅ `tecnicos` - Cadastro de técnicos
- ✅ `locais` - Cadastro de locais
- ✅ `kits` - Cadastro de kits
- ✅ `config` - Configurações do sistema
- ✅ `registro_historico` - Histórico de alterações

### Antes:
```python
# main_window.py criava as tabelas
# gerar_dados_teste.py também criava as tabelas
# Código duplicado em 2 lugares
```

### Agora:
```python
# database.py cria TUDO automaticamente
# main.py → Database → cria tabelas
# gerar_dados_teste.py → Database → cria tabelas
# Código centralizado em 1 lugar!
```

---

## 📊 Estrutura de Arquivos

| Arquivo | Linhas | Descrição |
|---------|--------|-----------|
| `main.py` | 10 | Ponto de entrada |
| `settings.py` | 14 | Configurações |
| `database.py` | 102 | Model - Banco de dados |
| `main_window.py` | 1411 | View Principal |
| `stats_manager.py` | 1308 | Gerenciador de Estatísticas |
| `record_window.py` | 387 | Janela de Registros |
| `scrollable_combobox.py` | 186 | Widget ComboBox |
| `progress_dialog.py` | 132 | Diálogo de Progresso |
| `history_dialog.py` | 100 | Diálogo de Histórico |
| `helpers.py` | 77 | Funções auxiliares |
| `tooltip.py` | 31 | Widget Tooltip |
| `gerar_dados_teste.py` | 468 | Gerador de dados |
| **Total** | **4226** | - |

---

## 🆕 Novidades

### StatsManager Separado
- Gerenciador de estatísticas completamente isolado
- 1308 linhas de código dedicado
- Gráficos Matplotlib e Plotly
- Exportação PDF e CSV/Excel
- Cleanup automático de figuras

### Widgets Customizados
- `ScrollableComboBox` - ComboBox com scroll para muitos itens
- `ProgressDialog` - Diálogo de progresso com barra
- `Tooltip` - Dicas ao passar o mouse

### Sistema de Histórico
- Rastreamento de todas alterações
- Criação, edição e exclusão registrados
- Visualização completa do histórico por registro

---

## 🎯 Benefícios

1. ✅ **Sem erros de tabela não encontrada**
   - Database sempre cria tudo automaticamente

2. ✅ **Código não duplicado**
   - Uma única fonte de verdade

3. ✅ **Mais fácil manutenção**
   - Mudar schema? Apenas em database.py

4. ✅ **Funciona em qualquer lugar**
   - `main.py` → cria banco
   - `gerar_dados_teste.py` → cria banco
   - Qualquer script → cria banco

5. ✅ **Estatísticas otimizadas**
   - Fechamento correto de figuras matplotlib
   - Sem memory leak

6. ✅ **Interface responsiva**
   - Tela de progresso em exportações
   - Feedback visual ao usuário

---

## 🔧 Correções

- Fix: Memory leak em gráficos matplotlib
- Fix: Scroll em ComboBox com muitos itens
- Fix: Cores do tema escuro em dropdowns
- Fix: Validação de datas e horários
- Fix: Arquivamento mensal automático

---

## 📦 Dependências Atualizadas

```
customtkinter>=5.2.0
tkcalendar>=1.6.1
matplotlib>=3.7.0
plotly>=5.15.0
openpyxl>=3.1.2
Pillow>=10.0.0
reportlab>=4.0.0
numpy>=1.24.0
```

---

**Sistema de Controle de Kits v2.0.0** 🎉