import ujson
import lib.logging as logging
from lib.http import TELEMETRY_PATH, SUBSCRIBE_PATH_MQTT, SUBSCRIBE_PATH_HTTP, ATTRIBUTES_PATH

log = logging.getLogger("Messages")

# Send sensors data through MQTT configuration
def send_sensors_via_mqtt(ue):
    mqtt_message = sensors_into_message(ue)
    path = token_into_path(ue.config.token, TELEMETRY_PATH)
    ue.config.mqtt.publish(path, smqtt_message)

# Send sensors data through HTTP configuration
def send_sensors_via_http(ue, alarm=False, data=False):
    if alarm is not False:
        message = str(data)
    else:
        message = sensors_into_message(ue)
    type = "POST"
    content_type = "application/json"
    path = token_into_path(ue.config.token, TELEMETRY_PATH)
    packet = ue.config.http.http_to_packet(type, path, content_type, message)
    if packet is not False:
        ue.config.http.send_message(packet)
        #wait_for_answer
            #if ack good
            #else if 400 bad http request
            #else if 401 bad token
            #else if 404 resource not found
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

# Take a list of sensor objects and turn into a single json string.
def sensors_into_message(ue):
    ue.sensors_dict = {}
    for sensor in ue.config.sensors:
        # Do not add alarms to regular telemetry
        if 'Alarm' in sensor.type:
            continue
        value = sensor.get_value()
        if len(sensor.type) == 1:
            if value is None:
                ue.add_sensor_to_dict(sensor.name, sensor.type[0], '')
            else:
                ue.add_sensor_to_dict(sensor.name, sensor.type[0], value)
        else:
            for i in range(len(sensor.type)):
                if value is None:
                    ue.add_sensor_to_dict(sensor.name, sensor.type[i], '')
                else:
                    ue.add_sensor_to_dict(sensor.name, sensor.type[i], value[i])
    http_payload = ujson.dumps(ue.sensors_dict)
    return http_payload

def subscribe_to_server(ue):
    if ue.config.mqtt is not None: # MQTT == primary protocol
        path = token_into_path(ue.config.token, SUBSCRIBE_PATH_MQTT)
        ue.config.mqtt.subscribe(path) # NEED work on what the server expects
    elif ue.config.http is not None:
        path = token_into_path(ue.config.token, SUBSCRIBE_PATH_HTTP)
        packet = ue.config.http.http_to_packet("GET", path, None, None)
        if packet is not False: # Send message
            ue.config.http.send_message(packet)
        else:
            log.warning("Missing vital information for an HTTP message: " + packet)

def send_attribute(ue, attr):
    path = token_into_path(ue.config.token, ATTRIBUTES_PATH)
    if ue.config.mqtt is not None: # MQTT == primary protocol
        ue.config.mqtt.publish(path, attr) # NEED work on what the server expects
    elif ue.config.http is not None:
        content_type = "application/json"
        packet = ue.config.http.http_to_packet("POST", path, content_type, attr)
        if packet is not False: # Send message
            ue.config.http.send_message(packet)
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

def request_attributes(ue):
    if ue.config.mqtt is not None: # MQTT == primary protocol
        path = token_into_path(ue.config.token, MQTT_REQUEST_ATTR)
        ue.config.mqtt.publish(path, attr) # NEED work on what the server expects
    elif ue.config.http is not None:
        path = token_into_path(ue.config.token, HTTP_REQUEST_ATTR)

def token_into_path(token, path):
    try:
        path = path.replace('token', token)
    except AttributeError as e:
        log.exception()
    return path
