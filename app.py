import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import requests
from datetime import datetime

# Configuração para ambiente headless (Railway)
import matplotlib
matplotlib.use('Agg')

# ── Geolocation helper ──────────────────────────────────────────────────────

def fetch_weather_and_altitude(lat: float, lon: float) -> dict | None:
    """
    Fetch current temperature (°C) and surface pressure (hPa) from Open-Meteo,
    plus elevation (m) from the Open-Meteo elevation endpoint.
    Returns a dict with keys: altitude_m, temperature_c, pressure_hpa, city.
    Returns None on any network / parsing error.
    """
    try:
        # Elevation
        elev_url = (
            f"https://api.open-meteo.com/v1/elevation"
            f"?latitude={lat}&longitude={lon}"
        )
        elev_resp = requests.get(elev_url, timeout=8)
        elev_resp.raise_for_status()
        altitude_m = elev_resp.json()["elevation"][0]

        # Current weather (temperature + surface pressure)
        wx_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,surface_pressure"
            f"&forecast_days=1"
        )
        wx_resp = requests.get(wx_url, timeout=8)
        wx_resp.raise_for_status()
        current = wx_resp.json()["current"]
        temperature_c = current["temperature_2m"]
        pressure_hpa  = current["surface_pressure"]

        # Reverse-geocode for a human-readable city name (nominatim)
        geo_url = (
            f"https://nominatim.openstreetmap.org/reverse"
            f"?lat={lat}&lon={lon}&format=json"
        )
        geo_resp = requests.get(
            geo_url, timeout=8,
            headers={"User-Agent": "SimuladorDinamometro/1.0"}
        )
        city = "Localização desconhecida"
        if geo_resp.ok:
            addr = geo_resp.json().get("address", {})
            city = (
                addr.get("city")
                or addr.get("town")
                or addr.get("village")
                or addr.get("county")
                or addr.get("state")
                or city
            )

        return {
            "altitude_m":    altitude_m,
            "temperature_c": temperature_c,
            "pressure_hpa":  pressure_hpa,
            "city":          city,
        }
    except Exception:
        return None


def calc_air_density(temperature_c: float, pressure_hpa: float) -> float:
    """
    ρ = P / (R_specific × T)
    R_specific for dry air = 287.05 J/(kg·K)
    """
    T = temperature_c + 273.15          # Kelvin
    P = pressure_hpa * 100.0            # Pa
    R = 287.05                          # J/(kg·K)
    return P / (R * T)

st.set_page_config(page_title="Simulador Dinamômetro Moto", layout="wide")

# ── Compact layout: tighten Streamlit's default padding ─────────────────────
st.markdown(
    """
    <style>
        /* Reduce top padding of the main block */
        .block-container { padding-top: 0.6rem !important; padding-bottom: 0.5rem !important; }
        /* Tighten sidebar padding */
        section[data-testid="stSidebar"] > div:first-child { padding-top: 0.6rem; }
        /* Reduce gap between widgets */
        div[data-testid="stVerticalBlock"] > div { gap: 0.25rem; }
        /* Smaller metric labels */
        [data-testid="stMetricLabel"] { font-size: 0.78rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 🚀 Simulador de Dinamômetro com Freio Hidráulico")

st.sidebar.header("Parâmetros do Dinamômetro")

raio_rolo_mm = st.sidebar.slider(
    "Raio do Rolo (mm)", 50, 300, 150, 1,
    help="Raio do cilindro de contato com o pneu (50–300 mm)."
)
raio_rolo_m = raio_rolo_mm / 1000

massa_total_kg = st.sidebar.slider(
    "Massa Total (Moto + Piloto) kg", 100, 500, 280, 5,
    help="Massa da moto + piloto. Afeta F_rr = C_rr × m × g (100–500 kg)."
)
C_rr = st.sidebar.slider(
    "C_rr - Coef. Rolamento", 0.005, 0.05, 0.015, 0.001,
    help="Coeficiente de resistência ao rolamento do pneu (0,005–0,05)."
)
CdA = st.sidebar.slider(
    "CdA - Área Frontal Efetiva (m²)", 0.3, 1.2, 0.6, 0.05,
    help="Cd × área frontal da moto+piloto. F_d = ½ρv²CdA (0,3–1,2 m²)."
)
# ── Densidade do Ar ─────────────────────────────────────────────────────────
st.sidebar.markdown("**🌍 Densidade do Ar (kg/m³)**")

usar_geolocalizacao = st.sidebar.checkbox(
    "Usar geolocalização para ajustar densidade",
    value=False,
    help="Detecta localização e consulta altitude/temperatura via Open-Meteo.",
)

if usar_geolocalizacao:
    # Import here so the app still works if the package is not installed
    try:
        from streamlit_geolocation import streamlit_geolocation
        _geo_available = True
    except ImportError:
        _geo_available = False

    if not _geo_available:
        st.sidebar.error(
            "⚠️ Pacote `streamlit-geolocation` não encontrado. "
            "Adicione-o ao requirements.txt e reinicie o app."
        )
        rho = st.sidebar.number_input(
            "Densidade do Ar (kg/m³)", value=1.225, min_value=0.5, max_value=2.0, step=0.001,
            format="%.3f",
            help="Valor padrão ISA ao nível do mar a 15 °C.",
        )
    else:
        location = streamlit_geolocation()

        geo_lat  = location.get("latitude")  if location else None
        geo_lon  = location.get("longitude") if location else None

        if geo_lat is None or geo_lon is None:
            st.sidebar.info(
                "📍 Aguardando permissão de localização do navegador… "
                "Clique em **Permitir** quando solicitado."
            )
            rho = st.sidebar.number_input(
                "Densidade do Ar (kg/m³)", value=1.225, min_value=0.5, max_value=2.0, step=0.001,
                format="%.3f",
                help="Será substituído automaticamente após a localização ser detectada.",
            )
        else:
            # Cache the API call so it doesn't fire on every widget interaction
            @st.cache_data(ttl=300, show_spinner=False)
            def _get_weather(lat, lon):
                return fetch_weather_and_altitude(lat, lon)

            with st.sidebar:
                with st.spinner("Consultando dados meteorológicos…"):
                    weather = _get_weather(round(geo_lat, 4), round(geo_lon, 4))

            if weather is None:
                st.sidebar.warning(
                    "⚠️ Não foi possível obter dados meteorológicos. "
                    "Verifique sua conexão ou use o valor manual abaixo."
                )
                rho = st.sidebar.number_input(
                    "Densidade do Ar (kg/m³)", value=1.225, min_value=0.5, max_value=2.0, step=0.001,
                    format="%.3f",
                )
            else:
                rho_calculado = calc_air_density(
                    weather["temperature_c"], weather["pressure_hpa"]
                )

                # Show location info in an expander inside the sidebar
                with st.sidebar.expander("📊 Dados da localização", expanded=False):
                    st.markdown(f"**📍 Local:** {weather['city']}")
                    st.markdown(f"**🏔️ Altitude:** {weather['altitude_m']:.0f} m")
                    st.markdown(f"**🌡️ Temperatura:** {weather['temperature_c']:.1f} °C")
                    st.markdown(f"**🔵 Pressão:** {weather['pressure_hpa']:.1f} hPa")
                    st.markdown(f"**💨 ρ calculada:** `{rho_calculado:.4f}` kg/m³")
                    st.caption(f"Atualizado em: {datetime.now().strftime('%H:%M:%S')}")

                    if st.button("🔄 Atualizar localização"):
                        st.cache_data.clear()
                        st.rerun()

                # Allow manual override of the calculated value
                rho = st.sidebar.number_input(
                    "Densidade do Ar (kg/m³)",
                    value=round(rho_calculado, 4),
                    min_value=0.5,
                    max_value=2.0,
                    step=0.001,
                    format="%.4f",
                    help="Calculado pela localização. Ajuste manualmente se necessário.",
                )
else:
    rho = st.sidebar.number_input(
        "Densidade do Ar (kg/m³)",
        value=1.225,
        min_value=0.5,
        max_value=2.0,
        step=0.001,
        format="%.3f",
        help="Densidade do ar no ensaio. Padrão ISA ao nível do mar a 15 °C: 1,225 kg/m³.",
    )
torque_freio_max_Nm = st.sidebar.slider(
    "Torque Máx Freio Hidráulico (Nm)", 50, 500, 200, 10,
    help="Torque máximo do freio hidráulico no rolo (50–500 Nm)."
)

# === CONTROLES DE SIMULAÇÃO ESPECÍFICA ===
st.markdown("**🎯 Simulação Específica**")

col1, col2 = st.columns(2)

with col1:
    col_inp, col_minus, col_plus = st.columns([3, 1, 1])
    vel_especifica = col_inp.number_input(
        "Velocidade (km/h)",
        min_value=0.0, max_value=220.0, value=100.0, step=1.0,
        help="Velocidade alvo para a simulação pontual."
    )
    if col_minus.button("−5", use_container_width=True):
        vel_especifica = max(0.0, vel_especifica - 5)
    if col_plus.button("+5", use_container_width=True):
        vel_especifica = min(220.0, vel_especifica + 5)

with col2:
    col_tm, col_ts = st.columns(2)
    tempo_min = col_tm.number_input("Min", min_value=0, max_value=15, value=5, step=1)
    tempo_seg = col_ts.number_input("Seg", min_value=0, max_value=59, value=0, step=1)
    tempo_total_seg = tempo_min * 60 + tempo_seg
    st.caption(f"⏱️ Tempo total: **{tempo_min} min {tempo_seg} seg**")

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
st.markdown("**📊 Resultados da Simulação**")

# Destaque da velocidade escolhida
idx = (np.abs(df['Velocidade (km/h)'] - vel_especifica)).argmin()
row = df.iloc[idx]

col_m1, col_m2 = st.columns([3, 2])

with col_m1:
    st.dataframe(df, use_container_width=True, height=220)

with col_m2:
    st.success(f"**Resultado em {vel_especifica:.0f} km/h**")
    mc1, mc2 = st.columns(2)
    mc1.metric("RPM do Rolo", f"{row['RPM Rolo']}")
    mc2.metric("Força de Perdas", f"{row['F_perdas (N)']} N")
    mc1.metric("Torque de Perdas", f"{row['Torque Perdas (Nm)']} Nm")
    mc2.metric("Torque Freio", f"{row['Torque Freio (Nm)']} Nm")
    st.metric("Potência no Freio", f"{row['Potência Freio (kW)']} kW")

    st.download_button(
        label="📥 Baixar CSV",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name="resultados_dinamometro.csv",
        mime="text/csv",
        use_container_width=True,
    )

# ================== GRÁFICOS ==================
st.markdown("**📈 Gráficos**")
fig, axs = plt.subplots(2, 2, figsize=(10, 5))

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

plt.tight_layout(pad=0.8)
st.pyplot(fig, use_container_width=True)

st.caption("🔧 Ajuste os parâmetros na barra lateral — tudo atualiza em tempo real. | Projeto Dinamômetro com Freio Hidráulico de Moto")
