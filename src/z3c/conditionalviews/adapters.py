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
import zope.dublincore.interfaces

import interfaces

class LastModificationDate(object):
    """
      >>> import datetime
      >>> import zope.component
      >>> import zope.publisher.browser
      >>> from zope.interface.verify import verifyObject

      >>> lmt = datetime.datetime(2007, 3, 2, 13, 34, 23)
      >>> class SimpleContent(object):
      ...    def __init__(self):
      ...        self.lastmodified = lmt

      >>> class DublinCore(object):
      ...    zope.interface.implements(
      ...        zope.dublincore.interfaces.IZopeDublinCore)
      ...    zope.component.adapts(SimpleContent)
      ...    def __init__(self, context):
      ...        self.context = context
      ...    @property
      ...    def modified(self):
      ...        return self.context.lastmodified

      >>> zope.component.getGlobalSiteManager().registerAdapter(DublinCore)

      >>> class SimpleView(zope.publisher.browser.BrowserView):
      ...    pass

      >>> content = SimpleContent()

    Adapting our simple view goes us our desired result.

      >>> validatordata = LastModificationDate(
      ...    content, None, SimpleView(content, None))
      >>> verifyObject(interfaces.ILastModificationDate, validatordata)
      True
      >>> validatordata.lastmodified == lmt
      True

    Cleanup

      >>> zope.component.getGlobalSiteManager().unregisterAdapter(DublinCore)
      True

    """
    zope.interface.implements(interfaces.ILastModificationDate)

    def __init__(self, context, request, view):
        self.dcadapter = zope.dublincore.interfaces.IDCTimes(context)

    @property
    def lastmodified(self):
        return self.dcadapter.modified
