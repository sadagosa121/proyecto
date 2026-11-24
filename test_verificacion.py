import logica

datos = logica.cargar_datos("datos/caso_verificacion.json")
alertas, valido = logica.validar_datos(datos)
print("Alertas:", alertas)
print("Es valido:", valido)

horas, totales = logica.simular_microrred(datos)
print("\n--- RESULTADOS HORA A HORA ---")
for h in horas:
    print(f"Hora {h['h']+1}: Solar={h['solar']} kWh, Carga={h['demand']} kWh -> Bateria={h['battKwh']} kWh, Red={h['flowGridLoad']} kWh, Vertido={h['flowSurplus']} kWh, Accion={h['act']}")

print("\n--- COMPROBACIÓN DEL CASO DE VERIFICACIÓN (SECCIÓN 5 DEL PDF) ---")
soc_esperado = [3.0, 7.0, 10.0, 0.0]
soc_obtenido = [h['battKwh'] for h in horas]
print(f"Carga de bateria al final de cada hora: {soc_obtenido} (Esperado: {soc_esperado}) -> {'OK' if soc_obtenido == soc_esperado else 'FALLO'}")

print(f"Compra a la red: {totales['energia_comprada']} kWh (Esperado: 2.0 kWh) -> {'OK' if totales['energia_comprada'] == 2.0 else 'FALLO'}")
print(f"Vertido: {totales['energia_vertida']} kWh (Esperado: 4.0 kWh) -> {'OK' if totales['energia_vertida'] == 4.0 else 'FALLO'}")
print(f"Carga final bateria: {totales['carga_final_bateria']} kWh (Esperado: 0.0 kWh) -> {'OK' if totales['carga_final_bateria'] == 0.0 else 'FALLO'}")
print(f"Porcentaje cubierto sin red: {totales['porcentaje_sin_red']}% (Esperado: 88.24%) -> {'OK' if totales['porcentaje_sin_red'] == 88.24 else 'FALLO'}")

reto_minima = logica.buscar_capacidad_minima_sin_red(datos)
print("\n--- RETO FUNCIONAL: CAPACIDAD MINIMA SIN RED ---")
print(reto_minima["mensaje"])
