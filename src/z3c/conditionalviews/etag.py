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

import zope.interface
import zope.component
from zope.app.http.interfaces import INullResource

import interfaces

class ETagValidator(object):
    """

      >>> from zope.interface.verify import verifyObject
      >>> from zope.publisher.interfaces.browser import IBrowserRequest
      >>> from zope.publisher.browser import TestRequest
      >>> from zope.publisher.browser import BrowserView

      >>> class SimpleView(BrowserView):
      ...    def __call__(self):
      ...        self.request.response.setStatus(200)
      ...        self.request.response.setHeader('ETag', '"xxxetag"')
      ...        return 'Rendered view representation'

    The ETagValidator is a HTTP utility validator that implements the entity
    tag protocol.

      >>> validator = ETagValidator()
      >>> verifyObject(interfaces.IHTTPValidator, validator)
      True

    We need to make sure that we can corrctly parse any `If-Match`, or
    `If-None-Match` HTTP header.

      >>> request = TestRequest(environ = {
      ...    'NOQUOTE': 'aa',
      ...    'ONE': '"aa"',
      ...    'TWO': '"aa", "bb"',
      ...    'ALL': '"aa", *, "bb"',
      ...    'WEAK': 'W/"w1"',
      ...    'WEAK_TWO': 'W/"w1", W/"w2"',
      ...    })
      >>> view = SimpleView(None, request)

      >>> validator.parseMatchList(request, 'missing')
      []
      >>> validator.parseMatchList(request, 'noquote')
      []
      >>> validator.parseMatchList(request, 'one')
      ['aa']
      >>> validator.parseMatchList(request, 'two')
      ['aa', 'bb']
      >>> validator.parseMatchList(request, 'all')
      ['aa', '*', 'bb']
      >>> validator.parseMatchList(request, 'weak')
      ['w1']
      >>> validator.parseMatchList(request, 'weak_two')
      ['w1', 'w2']

    When neither a `If-None-Match` or a `If-Match` header is present in the
    request then we cannot evaluate this request as a conditional request,
    according to the `If-None-Match` or `If-Match` protocol.

      >>> validator.evaluate(None, request, view)
      False

    But if someone does try and validate the request then it is just True.

      >>> validator.valid(None, request, view)
      True

    If-None-Match
    =============

    Define a simple ETag adapter for getting the current entity tag of a
    view. We can change the value of the current etag by setting the
    etag class attribute.

      >>> class CurrentETag(object):
      ...    zope.interface.implements(interfaces.IETag)
      ...    def __init__(self, context, request, view):
      ...        pass
      ...    weak = False
      ...    etag = 'xyzzy'

      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"'})
      >>> view = SimpleView(None, request)

    Since we have a conditional header present the validator can evaluate
    this request.

      >>> validator.evaluate(None, request, view)
      True

    No current IETag adapter available so the request is valid, and the
    update response method works but doesn't set any headers.

      >>> validator.valid(None, request, view)
      True
      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getHeader('ETag', None) is None
      True

    But if the `If-None-Match` value is '*' then the request is invalid
    even tough the resource has no entity tag.

      >>> request._environ['IF_NONE_MATCH'] = '"*"'
      >>> validator.valid(None, request, view)
      False
      >>> request._environ['IF_NONE_MATCH'] = '"xyzzy"'

    The default value for the current entity tab is the same as in the request,
    so the request is invalid, that is none of the entity tags match.

      >>> zope.component.getGlobalSiteManager().registerAdapter(
      ...    CurrentETag, (None, IBrowserRequest, None))

      >>> validator.valid(None, request, view)
      False

    Etags don't match so the request is valid.

      >>> CurrentETag.etag = 'xxx'
      >>> validator.valid(None, request, view)
      True

    Test '*' which matches all values.

      >>> request._environ['IF_NONE_MATCH'] = '"*"'
      >>> validator.valid(None, request, view)
      False

    Test multiple `If-None-Match` values.

      >>> request._environ['IF_NONE_MATCH'] = '"xxx", "yyy"'
      >>> validator.valid(None, request, view)
      False
      >>> CurrentETag.etag = 'xxxzz'
      >>> validator.valid(None, request, view)
      True

    Test multiple `If-None-Match` values with a '*'

      >>> request._environ['IF_NONE_MATCH'] = '"*", "xxx", "yyy"'
      >>> validator.valid(None, request, view)
      False
      >>> CurrentETag.etag = None
      >>> validator.valid(None, request, view)
      False

    If-Match
    ========

      >>> request = TestRequest(environ = {'IF_MATCH': '"xyzzy"'})
      >>> view = SimpleView(None, request)
      >>> CurrentETag.etag = None

    Since we have a conditional header present the validator can
    evaluate this request.

      >>> validator.evaluate(None, request, view)
      True

    Since there is no entity tag for the view, we don't match 'xyzzy', or
    equivalently it is set to None.

      >>> validator.valid(None, request, view)
      False

    The entity tags differ.

      >>> CurrentETag.etag = 'xxx'
      >>> validator.valid(None, request, view)
      False

    The entity tags are the same.

      >>> CurrentETag.etag = 'xyzzy'
      >>> validator.valid(None, request, view)
      True

    A `If-Match` header value of '*' matches everything.

      >>> request._environ['IF_MATCH'] = '"*"'
      >>> validator.valid(None, request, view)
      True

    Try multiple values.

      >>> request._environ['IF_MATCH'] = '"xxx", "yyy"'
      >>> validator.valid(None, request, view)
      False

      >>> request._environ['IF_MATCH'] = '"xyzzy", "yyy"'
      >>> validator.valid(None, request, view)
      True

    Try multiple values with an '*' value.

      >>> request._environ['IF_MATCH'] = '"xxx", "*", "yyy"'
      >>> validator.valid(None, request, view)
      True

    Common responses
    ================

    Whether or not a request is valid or invalid the updateResponse method
    is called after the status of the request is set by either the view / or
    the `invalidStatus` method. Note that the updateResponse method does not
    return any value. If it did then this value is not used for anything.

      >>> CurrentETag.etag = 'xxx'
      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"'})
      >>> view = SimpleView(None, request)
      >>> validator.valid(None, request, view)
      True

      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getStatus() # status is unset
      599
      >>> request.response.getHeader('ETag')
      '"xxx"'

    Since the `ETag` response header is set, we don't override it. Changing
    the current entity tag and recalling the updateResponse method confirms
    this. Note that this feature is neccessary to avoid situations where
    a developer manages the entity tag of a view independently of this package.

      >>> CurrentETag.etag = 'yyy'
      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getStatus()
      599
      >>> request.response.getHeader('ETag')
      '"xxx"'

    Marking the current entity tag as weak.

      >>> CurrentETag.weak = True

      >>> validator.updateResponse(None, request, view)
      >>> request.response.getHeader('ETag')
      '"xxx"'

    Since the 'ETag' header is already set we need to recreate the response
    object to test the condition when the weak attribute is True.

      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"'})
      >>> view = SimpleView(None, request)
      >>> validator.valid(None, request, view)
      True

      >>> validator.updateResponse(None, request, view)
      >>> request.response.getHeader('ETag')
      'W/"yyy"'

      >>> CurrentETag.weak = False

    Invalid header
    ==============

    If the header doesn't parse then the requets is True.

      >>> request._environ['IF_NONE_MATCH'] = '"yyy"'
      >>> validator.valid(None, request, view)
      False

    Now if we are missing the double quotes around the entity tag.

      >>> request._environ['IF_NONE_MATCH'] = 'yyy'
      >>> validator.valid(None, request, view)
      True

    Invalid status
    ==============

    In the case of entity tags and invalid responses we should return a 304
    for the GET, and HEAD method requests and 412 otherwise.

      >>> CurrentETag.etag = 'xyzzy'
      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"'})
      >>> request.method
      'GET'
      >>> view = SimpleView(None, request)
      >>> validator.valid(None, request, view)
      False

      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getStatus()
      599
      >>> request.response.getHeader('ETag')
      '"xyzzy"'

      >>> validator.invalidStatus(None, request, view)
      304

    And the same for `HEAD` methods.

      >>> CurrentETag.etag = 'xyzzy'
      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"',
      ...                                  'REQUEST_METHOD': 'HEAD'})
      >>> request.method
      'HEAD'
      >>> view = SimpleView(None, request)
      >>> validator.valid(None, request, view)
      False

      >>> validator.invalidStatus(None, request, view)
      304

    For anyother request method we get a `412 Precondition failed` response.

      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"',
      ...                                  'REQUEST_METHOD': 'FROG'})
      >>> request.method
      'FROG'
      >>> view = SimpleView(None, request)
      >>> validator.valid(None, request, view)
      False

      >>> validator.invalidStatus(None, request, view)
      412

    Query strings
    =============

    If a query is present in the request then either the client is filling
    in a form with a GET method (oh why..), or else they are trying to do
    some content negotiation, and hence the data supplied by the IETag adapter
    does not apply to the view. But there are still cases where a request with
    a query string can still fail.

      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"xyzzy"',
      ...                                  'REQUEST_METHOD': 'GET',
      ...                                  'QUERY_STRING': 'argument=value'})
      >>> view = SimpleView(None, request)
      >>> validator.evaluate(None, request, view)
      True
      >>> validator.valid(None, request, view)
      True
      >>> request._environ['IF_NONE_MATCH'] = '"*"'
      >>> validator.valid(None, request, view)
      False

      >>> request = TestRequest(environ = {'IF_MATCH': '"xyzzy"',
      ...                                  'REQUEST_METHOD': 'GET',
      ...                                  'QUERY_STRING': 'argument=value'})
      >>> view = SimpleView(None, request)
      >>> validator.evaluate(None, request, view)
      True
      >>> validator.valid(None, request, view)
      False
      >>> request._environ['IF_MATCH'] = '"*"'
      >>> validator.valid(None, request, view)
      True

    Finally if we have a query string then when we try and update the
    response we should not set the entity tag.

      >>> validator.updateResponse(None, request, view) is None
      True
      >>> request.response.getHeader('ETag', None) is None
      True

    Null resources
    ==============

    Additional functionality is needed to deal with null resources.

      >>> import zope.app.http.put
      >>> nullresource = zope.app.http.put.NullResource(None, 'test')

    The `If-None-Match: "*"' says that a request is valid if the resource
    corresponding to the resource does not exsist.

      >>> request = TestRequest(environ = {'IF_NONE_MATCH': '"*"'})
      >>> view = SimpleView(nullresource, request)
      >>> validator.valid(nullresource, request, view)
      True

    The `If-Match: "*"` header says that a request is valid if the resource
    corresponding the the request exsists. A null resource does not exist - it
    is a temporary non-presistent content object used as an location in the
    database that might exist, if a user PUT's data to it.

      >>> request = TestRequest(environ = {'IF_MATCH': '"*"'})
      >>> view = SimpleView(nullresource, request)
      >>> validator.valid(nullresource, request, view)
      False

    Cleanup
    -------

      >>> zope.component.getGlobalSiteManager().unregisterAdapter(
      ...    CurrentETag, (None, IBrowserRequest, None))
      True

    """
    zope.interface.implements(interfaces.IHTTPValidator)

    def parseMatchList(self, request, header):
        ret = []
        matches = request.getHeader(header, None)
        if matches is not None:
            for val in matches.split(","):
                val = val.strip()
                if val == "*":
                    ret.append(val)
                else:
                    if val[:2] == "W/":
                        val = val[2:]
                    if val[0] + val[-1] == '""' and len(val) > 2:
                        ret.append(val[1:-1])
        return ret

    def evaluate(self, context, request, view):
        return request.getHeader("If-None-Match", None) is not None or \
               request.getHeader("If-Match") is not None

    def getDataStorage(self, context, request, view):
        return zope.component.queryMultiAdapter(
            (context, request, view), interfaces.IETag)

    def _matches(self, context, request, etag, matchset):
        if "*" in matchset:
            if INullResource.providedBy(context):
                return False
            return True

        if request.get("QUERY_STRING", "") == "" and etag in matchset:
            return True

        return False

    def valid(self, context, request, view):
        etag = self.getDataStorage(context, request, view)
        if etag is not None:
            # A request can still be invalid without knowing entity tag.
            # If-Match: "*" matches everything
            etag = etag.etag

        # Test the most common validator first.
        matchset = self.parseMatchList(request, "If-None-Match")
        if matchset:
            return not self._matches(context, request, etag, matchset)

        matchset = self.parseMatchList(request, "If-Match")
        if matchset:
            return self._matches(context, request, etag, matchset)

        # Always default to True, this can happen if the requests contains
        # invalid data.
        return True

    def invalidStatus(self, context, request, view):
        if request.method in ("GET", "HEAD"):
            return 304
        else:
            # RFC2616 Section 14.26:
            # Instead, if the request method was GET or HEAD, the server
            # SHOULD respond with a 304 (Not Modified) response, including
            # the cache-related header fields (particularly ETag) of one of
            # the entities that matched.
            return 412

    def updateResponse(self, context, request, view):
        if request.response.getHeader("ETag", None) is None and \
               request.get("QUERY_STRING", "") == "":
            etag = self.getDataStorage(context, request, view)
            weak = etag and etag.weak
            etag = etag and etag.etag
            if etag:
                if weak:
                    request.response.setHeader("ETag", 'W/"%s"' % etag)
                else:
                    request.response.setHeader("ETag", '"%s"' % etag)
