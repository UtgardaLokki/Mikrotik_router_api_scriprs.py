
import routeros_api
import datetime
from scanNmapy import ScanNmapy
import constant


ip_list = ['', '']

no_access, communication_error = [], []

update_time = datetime.datetime(2017, 9, 15, 14, 20)
delta = datetime.timedelta(days=0.0005)


for ip in ip_list:
    time = str(update_time)[11:19]

    connection = routeros_api.RouterOsApiPool(ip, username=constant.login_02, password=constant.password_25)
    try:
        api = connection.get_api()
        try:
            task = api.get_resource('/system/scheduler')
            task.add(name='Konstantin check for updates', start_time=time,
                     on_event='system package update check-for-updates' + '\n' + 'system package update download')
            task.add(name='reset', start_time='03:00:00', start_date='Sep/18/2017', on_event='system reboot')
        except routeros_api.exceptions.RouterOsApiCommunicationError:
            communication_error.append(ip)

        connection.disconnect()
        print(ip + '  Done')
    except routeros_api.exceptions.RouterOsApiConnectionError:
        print(ip + '  NOT done')
        no_access.append(ip)

    update_time = update_time + delta


print('No access :')

print(no_access)
