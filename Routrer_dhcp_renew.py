# Renew dhcp-client on Mikrotiks

from librouteros import connect, exceptions
from ipaddress import ip_network
from scanNmapy import ScanNmapy
from datetime import date
from pymongo import MongoClient
import constant


mongo = MongoClient()
loop_log = mongo.script_conf.router_loop
pool = list(ip_network('172.16.0.0/20'))[100:]
today = str(date.today())  # Today date

loop_log.insert_one(dict(day=today, result="Not Done", network="172.16.0.0/20",
                         total_scanned=0, total_renewed=0, report_name='Router ntp setup'))

for ip in pool:
    ip = ip.compressed
    if ScanNmapy.scan_ip(ip) is True:
        loop_log.update_one({"day": today}, {"$inc": {"total_scanned": 1}})

        try:
            api = connect(username=constant.login_02, password=constant.password_25, host=ip)

            interface = api(cmd='/interface/pppoe-client/print')[0]['interface']

            dhcp_client = api(cmd='/ip/dhcp-client/print')
            dhcp_id = {n['interface']: n['.id'] for n in dhcp_client}[interface]

            api(cmd='/ip/dhcp-client/set', **{'use-peer-ntp': 'yes', '.id': dhcp_id, 'use-peer-dns': False,
                                              'add-default-route': False})

            if api(cmd='/system/clock/print')[0]['time-zone-name'] != constant.time_zone_r:
                api(cmd='/system/clock/set', **{'time-zone-name': constant.time_zone_r})
            api(cmd='/system/ntp/client/set', **{'enabled': 'yes', 'primary-ntp': '0.0.0.0'})

            api(cmd='/ip/dhcp-client/renew', **{'.id': dhcp_id})

            loop_log.update_one({"day": today}, {"$inc": {"total_renewed": 1}})

        except exceptions.ConnectionError:
            loop_log.update_one({"day": today}, {"$addToSet": {"error": {"ip": ip, "err": "Error. Timeout"}}})
        except exceptions.TrapError:
            loop_log.update_one({"day": today}, {"$addToSet": {"error": {"ip": ip, "err": "Error. Can not log in!"}}})
        except:
            loop_log.update_one({"day": today}, {"$addToSet": {"error": {"ip": ip, "err": "Error. Can not connect!"}}})

loop_log.update_one({"day": today}, {"$set": {"result": "Finished"}})
