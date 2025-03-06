import anvil.pico
import json
import network
import ntptime
import lcd_4bit_mode
import uasyncio as a
from machine import Pin
from time import sleep
from machine import ADC, Pin

UPLINK_KEY = "server_E7UCJ6I7S3P6DI7CDEVVIWZZ-HAK33GEK53MS7OGY"     #uplinkkey server de la pagina creada de ANvil works
WIFI_SSID = "Tabebuia"
WIFI_PASSWORD = "lula2022"                                          #Red y clave de WIFI

led = Pin("LED", Pin.OUT, value=1)                                  #Se inicializa el LED de la placa rpi 
pulsador_16 = Pin(17, Pin.IN, value=0)                             #boton de conexion a forma remota
pulsador_18 = Pin(18, Pin.IN, value=0)

#inicilizamos los pines analogicospara lectura de los sensores
Sensor_Humedad = ADC(26) 
Sensor_Temperatura = ADC(27)

#inicializamos lso pines para las salidas digitales de control de potencia
ventilador = Pin(0, Pin.OUT, value=0 )
Bomba = Pin(1,Pin.OUT, value=0)

# #inicializamos los pines para la pantalla lcd 1602
BACK_LIGHT = Pin(9, Pin.OUT)
ENABLE = Pin(10, Pin.OUT)
RS = Pin(11, Pin.OUT)
D7 = Pin(12, Pin.OUT)
D6 = Pin(13, Pin.OUT)
D5 = Pin(14, Pin.OUT)
D4 = Pin(15, Pin.OUT)

display = lcd_4bit_mode.LCD16x2(RS,ENABLE,BACK_LIGHT,D4,D5,D6,D7)


valores = [] #lista para almacenar valores leidos por las entradas de los sensores

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
    while True:
        valor_17 = pulsador_16.value()
        valor_18 = pulsador_18.value()
        Lectura_Sens_Humedad = Sensor_Humedad.read_u16()
        Lectura_Sensor_Temperatura = Sensor_Temperatura.read_u16()
    
        # Convertir valores analógicos a enteros
        s_hum_voltaje = float((Lectura_Sens_Humedad*3)/(2**16))  # convertimos el dato de entrada en el voltaje de entrada
        s_temp_voltaje = float((Lectura_Sensor_Temperatura*3.3)/(2**16))
    
    
        hum = int(100-((s_hum_voltaje-1.5)*100 /1.5)) # convertimos el voltaje de entrada a sus respectivas unidades
        temp = int((s_temp_voltaje*40)/3.3)
        
        if (temp > 30) :
            ventilador.on()
        else:
            ventilador.off()
    
        if hum < 50:
            Bomba.on()
        else:
            Bomba.off()
        
        #print(Lectura_Sens_Humedad)
        print('Volt sens hum = ' + str(s_hum_voltaje) + "    humedad = " + str(hum) + " %")
        print('Volt sens temp= ' + str(s_temp_voltaje) + "   tempertatura = " + str(temp) + "°C")
    
        print("")
        
        
        pantalla()    
        display.ClearScreenCursorHome()
        display.WriteLine('Temperatura= '+str(temp)+'°C',1)
        display.WriteLine('Humedad= '+str(hum)+'% ',2)
    
    
        if hum > 100:
            hum = 0

            #valores.append((valor_17,valor_18))
            valores.append((Lectura_Sens_Humedad, Lectura_Sensor_Temperatura))
            print(f"valores recolectados de pulsaodres : {valor_17}, {valor_18}")
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
    #display = lcd_4bit_mode.LCD16x2(RS,ENABLE,BACK_LIGHT,D4,D5,D6,D7)
    display.BackLightOn()
    display.WriteLine('Ctrl Invernadero',1)
    display.WriteLine('V2 Daniel Amaya',2)
    display.BackLightOff()
    sleep(2)    
    
    print("entrando a ultimo sleep de pantalla()")
    sleep(5)
    print("saliendo de ultimo sleep de pantalla()")
            


async def main():
    
    limpiar_datos_json()  #----------------------------------------------------------------------------------------------------------------------------
    
    while True:
        a.create_task( recolectar_valores())  # Iniciar la recolección de valores
        
        if pulsador_16.value():  # Verifica si el pulsador está en estado alto
            print("pulsador True entrando desde el while if")           
            await online()
            
        else:
            print("El pulsador no está energizado, trabajando de forma local")
            cargar_datos()  # Cargar datos al inicio
            print("antes  del a.create")
            #a.create_task( recolectar_valores())  # Iniciar la recolección de valores
            pantalla()
            print("pasando el a.create")
            #await a.sleep(20)         
            
    
            while True:
                guardar_datos()  # Guardar datos cada cierto tiempo
                print("datos guardados en el json desde el while")
                await a.sleep(60)  # Espera 60 segundos antes de guardar nuevamente
                
                if pulsador_16.value():  # Verifica si el pulsador está en estado alto
                    print("pulsado True entrando desde el while else")
                    await online()  
        
        print("esperando los 5 segundos, fin del while true del main")
        await a.sleep(5)  # Espera 1 segundo antes de volver a verificar

# Ejecutar el bucle principal
a.run(main())