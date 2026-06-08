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

raio_rolo_mm = st.sidebar.slider(
    "Raio do Rolo (mm)", 50, 300, 150, 1,
    help="Raio do cilindro de contato com o pneu. Determina a relação entre a velocidade linear do pneu e a rotação do rolo, afetando diretamente o cálculo de RPM e torque. Valores típicos: 50–300 mm."
)
raio_rolo_m = raio_rolo_mm / 1000

massa_total_kg = st.sidebar.slider(
    "Massa Total (Moto + Piloto) kg", 100, 500, 280, 5,
    help="Soma da massa da motocicleta e do piloto. Influencia a resistência ao rolamento (F_rr = C_rr × m × g) e, indiretamente, a carga sobre o rolo. Valores típicos: 100–500 kg."
)
C_rr = st.sidebar.slider(
    "C_rr - Coef. Rolamento", 0.005, 0.05, 0.015, 0.001,
    help="Coeficiente de resistência ao rolamento do pneu. Representa a energia dissipada por deformação do pneu e do rolo. Pneus de moto em asfalto ficam entre 0,005 e 0,02; valores maiores indicam maior perda. Valores típicos: 0,005–0,05."
)
CdA = st.sidebar.slider(
    "CdA - Área Frontal Efetiva (m²)", 0.3, 1.2, 0.6, 0.05,
    help="Produto do coeficiente de arrasto aerodinâmico (Cd) pela área frontal (A) da moto+piloto. Determina a força de arrasto (F_d = ½ × ρ × v² × CdA), que cresce com o quadrado da velocidade. Valores típicos para motos: 0,3–1,2 m²."
)
rho = st.sidebar.number_input(
    "Densidade do Ar (kg/m³)", value=1.225,
    help="Densidade do ar no local do ensaio. Varia com altitude e temperatura: ao nível do mar a 15 °C vale 1,225 kg/m³; em altitudes elevadas ou dias quentes o valor é menor, reduzindo o arrasto aerodinâmico. Valor padrão ISA: 1,225 kg/m³."
)
torque_freio_max_Nm = st.sidebar.slider(
    "Torque Máx Freio Hidráulico (Nm)", 50, 500, 200, 10,
    help="Torque máximo que o freio hidráulico consegue aplicar ao rolo. Limita a força de frenagem disponível para absorver a potência da moto; se o torque de perdas calculado superar este valor, o freio opera no limite. Valores típicos: 50–500 Nm."
)

# === CONTROLES DE SIMULAÇÃO ESPECÍFICA ===
st.subheader("🎯 Simulação Específica")

col1, col2 = st.columns(2)

with col1:
    vel_especifica = st.number_input("Velocidade para simular (km/h)", 
                                   min_value=0.0, max_value=220.0, 
                                   value=100.0, step=1.0, 
                                   help="Digite o valor ou use os botões")
    col_v1, col_v2, col_v3 = st.columns([1,2,1])
    if col_v2.button("➖ 5 km/h", use_container_width=True):
        vel_especifica = max(0.0, vel_especifica - 5)
    if col_v2.button("➕ 5 km/h", use_container_width=True):
        vel_especifica = min(220.0, vel_especifica + 5)

with col2:
    tempo_min = st.number_input("Tempo (minutos)", min_value=0, max_value=15, value=5, step=1)
    tempo_seg = st.slider("Segundos adicionais", 0, 59, 0)
    tempo_total_seg = tempo_min * 60 + tempo_seg
    st.info(f"⏱️ Tempo total: **{tempo_min} min {tempo_seg} seg**")

# ================== CÁLCULOS ==================
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

# ================== RESULTADOS ==================
st.subheader("📊 Resultados da Simulação")

# Destaque da velocidade escolhida
idx = (np.abs(df['Velocidade (km/h)'] - vel_especifica)).argmin()
row = df.iloc[idx]

col_m1, col_m2 = st.columns([3, 2])

with col_m1:
    st.dataframe(df, use_container_width=True)

with col_m2:
    st.success(f"**Resultado em {vel_especifica:.0f} km/h**")
    st.metric("RPM do Rolo", f"{row['RPM Rolo']}")
    st.metric("Força de Perdas", f"{row['F_perdas (N)']} N")
    st.metric("Torque de Perdas", f"{row['Torque Perdas (Nm)']} Nm")
    st.metric("Torque Freio Aplicado", f"{row['Torque Freio (Nm)']} Nm")
    st.metric("Potência no Freio", f"{row['Potência Freio (kW)']} kW")

    st.download_button(
        label="📥 Baixar Planilha Excel",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="resultados_dinamometro.csv",
        mime="text/csv"
    )

# ================== GRÁFICOS ==================
st.subheader("📈 Gráficos")
fig, axs = plt.subplots(2, 2, figsize=(12, 8))

axs[0,0].plot(vel_kmh, F_perdas, label='Perdas Totais')
axs[0,0].set_xlabel('Velocidade (km/h)')
axs[0,0].set_ylabel('Força (N)')
axs[0,0].legend()
axs[0,0].grid()

axs[0,1].plot(vel_kmh, torque_perdas_Nm, 'r', label='Torque Perdas')
axs[0,1].plot(vel_kmh, torque_aplicado, 'g--', label='Torque Freio')
axs[0,1].set_xlabel('Velocidade (km/h)')
axs[0,1].set_ylabel('Torque (Nm)')
axs[0,1].legend()
axs[0,1].grid()

axs[1,0].plot(vel_kmh, rpm_rolo, 'b')
axs[1,0].set_xlabel('Velocidade (km/h)')
axs[1,0].set_ylabel('RPM Rolo')
axs[1,0].grid()

axs[1,1].plot(vel_kmh, potencia_perdas_kw, label='Perdas (kW)')
axs[1,1].plot(vel_kmh, potencia_freio_kw, 'g', label='Freio Hidráulico')
axs[1,1].set_xlabel('Velocidade (km/h)')
axs[1,1].set_ylabel('Potência (kW)')
axs[1,1].legend()
axs[1,1].grid()

plt.tight_layout()
st.pyplot(fig)

st.info("🔧 Ajuste os parâmetros na barra lateral e a velocidade/tempo acima. Tudo atualiza em tempo real!")
st.caption("Projeto Dinamômetro com Freio Hidráulico de Moto - Rolo + Sensor de Rotação + Célula de Carga")
