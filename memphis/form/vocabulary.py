##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" vocabulary implementation from zope.schema """
from zope import interface
from memphis.form.interfaces import _, ITerm, IVocabulary


class SimpleTerm(object):
    """Simple tokenized term used by SimpleVocabulary."""
    interface.implements(ITerm)

    def __init__(self, value, token=None, 
                 title=None, description=None):
        """Create a term for value and token. If token is omitted,
        str(value) is used for the token.  If title is provided,
        term implements ITitledTokenizedTerm.
        """
        self.value = value
        if token is None:
            token = value
        self.token = str(token)
        self.title = title
        self.description = description


class SimpleVocabulary(object):
    """Vocabulary that works from a sequence of terms."""
    interface.implements(IVocabulary)

    def __init__(self, *terms):
        """Initialize the vocabulary given a list of terms.

        The vocabulary keeps a reference to the list of terms passed
        in; it should never be modified while the vocabulary is used.
        """
        self.by_value = {}
        self.by_token = {}
        self._terms = terms
        for term in self._terms:
            if term.value in self.by_value:
                raise ValueError(
                    'term values must be unique: %s' % repr(term.value))
            if term.token in self.by_token:
                raise ValueError(
                    'term tokens must be unique: %s' % repr(term.token))
            self.by_value[term.value] = term
            self.by_token[term.token] = term

    @classmethod
    def fromItems(cls, *items):
        """Construct a vocabulary from a list of (token, value) pairs. """
        terms = [cls.createTerm(*rec) for rec in items]
        return cls(*terms)

    @classmethod
    def fromValues(cls, *values):
        """Construct a vocabulary from a simple list. """
        terms = [cls.createTerm(value) for value in values]
        return cls(*terms)

    @classmethod
    def createTerm(cls, *args):
        """Create a single term from data."""
        return SimpleTerm(*args)

    def __contains__(self, value):
        try:
            return value in self.by_value
        except TypeError:
            # sometimes values are not hashable
            return False

    def getTerm(self, value):
        try:
            return self.by_value[value]
        except KeyError:
            raise LookupError(value)

    def getTermByToken(self, token):
        try:
            return self.by_token[token]
        except KeyError:
            raise LookupError(token)

    def getValue(self, token):
        return self.getTermByToken(token).value

    def __iter__(self):
        return iter(self._terms)

    def __len__(self):
        return len(self.by_value)
