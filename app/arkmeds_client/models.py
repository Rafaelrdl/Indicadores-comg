from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TokenData(BaseModel):
    token: str
    exp: datetime


class PaginatedResponse(BaseModel):
    count: int
    next: str | None = None
    results: list[dict]


class ArkBase(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class OSEstado(Enum):
    """Estados possíveis de Ordem de Serviço.
    
    ⚡ AUDITORIA REALIZADA: 24/07/2025
    📡 Fonte: Consulta à API /api/v3/estado_ordem_servico/
    📊 Total encontrado: 22 estados únicos
    🔍 Método: Consulta direta + análise de OSs em produção
    
    NOTA: Alguns estados (IDs 20, 21, 22) têm descrição apenas "." 
    na API, possivelmente estados de teste ou reservados.
    """
    # Estados principais
    ABERTA = 1
    FECHADA = 2
    CANCELADA = 3
    EM_EXECUCAO = 4
    
    # Estados de espera/pendência
    AGUARDANDO_PECAS = 5
    AGUARDANDO_APROVACAO_ORCAMENTO = 6
    AGUARDANDO_ORCAMENTO = 12
    AGUARDANDO_ANEXO_CERTIFICADOS = 13
    AGUARDANDO_ANALISE_CRITICA = 14
    AGUARDANDO_PROGRAMACAO = 18
    AGUARDANDO_ANALISE = 19
    EM_ESPERA = 11
    
    # Estados de conclusão/finalização
    SERVICO_FINALIZADO = 7
    ANALISE_CONCLUIDA = 8
    ORCAMENTO_APROVADO = 10
    
    # Estados de manutenção/reparo
    EM_MANUTENCAO = 16
    REPARO_EXTERNO = 9
    AGENDADA_FABRICANTE_CONTRATADO = 15
    SERVICO_CORRETIVA_PROGRAMADO = 17
    
    # Estados especiais/diversos
    ESTADO_ESPECIAL_1 = 20  # Descrição: "."
    ESTADO_ESPECIAL_2 = 21  # Descrição: "."
    ESTADO_ESPECIAL_3 = 22  # Descrição: "."
    
    @classmethod
    def estados_abertos(cls) -> list["OSEstado"]:
        """Retorna estados considerados 'abertos' (OS ainda em andamento)."""
        return [
            cls.ABERTA,
            cls.EM_EXECUCAO,
            cls.AGUARDANDO_PECAS,
            cls.AGUARDANDO_APROVACAO_ORCAMENTO,
            cls.AGUARDANDO_ORCAMENTO,
            cls.AGUARDANDO_ANEXO_CERTIFICADOS,
            cls.AGUARDANDO_ANALISE_CRITICA,
            cls.AGUARDANDO_PROGRAMACAO,
            cls.AGUARDANDO_ANALISE,
            cls.EM_ESPERA,
            cls.EM_MANUTENCAO,
            cls.REPARO_EXTERNO,
            cls.AGENDADA_FABRICANTE_CONTRATADO,
            cls.SERVICO_CORRETIVA_PROGRAMADO,
        ]
    
    @classmethod
    def estados_fechados(cls) -> list["OSEstado"]:
        """Retorna estados considerados 'fechados' (OS concluída)."""
        return [
            cls.FECHADA,
            cls.SERVICO_FINALIZADO,
            cls.ANALISE_CONCLUIDA,
            cls.ORCAMENTO_APROVADO,
        ]
    
    @classmethod
    def estados_cancelados(cls) -> list["OSEstado"]:
        """Retorna estados considerados 'cancelados'."""
        return [cls.CANCELADA]
    
    @classmethod
    def get_descricao(cls, estado_id: int) -> str:
        """Retorna descrição amigável do estado baseado no ID."""
        descricoes = {
            1: "Aberta",
            2: "Fechada", 
            3: "Cancelada",
            4: "Em execução",
            5: "Aguardando peças",
            6: "Aguardando aprovação do orçamento",
            7: "Serviço finalizado",
            8: "Análise concluída",
            9: "Reparo externo",
            10: "Orçamento Aprovado",
            11: "Em Espera",
            12: "Aguardando Orçamento",
            13: "Aguardando anexo de Certificados",
            14: "Aguardando Análise Crítica",
            15: "Agendada para o Fabricante ou Contratado",
            16: "Em Manutenção",
            17: "Serviço de manutenção corretiva programado",
            18: "Aguardando programação",
            19: "Aguardando analise",
            20: "Estado especial 1",
            21: "Estado especial 2", 
            22: "Estado especial 3",
        }
        return descricoes.get(estado_id, f"Estado desconhecido ({estado_id})")


class TipoOS(Enum):
    """Tipos possíveis de Ordem de Serviço.
    
    ⚡ AUDITORIA REALIZADA: 24/07/2025
    📡 Fonte: Consulta à API /api/v3/tipo_servico/
    📊 Total encontrado: 18 tipos únicos
    🔍 Método: Consulta direta à API
    
    NOTA: IDs 18 e 19 ambos são "Vistoria Diária" - possível duplicação na API
    """
    # Tipos principais de manutenção
    MANUTENCAO_PREVENTIVA = 1
    CALIBRACAO = 2
    MANUTENCAO_CORRETIVA = 3
    VISITA_TECNICA = 4
    EMPRESTIMO = 5
    TREINAMENTO = 6
    TESTE_SEGURANCA_ELETRICA = 7
    CHAMADO = 8
    INSTALACAO = 9
    TESTE_INICIAL = 10
    MANUTENCAO_PREDITIVA = 11
    
    # Tipos de vistoria/monitoramento
    VISTORIA_DIARIA_1 = 18  # Duplicação na API
    VISTORIA_DIARIA_2 = 19  # Duplicação na API
    MONITORAMENTO_DIARIO = 26
    
    # Tipos especializados
    BUSCA_ATIVA = 28
    INVENTARIO = 29
    ANALISE_INFRAESTRUTURA = 30
    INSPECAO_NR13 = 31
    
    @classmethod
    def tipos_manutencao(cls) -> list["TipoOS"]:
        """Retorna tipos relacionados à manutenção."""
        return [
            cls.MANUTENCAO_PREVENTIVA,
            cls.MANUTENCAO_CORRETIVA,
            cls.MANUTENCAO_PREDITIVA,
        ]
    
    @classmethod
    def tipos_preventivos(cls) -> list["TipoOS"]:
        """Retorna tipos considerados preventivos."""
        return [
            cls.MANUTENCAO_PREVENTIVA,
            cls.MANUTENCAO_PREDITIVA,
            cls.CALIBRACAO,
            cls.TESTE_SEGURANCA_ELETRICA,
            cls.TESTE_INICIAL,
            cls.VISTORIA_DIARIA_1,
            cls.VISTORIA_DIARIA_2,
            cls.MONITORAMENTO_DIARIO,
            cls.BUSCA_ATIVA,
            cls.INVENTARIO,
            cls.INSPECAO_NR13,
        ]
    
    @classmethod
    def tipos_corretivos(cls) -> list["TipoOS"]:
        """Retorna tipos considerados corretivos."""
        return [
            cls.MANUTENCAO_CORRETIVA,
            cls.CHAMADO,
        ]
    
    @classmethod
    def tipos_operacionais(cls) -> list["TipoOS"]:
        """Retorna tipos operacionais/administrativos."""
        return [
            cls.VISITA_TECNICA,
            cls.EMPRESTIMO,
            cls.TREINAMENTO,
            cls.INSTALACAO,
            cls.ANALISE_INFRAESTRUTURA,
        ]
    
    @classmethod
    def get_descricao(cls, tipo_id: int) -> str:
        """Retorna descrição amigável do tipo baseado no ID."""
        descricoes = {
            1: "Manutenção Preventiva",
            2: "Calibração",
            3: "Manutenção Corretiva",
            4: "Visita Técnica",
            5: "Empréstimo",
            6: "Treinamento",
            7: "Teste de Segurança Elétrica",
            8: "Chamado",
            9: "Instalação",
            10: "Teste Inicial",
            11: "Manutenção Preditiva",
            18: "Vistoria Diária",
            19: "Vistoria Diária",
            26: "Monitoramento Diário",
            28: "Busca Ativa",
            29: "Inventário",
            30: "Análise de Infraestrutura",
            31: "Inspeção NR13",
        }
        return descricoes.get(tipo_id, f"Tipo desconhecido ({tipo_id})")


# NOTA: EstadoOS removida - use OSEstado(Enum) que é mais completa e type-safe


class ResponsavelTecnico(ArkBase):
    """Modelo para responsável técnico baseado na API /api/v5/chamado/.
    
    ⚡ AUDITORIA REALIZADA: 24/07/2025
    📡 Fonte: Consulta à API /api/v5/chamado/ campo 'get_resp_tecnico'
    🔍 Estrutura real descoberta nos dados de chamados
    """
    id: str  # Vem como string na API (ex: "1", "6", "7")
    nome: str
    email: str
    has_avatar: bool = False
    has_resp_tecnico: bool = True
    avatar: str | None = None  # Pode ser URL ou iniciais (ex: "Uc", "HP")
    
    @property
    def id_int(self) -> int:
        """Retorna ID como inteiro."""
        try:
            return int(self.id)
        except (ValueError, TypeError):
            return 0
    
    @property
    def display_name(self) -> str:
        """Retorna nome para exibição."""
        if self.nome and self.nome.strip():
            return self.nome.strip()
        
        # Fallback para email sem domínio
        if self.email and self.email.strip():
            email_part = self.email.split("@")[0]
            if email_part.startswith("_"):
                email_part = email_part[1:]  # Remove underscore inicial
            return email_part
        
        return f"Técnico {self.id}"
    
    @property
    def avatar_display(self) -> str:
        """Retorna avatar para exibição (URL ou iniciais)."""
        if self.avatar and self.avatar.startswith("http"):
            return self.avatar  # URL completa
        elif self.avatar:
            return self.avatar  # Iniciais
        else:
            # Gerar iniciais do nome
            if self.nome:
                words = self.nome.split()
                if len(words) >= 2:
                    return f"{words[0][0]}{words[-1][0]}".upper()
                elif len(words) == 1:
                    return words[0][:2].upper()
            return f"T{self.id}"
    
    def __str__(self) -> str:
        """Representação string do responsável."""
        return self.display_name


class Equipment(ArkBase):
    id: int
    nome: str
    ativo: bool | None = None
    data_aquisicao: datetime | None = Field(default=None, alias="data_aquisicao")

    @field_validator("data_aquisicao", mode="before")
    @classmethod
    def _parse_date(cls, v: str | datetime | None) -> datetime | None:
        if v is None or isinstance(v, datetime):
            return v
        return datetime.strptime(v, "%d/%m/%y - %H:%M")


class Chamado(ArkBase):
    """Modelo para Chamados baseado na API /api/v5/chamado/.
    
    ⚡ AUDITORIA REALIZADA: 24/07/2025
    📡 Fonte: Consulta à API /api/v5/chamado/
    📊 Total de registros: 5,049 chamados
    🔍 Estrutura completa com tempo, responsável e ordem de serviço
    """
    id: int
    chamados: int  # Número sequencial do chamado
    chamado_arquivado: bool = False
    responsavel_id: int
    
    # Arrays de tempo [descrição, status, número, valor_adicional]
    tempo: list = Field(default_factory=list)  # Status de execução
    tempo_fechamento: list = Field(default_factory=list)  # Status de fechamento
    
    # Dados do responsável técnico
    get_resp_tecnico: ResponsavelTecnico
    
    # Dados da ordem de serviço associada
    ordem_servico: dict  # Estrutura complexa com equipamento, solicitante, etc.
    
    @field_validator("get_resp_tecnico", mode="before")
    @classmethod
    def _parse_responsavel(cls, v: dict | ResponsavelTecnico | None) -> ResponsavelTecnico | None:
        if v is None or isinstance(v, ResponsavelTecnico):
            return v
        if isinstance(v, dict):
            return ResponsavelTecnico.model_validate(v)
        return None
    
    @property
    def status_tempo(self) -> str:
        """Retorna status de execução em texto."""
        if self.tempo and len(self.tempo) > 0:
            return str(self.tempo[0])
        return "vazio"
    
    @property
    def status_fechamento(self) -> str:
        """Retorna status de fechamento em texto."""
        if self.tempo_fechamento and len(self.tempo_fechamento) > 0:
            return str(self.tempo_fechamento[0])
        return "vazio"
    
    @property
    def finalizado_sem_atraso(self) -> bool:
        """Verifica se foi finalizado sem atraso."""
        return self.status_tempo == "finalizado sem atraso" or self.status_fechamento == "finalizado sem atraso"
    
    @property
    def finalizado_com_atraso(self) -> bool:
        """Verifica se foi finalizado com atraso."""
        return self.status_tempo == "finalizado com atraso" or self.status_fechamento == "finalizado com atraso"
    
    @property
    def responsavel_nome(self) -> str:
        """Retorna nome do responsável técnico."""
        return self.get_resp_tecnico.display_name if self.get_resp_tecnico else f"Responsável {self.responsavel_id}"
    
    @property
    def numero_os(self) -> str:
        """Retorna número da ordem de serviço."""
        return self.ordem_servico.get("numero", "") if self.ordem_servico else ""
    
    @property
    def data_criacao_os(self) -> str:
        """Retorna data de criação da OS."""
        return self.ordem_servico.get("data_criacao", "") if self.ordem_servico else ""
    
    @property
    def equipamento_id(self) -> int | None:
        """Retorna ID do equipamento."""
        return self.ordem_servico.get("equipamento") if self.ordem_servico else None
    
    @property
    def tipo_servico_id(self) -> int | None:
        """Retorna ID do tipo de serviço."""
        return self.ordem_servico.get("tipo_servico") if self.ordem_servico else None
    
    @property
    def estado_id(self) -> int | None:
        """Retorna ID do estado."""
        return self.ordem_servico.get("estado") if self.ordem_servico else None
    
    @property
    def prioridade(self) -> int | None:
        """Retorna prioridade da OS."""
        return self.ordem_servico.get("prioridade") if self.ordem_servico else None
    
    def __str__(self) -> str:
        """Representação string do chamado."""
        return f"Chamado #{self.chamados} - OS {self.numero_os} - {self.responsavel_nome}"
