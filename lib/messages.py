import ujson
import lib.logging as logging
import lib.http as http
import lib.mqtt as mqtt

log = logging.getLogger("Messages")

# Send sensors data through MQTT configuration
def send_sensors_via_mqtt(ue):
    mqtt_message = sensors_into_message(ue)
    path = mqtt.TELEMETRY_PATH
    ue.config.mqtt.publish(path, mqtt_message)
    log.info("Sent message: {0} to topic: {1} via MQTT".format(mqtt_message, path))

# Send sensors data through HTTP configuration
def send_sensors_via_http(ue, alarm=False, data=False):
    if alarm is not False:
        message = str(data)
    else:
        message = sensors_into_message(ue)
    type = "POST"
    content_type = "application/json"
    path = token_into_path(ue.config.token, http.TELEMETRY_PATH)
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
    log.info("Sent message: {0} via HTTP".format(packet))

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

#Subscribe to a server's action (e.g the possibility to recieve attribute updates)
def subscribe_to_server(ue, _type='initial'):
    if _type == 'initial':
        path = mqtt.SUBSCRIBE_PATH
    else:
        path = mqtt.ATTRIBUTES_PATH
    if ue.config.mqtt is not None: # MQTT == primary protocol
        ue.config.mqtt.subscribe(path) # NEED work on what the server expects
    elif ue.config.http is not None:
        path = token_into_path(ue.config.token, http.SUBSCRIBE_PATH)
        packet = ue.config.http.http_to_packet("GET", path, None, None)
        if packet is not False: # Send message
            ue.config.http.send_message(packet)
        else:
            log.warning("Missing vital information for an HTTP message: " + packet)

# Send an attribute update to the server
def send_attribute(ue, attr):
    if ue.config.mqtt is not None: # MQTT == primary protocol
        ue.config.mqtt.publish(mqtt.ATTRIBUTES_PATH, attr) # NEED work on what the server expects
    elif ue.config.http is not None:
        path = token_into_path(ue.config.token, http.ATTRIBUTES_PATH)
        content_type = "application/json"
        packet = ue.config.http.http_to_packet("POST", path, content_type, attr)
        if packet is not False: # Send message
            ue.config.http.send_message(packet)
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)

# Request an attribute update from the server
def request_attributes(ue):
    json_obj = {}
    # check if keys are configured, request configured keys
    if ue.config.clientKeys:
        json_obj['clientKeys'] = ','.join(ue.config.clientKeys)
    if ue.config.serverKeys:
        json_obj['serverKeys'] = ','.join(ue.config.serverKeys)
    if ue.config.sharedKeys:
        json_obj['sharedKeys'] = ','.join(ue.config.sharedKeys)
    message = ujson.dumps(json_obj)
    request_id = '1'
    if ue.config.mqtt is not None: # MQTT == primary protocol
        ue.config.mqtt.publish(mqtt.REQUEST_ATTR_PATH + request_id, message) # NEED work on what the server expects
    elif ue.config.http is not None:
        path = token_into_path(ue.config.token, REQUEST_ATTR_PATH)

# Insert token into the path (required for http connections)
def token_into_path(token, path):
    try:
        path = path.replace('token', token)
    except AttributeError as e:
        log.exception()
    return path
