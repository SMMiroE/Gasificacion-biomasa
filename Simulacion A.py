import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import fsolve # Importamos el solver numérico

st.set_page_config(layout="centered", page_title="Simulación: Biomasa a Electricidad")

# --- Constantes y Masas Molares ---
# Masas molares de elementos (g/mol o kg/kmol)
MW_C = 12.011
MW_H = 1.008
MW_O = 15.999
MW_N = 14.007
MW_S = 32.06

# Masas molares de compuestos (g/mol o kg/kmol)
MW_H2 = 2 * MW_H
MW_CO = MW_C + MW_O
MW_CO2 = MW_C + 2 * MW_O
MW_CH4 = MW_C + 4 * MW_H
MW_H2O = 2 * MW_H + MW_O
MW_O2 = 2 * MW_O
MW_N2 = 2 * MW_N
MW_AIR = 28.97 # Masa molar promedio del aire

# Constante universal de los gases ideales (J/(mol*K))
R_UNIVERSAL = 8.314

# PCI de gases puros (MJ/Nm3) en condiciones normales (0°C, 1 atm)
# Fuente: Valores típicos de referencia
PCI_H2_Nm3 = 10.79 # MJ/Nm3
PCI_CO_Nm3 = 12.63 # MJ/Nm3
PCI_CH4_Nm3 = 35.80 # MJ/Nm3

# Volumen molar estándar (Nm3/kmol)
MOLAR_VOLUME_NTP = 22.414 # Nm3/kmol a 0°C y 1 atm (NTP)

# --- Funciones Auxiliares para Constantes de Equilibrio ---
def calculate_k_wgsr(T_k):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de desplazamiento de gas de agua (WGSR).
    CO + H2O <=> CO2 + H2
    Fuente: Journal of Environmental Chemical Engineering 8 (2020) 103755
    """
    log_kp = -2.2562 + (1829.0 / T_k) + 0.3546 * np.log(T_k) - (1.189 * 10**-4 * T_k) + (1.936 * 10**-8 * T_k**2)
    return np.exp(log_kp)

def calculate_k_boudouard(T_k):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de Boudouard.
    C + CO2 <=> 2CO
    Fuente: Adaptado de varias fuentes, basado en delta G.
    log10(Kp) = 8.775 - (9013/T) - 1.144 log10(T) + 2.06*10^-4 T - 1.57*10^-7 T^3 + 4.97*10^-11 T^3
    Convertir a ln(Kp) y base e.
    """
    # Usando una correlación simplificada para Boudouard
    # Kp = exp(A/T + B) para Boudouard: C + CO2 = 2CO
    # Para la reacción CO2 + C <=> 2CO, dG = 171 - 175.7*10^-3 T (kJ/mol)
    # Kp = exp(-dG/RT)
    delta_g = 171000 - 175.7 * T_k # J/mol
    kp = np.exp(-delta_g / (R_UNIVERSAL * T_k))
    return kp

def calculate_k_methanation(T_k):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de Metanación.
    CO + 3H2 <=> CH4 + H2O
    Fuente: Adaptado de varias fuentes, basado en delta G.
    """
    # Para la reacción CO + 3H2 <=> CH4 + H2O
    # Delta G = -215.93 + 0.233*T (kJ/mol)
    delta_g = -215930 + 0.233 * T_k # J/mol
    kp = np.exp(-delta_g / (R_UNIVERSAL * T_k))
    return kp


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
        align-items: center;
        padding-bottom: 5px;
        border-bottom: 1px dashed #b2f5ea;
    }
    .results-p:last-child {
        border-bottom: none;
    }
    .results-label {
        flex: 1;
        text-align: left;
        padding-right: 15px;
        min-width: 180px;
    }
    .results-value {
        font-weight: 700;
        color: #38b2ac;
        font-size: 1.2em;
        text-align: right;
        min-width: 120px;
    }
    </style>
    <h1 class="big-title">🌱 Simulación: Biomasa a Electricidad ⚡</h1>
    <p class="note">Ajusta los parámetros para ver cómo la biomasa se convierte en electricidad a través del syngas. Esta es una simulación conceptual y simplificada.</p>
""", unsafe_allow_html=True)

# --- Sección de Parámetros de Entrada ---
st.markdown("## Parámetros de Entrada")

st.subheader("Parámetros de la Biomasa")
biomass_flow = st.number_input(
    "Flujo de Biomasa (kg/h):",
    min_value=50,
    max_value=500,
    value=100,
    step=10,
    help="Cantidad de biomasa alimentada al gasificador por hora."
)

st.markdown("### Composición Elemental de la Biomasa (en peso, base seca y libre de cenizas)")
st.info("La suma de Carbono, Hidrógeno, Oxígeno, Nitrógeno y Azufre debe ser aproximadamente 100%.")

col_c, col_h, col_o = st.columns(3)
with col_c:
    biomass_C = st.number_input("Carbono (C) [%]:", min_value=0.0, max_value=100.0, value=50.0, step=0.1, format="%.1f") / 100.0
with col_h:
    biomass_H = st.number_input("Hidrógeno (H) [%]:", min_value=0.0, max_value=100.0, value=6.0, step=0.1, format="%.1f") / 100.0
with col_o:
    biomass_O = st.number_input("Oxígeno (O) [%]:", min_value=0.0, max_value=100.0, value=43.0, step=0.1, format="%.1f") / 100.0

col_n, col_s = st.columns(2)
with col_n:
    biomass_N = st.number_input("Nitrógeno (N) [%]:", min_value=0.0, max_value=10.0, value=0.5, step=0.01, format="%.2f") / 100.0
with col_s:
    biomass_S = st.number_input("Azufre (S) [%]:", min_value=0.0, max_value=10.0, value=0.0, step=0.01, format="%.2f") / 100.0

sum_elemental = (biomass_C + biomass_H + biomass_O + biomass_N + biomass_S) * 100
if abs(sum_elemental - 100) > 0.1:
    st.warning(f"La suma de C, H, O, N, S (base seca y libre de cenizas) es {sum_elemental:.1f}%. Debería ser ~100%. Por favor, ajusta los valores.")

st.markdown("### Contenido de Humedad y Cenizas (Base 'Tal como se Recibe')")

col_moisture, col_ash = st.columns(2)
with col_moisture:
    biomass_moisture = st.number_input(
        "Humedad de la Biomasa [%]:",
        min_value=0.0,
        max_value=60.0,
        value=10.0,
        step=0.5,
        format="%.1f",
        help="Contenido de humedad de la biomasa 'tal como se recibe'."
    ) / 100.0
with col_ash:
    biomass_ash = st.number_input(
        "Cenizas (Ash) [%]:",
        min_value=0.0,
        max_value=20.0,
        value=1.0,
        step=0.1,
        format="%.1f",
        help="Porcentaje de material incombustible en la biomasa 'tal como se recibe'."
    ) / 100.0

carbon_conversion_efficiency = st.number_input(
    "Eficiencia de Conversión de Carbono (CCE) [%]:",
    min_value=70.0,
    max_value=99.0,
    value=95.0,
    step=0.5,
    format="%.1f",
    help="Porcentaje del carbono de la biomasa que se convierte en gases (CO, CO2, CH4)."
) / 100.0

biomass_energy = st.number_input(
    "Poder Calorífico Biomasa (MJ/kg, base seca):",
    min_value=15.0,
    max_value=25.0,
    value=18.0,
    step=0.5,
    format="%.1f",
    help="Energía contenida por unidad de masa de biomasa (PCI), base seca."
)

st.subheader("Parámetros del Gasificador")
gasification_temp = st.number_input(
    "Temperatura de Gasificación (°C):",
    min_value=600,
    max_value=1200,
    value=800,
    step=10,
    help="Temperatura operativa en la zona de reacción del gasificador."
)
gasification_pressure = st.number_input(
    "Presión de Gasificación (bar):",
    min_value=1.0,
    max_value=10.0,
    value=1.0,
    step=0.1,
    format="%.1f",
    help="Presión operativa del gasificador (generalmente atmosférica o ligeramente superior)."
)

gasifying_agent = st.selectbox(
    "Agente Gasificante:",
    options=["Aire", "Vapor", "Oxígeno", "Mezcla Aire/Vapor"],
    index=0,
    help="Tipo de agente utilizado para la gasificación."
)

er_ratio = 0.0
steam_biomass_ratio = 0.0
oxygen_biomass_ratio = 0.0

if gasifying_agent == "Aire":
    er_ratio = st.slider(
        "Relación de Equivalencia (ER):",
        min_value=0.1,
        max_value=0.5,
        value=0.25,
        step=0.01,
        format="%.2f",
        help="Ratio de oxígeno real sobre el oxígeno estequiométrico para combustión completa. Un ER bajo (<1) indica gasificación."
    )
elif gasifying_agent == "Vapor":
    steam_biomass_ratio = st.slider(
        "Relación Vapor/Biomasa (SBR, kg vapor/kg biomasa):",
        min_value=0.1,
        max_value=1.0,
        value=0.5,
        step=0.05,
        format="%.2f",
        help="Ratio de masa de vapor sobre masa de biomasa alimentada."
    )
elif gasifying_agent == "Oxígeno":
    oxygen_biomass_ratio = st.slider(
        "Relación Oxígeno/Biomasa (OBR, kg O2/kg biomasa):",
        min_value=0.1,
        max_value=0.6,
        value=0.3,
        step=0.01,
        format="%.2f",
        help="Ratio de masa de oxígeno puro sobre masa de biomasa alimentada."
    )
elif gasifying_agent == "Mezcla Aire/Vapor":
    er_ratio = st.slider(
        "Relación de Equivalencia (ER, para aire):",
        min_value=0.1,
        max_value=0.5,
        value=0.2,
        step=0.01,
        format="%.2f",
        help="Ratio de oxígeno de aire real sobre el oxígeno estequiométrico para combustión completa."
    )
    steam_biomass_ratio = st.slider(
        "Relación Vapor/Biomasa (SBR, kg vapor/kg biomasa):",
        min_value=0.1,
        max_value=1.0,
        value=0.3,
        step=0.05,
        format="%.2f",
        help="Ratio de masa de vapor sobre masa de biomasa alimentada."
    )

st.info("La eficiencia de gasificación y el PCI del syngas se calcularán automáticamente en este modelo detallado.")

st.subheader("Parámetros del Sistema de Conversión Eléctrica")
engine_efficiency = st.number_input(
    "Eficiencia Motor-Generador (%):",
    min_value=20.0,
    max_value=45.0,
    value=30.0,
    step=0.5,
    format="%.1f",
    help="Porcentaje de la energía del syngas convertida en electricidad."
) / 100.0

hours_operated = st.number_input(
    "Horas de Operación:",
    min_value=1,
    max_value=24,
    value=8,
    step=1,
    help="Número de horas que el sistema opera para el cálculo total."
)

st.markdown("---")

# --- Función Principal de Simulación de Gasificación ---
def simulate_gasification(biomass_flow, biomass_C, biomass_H, biomass_O, biomass_N, biomass_S,
                          biomass_ash, biomass_moisture, carbon_conversion_efficiency,
                          gasification_temp, gasification_pressure, gasifying_agent,
                          er_ratio, steam_biomass_ratio, oxygen_biomass_ratio):

    T_k = gasification_temp + 273.15
    P_atm = gasification_pressure / 1.01325 # Convertir bar a atm para Kp basados en presiones parciales

    # 1. Calcular Masas Netas de Biomasa (por kg de biomasa 'as received')
    biomass_dry = 1 - biomass_moisture
    biomass_daf = biomass_dry * (1 - biomass_ash)

    # Moles de elementos en 1 kg de biomasa 'as received' (base reactiva)
    moles_C_biomass_in = (biomass_flow * biomass_daf * biomass_C) / MW_C
    moles_H_biomass_in = (biomass_flow * biomass_daf * biomass_H) / MW_H
    moles_O_biomass_in = (biomass_flow * biomass_daf * biomass_O) / MW_O
    moles_N_biomass_in = (biomass_flow * biomass_daf * biomass_N) / MW_N

    # Moles de H y O de la humedad
    moles_H2O_moisture_in = (biomass_flow * biomass_moisture) / MW_H2O
    
    # 2. Calcular Agente Gasificante
    moles_O2_agent_in = 0
    moles_N2_agent_in = 0
    moles_H2O_agent_in = 0

    if gasifying_agent == "Aire" or gasifying_agent == "Mezcla Aire/Vapor":
        O2_stoich_moles_per_kg_DAF = (biomass_C / MW_C) + (biomass_H / (4 * MW_H)) - (biomass_O / (2 * MW_O))
        moles_O2_agent_in = biomass_flow * biomass_daf * O2_stoich_moles_per_kg_DAF * er_ratio
        moles_N2_agent_in = moles_O2_agent_in / (0.21 / 0.79)
        
    if gasifying_agent == "Vapor" or gasifying_agent == "Mezcla Aire/Vapor":
        moles_H2O_agent_in = (biomass_flow * steam_biomass_ratio) / MW_H2O
    
    if gasifying_agent == "Oxígeno":
        moles_O2_agent_in = (biomass_flow * oxygen_biomass_ratio) / MW_O2

    # 3. Balance Total de Átomos de Entrada (por hora)
    total_moles_C_in = moles_C_biomass_in
    total_moles_H_in = moles_H_biomass_in + (moles_H2O_moisture_in * 2) + (moles_H2O_agent_in * 2)
    total_moles_O_in = moles_O_biomass_in + (moles_H2O_moisture_in * 1) + (moles_H2O_agent_in * 1) + (moles_O2_agent_in * 2)
    total_moles_N_in = moles_N_biomass_in + (moles_N2_agent_in * 2)

    # Moles de C no convertido (char)
    moles_C_unconverted = total_moles_C_in * (1 - carbon_conversion_efficiency)
    moles_C_converted = total_moles_C_in * carbon_conversion_efficiency

    # Moles de N2 en syngas (todo el N sale como N2)
    moles_N2_out = total_moles_N_in / 2

    # Ahora definimos las ecuaciones para el solver
    # Incógnitas: moles_H2, moles_CO, moles_CO2, moles_CH4, moles_H2O (salida por hora)
    # n[0]=H2, n[1]=CO, n[2]=CO2, n[3]=CH4, n[4]=H2O

    def equations(n, total_moles_C_in, total_moles_H_in, total_moles_O_in,
                  moles_C_unconverted, moles_N2_out, T_k, P_atm):
        
        n_H2, n_CO, n_CO2, n_CH4, n_H2O = n
        
        # Asegurarse de que las moles no sean negativas para el cálculo de fracciones
        # fsolve puede dar valores negativos, pero para los cálculos de Kp necesitamos positivos.
        epsilon = 1e-9
        n_H2_pos = max(epsilon, n_H2)
        n_CO_pos = max(epsilon, n_CO)
        n_CO2_pos = max(epsilon, n_CO2)
        n_CH4_pos = max(epsilon, n_CH4)
        n_H2O_pos = max(epsilon, n_H2O)

        # Moles totales de gases para fracciones molares
        total_moles_gases = n_H2_pos + n_CO_pos + n_CO2_pos + n_CH4_pos + n_H2O_pos + moles_N2_out
        
        # Fracciones molares
        X_H2 = n_H2_pos / total_moles_gases
        X_CO = n_CO_pos / total_moles_gases
        X_CO2 = n_CO2_pos / total_moles_gases
        X_CH4 = n_CH4_pos / total_moles_gases
        X_H2O = n_H2O_pos / total_moles_gases

        # Constantes de equilibrio a la temperatura de gasificación
        Kp_wgsr = calculate_k_wgsr(T_k)
        Kp_boudouard = calculate_k_boudouard(T_k)
        Kp_methanation = calculate_k_methanation(T_k)
        
        # Ecuaciones del sistema:
        # 1. Balance de Carbono (C)
        eq_C = (n_CO + n_CO2 + n_CH4) - (total_moles_C_in - moles_C_unconverted)

        # 2. Balance de Hidrógeno (H)
        eq_H = (2 * n_H2 + 4 * n_CH4 + 2 * n_H2O) - total_moles_H_in

        # 3. Balance de Oxígeno (O)
        eq_O = (n_CO + 2 * n_CO2 + n_H2O) - total_moles_O_in

        # 4. Equilibrio de WGSR: CO + H2O <=> CO2 + H2
        # Kp_wgsr = (X_CO2 * X_H2) / (X_CO * X_H2O)
        eq_wgsr = (X_CO2 * X_H2) - (Kp_wgsr * X_CO * X_H2O)

        # 5. Equilibrio de Metanación: CO + 3H2 <=> CH4 + H2O
        # Kp_methanation = (X_CH4 * X_H2O) / (X_CO * X_H2^3) * (1/P_total^2) si Kp usa presiones parciales
        # Si Kp está dado para fracciones molares, entonces es directo. Si está para presiones parciales,
        # Kp_molar_frac = Kp_pressure / (P_total^(delta_n_gas))
        # Para CO + 3H2 <=> CH4 + H2O, delta_n_gas = (1+1) - (1+3) = 2 - 4 = -2
        # Kp_molar_frac = Kp_pressure * P_total^2
        # Ajustamos el término de presión total en la ecuación de equilibrio si Kp es de presiones parciales.
        # Asumiendo que calculate_k_methanation devuelve Kp basado en presiones parciales en atm.
        eq_methanation = (X_CH4 * X_H2O) - (Kp_methanation * X_CO * (X_H2**3) * (P_atm**(-2))) # P_atm^-2 porque delta_n = -2

        return [eq_C, eq_H, eq_O, eq_wgsr, eq_methanation]

    # Valores iniciales para el solver (aproximación, pueden ser refinados)
    # Deben ser moles, no fracciones.
    # Intentamos con valores razonables de moles de salida para una primera aproximación.
    # La suma de estos moles debe ser consistente con la escala de moles_C_converted
    initial_guess_moles = np.array([0.1, 0.2, 0.1, 0.05, 0.1]) * moles_C_converted * 5 # Multiplicador heurístico para escalar

    # Resolver el sistema de ecuaciones
    try:
        sol = fsolve(equations, initial_guess_moles, args=(total_moles_C_in, total_moles_H_in, total_moles_O_in,
                                                       moles_C_unconverted, moles_N2_out, T_k, P_atm))
        
        moles_H2_out, moles_CO_out, moles_CO2_out, moles_CH4_out, moles_H2O_out = sol
        
        # Asegurarse de que ninguna mol sea negativa después del solver
        moles_H2_out = max(0, moles_H2_out)
        moles_CO_out = max(0, moles_CO_out)
        moles_CO2_out = max(0, moles_CO2_out)
        moles_CH4_out = max(0, moles_CH4_out)
        moles_H2O_out = max(0, moles_H2O_out)

    except Exception as e:
        st.error(f"Error al resolver el sistema de ecuaciones: {e}. Intente ajustar los parámetros.")
        return {}, 0, 0

    total_moles_syngas = moles_H2_out + moles_CO_out + moles_CO2_out + moles_CH4_out + moles_H2O_out + moles_N2_out
    
    if total_moles_syngas == 0:
        syngas_composition = {'H2': 0, 'CO': 0, 'CO2': 0, 'CH4': 0, 'N2': 0, 'H2O': 0}
        syngas_calorific_value = 0
        volume_syngas_produced = 0
    else:
        syngas_composition = {
            'H2': moles_H2_out / total_moles_syngas,
            'CO': moles_CO_out / total_moles_syngas,
            'CO2': moles_CO2_out / total_moles_syngas,
            'CH4': moles_CH4_out / total_moles_syngas,
            'N2': moles_N2_out / total_moles_syngas,
            'H2O': moles_H2O_out / total_moles_syngas
        }
        
        syngas_calorific_value = (syngas_composition['H2'] * PCI_H2_Nm3 +
                                  syngas_composition['CO'] * PCI_CO_Nm3 +
                                  syngas_composition['CH4'] * PCI_CH4_Nm3)
        
        volume_syngas_produced = total_moles_syngas * MOLAR_VOLUME_NTP

    return syngas_composition, syngas_calorific_value, volume_syngas_produced

# --- Realizar los cálculos de la simulación ---
# Llamar a la función de gasificación
syngas_composition, syngas_calorific_value_calc, volume_syngas_produced_calc = simulate_gasification(
    biomass_flow, biomass_C, biomass_H, biomass_O, biomass_N, biomass_S,
    biomass_ash, biomass_moisture, carbon_conversion_efficiency,
    gasification_temp, gasification_pressure, gasifying_agent,
    er_ratio, steam_biomass_ratio, oxygen_biomass_ratio
)

total_biomass_consumed = biomass_flow * hours_operated
total_biomass_energy = total_biomass_consumed * biomass_energy

energy_in_syngas = volume_syngas_produced_calc * syngas_calorific_value_calc * hours_operated

gasification_efficiency_calc = energy_in_syngas / total_biomass_energy if total_biomass_energy > 0 else 0

electric_energy_generated_mj = energy_in_syngas * engine_efficiency
electric_energy_generated_kwh = electric_energy_generated_mj * 0.2778

average_power_output = electric_energy_generated_kwh / hours_operated if hours_operated > 0 else 0

# Para el CO2 producido, necesitamos las moles totales de CO y CH4 que salieron del solver
# Si syngas_composition está vacío (por un error en el solver), estas serán 0.
moles_CO_out_total_hr = syngas_composition.get('CO', 0) * (volume_syngas_produced_calc / MOLAR_VOLUME_NTP)
moles_CH4_out_total_hr = syngas_composition.get('CH4', 0) * (volume_syngas_produced_calc / MOLAR_VOLUME_NTP)

moles_co2_produced_from_syngas = (moles_CO_out_total_hr + moles_CH4_out_total_hr) * hours_operated
mass_co2_produced = moles_co2_produced_from_syngas * MW_CO2


# --- Mostrar los resultados calculados ---
st.markdown(f"""
    <div class="results-container">
        <p class="results-p"><span class="results-label">Biomasa Consumida (total):</span> <span class="results-value">{total_biomass_consumed:.2f} kg</span></p>
        <p class="results-p"><span class="results-label">Energía Total de Biomasa:</span> <span class="results-value">{total_biomass_energy:.2f} MJ</span></p>
        <p class="results-p"><span class="results-label">**Eficiencia de Gasificación (calculada):**</span> <span class="results-value">{gasification_efficiency_calc:.2%}</span></p>
        <p class="results-p"><span class="results-label">Energía en Syngas Producido:</span> <span class="results-value">{energy_in_syngas:.2f} MJ</span></p>
        <p class="results-p"><span class="results-label">Volumen de Syngas Producido:</span> <span class="results-value">{volume_syngas_produced_calc * hours_operated:.2f} Nm³</span></p>
        <p class="results-p"><span class="results-label">**Poder Calorífico Syngas (calculado):**</span> <span class="results-value">{syngas_calorific_value_calc:.2f} MJ/Nm³</span></p>
        <p class="results-p"><span class="results-label">Energía Eléctrica Generada:</span> <span class="results-value">{electric_energy_generated_mj:.2f} MJ</span></p>
        <p class="results-p"><span class="results-label">Electricidad Generada:</span> <span class="results-value">{electric_energy_generated_kwh:.2f} kWh</span></p>
        <p class="results-p"><span class="results-label">Potencia Eléctrica Promedio:</span> <span class="results-value">{average_power_output:.2f} kW</span></p>
        <p class="results-p"><span class="results-label">CO2 Producido (combustión):</span> <span class="results-value">{mass_co2_produced:.2f} kg</span></p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Mostrar Composición del Syngas ---
st.markdown("### Composición del Syngas (calculada)")
if syngas_composition:
    syngas_df = pd.DataFrame(syngas_composition.items(), columns=['Componente', 'Fracción Molar'])
    syngas_df['Fracción Molar (%)'] = syngas_df['Fracción Molar'] * 100
    st.dataframe(syngas_df.style.format({'Fracción Molar': "{:.4f}", 'Fracción Molar (%)': "{:.2f}%"}), hide_index=True)
else:
    st.write("No se pudo calcular la composición del syngas. Verifique los parámetros de entrada o contacte al soporte si el error persiste.")


st.markdown("---")

## 💡 Ecuaciones utilizadas

with st.expander("Ecuaciones utilizadas"):
    st.markdown("""
    Aquí se detallan las ecuaciones principales utilizadas para los cálculos de la simulación. El modelo de gasificación se basa en un enfoque de **equilibrio termodinámico**, donde se asume que las principales reacciones químicas alcanzan el equilibrio a la temperatura de gasificación.
    """)

    st.subheader("1. Balances de Masa Atómicos")
    st.markdown("""
    Los balances de masa se realizan para cada elemento (C, H, O, N) desde la biomasa y el agente gasificante hacia los productos del syngas y el carbono no convertido. Estos balances deben cumplirse estrictamente.
    """)
    st.latex(r'''
        C_{\text{in}} = C_{\text{Syngas}} + C_{\text{no convertido}}
    ''')
    st.latex(r'''
        H_{\text{in}} = H_{\text{Syngas}}
    ''')
    st.latex(r'''
        O_{\text{in}} = O_{\text{Syngas}}
    ''')
    st.latex(r'''
        N_{\text{in}} = N_{\text{Syngas}}
    ''')
    st.markdown("""
    Donde:
    * $C_{\text{in}}$, $H_{\text{in}}$, $O_{\text{in}}$, $N_{\text{in}}$ son los moles totales de cada átomo que entran al gasificador (desde la biomasa seca, libre de cenizas, humedad y agente gasificante).
    * $C_{\text{Syngas}}$, $H_{\text{Syngas}}$, $O_{\text{Syngas}}$, $N_{\text{Syngas}}$ son los moles de cada átomo en los componentes gaseosos del syngas (CO, CO$_2$, CH$_4$, H$_2$, H$_2$O, N$_2$).
    * $C_{\text{no convertido}}$ es el carbono que no reacciona y sale como char/coque, determinado por la Eficiencia de Conversión de Carbono (CCE) ingresada.
    """)

    st.subheader("2. Reacciones de Equilibrio y sus Constantes ($K_p$)")
    st.markdown("El modelo considera las siguientes reacciones químicas en equilibrio a la temperatura y presión de gasificación. Las constantes de equilibrio ($K_p$) se calculan a partir de la energía libre de Gibbs de la reacción ($\Delta G^\circ = \Delta H^\circ - T\Delta S^\circ$) mediante la relación $K_p = e^{-\Delta G^\circ / (R T)}$. Aquí, se utilizan correlaciones aproximadas para $\Delta G^\circ$ en función de la temperatura ($T_k$ en Kelvin):")

    st.markdown("#### a) Reacción de Desplazamiento de Gas de Agua (WGSR)")
    st.latex(r'''
        \text{CO} + \text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + \text{H}_2
    ''')
    st.markdown("La constante de equilibrio $K_p$ para esta reacción se calcula como:")
    st.latex(r'''
        \ln K_p = -2.2562 + \frac{1829.0}{T_k} + 0.3546 \ln T_k - (1.189 \times 10^{-4} T_k) + (1.936 \times 10^{-8} T_k^2)
    ''')
    st.markdown("Fuente: Journal of Environmental Chemical Engineering 8 (2020) 103755.")

    st.markdown("#### b) Reacción de Boudouard")
    st.latex(r'''
        \text{C} + \text{CO}_2 \rightleftharpoons 2\text{CO}
    ''')
    st.markdown("La constante de equilibrio $K_p$ para esta reacción se calcula a partir de $\Delta G^\circ = 171000 - 175.7 \cdot T_k$ (en J/mol):")
    st.latex(r'''
        K_p = \exp\left(-\frac{171000 - 175.7 \cdot T_k}{R \cdot T_k}\right)
    ''')
    st.markdown("Donde $R$ es la constante universal de los gases ideales (8.314 J/(mol·K)). Esta reacción es fundamental para la formación de CO a partir de $\text{CO}_2$ y carbono sólido (coque/char).")

    st.markdown("#### c) Reacción de Metanación")
    st.latex(r'''
        \text{CO} + 3\text{H}_2 \rightleftharpoons \text{CH}_4 + \text{H}_2\text{O}
    ''')
    st.markdown("La constante de equilibrio $K_p$ para esta reacción se calcula a partir de $\Delta G^\circ = -215930 + 0.233 \cdot T_k$ (en J/mol):")
    st.latex(r'''
        K_p = \exp\left(-\frac{-215930 + 0.233 \cdot T_k}{R \cdot T_k}\right)
    ''')
    st.markdown("Esta reacción describe la formación de metano en el syngas.")

    st.markdown("Las expresiones de $K_p$ en términos de fracciones molares ($X_i$) y presión total ($P_{\text{total}}$) son:")
    st.latex(r'''
        K_{p, \text{WGSR}} = \frac{X_{\text{CO}_2} \cdot X_{\text{H}_2}}{X_{\text{CO}} \cdot X_{\text{H}_2\text{O}}}
    ''')
    st.latex(r'''
        K_{p, \text{Boudouard}} = \frac{X_{\text{CO}}^2}{X_{\text{CO}_2}} \cdot \frac{P_{\text{total}}}{P_0} \quad \text{ (donde } P_0 \text{ es la presión de referencia, 1 atm o bar)}
    ''')
    st.latex(r'''
        K_{p, \text{Metanación}} = \frac{X_{\text{CH}_4} \cdot X_{\text{H}_2\text{O}}}{X_{\text{CO}} \cdot X_{\text{H}_2}^3} \cdot \left(\frac{P_0}{P_{\text{total}}}\right)^2
    ''')
    st.markdown("Estas ecuaciones de equilibrio, junto con los balances de masa atómicos, forman un sistema de ecuaciones no lineales que se resuelve numéricamente para encontrar las moles de cada componente del syngas.")

    st.subheader("3. Cálculo de Fracciones Molares del Syngas")
    st.markdown("""
    Una vez que se han determinado las moles de cada componente gaseoso en el syngas ($n_{\text{H}_2}, n_{\text{CO}}, n_{\text{CO}_2}, n_{\text{CH}_4}, n_{\text{N}_2}, n_{\text{H}_2\text{O}}$), se calcula la fracción molar ($X_i$) de cada componente dividiendo sus moles por las moles totales del syngas:
    """)
    st.latex(r'''
        X_i = \frac{n_i}{n_{\text{Syngas, total}}}
    ''')
    st.markdown("""
    Donde:
    * $n_i$ es la cantidad de moles del componente $i$ en el syngas.
    * $n_{\text{Syngas, total}}$ es la suma de las moles de todos los componentes gaseosos presentes en el syngas.
    """)

    st.subheader("4. Poder Calorífico Inferior (PCI) del Syngas")
    st.markdown("""
    El PCI del syngas se calcula a partir de la composición molar predicha y los valores de PCI de sus componentes combustibles, a condiciones normales (0°C y 1 atm):
    """)
    st.latex(r'''
        \text{PCI}_{\text{Syngas}} = \sum_{i} (X_i \times \text{PCI}_{i, \text{Nm}^3})
    ''')
    st.markdown("""
    Donde $X_i$ es la fracción molar del componente combustible $i$ ($\text{H}_2, \text{CO}, \text{CH}_4$) y $\text{PCI}_{i, \text{Nm}^3}$ es el Poder Calorífico Inferior de ese componente por unidad de volumen.
    
    Los valores de PCI utilizados son:
    * **Hidrógeno ($\text{H}_2$):** 10.79 MJ/Nm³
    * **Monóxido de Carbono ($\text{CO}$):** 12.63 MJ/Nm³
    * **Metano ($\text{CH}_4$):** 35.80 MJ/Nm³
    """)

    st.subheader("5. Balance de Energía General")
    st.latex(r'''
        H_{\text{Biomasa}} = F_{\text{Biomasa}} \times \text{PCI}_{\text{Biomasa, seca}} \times t_{\text{operación}}
    ''')
    st.markdown("""
    Donde:
    * $H_{\text{Biomasa}}$ es la energía total disponible en la biomasa (MJ).
    * $F_{\text{Biomasa}}$ es el flujo de biomasa (kg/h).
    * $\text{PCI}_{\text{Biomasa, seca}}$ es el Poder Calorífico Inferior de la biomasa en base seca (MJ/kg).
    * $t_{\text{operación}}$ son las horas de operación (h).
    """)

    st.subheader("6. Eficiencia de Gasificación")
    st.latex(r'''
        \eta_{\text{gasificación}} = \frac{V_{\text{Syngas, total}} \times \text{PCI}_{\text{Syngas}}}{H_{\text{Biomasa}}}
    ''')
    st.markdown("""
    Donde $V_{\text{Syngas, total}}$ es el volumen total de syngas producido durante el periodo de operación ($\text{Nm}^3$).
    """)

    st.subheader("7. Energía Eléctrica Generada")
    st.latex(r'''
        E_{\text{eléctrica}} = H_{\text{Syngas}} \times \eta_{\text{motor-generador}}
    ''')
    st.markdown("""
    Donde:
    * $E_{\text{eléctrica}}$ es la energía eléctrica generada (MJ).
    * $H_{\text{Syngas}}$ es la energía total contenida en el syngas producido (MJ).
    * $\eta_{\text{motor-generador}}$ es la eficiencia del motor-generador (adimensional).
    """)

    st.latex(r'''
        E_{\text{eléctrica, kWh}} = E_{\text{eléctrica, MJ}} \times 0.2778 \frac{\text{kWh}}{\text{MJ}}
    ''')
    st.markdown("""
    Donde:
    * $E_{\text{eléctrica, kWh}}$ es la energía eléctrica en kilovatios-hora (kWh).
    """)

    st.subheader("8. Potencia Eléctrica Promedio")
    st.latex(r'''
        P_{\text{promedio}} = \frac{E_{\text{eléctrica, kWh}}}{t_{\text{operación}}}
    ''')
    st.markdown("""
    Donde:
    * $P_{\text{promedio}}$ es la potencia eléctrica promedio (kW).
    """)

    st.subheader("9. Emisiones de $\\text{CO}_2$ (basado en combustión de Syngas)")
    st.markdown("Las emisiones de $\\text{CO}_2$ se calculan a partir de la combustión completa del $\\text{CO}$ y $\\text{CH}_4$ presentes en el syngas. Las reacciones estequiométricas son:")
    st.latex(r'''
        \text{CO} + \frac{1}{2} \text{O}_2 \rightarrow \text{CO}_2
    ''')
    st.latex(r'''
        \text{CH}_4 + 2 \text{O}_2 \rightarrow \text{CO}_2 + 2 \text{H}_2\text{O}
    ''')
    st.markdown("Basado en estas reacciones, 1 mol de $\\text{CO}$ produce 1 mol de $\\text{CO}_2$, y 1 mol de $\\text{CH}_4$ también produce 1 mol de $\\text{CO}_2$.")
    st.latex(r'''
        \text{moles}_{\text{CO}_2, \text{total}} = (\text{moles}_{\text{CO}} + \text{moles}_{\text{CH}_4})_{\text{Syngas}}
    ''')
    st.latex(r'''
        \text{Masa}_{\text{CO}_2} = \text{moles}_{\text{CO}_2, \text{total}} \times \text{Masa Molar}_{\text{CO}_2}
    ''')
    st.markdown("""
    Donde:
    * $\text{moles}_{\text{CO}}$ y $\text{moles}_{\text{CH}_4}$ son los moles totales de CO y CH$_4$ generados en el syngas durante la operación.
    * $\text{Masa Molar}_{\text{CO}_2}$ es la masa molar del dióxido de carbono (44 kg/kmol).
    * Estas ecuaciones asumen que todo el CO y CH$_4$ en el syngas se convierten completamente en CO$_2$ durante la combustión.
    """)
