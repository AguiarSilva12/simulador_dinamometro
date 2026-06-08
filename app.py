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


# ================== FUNÇÃO DE ACELERAÇÃO ==================
def simulate_acceleration(max_velocity_kmh: float, time_to_max_seconds: float, num_points: int = 200):
    """
    Simula aceleração linear de 0 até max_velocity_kmh em time_to_max_seconds segundos.

    Returns
    -------
    time_s : np.ndarray  – instantes de tempo (s)
    vel_kmh : np.ndarray – velocidade correspondente (km/h)
    """
    time_s = np.linspace(0, time_to_max_seconds, num_points)
    vel_kmh = (max_velocity_kmh / time_to_max_seconds) * time_s
    return time_s, vel_kmh


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

# === SIMULAÇÃO DE ACELERAÇÃO ===
st.markdown("---")
st.markdown("#### 🏎️ Simulação de Aceleração")

accel_enabled = st.checkbox("Ativar simulação de aceleração (0 → velocidade máxima)", value=False)

if accel_enabled:
    col_a1, col_a2 = st.columns(2)
    with col_a1:
        accel_time = st.slider("Tempo de Aceleração (s)", min_value=1, max_value=300, value=10, step=1,
                               help="Tempo para atingir a velocidade máxima a partir do repouso")
    with col_a2:
        accel_max_vel = st.slider("Velocidade Máxima (km/h)", min_value=10, max_value=200, value=200, step=5,
                                  help="Velocidade alvo ao final da aceleração")

    accel_rate = accel_max_vel / accel_time
    st.info(f"📐 Taxa de aceleração: **{accel_rate:.2f} km/h/s** ({accel_rate / 3.6:.2f} m/s²)")

# ================== CÁLCULOS ==================

def calc_physics(vel_kmh_arr):
    """Calcula forças, torques e potências para um array de velocidades (km/h)."""
    vel_ms_arr = vel_kmh_arr / 3.6
    F_rr_arr = C_rr * massa_total_kg * 9.81
    F_d_arr = 0.5 * rho * vel_ms_arr**2 * CdA
    F_p = F_rr_arr + F_d_arr
    tq_perdas = F_p * raio_rolo_m
    rpm = (vel_ms_arr * 60) / (2 * np.pi * raio_rolo_m)
    tq_aplicado = np.minimum(tq_perdas * 1.1, torque_freio_max_Nm)
    pot_perdas = F_p * vel_ms_arr / 1000
    pot_freio = tq_aplicado * (rpm * 2 * np.pi / 60) / 1000
    return F_p, tq_perdas, rpm, tq_aplicado, pot_perdas, pot_freio

# --- Curva estática (sempre calculada para os gráficos de referência) ---
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

if accel_enabled:
    # --- Perfil de aceleração ---
    time_s_arr, vel_kmh_arr = simulate_acceleration(accel_max_vel, accel_time)
    F_p_arr, tq_perdas_arr, rpm_arr, tq_apl_arr, pot_perdas_arr, pot_freio_arr = calc_physics(vel_kmh_arr)

    df_accel = pd.DataFrame({
        'Tempo (s)': np.round(time_s_arr, 2),
        'Velocidade (km/h)': np.round(vel_kmh_arr, 1),
        'RPM Rolo': np.round(rpm_arr, 1),
        'F_perdas (N)': np.round(F_p_arr, 1),
        'Torque Perdas (Nm)': np.round(tq_perdas_arr, 1),
        'Torque Freio (Nm)': np.round(tq_apl_arr, 1),
        'Potência Perdas (kW)': np.round(pot_perdas_arr, 2),
        'Potência Freio (kW)': np.round(pot_freio_arr, 2),
    })

    col_m1, col_m2 = st.columns([3, 2])

    with col_m1:
        st.markdown(f"**Perfil de aceleração — 0 → {accel_max_vel} km/h em {accel_time} s**")
        st.dataframe(df_accel, use_container_width=True)

    with col_m2:
        st.success(f"**Métricas na velocidade máxima ({accel_max_vel} km/h)**")
        st.metric("RPM do Rolo", f"{rpm_arr[-1]:.1f}")
        st.metric("Força de Perdas", f"{F_p_arr[-1]:.1f} N")
        st.metric("Torque de Perdas", f"{tq_perdas_arr[-1]:.1f} Nm")
        st.metric("Torque Freio Aplicado", f"{tq_apl_arr[-1]:.1f} Nm")
        st.metric("Potência no Freio", f"{pot_freio_arr[-1]:.2f} kW")
        st.metric("Taxa de Aceleração", f"{accel_rate:.2f} km/h/s")

        st.download_button(
            label="📥 Baixar Perfil de Aceleração (CSV)",
            data=df_accel.to_csv(index=False).encode('utf-8'),
            file_name="perfil_aceleracao_dinamometro.csv",
            mime="text/csv"
        )

else:
    # --- Modo estático (velocidade única) ---
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

if accel_enabled:
    x_data = time_s_arr
    x_label = "Tempo (s)"
    title_suffix = f" — Aceleração 0→{accel_max_vel} km/h em {accel_time} s"

    axs[0, 0].plot(x_data, F_p_arr, label='Perdas Totais', color='steelblue')
    axs[0, 0].set_xlabel(x_label)
    axs[0, 0].set_ylabel('Força (N)')
    axs[0, 0].set_title(f'Força de Perdas{title_suffix}')
    axs[0, 0].legend()
    axs[0, 0].grid()

    axs[0, 1].plot(x_data, tq_perdas_arr, 'r', label='Torque Perdas')
    axs[0, 1].plot(x_data, tq_apl_arr, 'g--', label='Torque Freio')
    axs[0, 1].set_xlabel(x_label)
    axs[0, 1].set_ylabel('Torque (Nm)')
    axs[0, 1].set_title(f'Torques{title_suffix}')
    axs[0, 1].legend()
    axs[0, 1].grid()

    axs[1, 0].plot(x_data, vel_kmh_arr, color='darkorange', label='Velocidade')
    axs[1, 0].set_xlabel(x_label)
    axs[1, 0].set_ylabel('Velocidade (km/h)')
    axs[1, 0].set_title(f'Perfil de Velocidade{title_suffix}')
    axs[1, 0].legend()
    axs[1, 0].grid()

    axs[1, 1].plot(x_data, pot_perdas_arr, label='Perdas (kW)')
    axs[1, 1].plot(x_data, pot_freio_arr, 'g', label='Freio Hidráulico')
    axs[1, 1].set_xlabel(x_label)
    axs[1, 1].set_ylabel('Potência (kW)')
    axs[1, 1].set_title(f'Potência{title_suffix}')
    axs[1, 1].legend()
    axs[1, 1].grid()

else:
    axs[0, 0].plot(vel_kmh, F_perdas, label='Perdas Totais')
    axs[0, 0].set_xlabel('Velocidade (km/h)')
    axs[0, 0].set_ylabel('Força (N)')
    axs[0, 0].legend()
    axs[0, 0].grid()

    axs[0, 1].plot(vel_kmh, torque_perdas_Nm, 'r', label='Torque Perdas')
    axs[0, 1].plot(vel_kmh, torque_aplicado, 'g--', label='Torque Freio')
    axs[0, 1].set_xlabel('Velocidade (km/h)')
    axs[0, 1].set_ylabel('Torque (Nm)')
    axs[0, 1].legend()
    axs[0, 1].grid()

    axs[1, 0].plot(vel_kmh, rpm_rolo, 'b')
    axs[1, 0].set_xlabel('Velocidade (km/h)')
    axs[1, 0].set_ylabel('RPM Rolo')
    axs[1, 0].grid()

    axs[1, 1].plot(vel_kmh, potencia_perdas_kw, label='Perdas (kW)')
    axs[1, 1].plot(vel_kmh, potencia_freio_kw, 'g', label='Freio Hidráulico')
    axs[1, 1].set_xlabel('Velocidade (km/h)')
    axs[1, 1].set_ylabel('Potência (kW)')
    axs[1, 1].legend()
    axs[1, 1].grid()

plt.tight_layout()
st.pyplot(fig)

st.info("🔧 Ajuste os parâmetros na barra lateral e a velocidade/tempo acima. Tudo atualiza em tempo real!")
st.caption("Projeto Dinamômetro com Freio Hidráulico de Moto - Rolo + Sensor de Rotação + Célula de Carga")
