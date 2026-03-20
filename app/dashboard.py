import streamlit as st
import plotly.express as px
import pandas as pd
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
    /* Reduz o espaço em branco no topo */
    .block-container {padding-top: 2rem;}
    </style>
""", unsafe_allow_html=True)

def renderizar_sidebar():
    with st.sidebar:
        st.header("⚙️ Sobre o Projeto")
        st.markdown("""
        Este painel é a camada de consumo (Gold) de um pipeline de dados ponta a ponta.
        
        **Arquitetura:**
        * **Extração:** Dados abertos da ANAC.
        * **Processamento (Silver):** Apache Spark (PySpark) e armazenamento em Parquet.
        * **Data Warehouse (Gold):** Modelagem Star Schema em PostgreSQL / SQLite.
        """)
        
        st.divider()
        
        st.header("🎛️ Filtros Globais")
        anos_selecionados = st.slider(
            "Selecione o Período Histórico:",
            min_value=2000,
            max_value=2020,
            value=(2000, 2020)
        )
        
        st.divider()
        
        st.markdown("""
        **Desenvolvido por:**
        [Pedro Arthur](https://parthur.dev)
        *Estudante de Engenharia de Software na UnB*
        """)
        
        return anos_selecionados

def renderizar_dashboard():
    # Renderiza a barra lateral e captura o filtro de anos
    ano_inicio, ano_fim = renderizar_sidebar()
    
    st.title("✈️ Painel Analítico: Aviação Brasileira")
    st.markdown(f"**Visão Estratégica:** Operações comerciais no período de {ano_inicio} a {ano_fim}.")
    
    st.divider()

    # Obtém os dados puros do cache
    df_kpi_bruto = obter_kpis_negocio()
    df_share_bruto = obter_market_share_companhias()
    
    # Converte a coluna de texto do banco para inteiro numérico
    df_share_bruto['ano'] = pd.to_numeric(df_share_bruto['ano'])
    
    df_share = df_share_bruto[(df_share_bruto['ano'] >= ano_inicio) & (df_share_bruto['ano'] <= ano_fim)]

    # 1. Seção de KPIs Estratégicos
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Volume de Passageiros (Acumulado)", value=f"{df_kpi_bruto['total_passageiros'].iloc[0]:,.0f}".replace(',', '.'))
    with col2:
        st.metric(label="Carga Comercial (Toneladas)", value=f"{df_kpi_bruto['total_carga_toneladas'].iloc[0]:,.0f}".replace(',', '.'))
    with col3:
        st.metric(label="Taxa de Ocupação Global (Load Factor)", value=f"{df_kpi_bruto['load_factor'].iloc[0]:.1f}%")

    st.divider()

    # 2. Seção Analítica (Market Share e Eficiência)
    col_grafico1, col_grafico2 = st.columns(2)

    with col_grafico1:
        st.subheader("Evolução de Market Share")
        fig_share = px.area(
            df_share, x="ano", y="passageiros", color="empresa_agrupada",
            labels={"ano": "Ano", "passageiros": "Passageiros Pagos", "empresa_agrupada": "Companhia Aérea"},
            template="plotly_white"
        )
        fig_share.update_layout(
            legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5, title=None),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        fig_share.update_xaxes(dtick=2)
        st.plotly_chart(fig_share, use_container_width=True)
        st.caption("Visão do monopólio do setor: Agrupa as 6 maiores companhias do período e consolida o restante em 'Outras'. Reflete o volume absoluto de passageiros transportados.")

    with col_grafico2:
        st.subheader("Densidade Operacional por Rota")
        df_rotas = obter_eficiencia_rotas(limite=10)
        
        fig_rotas = px.bar(
            df_rotas, x="passageiros_por_voo", y="rota", 
            orientation='h',
            labels={"passageiros_por_voo": "Passageiros / Voo", "rota": "Trecho (Origem ➔ Destino)"},
            template="plotly_white",
            text="passageiros_por_voo" 
        )
        
        fig_rotas.update_traces(texttemplate='%{text:.0f} pax', textposition='outside')
        
        fig_rotas.update_layout(
            yaxis={'categoryorder':'total ascending'},
            margin=dict(r=50) 
        )
        
        st.plotly_chart(fig_rotas, use_container_width=True)
        st.caption("Eficiência de frota: Média de passageiros reais alocados por decolagem. Exclui rotas com menos de 500 voos registrados para evitar distorções estatísticas.")

if __name__ == "__main__":
    renderizar_dashboard()