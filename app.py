import streamlit as st
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ================== PAGE CONFIG ==================
st.set_page_config(
    page_title="DynaSilva",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 0.6rem !important; padding-bottom: 0.5rem !important; }
    h2, h3 { margin-top: 0.4rem !important; margin-bottom: 0.2rem !important; }
    [data-testid="metric-container"] { background: #f0f4ff; border-radius: 8px; padding: 6px 10px !important; }
</style>
""", unsafe_allow_html=True)

# ================== TITLE ==================
st.markdown(
    "<h1 style='text-align:center;color:#1E88E5;margin-bottom:0.1rem;font-size:1.5rem;'>"
    "DynaSilva — Simulador de Dinamômetro com Freio Hidráulico"
    "</h1>"
    "<p style='text-align:center;color:#666;margin-top:0;font-size:0.85rem;'>"
    "🏍️ Rolo + Sensor de Rotação + Célula de Carga"
    "</p>",
    unsafe_allow_html=True,
)

# ================== PARÂMETROS ==================
with st.expander("⚙️ Parâmetros do Dinamômetro", expanded=False):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        raio_rolo_m = st.slider("Raio do Rolo (m)", 0.05, 0.30, 0.15, 0.01)
        massa_total_kg = st.slider("Massa Total (kg)", 100, 500, 280, 5)
        C_rr = st.slider("C_rr — Coef. Rolamento", 0.005, 0.05, 0.015, 0.001)
    with col_p2:
        CdA = st.slider("CdA — Área Frontal (m²)", 0.3, 1.2, 0.6, 0.05)
        rho = st.number_input("Densidade do Ar (kg/m³)", value=1.225, step=0.001, format="%.4f")
        torque_freio_max_Nm = st.slider("Torque Máx Freio Hidráulico (Nm)", 50, 600, 200, 10)

g = 9.81

# ================== SIMULAÇÃO ESPECÍFICA ==================
st.subheader("🎯 Simulação Específica")
col1, col2 = st.columns(2)

with col1:
    vel_especifica = st.number_input(
        "Velocidade (km/h)", min_value=0.0, max_value=220.0, value=100.0, step=1.0,
        help="Velocidade alvo para cálculo pontual.",
    )
    btn_col1, btn_col2 = st.columns(2)
    if btn_col1.button("−5 km/h", use_container_width=True):
        vel_especifica = max(0.0, vel_especifica - 5)
    if btn_col2.button("+5 km/h", use_container_width=True):
        vel_especifica = min(220.0, vel_especifica + 5)

with col2:
    col_tm1, col_tm2 = st.columns(2)
    with col_tm1:
        t_aceleracao = st.number_input("Tempo Aceleração (s)", min_value=0.1, max_value=60.0, value=5.0, step=0.1)
    with col_tm2:
        t_frenagem = st.number_input("Tempo Frenagem (s)", min_value=0.1, max_value=60.0, value=3.0, step=0.1)

# ================== CÁLCULOS ==================
vel_ms_esp = vel_especifica / 3.6
rpm_rolo_esp = (vel_ms_esp * 60) / (2 * np.pi * raio_rolo_m) if raio_rolo_m > 0 else 0.0
F_rr_esp = C_rr * massa_total_kg * g
F_d_esp = 0.5 * rho * vel_ms_esp**2 * CdA
F_perdas_esp = F_rr_esp + F_d_esp
torque_perdas_esp = F_perdas_esp * raio_rolo_m
torque_freio_esp = min(torque_perdas_esp * 1.1, torque_freio_max_Nm)
pot_perdas_esp = F_perdas_esp * vel_ms_esp / 1000
pot_freio_esp = torque_freio_esp * (rpm_rolo_esp * 2 * np.pi / 60) / 1000 if rpm_rolo_esp > 0 else 0.0

a_acel = (vel_ms_esp / t_aceleracao) if t_aceleracao > 0 else 0.0
a_fren = (vel_ms_esp / t_frenagem) if t_frenagem > 0 else 0.0
F_inercia_acel = massa_total_kg * a_acel
F_inercia_fren = massa_total_kg * a_fren

# ================== RESULTADO RÁPIDO ==================
st.subheader("📊 Resultado Rápido")
m1, m2, m3, m4 = st.columns(4)
m1.metric("🔄 RPM do Rolo", f"{rpm_rolo_esp:.1f}")
m2.metric("⚡ Força de Perdas", f"{F_perdas_esp:.1f} N")
m3.metric("🔧 Torque no Freio", f"{torque_freio_esp:.1f} Nm")
m4.metric("💡 Potência Absorvida", f"{pot_freio_esp:.2f} kW")

m5, m6, m7, m8 = st.columns(4)
m5.metric("🚀 Acel. Linear", f"{a_acel:.2f} m/s²")
m6.metric("🛑 Desacel. Linear", f"{a_fren:.2f} m/s²")
m7.metric("➡️ F Inércia Acel.", f"{F_inercia_acel:.1f} N")
m8.metric("⬅️ F Inércia Fren.", f"{F_inercia_fren:.1f} N")

# ================== CURVAS COMPLETAS & TABELA ==================
with st.expander("📈 Curvas Completas e Tabela (0–200 km/h)", expanded=False):
    vel_kmh = np.linspace(0, 200, 41)
    vel_ms = vel_kmh / 3.6

    F_rr_arr = C_rr * massa_total_kg * g
    F_d_arr = 0.5 * rho * vel_ms**2 * CdA
    F_perdas_arr = F_rr_arr + F_d_arr
    torque_perdas_arr = F_perdas_arr * raio_rolo_m
    rpm_rolo_arr = (vel_ms * 60) / (2 * np.pi * raio_rolo_m)
    torque_aplicado_arr = np.minimum(torque_perdas_arr * 1.1, torque_freio_max_Nm)
    pot_perdas_arr = F_perdas_arr * vel_ms / 1000
    pot_freio_arr = torque_aplicado_arr * (rpm_rolo_arr * 2 * np.pi / 60) / 1000

    fig, axes = plt.subplots(2, 2, figsize=(10, 5))
    fig.tight_layout(pad=2.5)

    axes[0, 0].plot(vel_kmh, F_perdas_arr, color="#1E88E5", linewidth=1.8)
    axes[0, 0].set_title("Força de Perdas (N)", fontsize=9)
    axes[0, 0].set_xlabel("km/h", fontsize=8); axes[0, 0].set_ylabel("N", fontsize=8)
    axes[0, 0].grid(True, alpha=0.4)

    axes[0, 1].plot(vel_kmh, torque_perdas_arr, color="#E53935", linewidth=1.8, label="Perdas")
    axes[0, 1].plot(vel_kmh, torque_aplicado_arr, color="#43A047", linewidth=1.8, linestyle="--", label="Freio")
    axes[0, 1].set_title("Torque (Nm)", fontsize=9)
    axes[0, 1].set_xlabel("km/h", fontsize=8); axes[0, 1].set_ylabel("Nm", fontsize=8)
    axes[0, 1].legend(fontsize=7); axes[0, 1].grid(True, alpha=0.4)

    axes[1, 0].plot(vel_kmh, rpm_rolo_arr, color="#8E24AA", linewidth=1.8)
    axes[1, 0].set_title("RPM do Rolo", fontsize=9)
    axes[1, 0].set_xlabel("km/h", fontsize=8); axes[1, 0].set_ylabel("RPM", fontsize=8)
    axes[1, 0].grid(True, alpha=0.4)

    axes[1, 1].plot(vel_kmh, pot_perdas_arr, color="#FB8C00", linewidth=1.8, label="Perdas")
    axes[1, 1].plot(vel_kmh, pot_freio_arr, color="#43A047", linewidth=1.8, linestyle="--", label="Freio")
    axes[1, 1].set_title("Potência (kW)", fontsize=9)
    axes[1, 1].set_xlabel("km/h", fontsize=8); axes[1, 1].set_ylabel("kW", fontsize=8)
    axes[1, 1].legend(fontsize=7); axes[1, 1].grid(True, alpha=0.4)

    st.pyplot(fig)
    plt.close(fig)

    df = pd.DataFrame({
        "Vel (km/h)": vel_kmh,
        "RPM Rolo": np.round(rpm_rolo_arr, 1),
        "F Perdas (N)": np.round(F_perdas_arr, 1),
        "Torque Perdas (Nm)": np.round(torque_perdas_arr, 1),
        "Torque Freio (Nm)": np.round(torque_aplicado_arr, 1),
        "Pot Perdas (kW)": np.round(pot_perdas_arr, 2),
        "Pot Freio (kW)": np.round(pot_freio_arr, 2),
    })

    st.dataframe(df, use_container_width=True, height=220)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name="dynasilva_curvas.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ================== RODAPÉ ==================
st.markdown(
    "<p style='text-align:center;color:#aaa;font-size:0.75rem;margin-top:0.5rem;'>"
    "DynaSilva © 2024 — Simulador de Dinamômetro de Rolo para Motocicletas"
    "</p>",
    unsafe_allow_html=True,
)
