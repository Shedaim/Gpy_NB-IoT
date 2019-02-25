import lib.logging as logging

log = logging.getLogger("Variable_functions")

def update_initial_file(json_string):
    with open('Initial_configuration.json', 'w') as f:
        f.write(json_string)

def list_string_to_list(keys_string):
    assert keys_string.startswith('[') and keys_string.endswith(']'), "Keys received are not a list"
    keys_string = keys_string[1:-1]
    return keys_string.split(',')
