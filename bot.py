#!/usr/bin/env python
#-*- coding: UTF-8 -*-
"""Programme offrant différentes options pour simplifier la modération
    d'un forum"""



import urllib
import ConfigParser
import ClientForm
import difflib
import mechanize as ClientCookie
from datetime import timedelta, datetime
try:
    import BeautifulSoup
except ImportError, e:
    print("Vous devez installer le module BeautifulSoup")
import re
import os
import sys
from optparse import OptionParser
from utils import htmlentitydecode, transform_date


URL_FORUM = "http://forum.ubuntu-fr.org/viewforum.php?id=%s"
URL_24H = "http://forum.ubuntu-fr.org/search.php?action=show_24h"
URL_TOPIC = "http://forum.ubuntu-fr.org/viewtopic.php?id=%s"

#class BotForum(object):
#    """Cette classe regroupe un ensemble d'outils permettant de simplifier
#    l'admistration d'un forum punbb"""

#    def __init__(self):
#        self.parse_option()
        #login = None
        #password = None
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

def parse_option():
    """Gère les options en ligne de commande"""
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-m", "--mode", dest="mode",
                      help=u"Choisir quel mode lancer(doublons,recherche)",
                      choices=("doublons","recherche","ephemere"))
    parser.add_option("-f", "--file", dest="filename",
                    help=u"Permet de charger un fichier de configuration")
    parser.add_option("-n", "--nb_page", dest="nb_page", type="int", \
                    default=10, help=u"Définit le nombre de pages vues")
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
    verbose=options.verbose
    if mode == "doublons":
        doublons()
    elif mode == "ephemere":
        ephemere()
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
            search_post(**kwargs)
        else:
            print("Le fichier n'existe pas")
            sys.exit(2)

def debug(text):
    if verbose:
        print(text)


def connect(login, password):
    """Connection au forum"""
    cookie_jar = ClientCookie.CookieJar()
    opener = ClientCookie.build_opener(\
            ClientCookie.HTTPCookieProcessor(cookie_jar))
    opener.addheaders = [("User-agent","Mozilla/5.0 (compatible)")]
    ClientCookie.install_opener(opener)
    form_page = ClientCookie.urlopen("http://forum.ubuntu-fr.org/login.php")
    forms = ClientForm.ParseResponse(form_page)
    form_page.close()
    form = forms[1]
    form["req_username"] = login
    form["req_password"] = password
    form_page = ClientCookie.urlopen(form.click())
    form_page.close()

def get_page_max(url):
    """Pour obtenir le nombre de page dans un forum"""
    obj_page = urllib.urlopen(url)
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




def ephemere():
    """Fonction permettant d'obtenir la liste des message ayant dépassé
    la durée de validité dans le forum ephemere"""
    forum_id = 8
    url = URL_FORUM % forum_id

    topics = {}
    nb_page = get_page_max(url)

    url = url + "&p=%s"

    for num_page in range(1, 1 + nb_page):
        url_tmp = url % num_page
        print(url_tmp)
        obj_page = urllib.urlopen(url_tmp)
        soup = BeautifulSoup.BeautifulSoup( obj_page )

        for item in soup.findAll("div","tclcon"):
            if item.contents[0] and \
                 u"D&eacute;plac&eacute;" in  item.contents[0].strip():
                continue
            tr_parent = item.findParents("tr")
            obj_date = None
            is_closed = None
            if  tr_parent:
                tr_parent = tr_parent[0]
                is_closed = tr_parent.get("class") == "iclosed"
                balise_td = tr_parent.findAll("td", "tcr")
                if balise_td:
                    date = balise_td[0].findAll("a")[0].string
                    obj_date = transform_date(date)
            lien  = item.findAll("a")[0]
            span = item.findAll("span")[0]
            auteur = span.contents[0].replace("par&nbsp;","")
            url_topic =  lien["href"]
            topic_id = url_topic.split("id=")[-1]
            titre = htmlentitydecode(lien.string)
            topics[topic_id] = {"id":topic_id, "auteur":auteur, "titre":titre,
            "url":url_topic, "is_closed":is_closed, "date_last":obj_date}
    import pprint
    now = datetime.now() + timedelta(5)
    pprint.pprint([item for item in topics.values() \
                    if item["date_last"] <= now ])



def doublons():
    """Recherche les doublons dans les derniers messages du forum"""
    topics = {}
    topic_by_auteur = {}
    url = URL_24H
    nb_page = get_page_max(url)
    url = url + "&p=%s"

    for num_page in range(1, 1 + nb_page):
        url_tmp = url % num_page
        print(url_tmp)
        obj_page = urllib.urlopen(url_tmp)
        soup = BeautifulSoup.BeautifulSoup( obj_page )

        for item in soup.findAll("div", "tclcon"):
            if item.contents[0] and \
                    u"D&eacute;plac&eacute;" in  item.contents[0].strip():
                continue
            tr_parent = item.findParents("tr", "iclosed")
            is_closed = bool(tr_parent)
            lien  = item.findAll("a")[0]
            span = item.findAll("span")[0]
            auteur = span.contents[0].replace("par&nbsp;", "")
            url_topic =  lien["href"]
            topic_id = url_topic.split("id=")[-1]
            titre = htmlentitydecode(lien.string)
            topics[topic_id] = {"id":topic_id, "auteur":auteur, "titre":titre, \
                            "url":url_topic, "is_closed":is_closed}
            topic_by_auteur.setdefault(auteur, [])
            topic_by_auteur[auteur].append(topic_id)

    auteur_many_topic = dict([(key, [ele for ele in value\
                            if not topics[ele]["is_closed"]]) \
                            for key, value in topic_by_auteur.items()\
                                if len(value) >1 and \
                                   [ele for ele in value \
                                   if not topics[ele]["is_closed"]]\
                            ])
    if False:
        for auteur, value in auteur_many_topic.items():
            for id_nbr, id_topic in enumerate(value):
                title = topics[id_topic]['titre']
                titles = [topics[topic_id]['titre'] for topic_id \
                       in auteur_many_topic[auteur]][id_nbr+1:]
                matchs = difflib.get_close_matches(title, titles, cutoff=0.5)
                if len(matchs) > 0:
                    print('--------------\n'+auteur)
                    print(title)
                    for titre in matchs:
                        print(titre)
    else:
        html_page = \
        u"""
        <!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN'i\
                'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
      <head>
      </head>
      <body >
    <form method="post" action="http://forum.ubuntu-fr.org/moderate.php?fid=%s">
        <table>
        <tr>
                <th><a href="http://forum.ubuntu-fr.org/userlist.php">auteur</a></th>
                <th><a href="http://forum.ubuntu-fr.org/search.php?action=show_24h">Sujets</a></th>
            </tr>"""

        for auteur, value in auteur_many_topic.items():
            for id_nbr, id_topic in enumerate(value):
                title = topics[id_topic]['titre']
                titles = [topics[topic_id]['titre'] for topic_id \
                       in auteur_many_topic[auteur]][id_nbr+1:]
                matchs = difflib.get_close_matches(title, titles, cutoff=0.5)
                if len(matchs) > 0:
                    obj_page = urllib.urlopen(URL_TOPIC % id_topic)
                    soup = BeautifulSoup.BeautifulSoup( obj_page )
                    auteur_id = soup.findAll("div","postleft")[0].findAll("a")[0]["href"].split("id=")[-1]
                    debug('--------------\n'+auteur)
                    debug(title)
                    html_page += """<tr>
                    <td><a href="http://forum.ubuntu-fr.org/profile.php?id=%(auteur_id)s">%(auteur)s</a></td><td><a href="http://forum.ubuntu-fr.org/search.php?action=show_user&user_id=%(auteur_id)s">(tous les messages)</a></td></tr>
                    <tr><td></td><td><a href="http://forum.ubuntu-fr.org/viewtopic.php?id=%(topic_id)s">%(titre)s</a> 
                    </td></tr>""" % {"auteur_id":auteur_id, "auteur":auteur, "titre": title,"topic_id": topic_id}
                    for titre in matchs:
                        debug(titre)
                        html_page += """<tr><td></td><td><a href="http://forum.ubuntu-fr.org/viewtopic.php?id=%(topic_id)s">%(titre)s</a></td>
          </tr>""" % {"titre": titre,"topic_id": topic_id}


        html_page  +=  """
        </table>
        </form>
        </body>
        </html>"""


        obj_file = open("doublons.html", "w")
        html_page = html_page.encode("utf-8")
        obj_file.write(html_page)
        obj_file.close()


def search_post(**kwargs):
    """Recherche les topic dans un forum correspondant à une liste de
    mot clé"""
    nb_page = kwargs["nb_page"]
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
    nb_page_max = get_page_max(url)
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
    for num_page in range(start_page, stop_page):
        url = " http://forum.ubuntu-fr.org/viewforum.php?id=%s&p=%s"\
                % (forum_id, num_page)
        print(url)
        obj_page = urllib.urlopen(url)
        soup = BeautifulSoup.BeautifulSoup( obj_page )
        for item in soup.findAll("div", "tclcon"):
            if item.contents[0] and  u"D&eacute;plac&eacute;" in \
                    item.contents[0].strip():
                continue
            lien  = item.findAll("a")[0]
            url = lien["href"]
            topic_id = url.split("id=")[-1]
            titre = htmlentitydecode( lien.string)
            debug(titre)
            if comp_regexp.search(titre):
                topics[topic_id] = titre
                pagenums[topic_id] = num_page
                #break

    html_page = \
    u"""
    <!DOCTYPE html PUBLIC '-//W3C//DTD XHTML 1.0 Strict//EN'i\
            'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd'>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
  <head>
  </head>
  <body >
<form method="post" action="http://forum.ubuntu-fr.org/moderate.php?fid=%s">
    <table>
    <tr>
            <th>Page</th>
            <th>Sujet</th>
            <th>Sélectionner</th>
        </tr>""" % (forum_id)

    for topic_id, titre in topics.items():
        html_page += """<tr>
        <td><a href="http://forum.ubuntu-fr.org/viewforum.php?id=%(forum_id)s&p=%(pagenums)s">%(pagenums)s</a></td>
        <td><a href="http://forum.ubuntu-fr.org/viewtopic.php?id=%(topic_id)s">%(titre)s</a></td>
        <td>
        <input type="checkbox" name="topics[%(topic_id)s]" value="1" checked />
        </td>
        </tr>""" % {"forum_id":forum_id, "pagenums": pagenums[topic_id], \
                       "titre": titre,"topic_id": topic_id}


    html_page  +=  """
    </table> <input type="submit" value="Deplacer" name="move_topics">&nbsp;&nbsp;<input type="submit" name="delete_topics" value="Supprimer" />&nbsp;&nbsp;<input type="submit" name="open" value="Ouvrir" />&nbsp;&nbsp;<input type="submit" name="close" value="Fermer" />
    </form>
    </body>
    </html>"""


    obj_file = open("log.html", "w")
    html_page = html_page.encode("utf-8")
    obj_file.write(html_page)
    obj_file.close()


if __name__ == "__main__":
    parse_option()

