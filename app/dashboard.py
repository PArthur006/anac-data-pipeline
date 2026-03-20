import streamlit as st
import plotly.express as px
from queries import obter_kpis_negocio, obter_market_share_companhias, obter_eficiencia_rotas

st.set_page_config(
    page_title="ANAC Analytics | Data Pipeline",
    page_icon="✈️",
    layout="wide"
)

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1f77b4;}
    </style>
""", unsafe_allow_html=True)

def renderizar_dashboard():
    st.title("✈️ Painel Analítico: Aviação Brasileira (2000-2020)")
    st.markdown("Análise de inteligência de mercado extraída de Data Warehouse PostgreSQL. Foco em eficiência operacional e Market Share.")
    
    st.divider()

    # 1. Seção de KPIs Estratégicos
    with st.spinner("Processando agregações..."):
        df_kpi = obter_kpis_negocio()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(label="Volume de Passageiros", value=f"{df_kpi['total_passageiros'].iloc[0]:,.0f}".replace(',', '.'))
        with col2:
            st.metric(label="Carga Comercial (Toneladas)", value=f"{df_kpi['total_carga_toneladas'].iloc[0]:,.0f}".replace(',', '.'))
        with col3:
            # Exibe o Load Factor com formatação de porcentagem
            st.metric(label="Taxa de Ocupação Global (Load Factor)", value=f"{df_kpi['load_factor'].iloc[0]:.1f}%")

    st.divider()

    # 2. Seção Analítica (Market Share e Eficiência)
    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.subheader("Evolução de Market Share (Top 6 Companhias)")
        df_share = obter_market_share_companhias()
        
        # Gráfico de Área Empilhada (Stacked Area) para mostrar domínio de mercado
        fig_share = px.area(
            df_share, x="ano", y="passageiros", color="empresa_agrupada",
            labels={"ano": "Ano", "passageiros": "Passageiros Pagos", "empresa_agrupada": "Companhia Aérea"},
            template="plotly_white"
        )
        fig_share.update_xaxes(dtick=1)
        st.plotly_chart(fig_share, use_container_width=True)

    with col_grafico2:
        st.subheader("Densidade Operacional (Rotas Mais Cheias)")
        st.markdown("*Média de passageiros por decolagem (mínimo de 500 voos na rota).*")
        df_rotas = obter_eficiencia_rotas(limite=10)
        
        # Gráfico de Barras focado em eficiência
        fig_rotas = px.bar(
            df_rotas, x="passageiros_por_voo", y="rota", 
            orientation='h',
            labels={"passageiros_por_voo": "Passageiros / Voo", "rota": "Trecho"},
            template="plotly_white"
        )
        fig_rotas.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_rotas, use_container_width=True)

if __name__ == "__main__":
    renderizar_dashboard()

