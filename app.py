import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

matplotlib.use('Agg')

st.set_page_config(page_title="DynaSilva", layout="wide", initial_sidebar_state="collapsed")

# Título centralizado
st.markdown("""
    <h1 style='text-align: center; color: #1E88E5; margin-bottom: 0.3rem;'>
        DynaSilva - Simulador de Dinamômetro com Freio Hidráulico
    </h1>
    <p style='text-align: center; color: #666;'>🏍️ Rolo + Sensor de Rotação + Célula de Carga</p>
""", unsafe_allow_html=True)

# ================== PARÂMETROS EM EXPANDER ==================
with st.expander("⚙️ Parâmetros do Dinamômetro", expanded=False):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        raio_rolo_m = st.slider("Raio do Rolo (m)", 0.05, 0.30, 0.15, 0.01)
        massa_total_kg = st.slider("Massa Total (Moto + Piloto) kg", 100, 500, 280, 5)
        C_rr = st.slider("C_rr - Coef. Rolamento", 0.005, 0.05, 0.015, 0.001)
    with col_p2:
        CdA = st.slider("CdA - Área Frontal Efetiva (m²)", 0.3, 1.2, 0.6, 0.05)
        rho = st.number_input("Densidade do Ar (kg/m³)", value=1.225, step=0.001, format="%.3f")
        torque_freio_max_Nm = st.slider("Torque Máx Freio Hidráulico (Nm)", 50, 600, 200, 10)

# ================== SIMULAÇÃO ESPECÍFICA ==================
st.subheader("🎯 Simulação Específica")
col1, col2 = st.columns(2)

with col1:
    vel_especifica = st.number_input("Velocidade (km/h)", min_value=0.0, max_value=220.0, value=100.0, step=1.0)
    c1, c2, c3 = st.columns([1,2,1])
    if c2.button("−5 km/h", use_container_width=True):
        vel_especifica = max(0.0, vel_especifica - 5)
    if c2.button("+5 km/h", use_container_width=True):
        vel_especifica = min(220.0, vel_especifica + 5)

with col2:
    col_tm
