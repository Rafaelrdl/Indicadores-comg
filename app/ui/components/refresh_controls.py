"""
Componente de controles de refresh para sincronização de dados.

Este módulo fornece interface visual para controlar a sincronização
de dados com feedback visual e controles granulares.
"""

import asyncio
from datetime import datetime

import streamlit as st

from app.core.logging import app_logger
from app.services.repository import get_database_stats
from app.services.sync.delta import run_incremental_sync, should_run_incremental_sync
from app.services.sync.ingest import BackfillSync


def render_refresh_controls(
    resources: list[str] = None, show_advanced: bool = True, compact_mode: bool = False
) -> None:
    """
    Renderiza controles de sincronização com status visual.

    Args:
        resources: Lista de recursos para sincronizar ['orders', 'equipments', 'technicians']
        show_advanced: Se deve mostrar opções avançadas
        compact_mode: Modo compacto para sidebars
    """
    if resources is None:
        resources = ["orders", "equipments", "technicians"]

    # Container principal
    if compact_mode:
        container = st.container()
    else:
        container = st.expander("🔄 Sincronização de Dados", expanded=True)

    with container:
        # ========== INDICADORES DE STATUS ==========
        render_sync_status(resources, compact_mode)

        # ========== CONTROLES DE REFRESH ==========
        render_sync_controls(resources, show_advanced, compact_mode)


def render_sync_status(resources: list[str], compact_mode: bool = False) -> None:
    """Renderiza indicadores de status de sincronização."""

    try:
        stats = get_database_stats()
        last_syncs = stats.get("last_syncs", [])

        if compact_mode:
            st.markdown("**📊 Status dos Dados**")
        else:
            st.subheader("📊 Status dos Dados")

        # Criar mapa de último sync por recurso
        sync_map = {}
        for sync in last_syncs:
            resource = sync.get("resource")
            if resource:
                sync_map[resource] = sync

        # Mostrar status por recurso
        for resource in resources:
            render_resource_status(resource, sync_map.get(resource), stats, compact_mode)

    except Exception as e:
        st.error(f"❌ Erro ao carregar status: {e}")
        app_logger.log_error(f"Erro no render_sync_status: {e}")


def render_resource_status(
    resource: str, sync_info: dict | None, stats: dict, compact_mode: bool = False
) -> None:
    """Renderiza status de um recurso específico."""

    # Mapear nomes amigáveis
    resource_names = {
        "orders": "Ordens de Serviço",
        "equipments": "Equipamentos",
        "technicians": "Técnicos",
    }

    display_name = resource_names.get(resource, resource.title())
    record_count = stats.get(f"{resource}_count", 0)

    # Determinar status
    is_fresh = not should_run_incremental_sync(resource, max_age_hours=2)

    # Status visual
    if is_fresh:
        status_icon = "✅"
        status_text = "Atualizado"
        status_color = "green"
    else:
        status_icon = "⚠️"
        status_text = "Desatualizado"
        status_color = "orange"

    # Layout do status
    if compact_mode:
        st.markdown(f"{status_icon} **{display_name}**: {record_count:,} registros")
        if sync_info:
            last_sync = sync_info.get("synced_at") or sync_info.get("updated_at", "Nunca")
            if last_sync != "Nunca":
                try:
                    # Parse timestamp
                    if "T" in last_sync:
                        dt = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                    else:
                        dt = datetime.fromisoformat(last_sync)

                    formatted_time = dt.strftime("%H:%M:%S - %d/%m/%Y")
                    st.caption(f"Última sync: {formatted_time}")
                except:
                    st.caption(f"Última sync: {last_sync}")
        else:
            st.caption("Nunca sincronizado")
    else:
        col1, col2, col3 = st.columns([3, 2, 2])

        with col1:
            st.markdown(f"**{display_name}**")
            st.caption(f"{record_count:,} registros")

        with col2:
            st.markdown(
                f"<span style='color: {status_color}'>{status_icon} {status_text}</span>",
                unsafe_allow_html=True,
            )

        with col3:
            if sync_info:
                last_sync = sync_info.get("synced_at") or sync_info.get("updated_at", "Nunca")
                if last_sync != "Nunca":
                    try:
                        # Parse e formatar timestamp
                        if "T" in last_sync:
                            dt = datetime.fromisoformat(last_sync.replace("Z", "+00:00"))
                        else:
                            dt = datetime.fromisoformat(last_sync)

                        # Tempo relativo
                        now = datetime.now()
                        diff = now - dt.replace(tzinfo=None) if dt.tzinfo else now - dt

                        if diff.total_seconds() < 3600:  # < 1 hora
                            time_ago = f"{int(diff.total_seconds() / 60)}min atrás"
                        elif diff.days == 0:  # < 1 dia
                            time_ago = f"{int(diff.total_seconds() / 3600)}h atrás"
                        else:
                            time_ago = f"{diff.days}d atrás"

                        st.caption(time_ago)
                        st.caption(dt.strftime("%H:%M - %d/%m"))
                    except:
                        st.caption("Formato inválido")
                else:
                    st.caption("Nunca")
            else:
                st.caption("Nunca")


def render_sync_controls(
    resources: list[str], show_advanced: bool = True, compact_mode: bool = False
) -> None:
    """Renderiza controles de sincronização."""

    if not compact_mode:
        st.divider()
        st.subheader("🎛️ Controles")

    # ========== CONFIGURAÇÕES ==========
    col1, col2 = st.columns([2, 1] if compact_mode else [3, 2])

    with col1:
        # Opção principal: apenas novos/alterados
        only_delta = st.checkbox(
            "🔄 Apenas novos/alterados",
            value=True,
            help="Quando ativado, sincroniza apenas registros modificados. Desativado = sincronização completa.",
        )

        # Recursos para sincronizar
        if show_advanced and not compact_mode:
            selected_resources = st.multiselect(
                "📂 Recursos para sincronizar",
                options=resources,
                default=resources,
                help="Selecione quais tipos de dados sincronizar",
            )
        else:
            selected_resources = resources

    with col2:
        # Opções avançadas
        if show_advanced:
            batch_size = st.number_input(
                "Tamanho do lote",
                min_value=10,
                max_value=500,
                value=100,
                step=10,
                help="Registros processados por vez",
            )
        else:
            batch_size = 100

    # ========== BOTÕES DE AÇÃO ==========

    # Layout dos botões
    if compact_mode:
        col_btn1, col_btn2 = st.columns(2)
    else:
        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 1])

    with col_btn1:
        # Botão principal de atualização
        if st.button(
            "🔄 Atualizar Agora" if only_delta else "🔄 Sincronização Completa",
            type="primary" if only_delta else "secondary",
            use_container_width=True,
        ):
            run_sync_action(selected_resources, only_delta, batch_size)

    with col_btn2:
        # Botão de verificação rápida
        if st.button(
            "🔍 Verificar Status", use_container_width=True, help="Verifica status sem sincronizar"
        ):
            check_sync_status(selected_resources)

    # Botão de reset apenas no modo não-compacto
    if not compact_mode:
        with col_btn3:
            if st.button(
                "🗑️ Reset",
                help="Limpa cache e força sincronização completa",
                use_container_width=True,
            ):
                if st.confirmation_dialog("Reset completo dos dados?"):
                    reset_all_data(selected_resources)


def run_sync_action(resources: list[str], only_delta: bool, batch_size: int) -> None:
    """Executa ação de sincronização."""

    if not resources:
        st.warning("⚠️ Selecione pelo menos um recurso para sincronizar")
        return

    # Mostrar confirmação para sync completo
    if not only_delta:
        if not st.confirmation_dialog(
            "Confirmação de Sincronização Completa",
            "Isso pode levar vários minutos e sobrescrever dados locais. Continuar?",
        ):
            return

    # Container de progresso
    progress_container = st.container()

    with progress_container:
        if only_delta:
            st.info("🔄 Iniciando sincronização incremental...")
        else:
            st.warning("🔄 Iniciando sincronização completa...")

        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Executar sincronização
            if only_delta:
                run_incremental_sync_with_progress(resources, progress_bar, status_text)
            else:
                run_full_sync_with_progress(resources, batch_size, progress_bar, status_text)

            # Sucesso
            progress_bar.progress(100)
            st.success("✅ Sincronização concluída com sucesso!")

            # Limpar cache do Streamlit para refletir mudanças
            st.cache_data.clear()

        except Exception as e:
            st.error(f"❌ Erro na sincronização: {e}")
            app_logger.log_error(f"Erro na sincronização: {e}")


def run_incremental_sync_with_progress(
    resources: list[str], progress_bar: st.progress, status_text: st.empty
) -> None:
    """Executa sync incremental com barra de progresso."""

    total_resources = len(resources)

    for i, resource in enumerate(resources):
        status_text.text(f"🔄 Sincronizando {resource}...")
        progress_bar.progress((i) / total_resources)

        # Executar sync do recurso
        try:
            # Criar cliente da API
            from app.arkmeds_client.auth import ArkmedsAuth
            from app.arkmeds_client.client import ArkmedsClient

            auth = ArkmedsAuth()
            client = ArkmedsClient(auth)

            # Como run_incremental_sync é async, precisamos executar de forma síncrona
            result = asyncio.run(run_incremental_sync(client, [resource]))

            status_text.text(f"✅ {resource}: {result.get(resource, 0)} registros sincronizados")

        except Exception as e:
            status_text.text(f"❌ Erro em {resource}: {e}")
            continue

        progress_bar.progress((i + 1) / total_resources)


def run_full_sync_with_progress(
    resources: list[str], batch_size: int, progress_bar: st.progress, status_text: st.empty
) -> None:
    """Executa backfill completo com progresso."""

    try:
        status_text.text("🔄 Iniciando sincronização completa...")

        # Criar instância do backfill
        backfill = BackfillSync()

        # Executar backfill
        asyncio.run(backfill.run_backfill(resources, batch_size=batch_size))

        status_text.text("✅ Sincronização completa finalizada")

    except Exception as e:
        status_text.text(f"❌ Erro na sincronização: {e}")
        raise


def check_sync_status(resources: list[str]) -> None:
    """Verifica status de sincronização sem executar sync."""

    st.info("🔍 Verificando status dos dados...")

    try:
        stats = get_database_stats()

        # Mostrar resumo
        total_records = sum(stats.get(f"{r}_count", 0) for r in resources)

        st.success(f"📊 Total de registros: {total_records:,}")

        # Status por recurso
        for resource in resources:
            count = stats.get(f"{resource}_count", 0)
            is_fresh = not should_run_incremental_sync(resource, max_age_hours=2)

            status = "✅ Atualizado" if is_fresh else "⚠️ Desatualizado"
            st.write(f"**{resource.title()}**: {count:,} registros - {status}")

    except Exception as e:
        st.error(f"❌ Erro ao verificar status: {e}")


def reset_all_data(resources: list[str]) -> None:
    """Reset completo dos dados."""

    st.warning("🗑️ Executando reset dos dados...")

    try:
        from app.core.db import get_conn

        with get_conn() as conn:
            # Limpar tabelas
            for resource in resources:
                conn.execute(f"DELETE FROM {resource}")
                st.write(f"✅ Tabela {resource} limpa")

            # Limpar estado de sync
            conn.execute(
                "DELETE FROM sync_state WHERE resource IN ({})".format(
                    ",".join(["?" for _ in resources])
                ),
                resources,
            )

            conn.commit()

        # Limpar cache
        st.cache_data.clear()

        st.success("✅ Reset concluído. Execute uma sincronização completa.")

    except Exception as e:
        st.error(f"❌ Erro no reset: {e}")


# ========== COMPONENTES AUXILIARES ==========


def render_sync_badge(resource: str, compact: bool = False) -> None:
    """Renderiza badge de status para um recurso específico."""

    try:
        is_fresh = not should_run_incremental_sync(resource, max_age_hours=2)

        if is_fresh:
            if compact:
                st.success("🟢 Atual", icon="✅")
            else:
                st.success(f"✅ {resource.title()} atualizado")
        else:
            if compact:
                st.warning("🟡 Antigo", icon="⚠️")
            else:
                st.warning(f"⚠️ {resource.title()} desatualizado")

    except Exception:
        if compact:
            st.error("🔴 Erro", icon="❌")
        else:
            st.error(f"❌ Erro ao verificar {resource}")


def render_compact_refresh_button(resources: list[str] = None) -> None:
    """Renderiza botão compacto de refresh para sidebars."""

    if resources is None:
        resources = ["orders"]

    if st.button("🔄 Atualizar", help="Sincronização rápida", use_container_width=True):
        with st.spinner("Sincronizando..."):
            try:
                # Criar cliente da API
                from app.arkmeds_client.auth import ArkmedsAuth
                from app.arkmeds_client.client import ArkmedsClient

                auth = ArkmedsAuth()
                client = ArkmedsClient(auth)

                # Executar sincronização para todos os recursos
                asyncio.run(run_incremental_sync(client, resources))
                st.success("✅ Atualizado!")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ Erro: {e}")
