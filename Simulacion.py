import streamlit as st
import pandas as pd # Aunque no se usa directamente en esta versión, es útil para datos
import numpy as np  # Para cálculos numéricos

st.set_page_config(layout="centered", page_title="Simulación: Biomasa a Electricidad")

# --- Título y Descripción ---
st.markdown("""
    <style>
    .big-title {
        font-size: 2.5rem;
        color: #1a202c;
        text-align: center;
        margin-bottom: 20px;
        font-weight: 700;
    }
    .note {
        font-size: 0.95em;
        color: #666;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 30px;
    }
    .results-container {
        padding: 25px;
        background-color: #e6fffa;
        border: 1px solid #81e6d9;
        border-radius: 10px;
        font-size: 1.15em;
        line-height: 1.6;
        margin-top: 30px;
    }
    .results-p {
        margin: 10px 0;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 5px;
        border-bottom: 1px dashed #b2f5ea;
    }
    .results-p:last-child {
        border-bottom: none;
    }
    .results-strong {
        color: #38b2ac;
        font-weight: 700;
        font-size: 1.2em;
    }
    .diagram-img {
        max-width: 100%;
        height: auto;
        border: 2px solid #a0aec0;
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        /* No se puede aplicar @keyframes directamente en Markdown/HTML de Streamlit
           sin usar st.components.v1.html y CSS incrustado completo,
           así que se omite la animación de pulso por simplicidad en este contexto. */
    }
    </style>
    <h1 class="big-title">🌱 Simulación: Biomasa a Electricidad ⚡</h1>
    <p class="note">Ajusta los parámetros para ver cómo la biomasa se convierte en electricidad a través del syngas. Esta es una simulación conceptual y simplificada.</p>
""", unsafe_allow_html=True)

# --- Diagrama del Sistema ---
st.image("https://placehold.co/600x300/e0e0e0/555555?text=Diagrama+del+Sistema",
         caption="Diagrama del Sistema de Gasificación de Biomasa",
         use_column_width=True)

st.markdown("## Parámetros de Entrada")

# --- Parámetros de Entrada con Sliders ---
biomass_flow = st.slider(
    "Flujo de Biomasa (kg/h):",
    min_value=50,
    max_value=500,
    value=100,
    step=10,
    help="Cantidad de biomasa alimentada al gasificador por hora."
)

biomass_energy = st.slider(
    "Poder Calorífico Biomasa (MJ/kg):",
    min_value=15.0,
    max_value=25.0,
    value=18.0,
    step=0.5,
    format="%.1f",
    help="Energía contenida por unidad de masa de biomasa (PCI)."
)

gasification_efficiency = st.slider(
    "Eficiencia de Gasificación (%):",
    min_value=50,
    max_value=85,
    value=70,
    step=1,
    help="Porcentaje de la energía de la biomasa convertida en energía en el syngas."
) / 100.0 # Convertir a decimal

syngas_calorific_value = st.slider(
    "Poder Calorífico Syngas (MJ/Nm³):",
    min_value=3.0,
    max_value=7.0,
    value=5.0,
    step=0.1,
    format="%.1f",
    help="Energía contenida por unidad de volumen normal de syngas (PCI)."
)

engine_efficiency = st.slider(
    "Eficiencia Motor-Generador (%):",
    min_value=20.0,
    max_value=45.0,
    value=30.0,
    step=0.5,
    format="%.1f",
    help="Porcentaje de la energía del syngas convertida en electricidad."
) / 100.0 # Convertir a decimal

hours_operated = st.slider(
    "Horas de Operación:",
    min_value=1,
    max_value=24,
    value=8,
    step=1,
    help="Número de horas que el sistema opera para el cálculo total."
)

st.markdown("---") # Línea divisoria

st.markdown("## Resultados de la Simulación")

# --- Realizar los cálculos de la simulación ---
total_biomass_consumed = biomass_flow * hours_operated
total_biomass_energy = total_biomass_consumed * biomass_energy
energy_in_syngas = total_biomass_energy * gasification_efficiency

# Evitar división por cero si el poder calorífico del syngas es cero
volume_syngas_produced = energy_in_syngas / syngas_calorific_value if syngas_calorific_value > 0 else 0

electric_energy_generated_mj = energy_in_syngas * engine_efficiency
electric_energy_generated_kwh = electric_energy_generated_mj * 0.2778  # Factor de conversión: 1 MJ = 0.2778 kWh

# Evitar división por cero si las horas de operación son cero
average_power_output = electric_energy_generated_kwh / hours_operated if hours_operated > 0 else 0

# --- Cálculo de CO2 Producido ---
# Asunciones para la composición del syngas (volumétrica, base seca, libre de N2 y CO2 inicial)
# Estas son simplificaciones para la simulación conceptual.
# Se asume que el syngas contiene un 20% de CO y un 3% de CH4 en volumen.
co_percentage = 0.20   # 20% de CO en el syngas
ch4_percentage = 0.03  # 3% de CH4 en el syngas

# Constante molar de volumen (Nm³/kmol) a 0°C y 1 atm (condiciones normales)
molar_volume_stp = 22.4
# Masa molar de CO2 (kg/kmol)
co2_molar_mass = 44  # g/mol = kg/kmol

# Moles de CO y CH4 en el volumen total de syngas producido
# (Volumen de gas * % de componente) / Volumen molar estándar
moles_co = (volume_syngas_produced * co_percentage) / molar_volume_stp
moles_ch4 = (volume_syngas_produced * ch4_percentage) / molar_volume_stp

# Moles de CO2 producidos por combustión
# Reacciones: CO + 0.5 O2 -> CO2 (1 mol CO produce 1 mol CO2)
#             CH4 + 2 O2 -> CO2 + 2 H2O (1 mol CH4 produce 1 mol CO2)
moles_co2_produced = moles_co + moles_ch4

# Masa de CO2 producida (en kg)
mass_co2_produced = moles_co2_produced * co2_molar_mass

# --- Mostrar los resultados calculados ---
st.markdown(f"""
    <div class="results-container">
        <p class="results-p">Biomasa Consumida (total): <strong class="results-strong">{total_biomass_consumed:.2f}</strong> kg</p>
        <p class="results-p">Energía Total de Biomasa: <strong class="results-strong">{total_biomass_energy:.2f}</strong> MJ</p>
        <p class="results-p">Energía en Syngas Producido: <strong class="results-strong">{energy_in_syngas:.2f}</strong> MJ</p>
        <p class="results-p">Volumen de Syngas Producido: <strong class="results-strong">{volume_syngas_produced:.2f}</strong> Nm³</p>
        <p class="results-p">Energía Eléctrica Generada: <strong class="results-strong">{electric_energy_generated_mj:.2f}</strong> MJ</p>
        <p class="results-p">Electricidad Generada: <strong class="results-strong">{electric_energy_generated_kwh:.2f}</strong> kWh</p>
        <p class="results-p">Potencia Eléctrica Promedio: <strong class="results-strong">{average_power_output:.2f}</strong> kW</p>
        <p class="results-p">CO2 Producido (combustión): <strong class="results-strong">{mass_co2_produced:.2f}</strong> kg</p>
    </div>
""", unsafe_allow_html=True)
