import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(layout="centered", page_title="Simulación: Biomasa a Electricidad")

# --- Título y Descripción (mantener) ---
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
    </style>
    <h1 class="big-title">🌱 Simulación: Biomasa a Electricidad ⚡</h1>
    <p class="note">Ajusta los parámetros para ver cómo la biomasa se convierte en electricidad a través del syngas. Esta es una simulación conceptual y simplificada.</p>
""", unsafe_allow_html=True)

# --- Contenedor principal para organizar el diagrama y los parámetros ---
st.markdown("## Parámetros de Entrada")

# Puedes usar un contenedor para agrupar visualmente esta sección
with st.container(border=True):
    st.markdown("### Diagrama del Sistema y Parámetros")

    # Usamos columnas para colocar los parámetros alrededor del diagrama.
    # Los ratios (ej. [0.8, 3, 1]) definen el ancho relativo de cada columna.
    # Ajusta estos valores para que se vea bien con tu diagrama.
    col_params_izq, col_diagrama, col_params_der = st.columns([0.9, 3, 1.2]) # Ajusta los anchos aquí

    with col_params_izq:
        st.subheader("Entrada de Biomasa")
        biomass_flow = st.number_input(
            "Flujo (kg/h):",
            min_value=50,
            max_value=500,
            value=100,
            step=10,
            help="Cantidad de biomasa alimentada al gasificador por hora."
        )
        biomass_energy = st.number_input(
            "PCI (MJ/kg):",
            min_value=15.0,
            max_value=25.0,
            value=18.0,
            step=0.5,
            format="%.1f",
            help="Poder calorífico inferior de la biomasa."
        )
        # Puedes añadir otros inputs aquí si pertenecen a la fase de entrada de biomasa

    with col_diagrama:
        # Asegúrate de que tu archivo de imagen 'image_3c55b6.png' esté en la misma carpeta que tu script
        st.image("image_3c55b6.png",
                 caption="Diagrama del Proceso de Conversión",
                 use_container_width=True) # Usamos use_container_width según la advertencia

    with col_params_der:
        st.subheader("Proceso y Salida")
        syngas_calorific_value = st.number_input(
            "PCI Syngas (MJ/Nm³):",
            min_value=3.0,
            max_value=7.0,
            value=5.0,
            step=0.1,
            format="%.1f",
            help="Poder calorífico inferior del syngas."
        )
        engine_efficiency = st.number_input(
            "Eficiencia Motor-Gen (%):",
            min_value=20.0,
            max_value=45.0,
            value=30.0,
            step=0.5,
            format="%.1f",
            help="Porcentaje de la energía del syngas convertida en electricidad."
        )
        # Puedes añadir otros inputs aquí si pertenecen a la fase de salida

    # Parámetros que afectan a todo el sistema o que no caben bien en los lados
    st.subheader("Eficiencias y Operación General")
    gasification_efficiency = st.number_input(
        "Eficiencia de Gasificación (%):",
        min_value=50,
        max_value=85,
        value=70,
        step=1,
        help="Porcentaje de la energía de la biomasa convertida en energía en el syngas."
    ) / 100.0 # Convertir a decimal

    hours_operated = st.number_input(
        "Horas de Operación (h):",
        min_value=1,
        max_value=8760, # Un año completo tiene 8760 horas
        value=8,
        step=1,
        help="Número de horas que el sistema opera para el cálculo total (ej. diario, anual)."
    )


st.markdown("---") # Línea divisoria

st.markdown("## Resultados de la Simulación")

# --- Realizar los cálculos de la simulación (mantener lo mismo) ---
total_biomass_consumed = biomass_flow * hours_operated
total_biomass_energy = total_biomass_consumed * biomass_energy
energy_in_syngas = total_biomass_energy * gasification_efficiency

# Evitar división por cero si el poder calorífico del syngas es cero
volume_syngas_produced = energy_in_syngas / syngas_calorific_value if syngas_calorific_value > 0 else 0

electric_energy_generated_mj = energy_in_syngas * engine_efficiency
electric_energy_generated_kwh = electric_energy_generated_mj * 0.2778  # Factor de conversión: 1 MJ = 0.2778 kWh

# Evitar división por cero si las horas de operación son cero
average_power_output = electric_energy_generated_kwh / hours_operated if hours_operated > 0 else 0

# --- Cálculo de CO2 Producido (mantener lo mismo) ---
# Asunciones para la composición del syngas (volumétrica, base seca, libre de N2 y CO2 inicial)
co_percentage = 0.20
ch4_percentage = 0.03

molar_volume_stp = 22.4
co2_molar_mass = 44

moles_co = (volume_syngas_produced * co_percentage) / molar_volume_stp
moles_ch4 = (volume_syngas_produced * ch4_percentage) / molar_volume_stp
moles_co2_produced = moles_co + moles_ch4
mass_co2_produced = moles_co2_produced * co2_molar_mass

# --- Mostrar los resultados calculados (mantener lo mismo) ---
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
