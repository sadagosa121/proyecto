"""
================================================================================
MÓDULO DE LÓGICA DE SIMULACIÓN - MICRORRED CON BATERÍA
Asignatura: Fundamentos de Programación (Ingeniería Energética)
================================================================================
Este módulo contiene la lógica matemática y de negocio para simular el
comportamiento horario de una microrred con generación solar, batería, carga
y conexión a red eléctrica externa.

RESTRICCIONES ACADÉMICAS CUMPLIDAS:
- Funciones modulares con return.
- Uso exclusivo de tipos y estructuras vistas en clase:
  números (int, float), listas, diccionarios, ciclos (for/while),
  condicionales (if/elif/else), variables locales y manejo de JSON.
================================================================================
"""

import json


# ------------------------------------------------------------------------------
# 1. CARGA, GUARDADO Y VALIDACIÓN DE DATOS (JSON)
# ------------------------------------------------------------------------------

def cargar_datos(ruta_archivo):
    """
    Lee un archivo JSON con los parámetros de la microrred y el perfil horario.
    Retorna un diccionario con los datos o None si ocurre un error.
    """
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
        return datos
    except Exception as error:
        return {"error": str(error)}


def guardar_resultados(ruta_archivo, resultados):
    """
    Guarda los resultados de la simulación en un archivo JSON formateado.
    Retorna True si fue exitoso o False en caso de error.
    """
    try:
        with open(ruta_archivo, "w", encoding="utf-8") as archivo:
            json.dump(resultados, archivo, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def validar_datos(datos):
    """
    Verifica que los datos cumplan con las reglas de negocio:
    - Capacidad positiva.
    - SOC inicial entre 0 y la capacidad.
    - Valores de generación y carga no negativos.
    - Cantidad de horas (aviso si es diferente de 24).
    Retorna una lista de mensajes (alertas o advertencias) y un booleano (es_valido).
    """
    alertas = []
    es_valido = True

    if not isinstance(datos, dict):
        return ["El formato del archivo no es un diccionario JSON válido."], False

    capacidad = datos.get("capacidad", 0)
    soc_inicial = datos.get("soc_inicial", 0)
    horas = datos.get("horas", [])

    # Validación 1: Capacidad de la batería
    if capacidad <= 0:
        alertas.append("Error crítico: La capacidad de la batería debe ser mayor a 0 kWh.")
        es_valido = False

    # Validación 2: SOC inicial dentro del rango 0 - capacidad
    if soc_inicial < 0:
        alertas.append(f"Alerta: El SOC inicial ({soc_inicial} kWh) es negativo. Se ajustará temporalmente a 0 kWh.")
    elif capacidad > 0 and soc_inicial > capacidad:
        alertas.append(f"Alerta: El SOC inicial ({soc_inicial} kWh) supera la capacidad ({capacidad} kWh). Se ajustará a la capacidad.")

    # Validación 3: Estructura de horas y valores no negativos
    if not isinstance(horas, list) or len(horas) == 0:
        alertas.append("Error crítico: La lista de horas está vacía o no tiene el formato correcto.")
        es_valido = False
    else:
        # Validación de cantidad de horas
        if len(horas) < 24:
            alertas.append(f"Aviso: El perfil contiene {len(horas)} horas (menos del ciclo diario típico de 24 horas).")
        elif len(horas) > 24:
            alertas.append(f"Aviso: El perfil contiene {len(horas)} horas (más de las 24 horas convencionales).")

        # Chequeo de valores por hora
        for i in range(len(horas)):
            par = horas[i]
            if not isinstance(par, (list, tuple)) or len(par) < 2:
                alertas.append(f"Error en la hora {i}: debe ser una lista [generación, carga].")
                es_valido = False
                break
            gen, dem = par[0], par[1]
            if gen < 0:
                alertas.append(f"Alerta en la hora {i}: Generación negativa ({gen} kWh). Se tratará como 0 kWh.")
            if dem < 0:
                alertas.append(f"Alerta en la hora {i}: Demanda negativa ({dem} kWh). Se tratará como 0 kWh.")

    return alertas, es_valido


# ------------------------------------------------------------------------------
# 2. LÓGICA DE SIMULACIÓN HORA A HORA
# ------------------------------------------------------------------------------

def simular_hora(generacion, carga, capacidad, soc_actual, eficiencia=1.0):
    """
    Calcula el balance energético para UNA sola hora según las reglas obligatorias:
    - Si sobra energía: carga la batería hasta su capacidad (afectada por eficiencia si se aplica); lo que no cabe se vierte.
    - Si falta energía: descarga la batería hasta 0 (afectada por eficiencia si se aplica); lo que aún falte se compra a la red.
    Retorna un diccionario con los flujos y el nuevo SOC.
    """
    # Limpieza de valores negativos
    gen = generacion if generacion >= 0 else 0.0
    dem = carga if carga >= 0 else 0.0
    soc = soc_actual if soc_actual >= 0 else 0.0
    if soc > capacidad:
        soc = capacidad

    eta = float(eficiencia) if eficiencia > 0 else 1.0

    sol_carga = 0.0
    sol_bateria = 0.0
    bateria_carga = 0.0
    red_carga = 0.0
    vertido = 0.0
    soc_siguiente = soc
    accion = "equilibrio"  # 'carga', 'descarga', 'grid', 'surplus', 'equilibrio'

    # CASO 1: La generación solar es mayor o igual a la demanda
    if gen >= dem:
        sol_carga = dem
        excedente = gen - dem
        espacio_libre = capacidad - soc
        energia_almacenable = excedente * eta

        if energia_almacenable <= espacio_libre:
            # Todo el excedente puede ser admitido por la batería
            sol_bateria = excedente
            soc_siguiente = soc + energia_almacenable
            vertido = 0.0
            if sol_bateria > 0:
                accion = "carga"
            else:
                accion = "equilibrio"
        else:
            # La batería se llena al 100% y el resto del solar se vierte
            sol_bateria = (espacio_libre / eta) if eta > 0 else espacio_libre
            soc_siguiente = capacidad
            vertido = max(0.0, excedente - sol_bateria)
            accion = "surplus"

    # CASO 2: La generación solar no alcanza para cubrir la demanda
    else:
        sol_carga = gen
        deficit = dem - gen
        energia_necesaria_bateria = (deficit / eta) if eta > 0 else deficit

        if soc >= energia_necesaria_bateria:
            # La batería cubre completamente el déficit
            bateria_carga = deficit
            soc_siguiente = soc - energia_necesaria_bateria
            red_carga = 0.0
            accion = "descarga"
        else:
            # La batería se descarga hasta 0 y el faltante se compra a la red
            bateria_carga = soc * eta
            soc_siguiente = 0.0
            red_carga = max(0.0, deficit - bateria_carga)
            accion = "grid"

    # Redondeo para evitar imprecisiones de coma flotante de Python
    resultado_hora = {
        "solar": round(gen, 3),
        "demand": round(dem, 3),
        "battKwh": round(soc_siguiente, 3),
        "battPct": round((soc_siguiente / capacidad * 100) if capacidad > 0 else 0.0, 1),
        "flowSolLoad": round(sol_carga, 3),
        "flowSolBatt": round(sol_bateria, 3),
        "flowBattLoad": round(bateria_carga, 3),
        "flowGridLoad": round(red_carga, 3),
        "flowSurplus": round(vertido, 3),
        "act": accion
    }

    return resultado_hora


# ------------------------------------------------------------------------------
# 3. SIMULACIÓN COMPLETA DE LA MICRORRED
# ------------------------------------------------------------------------------

def simular_microrred(datos, eficiencia=1.0):
    """
    Ejecuta la simulación para todas las horas provistas en el diccionario 'datos'.
    Permite opcionalmente aplicar eficiencia de carga y descarga (Reto Funcional).
    Retorna una tupla: (lista_horas, totales).
    """
    capacidad = float(datos.get("capacidad", 10.0))
    soc_actual = float(datos.get("soc_inicial", 5.0))
    horas_entrada = datos.get("horas", [])
    eta = float(eficiencia) if eficiencia > 0 else 1.0

    # Ajuste inicial si soc_inicial excede capacidad
    if soc_actual > capacidad:
        soc_actual = capacidad
    elif soc_actual < 0:
        soc_actual = 0.0

    lista_resultados = []

    # Acumuladores de totales
    total_generacion = 0.0
    total_demanda = 0.0
    total_sol_carga = 0.0
    total_cargado_bateria = 0.0
    total_descargado_bateria = 0.0
    total_comprado_red = 0.0
    total_vertido = 0.0

    for i in range(len(horas_entrada)):
        par = horas_entrada[i]
        gen = float(par[0])
        dem = float(par[1])

        # Simular una hora con la eficiencia indicada
        res_hora = simular_hora(gen, dem, capacidad, soc_actual, eficiencia=eta)
        res_hora["h"] = i

        # Actualizar el SOC para la siguiente iteración
        soc_actual = res_hora["battKwh"]

        # Acumular totales
        total_generacion += res_hora["solar"]
        total_demanda += res_hora["demand"]
        total_sol_carga += res_hora["flowSolLoad"]
        total_cargado_bateria += res_hora["flowSolBatt"]
        total_descargado_bateria += res_hora["flowBattLoad"]
        total_comprado_red += res_hora["flowGridLoad"]
        total_vertido += res_hora["flowSurplus"]

        lista_resultados.append(res_hora)

    # Porcentaje de la carga cubierto sin la red:
    # Cubierto sin red = Demanda Total - Compra a la Red
    # Porcentaje = (Cubierto / Demanda Total) * 100
    if total_demanda > 0:
        cubierto_sin_red = total_demanda - total_comprado_red
        porcentaje_sin_red = (cubierto_sin_red / total_demanda) * 100
    else:
        porcentaje_sin_red = 100.0

    totales = {
        "total_generacion": round(total_generacion, 2),
        "total_demanda": round(total_demanda, 2),
        "total_sol_carga": round(total_sol_carga, 2),
        "total_cargado": round(total_cargado_bateria, 2),
        "total_descargado": round(total_descargado_bateria, 2),
        "energia_comprada": round(total_comprado_red, 2),
        "energia_vertida": round(total_vertido, 2),
        "carga_final_bateria": round(soc_actual, 2),
        "porcentaje_sin_red": round(porcentaje_sin_red, 2),
        "capacidad_bateria": capacidad,
        "soc_inicial": float(datos.get("soc_inicial", 5.0)),
        "horas_simuladas": len(horas_entrada)
    }

    return lista_resultados, totales


# ------------------------------------------------------------------------------
# 4. RETO FUNCIONAL (OPCIÓN 1 & OPCIÓN 2 & OPCIÓN 3)
# ------------------------------------------------------------------------------

def buscar_capacidad_minima_sin_red(datos, soc_inicial_relativo=0.5):
    """
    RETO FUNCIONAL 2:
    Encuentra la capacidad mínima de batería requerida (kWh) para que
    la compra a la red eléctrica sea exactamente 0 kWh en el periodo simulado.
    Realiza una búsqueda paso a paso usando un ciclo while con pasos de 0.1 kWh.
    """
    total_gen = 0.0
    total_dem = 0.0
    for par in datos.get("horas", []):
        total_gen += par[0]
        total_dem += par[1]

    # Si la generación total no cubre la demanda total, físicamente es imposible
    # tener 0 compra de red aunque la batería sea infinita.
    if total_gen < total_dem:
        return {
            "posible": False,
            "mensaje": f"Imposible sin red: La generación total ({round(total_gen, 2)} kWh) es menor a la demanda total ({round(total_dem, 2)} kWh). Faltan {round(total_dem - total_gen, 2)} kWh.",
            "capacidad_minima": None
        }

    # Búsqueda iterativa desde 0 hasta el doble de la demanda máxima con paso 0.2 kWh
    capacidad_prueba = 0.0
    paso = 0.2
    limite_maximo = max(total_dem * 2, 100.0)

    copia_datos = {
        "microrred": datos.get("microrred", "Simulacion"),
        "capacidad": capacidad_prueba,
        "soc_inicial": capacidad_prueba * soc_inicial_relativo,
        "horas": datos.get("horas", [])
    }

    encontrado = False
    capacidad_optima = 0.0

    while capacidad_prueba <= limite_maximo:
        copia_datos["capacidad"] = capacidad_prueba
        copia_datos["soc_inicial"] = capacidad_prueba * soc_inicial_relativo

        _, totales = simular_microrred(copia_datos)

        if totales["energia_comprada"] == 0.0:
            encontrado = True
            capacidad_optima = round(capacidad_prueba, 1)
            break

        capacidad_prueba += paso

    if encontrado:
        return {
            "posible": True,
            "mensaje": f"Capacidad mínima requerida: {capacidad_optima} kWh (con SOC inicial al {int(soc_inicial_relativo*100)}%). Compra a la red = 0.0 kWh.",
            "capacidad_minima": capacidad_optima
        }
    else:
        return {
            "posible": False,
            "mensaje": "No se encontró capacidad suficiente en el rango analizado.",
            "capacidad_minima": None
        }


def simular_con_eficiencia(datos, eficiencia=0.90):
    """
    RETO FUNCIONAL 1:
    Simulación que incluye eficiencia de carga y descarga de la batería (ej. 90%).
    - Al cargar: la batería almacena (excedente * eficiencia).
    - Al descargar: para cubrir la demanda, la batería se reduce en (demanda / eficiencia).
    """
    capacidad = float(datos.get("capacidad", 10.0))
    soc_actual = float(datos.get("soc_inicial", 5.0))
    horas_entrada = datos.get("horas", [])
    eta = float(eficiencia)

    lista_resultados = []
    total_comprado_red = 0.0
    total_demanda = 0.0

    for i in range(len(horas_entrada)):
        gen = float(horas_entrada[i][0])
        dem = float(horas_entrada[i][1])
        total_demanda += dem

        if gen >= dem:
            excedente = gen - dem
            espacio = capacidad - soc_actual
            energia_a_guardar = excedente * eta
            if energia_a_guardar <= espacio:
                soc_actual += energia_a_guardar
                vertido = 0.0
            else:
                soc_actual = capacidad
                vertido = (energia_a_guardar - espacio) / eta
            red = 0.0
        else:
            deficit = dem - gen
            energia_necesaria_bateria = deficit / eta
            if soc_actual >= energia_necesaria_bateria:
                soc_actual -= energia_necesaria_bateria
                red = 0.0
            else:
                deficit_restante = (deficit - (soc_actual * eta))
                soc_actual = 0.0
                red = deficit_restante
            vertido = 0.0

        total_comprado_red += red
        lista_resultados.append({
            "h": i,
            "solar": round(gen, 2),
            "demand": round(dem, 2),
            "battKwh": round(soc_actual, 2),
            "flowGridLoad": round(red, 2)
        })

    cubierto = total_demanda - total_comprado_red
    pct = (cubierto / total_demanda * 100) if total_demanda > 0 else 100.0

    return {
        "resultados": lista_resultados,
        "energia_comprada": round(total_comprado_red, 2),
        "porcentaje_sin_red": round(pct, 2)
    }


# ------------------------------------------------------------------------------
# RETO 3: DEMOSTRACIÓN CONCEPTUAL DE 'VARIABLE GLOBAL' VS 'RETURN'
# (Para explicación en la sustentación oral)
# ------------------------------------------------------------------------------
# En clase se estudia el ámbito (scope) de las variables.
# Una variable global puede modificarse usando la palabra reservada 'global',
# pero en ingeniería de software se prefiere 'return' porque:
# 1. Permite funciones puras (sin efectos secundarios inesperados).
# 2. Facilita las pruebas automáticas y la reutilización.
# 3. No genera conflictos cuando varias partes del código leen la variable al tiempo.
_soc_global_demo = 5.0

def simular_hora_con_global(generacion, carga, capacidad):
    """
    Versión alternativa que modifica una variable global en lugar de retornar el nuevo SOC.
    Ilustra para el docente la diferencia conceptual explicada en clase.
    """
    global _soc_global_demo
    if generacion >= carga:
        excedente = generacion - carga
        espacio = capacidad - _soc_global_demo
        if excedente <= espacio:
            _soc_global_demo += excedente
        else:
            _soc_global_demo = capacidad
    else:
        deficit = carga - generacion
        if _soc_global_demo >= deficit:
            _soc_global_demo -= deficit
        else:
            _soc_global_demo = 0.0
    return _soc_global_demo
