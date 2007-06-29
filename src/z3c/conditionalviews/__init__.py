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

import zope.component
import zope.publisher.http
import zope.publisher.publish
import zope.publisher.interfaces
import zope.app.http.interfaces
import zope.app.publication.http
import zope.app.publication.interfaces

import interfaces

def validate(context, request, func, viewobj, *args, **kw):
    # count the number of invalid and evaulated validators, if evaluated is
    # greater then zero and equal to hte invalid count then the request is
    # invalid.
    evaluated = invalid = 0

    validators = [validator
                  for validator_name, validator in
                  zope.component.getUtilitiesFor(interfaces.IHTTPValidator)]

    invalidStatus = 999
    for validator in validators:
        if validator.evaluate(context, request, viewobj):
            evaluated += 1
            if not validator.valid(context, request, viewobj):
                invalid += 1
                invalidStatus = validator.invalidStatus(
                    context, request, viewobj)

    if evaluated > 0 and evaluated == invalid:
        # The request is invalid so we do not process it.
        request.response.setStatus(invalidStatus)
        result = ""
    else:
        # The request is valid so we do process it.
        result = func(viewobj, *args, **kw)

    for validator in validators:
        validator.updateResponse(context, request, viewobj)

    return result


class BoundConditionalView(object):
    def __init__(self, pt, ob):
        object.__setattr__(self, "im_func", pt)
        object.__setattr__(self, "im_self", ob)

    def __call__(self, *args, **kw):
        args = (self.im_self,) + args
        return validate(self.im_self.context, self.im_self.request,
                        self.im_func, *args, **kw)

###############################################################################
#
# Decorators to turn a specific view into a conditonal view. For example
# file downloads / upload views.
#
###############################################################################

class ConditionalView(object):
    def __init__(self, viewmethod):
        self.viewmethod = viewmethod

    def __get__(self, instance, class_):
        return BoundConditionalView(self.viewmethod, instance)

###############################################################################
#
# Generic publication object to turn a whole set of request handlers into
# conditional views.
#
###############################################################################

class ConditionalHTTPRequest(zope.publisher.http.HTTPRequest):
    zope.interface.classProvides(
        zope.app.publication.interfaces.IHTTPRequestFactory)

    def setPublication(self, publication):
        super(ConditionalHTTPRequest, self).setPublication(
            ConditionalPublication(publication))


class ConditionalPublication(object):

    def __init__(self, publication):
        self._publication = publication
        for name in zope.publisher.interfaces.IPublication:
            if name not in ("callObject",):
                setattr(self, name, getattr(publication, name))

    def callObject(self, request, ob):
        # Exception handling, dont try to call request.method
        if not zope.app.http.interfaces.IHTTPException.providedBy(ob):
            view = zope.component.queryMultiAdapter(
                (ob, request), name = request.method)
            method = getattr(view, request.method, None)
            if method is None:
                raise zope.app.publication.http.MethodNotAllowed(ob, request)

            ob = BoundConditionalView(method.im_func, method.im_self)

        return zope.publisher.publish.mapply(
            ob, request.getPositionalArguments(), request)
