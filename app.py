"""
================================================================================
APLICACIÓN STREAMLIT - MONITOR DE ENERGÍA DE MICRORRED CON BATERÍA
Asignatura: Fundamentos de Programación - Ingeniería Energética
================================================================================
Interfaz visual interactiva de alta fidelidad para el monitoreo y simulación
de microrredes eléctricas con almacenamiento y conexión a red.
================================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import os
import importlib
import logica
importlib.reload(logica)

# Configuración inicial de la página
st.set_page_config(
    page_title="MICROGRID | Monitor de Energía",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para la barra lateral y contenedor de Streamlit
st.markdown("""
<style>
    /* Ocultar barra superior y eliminar espacios grises/negros alrededor */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    html, body, .stApp, section.main {
        background-color: #0B131E !important;
    }
    section.main {
        padding: 0 !important;
    }
    .main .block-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }
    div[data-testid="stCustomComponentV1"] {
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        background-color: #0B131E !important;
    }
    iframe {
        width: 100% !important;
        border: none !important;
        display: block;
        background-color: #0B131E !important;
    }
    [data-testid="stSidebar"] {
        background-color: #0E1724;
        border-right: 1px solid #1C2E42;
    }
    .stAlert {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# GESTIÓN DE ESTADO (SESSION STATE)
# ------------------------------------------------------------------------------
if "datos_activos" not in st.session_state:
    # Cargar por defecto datos de entrada si existen
    if os.path.exists("datos/entrada.json"):
        st.session_state.datos_activos = logica.cargar_datos("datos/entrada.json")
    else:
        st.session_state.datos_activos = {
            "microrred": "Rural 1",
            "capacidad": 15.0,
            "soc_inicial": 4.7,
            "horas": [[0.0, 1.2]] * 24
        }

if "preset_actual" not in st.session_state:
    st.session_state.preset_actual = "rural"


# ------------------------------------------------------------------------------
# PANEL LATERAL: CONTROLES, ARCHIVOS Y RETOS FUNCIONALES
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ **Panel de Control**")
    st.caption("Configuración y parámetros del modelo")

    # Selección de Escenarios
    opcion_preset = st.selectbox(
        "Seleccionar Escenario:",
        [
            "☀️ Microrred Rural 1 (24 Horas)",
            "⭐ Caso de Verificación Oficial (4h)",
            "📂 Subir archivo JSON personalizado"
        ],
        index=1 if st.session_state.preset_actual == "verificacion" else 0
    )

    if opcion_preset == "⭐ Caso de Verificación Oficial (4h)":
        st.session_state.preset_actual = "verificacion"
        if os.path.exists("datos/caso_verificacion.json"):
            st.session_state.datos_activos = logica.cargar_datos("datos/caso_verificacion.json")
    elif opcion_preset == "☀️ Microrred Rural 1 (24 Horas)":
        st.session_state.preset_actual = "rural"
        if os.path.exists("datos/entrada.json"):
            st.session_state.datos_activos = logica.cargar_datos("datos/entrada.json")
    else:
        st.session_state.preset_actual = "custom"
        archivo_subido = st.file_uploader("Cargar JSON de microrred", type=["json"])
        if archivo_subido is not None:
            try:
                datos_cargados = json.load(archivo_subido)
                st.session_state.datos_activos = datos_cargados
                st.success("¡Archivo cargado con éxito!")
            except Exception as e:
                st.error(f"Error al leer JSON: {e}")

    datos = st.session_state.datos_activos

    st.markdown("---")
    st.markdown("#### 🔋 **Parámetros de Batería**")

    # Controles en tiempo real de capacidad y SOC inicial
    capacidad_default = float(datos.get("capacidad", 10.0))
    soc_default = float(datos.get("soc_inicial", 5.0))

    capacidad_usuario = st.number_input(
        "Capacidad Máxima (kWh):",
        min_value=1.0,
        max_value=200.0,
        value=capacidad_default,
        step=1.0
    )

    soc_usuario = st.number_input(
        "SOC Inicial (kWh):",
        min_value=0.0,
        max_value=capacidad_usuario,
        value=min(soc_default, capacidad_usuario),
        step=0.5
    )

    # Actualizar copia para la simulación
    datos_simulacion = {
        "microrred": datos.get("microrred", "Microrred"),
        "capacidad": capacidad_usuario,
        "soc_inicial": soc_usuario,
        "horas": [list(par) for par in datos.get("horas", [])]
    }

    # Factor de escala solar (para pruebas interactivas en vivo del docente)
    factor_solar = st.slider(
        "Factor de Generación Solar:",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="Multiplica la generación solar de todas las horas (útil para pruebas en sustentación)."
    )
    if factor_solar != 1.0:
        for par in datos_simulacion["horas"]:
            par[0] = round(par[0] * factor_solar, 2)

    # --------------------------------------------------------------------------
    # RETO FUNCIONAL: EFICIENCIA DE CARGA Y DESCARGA (SECCIÓN 4 DEL PROYECTO)
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### ⚡ **Reto Funcional: Eficiencia**")
    eficiencia = st.slider(
        "Eficiencia de Batería (η):",
        min_value=0.50,
        max_value=1.00,
        value=0.90,
        step=0.05,
        format="%.2f",
        help="Eficiencia en los ciclos de carga y descarga (por ejemplo 90%). 1.00 representa batería ideal."
    )
    st.caption(f"🔋 Eficiencia activa: **{int(eficiencia * 100)}%**")

    # --------------------------------------------------------------------------
    # VALIDACIONES DE ROBUSTEZ (SECCIÓN D DE LA RÚBRICA)
    # --------------------------------------------------------------------------
    alertas_validacion, es_valido = logica.validar_datos(datos_simulacion)
    if alertas_validacion:
        st.markdown("---")
        st.markdown("#### ⚠️ **Validaciones del Sistema**")
        for alerta in alertas_validacion:
            if "Error" in alerta:
                st.error(alerta)
            else:
                st.warning(alerta)

    # Botón para descargar salida.json
    st.markdown("---")


# Precalculamos ambos escenarios estándar para cambio en tiempo real instantáneo sin parpadeo
# Los escenarios base usan eficiencia=1.0 (batería ideal) para visualización correcta del perfil.
# El reto funcional de eficiencia se muestra interactivamente a través del slider de la barra lateral.
datos_rural = logica.cargar_datos("datos/entrada.json") if os.path.exists("datos/entrada.json") else datos_simulacion
horas_rural, totales_rural = logica.simular_microrred(datos_rural, eficiencia=1.0)

datos_verif = logica.cargar_datos("datos/caso_verificacion.json") if os.path.exists("datos/caso_verificacion.json") else datos_simulacion
horas_verif, totales_verif = logica.simular_microrred(datos_verif, eficiencia=1.0)

initial_scenario_key = "verificacion" if st.session_state.preset_actual == "verificacion" else "rural"

# Escenario actualmente seleccionado para exportar en salida.json
datos_activos_sim = datos_verif if initial_scenario_key == "verificacion" else datos_rural
horas_simuladas, totales = (horas_verif, totales_verif) if initial_scenario_key == "verificacion" else (horas_rural, totales_rural)

# Soporte para JSON personalizado si el usuario sube uno
if st.session_state.preset_actual == "custom":
    horas_custom, totales_custom = logica.simular_microrred(datos_simulacion, eficiencia=eficiencia)
    horas_simuladas, totales = horas_custom, totales_custom
    initial_scenario_key = "custom"

salida_dict = {
    "microrred": datos_simulacion.get("microrred", "Microrred"),
    "totales": totales,
    "horas": horas_simuladas
}
os.makedirs("datos", exist_ok=True)
logica.guardar_resultados("datos/salida.json", salida_dict)

with st.sidebar:
    st.download_button(
        label="💾 Descargar salida.json",
        data=json.dumps(salida_dict, indent=2, ensure_ascii=False),
        file_name="salida.json",
        mime="application/json"
    )

# Paquete de escenarios para JavaScript (elimina el parpadeo en la interfaz)
scenarios_payload = {
    "rural": {
        "name": "Microrred Rural 1",
        "horas": horas_rural,
        "totales": totales_rural,
        "capacidad": totales_rural["capacidad_bateria"]
    },
    "verificacion": {
        "name": "Caso de Verificación Oficial",
        "horas": horas_verif,
        "totales": totales_verif,
        "capacidad": totales_verif["capacidad_bateria"]
    }
}
if st.session_state.preset_actual == "custom":
    scenarios_payload["custom"] = {
        "name": datos_simulacion.get("microrred", "Personalizada"),
        "horas": horas_simuladas,
        "totales": totales,
        "capacidad": totales["capacidad_bateria"]
    }

json_scenarios = json.dumps(scenarios_payload)
json_hourly_data = json.dumps(horas_simuladas)
json_totales = json.dumps(totales)
nombre_microrred = scenarios_payload[initial_scenario_key]["name"]
capacidad_max = scenarios_payload[initial_scenario_key]["capacidad"]

html_dashboard = f"""<!DOCTYPE html>
<html class="dark" lang="es" style="background-color: #0B131E !important;">
<head>
<meta charset="utf-8">
<meta content="width=device-width, initial-scale=1.0" name="viewport">
<title>MICROGRID | Monitor de Energía</title>
<style>
    html, body {{
      background-color: #0B131E !important;
      color: #F1F5F9;
    }}
</style>
<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com" rel="preconnect">
<link crossorigin="" href="https://fonts.gstatic.com" rel="preconnect">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
<script>
    tailwind.config = {{
      darkMode: 'class',
      theme: {{
        extend: {{
          fontFamily: {{
            sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace'],
          }},
          colors: {{
            solar: '#10B981',
            battery: '#38BDF8',
            warning: '#F59E0B',
            critical: '#EF4444',
            gridDark: '#080E18',
            surfaceCard: '#0E1626',
            surfaceSecondary: '#131F33',
            surfaceBorder: '#1E2D42',
            surfaceBorderHighlight: '#293E5C',
          }}
        }}
      }}
    }}
</script>
<style>
    @keyframes pulseGlow {{
      0%, 100% {{ opacity: 0.95; filter: drop-shadow(0 0 8px currentColor); }}
      50% {{ opacity: 0.45; filter: drop-shadow(0 0 2px currentColor); }}
    }}
    @keyframes dashMove {{
      to {{ stroke-dashoffset: -24; }}
    }}
    .flow-active {{
      stroke-dasharray: 6 6;
      animation: dashMove 1.1s linear infinite;
    }}
    .glow-green {{
      filter: drop-shadow(0 0 6px rgba(16, 185, 129, 0.45));
    }}
    .glow-blue {{
      filter: drop-shadow(0 0 6px rgba(57, 136, 214, 0.45));
    }}
    .glow-yellow {{
      filter: drop-shadow(0 0 6px rgba(234, 179, 8, 0.45));
    }}
    /* Custom range slider styling */
    input[type=range] {{
      -webkit-appearance: none;
      background: transparent;
    }}
    input[type=range]::-webkit-slider-thumb {{
      -webkit-appearance: none;
      height: 20px;
      width: 20px;
      border-radius: 9999px;
      background: #38BDF8;
      cursor: pointer;
      box-shadow: 0 0 10px rgba(56, 189, 248, 0.7);
      margin-top: -6px;
      transition: all 0.15s ease;
      border: 2px solid #0B131E;
    }}
    input[type=range]::-webkit-slider-thumb:hover {{
      transform: scale(1.2);
      box-shadow: 0 0 14px rgba(56, 189, 248, 0.9);
    }}
    input[type=range]::-webkit-slider-runnable-track {{
      width: 100%;
      height: 8px;
      cursor: pointer;
      background: #1C2E42;
      border-radius: 9999px;
      border: 1px solid #243B55;
    }}

    /* Light Theme support */
    html.light body {{
      background-color: #F8FAFC !important;
      color: #0F172A !important;
    }}
    html.light header, html.light section, html.light .bg-\\[\\#111C2A\\] {{
      background-color: #FFFFFF !important;
      border-color: #E2E8F0 !important;
    }}
    html.light .bg-\\[\\#0D1726\\] {{
      background-color: #F1F5F9 !important;
      border-color: #CBD5E1 !important;
    }}
    html.light .bg-\\[\\#162436\\] {{
      background-color: #E2E8F0 !important;
      color: #0F172A !important;
      border-color: #CBD5E1 !important;
    }}
    html.light .text-white {{
      color: #0F172A !important;
    }}
    html.light .text-\\[\\#F1F5F9\\] {{
      color: #0F172A !important;
    }}
</style>
</head>
<body class="bg-[#0B131E] text-[#F1F5F9] min-h-screen antialiased font-sans selection:bg-[#38BDF8]/30 selection:text-white" style="font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;">

<!-- TOP BAR -->
<header class="bg-[#111C2A] border-b border-[#1C2E42] sticky top-0 z-30 transition-colors">
<div class="w-full px-8 h-16 flex items-center justify-between">
  <!-- Brand & Title -->
  <div class="flex items-center gap-4">
    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#10B981] via-[#38BDF8] to-[#3988D6] p-0.5 shadow-lg shadow-emerald-950/40 flex items-center justify-center">
      <div class="w-full h-full bg-[#111C2A] rounded-[10px] flex items-center justify-center">
        <svg class="w-5 h-5 text-[#10B981]" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" viewBox="0 0 24 24">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
      </div>
    </div>
    <div>
      <div class="flex items-center gap-2">
        <h1 class="font-bold text-lg tracking-tight text-white">MICROGRID</h1>
        <span class="text-[11px] px-2 py-0.5 rounded font-medium bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/30">Académico</span>
      </div>
      <p class="text-xs text-[#94A3B8] font-medium">Energy Monitoring System · <span class="font-semibold text-gray-200" id="microrredLabel">{nombre_microrred}</span></p>
    </div>
  </div>

  <!-- Center: Operational Status & Real-time Scenario Switcher (Sin parpadeo) -->
  <div class="hidden md:flex items-center gap-4">
    <div class="flex items-center gap-1.5 bg-[#0D1726] p-1 rounded-xl border border-[#1C2E42]">
      <button id="scenarioBtnRural" onclick="switchScenario('rural')" class="px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 {'bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/40 shadow-sm' if initial_scenario_key == 'rural' else 'text-[#94A3B8] hover:text-white hover:bg-[#162436] border border-transparent'}">
        <span class="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span>
        <span>☀️ Rural 1 (24h)</span>
      </button>
      <button id="scenarioBtnVerif" onclick="switchScenario('verificacion')" class="px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 {'bg-amber-400/20 text-amber-300 border border-amber-400/40 shadow-sm' if initial_scenario_key == 'verificacion' else 'text-[#94A3B8] hover:text-white hover:bg-[#162436] border border-transparent'}">
        <span class="w-1.5 h-1.5 rounded-full bg-amber-400"></span>
        <span>⭐ Verificación (4h)</span>
      </button>
    </div>

    <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/30 shadow-[0_0_12px_rgba(16,185,129,0.15)]">
      <span class="w-2 h-2 rounded-full bg-[#10B981] animate-pulse"></span>
      <span class="text-xs font-semibold text-[#10B981]">Sistema operativo</span>
    </div>
    <div class="flex items-center gap-2 text-xs font-mono text-[#94A3B8] bg-[#162436] px-3 py-1.5 rounded-lg border border-[#1C2E42]">
      <svg class="w-3.5 h-3.5 text-[#38BDF8]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
      </svg>
      <span>HORA: <span class="font-bold text-white tracking-wide" id="topBarTime">01:00 h</span></span>
    </div>
  </div>

  <!-- Controls: Theme toggle & simulation status -->
  <div class="flex items-center gap-3">
    <div class="text-xs font-medium px-2.5 py-1 rounded bg-[#162436] border border-[#1C2E42] text-[#94A3B8] flex items-center gap-1.5" id="simModeBadge">
      <span class="w-1.5 h-1.5 rounded-full bg-amber-400" id="simDot"></span>
      <span id="simModeText">Pausado</span>
    </div>
    <button class="p-2 rounded-lg bg-[#162436] border border-[#1C2E42] hover:bg-[#1C2E42] text-amber-300 transition-colors flex items-center justify-center cursor-pointer" id="themeToggleBtn" title="Cambiar tema">
      <svg class="w-4 h-4 text-amber-400" fill="none" id="themeIconSun" stroke="currentColor" viewBox="0 0 24 24">
        <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
      </svg>
    </button>
  </div>
</div>
</header>

<!-- MAIN WRAPPER -->
<main class="w-full px-8 py-6 space-y-6">

<!-- B. INDICADORES GENERALES (4 Metric Cards) -->
<section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
  <!-- Card 1: Generación Solar -->
  <div class="bg-[#111C2A] p-5 rounded-xl border border-[#1C2E42] hover:border-[#243B55] shadow-lg relative overflow-hidden transition-all group">
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">Generación Solar</span>
      <div class="w-8 h-8 rounded-lg bg-[#10B981]/15 text-[#10B981] flex items-center justify-center border border-[#10B981]/30">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
        </svg>
      </div>
    </div>
    <div class="flex items-baseline gap-2">
      <span class="text-3xl font-extrabold text-white font-mono tracking-tight" id="metricSolar" style="font-size: 2.5rem; line-height: 1;">0.00</span>
      <span class="text-xs font-semibold text-[#94A3B8]">kWh</span>
    </div>
    <div class="mt-3 flex items-center justify-between text-xs pt-3 border-t border-[#1C2E42]">
      <span class="text-[#94A3B8]" id="totalSolarLabel">Total día: {totales['total_generacion']} kWh</span>
      <span class="text-[#10B981] font-semibold" id="metricSolarStatus">Activo</span>
    </div>
  </div>

  <!-- Card 2: Consumo Total -->
  <div class="bg-[#111C2A] p-5 rounded-xl border border-[#1C2E42] hover:border-[#243B55] shadow-lg relative overflow-hidden transition-all group">
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">Consumo Total</span>
      <div class="w-8 h-8 rounded-lg bg-[#38BDF8]/15 text-[#38BDF8] flex items-center justify-center border border-[#38BDF8]/30">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
        </svg>
      </div>
    </div>
    <div class="flex items-baseline gap-2">
      <span class="text-3xl font-extrabold text-white font-mono tracking-tight" id="metricDemand" style="font-size: 2.5rem; line-height: 1;">0.00</span>
      <span class="text-xs font-semibold text-[#94A3B8]">kWh</span>
    </div>
    <div class="mt-3 flex items-center justify-between text-xs pt-3 border-t border-[#1C2E42]">
      <span class="text-[#94A3B8]" id="totalDemandLabel">Total demanda: {totales['total_demanda']} kWh</span>
      <span class="text-[#38BDF8] font-semibold">Carga activa</span>
    </div>
  </div>

  <!-- Card 3: Energía Comprada a la Red -->
  <div class="bg-[#111C2A] p-5 rounded-xl border border-[#1C2E42] hover:border-[#243B55] shadow-lg relative overflow-hidden transition-all group">
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">Comprada a la Red</span>
      <div class="w-8 h-8 rounded-lg bg-[#EF4444]/15 text-[#EF4444] flex items-center justify-center border border-[#EF4444]/30">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M19 14l-7 7m0 0l-7-7m7 7V3" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
        </svg>
      </div>
    </div>
    <div class="flex items-baseline gap-2">
      <span class="text-3xl font-extrabold text-white font-mono tracking-tight" id="metricGridImport" style="font-size: 2.5rem; line-height: 1;">0.00</span>
      <span class="text-xs font-semibold text-[#94A3B8]">kWh</span>
    </div>
    <div class="mt-3 flex items-center justify-between text-xs pt-3 border-t border-[#1C2E42]">
      <span class="text-[#94A3B8]" id="totalGridLabel">Total compra: {totales['energia_comprada']} kWh</span>
      <span class="font-semibold" id="metricGridStatus">0% (Autosuficiente)</span>
    </div>
  </div>

  <!-- Card 4: Energía Vertida -->
  <div class="bg-[#111C2A] p-5 rounded-xl border border-[#1C2E42] hover:border-[#243B55] shadow-lg relative overflow-hidden transition-all group">
    <div class="flex items-center justify-between mb-3">
      <span class="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">Energía Vertida</span>
      <div class="w-8 h-8 rounded-lg bg-[#EAB308]/15 text-[#EAB308] flex items-center justify-center border border-[#EAB308]/30">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path d="M5 10l7-7m0 0l7 7m-7-7v18" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
        </svg>
      </div>
    </div>
    <div class="flex items-baseline gap-2">
      <span class="text-3xl font-extrabold text-white font-mono tracking-tight" id="metricSurplus" style="font-size: 2.5rem; line-height: 1;">0.00</span>
      <span class="text-xs font-semibold text-[#94A3B8]">kWh</span>
    </div>
    <div class="mt-3 flex items-center justify-between text-xs pt-3 border-t border-[#1C2E42]">
      <span class="text-[#94A3B8]" id="totalSurplusLabel">Total vertido: {totales['energia_vertida']} kWh</span>
      <span class="text-[#EAB308] font-semibold" id="metricSurplusStatus">Sin excedente</span>
    </div>
  </div>
</section>

<!-- LAS DOS VISUALIZACIONES PRINCIPALES: FLUJO & BATERÍA -->
<div class="grid grid-cols-1 md:grid-cols-12 gap-6">

  <!-- VISUALIZACIÓN 1: DIAGRAMA DE FLUJO ENERGÉTICO (7 cols on md+) -->
  <section class="md:col-span-7 bg-[#111C2A] rounded-xl border border-[#1C2E42] p-6 shadow-xl flex flex-col justify-between">
    <div>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-base font-bold text-white tracking-tight">1. Diagrama de flujo de energía</h2>
          <p class="text-xs text-[#94A3B8]">Distribución energética en tiempo real entre fuentes, acumulador y cargas</p>
        </div>
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[11px] font-semibold bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 shadow-[0_0_8px_rgba(16,185,129,0.2)]">
            <span class="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-ping"></span>
            Vector activo
          </span>
        </div>
      </div>

      <!-- Flow Diagram Canvas SVG Area -->
      <div class="relative w-full h-[330px] bg-[#0D1726] rounded-xl border border-[#1C2E42] overflow-hidden flex items-center justify-center p-4 shadow-inner">
        <!-- Background grid pattern -->
        <svg class="absolute inset-0 w-full h-full opacity-25 pointer-events-none" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern height="24" id="grid" patternUnits="userSpaceOnUse" width="24">
              <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#243B55" stroke-width="0.8"></path>
            </pattern>
          </defs>
          <rect fill="url(#grid)" height="100%" width="100%"></rect>
        </svg>

        <!-- Interactive SVG Connectors (viewBox: 600 x 320) -->
        <svg class="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="xMidYMid meet" viewBox="0 0 600 320">
          <defs>
            <marker id="arrow-green" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="6" refY="5" viewBox="0 0 10 10">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#10B981"></path>
            </marker>
            <marker id="arrow-blue" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="6" refY="5" viewBox="0 0 10 10">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#38BDF8"></path>
            </marker>
            <marker id="arrow-orange" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="6" refY="5" viewBox="0 0 10 10">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#EF4444"></path>
            </marker>
            <marker id="arrow-yellow" markerHeight="6" markerWidth="6" orient="auto-start-reverse" refX="6" refY="5" viewBox="0 0 10 10">
              <path d="M 0 1 L 10 5 L 0 9 z" fill="#EAB308"></path>
            </marker>
          </defs>

          <!-- PATH 1: Solar -> Load (Sol -> Carga) -->
          <path class="flow-active glow-green transition-all duration-300" d="M 154 70 C 198 70, 215 145, 246 150" fill="none" id="pathSolarLoad" marker-end="url(#arrow-green)" stroke="#10B981" stroke-linecap="round" stroke-width="3"></path>
          <!-- PATH 2: Solar -> Battery (Sol -> Batería) -->
          <path class="flow-active glow-green transition-all duration-300" d="M 108 105 L 108 215" fill="none" id="pathSolarBattery" marker-end="url(#arrow-green)" stroke="#10B981" stroke-linecap="round" stroke-width="3"></path>
          <!-- PATH 3: Battery -> Load (Batería -> Carga) -->
          <path class="transition-all duration-300 opacity-20" d="M 154 250 C 198 250, 215 175, 246 170" fill="none" id="pathBatteryLoad" marker-end="url(#arrow-blue)" stroke="#38BDF8" stroke-linecap="round" stroke-width="3"></path>
          <!-- PATH 4: Grid -> Load (Red -> Carga) -->
          <path class="transition-all duration-300 opacity-20" d="M 446 160 L 354 160" fill="none" id="pathGridLoad" marker-end="url(#arrow-orange)" stroke="#EF4444" stroke-linecap="round" stroke-width="3"></path>
          <!-- PATH 5: Surplus -> Grid (Vertido de energía: Carga hacia Red) -->
          <path class="flow-active glow-yellow transition-all duration-300" d="M 354 142 C 384 95, 416 95, 446 142" fill="none" id="pathSurplusGrid" marker-end="url(#arrow-yellow)" stroke="#EAB308" stroke-linecap="round" stroke-width="3"></path>
        </svg>

        <!-- Flow Values Labels Overlaid on Canvas (z-30 to always stay on top and in free space) -->
        <!-- badgeSolarLoad: punto medio del arco Sol->Carga (aprox 34% horiz, 25% vert = sobre la curva media superior) -->
        <div class="absolute left-[34%] top-[23%] transform -translate-x-1/2 -translate-y-1/2 bg-[#0E1626] px-2.5 py-0.5 rounded-full border border-[#10B981] shadow-lg text-[10px] font-mono font-bold text-[#10B981] z-30 transition-opacity pointer-events-none whitespace-nowrap" id="badgeSolarLoad">0.00 kWh</div>
        <!-- badgeSolarBattery: a la derecha del canal vertical Sol->Bat para no tapar ninguna tarjeta -->
        <div class="absolute left-[26%] top-[50%] transform -translate-x-1/2 -translate-y-1/2 bg-[#0E1626] px-2.5 py-0.5 rounded-full border border-[#10B981] shadow-lg text-[10px] font-mono font-bold text-[#10B981] z-30 transition-opacity pointer-events-none whitespace-nowrap" id="badgeSolarBattery">0.00 kWh</div>
        <!-- badgeBatteryLoad: punto medio del arco Bat->Carga, desplazado hacia arriba para separarlo de la tarjeta -->
        <div class="absolute left-[35%] top-[80%] transform -translate-x-1/2 -translate-y-1/2 bg-[#0E1626] px-2.5 py-0.5 rounded-full border border-[#38BDF8] shadow-lg text-[10px] font-mono font-bold text-[#38BDF8] z-30 opacity-0 transition-opacity pointer-events-none whitespace-nowrap" id="badgeBatteryLoad">0.00 kWh</div>
        <!-- badgeGridLoad: a mitad del segmento Red->Carga (66% horiz), centrado verticalmente pero bajo (68%) -->
        <div class="absolute left-[66%] top-[68%] transform -translate-x-1/2 -translate-y-1/2 bg-[#0E1626] px-2.5 py-0.5 rounded-full border border-[#EF4444] shadow-lg text-[10px] font-mono font-bold text-[#EF4444] z-30 opacity-0 transition-opacity pointer-events-none whitespace-nowrap" id="badgeGridLoad">0.00 kWh</div>
        <!-- badgeSurplusGrid: a mitad del arco Carga->Red (65% horiz, 18% vert = sobre el arco superior) -->
        <div class="absolute left-[66%] top-[18%] transform -translate-x-1/2 -translate-y-1/2 bg-[#0E1626] px-2.5 py-0.5 rounded-full border border-[#EAB308] shadow-lg text-[10px] font-mono font-bold text-[#EAB308] z-30 opacity-0 transition-opacity pointer-events-none whitespace-nowrap" id="badgeSurplusGrid">0.00 kWh</div>

        <!-- 4 Entities Nodes (z-20, balanced positions at 18%, 50%, 82% to prevent any border clipping) -->
        <div class="absolute left-[18%] top-[22%] -translate-x-1/2 -translate-y-1/2 w-[92px] sm:w-[98px] bg-[#0E1626]/95 backdrop-blur-md p-2 rounded-xl border border-[#10B981]/40 shadow-lg shadow-emerald-950/20 flex flex-col items-center text-center transition-all z-20">
          <div class="w-7 h-7 rounded-lg bg-[#10B981]/15 text-[#10B981] flex items-center justify-center mb-1 border border-[#10B981]/30">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
          <span class="text-[10px] font-bold text-slate-200 tracking-tight">Paneles Solares</span>
          <span class="text-[10px] font-mono font-bold text-[#10B981]" id="nodeSolarVal">0.00 kW</span>
        </div>

        <div class="absolute left-[18%] top-[78%] -translate-x-1/2 -translate-y-1/2 w-[92px] sm:w-[98px] bg-[#0E1626]/95 backdrop-blur-md p-2 rounded-xl border border-[#38BDF8]/40 shadow-lg shadow-sky-950/20 flex flex-col items-center text-center transition-all z-20">
          <div class="w-7 h-7 rounded-lg bg-[#38BDF8]/15 text-[#38BDF8] flex items-center justify-center mb-1 border border-[#38BDF8]/30">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M13 10V3L4 14h7v7l9-11h-7z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
          <span class="text-[10px] font-bold text-slate-200 tracking-tight">Almacén</span>
          <span class="text-[10px] font-mono font-bold text-[#38BDF8]" id="nodeBatteryVal">En espera</span>
        </div>

        <div class="absolute left-[50%] top-[50%] -translate-x-1/2 -translate-y-1/2 w-[104px] sm:w-[112px] bg-[#0E1626]/95 backdrop-blur-md p-2 rounded-xl border-2 border-[#38BDF8]/60 shadow-[0_0_20px_rgba(56,189,248,0.25)] flex flex-col items-center text-center transition-all z-20">
          <div class="w-7 h-7 rounded-lg bg-[#38BDF8]/20 text-[#38BDF8] flex items-center justify-center mb-1 border border-[#38BDF8]/40">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
          <span class="text-[10px] font-bold text-white tracking-tight">Carga Eléctrica</span>
          <span class="text-[10px] font-mono font-bold text-gray-200" id="nodeDemandVal">0.00 kW</span>
        </div>

        <div class="absolute left-[82%] top-[50%] -translate-x-1/2 -translate-y-1/2 w-[92px] sm:w-[98px] bg-[#0E1626]/95 backdrop-blur-md p-2 rounded-xl border border-[#EAB308]/40 shadow-lg shadow-amber-950/20 flex flex-col items-center text-center transition-all z-20">
          <div class="w-7 h-7 rounded-lg bg-[#142132] text-[#EAB308] flex items-center justify-center mb-1 border border-[#EAB308]/30">
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
          </div>
          <span class="text-[10px] font-bold text-slate-200 tracking-tight">Red Externa</span>
          <span class="text-[10px] font-mono font-bold text-[#EAB308]" id="nodeGridVal">En equilibrio</span>
        </div>
      </div>

      <!-- Flow Legend -->
      <div class="mt-4 flex flex-wrap items-center justify-between gap-2 text-xs text-[#94A3B8] border-t border-[#1C2E42] pt-3">
        <div class="flex items-center gap-4 flex-wrap">
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-[#10B981] shadow-[0_0_6px_#10B981]"></span>
            <span class="text-gray-300">Solar Directo</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-[#38BDF8] shadow-[0_0_6px_#38BDF8]"></span>
            <span class="text-gray-300">Batería</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-[#EF4444] shadow-[0_0_6px_#EF4444]"></span>
            <span class="text-gray-300">Red Importada</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-2.5 h-2.5 rounded-full bg-[#EAB308] shadow-[0_0_6px_#EAB308]"></span>
            <span class="text-gray-300">Vertido</span>
          </div>
        </div>
        <span class="text-[11px] font-mono text-[#64748B]">Dirección: Flechas animadas</span>
      </div>
    </div>
  </section>

  <!-- VISUALIZACIÓN 2: INDICADOR DE ESTADO DE LA BATERÍA (5 cols on md+) -->
  <section class="md:col-span-5 bg-[#111C2A] rounded-xl border border-[#1C2E42] p-6 shadow-xl flex flex-col justify-between">
    <div>
      <div class="flex items-center justify-between mb-4">
        <div>
          <h2 class="text-base font-bold text-white tracking-tight">2. Indicador de batería</h2>
          <p class="text-xs text-[#94A3B8]">Nivel de almacenamiento y autonomía energética</p>
        </div>
        <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/40 shadow-[0_0_8px_rgba(16,185,129,0.2)]" id="batteryStatusPill">Carga Óptima</span>
      </div>

      <!-- Large Dynamic Battery Graphic -->
      <div class="bg-[#0D1726] p-5 rounded-xl border border-[#1C2E42] flex flex-col items-center justify-center shadow-inner">
        <div class="relative w-56 flex items-center justify-center my-3">
          <div class="w-48 h-24 rounded-2xl border-4 border-gray-400 p-1.5 relative flex items-center bg-[#070D14] shadow-[inset_0_2px_8px_rgba(0,0,0,0.8)]">
            <div class="absolute -right-3.5 top-1/2 -translate-y-1/2 w-2.5 h-10 bg-gray-400 rounded-r-md"></div>
            <!-- Dynamic Fill Bar -->
            <div class="h-full rounded-xl transition-all duration-500 ease-out flex items-center justify-center relative overflow-hidden bg-[#10B981] shadow-[0_0_14px_rgba(16,185,129,0.6)]" id="batteryFillBar" style="width: 50%;">
              <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/25 to-transparent"></div>
              <svg class="w-6 h-6 text-white animate-pulse drop-shadow-[0_0_6px_rgba(255,255,255,0.8)]" fill="currentColor" id="batteryChargingIcon" viewBox="0 0 20 20" style="display: none;">
                <path clip-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" fill-rule="evenodd"></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- Battery Numerical Metrics -->
        <div class="w-full mt-3 grid grid-cols-3 gap-2 text-center pt-3 border-t border-[#1C2E42]">
          <div>
            <span class="text-[11px] text-[#94A3B8] block">Almacenado</span>
            <span class="text-lg font-bold font-mono text-white" id="batteryKwhVal">0.0</span>
            <span class="text-[11px] text-[#64748B]">kWh</span>
          </div>
          <div class="border-x border-[#1C2E42]">
            <span class="text-[11px] text-[#94A3B8] block">Porcentaje</span>
            <span class="text-lg font-bold font-mono text-[#10B981]" id="batteryPercentVal">0%</span>
          </div>
          <div>
            <span class="text-[11px] text-[#94A3B8] block">Cap. Máxima</span>
            <span class="text-lg font-bold font-mono text-white" id="batteryCapacityVal">{capacidad_max}</span>
            <span class="text-[11px] text-[#64748B]">kWh</span>
          </div>
        </div>

        <div class="w-full mt-3 px-3 py-1.5 rounded-lg bg-[#111C2A] text-[11px] flex items-center justify-between text-[#94A3B8] border border-[#1C2E42]">
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#10B981] shadow-[0_0_4px_#10B981]"></span> &gt;50% Normal</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#EAB308] shadow-[0_0_4px_#EAB308]"></span> 20-50% Precaución</span>
          <span class="flex items-center gap-1.5"><span class="w-2 h-2 rounded-full bg-[#EF4444] shadow-[0_0_4px_#EF4444]"></span> &lt;20% Crítico</span>
        </div>
      </div>
    </div>

    <!-- Simulation Controls -->
    <div class="mt-5 space-y-3 pt-3 border-t border-[#1C2E42]">
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">Control de Simulación</span>
        <span class="text-xs font-bold font-mono px-2.5 py-0.5 rounded bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30" id="selectedHourDisplay">Hora 1</span>
      </div>

      <!-- Slider -->
      <div class="relative pt-1">
        <input aria-label="Seleccionar hora" class="w-full cursor-pointer" id="hourSlider" max="{totales['horas_simuladas'] - 1}" min="0" type="range" value="0">
        <div class="flex justify-between text-[10px] text-[#64748B] font-mono mt-1" id="sliderTicks">
          <span>00:00</span>
          <span>12:00</span>
          <span>Fin</span>
        </div>
      </div>

      <!-- Play & Pause Buttons -->
      <div class="flex items-center gap-2 pt-1">
        <button class="flex-1 py-2 px-3 rounded-lg bg-[#3988D6] hover:bg-[#2e73b8] text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-all shadow-md cursor-pointer" id="playBtn">
          <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M4.5 3.5v13l11-6.5-11-6.5z"></path></svg>
          <span>Reproducir</span>
        </button>
        <button class="flex-1 py-2 px-3 rounded-lg bg-[#162436] hover:bg-[#1C2E42] text-gray-200 text-xs font-semibold flex items-center justify-center gap-1.5 transition-all border border-[#1C2E42] cursor-pointer" id="pauseBtn">
          <svg class="w-4 h-4 fill-current" viewBox="0 0 20 20"><path d="M5 4h3v12H5V4zm7 0h3v12h-3V4z"></path></svg>
          <span>Pausar</span>
        </button>
        <button class="p-2 rounded-lg bg-[#162436] hover:bg-[#1C2E42] text-gray-200 text-xs font-semibold transition-all border border-[#1C2E42] cursor-pointer" id="stepNextBtn" title="Hora siguiente">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M13 5l7 7-7 7M5 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path></svg>
        </button>
      </div>
    </div>
  </section>
</div>

<!-- VISUALIZACIÓN 3: LÍNEA DE TIEMPO ENERGÉTICA (N Horas) -->
<section class="bg-[#111C2A] rounded-xl border border-[#1C2E42] p-6 shadow-xl">
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
    <div>
      <h2 class="text-base font-bold text-white tracking-tight">3. Línea de tiempo con alertas ({totales['horas_simuladas']} Horas)</h2>
      <p class="text-xs text-[#94A3B8]">Comportamiento de la microrred celda por celda</p>
    </div>
    <!-- Legend -->
    <div class="flex items-center gap-3 text-xs flex-wrap">
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-[#10B981] shadow-[0_0_4px_#10B981]"></span>
        <span class="text-gray-300">Carga batería</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-[#38BDF8] shadow-[0_0_4px_#38BDF8]"></span>
        <span class="text-gray-300">Descarga batería</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-[#EF4444] shadow-[0_0_4px_#EF4444]"></span>
        <span class="text-gray-300">Compra red</span>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-3 h-3 rounded bg-[#EAB308] shadow-[0_0_4px_#EAB308]"></span>
        <span class="text-gray-300">Vertido</span>
      </div>
    </div>
  </div>

  <!-- Dynamic N Cells Grid -->
  <div class="overflow-x-auto pb-2">
    <div class="grid gap-1.5 min-w-[700px] py-1" id="timelineContainer"></div>
  </div>

  <!-- ALERTS SECTION & HOURLY BREAKDOWN -->
  <div class="mt-4 pt-4 border-t border-[#1C2E42] flex flex-col md:flex-row items-center justify-between gap-4" id="alertsContainer">
    <div class="flex items-center gap-2">
      <span class="text-xs font-bold uppercase tracking-wider text-[#94A3B8]">Alertas de la hora:</span>
      <div class="flex items-center gap-2 flex-wrap" id="alertBadgeList"></div>
    </div>
    <div class="text-xs text-[#94A3B8] font-mono">
      Selección activa: <span class="font-bold text-white" id="alertSelectedHourText">Hora 01</span>
    </div>
  </div>

  <!-- RESUMEN DE RESULTADOS (Summary Metrics Bar) -->
  <div class="mt-4 p-4 rounded-xl bg-[#0D1726] border border-[#1C2E42] grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
    <div>
      <span class="text-[11px] text-[#94A3B8] block">Total Cargado</span>
      <span class="text-base font-bold font-mono text-[#10B981]" id="statTotalCargado">{totales['total_cargado']} kWh</span>
    </div>
    <div>
      <span class="text-[11px] text-[#94A3B8] block">Total Descargado</span>
      <span class="text-base font-bold font-mono text-[#38BDF8]" id="statTotalDescargado">{totales['total_descargado']} kWh</span>
    </div>
    <div>
      <span class="text-[11px] text-[#94A3B8] block">Energía Comprada</span>
      <span class="text-base font-bold font-mono text-[#EF4444]" id="statTotalComprada">{totales['energia_comprada']} kWh</span>
    </div>
    <div>
      <span class="text-[11px] text-[#94A3B8] block">Energía Vertida</span>
      <span class="text-base font-bold font-mono text-[#EAB308]" id="statTotalVertida">{totales['energia_vertida']} kWh</span>
    </div>
    <div class="col-span-2 sm:col-span-1 border-t sm:border-t-0 sm:border-l border-[#1C2E42] sm:pl-4">
      <span class="text-[11px] text-[#94A3B8] block">Cubierto sin red</span>
      <span class="text-base font-bold font-mono text-[#10B981]" id="statCubiertoSinRed">{totales['porcentaje_sin_red']}%</span>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer class="flex flex-col sm:flex-row items-center justify-between text-xs text-[#64748B] pt-2 pb-6 px-1 border-t border-[#1C2E42]">
  <p>MICROGRID v2.4 · Laboratorio de Simulación de Energías Renovables · Ingeniería Energética</p>
  <p class="font-mono mt-1 sm:mt-0 text-[#94A3B8]">Diseñado para proyección en aula y despliegue modular con Streamlit</p>
</footer>

</main>

<!-- JAVASCRIPT: Simulation State, Hourly Model, Dynamic Connections -->
<script>
    const allScenarios = {json_scenarios};
    let currentScenarioKey = "{initial_scenario_key}";
    let hourlyData = allScenarios[currentScenarioKey].horas;
    let totales = allScenarios[currentScenarioKey].totales;
    let batteryCapacity = allScenarios[currentScenarioKey].capacidad;

    let currentHour = 0;
    let isPlaying = false;
    let timer = null;

    // DOM Elements
    const slider = document.getElementById('hourSlider');
    const selectedHourDisplay = document.getElementById('selectedHourDisplay');
    const topBarTime = document.getElementById('topBarTime');
    const playBtn = document.getElementById('playBtn');
    const pauseBtn = document.getElementById('pauseBtn');
    const stepNextBtn = document.getElementById('stepNextBtn');
    const simDot = document.getElementById('simDot');
    const simModeText = document.getElementById('simModeText');

    // Metrics
    const metricSolar = document.getElementById('metricSolar');
    const metricDemand = document.getElementById('metricDemand');
    const metricGridImport = document.getElementById('metricGridImport');
    const metricGridStatus = document.getElementById('metricGridStatus');
    const metricSurplus = document.getElementById('metricSurplus');
    const metricSurplusStatus = document.getElementById('metricSurplusStatus');

    // Battery Elements
    const batteryFillBar = document.getElementById('batteryFillBar');
    const batteryKwhVal = document.getElementById('batteryKwhVal');
    const batteryPercentVal = document.getElementById('batteryPercentVal');
    const batteryCapacityVal = document.getElementById('batteryCapacityVal');
    const batteryStatusPill = document.getElementById('batteryStatusPill');
    const batteryChargingIcon = document.getElementById('batteryChargingIcon');

    // Flow Paths and Badges
    const pathSolarLoad = document.getElementById('pathSolarLoad');
    const pathSolarBattery = document.getElementById('pathSolarBattery');
    const pathBatteryLoad = document.getElementById('pathBatteryLoad');
    const pathGridLoad = document.getElementById('pathGridLoad');
    const pathSurplusGrid = document.getElementById('pathSurplusGrid');

    const badgeSolarLoad = document.getElementById('badgeSolarLoad');
    const badgeSolarBattery = document.getElementById('badgeSolarBattery');
    const badgeBatteryLoad = document.getElementById('badgeBatteryLoad');
    const badgeGridLoad = document.getElementById('badgeGridLoad');
    const badgeSurplusGrid = document.getElementById('badgeSurplusGrid');

    const nodeSolarVal = document.getElementById('nodeSolarVal');
    const nodeBatteryVal = document.getElementById('nodeBatteryVal');
    const nodeDemandVal = document.getElementById('nodeDemandVal');
    const nodeGridVal = document.getElementById('nodeGridVal');

    const timelineContainer = document.getElementById('timelineContainer');
    const alertBadgeList = document.getElementById('alertBadgeList');
    const alertSelectedHourText = document.getElementById('alertSelectedHourText');

    // Switch scenario in real-time with zero flicker
    function switchScenario(key) {{
      if (key === currentScenarioKey) return;
      currentScenarioKey = key;
      const scen = allScenarios[key];
      if (!scen) return;

      const btnRural = document.getElementById('scenarioBtnRural');
      const btnVerif = document.getElementById('scenarioBtnVerif');
      if (btnRural && btnVerif) {{
        if (key === 'rural') {{
          btnRural.className = 'px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 bg-[#10B981]/20 text-[#10B981] border border-[#10B981]/40 shadow-sm';
          btnVerif.className = 'px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 text-[#94A3B8] hover:text-white hover:bg-[#162436] border border-transparent';
        }} else {{
          btnVerif.className = 'px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 bg-amber-400/20 text-amber-300 border border-amber-400/40 shadow-sm';
          btnRural.className = 'px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 text-[#94A3B8] hover:text-white hover:bg-[#162436] border border-transparent';
        }}
      }}

      hourlyData = scen.horas;
      totales = scen.totales;
      batteryCapacity = scen.capacidad;

      const microrredLabel = document.getElementById('microrredLabel');
      if (microrredLabel) microrredLabel.textContent = scen.name;

      const totalSolarLabel = document.getElementById('totalSolarLabel');
      if (totalSolarLabel) totalSolarLabel.textContent = `Total día: ${{totales.total_generacion}} kWh`;

      const totalDemandLabel = document.getElementById('totalDemandLabel');
      if (totalDemandLabel) totalDemandLabel.textContent = `Total demanda: ${{totales.total_demanda}} kWh`;

      const totalGridLabel = document.getElementById('totalGridLabel');
      if (totalGridLabel) totalGridLabel.textContent = `Total compra: ${{totales.energia_comprada}} kWh`;

      const totalSurplusLabel = document.getElementById('totalSurplusLabel');
      if (totalSurplusLabel) totalSurplusLabel.textContent = `Total vertido: ${{totales.energia_vertida}} kWh`;

      if (batteryCapacityVal) batteryCapacityVal.textContent = batteryCapacity.toFixed(1);

      const statTotalCargado = document.getElementById('statTotalCargado');
      if (statTotalCargado) statTotalCargado.textContent = `${{totales.total_cargado}} kWh`;

      const statTotalDescargado = document.getElementById('statTotalDescargado');
      if (statTotalDescargado) statTotalDescargado.textContent = `${{totales.total_descargado}} kWh`;

      const statTotalComprada = document.getElementById('statTotalComprada');
      if (statTotalComprada) statTotalComprada.textContent = `${{totales.energia_comprada}} kWh`;

      const statTotalVertida = document.getElementById('statTotalVertida');
      if (statTotalVertida) statTotalVertida.textContent = `${{totales.energia_vertida}} kWh`;

      const statCubiertoSinRed = document.getElementById('statCubiertoSinRed');
      if (statCubiertoSinRed) statCubiertoSinRed.textContent = `${{totales.porcentaje_sin_red}}%`;

      slider.max = hourlyData.length - 1;
      const sliderTicks = document.getElementById('sliderTicks');
      if (sliderTicks) {{
        if (hourlyData.length <= 4) {{
          sliderTicks.innerHTML = '<span>H1</span><span>H2</span><span>H3</span><span>H4</span>';
        }} else {{
          sliderTicks.innerHTML = '<span>00:00</span><span>12:00</span><span>Fin</span>';
        }}
      }}

      pauseSimulation();
      initTimeline();
      updateHour(0);
      autoResizeFrame();
    }}

    // Initialize the timeline buttons dynamically
    function initTimeline() {{
      timelineContainer.innerHTML = '';
      const totalH = hourlyData.length;
      timelineContainer.style.gridTemplateColumns = `repeat(${{totalH}}, minmax(0, 1fr))`;

      hourlyData.forEach((d) => {{
        const btn = document.createElement('button');
        btn.id = `cell-h-${{d.h}}`;
        
        let actColor = 'bg-[#10B981]'; // charge
        if (d.act === 'descarga' || d.act === 'discharge') {{ actColor = 'bg-[#38BDF8]'; }}
        if (d.act === 'grid') {{ actColor = 'bg-[#EF4444]'; }}
        if (d.act === 'surplus') {{ actColor = 'bg-[#EAB308]'; }}

        const isCurrent = d.h === currentHour;
        btn.className = `flex flex-col items-center justify-between p-1.5 rounded-lg border transition-all cursor-pointer h-20 text-center ${{
          isCurrent 
            ? 'ring-2 ring-[#38BDF8] border-[#38BDF8] bg-[#162436] shadow-lg shadow-[#38BDF8]/20 scale-105 z-10 font-bold' 
            : 'bg-[#0D1726] border-[#1C2E42] opacity-80 hover:opacity-100 hover:border-[#243B55]'
        }}`;

        btn.innerHTML = `
          <span class="text-[10px] font-mono text-[#94A3B8]">H${{d.h + 1}}</span>
          <div class="w-full h-2 rounded-full ${{actColor}} my-1 shadow-sm"></div>
          <span class="text-[9px] font-mono font-semibold text-gray-200 truncate w-full">${{d.solar > 0 ? d.solar.toFixed(1) : d.demand.toFixed(1)}}k</span>
        `;

        btn.addEventListener('click', () => {{
          pauseSimulation();
          updateHour(d.h);
        }});

        timelineContainer.appendChild(btn);
      }});
    }}

    // Update screen state for selected hour
    function updateHour(hour) {{
      currentHour = parseInt(hour, 10);
      if (currentHour < 0) currentHour = 0;
      if (currentHour >= hourlyData.length) currentHour = hourlyData.length - 1;

      const data = hourlyData[currentHour];
      if (!data) return;

      // Update Slider and Labels
      slider.value = currentHour;
      const formattedTime = `Hora ${{currentHour + 1}} (${{currentHour.toString().padStart(2, '0')}}:00 h)`;
      selectedHourDisplay.textContent = `Hora ${{currentHour + 1}} de ${{hourlyData.length}}`;
      topBarTime.textContent = `${{currentHour.toString().padStart(2, '0')}}:00 h`;
      alertSelectedHourText.textContent = formattedTime;

      // Update Top Metrics
      metricSolar.textContent = data.solar.toFixed(2);
      metricDemand.textContent = data.demand.toFixed(2);
      metricGridImport.textContent = data.flowGridLoad.toFixed(2);
      metricSurplus.textContent = data.flowSurplus.toFixed(2);

      if (data.flowGridLoad > 0) {{
        metricGridStatus.textContent = `Faltan ${{data.flowGridLoad.toFixed(2)}} kWh (Red)`;
        metricGridStatus.className = 'text-[#EF4444] font-semibold';
      }} else {{
        metricGridStatus.textContent = '0% (Autosuficiente)';
        metricGridStatus.className = 'text-[#10B981] font-semibold';
      }}

      if (data.flowSurplus > 0) {{
        metricSurplusStatus.textContent = `Vierte ${{data.flowSurplus.toFixed(2)}} kWh`;
        metricSurplusStatus.className = 'text-[#EAB308] font-semibold';
      }} else {{
        metricSurplusStatus.textContent = 'Sin excedente';
        metricSurplusStatus.className = 'text-[#64748B] font-medium';
      }}

      // Update Battery Indicator
      batteryKwhVal.textContent = data.battKwh.toFixed(1);
      batteryPercentVal.textContent = `${{data.battPct}}%`;
      batteryFillBar.style.width = `${{Math.max(4, data.battPct)}}%`;

      batteryFillBar.classList.remove('bg-[#10B981]', 'bg-[#EAB308]', 'bg-[#EF4444]', 'shadow-[0_0_14px_rgba(16,185,129,0.6)]', 'shadow-[0_0_14px_rgba(234,179,8,0.6)]', 'shadow-[0_0_14px_rgba(239,68,68,0.6)]');
      batteryPercentVal.classList.remove('text-[#10B981]', 'text-[#EAB308]', 'text-[#EF4444]');

      if (data.battPct > 50) {{
        batteryFillBar.classList.add('bg-[#10B981]', 'shadow-[0_0_14px_rgba(16,185,129,0.6)]');
        batteryPercentVal.classList.add('text-[#10B981]');
        batteryStatusPill.textContent = 'Carga Óptima';
        batteryStatusPill.className = 'text-xs font-semibold px-2.5 py-1 rounded-full bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/40 shadow-[0_0_8px_rgba(16,185,129,0.2)]';
      }} else if (data.battPct >= 20) {{
        batteryFillBar.classList.add('bg-[#EAB308]', 'shadow-[0_0_14px_rgba(234,179,8,0.6)]');
        batteryPercentVal.classList.add('text-[#EAB308]');
        batteryStatusPill.textContent = 'Nivel Medio';
        batteryStatusPill.className = 'text-xs font-semibold px-2.5 py-1 rounded-full bg-[#EAB308]/15 text-[#EAB308] border border-[#EAB308]/40 shadow-[0_0_8px_rgba(234,179,8,0.2)]';
      }} else {{
        batteryFillBar.classList.add('bg-[#EF4444]', 'shadow-[0_0_14px_rgba(239,68,68,0.6)]');
        batteryPercentVal.classList.add('text-[#EF4444]');
        batteryStatusPill.textContent = 'Batería Baja / Vacía';
        batteryStatusPill.className = 'text-xs font-semibold px-2.5 py-1 rounded-full bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/40 shadow-[0_0_8px_rgba(239,68,68,0.2)]';
      }}

      if (data.flowSolBatt > 0) {{
        batteryChargingIcon.style.display = 'block';
      }} else {{
        batteryChargingIcon.style.display = 'none';
      }}

      // Update Flow Nodes Text
      nodeSolarVal.textContent = `${{data.solar.toFixed(2)}} kW`;
      nodeDemandVal.textContent = `${{data.demand.toFixed(2)}} kW`;

      if (data.flowSolBatt > 0) {{
        nodeBatteryVal.textContent = `Cargando (+${{data.flowSolBatt.toFixed(1)}})`;
        nodeBatteryVal.className = 'text-[11px] font-mono font-semibold text-[#10B981]';
      }} else if (data.flowBattLoad > 0) {{
        nodeBatteryVal.textContent = `Descarga (-${{data.flowBattLoad.toFixed(1)}})`;
        nodeBatteryVal.className = 'text-[11px] font-mono font-semibold text-[#38BDF8]';
      }} else {{
        nodeBatteryVal.textContent = 'En espera (0.0)';
        nodeBatteryVal.className = 'text-[11px] font-mono font-semibold text-[#64748B]';
      }}

      if (data.flowSurplus > 0) {{
        nodeGridVal.textContent = `Vertiendo (${{data.flowSurplus.toFixed(1)}})`;
        nodeGridVal.className = 'text-[11px] font-mono font-semibold text-[#EAB308]';
      }} else if (data.flowGridLoad > 0) {{
        nodeGridVal.textContent = `Comprando (${{data.flowGridLoad.toFixed(1)}})`;
        nodeGridVal.className = 'text-[11px] font-mono font-semibold text-[#EF4444]';
      }} else {{
        nodeGridVal.textContent = 'En equilibrio';
        nodeGridVal.className = 'text-[11px] font-mono font-semibold text-[#10B981]';
      }}

      // Update Flow Connectors & Badges with animated dashed stroke
      if (data.flowSolLoad > 0) {{
        pathSolarLoad.classList.add('flow-active', 'glow-green');
        pathSolarLoad.style.opacity = '1';
        badgeSolarLoad.style.opacity = '1';
        badgeSolarLoad.textContent = `${{data.flowSolLoad.toFixed(2)}} kWh`;
      }} else {{
        pathSolarLoad.classList.remove('flow-active', 'glow-green');
        pathSolarLoad.style.opacity = '0.15';
        badgeSolarLoad.style.opacity = '0';
      }}

      if (data.flowSolBatt > 0) {{
        pathSolarBattery.classList.add('flow-active', 'glow-green');
        pathSolarBattery.style.opacity = '1';
        badgeSolarBattery.style.opacity = '1';
        badgeSolarBattery.textContent = `${{data.flowSolBatt.toFixed(2)}} kWh`;
      }} else {{
        pathSolarBattery.classList.remove('flow-active', 'glow-green');
        pathSolarBattery.style.opacity = '0.15';
        badgeSolarBattery.style.opacity = '0';
      }}

      if (data.flowBattLoad > 0) {{
        pathBatteryLoad.classList.add('flow-active', 'glow-blue');
        pathBatteryLoad.style.opacity = '1';
        badgeBatteryLoad.style.opacity = '1';
        badgeBatteryLoad.textContent = `${{data.flowBattLoad.toFixed(2)}} kWh`;
      }} else {{
        pathBatteryLoad.classList.remove('flow-active', 'glow-blue');
        pathBatteryLoad.style.opacity = '0.15';
        badgeBatteryLoad.style.opacity = '0';
      }}

      if (data.flowGridLoad > 0) {{
        pathGridLoad.classList.add('flow-active');
        pathGridLoad.style.opacity = '1';
        badgeGridLoad.style.opacity = '1';
        badgeGridLoad.textContent = `${{data.flowGridLoad.toFixed(2)}} kWh`;
      }} else {{
        pathGridLoad.classList.remove('flow-active');
        pathGridLoad.style.opacity = '0.15';
        badgeGridLoad.style.opacity = '0';
      }}

      if (data.flowSurplus > 0) {{
        pathSurplusGrid.classList.add('flow-active', 'glow-yellow');
        pathSurplusGrid.style.opacity = '1';
        badgeSurplusGrid.style.opacity = '1';
        badgeSurplusGrid.textContent = `${{data.flowSurplus.toFixed(2)}} kWh`;
      }} else {{
        pathSurplusGrid.classList.remove('flow-active', 'glow-yellow');
        pathSurplusGrid.style.opacity = '0.15';
        badgeSurplusGrid.style.opacity = '0';
      }}

      // Timeline cell active highlights
      for (let i = 0; i < hourlyData.length; i++) {{
        const cell = document.getElementById(`cell-h-${{i}}`);
        if (cell) {{
          if (i === currentHour) {{
            cell.className = 'flex flex-col items-center justify-between p-1.5 rounded-lg border-2 border-[#38BDF8] bg-[#162436] shadow-lg shadow-[#38BDF8]/20 scale-105 z-10 font-bold transition-all';
          }} else {{
            cell.className = 'flex flex-col items-center justify-between p-1.5 rounded-lg border border-[#1C2E42] bg-[#0D1726] opacity-80 hover:opacity-100 hover:border-[#243B55] transition-all';
          }}
        }}
      }}

      // Alerts list
      alertBadgeList.innerHTML = '';
      let hasAlerts = false;

      if (data.battKwh === 0 && data.flowGridLoad > 0) {{
        hasAlerts = true;
        const b = document.createElement('span');
        b.className = 'inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 font-medium';
        b.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg> Batería agotada (0.0 kWh). Suministro respaldado por red (+${{data.flowGridLoad.toFixed(2)}} kWh).`;
        alertBadgeList.appendChild(b);
      }} else if (data.battPct < 20) {{
        hasAlerts = true;
        const b = document.createElement('span');
        b.className = 'inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-[#EF4444]/15 text-[#EF4444] border border-[#EF4444]/30 font-medium';
        b.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg> Batería baja (${{data.battPct}}%). Consumo restringido recomendado.`;
        alertBadgeList.appendChild(b);
      }}

      if (data.flowSurplus > 0) {{
        hasAlerts = true;
        const b = document.createElement('span');
        b.className = 'inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-[#EAB308]/15 text-[#EAB308] border border-[#EAB308]/30 font-medium';
        b.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg> Excedente vertido: +${{data.flowSurplus.toFixed(2)}} kWh.`;
        alertBadgeList.appendChild(b);
      }}

      if (!hasAlerts) {{
        const b = document.createElement('span');
        b.className = 'inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 font-medium';
        b.innerHTML = `<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Flujo balanceado sin incidencias críticas.`;
        alertBadgeList.appendChild(b);
      }}
    }}

    // Simulation loop
    function playSimulation() {{
      if (isPlaying) return;
      isPlaying = true;
      simDot.className = 'w-1.5 h-1.5 rounded-full bg-[#10B981] animate-ping';
      simModeText.textContent = 'En reproducción';
      playBtn.classList.add('ring-2', 'ring-[#38BDF8]');
      pauseBtn.classList.remove('ring-2', 'ring-[#38BDF8]');

      timer = setInterval(() => {{
        let nextHour = (currentHour + 1) % hourlyData.length;
        updateHour(nextHour);
      }}, 1400);
    }}

    function pauseSimulation() {{
      if (!isPlaying) return;
      isPlaying = false;
      clearInterval(timer);
      simDot.className = 'w-1.5 h-1.5 rounded-full bg-amber-400';
      simModeText.textContent = 'Pausado';
      playBtn.classList.remove('ring-2', 'ring-[#38BDF8]');
      pauseBtn.classList.add('ring-2', 'ring-[#38BDF8]');
    }}

    // Events
    slider.addEventListener('input', (e) => {{
      pauseSimulation();
      updateHour(e.target.value);
    }});

    playBtn.addEventListener('click', playSimulation);
    pauseBtn.addEventListener('click', pauseSimulation);
    stepNextBtn.addEventListener('click', () => {{
      pauseSimulation();
      updateHour((currentHour + 1) % hourlyData.length);
    }});

    // Dark / Light Theme Toggle
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    themeToggleBtn.addEventListener('click', () => {{
      const html = document.documentElement;
      if (html.classList.contains('dark')) {{
        html.classList.remove('dark');
        html.classList.add('light');
      }} else {{
        html.classList.remove('light');
        html.classList.add('dark');
      }}
    }});

    // Auto-ajuste dinámico de altura para diseño continuo
    function autoResizeFrame() {{
      const h = Math.max(
        document.body.scrollHeight,
        document.documentElement.scrollHeight,
        1500
      );
      window.parent.postMessage({{ type: 'streamlit:setFrameHeight', height: h }}, '*');
    }}
    window.addEventListener('load', autoResizeFrame);
    window.addEventListener('resize', autoResizeFrame);
    setTimeout(autoResizeFrame, 200);
    setTimeout(autoResizeFrame, 800);

    // Init
    initTimeline();
    updateHour(0);
    autoResizeFrame();
</script>
</body>
</html>
"""

# Renderizamos el componente HTML dentro de Streamlit con scroll continuo
components.html(html_dashboard, height=1700, scrolling=False)


