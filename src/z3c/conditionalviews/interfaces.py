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

from zope import interface
from zope import schema

class IETag(interface.Interface):
    """
    Entity tags are used for comparing two or more entities from the same
    requested view.

    Used by the .etag.ETagValidator to validate a request against `If-Match`
    and `If-None-Match` conditional HTTP headers.
    """

    weak = interface.Attribute("""
    Boolean value indicated that the entity tag is weak.
    """)

    etag = interface.Attribute("""
    The current entity tag of this view.
    """)


class ILastModificationDate(interface.Interface):
    """
    Used by the ModificationSinceValidator to adapt a view in order to
    validate the `If-Modified-Since` and `If-UnModified-Since` conditional
    HTTP headers.
    """

    lastmodified = schema.Datetime(
        title = u"Last modification date",
        description = u"Indicates the last time this view last changed.",
        required = False)


class IHTTPValidator(interface.Interface):
    """
    This adapter is responsible for validating a HTTP request against one
    or more conditional headers.

    When a view is called then for each validator that is registered with
    the system, all validators that could possible return False, that is
    their `evaluate` method returns True are counted. And if the number
    of validators whose evaluate method returns True equals the number
    of validators who say that the request is invalid (i.e. the valid
    method returns False) then the request is considered invalid by this 
    package.

    When a request is invalid then the `invalidStatus` method is called to
    set the status code of the response and the view we are adapter is not
    called.

    If a request is valid then the view we adapted is called.

    In both situations, after the view is called or the `invalidStatus`
    then the `updateResponse` method is called for each registered validators.
    This method should (if not present) add a validator HTTP header to
    the response, so clients know how to make a request conditional.
    """

    def evaluate(context, request, view):
        """
        Return `True` if this request is a conditional request and this
        validator knows can validate the request.
        """

    def valid(context, request, view):
        """
        Return `True` request is valid and should be executed.

        If the request is not valid then the `invalidStatus` method will
        be called.

        By default this method should always return `True`.
        """

    def invalidStatus(context, request, view):
        """
        Return the integer status of that the response should be considering
        that this validator evaluated the request as invalid.

        If more then more validator are involved in failing a request then
        the first validator used will in the validation algorithm will be
        used. This isn't ideal but in practice, this problem is unlikely to
        show up.
        """

    def updateResponse(context, request, view):
        """
	This method is always called, and should set a HTTP header informing
        the current data needed to invalid a request the next time they
        request the adapted view.
        """
