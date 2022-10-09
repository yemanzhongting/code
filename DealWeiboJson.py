import requests
import time
import json
import re
import os
from pyquery import PyQuery as pq
import math
import os,json
import pandas as pd

key = ''  # 这里填写你的百度开放平台的key
x_pi = 0
pi = 0 # π
a =0 # 长半轴
ee = 0  # 扁率
#椭球参数关注微信公众号“协同感知与知识服务”（sensingcity）后台回复 椭球参数 免费获取

def transformlat(lng, lat):
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + \
          0.1 * lng * lat + 0.2 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 *
            math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 *
            math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def transformlng(lng, lat):
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + \
          0.1 * lng * lat + 0.1 * math.sqrt(math.fabs(lng))
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 *
            math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 *
            math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 *
            math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False


def bd09togcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return [gg_lng, gg_lat]


def gcj02towgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = transformlat(lng - 105.0, lat - 35.0)
    dlng = transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return [lng * 2 - mglng, lat * 2 - mglat]


def bd09towgs84(lng, lat):  # 114.277591,30.580842
    result2 = bd09togcj02(lng, lat)
    result4 = gcj02towgs84(result2[0], result2[1])
    return result4


# 日期转换
def trans_format(time_string):
    from_format = '%a %b %d %H:%M:%S +0800 %Y'
    to_format = '%Y-%m-%d %H:%M:%S'
    time_struct = time.strptime(time_string, from_format)
    times = time.strftime(to_format, time_struct)
    return times


def geocodeB(address, city):
    loca = {}
    try:
        if address.find('·'):
            address = address.replace('·', '市', 1)
        base = "http://api.map.baidu.com/geocoder?address=" + address + "&city=" + str(city) + "&output=json&key="+key"
        response = requests.get(base,timeout=(3.05, 27))
        answer = response.json()
        tamped = bd09towgs84(answer['result']['location']['lng'], answer['result']['location']['lat'])
        loca['lng'] = tamped[0]
        loca['lat'] = tamped[1]
        print(address,loca['lng'], loca['lat'])

        if loca:
            return loca
    except:
        print(address)
        loca['lng'] = 0
        loca['lat'] = 0
        return loca
        # geocodeB(address, city)
def get_latlng(location,address_dict,cityname):
    if location in address_dict:
        loca = address_dict[location]
    else:
        loca = geocodeB(location, cityname)
        # print(location)
        address_dict[location] = loca
    return loca

#前面是坐标转换分割线
######################
def pdfFilesPath(path):
    filePaths = [] # 存储目录下的所有文件名，含路径
    for root,dirs,files in os.walk(path):
        for file in files:
            if file.split('.')[-1]=='json':
                filePaths.append(os.path.join(root,file))
    return filePaths

if __name__=='__main__':
    # 原始Json文件所在文件夹
    filepath = r'C:\全国微博数据'
    files=pdfFilesPath(filepath)
    
    #我们抓取的字段
    columns=['user_id','lng','lat','user_name','reposts_count',
        'weibo_text','weibo_id','create_time','fans_num','location','img_url','follow_num','gender','Address','Heat','Source','city']
    
    for file in files:
        #每个城市一个地址词典
        address_dict = {}
        
        with open(file,'rb+') as f:
            tmp=f.readlines()
        cityname=json.loads(tmp[0])['city']
        
        print('正在处理...'+cityname)
        if cityname in ['长沙','深圳','广州','上海','杭州','郑州','成都','天津','福州','南京']:
            with open(cityname+'.csv','w+',encoding='utf-8') as f:
                for col in columns:
                    f.write(col)
                    f.write(',')
                f.write('\n')
                for i in tmp:
                    data=json.loads(i)
                    for col in columns:
                        f.write(str(data[col]).replace('\n',''))
                        f.write(',')
                    f.write('\n')
        
            df=pd.read_csv(cityname+'.csv',error_bad_lines=False)
            rf=df.drop_duplicates(subset=['weibo_id'], keep='first', inplace=False)
            rf=rf.drop(['Unnamed: 17'], axis=1)
        
            rf['latlng'] = rf.apply(lambda x: get_latlng(x['location'],address_dict,cityname), axis=1)
        
            rf['lat'] = rf.apply(lambda x: x['latlng']['lat'], axis=1)
            rf['lng'] = rf.apply(lambda x: x['latlng']['lng'], axis=1)
            rf=rf.drop(['latlng'], axis=1)
            rf.to_csv('完整版'+cityname+'.csv',index=None)
            rf[['user_id','lng','lat','reposts_count',
            'weibo_text','weibo_id','create_time',
            'fans_num','location','follow_num','gender',
            'Address','Heat','Source','city']].head(20000).to_csv('共享版'+cityname+'.csv',index=None)
