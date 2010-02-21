#!/usr/bin/env python
#-*- coding: UTF-8 -*-
"""Programme offrant différentes options pour simplifier la modération
    d'un forum"""


import re
import os
import sys
from optparse import OptionParser
import urllib
import urllib2
from urllib2 import urlopen
import cookielib
import ConfigParser
from operator import itemgetter
from datetime import timedelta, datetime
import difflib


try:
    from mako.lookup import TemplateLookup
except ImportError,e:
    print('VOus devez installer le module mako')
try:
    import BeautifulSoup
except ImportError, e:
    print("Vous devez installer le module BeautifulSoup")


from utils import htmlentitydecode, transform_date






mylookup = TemplateLookup(directories=['templates'], module_directory='/tmp/mako_modules',
       output_encoding='utf-8' )
URL_FORUM = "http://forum.ubuntu-fr.org/viewforum.php?id=%s"
URL_24H = "http://forum.ubuntu-fr.org/search.php?action=show_24h"
URL_TOPIC = "http://forum.ubuntu-fr.org/viewtopic.php?id=%s"
COOKIE_FILE = "bot_cookie.txt"
homedir = os.getenv("HOME")
CONFIG_FILE = os.path.join(homedir,".config/ForumBot/config")

class BotForum(object):
    """Cette classe regroupe un ensemble d'outils permettant de simplifier
    l'admistration d'un forum punbb"""

    def __init__(self):
        login = None
        password = None
        if os.path.exists(CONFIG_FILE):
            config_ini = ConfigParser.SafeConfigParser()
            config_ini.readfp(open(CONFIG_FILE,'r'))
            list_section = config_ini.sections()
            if config_ini.has_section('core'):
                if config_ini.has_option('core','login'):
                    login = config_ini.get('core','login')
                if config_ini.has_option("core","password"):
                    password = config_ini.get("core","password")
#        self.urlopen = urllib2.urlopen
        if login and password:
            self.connect(login,password)

    def parse_option(self):
        """Gère les options en ligne de commande"""
        usage = "usage: %prog [options] arg"
        parser = OptionParser(usage)
        parser.add_option("-m", "--mode", dest="mode",
                          help=u"Choisir quel mode lancer(doublons,recherche)",
                          choices=("doublons","recherche","ephemere"))
        parser.add_option("-f", "--file", dest="filename",
                        help=u"Permet de charger un fichier de configuration")
        parser.add_option("-n", "--nb_page", dest="nb_page", type="int", \
                        help=u"Définit le nombre de pages vues")
        parser.add_option("-p", "--start_page", dest="start_page", type="int", \
                        default=1, help=u"Définit la première page")
        parser.add_option("-i", "--forum_id", dest="forum_id", type="int",
                        help = u"Définit l'id du forum")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", \
                        help = u"affiche des informations supplémentaires", default=False)
        (options, args) = parser.parse_args()
        if  not options.mode:
            parser.error("L'option mode est obligatoire")
        mode = options.mode
        if options.filename:
            print(u"fichier de configuration : "+options.filename)
        global verbose
        self.verbose = options.verbose
        if mode == "doublons":
            kwargs = {"nb_page":options.nb_page}
            self.doublons(**kwargs)
        elif mode == "ephemere":
            self.ephemere()
        elif mode == "recherche" and options.filename:
            forum_id = options.forum_id
            if os.path.exists(options.filename):
                config_ini = ConfigParser.SafeConfigParser()
                config_ini.readfp(open(options.filename))
                if config_ini.has_section('core'):
                    patterns, regexp = False, False
                    if config_ini.has_option('core','forum_id'):
                        value = config_ini.get('core','forum_id')
                        forum_id = value if value else forum_id
                    if config_ini.has_option("core","patterns"):
                        patterns = config_ini.get("core","patterns")
                        patterns = [item.strip() for item in\
                                            patterns.strip().split(",")]
                    if config_ini.has_option("core","regexp"):
                        regexp = config_ini.get("core","regexp")
                if not (patterns or regexp):
                    print("Vous devez spécifier des mots ou une expression à rechercher")
                    sys.exit(2)
                if not forum_id:
                    print("Vous devez specifier un forum id")
                    sys.exit(2)
                kwargs = {"nb_page":options.nb_page, "forum_id":forum_id,
                        "patterns":patterns, "regexp":regexp, "start_page":options.start_page}
                self.search_post(**kwargs)
            else:
                print("Le fichier n'existe pas")
                sys.exit(2)

    def debug(self, text):
        if self.verbose:
            print(text)


    def connect(self, login, password):
        """Connection au forum"""
        Request = urllib2.Request
        cj = cookielib.LWPCookieJar()
        if os.path.isfile(COOKIE_FILE):
            cj.load(COOKIE_FILE)
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        urllib2.install_opener(self.opener)
        url = "http://forum.ubuntu-fr.org/login.php?action=in"
        data = urllib.urlencode({'req_username':login, 'req_password':password,
            'form_sent': '1', 'redirect_url' :'http://forum.ubuntu-fr.org/index.php'})
        try:
            # création d'un objet request
            req = Request(url, data)
            # on l'ouvre pour renvoyer un handle sur l'url
            handle = urlopen(req)
        except IOError, e:
            print 'We failed to open "%s".' % url
            if hasattr(e, 'code'):
                print 'We failed with error code - %s.' % e.code
            elif hasattr(e, 'reason'):
                print "The error object has the following 'reason' attribute :"
                print e.reason
                print "This usually means the server doesn't exist"
                print "is down, or we don't have an internet connection."
            sys.exit()
        # save the cookies again
        cj.save(COOKIE_FILE)





    def get_page_max(self, url):
        """Pour obtenir le nombre de page dans un forum"""
        obj_page = urlopen(url)
        soup = BeautifulSoup.BeautifulSoup( obj_page )
        p_page = soup.findAll("p", attrs={'class' : re.compile("pagelink")})[0]
        url_pages = p_page.findAll("a")
        if url_pages:
            nb_page = url_pages[-1].contents[0].strip()
        else:
            nb_page = p_page.strong.string.strip()
      #  url = url_pages[-1]["href"].split("&p=")[0]
      #  url = "http://forum.ubuntu-fr.org/"  + url + "&p=%s"
      #  print(url)
        print(url+" (%s pages)" %  nb_page)
        return  int(nb_page)


    def get_topics(self, list_url):
        nb_page = len(list_url)
        for num_page, url in enumerate(list_url):
            num_page += 1
            obj_page = urlopen(url)
            soup = BeautifulSoup.BeautifulSoup( obj_page )
            name_zone  = soup.findAll("div",{"id":"vf"})[0].h2.span.string
            search_category = False
            if name_zone == u'Résultats de la recherche':
                search_category = True
            else:
                category = name_zone
                id_category = url.split('id=')[-1].split("&")[0]
            sys.stdout.write('\rObtention des pages ▕'+'█'*num_page+' '*(nb_page-num_page)\
                       +'▏ '+str(num_page)+'/'+str(nb_page))
            sys.stdout.flush()

            for item in soup.findAll("div","tclcon"):
                is_move = False
                if item.contents[0] and \
                    u"D&eacute;plac&eacute;" in  item.contents[0].strip():
                    is_move = True
                tr_parent = item.findParents("tr")[0]

                topic_id = item.a['href'].split("id=")[-1]
                titre = htmlentitydecode(item.a.string)
                auteur = item.span.contents[0].replace("par&nbsp;","")

                is_closed = False
                is_closed = tr_parent.get("class") == "iclosed"
                if not is_move:
                    balise_td = tr_parent.findAll("td", "tcr")[0]
                    date = balise_td.a.string
                    obj_date = transform_date(date)
                else:
                    obj_date = None
                if search_category:
                    td_category = tr_parent.findAll('td', 'tc2')[0]
                    category = td_category.a.string
                    id_category = td_category.a['href'].split('id=')[-1]


                yield {'id':topic_id, 'auteur':auteur, 'titre':titre,
                       'is_closed':is_closed, 'date_last':obj_date,
                       'is_move': is_move, 'id_category': id_category,
                       'category': category, 'num_page': num_page}
        print('')


    def ephemere(self):
        """Fonction permettant d'obtenir la liste des message ayant dépassé
        la durée de validité dans le forum ephemere"""
        forum_id = 8
        url = URL_FORUM % forum_id
        nb_page = self.get_page_max(url)
        url = url + "&p=%s"
        list_url = [url % item for item in range(1, 1 +nb_page)]
        topics = dict([(topic['id'],topic) for topic in self.get_topics(list_url)])
        now = datetime.now() + timedelta(5)
        import pprint
        pprint.pprint([item for item in topics.values() \
                        if item["date_last"] <= now ])



    def doublons(self, **kwargs):
        """Recherche les doublons dans les derniers messages du forum"""
        topics = {}
        topic_by_auteur = {}
        url = URL_24H
        nb_page = self.get_page_max(url)
        if not kwargs["nb_page"]:
            pass
        elif kwargs["nb_page"] < nb_page:
            nb_page = kwargs["nb_page"]
        else:
            print("Vous dépassez la limite du forum, \
    il y a %s pages sur ce forum" % nb_page)
        url = url + "&p=%s"
        list_url = [url % item for item in range(1, 1 + nb_page)]
        for topic in self.get_topics(list_url):
            if topic['category'] != 'Trash':
                topic_id = topic['id']
                auteur = topic['auteur']
                topics[topic_id] = topic
                topic_by_auteur.setdefault(auteur, [])
                topic_by_auteur[auteur].append(topic_id)

        auteur_many_topic = dict([(key, [ele for ele in value\
                                if not topics[ele]["is_closed"]]) \
                                for key, value in topic_by_auteur.items()\
                                    if len(value) >1 and \
                                       [ele for ele in value \
                                       if not topics[ele]["is_closed"]]\
                                ])

        matchs_by_auth = {}
        namespace  = {}
        for auteur, value in auteur_many_topic.items():
            value=set(value) #bug de double id si un sujet chage de page pendant la récup
            titles = dict([(id_top,topics[id_top]) for id_top in auteur_many_topic[auteur]])
            matchs_by_auth[auteur] = []
            for id_nbr, id_topic in enumerate(value):
                matchs={}
                title = titles.pop(id_topic)['titre']
                for id_top in titles:
                    if matchs_by_auth[auteur].count(id_topic) == 0:
                        match = difflib.get_close_matches(title,[titles[id_top]['titre']], cutoff=0.5)
                        if match:
                            matchs[id_top]=match[0]
                            matchs_by_auth[auteur].append(id_top)
                if matchs:
                    matchs[id_topic] = title
                    obj_page = urlopen(URL_TOPIC % id_topic)
                    soup = BeautifulSoup.BeautifulSoup( obj_page )
                    auteur_id = soup.findAll("div","postleft")[0].findAll("a")[0]["href"].split("id=")[-1]
                    self.debug('--------------\n'+auteur)
                    for title in matchs.iteritems():
                        self.debug(title[1])
                    namespace.setdefault('topics',[])
                    list_titre = [{'topic_id':key, 'titre': value} for key,value in matchs.items()]
                    namespace['topics'].append({"auteur_id":auteur_id, "auteur":auteur, "list_titre": list_titre,"topic_id": topic_id})

        html_page = self.affichage("doublons.txt",namespace)
        obj_file = open("doublons.html", "w")
        obj_file.write(html_page)
        obj_file.close()


    def search_post(self, **kwargs):
        """Recherche les topic dans un forum correspondant à une liste de
        mot clé"""
        nb_page = kwargs["nb_page"]
        if not nb_page:
            nb_page = 10
        start_page = kwargs["start_page"]
        forum_id = kwargs["forum_id"]
        if not kwargs["regexp"]:
            patterns = kwargs["patterns"]
            regexp = '|'.join(patterns)
        else:
            regexp = kwargs["regexp"]
        try:
            comp_regexp = re.compile(regexp, re.IGNORECASE)
            print("pattern recherché : "+str(regexp))
        except TypeError, e:
            print("l'expression rationelle définie est invalide : "+str(regexp))
        stop_page = start_page + nb_page
        if not forum_id:
            print("Vous devez specifier un forum id")
            sys.exit(2)
        url = URL_FORUM % forum_id
        nb_page_max = self.get_page_max(url)
        if start_page > nb_page_max:
            print("Vous dépassez la limite du forum, \
    il y a %s pages sur ce forum" % nb_page_max)
            sys.exit(2)
        elif stop_page > nb_page_max + 1:
            print("Vous dépassez la limite du forum, \
    la recherche s'arrêtera à la page %s" % nb_page_max)
            stop_page = nb_page_max + 1

        topics = {}
        pagenums = {}
        list_url = ["http://forum.ubuntu-fr.org/viewforum.php?id=%s&p=%s"\
                % (forum_id,num_page) for num_page in range(start_page, stop_page)]
        for topic in self.get_topics(list_url):
                if topic['is_move']:
                    continue
                if comp_regexp.search(topic['titre']):
                    topics[topic['id']] = topic
        namespace = {}
        namespace["forum_id"] = forum_id
        namespace['topics'] = []
        for topic_id, topic in topics.items():
            namespace['topics'].append({ "pagenums": topic['num_page'],"titre": topic['titre'],"topic_id": topic_id})
            namespace['topics'].sort(key=itemgetter('pagenums'))


        obj_file = open("log.html", "w")
        html_page = self.affichage("search.txt",namespace)
        obj_file.write(html_page)
        obj_file.close()

    def affichage(self, name_template, namespace):
        if not namespace:
            namespace['topics'] = []
        mytemplate = mylookup.get_template(name_template)
        return mytemplate.render(**namespace)

class Topic(dict):
    pass

if __name__ == "__main__":
    bot = BotForum()
    bot.parse_option()

