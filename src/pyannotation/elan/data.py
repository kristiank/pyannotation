# -*- coding: utf-8 -*-
# (C) 2011 copyright by Peter Bouda
"""This module contains classes to access Elan data.

The class Eaf is a low level API to .eaf files.

EafGlossTree, EafPosTree, etc. are the classes to access the data via 
tree, which also contains the original .eaf IDs. Because of this
EafTrees are read-/writeable. 

"""

import os, glob, re
import pyannotation.data

from copy import deepcopy

from lxml import etree as ET
from lxml.etree import Element
from xml.parsers import expat


############################################# Builders

class EafAnnotationFileObject(pyannotation.data.AnnotationFileObject):

    def __init__(self, filepath):
        pyannotation.data.AnnotationFileObject.__init__(self, filepath)
        self.setFilepath(filepath)

    def getFile(self):
        return self.file

    def getFilepath(self):
        return self.filepath

    def setFilepath(self, filepath):
        self.filepath = filepath
        self.file = Eaf(self.filepath)

    def createTierHandler(self):
        if self.tierHandler == None:
            self.tierHandler = EafAnnotationFileTierHandler(self)
        return self.tierHandler

    def createParser(self):
        if self.parser == None:
            self.parser = EafAnnotationFileParser(self, self.createTierHandler())
        return self.parser

    def createParserWords(self):
        if self.parser == None:
            self.parser = EafAnnotationFileParserWords(self, self.createTierHandler())
        return self.parser

    def createParserPos(self):
        if self.parser == None:
            self.parser = EafAnnotationFileParserPos(self, self.createTierHandler())
        return self.parser


class EafFromToolboxAnnotationFileObject(pyannotation.data.AnnotationFileObject):

    def __init__(self, filepath):
        pyannotation.data.AnnotationFileObject.__init__(self, filepath)
        self.setFilepath(filepath)

    def getFile(self):
        return self.file

    def getFilepath(self):
        return self.filepath

    def setFilepath(self, filepath):
        self.filepath = filepath
        self.file = EafPythonic(self.filepath)

    def createTierHandler(self):
        if self.tierHandler == None:
            self.tierHandler = EafAnnotationFileTierHandler(self)
            self.tierHandler.setUtterancetierType("tx")
            self.tierHandler.setWordtierType("mo")
            self.tierHandler.setMorphemetierType("mo")
            self.tierHandler.setGlosstierType("gl")
            self.tierHandler.setTranslationtierType(["ft", "ot"])
        return self.tierHandler

    def createParser(self):
        if self.parser == None:
            self.parser = EafFromToolboxAnnotationFileParser(self, self.createTierHandler())
        return self.parser


class EafAnnotationFileTierHandler(pyannotation.data.AnnotationFileTierHandler):

    def __init__(self, annotationFileObject):
        pyannotation.data.AnnotationFileTierHandler.__init__(self, annotationFileObject)
        self.eaf = annotationFileObject.getFile()
        self.UTTERANCETIER_TYPEREFS = [ "utterance", "utterances", u"Äußerung", u"Äußerungen" ]
        self.WORDTIER_TYPEREFS = [ "words", "word", "Wort", "Worte", u"Wörter" ]
        self.MORPHEMETIER_TYPEREFS = [ "morpheme", "morphemes",  "Morphem", "Morpheme" ]
        self.GLOSSTIER_TYPEREFS = [ "glosses", "gloss", "Glossen", "Gloss", "Glosse" ]
        self.POSTIER_TYPEREFS = [ "part of speech", "parts of speech", "Wortart", "Wortarten" ]
        self.TRANSLATIONTIER_TYPEREFS = [ "translation", "translations", u"Übersetzung",  u"Übersetzungen" ]

    def setUtterancetierType(self, type):
        if isinstance(type, list):
            self.UTTERANCETIER_TYPEREFS = type
        else:
            self.UTTERANCETIER_TYPEREFS = [type]

    def setWordtierType(self, type):
        if isinstance(type, list):
            self.WORDTIER_TYPEREFS = type
        else:
            self.WORDTIER_TYPEREFS = [type]

    def setMorphemetierType(self, type):
        if isinstance(type, list):
            self.MORPHEMETIER_TYPEREFS = type
        else:
            self.MORPHEMETIER_TYPEREFS = [type]

    def setGlosstierType(self, type):
        if isinstance(type, list):
            self.GLOSSTIER_TYPEREFS = type
        else:
            self.GLOSSTIER_TYPEREFS = [type]

    def setPostierType(self, type):
        if isinstance(type, list):
            self.POSTIER_TYPEREFS = type
        else:
            self.POSTIER_TYPEREFS = [type]

    def setTranslationtierType(self, type):
        if isinstance(type, list):
            self.TRANSLATIONTIER_TYPEREFS = type
        else:
            self.TRANSLATIONTIER_TYPEREFS = [type]

    def getUtterancetierIds(self, parent = None):
        ret = []
        for type in self.UTTERANCETIER_TYPEREFS:
            ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
        return ret

    def getWordtierIds(self, parent = None):
        ret = []
        for type in self.WORDTIER_TYPEREFS:
            ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
        return ret

    def getMorphemetierIds(self, parent = None):
        ret = []
        for type in self.MORPHEMETIER_TYPEREFS:
            ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
        return ret

    def getGlosstierIds(self, parent = None):
        ret = []
        for type in self.GLOSSTIER_TYPEREFS:
            ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
        return ret

    def getPostierIds(self, parent = None):
        ret = []
        for type in self.POSTIER_TYPEREFS:
            ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
        return ret

    def getTranslationtierIds(self, parent = None):
        ret = []
        for type in self.TRANSLATIONTIER_TYPEREFS:
            ret.extend(self.eaf.getTierIdsForLinguisticType(type, parent))
        return ret

    def addTier(self, tierId, tierType, tierTypeConstraint, parentTier, tierDefaultLocale, tierParticipant):
        self.eaf.addTier(tierId, tierType, parentTier, tierDefaultLocale, tierParticipant)
        if not self.eaf.hasLinguisticType(tierType):
            self.eaf.addLinguisticType(tierType, tierTypeConstraint)

    def getLocaleForTier(self, idTier):
        return self.eaf.getLocaleForTier(idTier)

    def getParticipantForTier(self, idTier):
        return self.eaf.getParticipantForTier(idTier)


class EafAnnotationFileParser(pyannotation.data.AnnotationFileParser):

    def __init__(self, annotationFileObject, annotationFileTiers):
        pyannotation.data.AnnotationFileParser.__init__(self, annotationFileObject, annotationFileTiers)
        self.tierBuilder = annotationFileTiers
        self.eaf = annotationFileObject.getFile()
        self.lastUsedAnnotationId = self.eaf.getLastUsedAnnotationId()
        self.emptyIlElement = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

    def setFile(self, file):
        self.file = file

    def getNextAnnotationId(self):
        self.lastUsedAnnotationId = self.lastUsedAnnotationId + 1
        return self.lastUsedAnnotationId

    def parse(self):
        tree = []
        self.utteranceTierIds = self.tierBuilder.getUtterancetierIds()
        if self.utteranceTierIds != []:
            for uTier in self.utteranceTierIds:
                utterancesIds = self.eaf.getAlignableAnnotationIdsForTier(uTier) + self.eaf.getRefAnnotationIdsForTier(uTier)
                for uId in utterancesIds:
                    utterance = self.eaf.getAnnotationValueForAnnotation(uTier, uId)
                    translations = []
                    ilElements = []
                    locale = self.eaf.getLocaleForTier(uTier)
                    participant = self.eaf.getParticipantForTier(uTier)
                    translationTierIds = self.tierBuilder.getTranslationtierIds(uTier)
                    for tTier in translationTierIds:
                        transIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(uId, uTier, tTier)
                        for transId in transIds:
                            trans = self.eaf.getAnnotationValueForAnnotation(tTier, transId)
                            if trans != '':
                                translations.append([transId, trans])
                    wordTierIds = self.tierBuilder.getWordtierIds(uTier)
                    for wTier in wordTierIds:
                        wordsIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(uId, uTier, wTier)
                        for wordId in wordsIds:
                            ilElements.append(self.getIlElementForWordId(wordId, wTier))
                        if len(ilElements) == 0:
                            ilElements = self.emptyIlElement
                    tree.append([ uId,  utterance,  ilElements, translations, locale, participant, uTier ])
        else: # if self.utterancesTiers != []
            for wTier in self.tierBuilder.getWordtierIds():
                translations = []
                locale = self.eaf.getLocaleForTier(wTier)
                participant = self.eaf.getParticipantForTier(wTier)
                wordsIds = self.eaf.getAnnotationIdsForTier(wTier)
                for wordId in wordsIds:
                    ilElements.append(self.getIlElementForWordId(wordId, wTier))   
                if len(ilElements) == 0:
                    ilElements = self.emptyIlElement
                tree.append([ '',  '',  ilElements, translations, locale, participant, '' ])
        return tree

    def getIlElementForWordId(self, id, wTier):
        ilElement = []
        word = self.eaf.getAnnotationValueForAnnotation(wTier, id)
        ilElement.append(id)
        ilElement.append(word)
        morphElements = []
        morphemeTierIds = self.tierBuilder.getMorphemetierIds(wTier)
        for mTier in morphemeTierIds:
            morphIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(id, wTier, mTier)
            for morphId in morphIds:
                morphElements.append(self.getFuncElementForMorphemeId(morphId, mTier))
        if len(morphElements) == 0:
            ilElement.append([[ '',  '',  [ ['',  ''] ]]])
        else:
            ilElement.append(morphElements)
        return ilElement

    def getFuncElementForMorphemeId(self, morphId, mTier):
        ilElement = []
        morpheme = self.eaf.getAnnotationValueForAnnotation(mTier, morphId)
        morpheme = re.sub(r'^-', '', morpheme)
        morpheme = re.sub(r'-$', '', morpheme)
        ilElement.append(morphId)
        ilElement.append(morpheme)
        funcElements = []
        glossTierIds = self.tierBuilder.getGlosstierIds(mTier)
        for gTier in glossTierIds:
            funcIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(morphId, mTier, gTier)
            for funcId in funcIds:
                function = self.eaf.getAnnotationValueForAnnotation(gTier, funcId)
                function = re.sub(r'^-', '', function)
                morpheme = re.sub(r'-$', '', function)
                e = [funcId, function]
                funcElements.append(e)
        if len(funcElements) == 0:
            ilElement.append([['',  '']])
        else:
            ilElement.append(funcElements)
        return ilElement

    def removeAnnotationWithId(self, idAnnotation):
        self.eaf.removeAnnotationWithId(idAnnotation)

    def removeAnnotationsWithRef(self, idRefAnn):
        self.eaf.removeAnnotationsWithRef(idRefAnn)

    def updatePrevAnnotationForAnnotation(self, idAnnotation, idPrevAnn = None):
        self.eaf.updatePrevAnnotationForAnnotation(idAnnotation, idPrevAnn)

    def getAsEafXml(self, tree, tierUtterances, tierWords, tierMorphemes, tierGlosses, tierTranslations):
        # make local copy of eaf
        eaf2 = deepcopy(self.eaf)
        utterances = [[u[0], u[1]] for u in tree if u[6] == tierUtterances]
        translations = [[u[3], u[0]] for u in tree if u[6] == tierUtterances and len(u[3])>=1]
        words = [[w[0], w[1]] for u in tree if u[6] == tierUtterances for w in u[2]]
        ilelements = [u[2] for u in tree if u[6] == tierUtterances]
        # save utterances
        for u in utterances:
            eaf2.setAnnotationValueForAnnotation(tierUtterances, u[0], u[1])
        # save translations
        for t1 in translations:
            for t in t1[0]:
                if t[1] != "":
                    if not eaf2.setAnnotationValueForAnnotation(tierTranslations, t[0], t[1]):
                        eaf2.appendRefAnnotationToTier(tierTranslations, t[0], t[1], t1[1])
        # save words
        for w in words:
            eaf2.setAnnotationValueForAnnotation(tierWords, w[0], w[1])
        #save morphemes
        eaf2.removeAllAnnotationsFromTier(tierMorphemes)
        eaf2.removeAllAnnotationsFromTier(tierGlosses)
        for i in ilelements:
            for w in i:
                if len(w) >= 3:
                    refAnnMorph = w[0]
                    prevAnnMorph = None
                    for m in w[2]:
                        if len(m) >= 3:
                            if m[0] != "" and m[1] != "" and refAnnMorph != "":
                                eaf2.appendRefAnnotationToTier(tierMorphemes, m[0], m[1], refAnnMorph, prevAnnMorph)
                            prevAnnMorph = m[0]
                            refAnnGloss = m[0]
                            prevAnnGloss = None
                            for g in m[2]:
                                if len(g) >= 2:
                                    if g[0] != "" and g[1] != "" and refAnnGloss != "":
                                        eaf2.appendRefAnnotationToTier(tierGlosses, g[0], g[1], refAnnGloss, prevAnnGloss)
                                    prevAnnGloss = g[0]
        return eaf2.tostring()


class EafAnnotationFileParserPos(EafAnnotationFileParser):

    def __init__(self, annotationFileObject, annotationFileTiers):
        pyannotation.data.AnnotationFileParser.__init__(self, annotationFileObject, annotationFileTiers)
#        EafTree.__init__(self, annotationFileObject, annotationFileTiers)
        self.tierBuilder = annotationFileTiers
        self.eaf = annotationFileObject.getFile()
        self.lastUsedAnnotationId = self.eaf.getLastUsedAnnotationId()
        self.emptyIlElement = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

    def getIlElementForWordId(self, id, wTier):
        ilElement = []
        word = self.eaf.getAnnotationValueForAnnotation(wTier, id)
        ilElement.append(id)
        ilElement.append(word)
        posElements = []
        posTierIds = self.tierBuilder.getPostierIds(wTier)
        for pTier in posTierIds:
            posIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(id, wTier, pTier)
            for posId in posIds:
                pos = self.eaf.getAnnotationValueForAnnotation(pTier, posId)
                posElements.append((posId, pos))
        ilElement.append(posElements)
        return ilElement
    

class EafAnnotationFileParserWords(EafAnnotationFileParser):

    def __init__(self, annotationFileObject, annotationFileTiers):
        pyannotation.data.AnnotationFileParser.__init__(self, annotationFileObject, annotationFileTiers)
#        EafTree.__init__(self, annotationFileObject, annotationFileTiers)
        self.tierBuilder = annotationFileTiers
        self.eaf = annotationFileObject.getFile()
        self.lastUsedAnnotationId = self.eaf.getLastUsedAnnotationId()
        self.emptyIlElement = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

    def getIlElementForWordId(self, id, wTier):
        ilElement = []
        word = self.eaf.getAnnotationValueForAnnotation(wTier, wordId)
        ilElement = [wordId, word]
        return ilElement


class EafFromToolboxAnnotationFileParser(pyannotation.data.AnnotationFileParser):

    def __init__(self, annotationFileObject, annotationFileTiers):
        pyannotation.data.AnnotationFileParser.__init__(self, annotationFileObject, annotationFileTiers, wordSep = r"[ \n\t\r]+", morphemeSep = r"[-]", glossSep = r"[:]")
        self.tierBuilder = annotationFileTiers
        self.eaf = annotationFileObject.getFile()
        self.lastUsedAnnotationId = self.eaf.getLastUsedAnnotationId()
        self.emptyIlElement = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

    def setFile(self, file):
        self.file = file

    def getNextAnnotationId(self):
        self.lastUsedAnnotationId = self.lastUsedAnnotationId + 1
        return self.lastUsedAnnotationId

    def parse(self):
        tree = []
        self.utteranceTierIds = self.tierBuilder.getUtterancetierIds()
        for uTier in self.utteranceTierIds:
            utterancesIds = self.eaf.getAlignableAnnotationIdsForTier(uTier) + self.eaf.getRefAnnotationIdsForTier(uTier)
            for uId in utterancesIds:
                utterance = self.eaf.getAnnotationValueForAnnotation(uTier, uId)
                utterance = re.sub(r" +", " ", utterance)

                refId = self.eaf.getRefAnnotationIdForAnnotationId(uTier, uId)
                toolboxId = self.eaf.getAnnotationValueForAnnotation("ref", refId)

                translations = []
                ilElements = []
                locale = self.eaf.getLocaleForTier(uTier)
                participant = self.eaf.getParticipantForTier(uTier)
                translationTierIds = self.tierBuilder.getTranslationtierIds("ref")
                for tTier in translationTierIds:
                    transIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(refId, "ref", tTier)
                    for transId in transIds:
                        trans = self.eaf.getAnnotationValueForAnnotation(tTier, transId)
                        if trans != '':
                            translations.append([transId, trans])
                
                arrTextWords = re.split(self.WORD_BOUNDARY_PARSE, utterance)
                arrTextWords = filter(lambda i: i != '', arrTextWords)
                
                arrMorphWords = []
                arrGlossWords = []
                wordTierIds = self.tierBuilder.getWordtierIds("ref")
                for wTier in wordTierIds:
                    wordsIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(refId, "ref", wTier)
                    for wordId in wordsIds:
                        word = self.eaf.getAnnotationValueForAnnotation(wTier, wordId)
                        arrMorphWords.append(word)
                        glossTierIds = self.tierBuilder.getGlosstierIds(wTier)
                        for gTier in glossTierIds:
                            glossIds = self.eaf.getSubAnnotationIdsForAnnotationInTier(wordId, wTier, gTier)
                            for glossId in glossIds:
                                gloss = self.eaf.getAnnotationValueForAnnotation(gTier, glossId)
                                arrGlossWords.append(gloss)

                for i,word in enumerate(arrTextWords):
                    morphemes = ""
                    glosses = ""
                    if i < len(arrMorphWords):
                        morphemes = arrMorphWords[i]
                    if i < len(arrGlossWords):
                        glosses = arrGlossWords[i]
                    ilElement = self.ilElementForString("%s %s %s" % (word, morphemes, glosses))
                    
                    ilElements.append(ilElement)
                if len(ilElements) == 0:
                    ilElements = [ ['', '',  [ ['', '',  [ ['',  ''] ] ] ] ] ]

                tree.append([ toolboxId,  utterance,  ilElements, translations, locale, participant, uTier ])
        return tree

####################################### Files

class Eaf(object):

    def __init__(self, file):
        self.tree = ET.parse(file)

    def tostring(self):
        return ET.tostring(self.tree.getroot(), pretty_print=True, encoding="utf-8")

    def tiers(self):
        # returns tiers as dictionary: id -> type
        ret = {}
        for tier in self.tree.findall('TIER'):
            ret[tier.attrib['TIER_ID']] = tier.attrib['LINGUISTIC_TYPE_REF']
        return ret
        
    def childTiersFor(self,  id):
        ret = {}
        childTiers = self.tree.findall("TIER[@PARENT_REF='%s']" % id)
        for tier in childTiers:
            child_id = tier.attrib['TIER_ID']
            if child_id not in ret.keys():
                ret2 = self.childTiersFor(child_id)
                for k,  v in ret2.items():
                    ret[k] = v
            ret[child_id] = tier.attrib['LINGUISTIC_TYPE_REF']
        return ret

    def getIndexOfTier(self, id):
        ret = None
        i = 0
        for node in self.tree.getroot():
            if node.tag == 'TIER' and 'TIER_ID' in node.attrib and node.attrib['TIER_ID'] == id:
                ret = i
            i = i + 1
        return ret

    def getIndexOfLastTier(self):
        ret = None
        i = 0
        for node in self.tree.getroot():
            if node.tag == 'TIER':
                ret = i
            i = i + 1
        if ret == None:
            ret = i
        return ret

    def getLastUsedAnnotationId(self):
        strId = self.tree.findtext("HEADER/PROPERTY[@NAME='lastUsedAnnotationId']")
        lastId = 0
        if strId != None:
            lastId = int(strId)
        else:
            annotations = self.tree.findall("TIER/ANNOTATION/ALIGNABLE_ANNOTATION")
            for a in annotations:
                i = a.attrib['ANNOTATION_ID']
                i = int(re.sub(r"\D", "", i))
                if i > lastId:
                    lastId = i
            annotations = self.tree.findall("TIER/ANNOTATION/REF_ANNOTATION")
            for a in annotations:
                i = a.attrib['ANNOTATION_ID']
                i = int(re.sub(r"\D", "", i))
                if i > lastId:
                    lastId = i
        return lastId

    def setLastUsedAnnotationId(self, newAnnotationId):
        """sets the header property last used annotation id"""
        a = self.tree.find("HEADER/PROPERTY[@NAME='lastUsedAnnotationId']")
        a.text = str(newAnnotationId)

    def getTierIdsForLinguisticType(self, type, parent = None):
        ret = []
        if parent == None:
            tiers = self.tree.findall("TIER[@LINGUISTIC_TYPE_REF='%s']" % type) #.decode('utf-8')
        else:
            tiers = self.tree.findall("TIER[@LINGUISTIC_TYPE_REF='%s'][@PARENT_REF='%s']" % (type, parent)) #.decode('utf-8')
        for tier in tiers:
            ret.append(tier.attrib['TIER_ID'])
        return ret

    def getParameterDictForTier(self, id):
        tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
        return tier.attrib
        
    def getParameterDictForLinguisticType(self, id):
        tier = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % id)
        return tier.attrib

    def getLinguisticTypeForTier(self, id):
        tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
        if 'LINGUISTIC_TYPE_REF' in tier.attrib:
            return tier.attrib['LINGUISTIC_TYPE_REF']
        return None
        
    def getConstraintForLinguisticType(self, id):
        tier = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % id)
        if 'CONSTRAINTS' in tier.attrib:
            return tier.attrib['CONSTRAINTS']
        return None
        
    def linguisticTypeIsTimeAlignable(self, id):
        tier = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % id)
        if 'TIME_ALIGNABLE' in tier.attrib:
            if tier.attrib['TIME_ALIGNABLE'] == 'true':
                return True
            else:
                return False
        return None

    def getIndexOfLastLinguisticType(self):
        ret = None
        i = 0
        for node in self.tree.getroot():
            if node.tag == 'LINGUISTIC_TYPE':
                ret = i
            i = i + 1
        if ret == None:
            ret = i
        return ret

    def getLocaleForTier(self, id):
        locale = ''
        tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
        if 'DEFAULT_LOCALE' in tier.attrib:
            locale = tier.attrib['DEFAULT_LOCALE']
            if locale == None:
                locale = ''
        return locale
        
    def getParticipantForTier(self, id):
        participant = ''
        tier = self.tree.find("TIER[@TIER_ID='%s']" % id)
        if 'PARTICIPANT' in tier.attrib:
            participant = tier.attrib['PARTICIPANT']
            if participant == None:
                participant = ''
        participant = participant
        return participant

    def addLinguisticType(self, type, constraints, timeAlignable = False, graphicReferences = False, extRef = None):
        newtype = Element("LINGUISTIC_TYPE")
        newtype.attrib['LINGUISTIC_TYPE_ID'] = type
        newtype.attrib['CONSTRAINTS'] = constraints
        if timeAlignable:
            newtype.attrib['TIME_ALIGNABLE'] = 'true'
        else:
            newtype.attrib['TIME_ALIGNABLE'] = 'false'
        if graphicReferences:
            newtype.attrib['GRAPHIC_REFERENCES'] = 'true'
        else:
            newtype.attrib['GRAPHIC_REFERENCES'] = 'false'
        if extRef != None:
            newtype.attrib['EXT_REF'] = extRef
        newIndex = self.getIndexOfLastLinguisticType()
        self.tree.getroot().insert(newIndex, newtype)

    def hasLinguisticType(self, type):
        node = self.tree.find("LINGUISTIC_TYPE[@LINGUISTIC_TYPE_ID='%s']" % type)
        if node == None:
            return False
        else:
            return True

    def addTier(self,  id,  type,  parent = None, defaultLocale = None,  participant = ''):
        newtier = Element("TIER")
        newtier.attrib['TIER_ID'] = id
        newtier.attrib['LINGUISTIC_TYPE_REF'] = type
        if parent != None:
            newtier.attrib['PARENT_REF'] = parent
        if defaultLocale != None:
            newtier.attrib['DEFAULT_LOCALE'] = defaultLocale
        newtier.attrib['PARTICIPANT'] = participant
        newIndex = self.getIndexOfLastTier()
        if parent != None:
            i = self.getIndexOfTier(parent)
            if i != None:
                newIndex = i
        self.tree.getroot().insert(newIndex, newtier)                

    def getStartTsForAnnotation(self,  idTier,  idAnnotation):
        a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
        ret = a.attrib['TIME_SLOT_REF1']
        return ret

    def getEndTsForAnnotation(self,  idTier,  idAnnotation):
        a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
        ret = a.attrib['TIME_SLOT_REF2']
        return ret

    def getSubAnnotationIdsForAnnotationInTier(self, idAnn, idTier, idSubTier):
        type = self.getLinguisticTypeForTier(idSubTier)
        ret = []
        if self.linguisticTypeIsTimeAlignable(type):
            startTs = self.getStartTsForAnnotation(idTier, idAnn)
            endTs = self.getEndTsForAnnotation(idTier, idAnn)
            ret = self.getAlignableAnnotationIdsForTier(idSubTier, startTs, endTs)
        else:
            ret = self.getRefAnnotationIdsForTier(idSubTier, idAnn)
        return ret

    def getAnnotationIdsForTier(self, idTier):
        type = self.getLinguisticTypeForTier(idTier)
        ret = []
        if self.linguisticTypeIsTimeAlignable(type):
            ret = self.getAlignableAnnotationIdsForTier(idtier)
        else:
            ret = self.getRefAnnotationIdsForTier(idTier)
        return ret

    def getRefAnnotationIdForAnnotationId(self, idTier, idAnnotation):
        a = self.tree.find( "TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier, idAnnotation) )
        if a is not None:
            return a.attrib["ANNOTATION_REF"]
        else:
            return None
        
    def getRefAnnotationIdsForTier(self, idTier, annRef = None,  prevAnn = None):
        ret = []
        foundann = []
        prevs = {}
        if annRef == None:
            allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION" % idTier)
            for a in allAnnotations:
                ret.append(a.attrib['ANNOTATION_ID'])
        else:
            if prevAnn == None:
                allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % (idTier, annRef))
            else:
                allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s'][@PREVIOUS_ANNOTATION='%s']" % (idTier, annRef, prevAnn))
            for a in allAnnotations:
                if prevAnn == None and 'PREVIOUS_ANNOTATION' in a.attrib:
                    continue
                ret.append(a.attrib['ANNOTATION_ID'])
                foundann.append(a.attrib['ANNOTATION_ID'])
            for id in foundann:
                ret.extend(self.getRefAnnotationIdsForTier(idTier, annRef,  id))
        return ret

    def appendRefAnnotationToTier(self, idTier, idAnnotation, strAnnotation, annRef, prevAnn = None):
        t = self.tree.find("TIER[@TIER_ID='%s']" % idTier)
        if t == None:
            return False
        eAnnotation = Element("ANNOTATION")
        if prevAnn == None:
            eRefAnn = ET.SubElement(eAnnotation, "REF_ANNOTATION", ANNOTATION_ID=idAnnotation, ANNOTATION_REF=annRef)
        else:
            eRefAnn = ET.SubElement(eAnnotation, "REF_ANNOTATION", ANNOTATION_ID=idAnnotation, ANNOTATION_REF=annRef, PREVIOUS_ANNOTATION=prevAnn)
        eAnnVal = ET.SubElement(eRefAnn, "ANNOTATION_VALUE")
        eAnnVal.text = strAnnotation
        t.append(eAnnotation)
        return True

    def getAlignableAnnotationIdsForTier(self, id, startTs = None,  endTs = None):
        ret = []
        ts = {}
        if startTs != None and endTs != None:
            iStartTs = int(re.sub(r"\D", '', startTs))
            iEndTs = int(re.sub(r"\D", '', endTs))
        allAnnotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION" % id)
        for a in allAnnotations:
            aStartTs = a.attrib['TIME_SLOT_REF1']
            aEndTs = a.attrib['TIME_SLOT_REF2']
            iAStartTs = int(re.sub(r"\D", '', aStartTs))
            iAEndTs = int(re.sub(r"\D", '', aEndTs))
            if startTs != None and endTs != None:
                if iStartTs > iAStartTs or iEndTs < iAEndTs:
                    continue
            id = None
            v = []
            id = a.attrib['ANNOTATION_ID']
            if id:
                ts[id] = iAStartTs
        # sort ids via start timestamp
        alist = sorted(ts.iteritems(), key=lambda (k,v): (v,k))
        for k, v in alist:
            ret.append(k)
        return ret

    def removeAllAnnotationsFromTier(self, idTier):
        t = self.tree.find("TIER[@TIER_ID='%s']" % idTier)
        annotations = self.tree.findall("TIER[@TIER_ID='%s']/ANNOTATION" % idTier)
        if t == None or annotations == None:
            return False
        for a in annotations:
            t.remove(a)
        return True

    def removeAnnotationWithId(self, idAnnotation):
        a = self.tree.find("TIER/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % idAnnotation)
        if a != None:
            a.getparent().getparent().remove(a.getparent())
        else:
            a = self.tree.find("TIER/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % idAnnotation)
            if a != None:
                a.getparent().getparent().remove(a.getparent())

    def removeAnnotationsWithRef(self, idRefAnn):
        allAnnotations = self.tree.findall("TIER/ANNOTATION/REF_ANNOTATION[@ANNOTATION_REF='%s']" % idRefAnn)
        for a in allAnnotations:
            a.getparent().getparent().remove(a.getparent())

    def getAnnotationValueForAnnotation(self, idTier, idAnnotation):
        type = self.getLinguisticTypeForTier(idTier)
        ret = ''
        if self.linguisticTypeIsTimeAlignable(type):
            a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
            ret = a.findtext('ANNOTATION_VALUE')
        else:
            a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier,  idAnnotation))
            ret = a.findtext('ANNOTATION_VALUE')
        if ret == None:
            ret = ''
        return ret

    def setAnnotationValueForAnnotation(self, idTier, idAnnotation, strAnnotation):
        type = self.getLinguisticTypeForTier(idTier)
        ret = ''
        a = None
        if self.linguisticTypeIsTimeAlignable(type):
            a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % (idTier,  idAnnotation))
        else:
            a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']/ANNOTATION_VALUE" % (idTier,  idAnnotation))
        if a == None:
            return False
        a.text = strAnnotation
        return True

    def getLastUsedTimeSlotId(self):
        lastId = 0
        timeslots = self.tree.findall("TIME_ORDER/TIME_SLOT")
        for ts in timeslots:
            i = ts.attrib['TIME_SLOT_ID']
            i = int(re.sub(r"\D", "", i))
            if i > lastId:
                lastId = i
        return lastId

    def addTimeOrder(self):
        times = self.tree.find("TIME_ORDER")
        if times is None:
            times = ET.SubElement(self.tree.getroot(), "TIME_ORDER")
        return times

    def getTimeOrderTree(self):
        return self.addTimeOrder()

    def addTimeSlot(self, tsId, tsStartMs, tsEndMs=None):
        times = self.getTimeOrderTree()
        if tsId is None:
            tsId = self.getLastUsedTimeSlotId() + 1
        newtimeslot = ET.SubElement(times,
                                    "TIME_SLOT",
                                    TIME_SLOT_ID = str(tsId),
                                    TIME_VALUE = str(tsStartMs))
        if tsEndMs is None:
            return tsId
        else:
            return (tsId, addTimeSlot(None, tsEndMs))

    def setTsForAnnotation(self, idTier, idAnnotation, idTimeSlotStart, idTimeSlotEnd=None):
        times = self.getTimeOrderTree()
        if not self.linguisticTypeIsTimeAlignable(self.getLinguisticTypeForTier(idTier)):
            return False
        a = self.tree.find("TIER[@TIER_ID='%s']/ANNOTATION/ALIGNABLE_ANNOTATION[@ANNOTATION_ID='%s']" % (idTier, idAnnotation))
        if idTimeSlotStart is not None:
            a.attrib['TIME_SLOT_REF1'] = str(idTimeSlotStart)
        if idTimeSlotEnd is not None:
            a.attrib['TIME_SLOT_REF2'] = str(idTimeSlotEnd)

    def addAnnotationToTier(self, idTier, strAnnotation, tsStartMs = None, tsEndMs = None):
        tsDefaultLengthMs = 500
        idAnnotation = self.getLastUsedAnnotationId() + 1
        self.setLastUsedAnnotationId(idAnnotation)
        if tsStartMs is None:
            tsStartMs = idAnnotation * tsDefaultLengthMs
            if tsEndMs is None:
                tsEndMs = tsStartMs + tsDefaultLengthMs
#        tiertype = self.getLinguisticTypeForTier(idTier)
        tierelem = self.tree.find("TIER[@TIER_ID='%s']" % idTier)
        annotationelem = ET.SubElement(tierelem, "ANNOTATION")
        alignableelem = ET.SubElement(annotationelem, "ALIGNABLE_ANNOTATION")
        annotationvalueelem = ET.SubElement(alignableelem, "ANNOTATION_VALUE")
        alignableelem.attrib["ANNOTATION_ID"] = str(idAnnotation)
        annotationvalueelem.text = strAnnotation
        idTsStartMs = self.addTimeSlot(None, tsStartMs)
        idTsEndMs = self.addTimeSlot(None, tsEndMs)
        self.setTsForAnnotation(idTier, idAnnotation, idTsStartMs, idTsEndMs)

    def updatePrevAnnotationForAnnotation(self, idAnnotation, idPrevAnn = None):
        # this will just do nothing for time-aligned tiers
        # if idPrevAnn is None, then the attribute will be removed
        a = self.tree.find("TIER/ANNOTATION/REF_ANNOTATION[@ANNOTATION_ID='%s']" % idAnnotation)
        if a != None:
            if idPrevAnn == None:
                del(a.attrib['PREVIOUS_ANNOTATION'])
            else:
                a.attrib['PREVIOUS_ANNOTATION'] = idPrevAnn

    def writeToFile(self, filepath, encoding="UTF-8"):
        """writes the eaf tree as pretty-print xml in filepath"""
        self.tree.write(filepath, encoding=encoding)

class EafPythonic(object):
    
    def __init__(self, filename):
        self.tiersDict = {}
        self.alignableAnnotationsDict = {}
        self.refAnnotationsDict = {}
        self.refAnnotationsDictByTierAndAnnRef = {}
        self.linguistictypesDict = {}
        
        parser = Xml2Obj()
        rootElement = parser.parse(filename)

        for ltElement in rootElement.getElements("LINGUISTIC_TYPE"):
            ta = False
            idLt = ltElement.getAttribute("LINGUISTIC_TYPE_ID")
            if ltElement.getAttribute("TIME_ALIGNABLE") == "true":
                ta = True
            self.linguistictypesDict[idLt] = ta

        for tierElement in rootElement.getElements("TIER"):
            idTier = tierElement.getAttribute("TIER_ID")
            linguisticType = tierElement.getAttribute("LINGUISTIC_TYPE_REF")
            timeAlignable = self.linguistictypesDict[linguisticType]
            participant = tierElement.getAttribute("PARTICIPANT")
            locale = tierElement.getAttribute("PARTICIPANT")
            parent = tierElement.getAttribute("PARENT_REF")
            
            self.tiersDict[idTier] = {
                'linguistic_type' : linguisticType,
                'time_alignable' : timeAlignable,
                'participant' : participant,
                'locale' : locale,
                'parent' : parent
            }
            
            for annotationElement in tierElement.getElements("ANNOTATION"):
                if timeAlignable:
                    for alignableElement in annotationElement.getElements("ALIGNABLE_ANNOTATION"):
                        idAnn = alignableElement.getAttribute("ANNOTATION_ID")
                        ts1 = alignableElement.getAttribute("TIME_SLOT_REF1")
                        ts2 = alignableElement.getAttribute("TIME_SLOT_REF2")
                        value = alignableElement.getElements("ANNOTATION_VALUE")[0].getData()
                        self.alignableAnnotationsDict[idAnn] = {
                            'id' : idAnn,
                            'tierId' : idTier,
                            'ts1' : ts1,
                            'ts2' : ts2,
                            'value' : value
                        }
                else:
                    for refElement in annotationElement.getElements("REF_ANNOTATION"):
                        idAnn = refElement.getAttribute("ANNOTATION_ID")
                        annRef = refElement.getAttribute("ANNOTATION_REF")
                        prevAnn = refElement.getAttribute("PREVIOUS_ANNOTATION")
                        value = refElement.getElements("ANNOTATION_VALUE")[0].getData()
                        self.refAnnotationsDict[idAnn] = {
                            'id' : idAnn,
                            'tierId' : idTier,
                            'annRef' : annRef,
                            'prevAnn' : prevAnn,
                            'value' : value
                        }
                        idByTierAndAnnRef = "%s.%s" % (idTier, annRef)
                        if idByTierAndAnnRef in self.refAnnotationsDictByTierAndAnnRef:
                            self.refAnnotationsDictByTierAndAnnRef[idByTierAndAnnRef].append(idAnn)
                        else:
                            self.refAnnotationsDictByTierAndAnnRef[idByTierAndAnnRef] = [ idAnn ]
                            
    def getLastUsedAnnotationId(self):
        return 0

    def getLocaleForTier(self, idTier):
        return self.tiersDict[idTier]["locale"]

    def getParticipantForTier(self, idTier):
        return self.tiersDict[idTier]["participant"]

    def getTierIdsForLinguisticType(self, type, parent = None):
        return [ id for id in self.tiersDict
                if self.tiersDict[id]["linguistic_type"] == type
                and (parent == None or self.tiersDict[id]["parent"] == parent)]

    def getRefAnnotationIdForAnnotationId(self, idTier, idAnnotation):
        return self.refAnnotationsDict[idAnnotation]["annRef"]

    def getRefAnnotationIdsForTier(self, idTier, annRef = None,  prevAnn = None):
        if annRef != None and prevAnn == None:
            idByTierIdAndAnnRef = "%s.%s" % (idTier, annRef)
            if idByTierIdAndAnnRef in self.refAnnotationsDictByTierAndAnnRef:
                return self.refAnnotationsDictByTierAndAnnRef[idByTierIdAndAnnRef]
            else:
                return []
        else:
            return [ id for id in self.refAnnotationsDict
                    if self.refAnnotationsDict[id]["tierId"] == idTier
                    and (annRef == None or self.refAnnotationsDict[id]["annRef"] == annRef)
                    and (prevAnn == None or self.refAnnotationsDict[id]["prevAnn"] == prevAnn)]

    def getAlignableAnnotationIdsForTier(self, idTier, startTs = None,  endTs = None):
        return [ id for id in self.alignableAnnotationsDict
                if self.alignableAnnotationsDict[id]["tierId"] == idTier
                and (startTs == None or self.alignableAnnotationsDict[id]["ts1"] == startTs)
                and (endTs == None or self.alignableAnnotationsDict[id]["ts2"] == endTs)]

    def getStartTsForAnnotation(self, idTier, idAnn):
        return self.alignableAnntotationsDict[idAnn]["ts1"]
        
    def getEndTsForAnnotation(self, idTier, idAnn):
        return self.alignableAnntotationsDict[idAnn]["ts2"]

    def getAnnotationValueForAnnotation(self, idTier, idAnn):
        if self.tiersDict[idTier]["time_alignable"]:
            return self.alignableAnnotationsDict[idAnn]["value"]
        else:
            return self.refAnnotationsDict[idAnn]["value"]

    def getLinguisticTypeForTier(self, idTier):
        return self.tiersDict[idTier]["linguistic_type"]

    def getSubAnnotationIdsForAnnotationInTier(self, idAnn, idTier, idSubTier):
        ret = []
        if self.tiersDict[idSubTier]["time_alignable"]:
            startTs = self.getStartTsForAnnotation(idTier, idAnn)
            endTs = self.getEndTsForAnnotation(idTier, idAnn)
            ret = self.getAlignableAnnotationIdsForTier(idSubTier, startTs, endTs)
        else:
            ret = self.getRefAnnotationIdsForTier(idSubTier, idAnn)
        return ret

class XmlElement(object):
    ''' A parsed XML element '''
    
    def __init__(self, name, attributes):
        # Record tagname and attributes dictionary
        self.name = name
        self.attributes = attributes
        # Initialize the element's cdata and children to empty
        self.cdata = ''
        self.children = [  ]
        
    def addChild(self, element):
        self.children.append(element)
        
    def getAttribute(self, key):
        return self.attributes.get(key)
        
    def getData(self):
        return self.cdata
    
    def getElements(self, name=''):
        if name:
            return [c for c in self.children if c.name == name]
        else:
            return list(self.children)

class Xml2Obj(object):
    
    def __init__(self):
        self.root = None
        self.nodeStack = [  ]

    def startElement(self, name, attributes):
        'Expat start element event handler'
        # Instantiate an Element object
        element = XmlElement(name.encode( ), attributes)
        # Push element onto the stack and make it a child of parent
        if self.nodeStack:
            parent = self.nodeStack[-1]
            parent.addChild(element)
        else:
            self.root = element
        self.nodeStack.append(element)

    def endElement(self, name):
        'Expat end element event handler'
        self.nodeStack.pop( )

    def characterData(self, data):
        'Expat character data event handler'
        if data.strip( ):
            #data = data.decode("utf-8")
            #data = data.encode( )
            element = self.nodeStack[-1]
            element.cdata += data

    def parse(self, filename):
        # Create an Expat parser
        Parser = expat.ParserCreate("utf-8")
        # Set the Expat event handlers to our methods
        Parser.StartElementHandler = self.startElement
        Parser.EndElementHandler = self.endElement
        Parser.CharacterDataHandler = self.characterData
        # Parse the XML File
        ParserStatus = Parser.Parse(open(filename).read( ), 1)
        return self.root
