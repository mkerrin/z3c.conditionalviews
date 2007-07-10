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

import calendar
import zope.component
import zope.datetime
import zope.interface

import interfaces

class ModifiedSinceValidator(object):
    """

      >>> import datetime
      >>> from zope.interface.verify import verifyObject
      >>> from zope.publisher.interfaces.browser import IBrowserRequest
      >>> from zope.publisher.browser import TestRequest
      >>> from zope.publisher.browser import BrowserView

      >>> def format(dt):
      ...    return zope.datetime.rfc1123_date(
      ...        calendar.timegm(dt.utctimetuple()))

      >>> lmt = datetime.datetime(2007, 1, 6, 13, 42, 12,
      ...    tzinfo = zope.datetime.tzinfo(60))

    ModifiedSinceValidator is a HTTP validator utility that will evaluate
    a HTTP request to see if it passes or fails the If-Modifed* protocol.

      >>> validator = ModifiedSinceValidator()
      >>> verifyObject(interfaces.IHTTPValidator, validator)
      True

    If-Modified-Since
    =================

    The If-Modified-Since request-header field is used with a method to
    make it conditional: if the requested variant has not been modified
    since the time specified in this field, an entity will not be
    returned from the server; instead, a 304 (not modified) response will
    be returned without any message-body.

      >>> class SimpleView(BrowserView):
      ...    def __call__(self):
      ...        self.request.response.setStatus(200)
      ...        self.request.response.setHeader('Last-Modified', format(lmt))
      ...        return 'Rendered view representation.'

    Create a context adapter to find the last modified date of the context
    object. We store the lastmodifed datatime object as a class attribute so
    that we can easily change its value during these tests.

      >>> class LastModification(object):
      ...    zope.interface.implements(interfaces.ILastModificationDate)
      ...    lastmodified = None
      ...    def __init__(self, context, request, view):
      ...        pass

    A ILastModificationDate adapter must be registered for this validator
    to know when a view was last modified.

      >>> request = TestRequest(
      ...    environ = {'IF_MODIFIED_SINCE': format(lmt)})
      >>> request['IF_MODIFIED_SINCE']
      'Sat, 06 Jan 2007 12:42:12 GMT'
      >>> view = SimpleView(None, request)

      >>> validator.valid(None, request, view) #doctest:+ELLIPSIS
      True

    Now register the last modified data adapter, and set up 

      >>> gsm = zope.component.getGlobalSiteManager()
      >>> gsm.registerAdapter(LastModification, (None, IBrowserRequest, None))

    Since there is no last modification date by default the request is valid.

      >>> validator.valid(None, request, view)
      True

    Set the last modification date to be equal.

      >>> LastModification.lastmodified = lmt
      >>> validator.valid(None, request, view)
      False

    Increase the current last modification time of the view by 1 second.

      >>> LastModification.lastmodified = lmt + datetime.timedelta(seconds = 1)
      >>> validator.valid(None, request, view)
      True

    Decrease the current last modification time of the view by 1 second.

      >>> LastModification.lastmodified = lmt - datetime.timedelta(seconds = 1)
      >>> validator.valid(None, request, view)
      False

    Test invalid request data.

      >>> invalidrequest = TestRequest(environ = {'IF_MODIFIED_SINCE': 'XXX'})
      >>> validator.valid(None, invalidrequest, view)
      True

      >>> LastModification.lastmodified = lmt

    If-UnModified-Since
    ===================

      >>> request = TestRequest(
      ...    environ = {'IF_UNMODIFIED_SINCE': format(lmt)})
      >>> request['IF_UNMODIFIED_SINCE']
      'Sat, 06 Jan 2007 12:42:12 GMT'

      >>> view = SimpleView(None, request)

    The If-Unmodified-Since request-header field is used with a method to
    make it conditional. If the requested resource has not been modified
    since the time specified in this field, the server SHOULD perform the
    requested operation as if the If-Unmodified-Since header were not
    present.

      >>> validator.valid(None, request, view)
      True

    Increase the current last modified time of the view by 1 second.

      >>> LastModification.lastmodified = lmt + datetime.timedelta(seconds = 1)
      >>> validator.valid(None, request, view)
      False

    Decrease the current last modified time of the view by 1 second.

      >>> LastModification.lastmodified = lmt - datetime.timedelta(seconds = 1)
      >>> validator.valid(None, request, view)
      True

    Invalid date header.

      >>> request = TestRequest(
      ...    environ = {'IF_UNMODIFIED_SINCE': 'xxx'})
      >>> view = SimpleView(None, request)

      >>> validator.valid(None, request, view)
      False

    If no `If-Modified-Since` or `If-UnModified-Since` conditional HTTP
    headers are set then the request is valid.

      >>> request = TestRequest()
      >>> view = SimpleView(None, request)
      >>> validator.valid(None, request, view)
      Traceback (most recent call last):
      ...
      ValueError: Protocol implementation is broken - evaluate should be False

    But then the validator should not evaluate the request.

      >>> validator.evaluate(None, request, view)
      False

    Valid responses
    ===============

      >>> LastModification.lastmodified = lmt
      >>> request = TestRequest(
      ...    environ = {'IF_UNMODIFIED_SINCE': format(lmt)})
      >>> view = SimpleView(None, request)

    Since we have a conditional header present the validator can evaluate
    the data.

      >>> validator.evaluate(None, request, view)
      True

      >>> validator.valid(None, request, view)
      True

      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getStatus()
      599
      >>> request.response.getHeader('Last-Modified')
      'Sat, 06 Jan 2007 12:42:12 GMT'

    Since the `Last-Modified` header is already set, it doesn't get overriden.

      >>> LastModification.lastmodified = lmt + datetime.timedelta(seconds = 1)
      >>> validator.updateResponse(None, request, view)
      >>> request.response.getStatus()
      599
      >>> request.response.getHeader('Last-Modified')
      'Sat, 06 Jan 2007 12:42:12 GMT'

    Invalid responses
    =================

      >>> LastModification.lastmodified = lmt + datetime.timedelta(seconds = 1)
      >>> request = TestRequest(environ = {'IF_UNMODIFIED_SINCE': format(lmt)})
      >>> view = SimpleView(None, request)

    Since we have a conditional header present the validator can evaluate
    the data.

      >>> validator.evaluate(None, request, view)
      True
      >>> validator.valid(None, request, view)
      False

      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getStatus()
      599
      >>> request.response.getHeader('Last-Modified')
      'Sat, 06 Jan 2007 12:42:13 GMT'
      >>> validator.invalidStatus(None, request, view)
      304

    Since the `Last-Modified` header is already set, it doesn't get overriden.

      >>> LastModification.lastmodified = lmt
      >>> validator.updateResponse(None, request, view)
      >>> request.response.getHeader('Last-Modified')
      'Sat, 06 Jan 2007 12:42:13 GMT'

    Query strings
    =============

    If a query string is present in the request, then the client requested
    a content negotiated view, or else they tried to fill out a form. Either
    way the request must evaluate to True, and be executed.

      >>> LastModification.lastmodified = lmt + datetime.timedelta(seconds = 1)
      >>> request = TestRequest(environ = {'IF_UNMODIFIED_SINCE': format(lmt),
      ...                                  'QUERY_STRING': 'argument=true'})
      >>> view = SimpleView(None, request)
      >>> validator.evaluate(None, request, view)
      True
      >>> validator.valid(None, request, view)
      True

    We should not update the response when there is a query string present.

      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getHeader('Last-Modified') is None
      True

    Cleanup
    -------

      >>> gsm.unregisterAdapter(LastModification,
      ...    (None, IBrowserRequest, None))
      True

    """
    zope.interface.implements(interfaces.IHTTPValidator)

    def ifModifiedSince(self, request, mtime, header):
        headervalue = request.getHeader(header, None)
        if headervalue is not None:
            # current last modification time for this view
            last_modification_time = long(calendar.timegm(mtime.utctimetuple()))
            try:
                headervalue = long(zope.datetime.time(
                    headervalue.split(";", 1)[0]))
            except:
                # error processing the HTTP-date value - return the
                # default value.
                return True
            else:
                return last_modification_time > headervalue
        # By default all HTTP Cache validators should return True so that the
        # request proceeds as normal.
        return True

    def evaluate(self, context, request, view):
        return \
             request.getHeader("If-Modified-Since", None) is not None or \
             request.getHeader("If-UnModified-Since", None) is not None

    def getDataStorage(self, context, request, view):
        return zope.component.queryMultiAdapter(
            (context, request, view), interfaces.ILastModificationDate)

    def valid(self, context, request, view):
        if request.get("QUERY_STRING", "") != "":
            # a query string was supplied in the URL, so the data supplied
            # by the ILastModificationDate does not apply to this view.
            return True

        lmd = self.getDataStorage(context, request, view)
        if lmd is None:
            return True

        lmd = lmd.lastmodified
        if lmd is None:
            return True

        if request.getHeader("If-Modified-Since", None) is not None:
            return self.ifModifiedSince(request, lmd, "If-Modified-Since")
        if request.getHeader("If-UnModified-Since", None) is not None:
            return not self.ifModifiedSince(
                request, lmd, "If-UnModified-Since")

        raise ValueError(
            "Protocol implementation is broken - evaluate should be False")

    def invalidStatus(self, context, request, view):
        return 304

    def updateResponse(self, context, request, view):
        if request.response.getHeader("Last-Modified", None) is None and \
               request.get("QUERY_STRING", "") == "":
            storage = self.getDataStorage(context, request, view)
            if storage is not None and storage.lastmodified is not None:
                lmd = zope.datetime.rfc1123_date(
                    calendar.timegm(storage.lastmodified.utctimetuple()))
                request.response.setHeader("Last-Modified", lmd)
