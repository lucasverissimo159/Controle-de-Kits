#!/usr/bin/env python3
"""
Gerador de Dados de Teste para o Sistema de Controle de Kits
Gera registros para todos os meses de 2023, 2024, 2025 e 2026
ATUALIZADO: Com sistema de matrículas para técnicos
"""
import sqlite3
import random
from datetime import datetime, timedelta
import os
import json
from models.database import Database

# Configurações
DB_NAME = 'kit_control.db'
ARCHIVE_DIR = 'arquivos_mensais'

# Dados para gerar - ATUALIZADO com matrículas
TECNICOS = [
    {"nome": "JOÃO SILVA", "matricula": "MAT0001"},
    {"nome": "MARIA SANTOS", "matricula": "MAT0002"},
    {"nome": "PEDRO OLIVEIRA", "matricula": "MAT0003"},
    {"nome": "ANA COSTA", "matricula": "MAT0004"},
    {"nome": "CARLOS SOUZA", "matricula": "MAT0005"},
    {"nome": "JULIANA LIMA", "matricula": "MAT0006"},
    {"nome": "RICARDO ALVES", "matricula": "MAT0007"},
    {"nome": "FERNANDA ROCHA", "matricula": "MAT0008"},
    {"nome": "BRUNO MARTINS", "matricula": "MAT0009"},
    {"nome": "PATRICIA FERNANDES", "matricula": "MAT0010"},
    # Adicionar técnicos com NOMES IGUAIS para testar matrícula
    {"nome": "JOÃO SILVA", "matricula": "MAT0011"},  # Mesmo nome, matrícula diferente
    {"nome": "MARIA SANTOS", "matricula": "MAT0012"},  # Mesmo nome, matrícula diferente
]

LOCAIS = [
    "FILIAL CENTRO", "FILIAL NORTE", "FILIAL SUL",
    "FILIAL LESTE", "FILIAL OESTE", "MATRIZ",
    "ALMOXARIFADO CENTRAL", "LOJA SHOPPING", 
    "DEPÓSITO A", "UNIDADE INDUSTRIAL"
]

KITS = [
    "KIT-001", "KIT-002", "KIT-003", "KIT-004", "KIT-005",
    "KIT-006", "KIT-007", "KIT-008", "KIT-009", "KIT-010",
    "KIT-011", "KIT-012", "KIT-013", "KIT-014", "KIT-015",
    "KIT-020", "KIT-025", "KIT-030", "KIT-035", "KIT-040"
]

def criar_banco():
    """Cria conexão com banco e inicializa estrutura"""
    print("🔧 Inicializando banco de dados...")
    db = Database(DB_NAME)
    print("✅ Estrutura do banco criada automaticamente")
    return db.conn, db.cursor

def limpar_dados_anteriores(cursor, conn):
    """Limpa dados de teste anteriores"""
    print("🗑️  Limpando dados anteriores...")
    
    cursor.execute("DELETE FROM registros")
    cursor.execute("DELETE FROM tecnicos")
    cursor.execute("DELETE FROM locais")
    cursor.execute("DELETE FROM kits")
    cursor.execute("DELETE FROM registro_historico")
    
    conn.commit()
    print("✅ Dados anteriores removidos")

def cadastrar_tecnicos(cursor, conn):
    """Cadastra técnicos COM MATRÍCULA"""
    print("\n👷 Cadastrando técnicos com matrícula...")
    
    for tecnico in TECNICOS:
        cursor.execute('''
            INSERT INTO tecnicos (nome, matricula) VALUES (?, ?)
        ''', (tecnico['nome'], tecnico['matricula']))
    
    conn.commit()
    print(f"✅ {len(TECNICOS)} técnicos cadastrados")
    
    # Mostrar técnicos com nomes duplicados
    duplicados = {}
    for tec in TECNICOS:
        if tec['nome'] in duplicados:
            duplicados[tec['nome']].append(tec['matricula'])
        else:
            duplicados[tec['nome']] = [tec['matricula']]
    
    print("\n📋 Técnicos com nomes duplicados:")
    for nome, matriculas in duplicados.items():
        if len(matriculas) > 1:
            print(f"   • {nome}:")
            for mat in matriculas:
                print(f"      - Matrícula: {mat}")

def cadastrar_locais(cursor, conn):
    """Cadastra locais"""
    print("\n📍 Cadastrando locais...")
    
    for local in LOCAIS:
        cursor.execute("INSERT INTO locais (nome) VALUES (?)", (local,))
    
    conn.commit()
    print(f"✅ {len(LOCAIS)} locais cadastrados")

def cadastrar_kits(cursor, conn):
    """Cadastra kits"""
    print("\n📦 Cadastrando kits...")
    
    for kit in KITS:
        cursor.execute("INSERT INTO kits (numero) VALUES (?)", (kit,))
    
    conn.commit()
    print(f"✅ {len(KITS)} kits cadastrados")

def gerar_horario_aleatorio():
    """Gera horário aleatório"""
    hora_inicio = random.randint(7, 17)
    minuto_inicio = random.choice([0, 15, 30, 45])
    
    duracao_horas = random.randint(1, 4)
    duracao_minutos = random.choice([0, 15, 30, 45])
    
    inicio = f"{hora_inicio:02d}:{minuto_inicio:02d}"
    
    # Calcular fim
    total_minutos_inicio = hora_inicio * 60 + minuto_inicio
    total_minutos_fim = total_minutos_inicio + (duracao_horas * 60) + duracao_minutos
    
    hora_fim = (total_minutos_fim // 60) % 24
    minuto_fim = total_minutos_fim % 60
    
    fim = f"{hora_fim:02d}:{minuto_fim:02d}"
    
    return inicio, fim

def obter_dias_mes(mes, ano):
    """Retorna o número de dias do mês"""
    if mes == 2:
        # Ano bissexto
        if (ano % 4 == 0 and ano % 100 != 0) or (ano % 400 == 0):
            return 29
        return 28
    elif mes in [4, 6, 9, 11]:
        return 30
    else:
        return 31

def gerar_registros_ano(cursor, conn, ano, mes_inicio=1, mes_fim=12, dia_max_ultimo_mes=None):
    """Gera registros para um ano específico - ATUALIZADO com matrícula"""
    print(f"\n📊 Gerando registros para {ano}...")
    
    total_registros = 0
    registros_incompletos = 0
    
    for mes in range(mes_inicio, mes_fim + 1):
        # Determinar número máximo de dias para o mês
        dias_mes = obter_dias_mes(mes, ano)
        
        # Se for o último mês e houver limite de dia, usar esse limite
        if mes == mes_fim and dia_max_ultimo_mes:
            dias_mes = min(dias_mes, dia_max_ultimo_mes)
        
        # Número de registros para o mês
        num_registros = random.randint(15, 45)
        
        print(f"   Mês {mes:02d}/{ano}: {num_registros} registros")
        
        for _ in range(num_registros):
            dia = random.randint(1, dias_mes)
            data_inicio = f"{dia:02d}/{mes:02d}/{ano}"
            
            # Selecionar técnico aleatório e usar MATRÍCULA
            tecnico_info = random.choice(TECNICOS)
            matricula_tecnico = tecnico_info['matricula']
            
            local = random.choice(LOCAIS)
            kit = random.choice(KITS)
            
            horario_inicio, _ = gerar_horario_aleatorio()
            
            # Para dezembro/2026, 30% dos registros serão incompletos
            if ano == 2026 and mes == 12:
                if random.random() < 0.30:
                    data_fim = None
                    horario_fim = None
                    registros_incompletos += 1
                else:
                    dias_duracao = random.choices([0, 1, 2], weights=[80, 15, 5])[0]
                    
                    if dias_duracao == 0:
                        data_fim = data_inicio
                    else:
                        data_obj = datetime(ano, mes, dia)
                        data_fim_obj = data_obj + timedelta(days=dias_duracao)
                        # Garantir que não ultrapasse o limite de dias do mês
                        if dia_max_ultimo_mes and data_fim_obj.day > dia_max_ultimo_mes:
                            data_fim = f"{dia_max_ultimo_mes:02d}/{mes:02d}/{ano}"
                        else:
                            data_fim = data_fim_obj.strftime("%d/%m/%Y")
                    
                    _, horario_fim = gerar_horario_aleatorio()
            else:
                # Registros normais (completos)
                dias_duracao = random.choices([0, 1, 2, 3], weights=[70, 20, 7, 3])[0]
                
                if dias_duracao == 0:
                    data_fim = data_inicio
                else:
                    data_obj = datetime(ano, mes, dia)
                    data_fim_obj = data_obj + timedelta(days=dias_duracao)
                    data_fim = data_fim_obj.strftime("%d/%m/%Y")
                
                _, horario_fim = gerar_horario_aleatorio()
            
            # INSERIR COM MATRÍCULA ao invés de nome
            cursor.execute('''
                INSERT INTO registros 
                (data_inicio, data_fim, matricula_tecnico, num_kit, local, 
                 horario_inicio, horario_fim)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data_inicio, data_fim, matricula_tecnico, kit, local, 
                  horario_inicio, horario_fim))
            
            total_registros += 1
    
    conn.commit()
    
    if registros_incompletos > 0:
        print(f"\n✅ Total {ano}: {total_registros} registros gerados")
        print(f"⚠️  Registros incompletos: {registros_incompletos}")
    else:
        print(f"\n✅ Total {ano}: {total_registros} registros gerados")
    
    return total_registros, registros_incompletos

def criar_arquivos_mensais(cursor):
    """Cria arquivos JSON mensais - ATUALIZADO com matrícula"""
    print("\n📁 Criando arquivos mensais...")
    
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)
    
    total_arquivos = 0
    
    # Para cada ano de 2023 a 2026
    for ano in [2023, 2024, 2025, 2026]:
        # Para cada mês
        for mes in range(1, 13):
            cursor.execute('''
                SELECT r.*, t.nome as tecnico_nome
                FROM registros r
                JOIN tecnicos t ON r.matricula_tecnico = t.matricula
                WHERE substr(r.data_inicio, 4, 2) = ? 
                AND substr(r.data_inicio, 7, 4) = ?
            ''', (f"{mes:02d}", str(ano)))
            
            registros = cursor.fetchall()
            
            if not registros:
                continue
            
            filename = f"{ARCHIVE_DIR}/registros_{mes:02d}_{ano}.json"
            
            dados = []
            for reg in registros:
                dados.append({
                    'id': reg[0],
                    'data_inicio': reg[1],
                    'data_fim': reg[2],
                    'matricula_tecnico': reg[3],
                    'tecnico_nome': reg[8],  # Nome do técnico (join)
                    'num_kit': reg[4],
                    'local': reg[5],
                    'horario_inicio': reg[6],
                    'horario_fim': reg[7]
                })
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ {filename} ({len(registros)} registros)")
            total_arquivos += 1
    
    print(f"\n✅ {total_arquivos} arquivos mensais criados")

def exibir_estatisticas(cursor):
    """Exibe estatísticas dos dados gerados - ATUALIZADO com matrícula"""
    print("\n" + "="*60)
    print("📊 ESTATÍSTICAS DOS DADOS GERADOS")
    print("="*60)
    
    cursor.execute("SELECT COUNT(*) FROM registros")
    total = cursor.fetchone()[0]
    print(f"\n📌 Total de Registros: {total}")
    
    # Registros incompletos
    cursor.execute('''
        SELECT COUNT(*) FROM registros 
        WHERE data_fim IS NULL OR horario_fim IS NULL
    ''')
    incompletos = cursor.fetchone()[0]
    print(f"⚠️  Registros Incompletos: {incompletos}")
    
    # Registros por ano
    print("\n📅 Registros por Ano:")
    for ano in [2023, 2024, 2025, 2026]:
        cursor.execute('''
            SELECT COUNT(*) FROM registros 
            WHERE substr(data_inicio, 7, 4) = ?
        ''', (str(ano),))
        count = cursor.fetchone()[0]
        print(f"   {ano}: {count} registros")
    
    # Top 5 técnicos (por matrícula + nome)
    print("\n👷 Top 5 Técnicos:")
    cursor.execute('''
        SELECT t.matricula, t.nome, COUNT(*) as total 
        FROM registros r
        JOIN tecnicos t ON r.matricula_tecnico = t.matricula
        GROUP BY t.matricula, t.nome
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (matricula, nome, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {nome} ({matricula}): {total} registros")
    
    # Mostrar técnicos com nomes duplicados
    print("\n🔍 Verificando técnicos com nomes duplicados:")
    cursor.execute('''
        SELECT nome, GROUP_CONCAT(matricula, ', ') as matriculas, COUNT(*) as qtd
        FROM tecnicos
        GROUP BY nome
        HAVING qtd > 1
    ''')
    duplicados = cursor.fetchall()
    if duplicados:
        for nome, matriculas, qtd in duplicados:
            print(f"   • {nome}: {qtd} técnicos")
            print(f"      Matrículas: {matriculas}")
            
            # Contar registros por matrícula
            for mat in matriculas.split(', '):
                cursor.execute('''
                    SELECT COUNT(*) FROM registros WHERE matricula_tecnico=?
                ''', (mat,))
                count = cursor.fetchone()[0]
                print(f"         {mat}: {count} registros")
    else:
        print("   Nenhum técnico com nome duplicado")
    
    # Top 5 locais
    print("\n📍 Top 5 Locais:")
    cursor.execute('''
        SELECT local, COUNT(*) as total 
        FROM registros 
        GROUP BY local 
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (local, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {local}: {total} registros")
    
    # Top 5 kits
    print("\n📦 Top 5 Kits:")
    cursor.execute('''
        SELECT num_kit, COUNT(*) as total 
        FROM registros 
        GROUP BY num_kit 
        ORDER BY total DESC 
        LIMIT 5
    ''')
    for i, (kit, total) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {kit}: {total} registros")
    
    print("\n" + "="*60)

def main():
    """Função principal"""
    print("="*60)
    print("🎲 GERADOR DE DADOS DE TESTE")
    print("Sistema de Controle de Kits - COM MATRÍCULA")
    print("="*60)
    print("\n📆 Período: Janeiro/2023 até Dezembro/2026")
    print("⚠️  Dezembro/2026 terá registros incompletos")
    print("🆔 Sistema de matrícula implementado")
    
    conn, cursor = criar_banco()
    
    resposta = input("\n⚠️  Limpar dados existentes? (S/N): ").strip().upper()
    if resposta == 'S':
        limpar_dados_anteriores(cursor, conn)
    
    cadastrar_tecnicos(cursor, conn)
    cadastrar_locais(cursor, conn)
    cadastrar_kits(cursor, conn)
    
    # Gerar registros para 2023 (ano completo)
    total_2023, _ = gerar_registros_ano(cursor, conn, 2023)
    
    # Gerar registros para 2024 (ano completo)
    total_2024, _ = gerar_registros_ano(cursor, conn, 2024)
    
    # Gerar registros para 2025 (ano completo)
    total_2025, _ = gerar_registros_ano(cursor, conn, 2025)
    
    # Gerar registros para 2026 (ano completo, mas dezembro com incompletos)
    total_2026, incompletos = gerar_registros_ano(cursor, conn, 2026)
    
    criar_arquivos_mensais(cursor)
    
    exibir_estatisticas(cursor)
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ DADOS DE TESTE GERADOS COM SUCESSO!")
    print("="*60)
    print(f"\n📊 Total: {total_2023 + total_2024 + total_2025 + total_2026} registros criados")
    print(f"   - 2023 (Jan-Dez): {total_2023} registros")
    print(f"   - 2024 (Jan-Dez): {total_2024} registros")
    print(f"   - 2025 (Jan-Dez): {total_2025} registros")
    print(f"   - 2026 (Jan-Dez): {total_2026} registros")
    print(f"   - Incompletos: {incompletos} registros")
    print(f"\n🆔 {len(TECNICOS)} técnicos cadastrados com matrícula")
    print(f"   Matrículas: MAT0001 até MAT{len(TECNICOS):04d}")
    print(f"\n📁 Arquivos JSON salvos em: {ARCHIVE_DIR}/")
    print(f"💾 Banco de dados: {DB_NAME}")
    print("\n🚀 Execute 'python main.py' para testar o sistema!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()