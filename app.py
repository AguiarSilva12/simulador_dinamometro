import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configuração para ambiente headless (Railway)
import matplotlib
matplotlib.use('Agg')

st.set_page_config(page_title="Simulador Dinamômetro Moto", layout="wide")
st.title("🚀 Simulador de Dinamômetro com Freio Hidráulico")

st.sidebar.header("Parâmetros do Dinamômetro")

raio_rolo_m = st.sidebar.slider("Raio do Rolo (m)", 0.05, 0.30, 0.15, 0.01)
massa_total_kg = st.sidebar.slider("Massa Total (Moto + Piloto) kg", 100, 500, 280, 5)
C_rr = st.sidebar.slider("C_rr - Coef. Rolamento", 0.005, 0.05, 0.015, 0.001)
CdA = st.sidebar.slider("CdA - Área Frontal Efetiva (m²)", 0.3, 1.2, 0.6, 0.05)
rho = st.sidebar.number_input("Densidade do Ar (kg/m³)", value=1.225)
torque_freio_max_Nm = st.sidebar.slider("Torque Máx Freio Hidráulico (Nm)", 50, 500, 200, 10)

vel_kmh = np.linspace(0, 220, 45)
vel_ms = vel_kmh / 3.6

F_rr = C_rr * massa_total_kg * 9.81
F_d = 0.5 * rho * vel_ms**2 * CdA
F_perdas = F_rr + F_d

torque_perdas_Nm = F_perdas * raio_rolo_m
rpm_rolo = (vel_ms * 60) / (2 * np.pi * raio_rolo_m)
torque_aplicado = np.minimum(torque_perdas_Nm * 1.1, torque_freio_max_Nm)

potencia_perdas_kw = F_perdas * vel_ms / 1000
potencia_freio_kw = torque_aplicado * (rpm_rolo * 2 * np.pi / 60) / 1000

df = pd.DataFrame({
    'Velocidade (km/h)': vel_kmh,
    'RPM Rolo': np.round(rpm_rolo, 1),
    'F_perdas (N)': np.round(F_perdas, 1),
    'Torque Perdas (Nm)': np.round(torque_perdas_Nm, 1),
    'Torque Freio (Nm)': np.round(torque_aplicado, 1),
    'Potência Perdas (kW)': np.round(potencia_perdas_kw, 2),
    'Potência Freio (kW)': np.round(potencia_freio_kw, 2)
})

st.subheader("📊 Resultados da Simulação")
col1, col2 = st.columns(2)
with col1:
    st.dataframe(df, use_container_width=True)

with col2:
    st.download_button("Baixar Planilha Excel", df.to_csv(index=False).encode('utf-8'), "resultados_dinamometro.csv", "text/csv")

# Gráficos
fig, axs = plt.subplots(2, 2, figsize=(12, 8))

axs[0,0].plot(vel_kmh, F_perdas, label='Perdas Totais')
axs[0,0].set_xlabel('Velocidade (km/h)'); axs[0,0].set_ylabel('Força (N)'); axs[0,0].legend(); axs[0,0].grid()

axs[0,1].plot(vel_kmh, torque_perdas_Nm, 'r', label='Torque Perdas')
axs[0,1].plot(vel_kmh, torque_aplicado, 'g--', label='Torque Freio')
axs[0,1].set_xlabel('Velocidade (km/h)'); axs[0,1].set_ylabel('Torque (Nm)'); axs[0,1].legend(); axs[0,1].grid()

axs[1,0].plot(vel_kmh, rpm_rolo, 'b')
axs[1,0].set_xlabel('Velocidade (km/h)'); axs[1,0].set_ylabel('RPM Rolo'); axs[1,0].grid()

axs[1,1].plot(vel_kmh, potencia_perdas_kw, label='Perdas (kW)')
axs[1,1].plot(vel_kmh, potencia_freio_kw, 'g', label='Freio Hidráulico')
axs[1,1].set_xlabel('Velocidade (km/h)'); axs[1,1].set_ylabel('Potência (kW)'); axs[1,1].legend(); axs[1,1].grid()

plt.tight_layout()
st.pyplot(fig)

st.info("🔧 Ajuste os sliders na barra lateral e veja os resultados em tempo real!")
st.caption("Simulador para dinamômetro com freio hidráulico, rolo, sensor de rotação e célula de carga")
