import xmlrpclib
from datetime import timedelta, datetime
import time
from ConfigParser import ConfigParser

import anviz

Config = ConfigParser()
Config.read('/etc/odoo_clock.conf')
dbname = Config.get("odooserver", 'dbname')
username = Config.get("odooserver", 'username')
pwd = Config.get("odooserver", 'pwd')
url = Config.get("odooserver", 'url')

sock_common = xmlrpclib.ServerProxy(url + 'xmlrpc/common')

uid = sock_common.login(dbname, username, pwd)
sock = xmlrpclib.ServerProxy(url + 'xmlrpc/object')

devices = {
    '2': (2, '192.168.89.220', 8010),
    #'1': (1, '192.168.93.8', 5010),
    '3': (3, '192.168.94.12', 8010),
    '5': (5, '192.168.97.12', 8010),
    '7': (7, '192.168.96.205', 5010),
    #'9': (9, '192.168.91.10', 8009),
    '11': (11, '192.168.90.15', 8085),

}


def create(attendance):
    args = [('name', '=',  str(attendance['employee_id']) + str(attendance['name'])),
            ('module', '=', "anvis_xmlrcp"),
            ('model', '=', 'hr.attendance'),
            ]

    external_id = sock.execute(
        dbname, uid, pwd, 'ir.model.data', 'search', args)
    if not external_id:

        odooObject_id = sock.execute(
            dbname, uid, pwd, 'hr.attendance', 'create', attendance)

        external_link = {
            'name':  str(attendance['employee_id']) + str(attendance['name']),
            'module':  "anvis_xmlrcp",
            'model': 'hr.attendance',
            'res_id': odooObject_id,
        }
        external_id = sock.execute(
            dbname, uid, pwd, 'ir.model.data', 'create', external_link)
        print "creado %r %r " % (str(attendance['employee_id']), str(attendance['name']))
    else:
        print "ya existe %r %r " % (str(attendance['employee_id']), str(attendance['name']))


def device_start(device):
    clock = anviz.Device(device_id=devices[device][0], ip_addr=devices[
                         device][1], ip_port=devices[device][2])

    print("Conectado a %s " % devices[device][1])
    clock.set_datetime(datetime.now())
    print("Fecha actualizada a %s " % clock.get_datetime())

    employees_rel = {}
    employees = sock.execute(dbname, uid, pwd, 'hr.employee', 'search_read', [
                             ('anviz_code', '!=', False)], ['id', 'user_id', 'anviz_code'])
    for employee in employees:
        employees_rel[employee['anviz_code']] = employee['id']

    try:
        record = clock.download_new_records()
        #record = clock.download_all_records()
        for row in record:
            if row.type == 2:
                continue

            if str(row.code) in employees_rel.keys():
                action = 'sign_in' if row.type == 0 else 'sign_out'
                hr_attendance = {
                    'employee_id': employees_rel[str(row.code)],
                    'name': (row.datetime + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                    #'name' : parser.parse(row['Fecha/Hora']),
                    'action': action
                }
                create(hr_attendance)
            else:
                print "sin registro %r %s " % (row.code, row.datetime)
    except:
        time.sleep(7)
        print "segundo intento"
        clock = anviz.Device(device_id=devices[device][0], ip_addr=devices[
                         device][1], ip_port=devices[device][2])

        record = clock.download_new_records()
        #record = clock.download_all_records()
        for row in record:
            if row.type == 2:
                continue
	    #if (row.datetime + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S') <  datetime.datetime('2021-05-29'):
            #    continue
            if str(row.code) in employees_rel.keys():
                action = 'sign_in' if row.type == 0 else 'sign_out'
                hr_attendance = {
                    'employee_id': employees_rel[str(row.code)],
                    'name': (row.datetime + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S'),
                    #'name' : parser.parse(row['Fecha/Hora']),
                    'action': action
                }
                create(hr_attendance)
            else:
                print "sin registro %r %s " % (row.code, row.datetime)


if __name__ == '__main__':

    for dev in devices.keys():
        try:
            device_start(dev)
        except Exception as e:
            print ('error en %s' % dev)
