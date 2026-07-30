# 📊 Dados de Teste - Sistema de Controle de Kits

## Visão Geral

O script `gerar_dados_teste.py` cria um conjunto completo de dados fictícios para testar todas as funcionalidades do sistema.

---

## 📅 Período dos Dados

| Período | Meses | Quantidade |
|---------|-------|------------|
| **2024** | Novembro - Dezembro | 30-90 registros |
| **2025** | Janeiro - Novembro | 165-495 registros |
| **Total** | 13 meses | ~300-400 registros |

---

## 👷 Técnicos Cadastrados

```
1. JOÃO SILVA
2. MARIA SANTOS
3. PEDRO OLIVEIRA
4. ANA COSTA
5. CARLOS SOUZA
6. JULIANA LIMA
7. RICARDO ALVES
8. FERNANDA ROCHA
9. BRUNO MARTINS
10. PATRICIA FERNANDES
```

---

## 📍 Locais Cadastrados

```
1. FILIAL CENTRO
2. FILIAL NORTE
3. FILIAL SUL
4. FILIAL LESTE
5. FILIAL OESTE
6. MATRIZ
7. ALMOXARIFADO CENTRAL
8. LOJA SHOPPING
9. DEPÓSITO A
10. UNIDADE INDUSTRIAL
```

---

## 📦 Kits Cadastrados

```
KIT-001, KIT-002, KIT-003, KIT-004, KIT-005
KIT-006, KIT-007, KIT-008, KIT-009, KIT-010
KIT-011, KIT-012, KIT-013, KIT-014, KIT-015
KIT-020, KIT-025, KIT-030, KIT-035, KIT-040
```

Total: 20 kits

---

## 🎲 Características dos Dados

### Distribuição de Registros
- **15 a 45 registros por mês** (aleatório)
- **Distribuição uniforme** entre técnicos, locais e kits

### Duração das Visitas
| Duração | Probabilidade |
|---------|--------------|
| Mesmo dia | 70% |
| 1 dia | 20% |
| 2 dias | 7% |
| 3 dias | 3% |

### Horários
- **Início:** Entre 07:00 e 17:00
- **Duração:** 1 a 4 horas
- **Minutos:** 00, 15, 30 ou 45

### Registros Incompletos (Novembro/2025)
- **30% dos registros** de novembro não têm:
  - `data_fim` (NULL)
  - `horario_fim` (NULL)
- Simula registros em andamento

---

## 📁 Arquivos JSON Criados

```
arquivos_mensais/
├── registros_11_2024.json
├── registros_12_2024.json
├── registros_01_2025.json
├── registros_02_2025.json
├── registros_03_2025.json
├── registros_04_2025.json
├── registros_05_2025.json
├── registros_06_2025.json
├── registros_07_2025.json
├── registros_08_2025.json
├── registros_09_2025.json
├── registros_10_2025.json
└── registros_11_2025.json
```

### Formato do JSON
```json
[
  {
    "id": 1,
    "data_inicio": "15/11/2024",
    "data_fim": "15/11/2024",
    "tecnico": "JOÃO SILVA",
    "num_kit": "KIT-005",
    "local": "FILIAL CENTRO",
    "horario_inicio": "08:30",
    "horario_fim": "11:45"
  },
  ...
]
```

---

## 🗄️ Estrutura do Banco de Dados

### Tabela `registros`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| data_inicio | TEXT | DD/MM/AAAA |
| data_fim | TEXT | DD/MM/AAAA (pode ser NULL) |
| tecnico | TEXT | Nome do técnico |
| num_kit | TEXT | Número do kit |
| local | TEXT | Nome do local |
| horario_inicio | TEXT | HH:MM |
| horario_fim | TEXT | HH:MM (pode ser NULL) |

### Tabela `tecnicos`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome único |

### Tabela `locais`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| nome | TEXT | Nome único |

### Tabela `kits`
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| id | INTEGER | Chave primária |
| numero | TEXT | Número único |

---

## 🚀 Como Usar

### Gerar dados (limpa anteriores)
```bash
python gerar_dados_teste.py
# Responda "S" para limpar dados anteriores
```

### Adicionar mais dados
```bash
python gerar_dados_teste.py
# Responda "N" para manter dados existentes
```

### Saída esperada
```
============================================================
🎲 GERADOR DE DADOS DE TESTE
Sistema de Controle de Kits
============================================================

📆 Período: Nov-Dez/2024 + Jan-Nov/2025 (até 22/11)
⚠️  Novembro/2025 terá registros incompletos

⚠️  Limpar dados existentes? (S/N): S

🔧 Inicializando banco de dados...
✅ Estrutura do banco criada automaticamente
🗑️  Limpando dados anteriores...
✅ Dados anteriores removidos

👷 Cadastrando técnicos...
✅ 10 técnicos cadastrados

📍 Cadastrando locais...
✅ 10 locais cadastrados

📦 Cadastrando kits...
✅ 20 kits cadastrados

📊 Gerando registros para novembro e dezembro de 2024...
   Mês 11/2024: 32 registros
   Mês 12/2024: 28 registros

✅ Total 2024: 60 registros gerados

📊 Gerando registros para 2025 (janeiro a novembro)...
   Mês 01/2025: 25 registros
   Mês 02/2025: 31 registros
   ...
   Mês 11/2025 (até dia 22): 28 registros
   ⚠️  Alguns registros terão Data Fim e Horário Fim vazios

✅ Total 2025: 298 registros gerados
⚠️  Registros incompletos (novembro): 8

📁 Criando arquivos mensais...
   ✅ arquivos_mensais/registros_11_2024.json (32 registros)
   ✅ arquivos_mensais/registros_12_2024.json (28 registros)
   ...

============================================================
📊 ESTATÍSTICAS DOS DADOS GERADOS
============================================================

📌 Total de Registros: 358
⚠️  Registros Incompletos: 8

📅 Registros por Mês (2024):
   Mês 11: 32 registros
   Mês 12: 28 registros

📅 Registros por Mês (2025):
   Mês 01: 25 registros
   ...

👷 Top 5 Técnicos:
   1. MARIA SANTOS: 42 registros
   2. JOÃO SILVA: 38 registros
   ...

📍 Top 5 Locais:
   1. MATRIZ: 45 registros
   ...

📦 Top 5 Kits:
   1. KIT-007: 28 registros
   ...

============================================================
✅ DADOS DE TESTE GERADOS COM SUCESSO!
============================================================
```

---

## 📈 Estatísticas Típicas

Após gerar os dados, você verá estatísticas como:

| Métrica | Valor Típico |
|---------|-------------|
| Total de registros | 300-400 |
| Registros por mês | 15-45 |
| Registros incompletos | 6-12 |
| Técnicos ativos | 10 |
| Locais utilizados | 10 |
| Kits em uso | 20 |

---

## 💡 Dicas

### Testar filtros
Com ~350 registros distribuídos em 13 meses, você tem dados suficientes para:
- Filtrar por diferentes meses
- Ver variações nos gráficos
- Testar exportações completas

### Testar registros incompletos
Novembro/2025 tem registros sem data/hora fim, útil para testar:
- Exibição de campos vazios
- Cálculo de taxa de conclusão
- Filtros de registros em andamento

### Resetar o ambiente
```bash
rm kit_control.db
rm -rf arquivos_mensais/
python gerar_dados_teste.py
```

---

## ⚠️ Observações

1. **Dados são aleatórios** - cada execução gera valores diferentes
2. **IDs são sequenciais** - começam em 1 após limpar
3. **Arquivos JSON** - são recriados a cada execução
4. **Banco SQLite** - arquivo `kit_control.db` na raiz do projeto

---

**Gerador de Dados v2.0** 🎲