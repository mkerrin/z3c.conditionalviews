##############################################################################
# Copyright (c) 2007 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
##############################################################################

import os
import datetime
import unittest

import persistent
import zope.interface
import zope.schema
import zope.filerepresentation.interfaces
import zope.annotation.interfaces
import zope.publisher.browser
from zope.security.proxy import removeSecurityProxy
from zope.testing import doctest
import zope.app.testing.functional

import z3c.conditionalviews
import z3c.conditionalviews.interfaces

here = os.path.dirname(os.path.realpath(__file__))
ConditionalViewLayer = zope.app.testing.functional.ZCMLLayer(
    os.path.join(here, "ftesting.zcml"), __name__, "ConditionalViewLayer")


class Simpleview(zope.publisher.browser.BrowserView):

    @z3c.conditionalviews.ConditionalView
    def __call__(self, letter = "x"):
        return "%s\n%s\n" %(letter * 40, letter * 40)


class IFile(zope.interface.Interface):

    data = zope.schema.Bytes(
        title = u"Data")


class File(persistent.Persistent):
    zope.interface.implements(IFile)

    def __init__(self, data):
        self.data = data


class ViewFile(zope.publisher.browser.BrowserView):

    @z3c.conditionalviews.ConditionalView
    def __call__(self):
        return self.context.data


class FileFactory(object):
    zope.interface.implements(zope.filerepresentation.interfaces.IFileFactory)

    def __init__(self, container):
        self.container = container

    def __call__(self, name, content_type, data):
        fileobj = File(data)
        setETag(fileobj, None)
        return fileobj


class WriteFile(object):
    zope.interface.implements(zope.filerepresentation.interfaces.IWriteFile)

    def __init__(self, context):
        self.context = context

    def write(self, data):
        self.context.data = data
        setETag(self.context, None)


class FileETag(object):
    zope.interface.implements(z3c.conditionalviews.interfaces.IETag)
        
    def __init__(self, context, request, view):
        self.context = self.__parent__ = context

    weak = False

    @property
    def etag(self):
        annots = zope.annotation.interfaces.IAnnotations(self.context)
        return "%s:%d" %(self.context.__name__, annots["ETAG"])


def setETag(fileobj, event):
    annots = zope.annotation.interfaces.IAnnotations(
        removeSecurityProxy(fileobj))
    annots.setdefault("ETAG", 0)
    annots["ETAG"] = annots["ETAG"] + 1


class LastModification(object):
    zope.interface.implements(
        z3c.conditionalviews.interfaces.ILastModificationDate)

    def __init__(self, view):
        self.view = view

    lastmodified = datetime.datetime(2007, 2, 5, 5, 43, 23)


def integrationSetup(test):
    test.globs["http"] = zope.app.testing.functional.HTTPCaller()


def integrationTeardown(test):
    del test.globs["http"]


def test_suite():
    readme = doctest.DocFileSuite(
        "README.txt",
        setUp = integrationSetup,
        tearDown = integrationTeardown,
        optionflags = doctest.NORMALIZE_WHITESPACE)
    readme.layer = ConditionalViewLayer

    return unittest.TestSuite((
        doctest.DocFileSuite("validation.txt"),
        doctest.DocTestSuite("z3c.conditionalviews.lastmodification"),
        doctest.DocTestSuite("z3c.conditionalviews.etag"),
        doctest.DocTestSuite("z3c.conditionalviews.adapters"),
        readme,
        ))
