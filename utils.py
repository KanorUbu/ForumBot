#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import htmlentitydefs
import re
from datetime import datetime,timedelta

def htmlentitydecode(s):
    """Decode les caractére 'html' """
    # First convert alpha entities (such as &eacute;)
    # (Inspired from [url]http://mail.python.org/pipermail/python-list/2007-June/443813.html[/url])
    def entity2char(m):
        entity = m.group(1)
        if entity in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[entity])
        return u" "  # Unknown entity: We replace with a space.
    expression = u'&(%s);' % u'|'.join(htmlentitydefs.name2codepoint)
    t = re.sub(expression, entity2char, s)


    # Then convert numerical entities (such as &#38;#233;)
    t = re.sub(u'&#38;#(d+);', lambda x: unichr(int(x.group(1))), t)

    # Then convert hexa entities (such as &#38;#x00E9;)
    return re.sub(u'&#38;#x(w+);', lambda x: unichr(int(x.group(1),16)), t)

def transform_date(str_date):
    str_date = str_date.strip()
    date_obj = None
    if str_date.find("Aujourd'hui") != -1:
        date_obj = datetime.now()
        str_date = str_date.replace("Aujourd'hui","").strip()
    if str_date.find("Hier") != -1:
        date_obj = datetime.now()
        date_obj = date_obj - timedelta(1)
        str_date = str_date.replace("Hier","").strip()
    if date_obj:
        str_date = str_date.replace(u"\xe0","")
        hour,minute = (int(item) for item in str_date.strip().split(":") )
        date_obj.replace(hour=hour,minute=minute)
    if str_date.startswith("Le"):
        str_date = str_date.replace("Le","").strip()
        date,heure = str_date.split(",")
        heure = heure.replace(u"\xe0","").strip()
        day,month,year = (int(item) for item in date.split("/"))
        hour,minute = (int(item) for item in heure.split(":"))
        date_obj = datetime(year,month,day,hour,minute)
    return date_obj


