import re
import urllib2
import collectd


PLUGIN_NAME = 'nginx_sla'
INTERVAL = 10  # seconds

SLAURL = None
PREFIXES = None

regex = re.compile(r'(\w+)\.((.+:\d+)|(\w+))\.(\S+)\s*=\s*(\d+)')


def configure_callback(conf):
    global SLAURL
    global PREFIXES
    for c in conf.children:
        if c.key == 'SLAURL':
            SLAURL = c.values[0]
        elif c.key == 'PREFIXES':
            PREFIXES = c.values  # type = tuple
        else:
            collectd.warning('nginx_sla plugin: Unknown config key: %s.' % c.key)


def get_data(url):
    response = urllib2.urlopen(urllib2.Request(url))
    data = response.read()
    return data


def parse_line(line):
    result = {}
    found = regex.search(line)
    result['pool'] = found.group(1)
    result['upstream'] = found.group(2)
    result['gauge'] = found.group(5)
    result['value'] = int(found.group(6))
    return result


def collect_data():
    global SLAURL
    global PREFIXES
    data = get_data(SLAURL)
    data_list = []
    for line in data.split('\n'):
        line = line.strip()
        if not line or not line.startswith(PREFIXES):
            continue
        try:
            data_dict = parse_line(line)
        except Exception:
            continue
        data_list.append(data_dict)
    return data_list


def dispatch_value(value_dict):
    val = collectd.Values(plugin=PLUGIN_NAME)
    val.plugin_instance = value_dict['pool'] + '.' + value_dict['upstream']
    val.type = 'count'
    val.type_instance = value_dict['gauge']
    val.values = [value_dict['value']]
    val.dispatch()


def read():
    data = collect_data()
    for value_dict in data:
        dispatch_value(value_dict)

collectd.register_config(configure_callback)
collectd.register_read(read, INTERVAL)

