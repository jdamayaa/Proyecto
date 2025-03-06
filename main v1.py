import anvil.pico
import uasyncio as a
from machine import Pin

# This is an example Anvil Uplink script for the Pico W.
# See https://anvil.works/pico for more information

UPLINK_KEY = "server_E7UCJ6I7S3P6DI7CDEVVIWZZ-HAK33GEK53MS7OGY"

# We use the LED to indicate server calls and responses.
led = Pin("LED", Pin.OUT, value=1)
pulsador = Pin(16, Pin.IN)


# Call this function from your Anvil app:
#
#    anvil.server.call('pico_fn', 42)
#

@anvil.pico.callable(is_async=True)
async def pico_fn(n):
    # Output will go to the Pico W serial port
    print(f"Called local function with argument: {n}")
    if pulsador.value():  # El pulsador está energizado (estado alto)
        print("El pulsador está energizado.")
    else:
        print("El pulsador no está energizado.")    

    # Blink the LED and then double the argument and return it.
    for i in range(10):
        led.toggle()
        await a.sleep_ms(50)
    return n * 2


# Connect the Anvil Uplink. In MicroPython, this call will block forever.

anvil.pico.connect(UPLINK_KEY)
    


# There's lots more you can do with Anvil on your Pico W.
#
# See https://anvil.works/pico for more information


