"""
A few bits of helper functions for comment views.
"""

from future import standard_library
standard_library.install_aliases()
import urllib.request, urllib.parse, urllib.error
import textwrap
from django.http import HttpResponseRedirect
from django.core import urlresolvers
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import comments

def next_redirect(data, default, default_view, **get_kwargs):
    """
    Handle the "where should I go next?" part of comment views.

    The next value could be a kwarg to the function (``default``), or a
    ``?next=...`` GET arg, or the URL of a given view (``default_view``). See
    the view modules for examples.

    Returns an ``HttpResponseRedirect``.
    """
    next = data.get("next", default)
    if next is None:
        next = urlresolvers.reverse(default_view)
    if get_kwargs:
        if '#' in next:
            tmp = next.rsplit('#', 1)
            next = tmp[0]
            anchor = '#' + tmp[1]
        else:
            anchor = ''

        joiner = ('?' in next) and '&' or '?'
        next += joiner + urllib.parse.urlencode(get_kwargs) + anchor
    return HttpResponseRedirect(next)

def confirmation_view(template, doc="Display a confirmation view."):
    """
    Confirmation view generator for the "comment was
    posted/flagged/deleted/approved" views.
    """
    def confirmed(request):
        comment = None
        if 'c' in request.GET:
            try:
                comment = comments.get_model().objects.get(pk=request.GET['c'])
            except (ObjectDoesNotExist, ValueError):
                pass
        return render_to_response(template,
            {'comment': comment},
            context_instance=RequestContext(request)
        )

    confirmed.__doc__ = textwrap.dedent("""\
        %s

        Templates: `%s``
        Context:
            comment
                The posted comment
        """ % (doc, template)
    )
    return confirmed
