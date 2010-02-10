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
from optparse import OptionParser
from utils import htmlentitydecode




class BotForum(object):
    def __init__(self):
        self.parse_option()
        login = None
        password = None
#        if os.path.exists("config.ini"):
#            config_ini = ConfigParser.SafeConfigParser()
#            config_ini.readfp(open("config.ini"))
#            list_section = config_ini.sections()
#            if config_ini.has_section('core'):
#                if config_ini.has_option('core','login'):
#                    login = config_ini.get('core','login')
#                if config_ini.has_option("core","password"):
#                    password = config_ini.get("core","password")
#        if login and password:
#            self.connect(login,password)


    def parse_option(self):
        usage = "usage: %prog [options] arg"
        parser = OptionParser(usage)
        parser.add_option("-m", "--mode", dest="mode",
                          help=u"Choisir quel mode lancer(doublons,recherche)",
                          choices=("doublons","recherche"))
        parser.add_option("-f", "--file", dest="filename",
                        help=u"Permet de charger un fichier de configuration")
        parser.add_option("-n", "--nb_page", dest="nb_page",type="int",default=10,
                        help=u"Défini le nombre de page vue")
        parser.add_option("-p", "--start_page", dest="start_page",type="int",default=1,
                        help=u"Défini la premiére page")
        parser.add_option("-i", "--forum_id", dest="forum_id",type="int",
                        help=u"Défini l'id du forum")
        (options, args) = parser.parse_args()
        if  not options.mode:
            parser.error("L'option mode est obligatoire")
        mode = options.mode
        print options.filename
        if mode == "doublons":
            self.doublons()
        elif mode == "recherche" and options.filename:
            forum_id = options.forum_id
            if os.path.exists(options.filename):
                config_ini = ConfigParser.SafeConfigParser()
                config_ini.readfp(open(options.filename))
                list_section = config_ini.sections()
                if config_ini.has_section('core'):
                    if config_ini.has_option('core','forum_id'):
                        value = config_ini.get('core','forum_id')
                        forum_id = value if value else forum_id
                    if config_ini.has_option("core","patterns"):
                        patterns = config_ini.get("core","patterns")
                        patterns = [item.strip() for item in patterns.strip().split(",")]
                if not patterns:
                    print "Vous devez specifier les mots à rechercher"
                    sys.exit(2)
                if not forum_id:
                    print "Vous devez specifier un forum id"
                    sys.exit(2)
                kwargs = {"nb_page":options.nb_page,"forum_id":forum_id,"patterns":patterns,\
                    "start_page":options.start_page}
                self.search_post(**kwargs)
            else:
                print "Le fichier n'existe pas"
                sys.exit(2)



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
    def doublons(self,**kwargs):
        import difflib
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

        for num_page in range(1,1 + nb_page):
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
                titre = htmlentitydecode(lien.string)
                topics[id] = {"id":id,"auteur":auteur,"titre":titre,"url":url_topic}
                topic_by_auteur.setdefault(auteur,[])
                topic_by_auteur[auteur].append(id)
        auteur_many_topic = dict([(key,value) for key,value in topic_by_auteur.items() if len(value) >1])
        for auteur in auteur_many_topic.keys():
           for id_nbr in range(len(auteur_many_topic[auteur])):
               title=topics[auteur_many_topic[auteur][id_nbr]]['titre']
               #print title
               titles=[topics[id]['titre'] for id in auteur_many_topic[auteur]][id_nbr+1:]
               #print titles
               matchs=difflib.get_close_matches(title,titles,cutoff=0.5)
               if len(matchs) > 0:
                   print('--------------\n'+auteur)
                   print(title)
                   for titre in matchs:
                       print(titre)

#        for auteur,id_topics in auteur_many_topic.items():
#            print "Auteur : ", auteur
#            print "--"
#            for item in id_topics:
#                print "id: %s topic: %s" % (item,  topics[item]["titre"])
#            print "_____________________________"

    def search_post(self,**kwargs):
        nb_page = kwargs["nb_page"]
        start_page = kwargs["start_page"]
        forum_id = kwargs["forum_id"]
        patterns = kwargs["patterns"]

        topics = {}
        pagenums = {}
        for num_page in range(start_page,start_page + nb_page):
            url = " http://forum.ubuntu-fr.org/viewforum.php?id=%s&p=%s" %(forum_id, num_page)
            print url
            obj_page = urllib.urlopen(url)
            soup = BeautifulSoup.BeautifulSoup( obj_page )
            for item in soup.findAll("div","tclcon"):
                if item.contents[0] and  u"D&eacute;plac&eacute;" in  item.contents[0].strip():
                    continue
                lien  = item.findAll("a")[0]
                url =  lien["href"]
                id = url.split("id=")[-1]
                titre = htmlentitydecode( lien.string)
                print titre
                wifiregexp=re.compile('|'.join(patterns),re.IGNORECASE)
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
            <form method="post" action="http://forum.ubuntu-fr.org/moderate.php?fid=%s">
            <table>
            <tr>
                <th>Page</th>
                <th>Titre</th>
                <th>Lien</th>
                <th></th>
            </tr>""" %(forum_id)

        for id,titre in topics.items():
            try:
                html_page += """<tr>
                    <td><a href="http://forum.ubuntu-fr.org/viewforum.php?id=%s&p=%s">%s</a></td>
                    <td>%s</td>
                    <td><a href="http://forum.ubuntu-fr.org/viewtopic.php?id=%s">voir le sujet</a></td>
                    <td>
                    <input type="checkbox" name="topics[%s]" value="1" checked />
                    </td>
                    </tr>""" %(forum_id,pagenums[id],pagenums[id],titre,id,id)
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


if __name__== "__main__":
    BotForum()

