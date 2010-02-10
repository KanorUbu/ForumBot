#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import htmlentitydefs
import re

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
