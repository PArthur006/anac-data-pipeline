import streamlit as st
import plotly.express as px
import pandas as pd
from queries import obter_kpis_gerais, obter_evolucao_voos_por_ano, obter_top_aeroportos

# Configuração da página
st.set_page_config(
    page_title="ANAC Analytics | Data Pipeline",
    page_icon="✈️",
    layout="wide"
)

# Estilização via CSS injetado
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1f77b4;}
    </style>
""", unsafe_allow_html=True)

def renderizar_dashboard():
    st.title("✈️ Painel Analítico: Tráfego Aéreo Brasileiro")
    st.markdown("Visão consolidada de voos operados no Brasil entre 2000 e 2020. Pipeline construído com PySpark e PostgreSQL.")

    st.divider()

    # 1. Seção de KPIs (Indicadores Chave de Performance)
    with st.spinner("Carregando métricas..."):
        df_kpi = obter_kpis_gerais()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Total de Passageiros Pagos", value=f"{df_kpi['total_passageiros'].iloc[0]:,.0f}".replace(',', '.'))
        with col2:
            st.metric(label="Total de Decolagens", value=f"{df_kpi['total_decolagens'].iloc[0]:,.0f}".replace(',', '.'))
        with col3:
            st.metric(label="Carga Transportada (Toneladas)", value=f"{df_kpi['total_carga_toneladas'].iloc[0]:,.0f}".replace(',', '.'))
        
        st.divider()

        # 2. Seção de Gráficos
        col_grafico1, col_grafico2 = st.columns(2)

        with col_grafico1:
            st.subheader("Evolução de Voos (Série Histórica)")
            df_evolucao = obter_evolucao_voos_por_ano()
            fig_linha = px.line(
                df_evolucao, x='ano', y='total_voos',
                markers=True,
                labels={"ano": "Ano", "total_voos": "Quantidade de Voos"},
                template="plotly_white"
            )

            # Força o eixo X a mostrar apenas anos inteiros
            fig_linha.update_xaxes(dtick=1)
            st.plotly_chart(fig_linha, use_container_width=True)

        with col_grafico2:
            st.subheader("Top 10 Aeroportos por Volume de Passageiros")
            df_aeroportos = obter_top_aeroportos()

            # df_aeroportos["volume_passageiros"] = pd.to_numeric(df_aeroportos["volume_passageiros"], errors='coerce').fillna(0)
            
            fig_barra = px.bar(
                df_aeroportos, x="volume_passageiros", y="aeroporto", orientation='h',
                labels={"volumes_passageiros": "Passageiros", "aeroporto": "Aeroporto"},
                template="plotly_white"
            )

            # Inverte o eixo Y para o maior ficar no topo
            fig_barra.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_barra, use_container_width=True)

if __name__ == "__main__":
    renderizar_dashboard()
