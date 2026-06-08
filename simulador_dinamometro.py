import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ================== PARÂMETROS DO SEU DINAMÔMETRO ==================
raio_rolo_m = 0.15          # Raio do rolo (ajuste com o seu)
massa_total_kg = 280        # Moto + piloto
C_rr = 0.015                # Coeficiente de rolamento
CdA = 0.6                   # Área frontal efetiva (m²)
rho = 1.225                 # Densidade do ar
g = 9.81

# Parâmetros do freio hidráulico (simulação)
torque_freio_max_Nm = 200   # Torque máximo que o freio hidráulico consegue absorver

# ================== SIMULAÇÃO ==================
vel_kmh = np.linspace(0, 200, 41)
vel_ms = vel_kmh / 3.6

F_rr = C_rr * massa_total_kg * g
F_d = 0.5 * rho * vel_ms**2 * CdA
F_perdas = F_rr + F_d

# Força no rolo → Torque no rolo
torque_perdas_Nm = F_perdas * raio_rolo_m

# RPM do rolo (relação com velocidade linear)
rpm_rolo = (vel_ms * 60) / (2 * np.pi * raio_rolo_m)

# Simulação do freio hidráulico (exemplo: controla para manter velocidade)
torque_aplicado = np.minimum(torque_perdas_Nm * 1.1, torque_freio_max_Nm)

# Potência
potencia_perdas_kw = F_perdas * vel_ms / 1000
potencia_freio_kw = torque_aplicado * (rpm_rolo * 2 * np.pi / 60) / 1000

df = pd.DataFrame({
    'Velocidade (km/h)': vel_kmh,
    'RPM Rolo': np.round(rpm_rolo, 1),
    'F_perdas (N)': np.round(F_perdas, 1),
    'Torque Perdas (Nm)': np.round(torque_perdas_Nm, 1),
    'Torque Freio Aplicado (Nm)': np.round(torque_aplicado, 1),
    'Potência Perdas (kW)': np.round(potencia_perdas_kw, 2),
    'Potência Absorvida Freio (kW)': np.round(potencia_freio_kw, 2)
})

print(df.head(10))
df.to_excel('Resultados_Simulacao_Dinamometro.xlsx', index=False)

# Gráficos
plt.figure(figsize=(12, 8))
plt.subplot(2, 2, 1)
plt.plot(vel_kmh, F_perdas, label='Perdas Totais')
plt.xlabel('Velocidade (km/h)'); plt.ylabel('Força (N)'); plt.legend(); plt.grid()

plt.subplot(2, 2, 2)
plt.plot(vel_kmh, torque_perdas_Nm, 'r', label='Torque Perdas')
plt.plot(vel_kmh, torque_aplicado, 'g--', label='Torque Freio')
plt.xlabel('Velocidade (km/h)'); plt.ylabel('Torque (Nm)'); plt.legend(); plt.grid()

plt.subplot(2, 2, 3)
plt.plot(vel_kmh, rpm_rolo, 'b')
plt.xlabel('Velocidade (km/h)'); plt.ylabel('RPM Rolo'); plt.grid()

plt.subplot(2, 2, 4)
plt.plot(vel_kmh, potencia_perdas_kw, label='Perdas (kW)')
plt.plot(vel_kmh, potencia_freio_kw, 'g', label='Freio Hidráulico')
plt.xlabel('Velocidade (km/h)'); plt.ylabel('Potência (kW)'); plt.legend(); plt.grid()

plt.tight_layout()
plt.savefig('graficos_dinamometro.png')
plt.show()

print("\n✅ Simulação concluída! Arquivos gerados:")
print("- Resultados_Simulacao_Dinamometro.xlsx")
print("- graficos_dinamometro.png")
