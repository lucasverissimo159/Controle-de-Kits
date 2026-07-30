"""
Gerenciamento de banco de dados com suporte a histÃ³rico e matrÃ­cula
Cria e gerencia todas as tabelas do sistema
"""
import sqlite3
from datetime import datetime


class Database:
    """Classe para gerenciar banco de dados"""
    
    def __init__(self, db_name='kit_control.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_all_tables()
        self.migrate_to_matricula()  # MigraÃ§Ã£o automÃ¡tica
    
    def create_all_tables(self):
        """Cria TODAS as tabelas do sistema se nÃ£o existirem"""
        
        # Tabela de registros - ATUALIZADA com matricula_tecnico
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS registros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_inicio TEXT NOT NULL,
                data_fim TEXT,
                matricula_tecnico TEXT NOT NULL,
                num_kit TEXT NOT NULL,
                local TEXT NOT NULL,
                horario_inicio TEXT NOT NULL,
                horario_fim TEXT,
                FOREIGN KEY (matricula_tecnico) REFERENCES tecnicos(matricula)
            )
        ''')
        
        # Tabela de tÃ©cnicos - ATUALIZADA com matrÃ­cula
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tecnicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                matricula TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tabela de locais
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS locais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tabela de kits
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tabela de configuraÃ§Ãµes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
        ''')
        
        # Tabela de histÃ³rico de alteraÃ§Ãµes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS registro_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                registro_id INTEGER NOT NULL,
                campo_alterado TEXT NOT NULL,
                valor_anterior TEXT,
                valor_novo TEXT,
                data_alteracao TEXT NOT NULL,
                tipo_operacao TEXT NOT NULL,
                FOREIGN KEY (registro_id) REFERENCES registros(id)
            )
        ''')
        
        self.conn.commit()
    
    def migrate_to_matricula(self):
        """MigraÃ§Ã£o automÃ¡tica de banco antigo para novo formato com matrÃ­cula"""
        try:
            # Verificar se jÃ¡ tem coluna matricula_tecnico
            self.cursor.execute("PRAGMA table_info(registros)")
            columns = [col[1] for col in self.cursor.fetchall()]
            
            if 'matricula_tecnico' in columns:
                # JÃ¡ estÃ¡ no novo formato
                return
            
            print("ðŸ”„ Migrando banco de dados para formato com matrÃ­cula...")
            
            # Verificar se tem coluna 'tecnico' (formato antigo)
            if 'tecnico' not in columns:
                # Tabela vazia ou jÃ¡ migrada
                return
            
            # 1. Criar tabela temporÃ¡ria nova
            self.cursor.execute('''
                CREATE TABLE registros_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT,
                    matricula_tecnico TEXT NOT NULL,
                    num_kit TEXT NOT NULL,
                    local TEXT NOT NULL,
                    horario_inicio TEXT NOT NULL,
                    horario_fim TEXT,
                    FOREIGN KEY (matricula_tecnico) REFERENCES tecnicos(matricula)
                )
            ''')
            
            # 2. Obter todos os tÃ©cnicos Ãºnicos da tabela antiga
            self.cursor.execute("SELECT DISTINCT tecnico FROM registros")
            tecnicos_antigos = [row[0] for row in self.cursor.fetchall()]
            
            # 3. Criar matrÃ­culas para tÃ©cnicos existentes
            matricula_map = {}
            for i, nome in enumerate(tecnicos_antigos, start=1):
                matricula = f"MAT{i:04d}"
                matricula_map[nome] = matricula
                
                # Verificar se tÃ©cnico jÃ¡ existe na nova tabela
                self.cursor.execute("SELECT matricula FROM tecnicos WHERE nome=?", (nome,))
                existing = self.cursor.fetchone()
                
                if existing:
                    matricula_map[nome] = existing[0]
                else:
                    # Inserir na tabela de tÃ©cnicos
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO tecnicos (nome, matricula) 
                        VALUES (?, ?)
                    ''', (nome, matricula))
            
            # 4. Copiar dados para tabela nova com matrÃ­cula
            self.cursor.execute("SELECT * FROM registros")
            registros_antigos = self.cursor.fetchall()
            
            for reg in registros_antigos:
                id_reg, data_inicio, data_fim, tecnico, num_kit, local, horario_inicio, horario_fim = reg
                matricula = matricula_map.get(tecnico)
                
                if matricula:
                    self.cursor.execute('''
                        INSERT INTO registros_new 
                        (id, data_inicio, data_fim, matricula_tecnico, num_kit, local, 
                         horario_inicio, horario_fim)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (id_reg, data_inicio, data_fim, matricula, num_kit, local, 
                          horario_inicio, horario_fim))
            
            # 5. Substituir tabela antiga pela nova
            self.cursor.execute("DROP TABLE registros")
            self.cursor.execute("ALTER TABLE registros_new RENAME TO registros")
            
            self.conn.commit()
            print(f"âœ… MigraÃ§Ã£o concluÃ­da! {len(tecnicos_antigos)} tÃ©cnicos migrados")
            print(f"   MatrÃ­culas geradas: MAT0001 atÃ© MAT{len(tecnicos_antigos):04d}")
            
        except Exception as e:
            print(f"âš ï¸ Erro na migraÃ§Ã£o: {e}")
            self.conn.rollback()
    
    def add_history(self, registro_id, tipo, campo, anterior, novo):
        """Adiciona entrada no histÃ³rico"""
        self.cursor.execute('''
            INSERT INTO registro_historico 
            (registro_id, campo_alterado, valor_anterior, valor_novo, 
             data_alteracao, tipo_operacao)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (registro_id, campo, anterior, novo, 
              datetime.now().strftime('%d/%m/%Y %H:%M:%S'), tipo))
        self.conn.commit()
    
    def get_history(self, registro_id):
        """Busca histÃ³rico de um registro"""
        self.cursor.execute('''
            SELECT campo_alterado, valor_anterior, valor_novo, 
                   data_alteracao, tipo_operacao
            FROM registro_historico
            WHERE registro_id=?
            ORDER BY data_alteracao DESC
        ''', (registro_id,))
        return self.cursor.fetchall()
    
    def atualizar_nome_tecnico_em_cascata(self, matricula, nome_novo):
        """
        Atualiza o nome de um tÃ©cnico e TODOS os registros histÃ³ricos
        (tanto no banco quanto nos arquivos mensais JSON)
        """
        # 1. Buscar nome anterior
        self.cursor.execute("SELECT nome FROM tecnicos WHERE matricula=?", (matricula,))
        resultado = self.cursor.fetchone()
        
        if not resultado:
            return False, "MatrÃ­cula nÃ£o encontrada"
        
        nome_anterior = resultado[0]
        
        if nome_anterior == nome_novo:
            return True, "Nome nÃ£o foi alterado"
        
        # 2. Atualizar tabela de tÃ©cnicos
        self.cursor.execute('''
            UPDATE tecnicos SET nome=? WHERE matricula=?
        ''', (nome_novo, matricula))
        
        # 3. Registrar no histÃ³rico (para auditoria)
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        self.cursor.execute('''
            INSERT INTO registro_historico 
            (registro_id, campo_alterado, valor_anterior, valor_novo, 
             data_alteracao, tipo_operacao)
            VALUES (0, ?, ?, ?, ?, ?)
        ''', ('tecnico_nome_global', nome_anterior, nome_novo, timestamp, 'UPDATE_CASCADE'))
        
        # 4. Contar quantos registros serÃ£o afetados
        self.cursor.execute('''
            SELECT COUNT(*) FROM registros WHERE matricula_tecnico=?
        ''', (matricula,))
        total_afetados = self.cursor.fetchone()[0]
        
        self.conn.commit()
        
        return True, f"Nome atualizado! {total_afetados} registros vinculados Ã  matrÃ­cula {matricula}"
    
    def buscar_tecnico_por_matricula(self, matricula):
        """Busca informaÃ§Ãµes do tÃ©cnico pela matrÃ­cula"""
        self.cursor.execute('''
            SELECT id, nome, matricula FROM tecnicos WHERE matricula=?
        ''', (matricula,))
        return self.cursor.fetchone()
    
    def buscar_tecnico_por_nome(self, nome):
        """Busca tÃ©cnicos por nome (pode retornar mÃºltiplos se houver nomes duplicados)"""
        self.cursor.execute('''
            SELECT id, nome, matricula FROM tecnicos WHERE nome LIKE ?
        ''', (f'%{nome}%',))
        return self.cursor.fetchall()
    
    def get_all_tecnicos_com_matricula(self):
        """Retorna todos os tÃ©cnicos com matrÃ­cula"""
        self.cursor.execute('''
            SELECT id, nome, matricula FROM tecnicos ORDER BY nome
        ''')
        return self.cursor.fetchall()