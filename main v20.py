import anvil.pico
import json
import network
import ntptime
import time
import lcd_4bit_mode
import os
import uasyncio as a
from machine import Pin
from time import sleep
from machine import ADC, Pin

UPLINK_KEY = "server_E7UCJ6I7S3P6DI7CDEVVIWZZ-HAK33GEK53MS7OGY"     #uplinkkey server de la pagina creada de ANvil works
WIFI_SSID = "vivo y21"
WIFI_PASSWORD = "daniel97."                                          #Red y clave de WIFI

#inicilizacion de entradas, saldias y variables
led = Pin("LED", Pin.OUT, value=1)                                  #Se inicializa el LED de la placa rpi 
pulsador_conectar = Pin(16, Pin.IN, value=0)                             #boton de conexion a forma remota
Sensor_Humedad = ADC(27) 
Sensor_Temperatura = ADC(26)
keypad = ADC(28)

ventilador = Pin(0, Pin.OUT, value=0 )
bomba = Pin(1,Pin.OUT, value=0)

BACK_LIGHT = Pin(9, Pin.OUT)
ENABLE = Pin(10, Pin.OUT)
RS = Pin(11, Pin.OUT)
D7 = Pin(12, Pin.OUT)
D6 = Pin(13, Pin.OUT)
D5 = Pin(14, Pin.OUT)
D4 = Pin(15, Pin.OUT)
display = lcd_4bit_mode.LCD16x2(RS,ENABLE,BACK_LIGHT,D4,D5,D6,D7)  #definimos el objeto Display con sus atributos

opcion_teclado = ""
temp = None
hum = None
    
temp_set = 57
hum_set = 0

#horario_offset = -5*3600
wlan = None
#hora_google = False

valores = [] #lista para almacenar valores leidos por las entradas de los sensores

#Funcion para conectarse a la red Wifi y al servidor de anvil

async def conectar_red():
    global fecha_hora
    global wlan
    
    print('Conectando a la red y servidor Anvil')
    await a.sleep(1) # Without this, the USB handshake seems to break this script and then fail sometimes.

    led = Pin("LED", Pin.OUT, value=1)

    wlan = None
    while not wlan or wlan.status() != 3:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)

        # Blink LED slowly until the Wifi is connected.
        while True:
            print(wlan)
            led.toggle()
            await a.sleep(0.2)
            if wlan.status() in [-1, -2, 3]:
                break

    #print(wlan)
    print(f'Conexión exitosa a la red {WIFI_SSID}')
    display.ClearScreenCursorHome()
    linea1 = 'Conexion Exitosa'
    linea2 = f'Red: {WIFI_SSID}'
    pantalla(linea1,linea2)
    await a.sleep(1)
    
    
    # Setear la hora de google
#     ntptime.host = "time.google.com"    
#     for i in range(10):
#         try:
#             print("Configurando hora del sistema...Hora Inicial: ", time.localtime ())
#             ntptime.settime () 
#             print ("Hora sincronizada: ", time.localtime ())
#             print("")
#             hora_google = True
#             break
#         except Exception as e:
#             print(f"No se pudo configurar la hora del sistema: {e}")
#             print("")
#             await a.sleep(3)
    
    # Solid LED means we're connected and ready to go
    led.on()
    anvil.pico.connect(UPLINK_KEY)
    print("Conexión exitosa a Anvil.")
    print("Esperando 5 segundos luego de la conexion")
    await a.sleep(1)  # Espera 5 segundos para evitar múltiples conexiones
    

#Funcion de comunicacion con Anvil
@anvil.pico.callable(is_async=True)
async def pico_fn(n,m):
    global hum_set
    global temp_set
    print(f"Called local function with argument: {n} y {m}")
    temp_set = n
    hum_set = m
        
    for i in range(10):
        led.toggle()
        await a.sleep_ms(50)
        
@anvil.pico.callable(is_async=True)
async def pico_fn1():
    global hum_set
    global temp_set   
    #return hum_set, temp_set, temp, hum
    try:
        # Abrimos el archivo en modo lectura
        with open('datos.json', 'r') as f:
            datos = json.load(f)

        # Verificar que datos sea una lista (o tipo que esperas)
        if isinstance(datos, list):
            # Obtener los últimos 20 elementos (o menos si no hay suficientes)
            ultimos_20 = datos[-20:]
            print("Últimos 20 elementos:", ultimos_20)
            #return ultimos_20
        else:
            print("Los datos en el archivo no son una lista.")
            #return []

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error al leer el archivo: {e}")
        return []
    return ultimos_20, temp_set, hum_set

  
        
async def recolectar_valores():
    print("entrando a recolectar valores")
    global valores
    global hum
    global temp
    global hum_set
    global temp_set
    global datos_plataforma
    
    while True:
        Lectura_Sensor_Humedad = Sensor_Humedad.read_u16()
        print("temperatura")
        print(Lectura_Sensor_Humedad )
        Lectura_Sensor_Temperatura = Sensor_Temperatura.read_u16()
        print("humedad")
        print(Lectura_Sensor_Temperatura)
        print(f"hum_set: {hum_set}, temp_set: {temp_set}")
        
        hum = int(100/(2**16)*Lectura_Sensor_Humedad)           #Se convierte lalectura del pin analogico de 16 bit a % de humedad
        hum = round(hum, 1)                                       #Se indica que solamente tome 1 cifra decimal
        temp = int(100/(2**16)*Lectura_Sensor_Temperatura)      #Se convierte lalectura del pin analogico de 16 bit a °C de temperatura
        temp = round(temp, 1)
        
        #Se indica que solamente tome 1 cifra decimal
#         if hora_google == True:
#             tiempo_actual =  time.time() + horario_offset  # Ajusta la hora
#             fecha_hora = time.localtime(tiempo_actual)     # Se almacena la hora actualizada
#             #print("hora actualizada con google")
#         else:
#             fecha_hora = time.localtime()
#             #print("Hora sin actualizar con google")
        fecha_hora = time.localtime()
        #print("Fecha_Hora = ",fecha_hora)
        datosjson = (fecha_hora[:5], hum, temp)
        valores.append((fecha_hora[:5], hum, temp))   #Guarda los valores en una lista #se eleccionan solo los primero 5 datos de la fecha
        datos_plataforma = (fecha_hora[:5], hum, temp)
        agregar_datos(datosjson)
        #print(valores)
        
        
#         if (fecha_hora[4] % 10 == 5 or fecha_hora[4] % 10 == 0) and fecha_hora[5] == 0:
#             print("entando acargar datos")
#             valores.append((fecha_hora[:5], hum, temp))   #Guarda los valores en una lista #se eleccionan solo los primero 5 datos de la fecha
#             print(valores)
        mostrar_datos()
        await a.sleep(60)
        
def agregar_datos(nuevo_dato):
    try:
            with open('datos.json', 'r') as f:    #abre o crea el archivo.json la f sirve para interactuar con el archivo, la w significa q esta en modo escritura
                datos = json.load(f)
    except:
        # Si el archivo no existe o está vacío, inicializa una lista vacía
        datos = []             #Escribe la lista valores en el archivo en formato JSON
    # Agregar el nuevo dato a la lista
    datos.append(nuevo_dato)

    # Guardar los datos actualizados de vuelta al archivo
    with open('datos.json', 'w') as f:
        json.dump(datos, f)
    
    print("Nuevo dato agregado exitosamente.")
            
            
def mostrar_datos():
    #global valores
    try:
        with open ('datos.json', 'r') as f:
            dt = json.load(f)
            print("Datos cargados: ", dt)
#     except FileNotFoundError:
#         print("El archivo 'datos.json' no existe.")
    except :
        print("Error al decodificar los datos JSON.")
        
#funcion para guardar datos de la lista en el archivo JSON
# async def guardar_datos():
#     print('Guardando datos en el JSON')
#     global valores
#     while True:
#         try:
#             with open('datos.json', 'w') as f:    #abre o crea el archivo.json la f sirve para interactuar con el archivo, la w significa q esta en modo escritura
#                 json.dump(valores, f)             #Escribe la lista valores en el archivo en formato JSON
#                 print("datos guardados exitosamente en JSON-------------------------------------------------------")
#         except Exception as e:
#             print(f"Error al guardar los datos en JSON: {e}")
#         await a.sleep(60)


def limpiar_datos_json():
    try:
        with open ('datos.json', 'w') as f:
            f.write('[]')     #escribe una lista vacia en el archivo
            print("archivo json limpiado")
    except Exception as e:
        print(f'Error al limpiar el archivo json: {e}')
    
async def menu_ppal():
    global opcion_teclado
    opcion_teclado = ""
    display.ClearScreenCursorHome()
    while True:
        linea1 = 'Temp°C:'+str(temp)+' Set:' + str(temp_set)
        linea2 = 'Hum. %:'+str(hum)+' Set:' + str(hum_set)
        pantalla(linea1,linea2)
        lectura_teclado()
        if opcion_teclado == 'seleccionar' or opcion_teclado == 'derecha':
            await menu1_1()
            break
        await a.sleep(0.5)
        
async def menu1_1():
    global opcion_teclado
    opcion_teclado = ""
    display.ClearScreenCursorHome()
    linea1 = '>Temp Set: '+str(temp_set)+'°C'
    linea2 = ' Hum  Set: '+str(hum_set)+'% '
    pantalla(linea1,linea2)
    while True:
        lectura_teclado()
        if opcion_teclado == 'seleccionar':
            await menu1_1_1()
            break
        elif opcion_teclado == 'izquierda':
            await menu_ppal()
            break
        elif opcion_teclado == 'derecha':
            await menu1_1_1()
            break
        elif opcion_teclado == 'arriba':
            await menu1_2()
            break
        elif opcion_teclado == 'abajo':
            await menu1_2()
            break
        await a.sleep(0.1)

async def menu1_2():
    global opcion_teclado
    opcion_teclado = ""
    display.ClearScreenCursorHome()
    linea1 = ' Temp Set: '+str(temp_set)+'°C'
    linea2 = '>Hum  Set: '+str(hum_set)+'% '
    pantalla(linea1,linea2)
    while True:
        lectura_teclado()
        if opcion_teclado == 'seleccionar':
            await menu1_2_1()
            break
        elif opcion_teclado == 'izquierda':
            await menu_ppal()
            break
        elif opcion_teclado == 'derecha':
            await menu1_2_1()
            break
        elif opcion_teclado == 'arriba':
            await menu1_1()
            break
        elif opcion_teclado == 'abajo':
            await menu1_1()
            break
        await a.sleep(0.1)
   
async def menu1_1_1():
    global opcion_teclado
    global temp_set
    opcion_teclado = ""
    display.ClearScreenCursorHome()
    linea1 = ' Setear: '
    linea2 = '>Temperatura: '+str(temp_set)+' C'
    pantalla(linea1,linea2)
    while True:
        lectura_teclado()
        if opcion_teclado == 'seleccionar':
            await menu1_1()
            break
        elif opcion_teclado == 'izquierda':
            await menu1_1()
            break
        elif opcion_teclado == 'derecha':
            await menu1_1()
            break
        elif opcion_teclado == 'arriba':
            if temp_set < 60:
                temp_set = temp_set + 1
            await menu1_1_1()
            break
        elif opcion_teclado == 'abajo':
            if temp_set > 10:
                temp_set = temp_set - 1
            await menu1_1_1()
            break
        await a.sleep(0.1)
    
async def menu1_2_1():
    global opcion_teclado
    global hum_set
    opcion_teclado = ""
    display.ClearScreenCursorHome()
    linea1 = 'Setear: '
    linea2 = '>Humedad: '+str(hum_set)+' %'
    pantalla(linea1,linea2)    
    while True:      
        lectura_teclado()
        if opcion_teclado == 'seleccionar':
            await menu1_2()
            break
        elif opcion_teclado == 'izquierda':
            await menu1_2()
            break
        elif opcion_teclado == 'derecha':
            await menu1_2()
            break
        elif opcion_teclado == 'arriba':
            if hum_set < 60:
                hum_set = hum_set + 1
            await menu1_2_1()
            break
        elif opcion_teclado == 'abajo':
            if hum_set > 20:
                hum_set = hum_set - 1
            await menu1_2_1()
            break
        await a.sleep(0.1)
        
def lectura_teclado():
    global opcion_teclado
    pulsador_oprimido = keypad.read_u16()
    if pulsador_oprimido < 8000:
        opcion_teclado ="derecha"
    elif 7000 <= pulsador_oprimido < 9000:
        opcion_teclado ="arriba"
    elif 9000 <= pulsador_oprimido < 19000:
        opcion_teclado ="abajo"
    elif 19000 <= pulsador_oprimido < 28000:
        opcion_teclado ="izquierda"
    elif 28000 <= pulsador_oprimido < 40000:
        opcion_teclado ="seleccionar"
    else :
        opcion_teclado ="none"
    #print(opcion_teclado)
    #print(pulsador_oprimido)
    sleep(0.05)
    return opcion_teclado
    
def pantalla(linea1,linea2):
    #display.ClearScreenCursorHome()
    #print("Mostrando por pantalla")
    #print(linea1)
    #print(linea2)
    #print("")
    sleep(0.1)
    display.BackLightOn()
    display.WriteLine(linea1, 1)
    display.WriteLine(linea2, 2)
        
def mensaje_inicio():
    linea1 = 'Ctrl Invernadero'
    linea2 = 'V2 Daniel Amaya'
    pantalla(linea1, linea2)
    sleep(2)
    linea1 = ''
    linea2 = 'Bienvenidos...!'
    pantalla(linea1, linea2)
    sleep(2)
    
def u20():
    try:
        # Abrimos el archivo en modo lectura
        with open('datos.json', 'r') as f:
            datos = json.load(f)

        # Verificar que datos sea una lista (o tipo que esperas)
        if isinstance(datos, list):
            # Obtener los últimos 20 elementos (o menos si no hay suficientes)
            ultimos_20 = datos[-20:]
            print("Últimos 20 elementos:", ultimos_20)
            return ultimos_20
        else:
            print("Los datos en el archivo no son una lista.")
            return []

    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error al leer el archivo: {e}")
        return []
    
async def main():
    #mensaje_inicio()
    #mostrar_datos()
    #u20()
    #limpiar_datos_json()

    
    while True:
        #lectura_teclado()
        #await a.gather(conectar_red(),recolectar_valores(), menu_ppal(), guardar_datos())
        await a.gather(conectar_red(),recolectar_valores(), menu_ppal())
        #await a.gather(recolectar_valores())
        #await a.gather(recolectar_valores())
#    limpiar_datos_json()  #----------------------------------------------------------------------------------------------------------------------------
        
# Ejecutar el bucle principal
a.run(main())