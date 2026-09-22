import os
import re

# 1. Atualizar obter_historico_avaliacoes para aceitar e usar o caminho da base de dados fornecido
db_path_file = 'services/database_service.py'
if os.path.exists(db_path_file):
    with open(db_path_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    target_func = '''def obter_historico_avaliacoes(*args, **kwargs):
    import pandas as pd
    import sqlite3
    db_file = args[0] if args else 'database.db'
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='avaliacoes'")
        if not cursor.fetchone():
            conn.close()
            return pd.DataFrame()
        df = pd.read_sql_query('SELECT * FROM avaliacoes', conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()'''
        
    if 'def obter_historico_avaliacoes' in content:
        content = re.sub(r'def obter_historico_avaliacoes.*?(?=\ndef |\Z)', target_func, content, flags=re.DOTALL)
    else:
        content += '\n\n' + target_func
        
    with open(db_path_file, 'w', encoding='utf-8') as f:
        f.write(content)

# 2. Corrigir o texto do veto em todo o código e testes se necessário
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith('.py'):
            p = os.path.join(root, file)
            with open(p, 'r', encoding='utf-8') as f:
                c = f.read()
            modified = False
            if 'Veto de Governança' in c:
                c = c.replace('Veto de Governança', 'Veto de Governança')
                modified = True
            elif 'Veto de Governança
                c = c.replace('Veto de Governança, 'Veto de Governança')
                modified = True
            if modified:
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(c)

print('Ajustes finais aplicados com sucesso!')
