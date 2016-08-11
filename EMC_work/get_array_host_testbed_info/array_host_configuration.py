import os
import xlsxwriter

sfp = {
'019-078-041': '10Gb iSCSI',
'019-078-042': '8Gb FC',
'019-078-045': '16Gb FC',
}
data = dict()

def get_info(array):
    print "*"*75
    print "array:\n\t%s" % array
    
    #get ip and check ping of array
    ip_spa, status_spa, ip_spb, status_spb, ip_primary = os.popen("Array=" + array + ";ip_spa=$(swarm $Array --showipinfo | awk 'NR==2{print $5}');ip_spb=$(swarm $Array --showipinfo | awk 'NR==2{print $6}');if [[ $(ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root $ip_spa -i /c4shares/Public/ssh/id_rsa.root crm_mon -1 | grep ECOM | awk '{print $NF}') == 'spa' ]];then ip_primary=$ip_spa;else ip_primary=$ip_spb;fi;for sp in spa spb;do eval ip_addr='$''ip_'$sp;ping -c 1 -W 2 $ip_addr >/dev/null 2>&1 && eval 'status_'$sp='ping_available' || eval 'status_'$sp='ping_failed';done;echo $ip_spa $status_spa $ip_spb $status_spb $ip_primary|xargs").readline()[:-1].split(' ')
    print "ip_spa:\n\t%s\t%s\nip_spb:\n\t%s\t%s\n\tprimary:\t%s" % (ip_spa, status_spa, ip_spb, status_spb, ip_primary)

    #init data dict
    data[array] = dict()
    data[array]['SLIC'] = dict()
    for slot in range(6):
        data[array]['SLIC'][slot] = dict()
        for item in ['Name', 'Inserted', 'Type', 'Port']:
            data[array]['SLIC'][slot][item] = dict()
        #for port in range(4 if slot!=2 and slot!=5 else 6):
        for port in range(6):
            data[array]['SLIC'][slot]['Port'][port] = dict()
            for item in ['Name', 'Link Status', 'Type', 'SFP']:
                data[array]['SLIC'][slot]['Port'][port][item] = '' 
    data[array]['Drives'] = dict()
    for num in range(6):
        data[array]['Drives'][num] = dict()
        for item in ['Type', 'Size', 'Speed', 'Number']:
            data[array]['Drives'][num][item] = ''
    data[array]['DAE'] = dict()
    for num in range(6):
        data[array]['DAE'][num] = dict()
        for item in ['Type']:
            data[array]['DAE'][num][item]  = ''

    print data[array]
  
    #get info of SLIC
    data_slic = [item[:-2].split(",") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root speclcli -getiomodulestatus|grep -E -A3 "IO Module|Onboard IO"|sed -n "/IO Module/{P;n;n;P;n;P};/Onboard IO/{P;n;n;P;n;P}"|sed -r "s/.*(IO Module-[AB][01]).*/\1/;s/.*: (False|True).*/\1/;s/.*(SP[AB] Onboard).*/\1/;s/.*Timestamp.*//;s/.*Unique ID.*: (\w+)\b.*/\1/;s/.*: (Oberon SP).*/\1/;s/$/,/"|xargs -d "\n" -n 3|sed -r "s/[[:space:]]//2;s/ (Oberon)/\1/"').readlines()]

    #update SLIC status of data map
    for slot in range(6):
        data[array]['SLIC'][slot]['Name'] = data_slic[slot][0]
        data[array]['SLIC'][slot]['Inserted'] = data_slic[slot][1]
        data[array]['SLIC'][slot]['Type'] = data_slic[slot][2]

    #get info of Port
    ##get port link status of non-onboard io-modules
    data_iom = [item[:-1].split(" ") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "_iom_"|grep -E "ID|Health details"|sed "s/.*link is down.*/down/;s/.*operating normally.*/normally/;s/^.*= //"|xargs -d "\n" -n2|sort').readlines()]
    data_iom = [data_iom[i:i+4] for i in range(len(data_iom)) if i%4==0]

    ##get sas port link status of onboard io-module
    data_sas = [item[:-1].split(" ") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "_sas"|grep -E "ID|Health details"|sed "s/.*link is down.*/down/;s/.*operating normally.*/normally/;s/^.*= //"|xargs -d "\n" -n2|sort').readlines()]

    ##get iSCSI port onk status of onboard io-module
    data_iscsi = [item[:-1].split(" ") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -A7 "_eth"|grep -E "ID|Health details"|sed "s/.*link is down.*/down/;s/.*operating normally.*/normally/;s/^.*= //"|xargs -d "\n" -n2|sort').readlines()]

    ##get CNA port link status of onboard io-module
    ###Need to check CNA mode firstly, cause CNA mode can be "iSCSI" or "FC"
    cna_status = os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show|grep -E "eth4|eth5" > /dev/null && echo iSCSI || echo FC').readline()[:-1]
    if cna_status == 'iSCSI':
        data_cna = [item[:-1].split(" ") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port show -detail|grep -E -A7 "eth4|eth5"|grep -E "ID|Health details"|sed "s/.*link is down.*/down/;s/.*operating normally.*/normally/;s/^.*= //"|xargs -d "\n" -n2').readlines()]
    elif cna_status == 'FC':
        data_cna = [item[:-1].split(" ") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /net/port/fc show -detail|grep -E -A8 "fc4|fc5"|grep -E "ID|Health details"|sed "s/.*link is down.*/down/;s/.*operating normally.*/normally/;s/^.*= //"|xargs -d "\n" -n2').readlines()]
    data_onboard_io_spa = data_sas[0] + data_sas[1] + data_iscsi[0] + data_iscsi[1] + data_cna[0] +data_cna[1]
    data_onboard_io_spa = [data_onboard_io_spa[i:i+2] for i in range(len(data_onboard_io_spa)) if i%2==0]
    data_onboard_io_spb = data_sas[2] + data_sas[3] + data_iscsi[2] + data_iscsi[3] + data_cna[2] +data_cna[3]
    data_onboard_io_spb = [data_onboard_io_spb[i:i+2] for i in range(len(data_onboard_io_spb)) if i%2==0]

    #update Port status of data map
    if data_iom != [[['']]]:
        for slot in [0, 1, 3, 4]:
            for port in range(4):
                if slot in [0, 1]:
                    data[array]['SLIC'][slot]['Port'][port]['Name'] = data_iom[slot][port][0]
                    data[array]['SLIC'][slot]['Port'][port]['Link Status'] = data_iom[slot][port][1]
                elif slot in [3, 4]:
                    data[array]['SLIC'][slot]['Port'][port]['Name'] = data_iom[slot-1][port-1][0]
                    data[array]['SLIC'][slot]['Port'][port]['Link Status'] = data_iom[slot-1][port-1][1]
    for port in range(6):
        data[array]['SLIC'][2]['Port'][port]['Name'] = data_onboard_io_spa[port][0]
        data[array]['SLIC'][2]['Port'][port]['Link Status'] = data_onboard_io_spa[port][1]
        data[array]['SLIC'][5]['Port'][port]['Name'] = data_onboard_io_spb[port][0]
        data[array]['SLIC'][5]['Port'][port]['Link Status'] = data_onboard_io_spb[port][1]

    ##get SFP info
    data_sfp = dict()
    for ip in [ip_spa, ip_spb]:
        sp = "spa" if [ip_spa, ip_spb].index(ip) == 0 else "spb"
        data_sfp[sp] = [item[:-2].split(",") for item in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip + ' -i /c4shares/Public/ssh/id_rsa.root speclcli -getiomodulestatus verbose|grep -B70 "EMC PN"|grep -E "Module Index|Physical Port Index|EMC PN"|awk \'{print $NF}\'|sed "s/$/,/"|xargs -d "\n" -n 3|sed "s/[[:space:]]*//g"').readlines()]
        for item in data_sfp[sp]:
            if sp == "spb":
                item[0] = int(item[0]) + 3    
            else:
                item[0] = int(item[0])
            item[1] = int(item[1])
            item[2] = sfp[item[2]]
    data_sfp = data_sfp['spa'] + data_sfp['spb']

    ##update SFP info
    if data_sfp != [['']]:
        for item in data_sfp:
            slot = item[0]
            port = item[1]
            data[array]['SLIC'][slot]['Port'][port]['SFP'] = item[2]


    #get info of Drives
    data_drives = [x[:-2].split(",") for x in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + r' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /stor/config/dg show|grep -E "Drive type|Vendor size|Rotational speed|Number of drives"|cut -d "=" -f 2|sed -r "s/^[[:space:]]*//g;s/(.*) [0-9].*/\1/;s/$/,/"|xargs -d "\n" -n 4|sed "s/^[[:space:]]*//g"').readlines()]
    if data_drives != [['']]:
        for i in range(len(data_drives)):
            if i >= 6:
                data[array]['Drives'][i] = dict()
            for j,item in enumerate(['Type', 'Size', 'Speed', 'Number']):
                data[array]['Drives'][i][item] = data_drives[i][j]
    print "data[array]['Drives']:\n\t%s" % data[array]['Drives']

    #get info of DAE
    data_dae = [x[:-1].split(",") for x in os.popen(r'ssh -q -o ConnectTimeout=10 -o StrictHostKeyChecking=no -l root ' + ip_primary + ' -i /c4shares/Public/ssh/id_rsa.root uemcli -sslPolicy accept /env/dae show -detail|grep Model|awk \'{print $3}\'|sed "s/^[[:space:]]*//g"').readlines()]
    if data_dae != [['']]:
        for i in range(len(data_dae)):
            for j,item in enumerate(['Type']):
                data[array]['DAE'][i][item] = data_dae[i][j]
    print "data[array]['DAE']:\n\t%s" % data[array]['DAE']

def save_to_excel(data, file_name, sheet_name):
    workbook = xlsxwriter.Workbook(file_name)
    worksheet = workbook.add_worksheet(sheet_name)

    # 
    worksheet.set_tab_color('red')
    for col in ['A:A', 'B:D', 'E:V']:
        worksheet.set_column(col, 14)
    #for col in ['A:A', 'D:D', 'G:G', 'J:J', 'M:M', 'P:P', 'S:S', 'V:V', 'Z:Z', 'AA:AA']:
    #    worksheet.set_column(col, None, workbook.add_format({'right':1,}))
    worksheet.set_row(0, 30)
    worksheet.set_row(1, 15)
    worksheet.set_row(2, 15)

    # Create a format to use in the merged range.
    cell_format1 = workbook.add_format({
                                        'font_name': 'Arial',
                                        'border': 1,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap': 1,
                                       })
    cell_format2 = workbook.add_format({
                                        'font_name':' Arial',
                                        'font_size': 10,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap': 1,
                                       })
    cell_format_r_border = workbook.add_format({
                                        'font_name':' Arial',
                                        'font_size': 10,
                                        'right': 1,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap': 1,
                                       })
    cell_format_b_border = workbook.add_format({
                                        'font_name':' Arial',
                                        'font_size': 10,
                                        'bottom': 1,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap': 1,
                                       })
    cell_format_rb_border = workbook.add_format({
                                        'font_name':' Arial',
                                        'font_size': 10,
                                        'right': 1,
                                        'bottom': 1,
                                        'align': 'center',
                                        'valign': 'vcenter',
                                        'text_wrap': 1,
                                       })

    worksheet.merge_range('A1:A3','Storage System', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','text_wrap':1,'fg_color':'yellow'}))
    worksheet.merge_range('B1:D1','SLIC', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))
    worksheet.merge_range('E1:V1','Port && SFP', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))
    worksheet.merge_range('W1:Z1','Drives', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCFFCC',}))
    worksheet.write_string('AA1','DAE', workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'FFCC99',}))
 
    slic_items = ['Name', 'Inserted', 'Type']
    port_nums = ['Port0', 'Port1', 'Port2', 'Port3', 'Port4', 'Port5']
    port_items = ['Name', 'Link Status', 'SFP']
    drives_items = ['Type','Size','Speed','Number']
    dae_items = ['Type']       

    for i,item in enumerate(slic_items):
        worksheet.merge_range(1,i+1,2,i+1,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))
    for i,item in enumerate(drives_items):
        worksheet.merge_range(1,i+22,2,i+22,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCFFCC',}))
    for i,item in enumerate(dae_items):
        worksheet.merge_range(1,i+26,2,i+26,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#FFCC99',}))
    for i, item in enumerate(port_nums):       
        worksheet.merge_range(1,i*3+4,1,i*3+6,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))
    for i in range(6):       
        for j, item in enumerate(port_items):       
            worksheet.write_string(2,i*3+4+j,item,workbook.add_format({'font_name':'Arial','bold':1,'border':1,'align':'center','valign':'vcenter','fg_color':'#CCCCFF',}))

    row = 3
    for array in data:
        worksheet.merge_range(row,0,row+5,0,array,workbook.add_format({'font_name':'Arial','border':1,'font_size':10,'align':'center','valign':'vcenter','text_wrap':1}))
        for i,slot in enumerate(data[array]['SLIC']):
            for j,item in enumerate(slic_items):       
                if slot == 5:
                    if item == 'Type':
                        worksheet.write_string(row+i,j+1,data[array]['SLIC'][slot][item],cell_format_rb_border)
                    else:
                        worksheet.write_string(row+i,j+1,data[array]['SLIC'][slot][item],cell_format_b_border)
                else:
                    cell_format = cell_format_r_border if item == 'Type' else cell_format2
                    worksheet.write_string(row+i,j+1,data[array]['SLIC'][slot][item],cell_format)
            for j in range(6):
                for k,item in enumerate(port_items):
                    if slot == 5:
                        if item == 'SFP':
                            worksheet.write_string(row+i,j*3+k+4,data[array]['SLIC'][slot]['Port'][j][item],cell_format_rb_border)
                        else:
                            worksheet.write_string(row+i,j*3+k+4,data[array]['SLIC'][slot]['Port'][j][item],cell_format_b_border)
                    else:  
                        cell_format = cell_format_r_border if item == 'SFP' else cell_format2
                        worksheet.write_string(row+i,j*3+k+4,data[array]['SLIC'][slot]['Port'][j][item],cell_format)

        n_drives = len(data[array]['Drives'])
        n = 6 if n_drives <= 6 else n_drives
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


        for i in range(6):
            for j,item in enumerate(dae_items):       
                if i == n-1:
                    if item == 'Type':
                        worksheet.write_string(row+i,j+26,data[array]['DAE'][i][item],cell_format_rb_border)
                    else:
                        worksheet.write_string(row+i,j+26,data[array]['DAE'][i][item],cell_format_b_border)
                else:
                    cell_format = cell_format_r_border if item == 'Type' else cell_format2
                    worksheet.write_string(row+i,j+26,data[array]['DAE'][i][item],cell_format)

        for i in range(n):
            #if i == 0:
            #    worksheet.set_row(row+i, 15, workbook.add_format({'top':1}))
            #elif i == n-1:
            #    worksheet.set_row(row+i, 15, workbook.add_format({'bottom':1}))
            #else:
            #    worksheet.set_row(row+i, 15)
            worksheet.set_row(row+i, 15)
        row += n
    
    #
    worksheet.set_tab_color('red')
    for col in ['A:A', 'B:D', 'E:V']:
        worksheet.set_column(col, 14)
    #for col in ['A:A', 'D:D', 'G:G', 'J:J', 'M:M', 'P:P', 'S:S', 'V:V', 'Z:Z', 'AA:AA']:
    #    worksheet.set_column(col, None, workbook.add_format({'right':1,}))
    worksheet.set_row(0, 30)
    worksheet.set_row(1, 15)
    worksheet.set_row(2, 15)
    workbook.close()
 
   
    
def main():
   array_list = ['OB-D1090', 'OB-D1091', 'OB-H1073', 'OB-H1072', 'OB-H1071']
   #array_list = ['OB-D1090']
   #array_list = ['OB-D1090', 'OB-D1091', 'OB-S2009', 'OB-S2010']
   #array_list = ['OB-S2009', 'OB-S2010']
   for array in array_list:
      get_info(array)
   print "*"*75
   print data
   save_to_excel(data, 'configuration.xlsx', 'configuration')

if __name__ == "__main__":
    main()
