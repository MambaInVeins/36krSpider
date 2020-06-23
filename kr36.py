import requests
from bs4 import BeautifulSoup
import re
import time
import socket
import sys
from selenium import webdriver
import hashlib
from lxml import etree
import os
import csv

class Crawler:
    """docstring for Crawler"""
    def __init__(self, url):
        self.path = os.path.abspath('.')
        self.name = '36kr'
        self.browser = webdriver.Firefox()
        option = webdriver.FirefoxOptions()
        option.add_argument('--headless')
        # drivepath = r'D:\Software\Python 3.6.8\Lib\site-packages\selenium\chromedriver.exe'
        self.browser = webdriver.Firefox(options = option)
        self.browser.get(url)

    def getUser(self,url):
        userset = set()
        try:
            for j in range(1):
                try:
                    button = self.browser.execute_script("var div = document.getElementsByClassName('kr-loading-more-button show'); div[0].click();")
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
                    time.sleep(2)
                except:
                    print('could not click more!')
                    sys.exit()
            bs = BeautifulSoup(self.browser.page_source,'html.parser')
            if bs is not None:
                for link in bs.find_all('a',href=re.compile('^(/user/)')):
                    if 'href' in link.attrs:
                        url = link.attrs['href']
                        if url != '' and url not in userset:
                            userset.add(url)
                    # time.sleep(0.3)
        except HTTPError as e:
            print('Error：网页在服务器上不存在')
            return None
        except URLError as e:
            print('Error：服务器不存在')
            return None
        except AttributeError as e:
            print('AttributeErrorError')
            return None
        return userset

    def getPage(self,url): 
        linkset = set()
        try:  
            self.browser.get(url)
            for j in range(3):
                try:
                    button = self.browser.execute_script("var div = document.getElementsByClassName('kr-loading-more-button show'); div[0].click();")
                    self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);") 
                    time.sleep(2)
                except:
                    # print('could not click more!')
                    pass
            bs = BeautifulSoup(self.browser.page_source,'html.parser')
            if bs is not None:
                username = bs.find('a',class_="author-name").get_text()
                for link in bs.find_all('a',href=re.compile('^(/p/)')):
                    if 'href' in link.attrs:
                        url = link.attrs['href']
                        if url != '' and url not in linkset:
                            linkset.add(url)
                    # time.sleep(0.3)
        except Exception as e:
            print(e)
            return None
        return username,linkset

    def write_csv(self,data):
        path = '36kr.csv'
        with open(path, 'a+',encoding='utf-8',errors='ignore') as f:  # Just use 'w' mode in 3.x
            w = csv.DictWriter(f, data.keys())
            # w.writeheader()
            w.writerow(data)

    def clean_text(self,text):
        # NOTE: 完全清除所有的符号，只保留中文
        # comp = re.compile('[^A-Z^a-z^0-9^\u4e00-\u9fa5]')
        # return comp.sub('', text)
        # NOTE: 将中文特殊符号使用‘，’进行替换
        return re.sub(u"([^\u4e00-\u9fa5\u0030-\u0039\u0041-\u005a\u0061-\u007a])",",",text)

    def write_txt(self,data):

        fw = open('d:\\Data\Webspider\\news\\' + self.clean_text(data[0]) + '.txt','a+',encoding='utf-8')
        # NOTE:上述代码需要在制定位置建立相应的文件夹
        # filename = str(data[0])+ '.txt' # NOTE: r'D:\Data\Webspider\news'+'\\' +
        # fw = open(filename,'a+',encoding='utf-8')
        for element in data:
            fw.write(str(element))
            fw.write('\r\n')

    def getEssay(self,url,user):
        item={}
        item['user_name'] = user
        # item['spider_name']=self.name
        item['file_urls']=[]
        item['source_url'] = url
        item['img_info'] = []
        contentlist = list()
        text = requests.get(url).text
        html = etree.HTML(text)
        content_body = html.xpath(".//div[@class='common-width content articleDetailContent kr-rich-text-wrapper']/*")  
        img_items = html.xpath(".//div[@class='common-width content articleDetailContent kr-rich-text-wrapper']//img")
        for img in img_items:
            src = img.xpath("./@src")[0]
            if src:
                img_path='/36kr/' + '/'.join(src.split("/")[3:])   # 图片存储路径保留原网站路径
                img_id=self.get_md5_value(src)
                item['img_info'].append({"id":img_id,"path":img_path,"url":src})
                item['file_urls'].append(src)
                self.download_img(src,img_path)
        #标题
        item['title']=html.xpath(".//h1/text()")[0]
        #内容
        item['content']=''
        img_num=0
        for i in content_body:
            if i.xpath(".//img"):
                img_tab = "\n<img>@img_id={}</img>\n".format(item['img_info'][img_num]["id"])
                item['content'] += img_tab
                img_num += 1
            else:
                item['content'] +="".join(i.xpath(".//text()"))
        # item['content'] = self.clean_text(item['content'])
        #时间
        timestamp = int(re.findall('"publishTime":(\d+)',text)[0])
        time_local = time.localtime(timestamp/1000)
        pub_time = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        item['pub_time'] = pub_time
        return item

    def get_md5_value(self,src):
        my_md5 = hashlib.md5()
        my_md5.update(src.encode())
        my_md5_Digest = my_md5.hexdigest()
        return my_md5_Digest

    def download_img(self,src,path):
        folder_path = self.path + '/'.join(path.split('/')[0:-1])
        print(folder_path)
        try:
            pic = requests.get(src, timeout=10)
            try:
                #保存图片路径
                if os.path.exists(folder_path) == False:
                    os.makedirs(folder_path)
                print(self.path + path)    
                fp = open(self.path + path, 'wb')
                fp.write(pic.content)
                fp.close()
            except OSError:#文件名、目录名或卷标语法不正确
                pass
        except requests.exceptions.ConnectionError:
            print('图片无法下载')
        except:
            pass

    def mkdir_multi(self,path):
        # 判断路径是否存在
        isExists=os.path.exists(path)
        if not isExists:
            # 如果不存在，则创建目录（多层）
            os.makedirs(path) 
            print('目录创建成功！')
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            print('目录已存在！')
            return False


if __name__ == "__main__":
    socket.setdefaulttimeout(25)
    # 获取科技板块首页用户
    domain = 'https://36kr.com'
    target = domain + '/information/technology'
    num = 0
    try:
        crawler = Crawler(target)
        userset = crawler.getUser(target)
        
        userlist = list(userset)
        count_user = len(userlist)
        print(count_user)
        if count_user >= 20 :
            userlist = userlist[0:20]
        else:
            pass
        for user in userlist:
            user_url = domain + user
            username,linkset = crawler.getPage(user_url)
            print(username)
            count_eassy = 0
            for link in linkset:
                essay_url = domain + link
                try:
                    data = crawler.getEssay(essay_url,username)
                    print(data)
                    crawler.write_csv(data)
                    count_eassy += 1
                except Exception as e:
                    print(e)
                if count_eassy > 50:
                    break
        crawler.browser.close()
    except socket.timeout:
        print('获取连接超时！')