import streamlit as st
import pandas as pd
import numpy as np

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
    </style>
    <h1 class="big-title">🌱 Simulación: Biomasa a Electricidad ⚡</h1>
    <p class="note">Ajusta los parámetros para ver cómo la biomasa se convierte en electricidad a través del syngas. Esta es una simulación conceptual y simplificada.</p>
""", unsafe_allow_html=True)

# --- Diagrama del Sistema ---
# Usamos un placeholder genérico. Si tienes tu propia imagen, reemplaza la URL.
st.image("https://placehold.co/600x300/e0e0e0/555555?text=Diagrama+del+Sistema",
         caption="Diagrama del Sistema de Gasificación de Biomasa",
         use_container_width=True) # Actualizado: use_column_width ha sido deprecado

st.markdown("## Parámetros de Entrada")

# --- Parámetros de Entrada con Campos Numéricos ---
biomass_flow = st.number_input(
    "Flujo de Biomasa (kg/h):",
    min_value=50,
    max_value=500,
    value=100,
    step=10,
    help="Cantidad de biomasa alimentada al gasificador por hora."
)

biomass_energy = st.number_input(
    "Poder Calorífico Biomasa (MJ/kg):",
    min_value=15.0,
    max_value=25.0,
    value=18.0,
    step=0.5,
    format="%.1f",
    help="Energía contenida por unidad de masa de biomasa (PCI)."
)

gasification_efficiency = st.number_input(
    "Eficiencia de Gasificación (%):",
    min_value=50,
    max_value=85,
    value=70,
    step=1,
    help="Porcentaje de la energía de la biomasa convertida en energía en el syngas."
) / 100.0 # Convertir a decimal

syngas_calorific_value = st.number_input(
    "Poder Calorífico Syngas (MJ/Nm³):",
    min_value=3.0,
    max_value=7.0,
    value=5.0,
    step=0.1,
    format="%.1f",
    help="Energía contenida por unidad de volumen normal de syngas (PCI)."
)

engine_efficiency = st.number_input(
    "Eficiencia Motor-Generador (%):",
    min_value=20.0,
    max_value=45.0,
    value=30.0,
    step=0.5,
    format="%.1f",
    help="Porcentaje de la energía del syngas convertida en electricidad."
) / 100.0 # Convertir a decimal

hours_operated = st.number_input(
    "Horas de Operación:",
    min_value=1,
    max_value=24, # O puedes cambiar a 8760 para operación anual
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
co_percentage = 0.20
ch4_percentage = 0.03

molar_volume_stp = 22.4
co2_molar_mass = 44

moles_co = (volume_syngas_produced * co_percentage) / molar_volume_stp
moles_ch4 = (volume_syngas_produced * ch4_percentage) / molar_volume_stp
moles_co2_produced = moles_co + moles_ch4
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

st.markdown("---")

## 💡 Balances de Materia y Energía Utilizados para el Cálculo

with st.expander("Ver Balances de Materia y Energía"):
    st.markdown("""
    Aquí se detallan las ecuaciones principales utilizadas para los cálculos de la simulación.
    """)

    st.subheader("1. Balance de Energía de la Biomasa")
    st.latex(r'''
        H_{\text{Biomasa}} = F_{\text{Biomasa}} \times \text{PCI}_{\text{Biomasa}} \times t_{\text{operación}}
    ''')
    st.markdown("""
    Donde:
    * $H_{\\text{Biomasa}}$ es la energía total disponible en la biomasa (MJ).
    * $F_{\\text{Biomasa}}$ es el flujo de biomasa (kg/h).
    * $\\text{PCI}_{\\text{Biomasa}}$ es el Poder Calorífico Inferior de la biomasa (MJ/kg).
    * $t_{\\text{operación}}$ son las horas de operación (h).
    """)

    st.subheader("2. Energía en el Syngas")
    st.latex(r'''
        H_{\text{Syngas}} = H_{\text{Biomasa}} \times \eta_{\text{gasificación}}
    ''')
    st.markdown("""
    Donde:
    * $H_{\\text{Syngas}}$ es la energía contenida en el syngas (MJ).
    * $\eta_{\\text{gasificación}}$ es la eficiencia de gasificación (adimensional).
    """)

    st.subheader("3. Volumen de Syngas Producido")
    st.latex(r'''
        V_{\text{Syngas}} = \frac{H_{\text{Syngas}}}{\text{PCI}_{\text{Syngas}}}
    ''')
    st.markdown("""
    Donde:
    * $V_{\\text{Syngas}}$ es el volumen de syngas producido (\text{Nm}^3).
    * $\\text{PCI}_{\\text{Syngas}}$ es el Poder Calorífico Inferior del syngas (\text{MJ/Nm}^3).
    """)

    st.subheader("4. Energía Eléctrica Generada")
    st.latex(r'''
        E_{\text{eléctrica}} = H_{\text{Syngas}} \times \eta_{\text{motor-generador}}
    ''')
    st.markdown("""
    Donde:
    * $E_{\\text{eléctrica}}$ es la energía eléctrica generada (MJ).
    * $\eta_{\\text{motor-generador}}$ es la eficiencia del motor-generador (adimensional).
    """)

    st.latex(r'''
        E_{\text{eléctrica, kWh}} = E_{\text{eléctrica, MJ}} \times 0.2778 \frac{\text{kWh}}{\text{MJ}}
    ''')
    st.markdown("""
    Donde:
    * $E_{\\text{eléctrica, kWh}}$ es la energía eléctrica en kilovatios-hora (kWh).
    """)

    st.subheader("5. Potencia Eléctrica Promedio")
    st.latex(r'''
        P_{\text{promedio}} = \frac{E_{\text{eléctrica, kWh}}}{t_{\text{operación}}}
    ''')
    st.markdown("""
    Donde:
    * $P_{\\text{promedio}}$ es la potencia eléctrica promedio (kW).
    """)

    st.subheader("6. Emisiones de $\\text{CO}_2$ (basado en combustión de Syngas)")
    st.latex(r'''
        \text{moles}_{\text{CO}} = \frac{V_{\text{Syngas}} \times \text{frac}_{\text{CO}}}{\text{Volumen Molar}}
    ''')
    st.latex(r'''
        \text{moles}_{\text{CH}_4} = \frac{V_{\text{Syngas}} \times \text{frac}_{\text{CH}_4}}{\text{Volumen Molar}}
    ''')
    st.latex(r'''
        \text{moles}_{\text{CO}_2, \text{total}} = \text{moles}_{\text{CO}} + \text{moles}_{\text{CH}_4}
    ''')
    st.latex(r'''
        \text{Masa}_{\text{CO}_2} = \text{moles}_{\text{CO}_2, \text{total}} \times \text{Masa Molar}_{\text{CO}_2}
    ''')
    st.markdown("""
    Donde:
    * $\\text{frac}_{\\text{CO}}$ y $\\text{frac}_{\\text{CH}_4}$ son las fracciones volumétricas de CO y $\\text{CH}_4$ en el syngas, respectivamente.
    * Volumen Molar es el volumen molar estándar (22.4 $\\text{Nm}^3$/kmol).
    * Masa Molar$_{\\text{CO}_2}$ es la masa molar del dióxido de carbono (44 kg/kmol).
    * Estas ecuaciones asumen que todo el CO y $\\text{CH}_4$ en el syngas se convierten completamente en $\\text{CO}_2$ durante la combustión.
    """)
