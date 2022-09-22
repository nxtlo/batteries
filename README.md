# batteries
A robust communication service between devices and websocket server using ZeroMQ.


## Example application

```py
from message_service import gateway, devices, enums

# server.py
server = gateway.Gateway()

await server.open()

# clients.py

# Connect to the gateway.
device = devices.Device()

await device.open()
# Send a signal to the gateway that we want to open connection.
await device.signal(enums.Signal.OPEN)
# Restart the device.
await device.signal(enums.Signal.RESTART)
# Close.
await device.close()

```

### Results in
```py
INFO:connector: Connected to gateway...
DEBUG:connector: Device IP: 172.17.8.209 Name: web-22 Event: OPEN
INFO:connector: {'web-22': DeviceView(host_name='web-22', ip_address='172.17.8.209', mac_address='85:03:45:1c:b6:9b', signal=<Signal.OPEN: 2>)}       
DEBUG:connector: Device IP: 172.17.8.209 Name: web-22 Event: RESTART
INFO:connector: Restarting device web-22
DEBUG:connector: Device IP: 172.17.8.209 Name: web-22 Event: CLOSE
```
