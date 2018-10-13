import routeros_api
import constant

ip_list = []


no_pppoe = []
no_access = []


for ip in ip_list:

    connection = routeros_api.RouterOsApiPool(ip, username=constant.login_02, password=constant.password_25)
    try:
        api = connection.get_api()

        firewall = api.get_resource('/ip/firewall/filter')
        info = firewall.get()

        for i, n in enumerate(info):
            try:
                if n['dst-port'] == '53':
                    firewall.remove(id=str(i))
                else:
                    pass
            except KeyError:
                pass

        try :
            firewall.add(chain='input', protocol='tcp', dst_port='53', in_interface='pppoe-out1', action='drop')
            firewall.add(chain='input', protocol='udp', dst_port='53', in_interface='pppoe-out1', action='drop')
        except routeros_api.exceptions.RouterOsApiCommunicationError:
            no_pppoe.append(ip)

        connection.disconnect()
        print(ip + '  Done')
    except routeros_api.exceptions.RouterOsApiConnectionError:
        print(ip + '  NOT done')
        no_access.append(ip)

print('No access :')
print(no_access)

print('No pppoe :')
print(no_pppoe)
