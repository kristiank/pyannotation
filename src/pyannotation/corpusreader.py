# -*- coding: utf-8 -*-
# (C) 2009 copyright by Peter Bouda
"""
CorpusReader, GlossCorpusReader, PosCorpusReader implement a
part of the corpus reader API described in the Natural
Language Toolkit (NLTK):
http://nltk.googlecode.com/svn/trunk/doc/howto/corpus.html
"""

__author__ =  'Peter Bouda'
__version__=  '0.2.0'

import os, glob
import re
from pyannotation.elan.data import EafAnnotationFileObject
from pyannotation.toolbox.data import ToolboxAnnotationFileObject
from pyannotation.data import AnnotationTree

# file types
(EAF, KURA, TOOLBOX) = range(3)

# interlinear types: WORDS means "no interlinear"
(GLOSS, WORDS, POS) = range(3)

class CorpusReader(object):
    """
    The base class for all corpus readers. It provides
    access to all data that contain utterances and words.
    """
    def __init__(self, locale = None, participant = None, utterancetierTypes = None, wordtierTypes = None, translationtierTypes = None):
        self.locale = locale
        self.participant = participant
        self.utterancetierTypes = utterancetierTypes
        self.wordtierTypes = wordtierTypes
        self.translationtierTypes = translationtierTypes
        self.postierTypes = None
        self.morphemetierTypes = None
        self.glosstierTypes = None
        self.interlineartype = WORDS
        self.eaftrees = []

    def addFile(self, filepath, filetype):
        annotationFileObject = None
        if filetype == EAF:
            annotationFileObject = EafAnnotationFileObject(filepath)
        elif filetype == TOOLBOX:
            annotationFileObject = ToolboxAnnotationFileObject(filepath)
        if annotationFileObject != None:
            annotationTierHandler = annotationFileObject.createTierHandler()

            # create the parser
            if self.interlineartype == GLOSS:
              annotationParser = annotationFileObject.createParser()
            elif self.interlineartype == WORDS:
              annotationParser = annotationFileObject.createParserWords()
            elif self.interlineartype == POS:
              annotationParser = annotationFileObject.createParserPos()

            annotationTree = AnnotationTree(annotationParser)
            # Setting the tier types for the parse
            if self.utterancetierTypes != None:
                annotationTierHandler.setUtterancetierType(self.utterancetierTypes)
            if self.wordtierTypes != None:
                annotationTierHandler.setWordtierType(self.wordtierTypes)
            if self.morphemetierTypes != None:
                annotationTierHandler.setMorphemetierType(self.morphemetierTypes)
            if self.glosstierTypes != None:
                annotationTierHandler.setGlosstierType(self.glosstierTypes)
            if self.postierTypes != None:
                annotationTierHandler.setPostierType(self.glosstierTypes)
            if self.translationtierTypes != None:
                annotationTierHandler.setTranslationtierType(translationtierTypes)
            annotationTree.parse()
            self.eaftrees.append([filepath, annotationTree])

    def words(self):
        """
        Returns a list of words from the corpus files.
        """
        words = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                for word in utterance[2]:
                    if len(word) > 0:
                        words.append(word[1].encode("utf-8"))
        return words

    def sents(self):
        """
        Returns a list of sentences, which are lists of words from the
        corpus files.
        """
        sents = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                words = []
                for word in utterance[2]:
                    if len(word) > 0:
                        words.append(word[1].encode("utf-8"))
                if len(words) > 0:
                    sents.append(words)
        return sents

    def sentsWithTranslations(self):
        """
        Returns a list of (list of words, translation) tuples from the
        corpus files.
        """
        sents = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                words = []
                for word in utterance[2]:
                    if len(word) > 0:
                        words.append(word[1].encode("utf-8"))
                if len(words) > 0:
                    sents.append((words, utterance[3]))
        return sents

class PosCorpusReader(CorpusReader):
    """
    The class EafPosCorpusReader implements a part of the corpus reader API
    described in the Natual Language Toolkit (NLTK). The class reads in all
    the .eaf files (from the linguistics annotation software called Elan)
    in a given directory and makes this data accessible through
    several functions. The data contains "tags", which are annotations
    in "part of speech" tiers in Elan.
    The .eaf files must at least contain a tier with words.
    Access to the data is normally read-only.
    """
    
    def __init__(self, locale = None, participant = None, utterancetierTypes = None, wordtierTypes = None, postierTypes = None, translationtierTypes = None):
        """
        root: is the directory where your .eaf files are stored. Only the
            files in the given directory are read, there is no recursive
            reading right now. This parameter is obligatory.
        files: a regular expression for the filenames to read. The
            default value is "*.eaf"
        locale: restricts the corpus data to tiers with the given locale.
        participant: restricts the corpus data to tiers with the given
            particiapant.
        utterancetierType: the type of the tier you gave to your
            "utterances" in Elan. The EafTrees have several default values
            for this tier type: [ "utterance", "utterances", "Äußerung",
            "Äußerungen" ]. If you used a different tier type in Elan you
            can specify it as a parameter here. The parameter may either
            be a string or a list of strings.
        wordtierType: the type of the tier you gave to your
            "words" in Elan. The EafTrees have several default values
            for this tier type: [ "words", "word", "Wort", "Worte",
            "Wörter" ]. If you used a different tier type in Elan you
            can specify it as a parameter here. The parameter may either
            be a string or a list of strings.
        postierType: the type of the tier you gave to your
            "parts of speeches" in Elan. The EafTrees have several default
            values for this tier type: [ "part of speech", "parts of speech",
            "Wortart", "Wortarten" ]. If you used a different tier type in
            Elan you can specify it as a parameter here. The parameter
            may either be a string or a list of strings.
        """
        self.locale = locale
        self.participant = participant
        self.utterancetierTypes = utterancetierTypes
        self.wordtierTypes = wordtierTypes
        self.postierTypes = postierTypes
        self.morphemetierTypes = None
        self.glosstierTypes = None
        self.translationtierTypes = translationtierTypes
        self.interlineartype = POS
        self.eaftrees = []

    def taggedWords(self):
        """
        Returns a list of (word, tag) tuples. Each tag is a list of
        parts of speech.
        """
        words = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                for word in utterance[2]:
                    if len(word) > 0:
                        tag = []
                        for (id, pos) in word[2]:
                            tag.append(pos)
                        words.append((word[1].encode('utf-8'), tag))
        return words

    def taggedSents(self):
        """
        Returns a list of (list of (word, tag) tuples). Each tag is a list
        of parts of speech.
        """
        sents = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                words = []
                for word in utterance[2]:
                    if len(word) > 0:
                        tag = []
                        for id, pos in word[2]:
                            tag.append(pos)
                        words.append((word[1].encode('utf-8'), tag))
                if len(words) > 0:
                    sents.append(words)
        return sents

    def taggedSentsWithTranslations(self):
        """
        Returns a list of (sentence, translation) tuples. Sentences
        are lists of (word, tag) tuples. Each tag is a list of
        parts of speech.
        """
        sents = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                words = []
                for word in utterance[2]:
                    if len(word) > 0:
                        tag = []
                        for id, pos in word[2]:
                            tag.append(pos)
                        words.append((word[1].encode('utf-8'), tag))
                if len(words) > 0:
                    sents.append((words, utterance[3]))
        return sents

class GlossCorpusReader(CorpusReader):
    """The class EafGlossCorpusReader implements a part of the corpus reader API
    described in the Natural Language Toolkit (NLTK). The class reads in all
    the .eaf files (from the linguistics annotation software called Elan)
    in a given directory and makes this data accessible through
    several functions. The data contains "tags", which are annotations
    in "morpheme" and "gloss" tiers in Elan.
    The .eaf files must at least contain a tier with words.
    Access to the data is normally read-only.
    """

    def __init__(self, locale = None, participant = None, utterancetierTypes = None, wordtierTypes = None,  morphemetierTypes = None, glosstierTypes = None, translationtierTypes = None):
        """
        root: is the directory where your .eaf files are stored. Only the
            files in the given directory are read, there is no recursive
            reading right now. This parameter is obligatory.
        files: a regular expression for the filenames to read. The
            default value is "*.eaf"
        locale: restricts the corpus data to tiers with the given locale.
        participant: restricts the corpus data to tiers with the given
            particiapant.
        utterancetierTypes: the type of the tier you gave to your
            "utterances" in Elan. The EafTrees have several default values
            for this tier type: [ "utterance", "utterances", "Äußerung",
            "Äußerungen" ]. If you used a different tier type in Elan you
            can specify it as a parameter here. The parameter may either
            be a string or a list of strings.
        wordtierTypes: the type of the tier you gave to your
            "words" in Elan. The EafTrees have several default values
            for this tier type: [ "words", "word", "Wort", "Worte",
            "Wörter" ]. If you used a different tier type in Elan you
            can specify it as a parameter here. The parameter may either
            be a string or a list of strings.
        morphemetierTypes: the type of the tier you gave to your
            "morphemes" in Elan. The EafTrees have several default values
            for this tier type: [ "morpheme", "morphemes",  "Morphem",
            "Morpheme" ]. If you used a different tier type in Elan you
            can specify it as a parameter here. The parameter may either
            be a string or a list of strings.
        glosstierTypes: the type of the tier you gave to your
            "glosses" in Elan. The EafTrees have several default values
            for this tier type: [ "glosses", "gloss", "Glossen", "Gloss",
            "Glosse" ]. If you used a different tier type in Elan you
            can specify it as a parameter here. The parameter may either
            be a string or a list of strings.
        translationtierTypes: the type of the tier you gave to your
            "translations" in Elan. The EafTrees have several default values
            for this tier type: [  "translation", "translations",
            "Übersetzung",  "Übersetzungen" ]. If you used a different tier
            type in Elan you can specify it as a parameter here. The
            parameter may either be a string or a list of strings.
        """
        self.locale = locale
        self.participant = participant
        self.utterancetierTypes = utterancetierTypes
        self.wordtierTypes = wordtierTypes
        self.postierTypes = None
        self.morphemetierTypes = utterancetierTypes
        self.glosstierTypes = utterancetierTypes
        self.translationtierTypes = translationtierTypes
        self.interlineartype = GLOSS
        self.eaftrees = []

    def morphemes(self):
        """
        Returns a list of morphemes from the corpus files.
        """
        morphemes = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                for word in utterance[2]:
                    if len(word) > 0:
                        for morpheme in word[2]:
                            if morpheme[1] != '':
                                morphemes.append(morpheme[1].encode("utf-8"))
        return morphemes

    def taggedMorphemes(self):
        """
        Returns a list of (morpheme, list of glosses) tuples.
        """
        morphemes = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                for word in utterance[2]:
                    if len(word) > 0:
                        for morpheme in word[2]:
                            if morpheme[1] != '':
                                glosses = []
                                for gloss in morpheme[2]:
                                    if gloss[1] != '':
                                        glosses.append(gloss[1].encode("utf-8"))
                                morphemes.append((morpheme[1].encode("utf-8"), glosses))
        return morphemes
        
    def taggedWords(self):
        """
        Returns a list of (word, tag) tuples. Each tag is a list of
        (morpheme, list of glosses) tuples.
        """
        words = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                for word in utterance[2]:
                    if len(word) > 0:
                        tag = []
                        for morpheme in word[2]:
                            if morpheme[1] != '':
                                glosses = []
                                for gloss in morpheme[2]:
                                    if gloss[1] != '':
                                        glosses.append(gloss[1].encode("utf-8"))
                                tag.append((morpheme[1].encode("utf-8"), glosses))
                        words.append((word[1].encode("utf-8"), tag))
        return words

    def taggedSents(self):
        """
        Returns a list of (list of (word, tag) tuples). Each tag is
        a list of (morpheme, list of glosses) tuples.
        """
        sents = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                words = []
                for word in utterance[2]:
                    if len(word) > 0:
                        tag = []
                        for morpheme in word[2]:
                            if morpheme[1] != '':
                                glosses = []
                                for gloss in morpheme[2]:
                                    if gloss[1] != '':
                                        glosses.append(gloss[1].encode("utf-8"))
                                tag.append((morpheme[1].encode("utf-8"), glosses))
                        words.append((word[1].encode("utf-8"), tag))
                if len(words) > 0:
                    sents.append(words)
        return sents

    def taggedSentsWithTranslations(self):
        """
        Returns a list of (sentence, translation) tuples. Sentences
        are lists of (word, tag) tuples. Each tag is a list of
        (morpheme, list of glosses) tuples.
        """
        sents = []
        for (infile, tree) in self.eaftrees:
            for utterance in tree.getTree():
                if self.locale != None and utterance[4] != self.locale:
                    continue
                if self.participant != None and utterance[5] != self.participant:
                    continue
                words = []
                for word in utterance[2]:
                    if len(word) > 0:
                        tag = []
                        #print word
                        for morpheme in word[2]:
                            if morpheme[1] != '':
                                glosses = []
                                for gloss in morpheme[2]:
                                    if gloss[1] != '':
                                        glosses.append(gloss[1].encode("utf-8"))
                                tag.append((morpheme[1].encode("utf-8"), glosses))
                        words.append((word[1].encode("utf-8"), tag))
                if len(words) > 0:
                    sents.append((words, utterance[3]))
        return sents

