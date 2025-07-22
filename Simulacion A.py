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
# Asegúrate de que la imagen "image_3c55b6.png" esté en la misma carpeta que tu script
st.image("image_3c55b6.png",
         caption="Diagrama del Sistema de Gasificación de Biomasa",
         use_container_width=True)

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
        # O2_stoichiometric_moles_per_kg_DAF = (biomass_C / MW_C) + (biomass_H / (4 * MW_H)) - (biomass_O / (2 * MW_O))
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

    # Usaremos un método iterativo simple o una solución algebraica si es posible.
    # Kp = X_CO2 * X_H2 / (X_CO * X_H2O)
    # moles_CO2 = moles_C_in_CO_CO2 - moles_CO
    # moles_H2 = (moles_H_remaining - 2*moles_H2O) / 2
    # ... esto se vuelve complejo rápido.

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
    
    # Vamos a usar una aproximación lineal para la distribución de CO/CO2/H2/H2O
    # basándonos en la experiencia. Este es el trade-off por no usar un solver.
    # Definimos unas proporciones relativas para el C, H y O que NO fueron a CH4
    # Estas son estimaciones y NO son el resultado de un equilibrio termodinámico real.
    
    # Aproximación:
    # Moles de H2O que se producen de la humedad (ya está en total_moles_H_in y total_moles_O_in)
    # Moles de H2O que reaccionan por WGSR
    # Moles de CO2 que se producen vs CO

    # Dado que la WGSR es la única reacción de equilibrio explícita, podemos intentar
    # despejar asumiendo los moles restantes de C_in_CO_CO2, H_remaining, O_remaining.
    
    # Intentemos con un método iterativo simple para la WGSR
    kp_val = calculate_k_wgsr(T_k)
    
    # Inicializamos con un valor para moles_CO_out
    # Por ejemplo, una fracción del carbono convertido restante
    moles_CO_out = moles_C_in_CO_CO2 * 0.6 # Asumimos 60% del C va a CO, 40% a CO2
    moles_CO2_out = moles_C_in_CO_CO2 - moles_CO_out

    # Calculamos H2O y H2 a partir de los balances con estas suposiciones,
    # y luego verificamos Kp. Si no cuadra, ajustamos.
    # Esto es una simulación simplificada, no un solver riguroso.

    # Primera estimación de H2O y H2 a partir de balances de O y H, sin Kp aún
    # (Esto será el valor a iterar o resolver)
    
    # Para tener valores iniciales razonables y evitar negativos:
    moles_H2_out_initial = moles_H_remaining * 0.5 / 2 # ~50% de H a H2
    moles_H2O_out_initial = moles_H_remaining * 0.5 / 2 # ~50% de H a H2O

    # Ajustar para que el oxígeno restante se distribuya.
    # 2*moles_CO2_out + moles_CO_out + moles_H2O_out = moles_O_remaining
    # moles_H2O_out = moles_O_remaining - (2*moles_CO2_out + moles_CO_out)
    
    # Esto es una aproximación, no una resolución simultánea de equilibrio.
    # Para la simulación, y sin un solver, podemos usar aproximaciones comunes:
    # 1. Fijar CO2/CO ratio (ej. 0.5)
    # 2. Fijar H2/CO ratio (ej. 1.0)
    # 3. Calcular H2O por balance de O.

    # Opción simplificada para obtener resultados coherentes:
    # Asumimos una distribución de carbono entre CO y CO2
    CO_fraction_of_carbon = 0.65 # Ej: 65% del C_in_CO_CO2 va a CO
    moles_CO_out = moles_C_in_CO_CO2 * CO_fraction_of_carbon
    moles_CO2_out = moles_C_in_CO_CO2 * (1 - CO_fraction_of_carbon)

    # El oxígeno y el hidrógeno restantes se distribuyen entre H2 y H2O
    # H = 2*H2 + 2*H2O
    # O = CO + 2*CO2 + H2O
    # De aquí podemos despejar H2O y H2
    
    # Esto es un sistema de 2 ecuaciones con 2 incógnitas (H2, H2O)
    # O_balance_for_H2O_H2 = moles_O_remaining - moles_CO_out - 2*moles_CO2_out
    # H_balance_for_H2O_H2 = moles_H_remaining
    
    # Consideramos que la mayoría del oxígeno se usa para CO/CO2, el resto va a H2O
    # Y el hidrógeno restante se distribuye entre H2 y H2O.
    
    # Vamos a basarnos en la correlación de Kp de la WGSR para que sea más "realista"
    # Este es un enfoque común en modelos empíricos o de equilibrio simplificado
    # Definimos una variable de extensión de reacción 'epsilon' para la WGSR
    # CO_in + H2O_in <=> CO2_out + H2_out
    # moles_CO_out = moles_CO_ref - epsilon
    # moles_H2O_out = moles_H2O_ref - epsilon
    # moles_CO2_out = moles_CO2_ref + epsilon
    # moles_H2_out = moles_H2_ref + epsilon
    
    # Para el modelo simplificado, vamos a asumir que la relación H2/CO es fija.
    # Esto es un método común cuando no se usa un solver completo.
    # Luego, ajustamos con los balances de C, H, O.
    
    # Reintentamos con una distribución más coherente, basándonos en balances y Kp
    # H_total = 2*moles_H2_out + 4*moles_CH4_out + 2*moles_H2O_out
    # O_total = moles_CO_out + 2*moles_CO2_out + moles_H2O_out + 2*moles_O2_out_unreacted (assuming any unreacted O2)
    # C_total = moles_CO_out + moles_CO2_out + moles_CH4_out + moles_C_unconverted

    # Considerando que moles_O2_agent_in ya fue usado en total_moles_O_in, y que
    # no asumimos O2 sin reaccionar en el syngas.

    # Moles de CO, CO2, H2, H2O
    # Resolver un sistema de ecuaciones para esto es la parte más compleja.
    # Por el momento, y para que la aplicación funcione, voy a usar una distribución
    # típica basada en un gasificador de aire. Esto NO es un equilibrio completo,
    # sino una aproximación empírica para el output.

    # Estos valores son EMPÍRICOS y representan un resultado esperado de gasificación con aire.
    # La parte rigurosa con Kp requiere un solver numérico para CO, CO2, H2, H2O.
    # Asumamos una distribución de carbono convertido para fines de ejemplo:
    moles_CO_out_frac = 0.50 # Fracción del C_in_CO_CO2
    moles_CO2_out_frac = 0.42 # Fracción del C_in_CO_CO2
    # El resto del C_in_CO_CO2 (0.08) es implicito para CH4 (CH4_carbon_fraction = 0.08)

    # Calculamos moles de CO y CO2
    moles_CO_out = moles_C_in_CO_CO2 * moles_CO_out_frac
    moles_CO2_out = moles_C_in_CO_CO2 * moles_CO2_out_frac

    # Distribuimos el Hidrógeno y Oxígeno restantes.
    # Necesitamos balancear H y O con H2 y H2O
    # Supongamos una relación H2/CO típica:
    H2_CO_ratio_syngas = 0.6 # Aproximación común para gasificación con aire

    moles_H2_out = moles_CO_out * H2_CO_ratio_syngas
    
    # Calcular H2O a partir del balance de H y O
    # H_remaining = 2*moles_H2_out + 2*moles_H2O_out
    # O_remaining = moles_CO_out + 2*moles_CO2_out + moles_H2O_out

    # Despejamos moles_H2O_out de la ecuación de balance de O:
    # moles_H2O_out = total_moles_O_in - moles_O_biomass_in_syngas - moles_O_agent_in_syngas (no es así)
    
    # Intentamos balancear H2O para satisfacer el oxígeno restante
    # O_disponible = total_moles_O_in - moles_CO_out - 2*moles_CO2_out
    # moles_H2O_out = O_disponible # Esta sería una simplificación si todo O extra va a H2O

    # Para un modelo conceptual, podemos asumir que una parte de la humedad se condensa
    # y otra reacciona, y el resto del H y O se balancea entre H2 y H2O de acuerdo a Kp.
    # Esto es el punto más débil sin un solver.

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
    moles_CO_out_perc = 0.20 # % molar
    moles_H2_out_perc = 0.18 # % molar
    moles_CO2_out_perc = 0.12 # % molar
    moles_CH4_out_perc = 0.03 # % molar (viene del CCE)

    # La suma de los anteriores es 0.53
    # N2 será dominante
    # H2O dependerá de la humedad de la biomasa y el vapor si es usado.

    # Calculamos el Kp de la WGSR
    kp_wgsr = calculate_k_wgsr(T_k)
    
    # Ahora, un método de resolución algebraica para CO, CO2, H2, H2O basado en 
    # balances atómicos y la constante Kp.
    # Definamos las incógnitas: nCO, nCO2, nH2, nH2O (moles de salida)
    
    # nC_total_in_syngas = nCO + nCO2 + nCH4
    # nH_total_in_syngas = 2*nH2 + 4*nCH4 + 2*nH2O
    # nO_total_in_syngas = nCO + 2*nCO2 + nH2O
    
    # De los inputs: total_moles_C_in, total_moles_H_in, total_moles_O_in
    
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

    # Vamos a usar una heurística para la relación CO/CO2 y luego los balances.
    # Esta es una simplificación fuerte para evitar un solver.
    # Por ejemplo, podemos asumir que la relación H2O/H2 está cerca del equilibrio,
    # o que una cierta fracción del C va a CO y el resto a CO2.

    # Método de simplificación avanzada para modelos de gasificación:
    # 1. Definir moles de N2 y CH4 (ya hecho)
