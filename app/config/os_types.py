"""Mappings for OS types and areas.

⚡ AUDITORIA REALIZADA: 24/07/2025
📡 Fonte: Consulta à API /api/v3/tipo_servico/
🔍 IDs atualizados baseados na descoberta real da API

Edit IDs if API mappings change.
"""

# Tipos de OS - IDs reais da API
TIPO_PREVENTIVA = 1  # Manutenção Preventiva
TIPO_CALIBRACAO = 2  # Calibração
TIPO_CORRETIVA = 3  # Manutenção Corretiva
TIPO_VISITA_TECNICA = 4  # Visita Técnica
TIPO_EMPRESTIMO = 5  # Empréstimo
TIPO_TREINAMENTO = 6  # Treinamento
TIPO_TESTE_SEG_ELETRICA = 7  # Teste de Segurança Elétrica
TIPO_CHAMADO = 8  # Chamado
TIPO_INSTALACAO = 9  # Instalação
TIPO_TESTE_INICIAL = 10  # Teste Inicial
TIPO_PREDITIVA = 11  # Manutenção Preditiva
TIPO_VISTORIA_DIARIA_1 = 18  # Vistoria Diária
TIPO_VISTORIA_DIARIA_2 = 19  # Vistoria Diária (duplicata)
TIPO_MONITORAMENTO = 26  # Monitoramento Diário
TIPO_BUSCA_ATIVA = 28  # Busca Ativa
TIPO_INVENTARIO = 29  # Inventário
TIPO_ANALISE_INFRA = 30  # Análise de Infraestrutura
TIPO_INSPECAO_NR13 = 31  # Inspeção NR13

# Áreas - manter valores originais (não foram auditados ainda)
AREA_PREDIAL = 10
AREA_ENG_CLIN = 11

# NOTA: Compatibilidade com código antigo
# Estas constantes foram mantidas mas podem ter valores diferentes
# Para novos desenvolvimentos, use TipoOS enum de models.py
