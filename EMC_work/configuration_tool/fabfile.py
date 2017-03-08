from fabric.api import run
from fabric.context_managers import env
from fabric.context_managers import cd
import json,re
#import matplotlib
#matplotlib.use('Agg')
import xlwt

#env.hosts = ['10.62.34.185']
env.hosts = ['10.62.34.5', '10.62.34.6']
#env.hosts = ['10.62.34.5']
#env.hosts = ['10.62.34.6']
env.user = 'root'
env.password = 'c4proto!'
env.parallel = True
def get_io_module():
    #cmd = r'speclcli -getiomodulestatus | grep -A3 -E "IO Module|Onboard IO" | sed "/--/d" | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*: /\":\"/" | sed -e "s/ __/\":{/" -e "s/^__ /},\"/" | sed -e "s/^/\"/" -e "s/$/\",/" | tr -d "\n" | sed -e "s/{\",/{/g" -e "s/,\"}/}/g" | sed -e "s/^\"},/{/" -e s"/,$/}}/"'
    #cmd = r'speclcli -getiomodulestatus | grep -A3 -E "IO Module|Onboard IO" | grep -v -E "Transaction|Timestamp" | sed "/--/d" | sed -e "s/^[[:space:]]*//" -e "s/[[:space:]]*: /:/" | tr -s "\n" "&" | sed -e "s/ __/@@/g" -e "s/__ /##/g" | sed -e "s/^/A/" -e "s/$/B/"'
    cmd = r"""sp=$(hostname|tr "a-z" "A-Z"|cut -c 3-);if [[ "$sp" == "A" ]];then cmd='sed -n "/IO Module-A0/,/IO Module-B0/p"';else cmd='sed -n "/IO Module-B0/,//p"';fi;speclcli -getiomodulestatus verbose|eval $cmd|grep -E -A3 "IO Module-$sp|SP$sp Onboard"|grep -E -v "Transaction|Timestamp"|sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*: /:/' -e 's/:/":"/' -e 's/__ /@/' -e 's/ __/#/' -e '/--/d'|tr -s '\n' '&'|sed -e 's/&/","/g' -e 's/#",/":{/g' -e 's/","@/"},"/g' -e 's/@/{"/' -e 's/,"$/}}/'"""
    data = run(cmd)
    return data

def get_sfp(n):
    cmd = 'speclcli -getiomodulestatus $(hostname)' + ' ' + n + ' ' +  'verbose|grep "EMC PN"|cut -d ":" -f 2|xargs|tr -s " " ","'
    data = run(cmd)
    return data

class ExcelHelper:
    def __init__(self,log = None):
        self.log = log

    def _def_font(self):
        font = xlwt.Font()
        font.name ='Arial'
        font.bold =True
        font.height = 8*20
        return font

    def _def_cell_style(self):
        style = xlwt.XFStyle()
        style.alignment.wrap = 1
        style.alignment.vert = style.alignment.VERT_CENTER
        style.alignment.horz=style.alignment.HORZ_CENTER
        style.borders.left=style.borders.MEDIUM
        style.borders.top=style.borders.MEDIUM
        style.borders.right=style.borders.MEDIUM
        style.borders.bottom=style.borders.MEDIUM
        return style

    def _def_cell_pattern(self):
        pat = xlwt.Pattern()
        pat.pattern=xlwt.Pattern.SOLID_PATTERN
        pat.pattern_fore_colour = 42
        return pat

    def save_twod_array_to_excel(self,text,file_name,sheet_name,col_num_and_width=None):
        """
        Saves the data in two dimension array into excel file
        :param text: two dimension array containing the data
        :param file_name: path to save the excel file
        :param sheet_name: name of the sheet in excel file
        :param col_num_and_width: list of column number with it desiered width
        :return:
        """
        style = self._def_cell_style()
        style.font = self._def_font()

        workbook = xlwt.Workbook(encoding="utf8")
        worksheet = workbook.add_sheet(sheet_name)
        for x in range(1,len(text)):
            for y in range(0,len(text[0])):
                #print str(text[x][y])
                worksheet.write(x,y,(str(text[x][y]).decode("cp1251").encode("utf8")),style)
        style.pattern=self._def_cell_pattern()
        for y in range(0,len(text[0])):
            worksheet.write(0,y,(str(text[0][y])),style)
        for x in range(1,len(text)):
            worksheet.row(x).height_mismatch = True
            worksheet.row(x).height = 60*20
        if col_num_and_width is not None:
            for x in col_num_and_width:
                worksheet.col(x[0]).width = x[1]
        workbook.save(file_name)

def main():
    str_io_module = get_io_module()
    map = json.loads(str_io_module)
    pattern = re.compile(r'\d')
    for module in map:
        if map[module]['Inserted']=='True':
            num = pattern.search(module).group()
            a = get_sfp(num)
            map[module]['EMC PN'] = get_sfp(num)
    
    data = list()
    data.append([])
    data[0].extend(['', 'Inserted', 'Unique ID', 'EMC PN'])
    i = 1
    for module in sorted(map.keys()):
        data.append([])
        data[i].append(module)
        for key in data[0][1:]:
            if key not in map[module].keys():
                data[i].append('')
            else:
                data[i].append(map[module][key])
        i += 1
    print data
    excel = ExcelHelper()
    excel.save_twod_array_to_excel(data, "test.xls", "IO Module")
    #title = 'Configure Info'
    #draw_table_first_row_colored(data, 1.1*len(data[0]), 0.5*len(data), 0.98, True, title, 'left', 10)

    #data = dict()
    #data[env.host] = map
    #print "data is : \n%s "  %  data
    
    
    
    


