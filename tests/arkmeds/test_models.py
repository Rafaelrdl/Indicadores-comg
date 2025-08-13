"""Testes para modelos Pydantic do arkmeds_client.

Este módulo testa a validação e serialização dos modelos
de dados da API Arkmeds.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.arkmeds_client.models import (
    TokenData,
    PaginatedResponse,
    OSEstado,
    TipoOS,
    ResponsavelTecnico,
    Company,
    Equipment,
    Chamado,
)


class TestTokenData:
    """Testes para modelo TokenData."""

    def test_token_data_creation(self):
        """Testa criação de TokenData."""
        exp_time = datetime.now(timezone.utc)
        token_data = TokenData(token="test_token", exp=exp_time)

        assert token_data.token == "test_token"
        assert token_data.exp == exp_time

    def test_token_data_validation(self):
        """Testa validação de TokenData."""
        with pytest.raises(ValidationError):
            # Passar tipo inválido para exp
            TokenData.model_validate({"token": "test", "exp": "invalid_datetime"})


class TestPaginatedResponse:
    """Testes para modelo PaginatedResponse."""

    def test_paginated_response_creation(self):
        """Testa criação de PaginatedResponse."""
        response = PaginatedResponse(
            count=100, next="https://api.test.com/next/", results=[{"id": 1}, {"id": 2}]
        )

        assert response.count == 100
        assert response.next == "https://api.test.com/next/"
        assert len(response.results) == 2

    def test_paginated_response_no_next(self):
        """Testa PaginatedResponse sem próxima página."""
        response = PaginatedResponse(count=2, next=None, results=[{"id": 1}, {"id": 2}])

        assert response.next is None


class TestOSEstado:
    """Testes para enum OSEstado."""

    def test_estados_abertos(self):
        """Testa classificação de estados abertos."""
        estados_abertos = OSEstado.estados_abertos()

        assert OSEstado.ABERTA in estados_abertos
        assert OSEstado.EM_EXECUCAO in estados_abertos
        assert OSEstado.AGUARDANDO_PECAS in estados_abertos
        assert OSEstado.FECHADA not in estados_abertos

    def test_estados_fechados(self):
        """Testa classificação de estados fechados."""
        estados_fechados = OSEstado.estados_fechados()

        assert OSEstado.FECHADA in estados_fechados
        assert OSEstado.SERVICO_FINALIZADO in estados_fechados
        assert OSEstado.ABERTA not in estados_fechados

    def test_estados_cancelados(self):
        """Testa classificação de estados cancelados."""
        estados_cancelados = OSEstado.estados_cancelados()

        assert OSEstado.CANCELADA in estados_cancelados
        assert len(estados_cancelados) == 1

    def test_get_descricao(self):
        """Testa obtenção de descrição por ID."""
        assert OSEstado.get_descricao(1) == "Aberta"
        assert OSEstado.get_descricao(2) == "Fechada"
        assert OSEstado.get_descricao(999) == "Estado desconhecido (999)"


class TestTipoOS:
    """Testes para enum TipoOS."""

    def test_tipos_manutencao(self):
        """Testa classificação de tipos de manutenção."""
        tipos_manutencao = TipoOS.tipos_manutencao()

        assert TipoOS.MANUTENCAO_PREVENTIVA in tipos_manutencao
        assert TipoOS.MANUTENCAO_CORRETIVA in tipos_manutencao
        assert TipoOS.MANUTENCAO_PREDITIVA in tipos_manutencao
        assert TipoOS.TREINAMENTO not in tipos_manutencao

    def test_tipos_preventivos(self):
        """Testa classificação de tipos preventivos."""
        tipos_preventivos = TipoOS.tipos_preventivos()

        assert TipoOS.MANUTENCAO_PREVENTIVA in tipos_preventivos
        assert TipoOS.CALIBRACAO in tipos_preventivos
        assert TipoOS.BUSCA_ATIVA in tipos_preventivos
        assert TipoOS.MANUTENCAO_CORRETIVA not in tipos_preventivos

    def test_tipos_corretivos(self):
        """Testa classificação de tipos corretivos."""
        tipos_corretivos = TipoOS.tipos_corretivos()

        assert TipoOS.MANUTENCAO_CORRETIVA in tipos_corretivos
        assert TipoOS.CHAMADO in tipos_corretivos
        assert TipoOS.MANUTENCAO_PREVENTIVA not in tipos_corretivos

    def test_get_descricao(self):
        """Testa obtenção de descrição por ID."""
        assert TipoOS.get_descricao(1) == "Manutenção Preventiva"
        assert TipoOS.get_descricao(3) == "Manutenção Corretiva"
        assert TipoOS.get_descricao(999) == "Tipo desconhecido (999)"


class TestResponsavelTecnico:
    """Testes para modelo ResponsavelTecnico."""

    def test_responsavel_tecnico_creation(self):
        """Testa criação de ResponsavelTecnico."""
        responsavel = ResponsavelTecnico(
            id="1", nome="João Silva", email="joao@teste.com", has_avatar=True, avatar="JS"
        )

        assert responsavel.id == "1"
        assert responsavel.nome == "João Silva"
        assert responsavel.email == "joao@teste.com"
        assert responsavel.has_avatar is True
        assert responsavel.avatar == "JS"

    def test_id_int_property(self):
        """Testa propriedade id_int."""
        responsavel = ResponsavelTecnico(id="123", nome="Teste", email="teste@example.com")

        assert responsavel.id_int == 123

    def test_id_int_invalid(self):
        """Testa id_int com valor inválido."""
        responsavel = ResponsavelTecnico(id="invalid", nome="Teste", email="teste@example.com")

        assert responsavel.id_int == 0

    def test_display_name_with_nome(self):
        """Testa display_name com nome válido."""
        responsavel = ResponsavelTecnico(id="1", nome="  João Silva  ", email="joao@teste.com")

        assert responsavel.display_name == "João Silva"

    def test_display_name_fallback_email(self):
        """Testa display_name com fallback para email."""
        responsavel = ResponsavelTecnico(id="1", nome="", email="_joao.silva@teste.com")

        assert responsavel.display_name == "joao.silva"

    def test_display_name_fallback_id(self):
        """Testa display_name com fallback para ID."""
        responsavel = ResponsavelTecnico(id="1", nome="", email="")

        assert responsavel.display_name == "Técnico 1"

    def test_avatar_display_url(self):
        """Testa avatar_display com URL."""
        responsavel = ResponsavelTecnico(
            id="1", nome="João", email="joao@teste.com", avatar="https://example.com/avatar.jpg"
        )

        assert responsavel.avatar_display == "https://example.com/avatar.jpg"

    def test_avatar_display_initials(self):
        """Testa avatar_display com iniciais."""
        responsavel = ResponsavelTecnico(id="1", nome="João", email="joao@teste.com", avatar="JS")

        assert responsavel.avatar_display == "JS"

    def test_avatar_display_generated(self):
        """Testa avatar_display gerado do nome."""
        responsavel = ResponsavelTecnico(
            id="1", nome="João Silva Santos", email="joao@teste.com", avatar=None
        )

        assert responsavel.avatar_display == "JS"


class TestCompany:
    """Testes para modelo Company."""

    def test_company_creation(self):
        """Testa criação de Company."""
        company = Company(
            id=1,
            nome="Hospital Central",
            nome_fantasia="HC",
            cnpj="12.345.678/0001-90",
            cidade="São Paulo",
            estado="SP",
            equipamentos=[{"id": 1, "nome": "Equipamento 1"}],
        )

        assert company.id == 1
        assert company.nome == "Hospital Central"
        assert company.nome_fantasia == "HC"
        assert len(company.equipamentos) == 1

    def test_display_name(self):
        """Testa propriedade display_name."""
        # Com nome fantasia
        company1 = Company(id=1, nome="Hospital Central LTDA", nome_fantasia="Hospital Central")
        assert company1.display_name == "Hospital Central"

        # Sem nome fantasia
        company2 = Company(id=2, nome="Clínica São José")
        assert company2.display_name == "Clínica São José"

    def test_total_equipamentos(self):
        """Testa propriedade total_equipamentos."""
        company = Company(id=1, nome="Hospital", equipamentos=[{"id": 1}, {"id": 2}, {"id": 3}])

        assert company.total_equipamentos == 3

    def test_endereco_completo(self):
        """Testa propriedade endereco_completo."""
        company = Company(
            id=1,
            nome="Hospital",
            rua="Rua das Flores",
            numero=123,
            complemento="Andar 2",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP",
            cep="01234-567",
        )

        endereco = company.endereco_completo
        assert "Rua das Flores, 123 - Andar 2" in endereco
        assert "Centro" in endereco
        assert "São Paulo - SP" in endereco
        assert "CEP: 01234-567" in endereco

    def test_endereco_vazio(self):
        """Testa endereco_completo quando vazio."""
        company = Company(id=1, nome="Hospital")

        assert company.endereco_completo == "Endereço não informado"


class TestEquipment:
    """Testes para modelo Equipment."""

    def test_equipment_creation(self):
        """Testa criação de Equipment."""
        equipment = Equipment(
            id=1,
            fabricante="Philips",
            modelo="MX400",
            patrimonio="PAT001",
            numero_serie="SN123456",
            identificacao="Monitor Cardíaco Sala 1",
            tipo_criticidade=3,
            prioridade=2,
            proprietario=10,
        )

        assert equipment.id == 1
        assert equipment.fabricante == "Philips"
        assert equipment.modelo == "MX400"
        assert equipment.proprietario == 10

    def test_display_name_priority(self):
        """Testa prioridade do display_name."""
        # Prioridade: identificacao > nome > patrimonio > id
        eq1 = Equipment(
            id=1, identificacao="Monitor Cardíaco", nome="Nome Antigo", patrimonio="PAT001"
        )
        assert eq1.display_name == "Monitor Cardíaco"

        eq2 = Equipment(id=2, nome="Monitor X1", patrimonio="PAT002")
        assert eq2.display_name == "Monitor X1"

        eq3 = Equipment(id=3, patrimonio="PAT003")
        assert eq3.display_name == "Patrimônio PAT003"

        eq4 = Equipment(id=4)
        assert eq4.display_name == "Equipamento 4"

    def test_descricao_completa(self):
        """Testa propriedade descricao_completa."""
        equipment = Equipment(
            id=1,
            identificacao="Monitor",
            fabricante="Philips",
            modelo="MX400",
            numero_serie="SN123",
        )

        descricao = equipment.descricao_completa
        assert "Monitor" in descricao
        assert "Fabricante: Philips" in descricao
        assert "Modelo: MX400" in descricao
        assert "S/N: SN123" in descricao

    def test_criticidade_nivel(self):
        """Testa propriedade criticidade_nivel."""
        eq1 = Equipment(id=1, tipo_criticidade=1)
        assert eq1.criticidade_nivel == "Baixa"

        eq2 = Equipment(id=2, tipo_criticidade=3)
        assert eq2.criticidade_nivel == "Alta"

        eq3 = Equipment(id=3, tipo_criticidade=99)
        assert eq3.criticidade_nivel == "Nível 99"

        eq4 = Equipment(id=4)
        assert eq4.criticidade_nivel == "Não definida"

    def test_prioridade_nivel(self):
        """Testa propriedade prioridade_nivel."""
        eq1 = Equipment(id=1, prioridade=1)
        assert eq1.prioridade_nivel == "Baixa"

        eq2 = Equipment(id=2, prioridade=4)
        assert eq2.prioridade_nivel == "Urgente"

        eq3 = Equipment(id=3, prioridade=99)
        assert eq3.prioridade_nivel == "Prioridade 99"

        eq4 = Equipment(id=4)
        assert eq4.prioridade_nivel == "Não definida"


class TestChamado:
    """Testes para modelo Chamado."""

    @pytest.fixture
    def sample_responsavel(self):
        """ResponsavelTecnico de exemplo."""
        return {
            "id": "1",
            "nome": "João Silva",
            "email": "joao@teste.com",
            "has_avatar": False,
            "has_resp_tecnico": True,
            "avatar": "JS",
        }

    @pytest.fixture
    def sample_ordem_servico(self):
        """Ordem de serviço de exemplo."""
        return {
            "numero": "OS-2024-001",
            "data_criacao": "2024-07-01",
            "equipamento": 123,
            "tipo_servico": 1,
            "estado": 2,
            "prioridade": 2,
        }

    def test_chamado_creation(self, sample_responsavel, sample_ordem_servico):
        """Testa criação de Chamado."""
        chamado = Chamado(
            id=1,
            chamados=12345,
            responsavel_id=1,
            tempo=["finalizado sem atraso", "normal", 1, 0],
            tempo_fechamento=["vazio", "normal", 0, 0],
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.id == 1
        assert chamado.chamados == 12345
        assert chamado.responsavel_id == 1
        assert isinstance(chamado.get_resp_tecnico, ResponsavelTecnico)
        assert chamado.ordem_servico == sample_ordem_servico

    def test_status_tempo(self, sample_responsavel, sample_ordem_servico):
        """Testa propriedade status_tempo."""
        chamado = Chamado(
            id=1,
            chamados=1,
            responsavel_id=1,
            tempo=["finalizado com atraso", "normal", 1, 0],
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.status_tempo == "finalizado com atraso"

    def test_status_fechamento(self, sample_responsavel, sample_ordem_servico):
        """Testa propriedade status_fechamento."""
        chamado = Chamado(
            id=1,
            chamados=1,
            responsavel_id=1,
            tempo_fechamento=["finalizado sem atraso", "normal", 1, 0],
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.status_fechamento == "finalizado sem atraso"

    def test_finalizado_sem_atraso(self, sample_responsavel, sample_ordem_servico):
        """Testa propriedade finalizado_sem_atraso."""
        chamado = Chamado(
            id=1,
            chamados=1,
            responsavel_id=1,
            tempo=["finalizado sem atraso", "normal", 1, 0],
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.finalizado_sem_atraso is True
        assert chamado.finalizado_com_atraso is False

    def test_finalizado_com_atraso(self, sample_responsavel, sample_ordem_servico):
        """Testa propriedade finalizado_com_atraso."""
        chamado = Chamado(
            id=1,
            chamados=1,
            responsavel_id=1,
            tempo=["finalizado com atraso", "normal", 1, 0],
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.finalizado_com_atraso is True
        assert chamado.finalizado_sem_atraso is False

    def test_propriedades_ordem_servico(self, sample_responsavel, sample_ordem_servico):
        """Testa propriedades derivadas da ordem de serviço."""
        chamado = Chamado(
            id=1,
            chamados=1,
            responsavel_id=1,
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.numero_os == "OS-2024-001"
        assert chamado.data_criacao_os == "2024-07-01"
        assert chamado.equipamento_id == 123
        assert chamado.tipo_servico_id == 1
        assert chamado.estado_id == 2
        assert chamado.prioridade == 2

    def test_responsavel_nome(self, sample_responsavel, sample_ordem_servico):
        """Testa propriedade responsavel_nome."""
        chamado = Chamado(
            id=1,
            chamados=1,
            responsavel_id=1,
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        assert chamado.responsavel_nome == "João Silva"

    def test_chamado_str(self, sample_responsavel, sample_ordem_servico):
        """Testa representação string do chamado."""
        chamado = Chamado(
            id=1,
            chamados=12345,
            responsavel_id=1,
            get_resp_tecnico=sample_responsavel,
            ordem_servico=sample_ordem_servico,
        )

        str_repr = str(chamado)
        assert "Chamado #12345" in str_repr
        assert "OS OS-2024-001" in str_repr
        assert "João Silva" in str_repr
