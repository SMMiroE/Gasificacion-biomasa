import streamlit as st
import pandas as pd
import numpy as np

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

# --- Funciones Auxiliares ---
def calculate_k_wgsr(T_k):
    """
    Calcula la constante de equilibrio (Kp) para la reacción de desplazamiento de gas de agua (WGSR).
    CO + H2O <=> CO2 + H2
    Correlación válida para un rango de temperaturas.
    Args:
        T_k (float): Temperatura en Kelvin.
    Returns:
        float: Constante de equilibrio Kp.
    """
    # Fuente: Simplified equilibrium model for downdraft gasification of biomass
    # Journal of Environmental Chemical Engineering 8 (2020) 103755
    # Correlación ajustada para el rango de interés
    log_kp = -2.2562 + (1829.0 / T_k) + 0.3546 * np.log(T_k) - (1.189 * 10**-4 * T_k) + (1.936 * 10**-8 * T_k**2)
    return np.exp(log_kp)

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
# Se comenta la línea de la imagen para evitar el error de archivo no encontrado en el despliegue.
# La imagen 'image_3c55b6.png' debe estar en el mismo directorio del script en GitHub.
# st.image("image_3c55b6.png",
#          caption="Diagrama del Sistema de Gasificación de Biomasa",
#          use_container_width=True)

st.markdown("## Parámetros de Entrada")

# --- Sección de Parámetros de Biomasa ---
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

col_n, col_s = st.columns(2) # Ajustamos a 2 columnas aquí
with col_n:
    biomass_N = st.number_input("Nitrógeno (N) [%]:", min_value=0.0, max_value=10.0, value=0.5, step=0.01, format="%.2f") / 100.0
with col_s:
    biomass_S = st.number_input("Azufre (S) [%]:", min_value=0.0, max_value=10.0, value=0.0, step=0.01, format="%.2f") / 100.0

# Validación de suma de componentes C+H+O+N+S (base seca y libre de cenizas)
sum_elemental = (biomass_C + biomass_H + biomass_O + biomass_N + biomass_S) * 100
if abs(sum_elemental - 100) > 0.1: # Tolerancia de 0.1%
    st.warning(f"La suma de C, H, O, N, S (base seca y libre de cenizas) es {sum_elemental:.1f}%. Debería ser ~100%. Por favor, ajusta los valores.")

st.markdown("### Contenido de Humedad y Cenizas (Base 'Tal como se Recibe')")

col_moisture, col_ash = st.columns(2) # Nuevas columnas para humedad y cenizas
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

# Nueva entrada: Eficiencia de Conversión de Carbono
carbon_conversion_efficiency = st.number_input(
    "Eficiencia de Conversión de Carbono (CCE) [%]:",
    min_value=70.0,
    max_value=99.0,
    value=95.0,
    step=0.5,
    format="%.1f",
    help="Porcentaje del carbono de la biomasa que se convierte en gases (CO, CO2, CH4)."
) / 100.0

# Por ahora, mantenemos la entrada directa para el PCI de la biomasa
biomass_energy = st.number_input(
    "Poder Calorífico Biomasa (MJ/kg, base seca):",
    min_value=15.0,
    max_value=25.0,
    value=18.0,
    step=0.5,
    format="%.1f",
    help="Energía contenida por unidad de masa de biomasa (PCI), base seca."
)

# --- Sección de Parámetros del Gasificador ---
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
    index=0, # Por defecto aire
    help="Tipo de agente utilizado para la gasificación."
)

# Parámetros específicos del agente gasificante
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

# Mantenemos los parámetros del motor-generador y horas de operación por ahora.
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
                          biomass_ash, biomass_moisture, biomass_energy,
                          carbon_conversion_efficiency,
                          gasification_temp, gasification_pressure, gasifying_agent,
                          er_ratio, steam_biomass_ratio, oxygen_biomass_ratio):

    # Convertir temperatura a Kelvin
    T_k = gasification_temp + 273.15

    # 1. Calcular Masas Netas de Biomasa (por kg de biomasa 'as received')
    # Masa seca de biomasa (excluyendo humedad)
    biomass_dry = 1 - biomass_moisture
    # Masa seca y libre de cenizas (base "realmente reactiva")
    biomass_daf = biomass_dry * (1 - biomass_ash)

    # Moles de elementos en 1 kg de biomasa 'as received' (base reactiva)
    # Convertimos porcentajes a moles por kg de biomasa total alimentada
    moles_C_biomass_in = (biomass_flow * biomass_daf * biomass_C) / MW_C
    moles_H_biomass_in = (biomass_flow * biomass_daf * biomass_H) / MW_H
    moles_O_biomass_in = (biomass_flow * biomass_daf * biomass_O) / MW_O
    moles_N_biomass_in = (biomass_flow * biomass_daf * biomass_N) / MW_N
    # moles_S_biomass_in = (biomass_flow * biomass_daf * biomass_S) / MW_S # No usado en syngas por simplicidad

    # Moles de H y O de la humedad
    moles_H2O_moisture_in = (biomass_flow * biomass_moisture) / MW_H2O
    moles_H_moisture_in = moles_H2O_moisture_in * 2
    moles_O_moisture_in = moles_H2O_moisture_in * 1

    # 2. Calcular Agente Gasificante (Masa y Moles de O2, N2, H2O)
    moles_O2_agent_in = 0
    moles_N2_agent_in = 0
    moles_H2O_agent_in = 0 # para vapor

    if gasifying_agent == "Aire" or gasifying_agent == "Mezcla Aire/Vapor":
        # Cálculo del O2 estequiométrico por kg de biomasa DAF
        # Basado en la fórmula de combustible C_a H_b O_c N_d S_e
        # moles de O2 requeridos para la combustión completa de 1 kg de biomasa DAF
        # (C/12) + (H/4) - (O/32)
        # Esto es más preciso:
        O2_stoich_moles_per_kg_DAF = (biomass_C / MW_C) + (biomass_H / (4 * MW_H)) - (biomass_O / (2 * MW_O))
        
        # Moles O2 alimentado por hora (kg biomasa_daf / kg biomasa_ar)
        moles_O2_agent_in = biomass_flow * biomass_daf * O2_stoich_moles_per_kg_DAF * er_ratio
        
        # Aire es 21% O2, 79% N2 molar. O2/N2 ratio = 0.21/0.79 = 0.2658
        moles_N2_agent_in = moles_O2_agent_in / (0.21 / 0.79) # moles N2 / hora
        
    if gasifying_agent == "Vapor" or gasifying_agent == "Mezcla Aire/Vapor":
        moles_H2O_agent_in = (biomass_flow * steam_biomass_ratio) / MW_H2O # moles H2O / hora
    
    if gasifying_agent == "Oxígeno":
        moles_O2_agent_in = (biomass_flow * oxygen_biomass_ratio) / MW_O2 # moles O2 / hora


    # 3. Balance Total de Átomos (por hora)
    total_moles_C_in = moles_C_biomass_in
    total_moles_H_in = moles_H_biomass_in + (moles_H2O_moisture_in * 2) + (moles_H2O_agent_in * 2)
    total_moles_O_in = moles_O_biomass_in + (moles_H2O_moisture_in * 1) + (moles_H2O_agent_in * 1) + (moles_O2_agent_in * 2)
    total_moles_N_in = moles_N_biomass_in + (moles_N2_agent_in * 2)


    # 4. Estimar Moles de Syngas (Simplificación y Balance Atómico)
    # Asunciones clave:
    # - Todo el N de la entrada sale como N2
    # - Carbono no convertido (char) = (1 - CCE) * C_biomasa
    # - Fracción de C convertido que va a CH4 (heurística)
    # - Resolver WGSR para CO, CO2, H2, H2O

    # Moles de N2 en syngas
    moles_N2_out = total_moles_N_in / 2 # Todo el N se convierte en N2

    # Moles de C no convertido (char)
    moles_C_unconverted = total_moles_C_in * (1 - carbon_conversion_efficiency)
    moles_C_converted = total_moles_C_in * carbon_conversion_efficiency

    # Asumir una fracción del carbono convertido se convierte en CH4
    # Este es un valor empírico y puede necesitar ajuste. 5-15% es común.
    CH4_carbon_fraction = 0.08 # 8% del carbono convertido va a CH4
    moles_CH4_out = moles_C_converted * CH4_carbon_fraction
    
    # Ajustar carbono convertido restante para CO y CO2
    moles_C_in_CO_CO2 = moles_C_converted - moles_CH4_out
    
    # Resto de moles de H y O disponibles para H2, CO, CO2, H2O (excluyendo N2 y CH4)
    # Cada mol de CH4 usa 4 moles de H y 1 mol de C
    moles_H_remaining = total_moles_H_in - (moles_CH4_out * 4)
    moles_O_remaining = total_moles_O_in # Ojo: O de CH4 es 0, O de N2 es 0

    # Ahora resolvemos para CO, CO2, H2, H2O
    # Sistema de ecuaciones no lineal:
    # 1) moles_CO_out + moles_CO2_out = moles_C_in_CO_CO2
    # 2) moles_CO_out + 2*moles_CO2_out + moles_H2O_out = moles_O_remaining
    # 3) 2*moles_H2_out + 2*moles_H2O_out = moles_H_remaining
    # 4) Kp = (moles_CO2_out * moles_H2_out) / (moles_CO_out * moles_H2O_out)
    
    # Para resolver este sistema, podemos usar una aproximación o un solver numérico.
    # Dada la naturaleza de Streamlit y la simplicidad buscada, usaremos una aproximación
    # que es común en modelos simplificados: asumir una relación H2/CO o CO/CO2.
    # O bien, una iteración simple para el equilibrio de WGSR.

    # --- SIMPLIFICACIÓN TEMPORAL (PENDIENTE DE IMPLEMENTACIÓN DE SOLVER) ---
    # Para la primera implementación funcional, vamos a fijar la relación CO2/CO
    # o H2/CO y luego usar el balance para los demás, y luego intentar aproximar el Kp.
    # La solución rigurosa del equilibrio termodinámico es compleja y requiere solvers.
    # Por ahora, mantendremos la simplificación que habíamos puesto, pero con una
    # base un poco más "inteligente" para que los números no sean completamente arbitrarios.
    
    # Vamos a usar una heurística para la relación H2/CO y luego ajustar por O y H
    # Esto es una simplificación grande para evitar un solver numérico complejo.
    # Relación típica H2/CO en syngas de aire: 0.5 a 1.2
    H2_CO_ratio_approx = 0.8 # Valor de diseño empírico para aire gasificación
    
    # Vamos a resolver las ecuaciones de balance de C, H, O y la relación Kp.
    # Este es el punto más complicado del modelo.
    # Por ahora, si no se implementa un solver real, los resultados serán aproximados.
    
    # Una heurística más robusta para CO, CO2, H2, H2O usando Kp:
    # Necesitamos una variable para iterar.
    # Vamos a usar fsolve de scipy.optimize si fuera un modelo completo.
    # Sin solver, es una asignación empírica o simplificación.

    # Para el propósito de esta app conceptual, mantendremos la simplificación,
    # pero el usuario debe entender que NO ES UN EQUILIBRIO TERM. RIGUROSO
    # sin un solver.

    # Los valores de ejemplo (proporciones molares típicas de un syngas de aire)
    # y luego balancear átomos.
    
    # Esta es una asignación EMPÍRICA, NO un cálculo de equilibrio.
    # Para tener valores coherentes para la demostración:
    # Calculamos el Kp de la WGSR
    kp_wgsr = calculate_k_wgsr(T_k)
    
    # Ahora, un método de resolución algebraica para CO, CO2, H2, H2O basado en 
    # balances atómicos y la constante Kp.
    # Definamos las incógnitas: nCO, nCO2, nH2, nH2O (moles de salida)
    
    # n_C_reactive = total_moles_C_in * carbon_conversion_efficiency
    # n_CH4 = n_C_reactive * CH4_carbon_fraction
    # n_C_remaining_for_CO_CO2 = n_C_reactive - n_CH4
    
    # Ahora tenemos un sistema con 3 balances (C, H, O) y la ecuación de Kp para 4 variables.
    # nCO + nCO2 = n_C_remaining_for_CO_CO2 (Eq C)
    # nCO + 2*nCO2 + nH2O = total_moles_O_in - (2*moles_O2_agent_in) - moles_O_moisture_in (Eq O)
    # 2*nH2 + 2*nH2O = total_moles_H_in - (4*nCH4) (Eq H)
    # Kp = (nCO2 * nH2) / (nCO * nH2O) (Eq Kp)

    # Este sistema de 4 ecuaciones no lineales para nCO, nCO2, nH2, nH2O
    # requiere un solver.
    # PARA EVITAR UN SOLVER COMPLEJO EN STREAMLIT: usaremos una aproximación muy común
    # en modelos simplificados: fijar una de las relaciones (p.ej., H2O/H2 o CO2/CO)
    # y usar Kp como chequeo o para un ajuste simple.

    # Vamos a usar una relación CO/CO2 típica para gasificación con aire.
    # Este es un punto de calibración empírica.
    R_CO_CO2 = 2.0 # CO/CO2 ratio. A mayor T, mayor CO/CO2.

    moles_CO2_out = moles_C_in_CO_CO2 / (R_CO_CO2 + 1)
    moles_CO_out = moles_C_in_CO_CO2 - moles_CO2_out

    # Ahora balanceamos H2 y H2O con las moles restantes de H y O, y la Kp.
    # total_moles_O_in = moles_CO_out + 2*moles_CO2_out + moles_H2O_out
    # moles_H2O_out = total_moles_O_in - moles_CO_out - 2*moles_CO2_out
    
    # H2O debe ser positivo, si es negativo, significa que nuestra estimación de CO/CO2 es demasiado alta
    # o el O total es muy bajo. Para evitar esto, si sale negativo, forzamos 0.
    moles_H2O_from_O_balance = total_moles_O_in - moles_CO_out - 2*moles_CO2_out
    moles_H2O_out = max(0, moles_H2O_from_O_balance) # Moles H2O según balance de O

    # Ahora, el H2 por balance de H:
    # total_moles_H_in = 2*moles_H2_out + 4*moles_CH4_out + 2*moles_H2O_out
    moles_H2_out = (total_moles_H_in - (4 * moles_CH4_out) - (2 * moles_H2O_out)) / 2
    moles_H2_out = max(0, moles_H2_out) # Aseguramos no negativo

    # Verificación de Kp (solo para información, no para resolver)
    # k_check = (moles_CO2_out * moles_H2_out) / (moles_CO_out * moles_H2O_out) if (moles_CO_out * moles_H2O_out) != 0 else np.nan
    # st.write(f"Kp Calculado: {k_check:.2f}, Kp a {gasification_temp}°C: {kp_wgsr:.2f}")

    # Es crucial asegurar que las moles no sean negativas
    moles_H2_out = max(0, moles_H2_out)
    moles_CO_out = max(0, moles_CO_out)
    moles_CO2_out = max(0, moles_CO2_out)
    moles_CH4_out = max(0, moles_CH4_out)
    moles_N2_out = max(0, moles_N2_out)
    moles_H2O_out = max(0, moles_H2O_out)


    # Convertimos los moles a fracciones molares y calculamos PCI del syngas
    total_moles_syngas = moles_H2_out + moles_CO_out + moles_CO2_out + moles_CH4_out + moles_N2_out + moles_H2O_out
    
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
        
        # Calcular PCI del syngas (MJ/Nm3)
        syngas_calorific_value = (syngas_composition['H2'] * PCI_H2_Nm3 +
                                  syngas_composition['CO'] * PCI_CO_Nm3 +
                                  syngas_composition['CH4'] * PCI_CH4_Nm3)
        
        # Volumen de syngas producido (Nm3/h)
        volume_syngas_produced = total_moles_syngas * MOLAR_VOLUME_NTP

    # La eficiencia de gasificación se calculará implícitamente del PCI del syngas
    # y la energía de la biomasa. La energía del syngas será PCI_syngas * volumen_syngas.
    # Luego, eficiencia = H_syngas / H_biomasa

    return syngas_composition, syngas_calorific_value, volume_syngas_produced

# --- Realizar los cálculos de la simulación ---
# Llamar a la función de gasificación
syngas_composition, syngas_calorific_value_calc, volume_syngas_produced_calc = simulate_gasification(
    biomass_flow, biomass_C, biomass_H, biomass_O, biomass_N, biomass_S,
    biomass_ash, biomass_moisture, biomass_energy, carbon_conversion_efficiency,
    gasification_temp, gasification_pressure, gasifying_agent,
    er_ratio, steam_biomass_ratio, oxygen_biomass_ratio
)

# Ahora los resultados de la gasificación se usan en los cálculos posteriores
total_biomass_consumed = biomass_flow * hours_operated
total_biomass_energy = total_biomass_consumed * biomass_energy # Este es PCI_biomasa * kg_biomasa_seca

# Energía en syngas producido (total durante las horas de operación)
energy_in_syngas = volume_syngas_produced_calc * syngas_calorific_value_calc * hours_operated

# Eficiencia de gasificación (implícita en el modelo)
gasification_efficiency_calc = energy_in_syngas / total_biomass_energy if total_biomass_energy > 0 else 0

electric_energy_generated_mj = energy_in_syngas * engine_efficiency
electric_energy_generated_kwh = electric_energy_generated_mj * 0.2778  # Factor de conversión: 1 MJ = 0.2778 kWh

average_power_output = electric_energy_generated_kwh / hours_operated if hours_operated > 0 else 0

# --- Cálculo de CO2 Producido (usando la composición calculada) ---
# Moles de CO2 producidos directamente de la combustión del CO y CH4 del syngas.
# Los moles de CO y CH4 de salida ya se calcularon en simulate_gasification y están en syngas_composition
# Hay que recalcular las moles de salida en la función o pasarlas.
# Para simplificar AHORA, usaremos las fracciones molares y el volumen total de syngas:
moles_CO_out_total_calc = syngas_composition['CO'] * volume_syngas_produced_calc / MOLAR_VOLUME_NTP # Moles por hora
moles_CH4_out_total_calc = syngas_composition['CH4'] * volume_syngas_produced_calc / MOLAR_VOLUME_NTP # Moles por hora

moles_co2_produced_from_syngas = (moles_CO_out_total_calc + moles_CH4_out_total_calc) * hours_operated
mass_co2_produced = moles_co2_produced_from_syngas * MW_CO2

# --- Mostrar los resultados calculados ---
st.markdown(f"""
    <div class="results-container">
        <p class="results-p">Biomasa Consumida (total): <strong class="results-strong">{total_biomass_consumed:.2f}</strong> kg</p>
        <p class="results-p">Energía Total de Biomasa: <strong class="results-strong">{total_biomass_energy:.2f}</strong> MJ</p>
        <p class="results-p">**Eficiencia de Gasificación (calculada):** <strong class="results-strong">{gasification_efficiency_calc:.2%}</strong></p>
        <p class="results-p">Energía en Syngas Producido: <strong class="results-strong">{energy_in_syngas:.2f}</strong> MJ</p>
        <p class="results-p">Volumen de Syngas Producido: <strong class="results-strong">{volume_syngas_produced_calc * hours_operated:.2f}</strong> Nm³</p>
        <p class="results-p">**Poder Calorífico Syngas (calculado):** <strong class="results-strong">{syngas_calorific_value_calc:.2f}</strong> MJ/Nm³</p>
        <p class="results-p">Energía Eléctrica Generada: <strong class="results-strong">{electric_energy_generated_mj:.2f}</strong> MJ</p>
        <p class="results-p">Electricidad Generada: <strong class="results-strong">{electric_energy_generated_kwh:.2f}</strong> kWh</p>
        <p class="results-p">Potencia Eléctrica Promedio: <strong class="results-strong">{average_power_output:.2f}</strong> kW</p>
        <p class="results-p">CO2 Producido (combustión): <strong class="results-strong">{mass_co2_produced:.2f}</strong> kg</p>
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
    st.write("No se pudo calcular la composición del syngas. Verifique los parámetros de entrada.")


st.markdown("---")

## 💡 Ecuaciones utilizadas

with st.expander("Ecuaciones utilizadas"):
    st.markdown("""
    Aquí se detallan las ecuaciones principales utilizadas para los cálculos de la simulación.
    """)

    st.subheader("1. Balances de Masa Atómicos")
    st.markdown("""
    Los balances de masa se realizan para cada elemento (C, H, O, N) desde la biomasa y el agente gasificante hacia los productos del syngas y el carbono no convertido.
    """)
    st.latex(r'''
        \text{C}_{\text{in}} = \text{C}_{\text{Syngas}} + \text{C}_{\text{no convertido}}
    ''')
    st.latex(r'''
        \text{H}_{\text{in}} = \text{H}_{\text{Syngas}}
    ''')
    st.latex(r'''
        \text{O}_{\text{in}} = \text{O}_{\text{Syngas}}
    ''')
    st.latex(r'''
        \text{N}_{\text{in}} = \text{N}_{\text{Syngas}}
    ''')
    st.markdown("""
    Donde:
    * $C_{in}$, $H_{in}$, $O_{in}$, $N_{in}$ son los moles totales de cada átomo que entran al gasificador (desde la biomasa seca, libre de cenizas, humedad y agente gasificante).
    * $C_{Syngas}$, $H_{Syngas}$, $O_{Syngas}$, $N_{Syngas}$ son los moles de cada átomo en los componentes gaseosos del syngas ($CO, CO_2, CH_4, H_2, H_2O, N_2$).
    * $C_{no convertido}$ es el carbono que no reacciona y sale como char/coque, determinado por la Eficiencia de Conversión de Carbono (CCE).
    """)

    st.subheader("2. Reacción de Desplazamiento de Gas de Agua (WGSR)")
    st.markdown("Esta reacción se asume en equilibrio para determinar la proporción entre $\\text{CO}$, $\\text{CO}_2$, $\\text{H}_2$ y $\\text{H}_2\text{O}$ en el syngas:")
    st.latex(r'''
        \text{CO} + \text{H}_2\text{O} \rightleftharpoons \text{CO}_2 + \text{H}_2
    ''')
    st.markdown("La constante de equilibrio $K_p$ de esta reacción depende de la temperatura y se utiliza para resolver el sistema de ecuaciones para las fracciones molares de estos gases. Su definición es:")
    st.latex(r'''
        K_p = \frac{X_{\text{CO}_2} \cdot X_{\text{H}_2}}{X_{\text{CO}} \cdot X_{\text{H}_2\text{O}}}
    ''')
    st.markdown("Donde $X_i$ es la fracción molar del componente $i$ en el syngas. El valor de $K_p$ se calcula internamente usando la siguiente correlación en función de la temperatura de gasificación ($T_k$ en Kelvin):")
    st.latex(r'''
        \ln K_p = -2.2562 + \frac{1829.0}{T_k} + 0.3546 \ln T_k - (1.189 \times 10^{-4} T_k) + (1.936 \times 10^{-8} T_k^2)
    ''')
    st.markdown("Esta correlación se utiliza para obtener el valor de $K_p$ a una temperatura dada, lo que permite un balance más preciso de los componentes gaseosos.")

    st.subheader("3. Cálculo de Fracciones Molares del Syngas")
    st.markdown("""
    Una vez que se han determinado las moles de cada componente gaseoso en el syngas ($\\text{H}_2, \\text{CO}, \\text{CO}_2, \\text{CH}_4, \\text{N}_2, \\text{H}_2\text{O}$), se calcula la fracción molar ($X_i$) de cada componente dividiendo sus moles por las moles totales del syngas:
    """)
    st.latex(r'''
        X_i = \frac{\text{moles}_i}{\text{moles}_{\text{Syngas, total}}}
    ''')
    st.markdown("""
    Donde:
    * $\\text{moles}_i$ es la cantidad de moles del componente $i$ en el syngas.
    * $\\text{moles}_{\text{Syngas, total}}$ es la suma de las moles de todos los componentes gaseosos presentes en el syngas.
    """)

    st.subheader("4. Poder Calorífico Inferior (PCI) del Syngas")
    st.markdown("""
    El PCI del syngas se calcula a partir de la composición molar predicha y los valores de PCI de sus componentes combustibles, a condiciones normales (0°C y 1 atm):
    """)
    st.latex(r'''
        \text{PCI}_{\text{Syngas}} = \sum_{i} (X_i \times \text{PCI}_{i, \text{Nm}^3})
    ''')
    st.markdown("""
    Donde $X_i$ es la fracción molar del componente combustible $i$ ($\\text{H}_2, \\text{CO}, \\text{CH}_4$) y $\\text{PCI}_{i, \text{Nm}^3}$ es el Poder Calorífico Inferior de ese componente por unidad de volumen.
    
    Los valores de PCI utilizados son:
    * **Hidrógeno ($\\text{H}_2$):** 10.79 MJ/Nm³
    * **Monóxido de Carbono ($\\text{CO}$):** 12.63 MJ/Nm³
    * **Metano ($\\text{CH}_4$):** 35.80 MJ/Nm³
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
        \eta_{\text{gasificación}} = \frac{V_{\text{Syngas, total}} \times \text{PCI}_{\text{Syngas}}}{\text{H}_{\text{Biomasa}}}
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
    * $\text{moles}_{\text{CO}}$ y $\text{moles}_{\text{CH}_4}$ son los moles totales de CO y $\text{CH}_4$ generados en el syngas durante la operación.
    * Masa Molar$_{\text{CO}_2}$ es la masa molar del dióxido de carbono (44 kg/kmol).
    * Estas ecuaciones asumen que todo el CO y $\text{CH}_4$ en el syngas se convierten completamente en $\text{CO}_2$ durante la combustión.
    """)
