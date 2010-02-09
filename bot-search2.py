#!/usr/bin/env python
#-*- coding: UTF-8 -*-



import urllib
import ConfigParser
import ClientForm
import mechanize as ClientCookie
try:
    import BeautifulSoup
except ImportError,e:
    print "Vous devez installer le module BeautifulSoup"
import re
import os
import sys




class BotForum(object):
    def __init__(self):
        print sys.argv
        arg = []
        mode = "search"
        if len(sys.argv)>1:
            mode = sys.argv[1]
            arg =sys.argv[2:]
        login = None
        password = None
        if os.path.exists("config.ini"):
            config_ini = ConfigParser.SafeConfigParser()
            config_ini.readfp(open("config.ini"))
            list_section = config_ini.sections()
            if config_ini.has_section('core'):
                if config_ini.has_option('core','login'):
                    login = config_ini.get('core','login')
                if config_ini.has_option("core","password"):
                    password = config_ini.get("core","password")
        if login and password:
            self.connect(login,password)
        if mode == "search":
            kwargs = {}
            if len(arg):
                if int(arg[0]):
                    kwargs["nb_page"] = int(arg[0])
            if len(arg) == 2:
                if int(arg[1]):
                    kwargs["start_page"] = int(arg[1])
            self.search_post(**kwargs)
        elif mode == "list":
            self.list_post()



    def connect(self,login,password):
        cookieJar = ClientCookie.CookieJar()
        opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cookieJar))
        opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
        ClientCookie.install_opener(opener)
        fp = ClientCookie.urlopen("http://forum.ubuntu-fr.org/login.php")
        forms = ClientForm.ParseResponse(fp)
        fp.close()
        form = forms[1]
        form["req_username"] = login
        form["req_password"] = password
        fp = ClientCookie.urlopen(form.click())
        fp.close()


    #print forms
    def list_post(self,**kwargs):
        nb_page = kwargs.get("nb_page",2)
        start_page = kwargs.get("start_page",1)
        forum = kwargs.get("forum","16")

        topics = {}
        topic_by_auteur = {}
        pagenums = {}
        url = "http://forum.ubuntu-fr.org/search.php?action=show_24h"
        obj_page = urllib.urlopen(url)
        soup = BeautifulSoup.BeautifulSoup( obj_page )
        p_page = soup.findAll("p","pagelink")[0]
        url_pages = p_page.findAll("a")
        url = url_pages[-1]["href"].split("&p=")[0]
        url = "http://forum.ubuntu-fr.org/"  + url + "&p=%s"
        print url
        nb_page = url_pages[-1].contents[0].strip()
        nb_page = int(nb_page)
        print nb_page
        control = False

        for num_page in range(start_page,start_page + nb_page):
            url_tmp = url % num_page
            print url_tmp
            obj_page = urllib.urlopen(url_tmp)
            soup = BeautifulSoup.BeautifulSoup( obj_page )

            for item in soup.findAll("div","tclcon"):
                if item.contents[0] and  u"D&eacute;plac&eacute;" in  item.contents[0].strip():
                    continue
                lien  = item.findAll("a")[0]
                span = item.findAll("span")[0]
                auteur = span.contents[0].replace("par&nbsp;","")
                url_topic =  lien["href"]
                id = url_topic.split("id=")[-1]
                titre = lien.string
                topics[id] = {"id":id,"auteur":auteur,"titre":titre,"url":url_topic}
                topic_by_auteur.setdefault(auteur,[])
                topic_by_auteur[auteur].append(id)
        auteur_many_topic = dict([(key,value) for key,value in topic_by_auteur.items() if len(value) >2])
        for auteur,id_topics in auteur_many_topic.items():
            print "Auteur : ", auteur
            print "--"
            for item in id_topics:
                print topics[item]["titre"]
            print "_____________________________"

    def search_post(self,**kwargs):
        nb_page = kwargs.get("nb_page",20)
        start_page = kwargs.get("start_page",1)
        forum = kwargs.get("forum","16")

        topics = {}
        pagenums = {}
        for num_page in range(start_page,start_page + nb_page):
            url = " http://forum.ubuntu-fr.org/viewforum.php?id=16&p=%s" % num_page
            print url
            obj_page = urllib.urlopen(url)
            soup = BeautifulSoup.BeautifulSoup( obj_page )
            for item in soup.findAll("div","tclcon"):
                if item.contents[0] and  u"D&eacute;plac&eacute;" in  item.contents[0].strip():
                    continue
                lien  = item.findAll("a")[0]
                url =  lien["href"]
                id = url.split("id=")[-1]
                titre = lien.string
                print titre
                wifipatterns=["wifi","wi-fi","iwconfig","wep","wpa","ndiswrapper","atheros","ath\d","ralink"]
                wifiregexp=re.compile('|'.join(wifipatterns),re.IGNORECASE)
                if wifiregexp.search(titre):
                    topics[id] = titre
                    pagenums[id] = num_page
                    #break

        html_page =\
        u"""<!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN' 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
        <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
            <head>
            </head>
            <body >
            <form method="post" action="http://forum.ubuntu-fr.org/moderate.php?fid=16">
            <table>
            <tr>
                <th>Page</th>
                <th>Titre</th>
                <th>Lien</th>
                <th></th>
            </tr>"""

        for id,titre in topics.items():
            try:
                html_page += """<tr>
                    <td><a href="http://forum.ubuntu-fr.org/viewforum.php?id=16&p=%s">%s</a></td>
                    <td>%s</td>
                    <td><a href="http://forum.ubuntu-fr.org/viewtopic.php?id=%s">voir le sujet</a></td>
                    <td>
                    <input type="checkbox" name="topics[%s]" value="1" checked />
                    </td>
                    </tr>""" %(pagenums[id],pagenums[id],titre,id,id)
            except Exception,e:
                print e
                print titre


        html_page  +=  """
        </table> <input type="submit" value="Deplacer" name="move_topics">
        </form>
        </body>
        </html>"""


        obj_file = open("log.html","w")
        html_page = html_page.encode("utf-8")
        obj_file.write(html_page)
        obj_file.close()

        import pprint
        pprint.pprint(topics)

if __name__== "__main__":
    BotForum()

