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

def calculate_k_boudouard(T_k, P_atm):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de Boudouard.
    C + CO2 <=> 2CO
    Kp = (P_CO^2) / (P_CO2 * a_C)
    Asumiendo a_C = 1 si C está presente.
    Kp = (X_CO^2 / X_CO2) * (P_total / P_ref)
    Donde P_ref = 1 atm.
    Fuente: Adaptado de varias fuentes, basado en delta G.
    delta_g = 171000 - 175.7 * T_k # J/mol
    kp_pressure_basis = np.exp(-delta_g / (R_UNIVERSAL * T_k))
    # Ajuste por presion: Kp_X = Kp_P * (P_total/P_ref)^(-delta_n_gas)
    # delta_n_gas = 2 - 1 = 1
    # Entonces, Kp_X = Kp_P * (P_total/P_ref)^(-1) = Kp_P * (P_ref/P_total)
    P_ref = 1.0 # atm, ya que P_atm está en atm
    return kp_pressure_basis * (P_ref / P_atm)


def calculate_k_methanation_co(T_k, P_atm):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de Metanación desde CO.
    # CO + 3H2 <=> CH4 + H2O # Esta línea fue comentada
    Kp = (P_CH4 * P_H2O) / (P_CO * P_H2^3)
    Kp = (X_CH4 * X_H2O) / (X_CO * X_H2^3) * (P_ref / P_total)^2
    Fuente: Adaptado de varias fuentes, basado en delta G.
    """
    delta_g = -215930 + 0.233 * T_k # J/mol
    kp_pressure_basis = np.exp(-delta_g / (R_UNIVERSAL * T_k))
    # Ajuste por presion: Kp_X = Kp_P * (P_total/P_ref)^(-delta_n_gas)
    # delta_n_gas = (1+1) - (1+3) = -2
    # Entonces, Kp_X = Kp_P * (P_total/P_ref)^(-(-2)) = Kp_P * (P_total/P_ref)^2
    P_ref = 1.0 # atm
    return kp_pressure_basis * (P_atm / P_ref)**2

def calculate_k_c_h2o(T_k, P_atm):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de Gas de Agua (Carbono-Vapor).
    C + H2O <=> CO + H2
    Kp = (P_CO * P_H2) / (P_H2O * a_C)
    Asumiendo a_C = 1 si C está presente.
    Kp = (X_CO * X_H2) / (X_H2O) * (P_total / P_ref)^0 = (X_CO * X_H2) / (X_H2O)
    delta_n_gas = (1+1) - 1 = 1.  (Esta es la que tiene la Kp en fracciones molares dependiente de la presión)
    Fuente: Delta G = 131340 - 134.1 * T_k (J/mol)
    """
    delta_g = 131340 - 134.1 * T_k # J/mol
    kp_pressure_basis = np.exp(-delta_g / (R_UNIVERSAL * T_k))
    # Ajuste por presion: delta_n_gas = (1+1) - 1 = 1
    # Kp_X = Kp_P * (P_total/P_ref)^(-1) = Kp_P * (P_ref/P_total)
    P_ref = 1.0 # atm
    return kp_pressure_basis * (P_ref / P_atm)

def calculate_k_c_ch4(T_k, P_atm):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de Metanación Directa (Carbono-Hidrógeno).
    C + 2H2 <=> CH4
    Kp = P_CH4 / P_H2^2 * a_C
    Asumiendo a_C = 1 si C está presente.
    Kp = X_CH4 / X_H2^2 * (P_ref / P_total)^(-1) = X_CH4 / X_H2^2 * (P_total / P_ref)
    delta_n_gas = 1 - 2 = -1.
    Fuente: Delta G = -74850 - 12.08 * T_k (J/mol)
    """
    delta_g = -74850 - 12.08 * T_k # J/mol
    kp_pressure_basis = np.exp(-delta_g / (R_UNIVERSAL * T_k))
    # Ajuste por presion: delta_n_gas = 1 - 2 = -1
    # Kp_X = Kp_P * (P_total/P_ref)^(-(-1)) = Kp_P * (P_total/P_ref)
    P_ref = 1.0 # atm
    return kp_pressure_basis * (P_atm / P_ref)


# --- Título y Descripción ---
st.markdown(f"""
    <style>
    .big-title {{
        font-size: "2.5rem";
        color: #1a202c;
        text-align: center;
        margin-bottom: "20px"; /* Corregido: "20px" entre comillas */
        font-weight: 700;
    }}
    .note {{
        font-size: 0.95em;
        color: #666;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 30px;
    }}
    .results-container {{
        padding: 25px;
        background-color: #e6fffa;
        border: 1px solid #81e6d9;
        border-radius: 10px;
        font-size: 1.15em;
        line-height: 1.6;
        margin-top: 30px;
    }}
    .results-p {{
        margin: 10px 0;
        display: flex;
        align-items: center;
        padding-bottom: 5px;
        border-bottom: 1px dashed #b2f5ea;
    }}
    .results-p:last-child {{
        border-bottom: none;
    }}
    .results-label {{
        flex: 1;
        text-align: left;
        padding-right: 15px;
        min-width: 180px;
    }}
    .results-value {{
        font-weight: 700;
        color: #38b2ac;
        font-size: 1.2em;
        text-align: right;
        min-width: 120px;
    }}
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

# --- CCE ELIMINADO COMO ENTRADA ---
st.info("La Eficiencia de Conversión de Carbono (CCE) ahora se calcula como un resultado del equilibrio termodinámico.")


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
                          biomass_ash, biomass_moisture,
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

    # Moles de N2 en syngas (todo el N sale como N2)
    moles_N2_out = total_moles_N_in / 2

    # Ahora definimos las ecuaciones para el solver
    # Incógnitas: n[0]=H2, n[1]=CO, n[2]=CO2, n[3]=CH4, n[4]=H2O, n[5]=C_unconverted (char)

    def equations(n, total_moles_C_in, total_moles_H_in, total_moles_O_in,
                  moles_N2_out, T_k, P_atm):
        
        n_H2, n_CO, n_CO2, n_CH4, n_H2O, n_C_unconverted = n
        
        # Asegurarse de que las moles no sean negativas para el cálculo de fracciones
        # fsolve puede dar valores negativos, pero para los cálculos de Kp necesitamos positivos.
        epsilon = 1e-12 # Un valor muy pequeño para evitar divisiones por cero o logaritmos de cero
        
        # Todas las moles deben ser no negativas
        n_H2_pos = max(epsilon, n_H2)
        n_CO_pos = max(epsilon, n_CO)
        n_CO2_pos = max(epsilon, n_CO2)
        n_CH4_pos = max(epsilon, n_CH4)
        n_H2O_pos = max(epsilon, n_H2O)
        n_C_unconverted_pos = max(epsilon, n_C_unconverted) # Moles de carbono no convertido deben ser >= 0

        # Moles totales de gases para fracciones molares (el char no se incluye en moles totales de GASES)
        total_moles_gases = n_H2_pos + n_CO_pos + n_CO2_pos + n_CH4_pos + n_H2O_pos + moles_N2_out
        
        # Fracciones molares (solo de los componentes gaseosos)
        X_H2 = n_H2_pos / total_moles_gases
        X_CO = n_CO_pos / total_moles_gases
        X_CO2 = n_CO2_pos / total_moles_gases
        X_CH4 = n_CH4_pos / total_moles_gases
        X_H2O = n_H2O_pos / total_moles_gases

        # Constantes de equilibrio a la temperatura de gasificación y presión
        Kp_wgsr = calculate_k_wgsr(T_k)
        Kp_boudouard = calculate_k_boudouard(T_k, P_atm)
        Kp_methanation_co = calculate_k_methanation_co(T_k, P_atm)
        # Kp_c_h2o = calculate_k_c_h2o(T_k, P_atm) # Ya no se usa directamente en fsolve, pero se mantiene la función
        # Kp_c_ch4 = calculate_k_c_ch4(T_k, P_atm) # Ya no se usa directamente en fsolve, pero se mantiene la función
        
        # Ecuaciones del sistema:
        # 1. Balance de Carbono (C)
        # El C de entrada debe ser igual al C en gases + C no convertido
        eq_C = (n_CO + n_CO2 + n_CH4 + n_C_unconverted) - total_moles_C_in

        # 2. Balance de Hidrógeno (H)
        eq_H = (2 * n_H2 + 4 * n_CH4 + 2 * n_H2O) - total_moles_H_in

        # 3. Balance de Oxígeno (O)
        eq_O = (n_CO + 2 * n_CO2 + n_H2O) - total_moles_O_in

        # 4. Equilibrio de WGSR: CO + H2O <=> CO2 + H2
        # Kp_wgsr = (X_CO2 * X_H2) / (X_CO * X_H2O)
        eq_wgsr = (X_CO2 * X_H2) - (Kp_wgsr * X_CO * X_H2O)

        # 5. Equilibrio de Metanación desde CO: CO + 3H2 <=> CH4 + H2O
        # Kp_methanation_co = (X_CH4 * X_H2O) / (X_CO * X_H2^3) * (P_total / P_ref)^2
        eq_methanation_co = (X_CH4 * X_H2O) - (Kp_methanation_co * X_CO * (X_H2**3))

        # 6. Equilibrio de Boudouard: C + CO2 <=> 2CO
        # Kp_boudouard = (X_CO^2) / X_CO2 * (P_total / P_ref) (Si C está presente, a_C = 1)
        # Este Kp_boudouard ya está ajustado para fracciones molares
        eq_boudouard = (X_CO**2) - (Kp_boudouard * X_CO2) # CORRECCIÓN AQUÍ: X_CO_pos -> X_CO, X_CO2_pos -> X_CO2
        
        # Las ecuaciones de equilibrio de C + H2O y C + CH4 no se incluyen directamente en el sistema de fsolve
        # para evitar un sistema sobre-determinado o problemas de convergencia al tratar
        # con la fase sólida explícitamente y mantener 6 ecuaciones para 6 incógnitas.
        # Su efecto se captura por los balances atómicos y las otras reacciones de equilibrio.

        return [
            eq_C,
            eq_H,
            eq_O,
            eq_wgsr,
            eq_methanation_co, # Metanación (CO + 3H2)
            eq_boudouard       # Boudouard (C + CO2)
        ]

    # Valores iniciales para el solver (aproximación, pueden ser refinados)
    # n[0]=H2, n[1]=CO, n[2]=CO2, n[3]=CH4, n[4]=H2O, n[5]=C_unconverted
    
    # Escalar los valores iniciales basados en el flujo de biomasa
    initial_guess_H2 = total_moles_H_in * 0.2
    initial_guess_CO = total_moles_C_in * 0.4
    initial_guess_CO2 = total_moles_C_in * 0.1
    initial_guess_CH4 = total_moles_C_in * 0.05
    initial_guess_H2O = total_moles_O_in * 0.1
    initial_guess_C_unconverted = total_moles_C_in * 0.1 # Asumir 10% de char inicial

    initial_guess_moles = np.array([
        initial_guess_H2,
        initial_guess_CO,
        initial_guess_CO2,
        initial_guess_CH4,
        initial_guess_H2O,
        initial_guess_C_unconverted
    ])

    # Asegurarse de que los valores iniciales no sean cero
    initial_guess_moles[initial_guess_moles <= 0] = 1e-6


    # Resolver el sistema de ecuaciones
    try:
        sol = fsolve(equations, initial_guess_moles, args=(total_moles_C_in, total_moles_H_in, total_moles_O_in,
                                                       moles_N2_out, T_k, P_atm))
        
        moles_H2_out, moles_CO_out, moles_CO2_out, moles_CH4_out, moles_H2O_out, moles_C_unconverted_out = sol
        
        # Asegurarse de que ninguna mol sea negativa después del solver
        moles_H2_out = max(0, moles_H2_out)
        moles_CO_out = max(0, moles_CO_out)
        moles_CO2_out = max(0, moles_CO2_out)
        moles_CH4_out = max(0, moles_CH4_out)
        moles_H2O_out = max(0, moles_H2O_out)
        moles_C_unconverted_out = max(0, moles_C_unconverted_out) # Char no puede ser negativo

    except Exception as e:
        st.error(f"Error al resolver el sistema de ecuaciones: {e}. Intente ajustar los parámetros.")
        return {}, 0, 0, 0, 0 # Añadir 0 para CCE_calc y moles_C_unconverted_out si hay error

    total_moles_syngas_dry = moles_H2_out + moles_CO_out + moles_CO2_out + moles_CH4_out + moles_N2_out

    if total_moles_syngas_dry == 0: # Si no se produjo syngas seco
        syngas_composition = {'H2': 0, 'CO': 0, 'CO2': 0, 'CH4': 0, 'N2': 0, 'H2O': 0}
        syngas_calorific_value = 0
        volume_syngas_produced = 0
        carbon_conversion_efficiency_calc = 0
    else:
        # Composicion del syngas SECO (sin H2O, que a menudo se condensa)
        syngas_composition_dry = {
            'H2': moles_H2_out / total_moles_syngas_dry,
            'CO': moles_CO_out / total_moles_syngas_dry,
            'CO2': moles_CO2_out / total_moles_syngas_dry,
            'CH4': moles_CH4_out / total_moles_syngas_dry,
            'N2': moles_N2_out / total_moles_syngas_dry
        }
        
        syngas_calorific_value = (syngas_composition_dry['H2'] * PCI_H2_Nm3 +
                                  syngas_composition_dry['CO'] * PCI_CO_Nm3 +
                                  syngas_composition_dry['CH4'] * PCI_CH4_Nm3)
        
        # Volumen total de syngas (húmedo)
        total_moles_syngas_wet = total_moles_syngas_dry + moles_H2O_out
        volume_syngas_produced = total_moles_syngas_wet * MOLAR_VOLUME_NTP

        # Calcular el CCE como salida
        carbon_in_syngas = moles_CO_out + moles_CO2_out + moles_CH4_out
        
        # Asegurarse de no dividir por cero
        if total_moles_C_in > 0:
            carbon_conversion_efficiency_calc = carbon_in_syngas / total_moles_C_in
        else:
            carbon_conversion_efficiency_calc = 0

        # Para la tabla de composicion, mostrar todo incluyendo H2O
        syngas_composition = {
            'H2': moles_H2_out / total_moles_syngas_wet,
            'CO': moles_CO_out / total_moles_syngas_wet,
            'CO2': moles_CO2_out / total_moles_syngas_wet,
            'CH4': moles_CH4_out / total_moles_syngas_wet,
            'N2': moles_N2_out / total_moles_syngas_wet,
            'H2O': moles_H2O_out / total_moles_syngas_wet
        }


    return syngas_composition, syngas_calorific_value, volume_syngas_produced, carbon_conversion_efficiency_calc, moles_C_unconverted_out

# --- Realizar los cálculos de la simulación ---
# Llamar a la función de gasificación
syngas_composition, syngas_calorific_value_calc, volume_syngas_produced_calc, carbon_conversion_efficiency_calc, moles_C_unconverted_out =
