import os
from lxml import etree

class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable

class Convert(object):
    def __init__(self):
        pass
        
    def toHtmllgr(text):
        xsl_path = os.path.join(os.path.dirname(__file__), '..',  'xsl', 'kura2htmllgr.xsl')
        xslt_doc = etree.parse(xsl_path)
        transform = etree.XSLT(xslt_doc)
        document = etree.parse(text)
        result = transfrom(doc)
        result = unicode(result,  'utf-8')
        return result
        
    def toTextwolines(text):
        xsl_path = os.path.join(os.path.dirname(__file__), '..', 'xsl', 'kura2textwolines.xsl')
        xslt_doc = etree.parse(xsl_path)
        transform = etree.XSLT(xslt_doc)
        document = etree.parse(text)
        result = transfrom(doc)
        result = unicode(result,  'utf-8')
        return result

    toHtmllgr = Callable(toHtmllgr)
    toTextwolines = Callable(toTextwolines)
 
