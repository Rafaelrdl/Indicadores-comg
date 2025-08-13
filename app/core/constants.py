"""Application constants and enums."""

from enum import Enum

# Date and Time Constants
DEFAULT_PERIOD_MONTHS = 12  # Default period for analysis
MAX_DATE_RANGE_DAYS = 365   # Maximum date range for queries
DATE_FORMAT_API = "%d/%m/%y - %H:%M"  # API date format
DATE_FORMAT_DISPLAY = "%d/%m/%Y"      # Display date format

# API Constants
MAX_CONCURRENT_REQUESTS = 10
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 1

# UI Constants
DEFAULT_PAGE_SIZE = 50
MAX_ROWS_DISPLAY = 1000
CHART_HEIGHT_DEFAULT = 400
TABLE_HEIGHT_DEFAULT = 400

# Performance Constants
ASYNC_BATCH_SIZE = 100
MAX_MEMORY_USAGE_MB = 512


class OSType(Enum):
    """Ordem de Serviço types from API."""
    PREVENTIVA = 1
    CALIBRACAO = 2
    CORRETIVA = 3
    VISITA_TECNICA = 4
    EMPRESTIMO = 5
    TREINAMENTO = 6
    TESTE_SEG_ELETRICA = 7
    CHAMADO = 8
    INSTALACAO = 9
    TESTE_INICIAL = 10


class OSStatus(Enum):
    """Ordem de Serviço status values."""
    ABERTA = "Aberta"
    EM_ANDAMENTO = "Em Andamento"
    PENDENTE = "Pendente"
    CONCLUIDA = "Concluída"
    CANCELADA = "Cancelada"


class EquipmentStatus(Enum):
    """Equipment status values."""
    ATIVO = "Ativo"
    INATIVO = "Inativo"
    MANUTENCAO = "Em Manutenção"
    DESCARTADO = "Descartado"


class Priority(Enum):
    """Priority levels."""
    BAIXA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4


class UserRole(Enum):
    """User roles in the system."""
    ADMIN = "admin"
    TECNICO = "tecnico"
    RESPONSAVEL_TECNICO = "responsavel_tecnico"
    VISUALIZADOR = "visualizador"


# Color schemes for charts
COLORS = {
    'primary': '#1f77b4',
    'secondary': '#ff7f0e', 
    'success': '#2ca02c',
    'warning': '#d62728',
    'info': '#17becf',
    'light': '#bcbd22',
    'dark': '#8c564b'
}

# Chart color palettes
COLOR_PALETTE_STATUS = [
    '#2E8B57',  # Concluído - Verde
    '#FF6347',  # Pendente - Vermelho  
    '#4682B4',  # Em Andamento - Azul
    '#DAA520',  # Aberto - Dourado
    '#8B008B'   # Cancelado - Roxo
]

COLOR_PALETTE_PRIORITY = [
    '#90EE90',  # Baixa - Verde claro
    '#FFD700',  # Média - Amarelo
    '#FF8C00',  # Alta - Laranja
    '#DC143C'   # Crítica - Vermelho escuro
]

# API endpoints
API_ENDPOINTS = {
    'login': '/rest-auth/token-auth/',
    'chamados': '/api/chamados/',
    'equipamentos': '/api/equipamentos/',
    'usuarios': '/api/usuarios/',
    'tipos_os': '/api/tipos-os/',
}
