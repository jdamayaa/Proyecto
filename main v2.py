import anvil.pico
import uasyncio as a
from machine import Pin
import json


UPLINK_KEY = "server_E7UCJ6I7S3P6DI7CDEVVIWZZ-HAK33GEK53MS7OGY"  #uplinkkey server de la pagina creada de ANvil works


led = Pin("LED", Pin.OUT, value=1)       #
pulsador_16 = Pin(16, Pin.IN, value=0)  
pulsador_17 = Pin(17, Pin.IN, value=0)
pulsador_18 = Pin(18, Pin.IN, value=0)

valores = [] #lista para almacenar valores leidos



@anvil.pico.callable(is_async=True)
async def pico_fn(n):
    print(f"Called local function with argument: {n}")
        
    for i in range(10):
        led.toggle()
        await a.sleep_ms(50)
    return datos.json

@anvil.pico.callable(is_async=True)
async def verificar_conexion(m):
    print("verificando conexion")
    return m * 2

def cargar_datos():
    global valores
    try:
        with open ('datos.json', 'r') as f:
            valores = json.load(f)
            print("Datos cargados: ", valores)
    except OSError:
        valores = []

async def recolectar_valores():
    global valores
    while True:
        valor_17 = pulsador_17.value()
        valor_18 = pulsador_18.value()
        valores.append((valor_17,valor_18))
        print(f"valores recolectados: {valor_17}, {valor_18}")
        print(valores)
        await a.sleep(20)
        
def guardar_datos():
    global valores
    try:
        with open('datos.json', 'w') as f:    #abre o crea el archivo.json la f sirve para interactuar con el archivo, la w significa q esta en modo escritura
            json.dump(valores, f)             #Escribe la lista valores en el archivo en formato JSON
            print("datos guardados exitosamente en JSON")
    except Exception as e:
        print(f"Error al guardar los datos en JSON: {e}")
        
def limpiar_datos_json():
    try:
        with open ('datos.json', 'w') as f:
            f.write('[]')     #escribe una lista vacia en el archivo
            print("archivo json limpiado")
    except Exception as e:
        print(f'Error al limpiar el archivo json: {e}')
            


async def main():
    limpiar_datos_json()  #----------------------------------------------------------------------------------------------------------------------------
    while True:
        if pulsador_17.value():  # Verifica si el pulsador está en estado alto
            print("pulsado True")
            anvil.pico.connect(UPLINK_KEY)
            print("Conexión exitosa a Anvil.")
            print("Esperando 5 segundos luego de la conexion")
            await a.sleep(5)  # Espera 5 segundos para evitar múltiples conexiones
        else:
            print("El pulsador no está energizado, trabajando de forma local")
            cargar_datos()  # Cargar datos al inicio
            a.create_task(recolectar_valores())  # Iniciar la recolección de valores
    
            while True:
                guardar_datos()  # Guardar datos cada cierto tiempo
                
                await a.sleep(60)  # Espera 60 segundos antes de guardar nuevamente
        
        await a.sleep(5)  # Espera 1 segundo antes de volver a verificar

# Ejecutar el bucle principal
a.run(main())