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

UPLINK_KEY = "server_GQJUMG6WJTSTWE3WFG3XEJ3T-HAK33GEK53MS7OGY"     #uplinkkey server de la pagina creada de ANvil works
WIFI_SSID = "Tabebuia"
WIFI_PASSWORD = "mimi1212"                                          #Red y clave de WIFI

#inicilizacion de entradas, saldias y variables
led = Pin("LED", Pin.OUT, value=1)                                  #Se inicializa el LED de la placa rpi 
pulsador_conectar = Pin(16, Pin.IN, value=0)                             #boton de conexion a forma remota
Sensor_Humedad = ADC(26) 
Sensor_Temperatura = ADC(27)
keypad = ADC(28)

ventilador = Pin(0, Pin.OUT, value=1)
bomba = Pin(1,Pin.OUT, value=1)

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
temp_set = 10
hum_set = 10
valores = [] #lista para almacenar valores leidos por las entradas de los sensores

#Funcion para conectarse a la red Wifi y al servidor de anvil
async def conectar_red():
    global fecha_hora
    global wlan
    #print('Conectando a la red y servidor Anvil')
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
            await a.sleep(0.4)
            if wlan.status() in [-1, -2, 3]:
                break

    #print(wlan)
    print(f'Conexión exitosa a la red {WIFI_SSID}')
    display.ClearScreenCursorHome()
    linea1 = 'Conexion Exitosa'
    linea2 = f'Red: {WIFI_SSID}'
    pantalla(linea1,linea2)
    await a.sleep(1)
    
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
    return 'Valores seteados correctamente'
        
@anvil.pico.callable(is_async=True)
async def pico_fn1():
    global hum_set
    global temp_set   
    try:
        # Abrimos el archivo en modo lectura
        with open('datos.json', 'r') as f:
            datos = json.load(f)

        # Verificar que datos sea una lista (o tipo que esperas)
        if isinstance(datos, list):
            # Obtener los últimos 20 elementos (o menos si no hay suficientes)
            ultimos_20 = datos[-20:]
            #print("Últimos 20 elementos:", ultimos_20)
        else:
            print("Los datos en el archivo no son una lista.")

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
        Lectura_Sensor_Temperatura = Sensor_Temperatura.read_u16()
        print(f"Lectura sensor humedad: {Lectura_Sensor_Humedad}, sensor temperatura: {Lectura_Sensor_Temperatura} -------------------------")
        
        hum = int((8000-(Lectura_Sensor_Humedad - 21000))*0.015)    #Se convierte lalectura del pin analogico de 16 bit a % de humedad
        if hum <0 or hum > 100:
            hum = 0
        hum = round(hum, 1)                                       #Se indica que solamente tome 1 cifra decimal
        
        temp = int(Lectura_Sensor_Temperatura / 160)      #Se convierte lalectura del pin analogico de 16 bit a °C de temperatura
        if temp <0 or temp > 100:
            temp = 0
        temp = round(temp, 1)
        print(f"Humedad: {hum}      Temperatura: {temp} -------------------------")
        
        fecha_hora = time.localtime()
        nuevaLectura = (fecha_hora[:5], temp, hum, hum_set, temp_set)
        agregar_datos(nuevaLectura)

        #mostrar_datos()
        await a.sleep(60)

async def ajustar_variables():
    global temp
    global temp_set
    global hum
    global hum_set
    global ventilador
    global bomba
    
    while True:
        print("ajustando variables")
        print(temp)
        print(temp_set)
        if temp > temp_set + 5:
            print("el en if")
            #ventilador.value(0)
        else:
            ventilador = 1
        await a.sleep(1)
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
    try:
        with open ('datos.json', 'r') as f:
            dt = json.load(f)
            #print("Datos cargados del archivo JSON")
    except :
        print("Error al decodificar los datos JSON.")
        
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
        await a.sleep(0.1)
        
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
    sleep(0.05)
    return opcion_teclado
    
def pantalla(linea1,linea2):
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
    
    
def ultimos_set():
    global hum_set
    global temp_set
    try:
        # Abrimos el archivo en modo lectura
        with open('datos.json', 'r') as f:
            datos = json.load(f)

        # Verificar que datos sea una lista (o tipo que esperas)
        if isinstance(datos, list):
            # Obtener los últimos 20 elementos (o menos si no hay suficientes)
            ultimo_temp_set = datos[-1][-1]
            ultimo_hum_set = datos[-1][-2]
            hum_set = ultimo_hum_set
            temp_set = ultimo_temp_set
#             print("ultimo_temp_set ", ultimo_temp_set )
#             print("ultimo_hum_set ",ultimo_hum_set  )
        else:
            print("Los datos en el archivo no son una lista.")

    except:
        print("Error al leer el archivo: ")
        return []
    
async def main():
    #mensaje_inicio()
    ultimos_set()

    while True:
        #lectura_teclado()
        await a.gather(conectar_red(),recolectar_valores(), ajustar_variables(), menu_ppal())
        

# Ejecutar el bucle principal
a.run(main())