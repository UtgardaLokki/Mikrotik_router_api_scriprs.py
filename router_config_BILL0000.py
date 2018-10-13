
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser
from time import sleep
from librouteros import connect, exceptions
import constant
from Antenna.scanNmapy import ScanNmapy


print('Configration started')

ip_88_status = 'down'
while ip_88_status == 'down':  # Starts onlu whenn host is up
    ip_88_status = ScanNmapy.scan_ip('192.168.88.1')
    sleep(1)
print('Logged on 192.168.88.1')
api = connect(username='admin', password='', host='192.168.88.1')  # Logging in the router

pool = {'name': 'dhcp', '.id': '*1', 'ranges': '192.168.22.10-192.168.22.254'}
api(cmd='/ip/pool/set', **pool)  # Set another pool of IP address

try:
    version = api(cmd='/system/resource/print')[0]['version']  # Get version of the router

    if float(version[:4]) > 3.8:  # On RouterOS 6.41 there is no master interface and all ports in bridge by default
        address = {'.id': '*1', 'address': '192.168.22.1/24', 'comment': 'defconf', 'interface': 'ether2',
                   'network': '192.168.22.0'}
        api(cmd='/ip/address/set', **address)  # Set another IP address
    else:
        address = {'.id': '*1', 'address': '192.168.22.1/24', 'comment': 'defconf', 'interface': 'ether2-master',
                   'network': '192.168.22.0'}
        api(cmd='/ip/address/set', **address)  # Set another IP address
except exceptions.ConnectionError:
    version = '3.8'
    pass

try:
    version = api(cmd='/system/resource/print')[0]['version']  # Get version of the router
except exceptions.ConnectionError:
    version = '3.8'
    pass


print('Done with 192.168.88.1')
sleep(2)


ip_22_status = 'down'
while ip_22_status == 'down':  # Starts only when host is up
    ip_22_status = ScanNmapy.scan_ip(constant.default_r_ip)
    sleep(1)

api = connect(username='admin', password='', host=constant.default_r_ip)  # Login to the router
print('Logged on 192.168.22.1')
#  all needed settings

try:
    version = api(cmd='/system/resource/print')[0]['version']  # Get version of the router
except exceptions.ConnectionError:
    version = '3.8'
    pass

pppoe_login = input('PPPoE login : ')  # None
pppoe_pass = input('PPPoE password : ')  # None
ssid_input = constant.co_name + '-' + input('SSID : ')  # None
wifi_pass = input('WI-Fi password : ')  # '12345678'

if wifi_pass == "":
    wifi_pass = "12345678"

if pppoe_login == "":
    pppoe_login = "BILL000"

bridge_guest = {'name': 'bridge_guest', 'protocol-mode': 'none'}
api(cmd='/interface/bridge/add', **bridge_guest)

wifi = {'.id': '*1', 'adaptive-noise-immunity': 'ap-and-client-mode', 'band': '2ghz-b/g/n', 'basic-rates-b': '',
        'disabled': 'no', 'distance': 'indoors', 'frequency': 'auto', 'hw-protection-mode': 'rts-cts',
        'mode': 'ap-bridge', 'rate-set': 'configured', 'supported-rates-b': '5.5Mbps,11Mbps',
        'wireless-protocol': '802.11', 'wps-mode': 'disabled'}
api(cmd='/interface/wireless/set', **wifi)

pppoe = {'add-default-route': 'yes', 'disabled': 'no', 'interface': 'ether1', 'max-mru': '1480', 'max-mtu': '1480',
         'mrru': '1600', 'name': 'pppoe-out1', 'use-peer-dns': 'yes', 'user': pppoe_login, 'password': pppoe_pass,
         "default-route-distance": "1"}
api(cmd='/interface/pppoe-client/add', **pppoe)

api(cmd='/interface/wireless/set', numbers=0, ssid=ssid_input)

wifi_secur = {'.id': '*0', 'authentication-types': 'wpa-psk,wpa2-psk', 'eap-methods': '', 'mode': 'dynamic-keys',
              'supplicant-identity': 'MikroTik', 'wpa-pre-shared-key': wifi_pass, 'wpa2-pre-shared-key': wifi_pass}
api(cmd='/interface/wireless/security-profiles/set', **wifi_secur)

wifi_secur_guest = {'authentication-types': 'wpa2-psk', 'eap-methods': '', 'management-protection': 'allowed',
                    'mode': 'dynamic-keys', 'name': 'profile_guest_wifi', 'supplicant-identity': '',
                    'wpa2-pre-shared-key': constant.guest_network_pass}
api(cmd='/interface/wireless/security-profiles/add', **wifi_secur_guest)


wifi_guest = {'disabled': 'no', 'keepalive-frames': 'disabled', 'mac-address': '66:D1:54:8B:38:A7',
              'master-interface': 'wlan1', 'mode': 'ap-bridge', 'multicast-buffering': 'disabled',
              'name': 'Guest Wi Fi', 'security-profile': 'profile_guest_wifi', 'ssid': constant.guest_network_ssid,
              'wds-cost-range': '0', 'wds-default-bridge': 'bridge', 'wds-default-cost': '0',
              'wmm-support': 'enabled', 'wps-mode': 'disabled'}
api(cmd='/interface/wireless/add', **wifi_guest)

pool_guest = {'name': 'dhcp_pool_guest', 'ranges': '192.168.12.101-192.168.12.150'}
api(cmd='/ip/pool/add', **pool_guest)

dhcp = {'.id': '*1', 'address-pool': 'dhcp', 'disabled': 'no', 'interface': 'bridge', 'name': 'defconf'}
api(cmd='/ip/dhcp-server/set', **dhcp)

dhcp_guest = {'address-pool': 'dhcp_pool_guest', 'disabled': 'no', 'interface': 'bridge_guest',
              'lease-time': '12h', 'name': 'dhcp_guest'}
api(cmd='/ip/dhcp-server/add', **dhcp_guest)


if float(version[:4]) <= 3.8:  # On RouterOS 6.41 there is no master interface and all ports in bridge by default
    api(cmd='/interface/set', numbers='1', name='ether2')
    port = {'numbers': '2', 'master-port': 'none'}
    api(cmd='/interface/ether/set', **port)
    port = {'numbers': '3', 'master-port': 'none'}
    api(cmd='/interface/ether/set', **port)

    bridge_port = {'bridge': 'bridge', 'comment': 'defconf', 'interface': 'ether2'}
    api(cmd='/interface/bridge/port/set', **bridge_port)
    bridge_port = {'bridge': 'bridge_guest', 'interface': 'Guest Wi Fi'}
    api(cmd='/interface/bridge/port/add', **bridge_port)
    bridge_port = {'bridge': 'bridge', 'comment': 'defconf', 'interface': 'wlan1'}
    api(cmd='/interface/bridge/port/set', **bridge_port)
    bridge_port = {'bridge': 'bridge', 'comment': 'defconf', 'interface': 'ether3'}
    api(cmd='/interface/bridge/port/add', **bridge_port)
    bridge_port = {'bridge': 'bridge', 'comment': 'defconf', 'interface': 'ether4'}
    api(cmd='/interface/bridge/port/add', **bridge_port)

tracking = {'tcp-established-timeout': '3h'}
api(cmd='/ip/firewall/connection/tracking/set', **tracking)


access_list = {'authentication': 'no', 'interface': 'Guest Wi Fi', 'vlan-mode': 'no-tag'}
api(cmd='/interface/wireless/access-list/add', **access_list)

address_guest = {'address': '192.168.12.1/24', 'interface': 'bridge_guest', 'network': '192.168.12.0'}
api(cmd='/ip/address/add', **address_guest)

dhcp_client = {'.id': '*1', 'add-default-route': 'no', 'dhcp-options': 'clientid,hostname', 'disabled': 'no',
               'interface': 'ether1', 'use-peer-dns': 'no', 'use-peer-ntp': 'no'}
try:
    api(cmd='/ip/dhcp-client/set', **dhcp_client)
except exceptions.TrapError:
    dhcp_client = {'add-default-route': 'no', 'dhcp-options': 'clientid,hostname', 'disabled': 'no',
                   'interface': 'ether1', 'use-peer-dns': 'no', 'use-peer-ntp': 'yes'}
    api(cmd='/ip/dhcp-client/add', **dhcp_client)


dhcp_server_guest = {'address': '192.168.12.0/24', 'dns-server': '192.168.12.1,8.8.8.8', 'gateway': '192.168.12.1'}
api(cmd='/ip/dhcp-server/network/add', **dhcp_server_guest)
dhcp_server = {'.id': '*1', 'address': '192.168.22.0/24', 'comment': 'defconf', 'gateway': constant.default_r_ip,
               'netmask': '24'}
api(cmd='/ip/dhcp-server/network/set', **dhcp_server)

dns = {'allow-remote-requests': 'yes'}
api(cmd='/ip/dns/set', **dns)

api(cmd='/ip/firewall/nat/remove', numbers=0)

rule = {'action': 'drop', 'chain': 'forward', 'comment': 'Deny guest reqests', 'dst-address': '192.168.12.0/24',
        'src-address': '192.168.22.0/24'}
api(cmd='/ip/firewall/filter/add', **rule)
rule = {'action': 'drop', 'chain': 'forward', 'comment': 'Deny guest reqests', 'dst-address': '192.168.22.0/24',
        'src-address': '192.168.12.0/24'}
api(cmd='/ip/firewall/filter/add', **rule)
rule = {'action': 'drop', 'chain': 'input', 'dst-port': '53', 'in-interface': 'pppoe-out1', 'protocol': 'tcp'}
api(cmd='/ip/firewall/filter/add', **rule)
rule = {'action': 'drop', 'chain': 'input', 'dst-port': '53', 'in-interface': 'pppoe-out1', 'protocol': 'udp'}
api(cmd='/ip/firewall/filter/add', **rule)

masquerade = {'action': 'masquerade', 'chain': 'srcnat', 'comment': 'defconf: masqrade', 'out-interface': 'pppoe-out1',
              'src-address-list': ''}
api(cmd='/ip/firewall/nat/add', **masquerade)

dns_static = {'address': constant.default_r_ip, 'name': 'route'}
api(cmd='/ip/dns/static/set', **dns_static)

api(cmd='/ip/firewall/filter/remove', numbers='1,2,3,4,5,6,7,8,9,10')

service_port = {'numbers': 'ftp', 'disabled': 'yes'}
api(cmd='/ip/firewall/service-port/set', **service_port)
service_port = {'numbers': 'tftp', 'disabled': 'yes'}
api(cmd='/ip/firewall/service-port/set', **service_port)
service_port = {'numbers': 'irc', 'disabled': 'yes'}
api(cmd='/ip/firewall/service-port/set', **service_port)
service_port = {'numbers': 'h323', 'disabled': 'yes'}
api(cmd='/ip/firewall/service-port/set', **service_port)
service_port = {'numbers': 'sip', 'disabled': 'yes'}
api(cmd='/ip/firewall/service-port/set', **service_port)
service_port = {'numbers': 'pptp', 'disabled': 'yes'}
api(cmd='/ip/firewall/service-port/set', **service_port)

ip_service = {'numbers': 'telnet', 'disabled': 'yes'}
api(cmd='/ip/service/set', **ip_service)
ip_service = {'numbers': 'ftp', 'disabled': 'yes'}
api(cmd='/ip/service/set', **ip_service)
ip_service = {'numbers': 'www', 'disabled': 'yes'}
api(cmd='/ip/service/set', **ip_service)
ip_service = {'numbers': 'ssh', 'disabled': 'yes'}
api(cmd='/ip/service/set', **ip_service)
ip_service = {'numbers': 'api-ssl', 'disabled': 'yes'}
api(cmd='/ip/service/set', **ip_service)

snmp = {'enabled': 'yes'}
api(cmd='/snmp/set', **snmp)

time_zone = {'time-zone-name': constant.time_zone_r}
api(cmd='/system/clock/set', **time_zone)

identity = {'name': pppoe_login}
api(cmd='/system/identity/set', **identity)

api(cmd='/system/ntp/client/set', **{'enabled': 'yes'})

boot = {'boot-device': 'flash-boot-once-then-nand'}
api(cmd='/system/routerboard/settings/set', **boot)
'6.41 (stable)'

password = {'.id': '*1', 'password': constant.default_r_pass}  # Set password to admin user
api(cmd='/user/set', **password)

mac = api(cmd='/interface/ethernet/print')[0].get("mac-address")

print('Finished ' + pppoe_login)
print('ether1 ' + mac)

