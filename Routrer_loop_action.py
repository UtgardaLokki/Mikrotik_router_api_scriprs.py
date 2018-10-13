from librouteros import connect, exceptions
from ipaddress import ip_network
from scanNmapy import ScanNmapy
from pymongo import MongoClient
from datetime import date
import constant


mongo = MongoClient()
loop_log = mongo.script_conf.router_loop  # path to mongo collection
today = str(date.today())  # Today date
pool = ip_network('172.16.0.0/20')

loop_log.insert_one(dict(day=today, result="Not Done", network="172.16.0.0/20", total_scanned=0, total_renewed=0))

for ip in pool:
    ip = ip.compressed
    if ScanNmapy.scan_ip(ip) is True:
        loop_log.update_one({"day": today}, {"$inc": {"total_scanned": 1}})

        try:
            api = connect(username=constant.login_02, password=constant.password_25, host=ip)
            '''if api(cmd='/interface/pppoe-client/monitor', numbers='pppoe-out1', once='yes')[0]['remote-address'] != '10.255.0.1':
                print(ip + '    already in BGP')
                pass
            else:
                api(cmd='/interface/pppoe-client/set', numbers='pppoe-out1', disabled='yes')
                sleep(1)
                api(cmd='/interface/pppoe-client/set', numbers='pppoe-out1', disabled='no')
            '''

            '''
            if  api(cmd='/interface/pppoe-client/print')[0]['disabled'] == True:
                print(ip + '     pppoe off <=============-----------========  !!!!!!!!!')
            else:
                pass
            '''

            api(cmd='/ip/service/set', numbers="winbox", address=constant.access_pool)

            api(cmd='/ip/service/set', numbers="api", address=constant.access_pool)
            loop_log.update_one({"day": today}, {"$inc": {"total_renewed": 1}})

        except exceptions.ConnectionError:
            loop_log.update_one({"day": today}, {"$addToSet": {"error": {"ip": ip, "err": "Error. Timeout"}}})
        except exceptions.TrapError:
            loop_log.update_one({"day": today}, {"$addToSet": {"error": {"ip": ip, "err": "Error. Can not log in!"}}})
        except:
            loop_log.update_one({"day": today}, {"$addToSet": {"error": {"ip": ip, "err": "Error. Can not connect!"}}})

loop_log.update_one({"day": today}, {"$set": {"result": "Finished"}})
