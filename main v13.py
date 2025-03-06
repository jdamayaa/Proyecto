import anvil.pico
import json
import network
import ntptime
import time
import lcd_4bit_mode
import uasyncio as a
from machine import Pin
from time import sleep
from machine import ADC, Pin

UPLINK_KEY = "server_E7UCJ6I7S3P6DI7CDEVVIWZZ-HAK33GEK53MS7OGY"     #uplinkkey server de la pagina creada de ANvil works
WIFI_SSID = "vivo y21"
WIFI_PASSWORD = "daniel97."                                          #Red y clave de WIFI

led = Pin("LED", Pin.OUT, value=1)                                  #Se inicializa el LED de la placa rpi 
pulsador_conectar = Pin(16, Pin.IN, value=0)                             #boton de conexion a forma remota

#inicilizamos los pines analogicospara lectura de los sensores
Sensor_Humedad = ADC(26) 
Sensor_Temperatura = ADC(27)
keypad = ADC(28)
opcion_teclado = ""

#inicializamos lso pines para las salidas digitales de control de potencia
ventilador = Pin(0, Pin.OUT, value=0 )
bomba = Pin(1,Pin.OUT, value=0)

# #inicializamos los pines para la pantalla lcd 1602
BACK_LIGHT = Pin(9, Pin.OUT)
ENABLE = Pin(10, Pin.OUT)
RS = Pin(11, Pin.OUT)
D7 = Pin(12, Pin.OUT)
D6 = Pin(13, Pin.OUT)
D5 = Pin(14, Pin.OUT)
D4 = Pin(15, Pin.OUT)

display = lcd_4bit_mode.LCD16x2(RS,ENABLE,BACK_LIGHT,D4,D5,D6,D7)  #definimos el objeto Display con sus atributos

temp = 10
hum = 20

temp_set = 20
hum_set = 40

horario_offset = -5*3600

wlan = None

#fecha_hora = ()

valores = [] #lista para almacenar valores leidos por las entradas de los sensores

#Funcion para conectarse a la red Wifi y al servidor de anvil
def conectar_red():
    global fecha_hora
    global wlan
    
    print('Conectando a la red y servidor Anvil')
    sleep(1) # Without this, the USB handshake seems to break this script and then fail sometimes.

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
            sleep(0.2)
            if wlan.status() in [-1, -2, 3]:
                break

    print(wlan)
    print(f'Conexión exitosa a la red {WIFI_SSID}')
    display.ClearScreenCursorHome()
    linea1 = 'Conexion Exitosa'
    linea2 = f'Red: {WIFI_SSID}'
    pantalla(linea1,linea2)
    
    sleep(5)
    
    ntptime.host = "time.google.com"
    
    # Set the RTC to the current time
    for i in range(10):
        try:
            print("Configurando hora del sistema...")
            print ("Hora inicial: ", time.localtime ()) 
            ntptime.settime () 
            print ("Hora sincronizada: ", time.localtime ())
            break
        except Exception as e:
            print(f"No se pudo configurar la hora del sistema: {e}")
            sleep(3)
    
    # Solid LED means we're connected and ready to go
    led.on()
    sleep(2)
    #anvil.pico.connect(UPLINK_KEY)
    print("Conexión exitosa a Anvil.")
    print("Esperando 5 segundos luego de la conexion")
    await a.sleep(5)  # Espera 5 segundos para evitar múltiples conexiones
    

#Funcion de comunicacion con Anvil
@anvil.pico.callable(is_async=True)
async def pico_fn(n):
    print(f"Called local function with argument: {n}")
        
    for i in range(10):
        led.toggle()
        await a.sleep_ms(50)
    return datos.json

def cargar_datos():
    global valores
    try:
        with open ('datos.json', 'r') as f:
            valores = json.load(f)
            print("Datos cargados: ", valores)
    except OSError:
        valores = []
        
async def recolectar_valores():
    print("recolectando valores")
    global valores
    global hum
    global temp
    while True:
        Lectura_Sensor_Humedad = Sensor_Humedad.read_u16()
        Lectura_Sensor_Temperatura = Sensor_Temperatura.read_u16()
        
        hum = float(100/(2**16)*Lectura_Sensor_Humedad)           #Se convierte lalectura del pin analogico de 16 bit a % de humedad
        hum = round(hum, 1)                                       #Se indica que solamente tome 1 cifra decimal
        temp = float(100/(2**16)*Lectura_Sensor_Temperatura)      #Se convierte lalectura del pin analogico de 16 bit a °C de temperatura
        temp = round(temp, 1)                                     #Se indica que solamente tome 1 cifra decimal
        #print(f"valores recolectados de los sensores: Humedad:{hum}, Temperatura:{temp}")
        tiempo_actual =  time.time() + horario_offset  # Ajusta la hora
        fecha_hora = time.localtime(tiempo_actual)          # Se almacena la hora en la tupla hora  una tupla vacia se defini t = ()
        #print("segundo = ",fecha_hora[5])
        print(wlan)
        print(fecha_hora)
        if (fecha_hora[4] % 10 == 5 or fecha_hora[4] % 10 == 0) and fecha_hora[5] == 0:
            print("entando acargar datos")
            valores.append((fecha_hora[:5], hum, temp))   #Guarda los valores en una lista #se eleccionan solo los primero 5 datos de la fecha
            print(valores)
        await a.sleep(1)
        

#funcion para guardar datos de la lista en el archivo JSON
async def guardar_datos():
    print('Guardando datos en el JSON')
    global valores
    while True:
        try:
            with open('datos.json', 'w') as f:    #abre o crea el archivo.json la f sirve para interactuar con el archivo, la w significa q esta en modo escritura
                json.dump(valores, f)             #Escribe la lista valores en el archivo en formato JSON
                print("datos guardados exitosamente en JSON-------------------------------------------------------")
        except Exception as e:
            print(f"Error al guardar los datos en JSON: {e}")
        await a.sleep(60)


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
    linea1 = 'Temp°C:'+str(temp)+' Set:' + str(temp_set)
    linea2 = 'Hum. %:'+str(hum)+' Set:' + str(hum_set)
    pantalla(linea1,linea2)
    while True:
        lectura_teclado()
        if opcion_teclado == 'seleccionar' or opcion_teclado == 'derecha':
            await menu1_1()
            break
        await a.sleep(0.1)
        
async def menu1_1():
    global opcion_teclado
    opcion_teclado = ""
    display.ClearScreenCursorHome()
    linea1 = '>Temp Set: '+str(temp)+'°C'
    linea2 = ' Hum  Set: '+str(hum)+'% '
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
    linea1 = ' Temp Set: '+str(temp)+'°C'
    linea2 = '>Hum  Set: '+str(hum)+'% '
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
    linea1 = 'Setear: '
    linea2 = '>Humedad: '+str(hum_set)+' %'
    pantalla(linea1,linea2)
    opcion_teclado = ""
    #display.ClearScreenCursorHome()
    while True:      
        lectura_teclado()
        if opcion_teclado == 'seleccionar':
            await menu1_2()
            break
        elif opcion_teclado == 'izquierda':
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
    
    if pulsador_oprimido < 1000:
        opcion_teclado ="derecha"
    elif 1000 <= pulsador_oprimido < 13000:
        opcion_teclado ="arriba"
    elif 13000 <= pulsador_oprimido < 20000:
        opcion_teclado ="abajo"
    elif 20000 <= pulsador_oprimido < 30000:
        opcion_teclado ="izquierda"
    elif 30000 <= pulsador_oprimido < 38000:
        opcion_teclado ="seleccionar"
    else :
        opcion_teclado ="none"
    #print(opcion_teclado)
    sleep(0.1)
    return opcion_teclado
    
def pantalla(linea1,linea2):
    display.ClearScreenCursorHome()
    print("Mostrando por pantalla")
    print(linea1)
    print(linea2)
    print("")
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

async def main():
    
    while True:
        
        await a.gather(recolectar_valores(), menu_ppal())
        #a.run(menu_ppal())
        
#     while True:
#         #print("Ingresando al while")
#         
#         
#         print("Aquiii")
#         sleep(1)
#         await cargar_datos_a_lista()
    
    #mensaje_inicio()
    #menu_ppal()
#    limpiar_datos_json()  #----------------------------------------------------------------------------------------------------------------------------
#     sleep(1)
#     while True:
#         #print('ingresando al While True')
#         a.create_task( recolectar_valores())  # Iniciar la recolección de valores
#         a.create_task( guardar_datos())
#         
#         if pulsador_conectar.value():  # Verifica si el pulsador está en estado alto
#             #print("pulsador True entrando desde el while if")           
#             await conectar_red()
#             
#         else:
#             print("El pulsador no está energizado, trabajando de forma local")
#             cargar_datos()  # Cargar datos al inicio
#             #print("antes  del a.create")
#             #a.create_task( recolectar_valores())  # Iniciar la recolección de valores
#             #pantalla()
#             #print("pasando el a.create")
#             #await a.sleep(20)         
#             
#     
#             while True:
#                 #guardar_datos()  # Guardar datos cada cierto tiempo
#                 print("datos guardados en el json desde el while")
#                 await a.sleep(60)  # Espera 60 segundos antes de guardar nuevamente
#                 
#                 if pulsador_conectar.value():  # Verifica si el pulsador está en estado alto
#                     print("pulsado True entrando desde el while else")
#                     await conectar_red()  
#         
#         print("esperando los 5 segundos, fin del while true del main")
#        await a.sleep(5)  # Espera 1 segundo antes de volver a verificar

# Ejecutar el bucle principal
a.run(main())