import re
import logging

log = logging.getLogger("Validate")

NAME_REGEX = "[A-Za-z0-9_]+"
TOKEN_REGEX = "[A-Za-z0-9]+"
PROTOCOL_REGEX = "MQTT||HTTP"
PORT_REGEX = "[0-9]+"

def is_valid_type(user_input, expected_type):
    if expected_type == 'string':
        return True if isinstance(user_input, str) else False
    elif expected_type == 'list':
        return True if isinstance(user_input, list) else False
    elif expected_type == 'int':
        try:
            user_input = int(user_input)
            return True
        except ValueError:
            return False
    elif expected_type == 'float':
        try:
            user_input = float(user_input)
            return True
        except ValueError:
            return False
    else:
        log.error("Function 'is_valid_type' called for unknown input type")
    return False


def is_valid_string(user_input, arg):
    if not is_valid_type(user_input, "string"): return False
    if arg == 'name':
        return match_regex(NAME_REGEX, user_input)
    elif arg == 'token':
        return match_regex(TOKEN_REGEX, user_input)
    else:
        log.error("Function 'is_valid_string' called for unknown string type")
    return False


def is_valid_remote_server(user_input):
    user_input = user_input.split(':')
    if len(user_input) != 3:
        return False
    else:
        if not match_regex(PROTOCOL_REGEX, user_input[0]): return False
        if not match_regex(PORT_REGEX, user_input[2]):
            return False
        else:
            try:
                if int(user_input[2]) > 65535: return False
            except ValueError:
                return False
        if not is_valid_ip(user_input[1]): return False
    return True


def match_regex(regex, user_input):
    try:
        re.match("^" + regex + "$", user_input).group(0)
        return True
    except AttributeError:
        return False


def is_valid_lte_bands(bands):
    if not is_valid_type(bands, "list"): return False
    for band in bands:
        try:
            band = int(band)
        except ValueError:
            return False
        if band < 1 or band > 44: return False
    return True


#[2,"PycomWifi","p@ssw0rd",11,0,"172.17.60.2","255.255.255.0"]
def is_valid_wifi(input):
    if not is_valid_type(input, "list") or not len(input) in [7,9]: return False
    # check AP/STATION conf
    try:
        if int(input[0]) not in [1,2]: return False
    except ValueError:
        return False
    # check ssid, password, default GW, subnet
    if (not is_valid_string(input[1], "name") \
        or not is_valid_type(input[2], "string") \
        or not is_valid_ip(input[5]) \
        or not is_valid_subnet(input[6])):
        return False
    # check channel
    if is_valid_type(input[3], "int"):
        if int(input[3]) < 0 or int(input[3]) > 14: return False
    else:
        return False
    # check antenna conf
    if is_valid_type(input[4], 'int'):
        if int(input[4]) not in [0,1]: return False
    else:
        return False
    if len(input) == 7: return True
    # check local ip address, subnet
    if not is_valid_ip(input[7]) or not is_valid_subnet(input[8]): return False
    return True



def is_valid_subnet(ip):
    if not is_valid_ip(ip):
        return False
    try:
        a, b, c, d = (int(octet) for octet in ip.split("."))
    except ValueError:
        return False
    mask = a << 24 | b << 16 | c << 8 | d
    if mask == 0:
        return False
    m = mask & -mask
    right0bits = -1
    while m:
        m >>= 1
        right0bits += 1
    # Verify that all the bits to the left are 1's
    if mask | ((1 << right0bits) - 1) != 0xffffffff:
        return False
    return True


def is_valid_ip(ip):
    ip = ip.split('.')
    if len(ip) != 4: return False
    for oct in ip:
        try:
            if (int(oct) < 0 or int(oct) > 255): return False
        except ValueError:
            return False
    return True
