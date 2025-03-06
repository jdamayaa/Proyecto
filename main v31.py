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

UPLINK_KEY = "server_GQJUMG6WJTSTWE3WFG3XEJ3T-HAK33GEK53MS7OGY"     #inicilizacion de entradas, saldias y variables
WIFI_SSID = "v12"
WIFI_PASSWORD = "daniel97."                                          

led = Pin("LED", Pin.OUT, value=1)                                
pulsador_conectar = Pin(16, Pin.IN, value=0)                             
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
temp = 10
hum = 10
temp_set = 10
hum_set = 10
hora = False
#valores = [] #lista para almacenar valores leidos por las entradas de los sensores
 

async def conectar_red():       #Funcion para conectarse a la red Wifi
    global hora_ajustada
    global fecha_hora
    global wlan
    
    await a.sleep(1)
    led = Pin("LED", Pin.OUT, value=1)

    wlan = None
    while not wlan or wlan.status() != 3:
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        while True:
            print(wlan)
            led.toggle()
            await a.sleep(0.4)
            if wlan.status() in [-1, -2, 3]:
                break
            led.on()
    try:							# Sincronizar la hora desde un servidor NTP
        ntptime.settime()
        sleep(2)
        print("Hora sincronizada con NTP:", time.localtime())
        hora_utc = time.localtime()  
        hora_local = ajustar_hora_zona(hora_utc) 
        print("Hora local ajustada:", hora_local)
    except Exception as e:
        print("Error al sincronizar con NTP:", e)
        
    print(f'Conexión exitosa a la red {WIFI_SSID}')
    display.ClearScreenCursorHome()
    linea1 = 'Conexion Exitosa'
    linea2 = f'Red: {WIFI_SSID}'
    pantalla(linea1,linea2)
    await a.sleep(2)

    led.on()
    anvil.pico.connect(UPLINK_KEY)
    await a.sleep(2)  

def ajustar_hora_zona(hora_utc):             #Funcion para ajustar la hora
    global hora
    global hora_ajustada
    
    DIFERENCIA_HORARIA = -5  
    hora_ajustada = list(hora_utc)
    hora_ajustada[3] += DIFERENCIA_HORARIA  
    
    
    if hora_ajustada[3] < 0:				# Asegurarse de que el día no se desajuste
        hora_ajustada[3] += 24
        hora_ajustada[2] -= 1  
    elif hora_ajustada[3] >= 24:
        hora_ajustada[3] -= 24
        hora_ajustada[2] += 1  
    hora = True
    return [hora_ajustada]


@anvil.pico.callable(is_async=True)     #Funcion de comunicacion con Anvil
async def pico_fn(n,m):
    global hum_set
    global temp_set

    print(f"Setear humedad en: {m} y temperatura en: {n}")
    temp_set = n
    hum_set = m
        
    for i in range(10):
        led.toggle()
        await a.sleep_ms(30)
    return 'Valores seteados correctamente'
        
@anvil.pico.callable(is_async=True)			#Funcion para comunicacion con interfaz remota
async def pico_fn1():
    global hum_set
    global temp_set
    try:
        with open('datos.json', 'r') as f: 				# Abrir el archivo en modo lectura
            datos = json.load(f)

        if isinstance(datos, list):						# Verificar que 'datos' sea una lista
            ahora = time.time()							# Obtener el tiempo actual en segundos
            dos_dias_atras = ahora - (2 * 3600) 	# Calcular el tiempo de hace 2 días (48 horas)
            datos_filtrados = []
            for registro in datos:
                año, mes, dia, hora, minuto = registro[0]
                fecha_registro = time.mktime((año, mes, dia, hora, minuto, 0, 0, 0, 0))
                
                if fecha_registro >= dos_dias_atras:		# Verificar si la fecha está dentro del rango de los últimos 2 días
                    datos_filtrados.append(registro)

            ultimos_20 = datos_filtrados[-20:] if len(datos_filtrados) >= 20 else datos_filtrados  # Obtener los últimos 20 elementos (o menos si no hay suficientes)

        else:
            print("Los datos en el archivo no son una lista.")
            return []

    except OSError as e:
        print(f"Error al leer el archivo: {e}")
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo JSON: {e}")
    return ultimos_20, temp_set, hum_set

async def recolectar_valores():
    global valores
    global hum
    global temp
    global hum_set
    global temp_set
    global datos_plataforma
    global hora_ajustada
    
    while True:
        await a.sleep(30)
        if hora ==  True:
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
            
            t = time.localtime()
            fecha_hora = ajustar_hora_zona(t)
            nuevaLectura = (fecha_hora[0][:5], temp, hum, hum_set, temp_set)
            agregar_datos(nuevaLectura)

            mostrar_datos()
        else:
            print("Hora no configurada")
        await a.sleep(30)

async def ajustar_variables():
    global temp
    global temp_set
    global hum
    global hum_set
    global ventilador
    global bomba
    
    while True:
        if temp > temp_set +5:
            #print("Ajustando temperatura")
            if temp > temp_set:
                ventilador.value(0)
        else:
            ventilador.value(1)

        if hum < hum_set -5:
            #print('Ajustando humedad')
            if hum < hum_set:
                bomba.value(0)
        else:
            bomba.value(1)         
        await a.sleep(5)
        
def agregar_datos(nuevo_dato):
    try:
            with open('datos.json', 'r') as f:    #abre o crea el archivo.json la f sirve para interactuar con el archivo, la w significa q esta en modo escritura
                datos = json.load(f)
    except:                   					#Si el archivo no existe o está vacío, inicializa una lista vacía
        datos = []            					#Escribe la lista valores en el archivo en formato JSON
    datos.append(nuevo_dato)  					#Agregar el nuevo dato a la lista

    with open('datos.json', 'w') as f:			# Guardar los datos actualizados de vuelta al archivo
        json.dump(datos, f)
    print("Nuevo dato agregado exitosamente.")
            
            
def mostrar_datos():				#Funcion para mostrar los datos almacendos en el archi JSON
    try:
        with open ('datos.json', 'r') as f:
            dt = json.load(f)
            print("Datos cargados del archivo JSON")
            print(dt)
    except :
        print("Error al decodificar los datos JSON.")
        
def limpiar_datos_json():		#funcion para borrar todos los datos del archivo JSON
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
        linea2 = 'Hum  %: '+str(hum)+' Set:' + str(hum_set)
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
    sleep(0.2)
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
        with open('datos.json', 'r') as f:		# Abrimos el archivo en modo lectura
            datos = json.load(f)

        if isinstance(datos, list):
            ultimo_temp_set = datos[-1][-1]
            ultimo_hum_set = datos[-1][-2]
            hum_set = ultimo_hum_set
            temp_set = ultimo_temp_set
            print("ultimo valor seteado de temperatura: ", ultimo_temp_set )
            print("ultimo valor seteado de humedad:     ",ultimo_hum_set  )
        else:
            print("Los datos en el archivo no son una lista.")

    except:
        print("Error al leer el archivo: ")
        #return []
    
async def main():
    mensaje_inicio()
    ultimos_set()

    while True:
        await a.gather(conectar_red(),  recolectar_valores(), ajustar_variables(), menu_ppal())
        
a.run(main()) # Ejecutar el bucle principal