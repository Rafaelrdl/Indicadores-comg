#!/usr/bin/env python3
"""
Teste final dos filtros corrigidos - simula exatamente o que o Streamlit fará.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.db import get_conn
from app.core.logging import app_logger
import pandas as pd
from datetime import date

def get_orders_with_correct_structure() -> pd.DataFrame:
    """
    Função idêntica à do Streamlit - testa a query corrigida.
    """
    sql = """
        SELECT
            json_extract(payload, '$.id') as id,
            json_extract(payload, '$.chamados') as chamados,
            json_extract(payload, '$.ordem_servico.data_criacao') as data_criacao,
            json_extract(payload, '$.ordem_servico.data_fechamento') as data_fechamento,
            json_extract(payload, '$.ordem_servico.estado') as estado,
            json_extract(payload, '$.ordem_servico.numero') as numero,
            json_extract(payload, '$.ordem_servico.tipo_servico') as tipo_id,
            json_extract(payload, '$.ordem_servico.problema') as problema_id,
            json_extract(payload, '$.responsavel_id') as responsavel_id,
            created_at,
            CASE 
                WHEN json_extract(payload, '$.ordem_servico.data_fechamento') IS NOT NULL 
                THEN 'FECHADA' 
                ELSE 'ABERTA' 
            END as status
        FROM orders
        WHERE json_extract(payload, '$.id') IS NOT NULL
        ORDER BY json_extract(payload, '$.ordem_servico.data_criacao') DESC
    """
    
    try:
        with get_conn() as conn:
            df = pd.read_sql_query(sql, conn)
            
        app_logger.log_info(f"📊 Carregadas {len(df)} ordens do SQLite com estrutura corrigida")
        return df
        
    except Exception as e:
        app_logger.log_error(e, {"context": "get_orders_with_correct_structure"})
        return pd.DataFrame()

def apply_date_filters(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """
    Função idêntica à do Streamlit - testa filtro corrigido.
    """
    if df.empty:
        return df
        
    try:
        df_filtered = df.copy()
        
        # Converter data_criacao do formato brasileiro para datetime
        def parse_brazilian_date(date_str):
            """Converte data do formato '19/04/23 - 15:58' para datetime."""
            if pd.isna(date_str) or date_str is None:
                return None
            try:
                # Formato: "19/04/23 - 15:58"
                date_part = str(date_str).split(' - ')[0]  # "19/04/23"
                return pd.to_datetime(date_part, format='%d/%m/%y')
            except:
                try:
                    # Tentar outros formatos possíveis
                    return pd.to_datetime(date_str, errors='coerce')
                except:
                    return None
        
        # Aplicar conversão
        df_filtered['data_criacao_dt'] = df_filtered['data_criacao'].apply(parse_brazilian_date)
        
        # Aplicar filtros de data
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date) + pd.Timedelta(days=1)  # Incluir dia final
        
        # Filtrar apenas registros com datas válidas no período
        df_filtered = df_filtered[
            df_filtered['data_criacao_dt'].notna() &
            (df_filtered['data_criacao_dt'] >= start_dt) &
            (df_filtered['data_criacao_dt'] < end_dt)
        ]
        
        # Remover coluna temporária
        df_filtered = df_filtered.drop('data_criacao_dt', axis=1)
        
        app_logger.log_info(f"📅 Filtro de data aplicado: {len(df_filtered)} registros de {len(df)} no período {start_date} a {end_date}")
        
        return df_filtered
        
    except Exception as e:
        print(f"Erro ao aplicar filtros de data: {e}")
        app_logger.log_error(e, {"context": "apply_date_filters"})
        return df

def test_complete_flow():
    """Teste do fluxo completo."""
    print("🚀 TESTE COMPLETO DO FLUXO DE FILTROS")
    print("="*60)
    
    # 1. Carregar dados
    print("📊 1. Carregando dados...")
    df_orders = get_orders_with_correct_structure()
    print(f"   Total de ordens: {len(df_orders)}")
    
    if df_orders.empty:
        print("❌ Nenhum dado encontrado!")
        return
    
    # 2. Mostrar amostra de datas
    print(f"\n📅 2. Amostra de datas:")
    sample_dates = df_orders['data_criacao'].dropna().head(5)
    for i, data in enumerate(sample_dates):
        print(f"   {i+1}. {data}")
    
    # 3. Testar filtro padrão (2024)
    print(f"\n🎛️ 3. Aplicando filtro padrão (2024)...")
    start_date = date(2024, 1, 1)
    end_date = date(2024, 12, 31)
    
    df_filtered = apply_date_filters(df_orders, start_date, end_date)
    print(f"   Filtrado: {len(df_filtered)} registros")
    
    # 4. Testar filtro menor (último mês de 2024)
    print(f"\n📆 4. Aplicando filtro menor (dezembro 2024)...")
    start_date_dec = date(2024, 12, 1)
    end_date_dec = date(2024, 12, 31)
    
    df_filtered_dec = apply_date_filters(df_orders, start_date_dec, end_date_dec)
    print(f"   Dezembro 2024: {len(df_filtered_dec)} registros")
    
    # 5. Mostrar estatísticas básicas
    if len(df_filtered) > 0:
        print(f"\n📈 5. Estatísticas (ano 2024):")
        estados = df_filtered['estado'].value_counts()
        status = df_filtered['status'].value_counts()
        
        print(f"   Estados:")
        for estado, count in estados.items():
            print(f"     Estado {estado}: {count} registros")
            
        print(f"   Status:")
        for st, count in status.items():
            print(f"     {st}: {count} registros")
    
    print(f"\n✅ Teste concluído com sucesso!")
    return len(df_filtered) > 0

if __name__ == "__main__":
    test_complete_flow()
