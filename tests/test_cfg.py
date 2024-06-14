# import xml.etree.ElementTree as ET
# import yaml
# import 

# tree = ET.parse('odbex_cfg.xml')
# root = tree.getroot()

# with open('odbex_cfg.py', 'r') as f:
#     cfg = eval(f)
# print(cfg)

# def cfgparser2():
#     import ConfigParser
#     config = ConfigParser.ConfigParser()
#     config.read('odbex_cfg.ini')


#     print(config)
#     print(config['file_explorer'].getboolean('enable'))   

def json_method() -> None:
    import json
    with open('odbex_cfg.json', 'r') as f:
        lines = ''.join([l.strip() for l in f.readlines() if not l.strip().startswith('//')])
    print(json.loads(lines))
    # print(cfg)

def cfgparser():
    import configparser
    config = configparser.ConfigParser()
    config.read('odbex_cfg.ini')


    print(config)
    print(config['file_explorer'].getboolean('enable'))

if __name__ == '__main__':
    json_method()