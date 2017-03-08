import os
import argparse
import xlsxwriter

def ping(ip):
    return os.popen('ping -c 1 -W 2 ' + ip + ' >/dev/null 2>&1 && echo "available" || echo "failed"').readline()[:-1]

def format_data(text):
    return [line.strip().split(',') for line in text]

def get_info(data, array):
    print "*"*75
    print "array:\n\t%s" % array

    #get spa spb ip from swarm
    FLAG = 0
    ip_list = os.popen('timeout 3 swarm --showipinfo ' + array +' 2>/dev/null|xargs -n 1|tail -2').readlines()
    if ip_list == ['\n']:
        print "Can't find in Swarm or Swarm is blocked."
        FLAG = 1
        
    #if array in swarm, get ip and check ping status of SPA SPB
    if FLAG == 0:
        ip_spa, ip_spb = [item.strip() for item in ip_list]
        ping_spa = ping(ip_spa)
        ping_spb = ping(ip_spb)
        if ping_spa == 'available' and ping_spb == 'available':
            ip = ip_spa
        elif ping_spa == 'available' and ping_spb == 'failed':
            FLAG = 2
            ip = ip_spa
        elif ping_spa == 'failed' and ping_spb == 'available':
            FLAG = 3 
            ip = ip_spb
        else:
            FLAG = 4

    #init data[array] dict
    data[array] = dict()
    data[array]['SLIC'] = dict()
    for slot in range(6):
        data[array]['SLIC'][slot] = dict()
        data[array]['SLIC'][slot]['Port'] = dict()
        for item in ['Name', 'Inserted', 'Type']:
            data[array]['SLIC'][slot][item] = ''
        for port in range(6):
            data[array]['SLIC'][slot]['Port'][port] = dict()
            for item in ['Type', 'Link Status', 'SFP']:
                data[array]['SLIC'][slot]['Port'][port][item] = '' 
    data[array]['Drives'] = dict()
    for num in range(6):
        data[array]['Drives'][num] = dict()
        for item in ['Type', 'Size', 'Speed', 'Number']:
            data[array]['Drives'][num][item] = ''
    data[array]['DAE'] = dict()
    for num in range(6):
        data[array]['DAE'][num] = dict()
        for item in ['ID', 'Type']:
            data[array]['DAE'][num][item]  = ''

    #return when swarm blocked or both SPs ping failed
    if FLAG == 1:
        data[array]['Status'] =  "can't find in swarm"
        return
    elif FLAG == 4:
        data[array]['Status'] =  'spa ping failed\nspb ping failed'
        return

    #get primary SP
    sp_primary = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip + ' -i /c4shares/Public/ssh/id_rsa.root crm_mon -1 | grep ECOM | awk \'{print $NF}\'').readline()[:-1]
    print "ip_spa:\n\t%s\t%s\nip_spb:\n\t%s\t%s\nsp_primary:\n\t%s" % (ip_spa, ping_spa, ip_spb, ping_spb, sp_primary)
    if sp_primary == '':
        data[array]['Status'] =  "can't get primary sp"
        return
    ip_primary = ip_spa if sp_primary == 'spa' else ip_spb

    #get configuration from primary SP
    ping_sp_primary = ping(ip_primary)
    if ping_sp_primary == 'available':
        #[get info of SLIC]
        data_slic = os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root speclcli -getiomodulestatus|grep -E -A3 "IO Module|Onboard IO"|sed -n "/IO Module/{P;n;n;P;n;P};/Onboard IO/{P;n;n;P;n;P}"|sed -r "s/.*(IO Module-[AB][01]).*/\1/;s/.*: (False|True).*/\1/;s/.*(SP[AB] Onboard).*/\1/;s/.*Timestamp.*//;s/.*Unique ID.*: (\w+)\b.*/\1/;s/.*: (Oberon SP).*/\1/"|sed "N;N;s/\n/,/g"|sed -r "s/(.*A)(0|1)(.*)/\2,\1\2\3/;/B0/s/^/3,/;/B1/s/^/4,/;/SPA Onboard.*/s/^/2,/;/SPB/s/^/5,/"').readlines()
        if len(data_slic) != 0:
            data_slic = format_data(data_slic)
            for item in data_slic:
                slot = int(item[0])
                data[array]['SLIC'][slot]['Name'] = item[1]
                data[array]['SLIC'][slot]['Inserted'] = item[2]
                data[array]['SLIC'][slot]['Type'] = item[3]
        print "data_slic:\n\t%s" % data_slic
        #[get info of Port] 
        #get port link status of non-onboard io-modules
        data_iom = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "_iom_"|grep -E "ID|Health details"|sed "s/.*down.*/down/;s/.*normally.*/normally/;s/.*removed.*/SFP-removed/;s/^.*= //"|sed -r "s/(sp[ab]_iom_)([0-1])(_.*)([0-3])(.*)/\2,\4,\1\2\3\4\5/"|sed -r "s/^0(.*spb.*)/3\1/;s/^1(.*spb.*)/4\1/"|sed "s/sp.*eth./iSCSI/;s/sp.*sas./SAS/;s/sp.*fc./FC/"|sed "$!N;s/\n/,/"|sort').readlines()
        data_iom = format_data(data_iom)
        if len(data_iom) != 0:
            for item in data_iom:
                slot = int(item[0])
                port = int(item[1])
                data[array]['SLIC'][slot]['Port'][port]['Type'] = item[2]
                data[array]['SLIC'][slot]['Port'][port]['Link Status'] = item[3]
        print "data_iom:\n\t%s" % data_iom
        #get SAS, iSCSI, CNA port's link status of onboard io-module
        data_sas = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "sp[ab]_sas[01]"|grep -E "ID|Health details"|sed -r "s/(.*)(sp[ab]_sas)([01])/\3,\2\3/"|sed "/spa/s/^/2,/;/spb/s/^/5,/;s/.*down.*/down/;s/.*normal.*/normal/;s/.*removed.*/SFP-removed/"|sed "s/sp._sas./SAS/"|sed "$!N;s/\n/,/"|sort').readlines()
        data_iscsi = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "sp[ab]_eth[23]"|grep -E "ID|Health details"|sed -r "s/(.*)(sp[ab]_eth)([23])/\3,\2\3/"|sed "/spa/s/^/2,/;/spb/s/^/5,/;s/.*down.*/down/;s/.*normal.*/normal/;s/.*removed.*/SFP-removed/"|sed "s/sp._eth./iSCSI/"|sed "$!N;s/\n/,/"|sort').readlines()
        data_cna_fc = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port/fc show -detail|grep -A10 "sp[ab]_fc[45]"|grep -E "ID|Health details"|sed -r "s/(.*)(sp[ab]_fc)([45])/\3,\2\3/"|sed "/spa/s/^/2,/;/spb/s/^/5,/;s/.*down.*/down/;s/.*normal.*/normal/;s/.*removed.*/SFP removed/;s/.*not supported.*/SFP unsupported/"|sed "s/sp._fc./FC/"|sed "N;s/\n/,/"|sort').readlines()
        data_cna_iscsi =  os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "sp[ab]_eth[45]"|grep -E "ID|Health details"|sed -r "s/(.*)(sp[ab]_eth)([45])/\3,\2\3/"|sed "/spa/s/^/2,/;/spb/s/^/5,/;s/.*down.*/down/;s/.*normal.*/normal/;s/.*removed.*/SFP-removed/;s/.*not supported.*/SFP unsupported/"|sed "s/sp._eth./iSCSI/"|sed "N;s/\n/,/"|sort').readlines()
        data_cna = data_cna_fc if data_cna_fc != [] else data_cna_iscsi
        data_iom_onboard = list()
        for item in [data_sas, data_iscsi, data_cna]:
            if item != []:
                data_iom_onboard += format_data(item)
        if len(data_iom_onboard) != 0:
            for item in data_iom_onboard:
                if item != []:
                    slot = int(item[0])
                    port = int(item[1])
                    data[array]['SLIC'][slot]['Port'][port]['Type'] = item[2]
                    data[array]['SLIC'][slot]['Port'][port]['Link Status'] = item[3]
        print "data_iom_onboard:\n\t%s" % data_iom_onboard

    #get SFP info
    data_sfp_spa = list()
    data_sfp_spb = list()
    if ping_spa == 'available':
        data_sfp_spa = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_spb + ' -i /c4shares/Public/ssh/id_rsa.root speclcli -getiomodulestatus verbose|grep -A3 -B70 "EMC Info"|sed "s/.*FCLF8522P2BTL-E5.*/EMC PN: 1Gb-iSCSI/"|grep -E "Module Index|Physical Port Index|EMC PN"|grep -B2 "EMC PN"|sed "/--/d"|awk \'{print $NF}\'|' + r'sed -r "N;N;s/\n/,/g"').readlines()
    if ping_spb == 'available':
        data_sfp_spb = os.popen('ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_spb + ' -i /c4shares/Public/ssh/id_rsa.root speclcli -getiomodulestatus verbose|grep -A3 -B70 "EMC Info"|sed "s/.*FCLF8522P2BTL-E5.*/EMC PN: 1Gb-iSCSI/"|grep -E "Module Index|Physical Port Index|EMC PN"|grep -B2 "EMC PN"|sed "/--/d"|awk \'/Module Index/{print $NF+3}/Physical Port Index|EMC PN/{print $NF}\'|' + r'sed -r "N;N;s/\n/,/g"').readlines()
    data_sfp = list()
    for item in [data_sfp_spa, data_sfp_spb]:
        if item != []:
            data_sfp += format_data(item)
    if len(data_sfp) != 0:
        for item in data_sfp:
            slot = int(item[0])
            port = int(item[1])
            data[array]['SLIC'][slot]['Port'][port]['SFP'] = item[2]
    print "data_sfp:\n\t%s" % data_sfp

    #get Drives info
    data_drives = os.popen("ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root " + ip_primary + " -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /stor/config/dg show|grep -E 'Drive type|Vendor size|Rotational speed|Number of drives'|awk -F '.*= ' '{print $NF}'" + r"|sed 'N;N;N;s|\n|,|g'|sort").readlines()
    if data_drives != []:
        data_drives = format_data(data_drives)
        for i in range(len(data_drives)):
            if i >= 6:
                data[array]['Drives'][i] = dict()
            for j,item in enumerate(['Type', 'Size', 'Speed', 'Number']):
                data[array]['Drives'][i][item] = data_drives[i][j]
    print "data_drives:\n\t%s" % data_drives
    #get DAE info 
    data_dae = os.popen("ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root " + ip_primary + r" -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /env/dae show -detail|awk '/ID/{print $4}/Model/{print $3}'|sed 'N;s/\n/,/'|sort").readlines()
    if data_dae != []:
        data_dae = format_data(data_dae)
        for i in range(len(data_dae)):
            if i >= 6:
                data[array]['DAE'][i] = dict()
            for j,item in enumerate(['ID', 'Type']):
                data[array]['DAE'][i][item] = data_dae[i][j]
    print "data_dae:\n\t%s" % data_dae
    
    #add "Status' flag to data map
    if FLAG ==  2:
        data[array]['Status'] = 'spb ping failed'
    elif FLAG ==  3:
        data[array]['Status'] = 'spa ping failed'

    #print "data[%s]:\n\t%s" % (array, data[array])
    return 

def save_to_excel(data, file_name, sheet_name):
    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet(sheet_name)

    #set sheet tab and row/column
    worksheet.set_tab_color('red')
    for col in ['A:B','D:D','F:G','I:J','L:M','O:P','R:S','U:Y','AA:AB']:
        worksheet.set_column(col, 11)
    for col in ['C:C','E:E','H:H','K:K','N:N','Q:Q','T:T','Z:Z']:
        worksheet.set_column(col, 8)
    for row in range(3):
       worksheet.set_row(row, 15)

    # create some formats to use.
    status_format = workbook.add_format({'color':'red'})
    cell_format1 = workbook.add_format({'font_name':'Arial','border':1,'align':'center','valign':'vcenter','text_wrap':1})
    cell_format2 = workbook.add_format({'font_name':'Arial','font_size':10,'align':'center','valign':'vcenter','text_wrap':1})
    cell_format_r_border = workbook.add_format({'font_name':'Arial','font_size':10,'right':1,'align':'center','valign':'vcenter','text_wrap': 1})
    cell_format_b_border = workbook.add_format({'font_name':'Arial','font_size':10,'bottom':1,'align':'center','valign':'vcenter','text_wrap': 1})
    cell_format_rb_border = workbook.add_format({'font_name':'Arial','font_size':10,'right':1,'bottom':1,'align':'center','valign':'vcenter','text_wrap':1})

    #populate worksheet header
    slic_items = ['Name', 'Inserted', 'Type']
    port_nums = ['Port0', 'Port1', 'Port2', 'Port3', 'Port4', 'Port5']
    port_items = ['Type', 'Link Status', 'SFP']
    drives_items = ['Type', 'Size', 'Speed', 'Number']
    dae_items = ['ID', 'Type']       

    worksheet.merge_range('A1:A3','Storage System', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','text_wrap':1,'fg_color':'yellow'}))
    worksheet.merge_range('B1:D1','SLIC', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCFFFF',}))
    worksheet.merge_range('E1:V1','Port && SFP', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))
    worksheet.merge_range('W1:Z1','Drives', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCFFCC',}))
    worksheet.merge_range('AA1:AB1','DAE', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'FFCC99',}))

    for i,item in enumerate(slic_items):
        worksheet.merge_range(1,i+1,2,i+1,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCFFFF',}))
    for i,item in enumerate(drives_items):
        worksheet.merge_range(1,i+22,2,i+22,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCFFCC',}))
    for i,item in enumerate(dae_items):
        worksheet.merge_range(1,i+26,2,i+26,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#FFCC99',}))
    for i, item in enumerate(port_nums):       
        worksheet.merge_range(1,i*3+4,1,i*3+6,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))
    for i in range(6):       
        for j, item in enumerate(port_items):       
            worksheet.write_string(2,i*3+4+j,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))

    #populate worksheet data
    row = 3
    for array in sorted(data):
        n_drives = len(data[array]['Drives'])
        n_dae = len(data[array]['DAE'])
        n = 6 if (n_drives <=6 and n_dae <=6) else (n_drives if n_drives > n_dae else n_dae)
        #set width of rows
        for i in range(n):
            worksheet.set_row(row+i, 15)
        #add '' to write excel    
        if n > 6:
            for slot in range(6, n):
                data[array]['SLIC'][slot] = dict()
                for item in slic_items:
                    data[array]['SLIC'][slot][item] = ''
                    data[array]['SLIC'][slot]['Port'] = dict()
                for port in range(6):
                    data[array]['SLIC'][slot]['Port'][port] = dict()
                    for item in port_items:
                        data[array]['SLIC'][slot]['Port'][port][item] = '' 
                if n == n_dae:
                    data[array]['Drives'][slot] = dict()
                    for item in drives_items:
                        data[array]['Drives'][slot][item] = '' 
                if n == n_drives:
                    data[array]['DAE'][slot] = dict()
                    for item in dae_items:
                        data[array]['DAE'][slot][item] = '' 

        #populate "Storage System" field
        if 'Status' not in data[array]:
            worksheet.merge_range(row,0,row+n-1,0,array,workbook.add_format({'font_name':'Arial','border':1,'font_size':10,'align':'center','valign':'vcenter','text_wrap':1}))
        else:
            worksheet.merge_range(row,0,row+n-1,0,'',workbook.add_format({'font_name':'Arial','border':1,'font_size':10,'align':'center','valign':'vcenter','text_wrap':1}))
            worksheet.write_rich_string(row,0,array+'\n',status_format,data[array]['Status'],workbook.add_format({'font_name':'Arial','border':1,'font_size':10,'align':'center','valign':'vcenter','text_wrap':1}))

        #populate Slot and Port data
        for i,slot in enumerate(data[array]['SLIC']):
            for j,item in enumerate(slic_items):       
                if slot == n-1:
                    if item == 'Type':
                        worksheet.write_string(row+i,j+1,data[array]['SLIC'][slot][item],cell_format_rb_border)
                    else:
                        worksheet.write_string(row+i,j+1,data[array]['SLIC'][slot][item],cell_format_b_border)
                else:
                    cell_format = cell_format_r_border if item == 'Type' else cell_format2
                    worksheet.write_string(row+i,j+1,data[array]['SLIC'][slot][item],cell_format)
            for j in range(6):
                for k,item in enumerate(port_items):
                    if slot == n-1:
                        if item == 'SFP':
                            worksheet.write_string(row+i,j*3+k+4,data[array]['SLIC'][slot]['Port'][j][item],cell_format_rb_border)
                        else:
                            worksheet.write_string(row+i,j*3+k+4,data[array]['SLIC'][slot]['Port'][j][item],cell_format_b_border)
                    else:  
                        cell_format = cell_format_r_border if item == 'SFP' else cell_format2
                        worksheet.write_string(row+i,j*3+k+4,data[array]['SLIC'][slot]['Port'][j][item],cell_format)
        #populate Drives data
        for i in range(n):
            for j,item in enumerate(drives_items):       
                if i == n-1:
                    if item == 'Number':
                        worksheet.write_string(row+i,j+22,data[array]['Drives'][i][item],cell_format_rb_border)
                    else:
                        worksheet.write_string(row+i,j+22,data[array]['Drives'][i][item],cell_format_b_border)
                else:
                    cell_format = cell_format_r_border if item == 'Number' else cell_format2
                    worksheet.write_string(row+i,j+22,data[array]['Drives'][i][item],cell_format)
        #populate DAE data
        for i in range(n):
            for j,item in enumerate(dae_items):       
                if i == n-1:
                    if item == 'Type':
                        worksheet.write_string(row+i,j+26,data[array]['DAE'][i][item],cell_format_rb_border)
                    else:
                        worksheet.write_string(row+i,j+26,data[array]['DAE'][i][item],cell_format_b_border)
                else:
                    cell_format = cell_format_r_border if item == 'Type' else cell_format2
                    worksheet.write_string(row+i,j+26,data[array]['DAE'][i][item],cell_format)

        #set row number for the next storage system
        row += n

def arg_parser():
    parser = argparse.ArgumentParser(add_help=True,description='Get array configuration information, save to excel and send email.')
    parser.add_argument(dest='Pool',help="Pool is a file with each line an arrayname.")
    parser.add_argument(dest='Email',help="Email address to receive")
    return parser.parse_args()
    
def main():
    args = arg_parser()
    Excel_file = args.Pool.split('.')[0] + '.xlsx'

    print "*"*75
    print "Pool file\t%s" % args.Pool
    print "Email address:\t%s" % args.Email
    print "Output file:\t%s" % Excel_file 

    data = dict()
    f = open(args.Pool)
    for line in f:
        array = line.strip('\n')
        get_info(data, array)
    print "*"*75
    save_to_excel(data, Excel_file, 'array_configuration')
    os.popen('echo ""|mail -s "Array configuration info" -a '+ Excel_file + ' ' + args.Email)
    print "END"

if __name__ == "__main__":
    main()
