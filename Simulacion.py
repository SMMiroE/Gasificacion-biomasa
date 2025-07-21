<!DOCTYPE html>
<htmllang="es">
<head>
    <metacharset="UTF-8">
    <metaname="viewport"content="width=device-width, initial-scale=1.0">
    <title>Simulación Syngas a Electricidad</title>
    <!-- Enlace a Tailwind CSS para un estilo moderno y responsivo -->
    <scriptsrc="https://cdn.tailwindcss.com"></script>
    <style>
        /* Estilos personalizados para el cuerpo y contenedor */
        body{
            font-family:'Inter',sans-serif;/* Usando Inter como fuente principal */
            background-color: #f0f2f5;/* Fondo suave */
            color: #333;
            display:flex;
            justify-content:center;
            align-items:flex-start;/* Alinear arriba para contenido largo */
            min-height:100vh;
            padding:20px;
            box-sizing:border-box;
        }
        .container{
            background:linear-gradient(135deg, #ffffff 0%, #f9f9f9 100%);/* Degradado suave */
            padding:30px;
            border-radius:15px;/* Bordes más redondeados */
            box-shadow:010px30pxrgba(0,0,0,0.15);/* Sombra más pronunciada */
            max-width:950px;
            width:100%;
            border:1pxsolid #e0e0e0;
        }
        h1,h2{
            color: #2c3e50;
            text-align:center;
            margin-bottom:20px;
            font-weight:700;/* Negrita para títulos */
        }
        h1{
            font-size:2.5rem;/* Tamaño de título principal */
            color: #1a202c;
        }
        h2{
            font-size:1.8rem;/* Tamaño de subtítulo */
            border-bottom:2pxsolid #e2e8f0;/* Línea divisoria */
            padding-bottom:10px;
            margin-top:30px;
        }
        .input-group{
            display:flex;
            flex-direction:column;/* Apilar elementos en móviles */
            margin-bottom:20px;
            background-color: #f7fafc;
            padding:15px;
            border-radius:10px;
            border:1pxsolid #e2e8f0;
        }
        .input-grouplabel{
            font-weight:600;/* Negrita para etiquetas */
            margin-bottom:8px;
            color: #4a5568;
            font-size:1.05rem;
        }
        .input-groupinput[type="range"]{
            width:100%;
            -webkit-appearance:none;/* Eliminar estilo por defecto en WebKit */
            appearance:none;
            height:8px;
            background: #cbd5e0;/* Color de la pista */
            border-radius:5px;
            outline:none;
            opacity:0.7;
            transition:opacity.2s;
        }
        .input-groupinput[type="range"]:hover{
            opacity:1;
        }
        .input-groupinput[type="range"]::-webkit-slider-thumb{
            -webkit-appearance:none;
            appearance:none;
            width:20px;
            height:20px;
            background: #4299e1;/* Color del pulgar */
            border-radius:50%;
            cursor:grab;
            box-shadow:02px5pxrgba(0,0,0,0.2);
        }
        .input-groupinput[type="range"]::-moz-range-thumb{
            width:20px;
            height:20px;
            background: #4299e1;
            border-radius:50%;
            cursor:grab;
            box-shadow:02px5pxrgba(0,0,0,0.2);
        }
        .input-value{
            text-align:right;
            font-weight:bold;
            color: #2b6cb0;
            margin-top:10px;/* Espacio entre slider y valor */
        }
        .results{
            margin-top:30px;
            padding:25px;
            background-color: #e6fffa;/* Fondo verde claro */
            border:1pxsolid #81e6d9;/* Borde verde */
            border-radius:10px;
            font-size:1.15em;
            line-height:1.6;
        }
        .resultsp{
            margin:10px0;
            display:flex;
            justify-content:space-between;
            align-items:center;
            padding-bottom:5px;
            border-bottom:1pxdashed #b2f5ea;
        }
        .resultsp:last-child{
            border-bottom:none;
        }
        .resultsstrong{
            color: #38b2ac;/* Verde azulado para resultados */
            font-weight:700;
            font-size:1.2em;
        }
        .diagram-container{
            text-align:center;
            margin:40px0;
        }
        /* Animación de pulso para la imagen del diagrama */
        @keyframespulse{
            0%{
                transform:scale(1);
                box-shadow:05px15pxrgba(0,0,0,0.1);
            }
            50%{
                transform:scale(1.01);/* Ligeramente más grande */
                box-shadow:08px20pxrgba(0,0,0,0.2);/* Sombra más pronunciada */
            }
            100%{
                transform:scale(1);
                box-shadow:05px15pxrgba(0,0,0,0.1);
            }
        }
        .diagram-containerimg{
            max-width:100%;
            height:auto;
            border:2pxsolid #a0aec0;
            border-radius:10px;
            box-shadow:05px15pxrgba(0,0,0,0.1);
            animation:pulse2sinfiniteease-in-out;/* Aplicar la animación */
        }
        .note{
            font-size:0.95em;
            color: #666;
            text-align:center;
            margin-top:15px;
            margin-bottom:30px;
        }

        /* Responsive adjustments */
        @media (min-width: 768px) {
            .input-group {
                flex-direction:row;/* Volver a fila en pantallas grandes */
                align-items:center;
            }
            .input-grouplabel{
                flex:2;
                margin-bottom:0;
                margin-right:20px;
            }
            .input-groupinput[type="range"]{
                flex:4;
            }
            .input-value{
                flex:1;
                text-align:right;
                min-width:70px;
                margin-top:0;
            }
        }
    </style>
</head>
<body>
    <divclass="container">
        <h1>🌱 Simulación: Biomasa a Electricidad ⚡</h1>
        <pclass="note">Ajusta los parámetros para ver cómo la biomasa se convierte en electricidad a través del syngas. Esta es una simulación conceptual y simplificada.</p>

        <divclass="diagram-container">
            <!-- Puedes reemplazar esta URL con una imagen de un diagrama real de gasificación de biomasa.
                 Por ejemplo, busca "diagrama gasificación biomasa motor generador" en Google Images,
                 sube una que te guste a un servicio como Imgur y pega el link aquí.
                 Si no tienes una, puedes eliminar la etiqueta <img>. -->
            <imgsrc="https://placehold.co/600x300/e0e0e0/555555?text=Diagrama+del+Sistema"alt="Diagrama del Sistema de Gasificación de Biomasa">
        </div>

        <h2>Parámetros de Entrada</h2>

        <divclass="input-group">
            <labelfor="biomassFlow">Flujo de Biomasa (kg/h):</label>
            <inputtype="range"id="biomassFlow"min="50"max="500"value="100"step="10">
            <spanid="biomassFlowValue"class="input-value">100</span>
        </div>

        <divclass="input-group">
            <labelfor="biomassEnergy">Poder Calorífico Biomasa (MJ/kg):</label>
            <inputtype="range"id="biomassEnergy"min="15"max="25"value="18"step="0.5">
            <spanid="biomassEnergyValue"class="input-value">18.0</span>
        </div>

        <divclass="input-group">
            <labelfor="gasificationEfficiency">Eficiencia de Gasificación (%):</label>
            <inputtype="range"id="gasificationEfficiency"min="50"max="85"value="70"step="1">
            <spanid="gasificationEfficiencyValue"class="input-value">70</span>
        </div>

        <divclass="input-group">
            <labelfor="syngasCalorificValue">Poder Calorífico Syngas (MJ/Nm³):</label>
            <inputtype="range"id="syngasCalorificValue"min="3"max="7"value="5"step="0.1">
            <spanid="syngasCalorificValue"class="input-value">5.0</span>
        </div>

        <divclass="input-group">
            <labelfor="engineEfficiency">Eficiencia Motor-Generador (%):</label>
            <inputtype="range"id="engineEfficiency"min="20"max="45"value="30"step="0.5">
            <spanid="engineEfficiencyValue"class="input-value">30.0</span>
        </div>

        <divclass="input-group">
            <labelfor="hoursOperated">Horas de Operación:</label>
            <inputtype="range"id="hoursOperated"min="1"max="24"value="8"step="1">
            <spanid="hoursOperatedValue"class="input-value">8</span>
        </div>

        <hrclass="my-8 border-gray-300">

        <h2>Resultados de la Simulación</h2>
        <divclass="results">
            <p>Biomasa Consumida (total): <strongid="totalBiomassConsumed">0</strong> kg</p>
            <p>Energía Total de Biomasa: <strongid="totalBiomassEnergy">0</strong> MJ</p>
            <p>Energía en Syngas Producido: <strongid="energyInSyngas">0</strong> MJ</p>
            <p>Volumen de Syngas Producido: <strongid="volumeSyngasProduced">0</strong> Nm³</p>
            <p>Energía Eléctrica Generada: <strongid="electricEnergyGenerated">0</strong> MJ</p>
            <p>Electricidad Generada: <strongid="electricityGeneratedKWh">0</strong> kWh</p>
            <p>Potencia Eléctrica Promedio: <strongid="averagePowerOutput">0</strong> kW</p>
            <p>CO2 Producido (combustión): <strongid="co2Produced">0</strong> kg</p>
        </div>
    </div>

    <script>
        // Función para actualizar los valores y realizar los cálculos de la simulación
        functionupdateSimulation(){
            // Obtener los valores de los controles deslizantes
            const biomassFlow = parseFloat(document.getElementById('biomassFlow').value);
            const biomassEnergy = parseFloat(document.getElementById('biomassEnergy').value);
            const gasificationEfficiency = parseFloat(document.getElementById('gasificationEfficiency').value)/100;// Convertir a decimal
            const syngasCalorificValue = parseFloat(document.getElementById('syngasCalorificValue').value);
            const engineEfficiency = parseFloat(document.getElementById('engineEfficiency').value)/100;// Convertir a decimal
            const hoursOperated = parseFloat(document.getElementById('hoursOperated').value);

            // Actualizar los valores numéricos mostrados junto a cada control deslizante
            document.getElementById('biomassFlowValue').textContent = biomassFlow;
            document.getElementById('biomassEnergyValue').textContent = biomassEnergy.toFixed(1);
            document.getElementById('gasificationEfficiencyValue').textContent =(gasificationEfficiency *100).toFixed(0);
            document.getElementById('syngasCalorificValue').textContent = syngasCalorificValue.toFixed(1);
            document.getElementById('engineEfficiencyValue').textContent =(engineEfficiency *100).toFixed(1);
            document.getElementById('hoursOperatedValue').textContent = hoursOperated;

            // Realizar los cálculos de la simulación
            const totalBiomassConsumed = biomassFlow * hoursOperated;
            const totalBiomassEnergy = totalBiomassConsumed * biomassEnergy;
            constenergyInSyngas=totalBiomassEnergy*gasificationEfficiency;
            
            // Evitar división por cero si el poder calorífico del syngas es cero
            const volumeSyngasProduced = syngasCalorificValue >0? energyInSyngas / syngasCalorificValue :0;
            
            const electricEnergyGeneratedMJ = energyInSyngas * engineEfficiency;
            const electricEnergyGeneratedKWh = electricEnergyGeneratedMJ *0.2778;// Factor de conversión: 1 MJ = 0.2778 kWh
            
            // Evitar división por cero si las horas de operación son cero
            const averagePowerOutput = hoursOperated >0? electricEnergyGeneratedKWh / hoursOperated :0;

            // --- Cálculo de CO2 Producido ---
            // Asunciones para la composición del syngas (volumétrica, base seca, libre de N2 y CO2 inicial)
            // Estas son simplificaciones para la simulación conceptual.
            // Se asume que el syngas contiene un 20% de CO y un 3% de CH4 en volumen.
            constcoPercentage=0.20;   // 20% de CO en el syngas
            const ch4Percentage =0.03;  // 3% de CH4 en el syngas

            // Constante molar de volumen (Nm³/kmol) a 0°C y 1 atm (condiciones normales)
            const molarVolumeSTP =22.4;
            // Masa molar de CO2 (kg/kmol)
            const co2MolarMass =44;// g/mol = kg/kmol

            // Moles de CO y CH4 en el volumen total de syngas producido
            // (Volumen de gas * % de componente) / Volumen molar estándar
            const molesCO =(volumeSyngasProduced * coPercentage)/ molarVolumeSTP;
            const molesCH4 =(volumeSyngasProduced * ch4Percentage)/ molarVolumeSTP;

            // Moles de CO2 producidos por combustión
            // Reacciones: CO + 0.5 O2 -> CO2 (1 mol CO produce 1 mol CO2)
            //            CH4 + 2 O2 -> CO2 + 2 H2O (1 mol CH4 produce 1 mol CO2)
            const molesCO2Produced =molesCO+ molesCH4;

            // Masa de CO2 producida (en kg)
            const massCO2Produced = molesCO2Produced * co2MolarMass;
            // --- Fin del Cálculo de CO2 Producido ---

            // Mostrar los resultados calculados en la sección de resultados
            document.getElementById('totalBiomassConsumed').textContent = totalBiomassConsumed.toFixed(2);
            document.getElementById('totalBiomassEnergy').textContent = totalBiomassEnergy.toFixed(2);
            document.getElementById('energyInSyngas').textContent = energyInSyngas.toFixed(2);
            document.getElementById('volumeSyngasProduced').textContent = volumeSyngasProduced.toFixed(2);
            document.getElementById('electricEnergyGenerated').textContent = electricEnergyGeneratedMJ.toFixed(2);
            document.getElementById('electricityGeneratedKWh').textContent = electricEnergyGeneratedKWh.toFixed(2);
            document.getElementById('averagePowerOutput').textContent = averagePowerOutput.toFixed(2);
            document.getElementById('co2Produced').textContent= massCO2Produced.toFixed(2);// Mostrar el CO2 producido
        }

        // Asignar un evento 'input' a cada control deslizante para que la simulación se actualice en tiempo real
        document.querySelectorAll('input[type="range"]').forEach(input =>{
            input.addEventListener('input',updateSimulation);
        });

        // Ejecutar la función de simulación una vez al cargar la página para mostrar los valores iniciales
        updateSimulation();
    </script>
</body>
</html>
