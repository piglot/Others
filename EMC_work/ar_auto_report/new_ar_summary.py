import time,datetime,logging,os,json,argparse
from RadarCrawler import *
import matplotlib.pyplot as plt
from UtilTime import *
from UtilArrayMap import *
from UtilGraph import *
from UtilEmail import *

__author__ = "Ming.Yao@emc.com"

__filename__ = os.path.basename(__file__)
fpath = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.getcwd()+os.sep + "new_ar_summary.log.txt"

timer = TimeHelper(logger)
CUR_TIME = int(timer.get_mtime())
CUR_WEEK_START_TIME = timer.get_week_start(CUR_TIME)
PRE_WEEK_START_DATE =timer.mtime_to_radar_date(CUR_WEEK_START_TIME -7*24*60*60)
PRE_WEEK_END_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME - 60*60)
CUR_WEEK_START_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME)
CUR_WEEK_END_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME + 7*24*60*60 -60*60)
CUR_DATE = timer.mtime_to_radar_date(CUR_TIME)


BASIC_URL = 'http://radar.usd.lab.emc.com/Classes/Misc/sp.asp?t=ArrivalARS&ex=1&p=%s&tab=B%s&' \
            'p2=Bug|&p1=P00|P01|P02|&p13=%s&p10=%s|&wkend=%s&&dt=%s'
crawler = RadarCrawler()

def arg_parser():
    parser = argparse.ArgumentParser(prog=__filename__,usage='%(prog)s [options]')
    parser.add_argument('-config','--configuration',help="provide configuration file",nargs=1)
    parser.add_argument('-t','--test',help="turn on test mode",action="store_true")
    return parser.parse_args()

def init_param(args):
    with open(fpath+'\\'+args.configuration[0]) as cfg:
        data = json.load(cfg)
        parammap = dict(data)
        cfg.close()
        if(args.test):
            parammap['to'] = __author__
            parammap['cc'] = __author__
        return parammap

def debug(message):
    """
    Writes the message into log file
    :param logg_file: path to the log file
    :param message: message to be written
    :return:
    """
    logging.basicConfig(filename=LOG_FILE,level=logging.DEBUG,)
    t = time.localtime()
    print message
    logging.debug('%s - %s' % (time.asctime(t),message))

def get_statistic_from_name(release,name_list,CWEEK):
    data={'In':0,'Out':0,'Change':0,'Fixed':0}
    debug("name_list: "+str(name_list))
    for name in name_list:
        release=release.replace(' ', '%20')
        name_format=name.replace(' ', '%20')
        name_format=name.replace('%', '')
        debug("name_replace_blank: "+str(name_format))

        if CWEEK == 0:
            WEEK_END_DATE=PRE_WEEK_END_DATE
        else:
            WEEK_END_DATE=CUR_WEEK_END_DATE
        debug("WEEK_END_DATE: "+str(WEEK_END_DATE))
        url_in = BASIC_URL % (release, "I", "Movein|New|Reopen|Other|", name_format, WEEK_END_DATE, CUR_TIME)
        url_out = BASIC_URL % (release, "O", "Duplicate|Fixed|DeferDismissal|ProgramChangeDeferral|NondeferDismissal|Other|",
                        name_format, WEEK_END_DATE, CUR_TIME)
        #debug("url_in : "+str(url_in))
        #debug("url_out : "+str(url_out))

        arin = crawler.get_url_response(url_in)
        arin.read()
        arrival_movein, arrival_new, arrival_other, arrival_reopen, totalin,text_in = crawler.count_arrivals(arin)
        logger.debug("arrival_movein: "+str(arrival_movein))
        arout = crawler.get_url_response(url_out)
        closure_dup, closure_fix, closure_deferdis,closure_prog, closure_nodeferdis, closure_other, totalout, text_out = \
        crawler.count_closures(arout)

        print "name %s - move in %s new %s other %s reopen %s totalin %s" % (name, arrival_movein, arrival_new, arrival_reopen, arrival_other, totalin)
        print "name %s - dup %s fixed %s deferDis %s Program change def %s Non defer Dis %s other %s totalout %s" % (name, closure_dup, closure_fix, closure_deferdis,
                                                                                   closure_prog, closure_nodeferdis, closure_other, totalout)
        data['In']+=totalin
        data['Out']+=totalout
        data['Change']=totalin-totalout
        data['Fixed']+=closure_fix
    return data

def draw(data,plt_width,plt_height,save_to_file,title=None,title_loc='left',font_size=10):
        lightgrn = (192/255.0, 192/255.0, 192/255.0)

        fig = plt.figure(figsize=(plt_width,plt_height))
        plt.axis('off')
        #ax = fig.add_subplot(111, frameon=True, xticks=[], yticks=[])
        #ax.spines["right"].set_visible(False)
        #ax.spines["top"].set_visible(False)
        #ax.spines["left"].set_visible(False)
        #ax.spines["bottom"].set_visible(False)

        the_table=plt.table(cellText=data,loc='center', cellLoc='center')

        plt.subplots_adjust(left=0.09, bottom=0.10,right=0.99,top=0.90)

        cell_dict=the_table.get_celld()

        #to set one column black
        for i in range(0,len(data[0])):
            cell_dict[(0,i)].set_color(lightgrn)
            cell_dict[(0,i)].set_edgecolor('Black')
        #to set one row black
        #for i in range(1,len(data)):
        #    cell_dict[(i,0)].set_color(lightgrn)
         #   cell_dict[(i,0)].set_edgecolor('Black')

        table_props=the_table.properties()
        table_cells=sorted(table_props['child_artists'])
        celw = 1.0/(len(data[0]))
        celh = 0.5/(len(data))
        for cell in table_cells:
            cell.set_width(celw)
            cell.set_height(celh)
            cell.set_fontsize(font_size)
            cell.set_text_props(multialignment='left')
        #if if_tight:

        #    for i in range(0,bug_category):
        #        the_table.auto_set_column_width(i)
        the_table.set_fontsize(font_size)
        if title is not None:
            plt.title(title,loc=title_loc)
        #the_table.auto_set_column_width

        plt.savefig(save_to_file, bbox_inches='tight')
        #
        plt.show()
def ar_summary_by_week(map_ca,release,CWEEK):
    ca_io = dict()
    for ca in sorted(map_ca.keys()):
        # Get the In/Out dat for each CA.
        ca_io[ca] = get_statistic_from_name(release, map_ca[ca],CWEEK)
    if CWEEK==0:
        START_DATE=PRE_WEEK_START_DATE
        END_DATA=PRE_WEEK_END_DATE
    else:
        START_DATE=CUR_WEEK_START_DATE
        END_DATA=CUR_DATE
    data=[[str(START_DATE)+" ~ "+str(END_DATA)],['In'],['Out'],['Change'],['Fixed']]
    for ca in sorted(ca_io.keys()):
        data[0].append(ca)
        data[1].append(ca_io[ca]['In'])
        data[2].append(ca_io[ca]['Out'])
        data[3].append(ca_io[ca]['Change'])
        data[4].append(ca_io[ca]['Fixed'])
    for i in range(1,len(data)):
        total=0
        for j in range(1,len(data[i])):
            total += int(data[i][j])
        data[i].append(total)
    data[0].append('Total')
    logger.debug("data final : "+str(data))
    return data

def ar_in_out_report(parammap,release,title, save_to_file):

    grapher = GraphHelper()
    #white = (255/255.0, 255/255.0, 255/255.0)
    #lightborwn = (250/255.0,250/255.0,245/255.0)
    lightgrn = (192/255.0, 192/255.0, 192/255.0)

    ayer = ArrayMapHelper()
    map_ca=ayer.negative_map_filter(parammap['ca_managers'], "Platform Integration")

    #get last week data
    CWEEK=0
    data_pre=ar_summary_by_week(map_ca,release,CWEEK)
    #get current week data
    CWEEK=1
    data_cur=ar_summary_by_week(map_ca,release,CWEEK)
    #merge data list
    data=data_pre+data_cur
    debug("data: "+str(data))

    #draw first row Black
    plt, table= grapher.draw_table_first_row_colored(data, 2.0*len(data[0]),
                                                  0.4*len(data), 0.98, False, title, 'left', 14)
    #draw row 4 Black
    cell_dict = table.get_celld()
    for i in range(0,len(data[0])):
            cell_dict[(5,i)].set_color(lightgrn)
            cell_dict[(5,i)].set_edgecolor('Black')

    #plt.show()
    plt.savefig(save_to_file, bbox_inches='tight')

def sent_report_email(parammap,files_to_send,additional_body):
    """
    Sends out report via email
    :param bug_releases: release of the bugs
    :param additional_body: additional to append at the end of the email
    :return:
    """
    mailer = EmailHelper()
    att = files_to_send['attachment']
    subj = parammap['report name'] + ' Bug Report'
    ifHtmlNody = True
    embed_images = files_to_send['image']
    body='<h3>This Report Is Generated Automatically By Product Integration Engineering Team.</h3><hr>'
    if len(additional_body) != 0:
        body += '<p><a href="#blockings">Check The Details Of Blocking ARs<a/></p>'

    style = '<style>table,th,td{border: 1px solid black;border-collapse: collapse;font-family:"Arial";'+\
            'font-size:8.0pt;color:black} table{width:900px;}caption{text-align: left;font-size:14.0pt;}'+\
            'th{text-align:center;font:bold;background-color:#ccff99} td{text-align:center;font:bold;}' +\
            'span{margin-bottom:20px;display:block;font-family:"sans-serif";font-size:14.0pt;}</style>'
    #print parammap['to']
    #print parammap['cc']
    mailer.send_email(parammap['to'],subj,style+body,ifHtmlNody,embed_images,additional_body,parammap['cc'],att)

def main():

    parammap = init_param(arg_parser())
    #fprefix = fpath+'\\'+parammap['report name'].replace(' ','')
    fprefix = os.getcwd()+os.sep
    files_to_send = {}
    files_to_send['attachment'] = []
    files_to_send["image"] = []
    additional_body = ""

    #releases=["Thunderbird SP1","Falcon"]
    for rel in sorted(parammap['in out report releases']):
        save_to_file=fprefix+rel.replace(' ','')+'-ar-in-out.png'
        title="AR In/Out/Change/Fix by CA"+"("+str(rel)+")"
        ar_in_out_report(parammap,rel,title,save_to_file)
        files_to_send["image"].append(save_to_file)

    #send report email
    sent_report_email(parammap,files_to_send,additional_body)

    '''
    parammap = init_param(arg_parser())
    save_to_file='-ar-in-out.png'
    ar_in_out_report(parammap,"Thunderbird SP1","test",save_to_file)
    '''



    '''
    #test for draw begin
    data=[['2016-06-13 ~ 2016-06-17', u'Platform Core', u'Platform Services', u'SNAP', u'Security', u'Virtual Platforms', 'Total'], ['In', 15, 15, 15, 1, 1, 47], ['Out', 10, 17, 9, 1, 1, 38], ['Change', 5, -2, 6, 0,
 0, 9], ['Fixed', 1, 1, 1, 1, 0, 4]]

    save_to_file=os.getcwd()+os.sep+"new_ar_summary.png"
    draw(data,0.4*len(data),0.4*len(data),save_to_file,title=None,title_loc='left',font_size=10)
    #test for draw end
    '''



if __name__ == '__main__':
    main()