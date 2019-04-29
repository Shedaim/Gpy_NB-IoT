import ujson
import logging
import networking.http as http
import networking.robust_mqtt as mqtt

log = logging.getLogger("Messages")

# Send sensors data through MQTT configuration
def send_sensors_via_mqtt(ue, alarm=False, data=False):
    if alarm is not False:
        mqtt_message = str(data)
    else:
        mqtt_message = sensors_into_message(ue)
    path = mqtt.TELEMETRY_PATH
    ue.remote_server.mqtt.publish(path, mqtt_message)
    log.info("Sent message: {0} to topic: {1} via MQTT".format(mqtt_message, path))


# Send sensors data through HTTP configuration
def send_sensors_via_http(ue, alarm=False, data=False):
    if alarm is not False:
        message = str(data)
    else:
        message = sensors_into_message(ue)
    _type = "POST"
    content_type = "application/json"
    path = token_into_path(ue.token, http.TELEMETRY_PATH)
    packet = ue.remote_server.http.http_to_packet(_type, path, content_type, message)
    if packet is not False:
        ue.remote_server.http.send_message(packet)
        # NEED to manage exceptions and code errors
    else:
        log.warning("Missing vital information for an HTTP message: " + packet)
    log.info("Sent message: {0} via HTTP".format(packet))


# Take a list of sensor objects and turn into a single json string.
def sensors_into_message(ue):
    sensors_dict = {}
    for sensor in ue.sensors:
        # Do not add alarms to regular telemetry
        if 'Alarm' in sensor.type:
            continue
        value = sensor.get_value()
        if value is None:
            continue
        if len(sensor.type) == 1:
            if value is None:
                add_sensor_to_dict(sensors_dict, sensor.name, sensor.type[0], '')
            else:
                add_sensor_to_dict(sensors_dict, sensor.name, sensor.type[0], value)
        else:
            for i in range(len(sensor.type)):
                if value is None:
                    add_sensor_to_dict(sensors_dict, sensor.name, sensor.type[i], '')
                else:
                    add_sensor_to_dict(sensors_dict, sensor.name, sensor.type[i], value[i])
    http_payload = ujson.dumps(sensors_dict)
    return http_payload

# Add (key, value) to sensors dictionary
def add_sensor_to_dict(sensors_dict, name, key, value):
    if key in sensors_dict:  # Key already in dictionary
        key = key + "_" + name
    sensors_dict[key] = value
    return sensors_dict


# Send an attribute update to the server
def send_attribute(ue, attr):
    if ue.remote_server.mqtt is not None:  # MQTT == primary protocol
        ue.remote_server.mqtt.publish(mqtt.ATTRIBUTES_PATH, attr)  # NEED work on what the server expects
    elif ue.remote_server.http is not None:
        path = token_into_path(ue.token, http.ATTRIBUTES_PATH)
        content_type = "application/json"
        packet = ue.remote_server.http.http_to_packet("POST", path, content_type, attr)
        if packet:  # Send message
            ue.remote_server.http.send_message(packet)
        else:
            log.warning("Failed to create HTTP message.")


# Request an attribute update from the server  (Used primarily as initial configuration)
def request_attributes(remote_server, client_attributes, server_attributes, shared_attributes):
    json_obj = {}
    # check if keys are configured, request configured keys
    if client_attributes:
        json_obj['clientKeys'] = ','.join(client_attributes)
    if server_attributes:
        json_obj['serverKeys'] = ','.join(server_attributes)
    if shared_attributes:
        json_obj['sharedKeys'] = ','.join(shared_attributes)
    message = ujson.dumps(json_obj)
    request_id = '1'  # Different ID may be used, but response will arrive with same ID. No need to implement yet.
    if remote_server.mqtt is not None:  # MQTT == primary protocol
        remote_server.mqtt.publish(mqtt.REQUEST_ATTR_PATH + request_id, message)
    elif remote_server.http is not None:
        path = token_into_path(remote_server.token, http.ATTRIBUTES_PATH)
        # TODO to implement - this is different than the MQTT publish.


# Insert token into the path (required for http connections)
def token_into_path(token, path):
    try:
        path = path.replace('token', token)
    except AttributeError:
        log.exception()
    return path
