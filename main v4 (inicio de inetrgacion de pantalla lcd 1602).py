import anvil.pico
import uasyncio as a
from machine import Pin
import json
import network
from time import sleep
import ntptime
from machine import ADC, Pin
import lcd_4bit_mode


UPLINK_KEY = "server_E7UCJ6I7S3P6DI7CDEVVIWZZ-HAK33GEK53MS7OGY"  #uplinkkey server de la pagina creada de ANvil works
WIFI_SSID = "vivo Y21s"
WIFI_PASSWORD = "daniel97."                                      #Red y clave de WIFI


led = Pin("LED", Pin.OUT, value=1)       #
pulsador_16 = Pin(16, Pin.IN, value=0)  
pulsador_17 = Pin(17, Pin.IN, value=0)
pulsador_18 = Pin(18, Pin.IN, value=0)
# 
# #inicializamos los pines para la pantalla lcd 1602
adc_26 = ADC(26) 
adc_27 = ADC(27)
adc_28 = ADC(28)
vent = machine.Pin(0,machine.Pin.OUT)
bom = machine.Pin(1,machine.Pin.OUT)
RS = machine.Pin(11,machine.Pin.OUT)
ENABLE = machine.Pin(10,machine.Pin.OUT)
BACK_LIGHT = machine.Pin(9,machine.Pin.OUT)
D4 = machine.Pin(15,machine.Pin.OUT)
D5 = machine.Pin(14,machine.Pin.OUT)
D6 = machine.Pin(13,machine.Pin.OUT)
D7 = machine.Pin(12,machine.Pin.OUT)


valores = [] #lista para almacenar valores leidos por las entradas

def conectar_red():
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

    # Set the RTC to the current time
    for i in range(10):
        try:
            print("Setting system time...")
            ntptime.settime()
            print(f"System time set to {ntptime.time()}")
            break
        except Exception as e:
            print(f"Failed to set system time: {e}")
            sleep(1)

    # Solid LED means we're connected and ready to go
    led.on()
    print(wlan)
    
def online():
    conectar_red()
    anvil.pico.connect(UPLINK_KEY)
    print("Conexión exitosa a Anvil.")
    print("Esperando 5 segundos luego de la conexion")
    await a.sleep(5)  # Espera 5 segundos para evitar múltiples conexiones
    



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
    print("recolectando valores")
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
        
def pantalla():
    print("ingresando a pantalla")
    display = lcd_4bit_mode.LCD16x2(RS,ENABLE,BACK_LIGHT,D4,D5,D6,D7)

    display.BackLightOn()
    display.WriteLine('Ctrl Invernadero',1)

    display.WriteLine('by Daniel Amaya',2)
    sleep(2)
    valor_26 = adc_26.read_u16()
    valor_27 = adc_27.read_u16()
    valor_28 = adc_28.read_u16()

    # Convertir valores analógicos a enteros
    s_hum_voltaje = float((valor_26*3)/(2**16))  # convertimos el dato de entrada en el voltaje de entrada
    s_temp_voltaje = float((valor_27*3.3)/(2**16))
    s_ilum_voltaje = float((valor_28*3.3)/(2**16))
    
    hum = int(100-((s_hum_voltaje-1.5)*100 /1.5)) # convertimos el voltaje de entrada a sus respectivas unidades
    temp = int((s_temp_voltaje*40)/3.3)
    ilum = int((s_ilum_voltaje*100)/3.3)
    
    if hum > 100:
        hum = 0
    
        
    #print(valor_26)
    print('Volt sens hum = ' + str(s_hum_voltaje) + "    humedad = " + str(hum) + " %")
    print('Volt sens temp= ' + str(s_temp_voltaje) + "   tempertatura = " + str(temp) + "°C")
    print('Volt sens ilum= ' + str(s_ilum_voltaje) + "   iluminacion = " + str(ilum) + "%")
    print("")
    
    display.ClearScreenCursorHome()
    display.WriteLine('Temperatura= '+str(temp)+'C',1)
    display.WriteLine('Hum='+str(hum)+'%  ilum='+str(ilum)+'%',2)
    
        
    
    if (temp > 30 or hum > 50) :
        vent.on()
    else:
        vent.off()
    
    if ilum < 50:
        bom.on()
    else:
        bom.off()
    print("entrando a ultimo sleep de pantalla()")
    sleep(5)
    print("saliendo de ultimo sleep de pantalla()")
            


async def main():
    
    limpiar_datos_json()  #----------------------------------------------------------------------------------------------------------------------------
    
    while True:
        pantalla()
        if pulsador_17.value():  # Verifica si el pulsador está en estado alto
            print("pulsado True entrando desde el while if")
            await online()
        else:
            print("El pulsador no está energizado, trabajando de forma local")
            cargar_datos()  # Cargar datos al inicio
            print("antes  del a.create")
            a.create_task( recolectar_valores())  # Iniciar la recolección de valores
            print("pasando el a.create")
            #await a.sleep(20)         
            
    
            while True:
                guardar_datos()  # Guardar datos cada cierto tiempo
                print("datos guardados en el json desde el while")
                await a.sleep(60)  # Espera 60 segundos antes de guardar nuevamente
                
                if pulsador_17.value():  # Verifica si el pulsador está en estado alto
                    print("pulsado True entrando desde el while else")
                    await online()  
        
        print("esperando los 5 segundos, fin del while true del main")
        await a.sleep(5)  # Espera 1 segundo antes de volver a verificar

# Ejecutar el bucle principal
a.run(main())