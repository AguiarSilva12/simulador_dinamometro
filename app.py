import streamlit as st
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests

# ================== GEOLOCATION & AIR DENSITY ==================
def fetch_weather_and_altitude(lat, lon):
    """Fetch altitude and weather data from open APIs to compute air density."""
    try:
        # Altitude via Open-Elevation API
        elev_resp = requests.get(
            "https://api.open-elevation.com/api/v1/lookup",
            params={"locations": f"{lat},{lon}"},
            timeout=5,
        )
        altitude_m = elev_resp.json()["results"][0]["elevation"]
    except Exception:
        altitude_m = 0.0

    try:
        # Temperature & pressure via Open-Meteo (free, no key required)
        wx_resp = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": True,
                "hourly": "surface_pressure,temperature_2m",
                "forecast_days": 1,
            },
            timeout=5,
        )
        wx = wx_resp.json()
        temp_c = wx["hourly"]["temperature_2m"][0]
        pressure_hpa = wx["hourly"]["surface_pressure"][0]
    except Exception:
        temp_c = 15.0
        pressure_hpa = 1013.25

    return altitude_m, temp_c, pressure_hpa


def calc_air_density(temp_c, pressure_hpa):
    """Calculate air density using the ideal gas law for dry air."""
    R = 287.05  # J/(kg·K) — specific gas constant for dry air
    T_k = temp_c + 273.15
    P_pa = pressure_hpa * 100.0
    return P_pa / (R * T_k)


# ================== PAGE CONFIG & CSS ==================
st.set_page_config(page_title="DynaSilva", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* Compact global padding */
    .block-container { padding-top: 0.6rem !important; padding-bottom: 0.5rem !important; }
    /* Tighter section headers */
    h2, h3 { margin-top: 0.4rem !important; margin-bottom: 0.2rem !important; }
    /* Reduce widget label size */
    .stSlider label, .stNumberInput label, .stTimeInput label { font-size: 0.82rem !important; }
    /* Metric cards */
    [data-testid="metric-container"] { background: #f0f4ff; border-radius: 8px; padding: 6px 10px !important; }
    /* Scrollable dataframe */
    [data-testid="stDataFrame"] > div { max-height: 220px; overflow-y: auto; }
    /* Inline button row */
    div[data-testid="column"] > div > div > button { padding: 0.2rem 0.6rem !important; font-size: 0.8rem !important; }
</style>
""", unsafe_allow_html=True)

# ================== TITLE ==================
st.markdown("""
    <h1 style='text-align:center;color:#1E88E5;margin-bottom:0.1rem;font-size:1.5rem;'>
        DynaSilva — Simulador de Dinamômetro com Freio Hidráulico
    </h1>
    <p style='text-align:center;color:#666;margin-top:0;font-size:0.85rem;'>
        🏍️ Rolo + Sensor de Rotação + Célula de Carga
    </p>
""", unsafe_allow_html=True)

# ================== GEOLOCATION PANEL ==================
with st.expander("📍 Ajuste de Densidade do Ar por Geolocalização", expanded=False):
    st.caption("Clique em **Obter Localização** para buscar temperatura, pressão e altitude automaticamente.")
    try:
        from streamlit_geolocation import streamlit_geolocation
        location = streamlit_geolocation()
    except ImportError:
        location = None
        st.warning("Pacote `streamlit-geolocation` não instalado. Instale via `pip install streamlit-geolocation`.")

    rho_default = 1.225
    geo_info = ""
    if location and location.get("latitude") and location.get("longitude"):
        lat = location["latitude"]
        lon = location["longitude"]
        with st.spinner("Buscando dados meteorológicos…"):
            alt_m, temp_c, pres_hpa = fetch_weather_and_altitude(lat, lon)
        rho_default = round(calc_air_density(temp_c, pres_hpa), 4)
        geo_info = (
            f"📌 Lat {lat:.4f} / Lon {lon:.4f} | "
            f"Altitude ≈ {alt_m:.0f} m | "
            f"Temp {temp_c:.1f} °C | "
            f"Pressão {pres_hpa:.1f} hPa → **ρ = {rho_default} kg/m³**"
        )
        st.success(geo_info)

# ================== PARÂMETROS EM EXPANDER ==================
with st.expander("⚙️ Parâmetros do Dinamômetro", expanded=False):
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        raio_rolo_m = st.slider("Raio do Rolo (m)", 0.05, 0.30, 0.15, 0.01)
        massa_total_kg = st.slider("Massa Total (kg)", 100, 500, 280, 5)
        C_rr = st.slider("C_rr — Coef. Rolamento", 0.005, 0.05, 0.015, 0.001)
    with col_p2:
        CdA = st.slider("CdA — Área Frontal (m²)", 0.3, 1.2, 0.6, 0.05)
        rho = st.number_input("Densidade do Ar (kg/m³)", value=rho_default, step=0.001, format="%.4f")
        torque_freio_max_Nm = st.slider("Torque Máx Freio Hidráulico (Nm)", 50, 600, 200, 10)

g = 9.81

# ================== SIMULAÇÃO ESPECÍFICA ==================
st.subheader("🎯 Simulação Específica")
col1, col2 = st.columns(2)

with col1:
    vel_especifica = st.number_input(
        "Velocidade (km/h)", min_value=0.0, max_value=220.0, value=100.0, step=1.0,
        help="Velocidade alvo para cálculo pontual."
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

# ---- Cálculos pontuais ----
vel_ms_esp = vel_especifica / 3.6
rpm_rolo_esp = (vel_ms_esp * 60) / (2 * np.pi * raio_rolo_m) if raio_rolo_m > 0 else 0.0
F_rr_esp = C_rr * massa_total_kg * g
F_d_esp = 0.5 * rho * vel_ms_esp**2 * CdA
F_perdas_esp = F_rr_esp + F_d_esp
torque_perdas_esp = F_perdas_esp * raio_rolo_m
torque_freio_esp = min(torque_perdas_esp * 1.1, torque_freio_max_Nm)
pot_perdas_esp = F_perdas_esp * vel_ms_esp / 1000
pot_freio_esp = torque_freio_esp * (rpm_rolo_esp * 2 * np.pi / 60) / 1000 if rpm_rolo_esp > 0 else 0.0

# ---- Métricas em grade 2×2 ----
m1, m2 = st.columns(2)
m3, m4 = st.columns(2)
m1.metric("🔄 RPM do Rolo", f"{rpm_rolo_esp:.1f}")
m2.metric("⚡ Força de Perdas", f"{F_perdas_esp:.1f} N")
m3.metric("🔧 Torque no Freio", f"{torque_freio_esp:.1f} Nm")
m4.metric("💡 Potência Absorvida", f"{pot_freio_esp:.2f} kW")

# ================== CURVAS COMPLETAS ==================
st.subheader("📈 Curvas Completas (0–200 km/h)")

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

# ================== TABELA DE RESULTADOS ==================
st.subheader("📋 Tabela de Resultados")

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

# ================== RODAPÉ ==================
st.markdown(
    "<p style='text-align:center;color:#aaa;font-size:0.75rem;margin-top:0.5rem;'>"
    "DynaSilva © 2024 — Simulador de Dinamômetro de Rolo para Motocicletas"
    "</p>",
    unsafe_allow_html=True,
)
