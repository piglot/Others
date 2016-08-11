#!/usr/bin/python

# Copyright 2015 by Platform Product Integration Team.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, not be used in advertising or publicity
# pertaining to distribution

import os,datetime,argparse,json
from UtilLogging import *
from UtilDatabase import *
from PlatformUnityDailyAR import *
from UtilGraph import *
from UtilArrayMap import *
from UtilExcel import *
from UtilEmail import *
from ARAuditTrail import *
from pandas import read_csv
from SharePointUploader import *
from RadarCrawler import *
import base64

__author__ = "Ming.Yao@emc.com"
ARGS = ['c3VueTE4', 'U3l5Mzg0JSUl']


reload(sys)
sys.setdefaultencoding('utf8')

__filename__ = os.path.basename(__file__)
fpath = os.path.dirname(os.path.realpath(__file__))
logger = LogHelper(fpath+'\\' + 'ar_repport_daily_log.txt')

timer = TimeHelper(logger)
CUR_TIME = int(timer.get_mtime())
CUR_WEEK_START_TIME = timer.get_week_start(CUR_TIME)
#PRE_WEEK_START_DATE =timer.mtime_to_radar_date(CUR_WEEK_START_TIME -7*24*60*60)
#PRE_WEEK_END_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME - 60*60)
CUR_WEEK_START_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME)
#CUR_WEEK_END_DATE = timer.mtime_to_radar_date(CUR_WEEK_START_TIME + 7*24*60*60 -60*60)
CUR_DATE = timer.mtime_to_radar_date(CUR_TIME)


COLOR_SETS = [
    [(155/255.0, 0/255.0, 0/255.0),(255/255.0,0/255.0, 0/255.0),\
     (255/255.0, 102/255.0, 102/255.0),(255/255.0, 204/255.0, 204/255.0),\
     (220/255.0, 100/255.0, 60/255.0),(255/255.0, 128/255.0, 0/255.0), \
     (255/255.0, 178/255.0, 102/255.0),(255/255.0, 255/255.0, 204/255.0)],
    [(220/255.0, 100/255.0, 60/255.0),(255/255.0, 128/255.0, 0/255.0), \
     (255/255.0, 178/255.0, 102/255.0),(255/255.0, 255/255.0, 229/255.0), \
     (102/255.0, 204/255.0, 0/255.0),(153/255.0, 255/255.0, 51/255.0),\
     (204/255.0,255/255.0, 153/255.0),(229/255.0, 255/255.0, 204/255.0)],
    [(102/255.0, 204/255.0, 0/255.0),(153/255.0, 255/255.0, 51/255.0),\
     (204/255.0,255/255.0, 153/255.0),(229/255.0, 255/255.0, 229/255.0),\
     (0/255.0, 128/255.0, 255/255.0),(102/255.0, 178/255.0, 255/255.0), \
     (204/255.0, 229/255.0, 255/255.0),(204/255.0, 255/255.0, 255/255.0)]
]


TARGET_DATES = ["6/14/2015","6/21/2015","6/28/2015","7/5/2015","7/12/2015","7/19/2015","7/26/2015","8/2/2015","8/9/2015",
                "8/16/2015","8/23/2015","8/30/2015","9/6/2015","9/13/2015","9/20/2015","9/27/2015","10/4/2015","10/11/2015",
                "10/18/2015","10/25/2015","11/1/2015","11/8/2015"]
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


def get_ar_obj_list(rawars):
    logger.debug("getting AR obj list ...")
    res = []
    for ar in rawars:
        res.append(generate_unity_ar_obj(ar))
    return res


def save_AR_list_to_excel(ar_list,filename):
    """
    Saves the content in the list of ARs to excel file
    :param ar_list: list of ARs
    :return:
    """
    timer = TimeHelper()
    text = []
    text.append([])
    text[0] = ['Entry-Id','Summary','Assigned-to','Owning\nCA','Direct\nManager','Reported\nby','Create-date', \
               'Status','Status\nDetails','Blocking','Prio\nrity','ETA','Report\nGroup',\
               'Report\nFunction','Major\nArea','Product\nArea','Product\nFamily','Product\nRel.','Releases Build-in',
               'Classification','Num of \nDuplicates','Version\nFound','Age/Days']
    for obj in ar_list:
        text.append([])
        text[len(text)-1].append(obj.entry_id)
        text[len(text)-1].append(obj.summary)
        text[len(text)-1].append(obj.assigned_to)
        text[len(text)-1].append(obj.owning_ca)
        text[len(text)-1].append(obj.direct_manager)
        text[len(text)-1].append(obj.reported_by)
        text[len(text)-1].append(obj.create_date_local)
        text[len(text)-1].append(obj.status)
        text[len(text)-1].append(obj.status_details)
        text[len(text)-1].append(obj.blocking)
        text[len(text)-1].append(obj.priority)
        #text[len(text)-1].append(obj.type)
        text[len(text)-1].append(obj.estimated_checkin_date_local)
        text[len(text)-1].append(obj.reported_by_group)
        text[len(text)-1].append(obj.reported_by_function)
        text[len(text)-1].append(obj.major_area)
        text[len(text)-1].append(obj.product_area)
        text[len(text)-1].append(obj.product_family)
        text[len(text)-1].append(obj.product_release)
        text[len(text)-1].append(obj.release_buildin)
        text[len(text)-1].append(obj.classification)
        text[len(text)-1].append(obj.num_dup)
        text[len(text)-1].append(obj.version_found)
        text[len(text)-1].append(int((timer.get_mtime()-obj.create_date)/(24*60*60)))
    exler = ExcelHelper(logger)
    exler.save_twod_array_to_excel(text,filename,'ARs',[[1,200*20],[8,70*20],[9,70*20]])
    exler.add_filter(filename,'ARs')


def count_bug_total(arObjList, twodkeyset):
    """
    Counts the number of ARs for each program, and for different priority levels
    :param arObjList: AR obj list
    :param twodkeyset: second dimension key set
    :return: map containing the number of ARs for each program, and for different priority levels
    """
    res = {}
    arrayer = ArrayMapHelper(logger)
    i = 0
    j=0
    k=0
    for obj in arObjList:

        if (obj.product_family == "Unified Systems") or (obj.product_family == "Bearcat"):
            arrayer.update_twod_map_values(res,obj.product_release,obj.priority,twodkeyset, iftotal=True)
            if obj.blocking is 'Y':
                arrayer.update_twod_map_values(res,obj.product_release,'Blockers',twodkeyset, iftotal=False)
        if obj.product_family == 'USD Test':
            arrayer.update_twod_map_values(res,obj.product_release,'Test Total',twodkeyset, iftotal=False)
    return res


def bug_total_report(arObjList,title,save_to_file):
    """
    Generates unity bug summary report
    :param arObjList: AR obj list
    :param save_to_file: path to save the report chart
    :return: map containing the total bug count data
    """
    grapher = GraphHelper()
    bug_count_map = count_bug_total(arObjList,['P00','P01','P02','Test Total','Blockers','Product Total'])

    #map product
    map_product = {}
    arrayer = ArrayMapHelper(logger)
    for key in sorted(bug_count_map.keys()):
        map_product[key] = arrayer.positive_map_filter(bug_count_map[key],['P00','P01','P02','Product Total'])
    map_product = arrayer.twod_map_to_report_table(map_product,'Program',True)

    #map product+test
    tester = arrayer.get_sublist_from_twodmap(bug_count_map,'Test Total', True, True, 'Test Total')
    map_product_test = arrayer.insert_col(map_product,tester,len(map_product[0]))
    logger.debug("tester : "+str(tester))

    #add product+test+block
    blocker = arrayer.get_sublist_from_twodmap(bug_count_map, 'Blockers', True, True, 'Blockers')
    map_product_test_block = arrayer.insert_col(map_product_test,blocker,len(map_product_test[0]))
    arrayer.replace_twod_array_zero(map_product_test_block,1,len(map_product_test_block)-2,1,len(map_product_test_block[0])-1,' ')

    #draw table
    plt, table= grapher.draw_table_first_last_row_colored(map_product_test_block, 2.0*len(map_product_test_block[0]),
                                                  0.4*len(map_product_test_block), 0.98, False, title, 'left', 10)
    cell_dict = table.get_celld()
    for i in range(1,len(map_product_test_block)):
        cell_dict[(i,len(map_product_test_block[0])-2)].get_text().set_color((153/255.0, 0/255.0, 0/255.0))
    for i in range(1,len(map_product_test_block)-1):
        for j in range(len(map_product_test_block[0])-2,len(map_product_test_block[0])):
            cell_dict[(i,j)].set_color((250/255.0,250/255.0,245/255.0))
            cell_dict[(i,j)].set_edgecolor('Black')

    #save figure
    plt.savefig(save_to_file, bbox_inches='tight')

    return bug_count_map


def count_bug_age(ar_obj_list):
    """
    Counts the age of ARs for each program and for different priority levels
    :param ar_obj_list:  list of AR object
    :return: map containing ages of ARs in each program with regarding to different priority levels
    """
    n=0
    timer = TimeHelper()
    res = {}
    ayer = ArrayMapHelper(logger)
    current_time = timer.get_day_start(timer.get_mtime())
    one_week = 7*24*60*60
    oned_key_set =['0-1 week','1-2 week','2-3 week','3-4 week','4-5 week','5-6 week','>=6 week']
    twod_key_set = ['P00','P01','P02']
    for obj in ar_obj_list:
        if (obj.product_family != 'Unified Systems') and (obj.product_family != 'Bearcat'):
            n=n+1
            print n
            logger.debug("[count_bug_age]"+obj.product_release+"---"+obj.product_family+"---"+str(n))
            continue
        tlen = current_time - obj.create_date
        if tlen < one_week:
            ayer.update_twod_map_values(res,'0-1 week',obj.priority,twod_key_set,iftotal=True)
        elif tlen < 2*one_week:
            ayer.update_twod_map_values(res,'1-2 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 3*one_week:
            ayer.update_twod_map_values(res,'2-3 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 4*one_week:
            ayer.update_twod_map_values(res,'3-4 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 5*one_week:
            ayer.update_twod_map_values(res,'4-5 week',obj.priority,twod_key_set, iftotal=True)
        elif tlen < 6*one_week:
            ayer.update_twod_map_values(res,'5-6 week',obj.priority,twod_key_set, iftotal=True)
        else:
            ayer.update_twod_map_values(res,'>=6 week',obj.priority,twod_key_set, iftotal=True)
    twod_key_set.append('Product Total')
    for key in oned_key_set:
        if key not in res.keys():
            res[key]={}
            for n in twod_key_set:
                res[key][n]=0
    return res


def bug_age_report(arObjList, ttitle,color_set,save_to_file):
    """
    Generates bug age report
    :param arObjList: list of AR objects
    :param ttitle: title of the report chart
    :param color_set: color set used to draw the rows and cols
    :param save_to_file: path to save the chart to
    :return:
    """
    timer = TimeHelper()
    grapher = GraphHelper()
    strer = StringHelper(logger)
    ayer = ArrayMapHelper(logger)
    bug_age_map = count_bug_age(arObjList)

    logger.debug("[bug_age_report]---bug_age_map is:")
    logger.debug(bug_age_map)

    bug_age_table = ayer.twod_map_to_report_table(bug_age_map,'Age',True)
    rownames = timer.get_weekly_interval(len(bug_age_table) -2)
    rownames.append(rownames[len(rownames)-1])
    rownames.append(" ")
    bug_age_table = ayer.insert_col(bug_age_table,rownames,0)
    ratecols = []
    week_duration =[1,2,3,6]
    total_num = bug_age_table[len(bug_age_table)-1][len(bug_age_table[0])-1]
    col_nums = len(bug_age_table[0])
    for i in range(0,len(week_duration)):
        ratecols.append([])
        ratecols[i].append(">"+str(week_duration[i])+" week")
        num = total_num
        for j in range(0,week_duration[i]):
            num = num - bug_age_table[j+1][col_nums-1]
        for m in range(0,len(bug_age_table)-2):
            ratecols[i].append(" ")
        ratecols[i].append(strer.get_rate_string(num,total_num))
        bug_age_table = ayer.insert_col(bug_age_table,ratecols[i],len(bug_age_table[0]))
    ayer.replace_twod_array_zero(bug_age_table, 1,len(bug_age_table)-2,2,len(bug_age_table[0])-1-len(week_duration),' ')
    plt, table = grapher.draw_age_table(bug_age_table,6.1,2.5,0.9,True,col_nums,week_duration,color_set,ttitle,'left',10)
    plt.savefig(save_to_file, bbox_inches='tight')


def count_direct_manager_bug(ar_obj_list):
    """
    Counts the number of ARs for each direct manager, regarding different product releases
    :param ar_obj_list: list of AR objects
    :return: map containing number of ARs for each direct manager with regarding to different product releases
    """
    ayer = ArrayMapHelper()
    res= {}
    releases = get_obj_releases(ar_obj_list)
    for obj in ar_obj_list:
        if (obj.product_family == "Unified Systems") or (obj.product_family == "Bearcat"):
            ayer.update_twod_map_values(res,obj.direct_manager,obj.product_release,releases, iftotal=True)
    return res


def unity_direct_manager_report(ar_obj_list,title, save_to_file):
    """
    Generates bug report for each direct manager of different product release
    :param ar_obj_list: list of AR objects
    :param save_to_file: path to save the chart to
    :return:
    """
    ayer = ArrayMapHelper()
    strer = StringHelper()
    grapher = GraphHelper()
    direct_manager_bug_map = count_direct_manager_bug(ar_obj_list)
    logger.debug("direct_manager_bug_map : " + str(direct_manager_bug_map))
    map_without_total = {}
    for key in sorted(direct_manager_bug_map.keys()):
        map_without_total[key] = ayer.negative_map_filter(direct_manager_bug_map[key],['Product Total'])
    direct_manager_bug_table = ayer.twod_map_to_report_table(map_without_total,'Direct Manager',True)
    total = []
    for key in sorted(direct_manager_bug_map.keys()):
        total.append(direct_manager_bug_map[key]['Product Total'])
    total.append(ayer.sum_array(total))
    total.insert(0,'Total')
    report_with_total = ayer.insert_col(direct_manager_bug_table,total,len(direct_manager_bug_table[0]))

    for j in range(1,len(report_with_total[0])):
        if len(report_with_total[0][j]) > 6:
            report_with_total[0][j] = strer.split_str_by_length(report_with_total[0][j],j+4)
    ayer.replace_twod_array_zero(report_with_total,1,len(report_with_total)-2,1,
                            len(report_with_total[0])-2,' ')
    #c_width = 0.8*len(report_with_total[0])
    plt, table = grapher.draw_table_first_last_row_colored(report_with_total, 0.9*len(report_with_total[0]),
                                                   0.5*len(report_with_total),0.9, True,
                                                   None, 'left', 10)
    celh = 1.0/(len(report_with_total))*1.8
    cell_dict = table.get_celld()
    for j in range(0,len(report_with_total[0])):
        cell_dict[(0,j)].set_height(celh)
    plt.text(-0.0005*len(report_with_total[0]),1 + 0.7/len(report_with_total),
             title,fontsize=14, ha='left')
    plt.savefig(save_to_file, bbox_inches='tight')


def count_product_area_bug(ar_obj_list):
    """
    Counts the number of ARs for each direct manager, regarding different product releases
    :param ar_obj_list: list of AR objects
    :return: map containing number of ARs for each direct manager with regarding to different product releases
    """
    ayer = ArrayMapHelper()
    res= {}
    releases = get_obj_releases(ar_obj_list)
    for obj in ar_obj_list:
        ayer.update_twod_map_values(res,obj.product_area,obj.product_release,releases, iftotal=True)
    return res


def unity_product_area_report(ar_obj_list,title, save_to_file):
    """
    Generates bug report for each direct manager of different product release
    :param ar_obj_list: list of AR objects
    :param save_to_file: path to save the chart to
    :return:
    """
    ayer = ArrayMapHelper()
    strer = StringHelper()
    grapher = GraphHelper()
    bug_map = count_product_area_bug(ar_obj_list)
    map_without_total = {}
    for key in sorted(bug_map.keys()):
        map_without_total[key] = ayer.negative_map_filter(bug_map[key],['Total'])
    product_area_bug_table = ayer.twod_map_to_report_table(map_without_total,'Product Area',True)
    total = []
    for key in sorted(bug_map.keys()):
        total.append(bug_map[key]['Total'])
    total.append(ayer.sum_array(total))
    total.insert(0,'Total')
    report_with_total = ayer.insert_col(product_area_bug_table,total,len(product_area_bug_table[0]))

    for j in range(1,len(report_with_total[0])):
        if len(report_with_total[0][j]) > 6:
            report_with_total[0][j] = strer.split_str_by_length(report_with_total[0][j],j+4)
    ayer.replace_twod_array_zero(report_with_total,1,len(report_with_total)-2,1,
                            len(report_with_total[0])-2,' ')
    #c_width = 0.8*len(report_with_total[0])
    plt, table = grapher.draw_table_first_last_row_colored(report_with_total, 0.9*len(report_with_total[0]),
                                                   0.5*len(report_with_total),0.9, True,
                                                   None, 'left', 10)
    celh = 1.0/(len(report_with_total))*1.8
    cell_dict = table.get_celld()
    for j in range(0,len(report_with_total[0])):
        cell_dict[(0,j)].set_height(celh)
    plt.text(-0.0005*len(report_with_total[0]),1 + 0.7/len(report_with_total),
             title,fontsize=14, ha='left')
    plt.savefig(save_to_file, bbox_inches='tight')


def count_major_area_bug(ar_obj_list):
    """
    Counts the number of ARs for each direct manager, regarding different product releases
    :param ar_obj_list: list of AR objects
    :return: map containing number of ARs for each direct manager with regarding to different product releases
    """
    ayer = ArrayMapHelper()
    res= {}
    releases = get_obj_releases(ar_obj_list)
    for obj in ar_obj_list:
        ayer.update_twod_map_values(res,obj.major_area,obj.product_release,releases, iftotal=True)
    return res


def unity_major_area_report(ar_obj_list,title, save_to_file):
    """
    Generates bug report for each direct manager of different product release
    :param ar_obj_list: list of AR objects
    :param save_to_file: path to save the chart to
    :return:
    """
    ayer = ArrayMapHelper()
    strer = StringHelper()
    grapher = GraphHelper()
    bug_map = count_major_area_bug(ar_obj_list)
    map_without_total = {}
    for key in sorted(bug_map.keys()):
        map_without_total[key] = ayer.negative_map_filter(bug_map[key],['Total'])
    major_area_bug_table = ayer.twod_map_to_report_table(map_without_total,'Major Area',True)
    total = []
    for key in sorted(bug_map.keys()):
        total.append(bug_map[key]['Total'])
    total.append(ayer.sum_array(total))
    total.insert(0,'Total')
    report_with_total = ayer.insert_col(major_area_bug_table,total,len(major_area_bug_table[0]))

    for j in range(1,len(report_with_total[0])):
        if len(report_with_total[0][j]) > 6:
            report_with_total[0][j] = strer.split_str_by_length(report_with_total[0][j],j+4)
    ayer.replace_twod_array_zero(report_with_total,1,len(report_with_total)-2,1,
                            len(report_with_total[0])-2,' ')
    #c_width = 0.8*len(report_with_total[0])
    plt, table = grapher.draw_table_first_last_row_colored(report_with_total, 0.9*len(report_with_total[0]),
                                                   0.5*len(report_with_total),0.9, True,
                                                   None, 'left', 10)
    celh = 1.0/(len(report_with_total))*1.8
    cell_dict = table.get_celld()
    for j in range(0,len(report_with_total[0])):
        cell_dict[(0,j)].set_height(celh)
    plt.text(-0.0005*len(report_with_total[0]),1 + 0.7/len(report_with_total),
             title,fontsize=14, ha='left')
    plt.savefig(save_to_file, bbox_inches='tight')

def get_statistic_from_name(release,name):
    crawler = RadarCrawler()
    BASIC_URL = 'http://radar.usd.lab.emc.com/Classes/Misc/sp.asp?t=ArrivalARS&ex=1&p=%s&tab=B%s&' \
            'p2=Bug|&p1=P00|P01|P02|&p13=%s&p10=%s|&wkend=%s&&dt=%s'

    release=release.replace(' ', '%20')
    name=name.replace(' ', '%20')

    url_in = BASIC_URL % (release, "I", "Movein|New|Reopen|Other|", name, CUR_DATE, CUR_TIME)
    url_out = BASIC_URL % (release, "O", "Duplicate|Fixed|DeferDismissal|ProgramChangeDeferral|NondeferDismissal|Other|",
                        name, CUR_DATE, CUR_TIME)
    #debug("url_in : "+str(url_in))
    # debug("url_out : "+str(url_out))

    arin = crawler.get_url_response(url_in)
    arrival_movein, arrival_new, arrival_other, arrival_reopen, totalin,text_in = crawler.count_arrivals(arin)
    arout = crawler.get_url_response(url_out)
    closure_dup, closure_fix, closure_deferdis,closure_prog, closure_nodeferdis, closure_other, totalout, text_out = \
    crawler.count_closures(arout)

    print "name %s - move in %s new %s other %s reopen %s totalin %s" % (name, arrival_movein, arrival_new, arrival_reopen, arrival_other, totalin)
    print "name %s - dup %s fixed %s deferDis %s Program change def %s Non defer Dis %s other %s totalout %s" % (name, closure_dup, closure_fix, closure_deferdis,
                                                                                   closure_prog, closure_nodeferdis, closure_other, totalout)
    data=dict()
    data['In']=totalin
    data['Out']=totalout
    data['Change']=totalin-totalout
    data['Fixed']=closure_fix
    return data

def ar_in_out_report(parammap,release,title, save_to_file):
    grapher = GraphHelper()
    white = (255/255.0, 255/255.0, 255/255.0)
    ca_io = dict()

    for ca in sorted(parammap['ca_managers'].keys()):
        # Get the In/Out dat for each CA.
        ca_io[ca] = get_statistic_from_name(release, parammap['ca_managers'][ca])
    data=[[str(CUR_WEEK_START_DATE)+" ~ "+str(CUR_DATE)],['In'],['Out'],['Change'],['Fixed']]
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
    #data=[['2016-06-13~2016-06-17', 'Platform Core', 'Platform Services', 'SNAP', 'Security', 'Virtual Platforms', 'Total'],
    #      ['In', 13, 15, 14, 1, 1, 44],
    #      ['Out', 10, 17, 9, 1, 1, 38],
    #      ['Change', 3, -2, 5, 0, 0, 6],
    #      ['Fixed', 1, 1, 1, 1, 0, 4]]
    #draw first and last row Black
    plt, table= grapher.draw_table_first_row_colored(data, 2.0*len(data[0]),
                                                  0.4*len(data), 0.98, False, title, 'left', 14)
    #draw last row White
    #cell_dict = table.get_celld()
    #for i in range(0,len(data[0])):
    #        cell_dict[(len(data)-1,i)].set_color(white)
    #        cell_dict[(len(data)-1,i)].set_edgecolor('Black')
    #plt.show()
    #save figure
    plt.savefig(save_to_file, bbox_inches='tight')


def convert_AR_objs_to_html_table(ar_list, table_name):
    """
    Coverts the list of ARs into html table
    :param ar_list: list of ARs
    :param table_name: id of the html table
    :return: html formatted table
    """
    timer = TimeHelper()
    ayer = ArrayMapHelper()
    text = []
    text.append([])
    text[0] = ['Entry-Id','Summary','Assigned-to','Direct\nManager','Reported\nby','Create-date', \
               'Status','Status\nDetails','Prio\nrity','ETA','Report\nGroup',\
               'Report\nFunction','Product\nRel.','Age']
    for obj in ar_list:
        text.append([])
        text[len(text)-1].append(obj.entry_id)
        text[len(text)-1].append(obj.summary)
        text[len(text)-1].append(obj.assigned_to)
        text[len(text)-1].append(obj.direct_manager)
        text[len(text)-1].append(obj.reported_by)
        text[len(text)-1].append(obj.create_date_local)
        text[len(text)-1].append(obj.status)
        text[len(text)-1].append(obj.status_details)
        #text[len(text)-1].append(obj.blocking)
        text[len(text)-1].append(obj.priority)
        #text[len(text)-1].append(obj.type)
        text[len(text)-1].append(obj.estimated_checkin_date_local)
        text[len(text)-1].append(obj.reported_by_group)
        text[len(text)-1].append(obj.reported_by_function)
        text[len(text)-1].append(obj.product_release)
        text[len(text)-1].append(int((timer.get_mtime()-obj.create_date)/(24*60*60)))
    text = ayer.sort_twod_array_by_col(text,1,12)
    return ayer.twod_array_to_html_table(text,table_name,'Blocking ARs'), text


def refine_twod_array(twod_array):
    strer = StringHelper()
    res = list()
    for i in range(0, len(twod_array)):
        res.append(list())
        for j in range(0, len(twod_array[0])):
            print twod_array[i][j]
            res[i].append(strer.split_str_by_length(str(twod_array[i][j]), 15, 45))
    return res


def update_last_record(file, timestamp, csvstr):
    with open(file, "a+") as myfile:
        lines = myfile.readlines()
        l = lines[-1]
        if timestamp in l:
            myfile.seek(0,os.SEEK_END)
            pos = myfile.tell() -len(l) -1
            myfile.seek(pos,os.SEEK_SET)
            myfile.truncate()
        myfile.write(csvstr)
        myfile.close()


def update_AR_summary_history_file(bug_map, entries, file):
    """
    Updates the records in AR summary history file. One record per day.
    :param bug_map: map containing AR infomation
    :return:
    """
    total = 0
    timer = TimeHelper()
    timestamp = timer.mtime_to_local_date(timer.get_mtime())
    for key in bug_map.keys():
        total += bug_map[key]['Product Total']
    csvstr = timestamp
    for rel in entries:
        if rel in bug_map.keys():
            csvstr += ',' + str(bug_map[rel]['Product Total'])
        else:
            csvstr += ',0'
    csvstr += ',' + str(total) + '\n'
    update_last_record(file,timestamp,csvstr)


def get_history_file_enteries(file_name):
    with open(file_name,'r') as myfile:
        lines = myfile.readlines()
        items = lines[0].split(',')
        res = []
        for i in items:
            if ('Date' not in i ) and ('Total' not in i):
                res.append(i)
        myfile.close()
        return res


def generate_AR_trends_report_data_file(num,file_origin,file):
    """
    Generates data file for AR trends report
    :return:
    """
    with open(file_origin, 'r') as myfile:
        lines = myfile.readlines()
        newfile = open(file,'w')
        newfile.write(lines[0])
        if len(lines) < num + 1:
            for i in range(1, len(lines)):
                newfile.write(lines[i])
        else:
            for i in range( len(lines) - num, len(lines)):
                newfile.write(lines[i])
        newfile.close()
        myfile.close()


def get_ca_map_entry(mmap, v):
    v = "\"" + v + "\""
    for k in mmap.keys():
        if v in mmap[k]:
            return k


def get_audit_trail_in_list(parammap):
    timer = TimeHelper()
    cur_date = timer.get_day_start(timer.get_mtime())
    pre_date = cur_date - 24*60*60
    res = []
    in_param = dict(parammap["audit trail param map"])
    in_param['From Time']=[str(pre_date),]
    in_param['To Time']=[str(cur_date),]
    ca_dict = dict(parammap['major areas'])
    for k,v in ca_dict.iteritems():
        if 'To Value' not in in_param.keys():
            in_param['To Value'] = list(v)
        else:
            in_param['To Value'] += list(v)
    dber = DatabaseHelper()
    print in_param
    for e in dber.get_AR_from_audit_trail(in_param)[0]:
        res.append(generate_audit_trail_obj(e))
    return res


def count_audit_in(llist,parammap):
    res = {}
    ayer = ArrayMapHelper()
    for i in llist:
        k = get_ca_map_entry(parammap['major areas'],i.to_value)
        ayer.update_oned_map_values(res,'IN - ' + k)
    return res


def get_audit_trail_out_list(parammap):
    timer = TimeHelper()
    cur_date = timer.get_day_start(timer.get_mtime())
    pre_date = cur_date - 24*60*60
    res = []
    out_param = dict(parammap["audit trail param map"])
    out_param['From Time']=[str(pre_date),]
    out_param['To Time']=[str(cur_date),]
    ca_dict = dict(parammap['major areas'])
    for k, v in ca_dict.iteritems():
        if 'From Value' not in out_param.keys():
            out_param['From Value'] = list(v)
        else:
            out_param['From Value'] += list(v)
    dber = DatabaseHelper()
    print out_param
    for e in dber.get_AR_from_audit_trail(out_param)[0]:
        res.append(generate_audit_trail_obj(e))
    return res


def count_audit_out(llist,parammap):
    res = {}
    ayer = ArrayMapHelper()
    for i in llist:
        k = get_ca_map_entry(parammap['major areas'],i.from_value)
        ayer.update_oned_map_values(res,'OUT - ' + k)
    return res


def update_CA_inout_history_file(ddict, entries, file):
    timer = TimeHelper()
    cur_date = timer.get_day_start(timer.get_mtime())
    pre_date = cur_date - 24*60*60
    timestamp = timer.mtime_to_local_date(pre_date)
    in_total = 0;
    out_total = 0;
    for key in ddict.keys():
        if key.find('IN') != -1:
            in_total += ddict[key]
        elif key.find('OUT') != -1:
            out_total += ddict[key]
    csvstr = timestamp
    for ca in entries:
        if ca in ddict.keys():
            csvstr += ',' + str(int(ddict[ca]))
        else:
            csvstr += ',0'
    csvstr += ',' + str(in_total) + ',' + str(out_total) + '\n'
    update_last_record(file,timestamp,csvstr)


def get_weekday_from_str(datestr):
    curdate = datestr
    curdate = time.strptime(curdate,'%m/%d/%Y')
    curdate = datetime.date(curdate.tm_year,curdate.tm_mon,curdate.tm_mday)
    return curdate.weekday()


def generate_CA_inout_weekly_history_file(num_rec, daily_file, output_file):
    with open(daily_file) as ffile:
        data = ffile.readlines()
        with open(output_file) as output:
            output.write(data[0])

def update_weekly_inout_history_file(daily_file,weekly_file):
    timer = TimeHelper()
    arrayer = ArrayMapHelper()
    datemin = timer.mtime_to_local_date(timer.get_mtime())
    datemin = timer.date_str_to_date_obj(datemin)
    datemin = datemin - datetime.timedelta(datemin.weekday())
    with open(daily_file) as daily:
        daily_data = daily.readlines()
        res = [0]*(len(daily_data[0].split(',')) - 1)
        for i in range(-7, 0):
            tmp = daily_data[i].split(',')
            tmpdate = timer.date_str_to_date_obj(tmp[0])
            if tmpdate >= datemin:
                res = arrayer.sum_two_arrays(res,tmp[1:])
    csvstr = datemin.strftime('%m/%d/%Y') + ','
    csvstr += arrayer.array_to_csv_string(res)
    update_last_record(weekly_file,datemin.strftime('%m/%d/%Y'),csvstr)


def sent_report_email(parammap,entries,files_to_send,bug_releases,additional_body):
    """
    Sends out report via email
    :param bug_releases: release of the bugs
    :param additional_body: additional to append at the end of the email
    :return:
    """
    mailer = EmailHelper()
    #TO = 'youye.sun@emc.com'
    #CC='youye.sun@emc.com'
    att = files_to_send['attachment']
    subj = parammap['report name'] + ' Bug Report'
    ifHtmlNody = True
    embed_images = files_to_send['image']
    body='<h3>This Report Is Generated Automatically By Product Integration Engineering Team.</h3><hr>'
    if len(additional_body) != 0:
        body += '<p><a href="#blockings">Check The Details Of Blocking ARs<a/></p>'
    notice = ''
    for key in entries:
        if key not in bug_releases:
            notice += key + ', '
    if len(notice) is not 0:
        notice = '<p style="color:red">' + notice[:-2]
        notice = notice + ' had 0 AR when this report was generated. First chart of this report does not show this' +\
                 ' information. But we are keeping track of it.<p>'
    #notice = '<p style="color:red"> Resent to more people..</p>' + notice
    body = body + notice
    style = '<style>table,th,td{border: 1px solid black;border-collapse: collapse;font-family:"Arial";'+\
            'font-size:8.0pt;color:black} table{width:900px;}caption{text-align: left;font-size:14.0pt;}'+\
            'th{text-align:center;font:bold;background-color:#ccff99} td{text-align:center;font:bold;}' +\
            'span{margin-bottom:20px;display:block;font-family:"sans-serif";font-size:14.0pt;}</style>'
    #print parammap['to']
    #print parammap['cc']
    mailer.send_email(parammap['to'],subj,style+body,ifHtmlNody,embed_images,additional_body,parammap['cc'],att)


def count_by_ca_manager(arobjlist, cas, camap):
    res = dict()
    for k in cas:
        res[k] = list()
    for o in arobjlist:
        for k in cas:
            if o.direct_manager in camap[k] or o.assigned_to in camap[k]:
                res[k].append(o)
                break
    return res


def update_target_records(file, ar_count_map):
    timer = TimeHelper()
    timestamp = timer.mtime_to_local_date(timer.get_mtime())
    csvstr = timestamp
    for k in sorted(ar_count_map.keys()):
        csvstr += ',' + str(len(ar_count_map[k]))
    csvstr += '\n'
    update_last_record(file,timestamp,csvstr)


def catarget(arobjlist, parammap):
    cammap = dict(parammap['major area manager'])
    ayer = ArrayMapHelper()
    cammap = ayer.remove_map_quote(cammap)
    ar_count_map = count_by_ca_manager(arobjlist, parammap["target"].keys(),cammap)

    update_target_records(fpath+'\\'+parammap['ca target'], ar_count_map)
    return ar_count_map


def upload_sharepoint(dst, imgs):
    #mapDrive("r:", dst, base64.b64decode(ARGS[0]), base64.b64decode(ARGS[1]))
    #for img in imgs:
    #    shutil.copy(img, "r:/")
    #unmapDrive("r:")
    return 1


#def upload_sharepoint_workaround_checkout(dst, imgs):
    #mapDrive("r:", dst, base64.b64decode(ARGS[0]), base64.b64decode(ARGS[1]))
    #for img in imgs:
    #    try:
    #        os.remove("r://" + img[img.rfind('\\')+1:])
    #    except Exception,e:
    #        print "remove file error"
    #    shutil.copy(img, "r:/")
    #unmapDrive("r:")


def add_assigned_to_ca(objlist, ca_manager_map):
    cammap =dict(ca_manager_map)
    ayer = ArrayMapHelper()
    cammap = ayer.remove_map_quote(cammap)
    for ar in objlist:
        for k in cammap.keys():
            if ar.direct_manager in cammap[k] or ar.assigned_to in cammap[k] :
#                print ar.direct_manager,ar.assigned_to,k
#                logger.debug(ar.direct_manager+"+"+ar.assigned_to+"+"+k)
                ar.owning_ca = k
                break


def main():
    parammap = init_param(arg_parser())
    fprefix = fpath+'\\'+parammap['report name'].replace(' ','')
    files_to_send = {}
    files_to_send['attachment'] = []
    files_to_send["image"] = []
    sharepoint_images = list()
    sharepoint_files = list()
    additional_body = ""

    logger.debug("="*25 + "Start" + "="*25 + "\n" + "-"*25 + "REPORT NAME: " + parammap['report name'] + "-"*25)
    dber = DatabaseHelper(logger)
    grapher = GraphHelper(logger)


    rawars, numrawars = dber.get_AR_from_assigned_to_manager(parammap['assinged to manager param map'])
    if numrawars == 0:
        logger.debug("No open AR ...")
        return

#get ar object list
    ar_obj_list = get_ar_obj_list(rawars)

#get Unified and TBSP1 AR
    unified_systems_ar = filter_product_family(ar_obj_list,["Unified Systems"],True)
    unified_thunderbirdsp1_ar = filter_release(unified_systems_ar,"Thunderbird SP1")
    print "Thunderbird SP1 AR number", len(unified_thunderbirdsp1_ar)

#add ARs assigned to ca
#    if "major area manager" in parammap.keys():
#       add_assigned_to_ca(ar_obj_list,parammap["major area manager"])

#save AR list to excel && append excel to sharepoint
    save_AR_list_to_excel(ar_obj_list, fprefix + 'ARList.xls')
    sharepoint_files.append(fprefix + 'ARList.xls')

#report:    All ARs (Product+Test)
    #bugmap
    bugmap = bug_total_report(ar_obj_list,parammap['report name'] + ' All ARs (Product+Test)', fprefix+ '-bug-total.png')
    files_to_send["image"].append(fprefix+ '-bug-total.png')
    files_to_send['attachment'].append(fprefix + 'ARList.xls')

#report:    Product ARs by Age
    bug_age_report(ar_obj_list,parammap['report name'] + ' Product ARs by Age',COLOR_SETS[0],fprefix + '-bug-age.png')
    files_to_send["image"].append(fprefix + '-bug-age.png')
    sharepoint_images.append(fprefix + '-bug-age.png')

#report:    AR Trend report
    update_AR_summary_history_file(bugmap,get_history_file_enteries(fpath+'\\'+parammap['ar history file']),
                                   fpath+'\\'+parammap['ar history file'])
    generate_AR_trends_report_data_file(130,fpath+'\\'+parammap['ar history file'],fprefix+"ARTrendsDataFile.csv")

    grapher.draw_trent_chart(fprefix+"ARTrendsDataFile.csv",['Total'],'Total '+parammap['report name']+' AR Trend',
                             7,4,20,'weekly',fprefix+'-total-trend.png')
    files_to_send["image"].append(fprefix+ '-total-trend.png')
    '''
#report:    AR In/Out report
    audit_in_list = get_audit_trail_in_list(parammap)
    in_map = count_audit_in(audit_in_list,parammap)
    print in_map
    audit_out_list = get_audit_trail_out_list(parammap)
    out_map = count_audit_out(audit_out_list,parammap)
    in_map.update(out_map)
    update_CA_inout_history_file(in_map,get_history_file_enteries(fpath+'\\'+parammap['ar in out file']),
                                 fpath+'\\'+parammap['ar in out file'])
    generate_AR_trends_report_data_file(datetime.datetime.today().weekday()+4*7,fpath+'\\'+parammap['ar in out file'],
                                        fprefix+"ARInOutDataFile.csv")
    grapher.draw_trent_chart(fprefix+"ARInOutDataFile.csv",["IN - Total","OUT - Total"],
                     parammap['report name']+' AR Incoming/Outgoing Trend',7,4,5,'weekly',fprefix+'-inout-trend.png')
    files_to_send["image"].append(fprefix+ '-inout-trend.png')
    '''
#report:      ARs for Direct Manager
    unity_direct_manager_report(ar_obj_list,parammap['report name']+' ARs for Direct Manager',fprefix+'-bug-manager.png')
    files_to_send["image"].append(fprefix + '-bug-manager.png')

#report:     TBV for Direct Manager
    tbv_list, num_tbv = dber.get_AR_from_reported_to_manager(parammap['reported by manager param map'])
    logger.debug("tbv_list : "+str(tbv_list))
    if num_tbv != 0:
        tbvobjlist = get_ar_obj_list(tbv_list)
        if "major area manager" in parammap.keys():
            add_assigned_to_ca(tbvobjlist,parammap["major area manager"])
        save_AR_list_to_excel(tbvobjlist,fprefix+'TBVList.xls')
        files_to_send['attachment'].append(fprefix+'TBVList.xls')
        sharepoint_files.append(fprefix+'TBVList.xls')
        unity_direct_manager_report(tbvobjlist,parammap['report name'] + ' TBV for Direct Manager',fprefix+'-tbv-manager.png')
        files_to_send["image"].append(fprefix + '-tbv-manager.png')

#report:     ARs In/Out by CA by releases
    for rel in sorted(parammap['in out report releases']):
        save_to_file=fprefix+rel.replace(' ','')+'-ar-in-out.png'
        title="AR In/Out/Change/Fix by CA"+"("+str(rel)+")"
        ar_in_out_report(parammap,rel,title,save_to_file)
        files_to_send["image"].append(save_to_file)

#report:     ARs by Age by releases
    for rel in parammap['age report releases']:
        filtered_obj_list = filter_release(ar_obj_list,rel)
        if len(filtered_obj_list) != 0:
            bug_age_report(filtered_obj_list,rel[0] +' ARs by Age',
                           COLOR_SETS[((parammap['age report releases'].index(rel))+1)%len(COLOR_SETS)],
                           fprefix+rel[0].replace(' ','')+'-bug-age.png')
            files_to_send["image"].append(fprefix+rel[0].replace(' ','')+'-bug-age.png')
            #####
            sharepoint_images.append(fprefix+rel[0].replace(' ','')+'-bug-age.png')

#report:    Thunderbird SP1 "Actual" and "ARs by Age" by CA
    if "target" in parammap.keys():
        ar_count_map = catarget(unified_thunderbirdsp1_ar,parammap)
        ar_history_data = read_csv(fpath+'\\'+parammap["ca target"])
        logger.debug("ar_history_data.Date.values :"+str(ar_history_data.Date.values))
        for k in sorted(parammap["target"].keys()):
            grapher.draw_target_chart(ar_history_data,TARGET_DATES,parammap["target"][k],ar_history_data.Date.values,ar_history_data[k].values,
                                      k + " Defect Actual(Thunderbird SP1) ",7,4,5,fprefix+k.replace(' ','')+'-defect-targets.png')
            files_to_send["image"].append(fprefix+k.replace(' ','')+'-defect-targets.png')
            #####
            sharepoint_images.append(fprefix+k.replace(' ','')+'-defect-targets.png')
            ca_ar_obj_list = ar_count_map[k]
            #if len(ca_ar_obj_list) != 0:
            bug_age_report(ca_ar_obj_list,k +' ARs by Age(Thunderbird SP1)',
                           COLOR_SETS[((parammap["target"].keys().index(k))+1)%len(COLOR_SETS)],
                           fprefix+k.replace(' ','')+'thunderbirdsp1-bug-age.png')
            files_to_send["image"].append(fprefix+k.replace(' ','')+'thunderbirdsp1-bug-age.png')

            sharepoint_images.append(fprefix+k.replace(' ','')+'thunderbirdsp1-bug-age.png')

#report:      Blocking ARs
    blocking_ar_list = get_blocking_AR(ar_obj_list)
    if len(blocking_ar_list) != 0:
        additional_body, blocking_text = convert_AR_objs_to_html_table(blocking_ar_list,'blockings')
        blocking_text = refine_twod_array(blocking_text)
        plt, table = grapher.draw_table_first_row_colored(blocking_text,1*len(blocking_text[0]),0.5*len(blocking_text), 0.98, True,
                                             parammap['report name']+' Blocking ARs', 'left', 10)
        plt.savefig(fprefix+'-total-blocking.png', bbox_inches='tight')

        sharepoint_images.append(fprefix+'-total-blocking.png')
        files_to_send["image"].append(fprefix+'-total-blocking.png')
        additional_body = ""
#upload sharepoint
#    if "sharepoint imgs" in parammap.keys():
#        upload_sharepoint(parammap["sharepoint imgs"], sharepoint_images)
#   if "sharepoint fls" in parammap.keys():
#        upload_sharepoint(parammap["sharepoint fls"], sharepoint_files)

#send report email
    sent_report_email(parammap,get_history_file_enteries(fpath+'\\'+parammap['ar history file']),
                      files_to_send,bugmap.keys(),additional_body)


if __name__ == '__main__':
    main()




"""



#report:      Bugs for Product Area
    if "product area table" in parammap.keys():
        unity_product_area_report(ar_obj_list,parammap['report name']+' Bugs for Product Area', fprefix+'-product-area.png')
        files_to_send["image"].append(fprefix+'-product-area.png')

#report:      Bugs for Major Area
    if "major area table" in parammap.keys():
        unity_major_area_report(ar_obj_list,parammap['report name']+' Bugs for Major Area', fprefix+'-major-area.png')
        files_to_send["image"].append(fprefix+'-major-area.png')


"""



