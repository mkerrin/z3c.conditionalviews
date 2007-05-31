===================
z3c.condtionalviews
===================

z3c.conditionalviews is a mechanism to validate a HTTP request based on some
conditional protocol like entity tags, or last modification date. It is also
extensible so that protocols like WebDAV can define there own conditional
protocol like the IF header.

It works by implementing each conditional protocol as a `IHTTPValidator`
utility, see etag and lastmodification modules for the most common use cases.
Then when certain views are called by the publisher we lookup these utilities
and ask them to validate the request object according to whatever protocol
the utility implements.

At the time of the view is called, and when we validate the request, we
generally have access to the context, request and view itself. So the
`IHTTPValidator` utilities generally adapt these 3 objects to an object
implementing an interface specific to the protocol in question. For example
the entity tag validator looks up an adapter implementing `IEtag`.

Integration with Zope
=====================

  >>> import zope.component
  >>> import zope.interface
  >>> import z3c.conditionalviews.interfaces
  >>> import z3c.conditionalviews.tests

Decorator
---------

In order to integrate common browser views that can be cached, we can decorate
the views call method with the `z3c.conditionalviews.ConditionalView` object.
Note that all the views used in this test are defined in the ftesting.zcml
file.

  >>> response = http(r"""
  ... GET /@@simpleview.html HTTP/1.1
  ... Host: localhost
  ... """, handle_errors = False)
  >>> response.getStatus()
  200
  >>> response.getHeader('content-length')
  '82'
  >>> response.getHeader('content-type')
  'text/plain'
  >>> print response.getBody()
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Since we haven't yet defined an adapter implementing IETag, the response
contains no ETag header.

  >>> response.getHeader('ETag') is None
  True

Define our IETag implementation.

  >>> class SimpleEtag(object):
  ...    zope.interface.implements(z3c.conditionalviews.interfaces.IETag)
  ...    def __init__(self, context, request, view):
  ...        pass
  ...    weak = False
  ...    etag = "3d32b-211-bab57a40"

  >>> zope.component.getGlobalSiteManager().registerAdapter(
  ...    SimpleEtag,
  ...    (zope.interface.Interface,
  ...     zope.publisher.interfaces.browser.IBrowserRequest,
  ...     zope.interface.Interface))

  >>> response = http(r"""
  ... GET /@@simpleview.html HTTP/1.1
  ... Host: localhost
  ... """, handle_errors = False)
  >>> response.getStatus()
  200
  >>> response.getHeader('content-length')
  '82'
  >>> response.getHeader('content-type')
  'text/plain'
  >>> response.getHeader('ETag')
  '"3d32b-211-bab57a40"'
  >>> print response.getBody()
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

Now by setting the request header If-None-Match: "3d32b-211-bab57a40", our
view fails the validation and a 304 response is returned.

  >>> response = http(r"""
  ... GET /@@simpleview.html HTTP/1.1
  ... Host: localhost
  ... If-None-Match: "3d32b-211-bab57a40"
  ... """, handle_errors = False)
  >>> response.getStatus()
  304
  >>> response.getHeader('ETag')
  '"3d32b-211-bab57a40"'
  >>> response.getBody()
  ''

XXX - this seems wrong the content-length and content-type should not be set
for this response.

  >>> response.getHeader('content-length')
  '0'
  >>> response.getHeader('content-type')
  'text/plain'

Now make sure that we haven't broken the publisher, by making sure that we
can still pass arguments to the different views.

  >>> response = http(r"""
  ... GET /@@simpleview.html?letter=y HTTP/1.1
  ... Host: localhost
  ... """, handle_errors = False)
  >>> response.getStatus()
  200
  >>> response.getHeader('content-length')
  '82'
  >>> print response.getBody()
  yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
  yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy

We are now getting a charset value for this request because the default
value for the SimpleView is not a unicode string, while the data received
from the request is automatically converted to unicode by default.

  >>> response.getHeader('content-type')
  'text/plain;charset=utf-8'

Since there is a query string present in the request, we don't set the ETag
header.

  >>> response.getHeader('ETag') is None
  True

The query string present in the following request causes the request to
be valid, otherwise it would be invalid.

  >>> response = http(r"""
  ... GET /@@simpleview.html?letter=y HTTP/1.1
  ... If-None-Match: "3d32b-211-bab57a40"
  ... Host: localhost
  ... """, handle_errors = False)
  >>> response.getStatus()
  200

Generic HTTP conditional publication
====================================

We can integrate the validation method with the publication call method. This
as the effect of trying to validate every request that passes through the
publications `callObject` method. This is useful to validate requests that
modify objects so that the client can say modify this resource if it hasn't
changed since it last downloaded the resource, or if there is no existing
resource at a location.

This has the added benifit in that we don't have to specify how some one
implements the PUT method.

  >>> resp = http(r"""
  ... PUT /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... Content-type: text/plain
  ... Content-length: 55
  ... aaaaaaaaaa
  ... aaaaaaaaaa
  ... aaaaaaaaaa
  ... aaaaaaaaaa
  ... aaaaaaaaaa""", handle_errors = False)
  >>> resp.getStatus()
  201
  >>> resp.getHeader('Content-length')
  '0'
  >>> resp.getHeader('Location')
  'http://localhost/testfile'
  >>> resp.getHeader('ETag', None) is None
  True
 
We can now get the resource and the entity tag.

  >>> resp = http(r"""
  ... GET /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  200
  >>> resp.getHeader('ETag')
  '"testfile:1"'
  >>> print resp.getBody()
  aaaaaaaaaa
  aaaaaaaaaa
  aaaaaaaaaa
  aaaaaaaaaa
  aaaaaaaaaa

We could have used the HEAD method to get the entity tag.

  >>> resp = http(r"""
  ... HEAD /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  200
  >>> resp.getHeader('ETag')
  '"testfile:1"'

With no 'If-None-Match' header we override the data.

  >>> resp = http(r"""
  ... PUT /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... Content-type: text/plain
  ... Content-length: 55
  ... bbbbbbbbbb
  ... bbbbbbbbbb
  ... bbbbbbbbbb
  ... bbbbbbbbbb
  ... bbbbbbbbbb""", handle_errors = False)
  >>> resp.getStatus()
  200
  >>> resp.getHeader('Content-length')
  '0'
  >>> resp.getHeader('Location', None) is None
  True
  >>> resp.getHeader('ETag')
  '"testfile:2"'

  >>> resp = http(r"""
  ... GET /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  200
  >>> print resp.getBody()
  bbbbbbbbbb
  bbbbbbbbbb
  bbbbbbbbbb
  bbbbbbbbbb
  bbbbbbbbbb

Specifying a `If-None-Match: "*"` header, says to upload the data only if there
is no resource at the location specified in the request URI. If there is a
resource at the location then a `412 Precondition Failed` response is
returned and the resource is not modified'

  >>> resp = http(r"""
  ... PUT /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... If-None-Match: "*"
  ... Content-type: text/plain
  ... Content-length: 55
  ... cccccccccc
  ... cccccccccc
  ... cccccccccc
  ... cccccccccc
  ... cccccccccc""")
  >>> resp.getStatus()
  412
  >>> resp.getHeader('Content-length')
  '0'
  >>> resp.getHeader('Location', None) is None
  True
  >>> resp.getHeader('ETag')
  '"testfile:2"'

The file does not change.

  >>> resp = http(r"""
  ... GET /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  200
  >>> print resp.getBody()
  bbbbbbbbbb
  bbbbbbbbbb
  bbbbbbbbbb
  bbbbbbbbbb
  bbbbbbbbbb

And now since testfile2 does exist yet we content the content.

  >>> resp = http(r"""
  ... PUT /testfile2 HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... If-None-Match: "*"
  ... Content-type: text/plain
  ... Content-length: 55
  ... yyyyyyyyyy
  ... yyyyyyyyyy
  ... yyyyyyyyyy
  ... yyyyyyyyyy
  ... yyyyyyyyyy""")
  >>> resp.getStatus()
  201
  >>> resp.getHeader('Content-length')
  '0'
  >>> resp.getHeader('Location')
  'http://localhost/testfile2'
  >>> resp.getHeader('ETag', None) is None # No etag adapter is configured
  True

  >>> resp = http(r"""
  ... GET /testfile2 HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  200
  >>> print resp.getBody()
  yyyyyyyyyy
  yyyyyyyyyy
  yyyyyyyyyy
  yyyyyyyyyy
  yyyyyyyyyy

We can now delete the resource, only if it hasn't changed. So for the
'/testfile' resource we can use its first entity tag to confirm this.

  >>> resp = http(r"""
  ... DELETE /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... If-Match: "testfile:1"
  ... """)
  >>> resp.getStatus()
  412

And the file still exists.

  >>> resp = http(r"""
  ... GET /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  200

But using a valid entity tag we can delete the resource.

  >>> resp = http(r"""
  ... DELETE /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... If-Match: "testfile:2"
  ... """)
  >>> resp.getStatus()
  200
  >>> resp.getBody()
  ''

  >>> resp = http(r"""
  ... GET /testfile HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  404

Method not allowed
==================

We should still get a `405 Method Not Allowed` status for methods that aren't
registered yet.

We need to be logged in order to traverse to the file.

  >>> resp = http(r"""
  ... FROG /testfile2 HTTP/1.1
  ... Authorization: Basic mgr:mgrpw
  ... """)
  >>> resp.getStatus()
  405
  >>> resp.getHeader('ETag', None) is None
  True

Cleanup
=======

  >>> zope.component.getGlobalSiteManager().unregisterAdapter(
  ...    SimpleEtag,
  ...    (zope.interface.Interface,
  ...     zope.publisher.interfaces.browser.IBrowserRequest,
  ...     zope.interface.Interface))
  True
