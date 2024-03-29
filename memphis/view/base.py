""" base view class with access to various api's """
import logging
from zope import interface
from memphis import config
from memphis.view.formatter import format
from memphis.view.resources import static, static_url
from memphis.view.message import addMessage, renderMessages
from memphis.view.library import library, include, renderIncludes
from memphis.view.interfaces import IPagelet, IMemphisView, INavigationRoot

log = logging.getLogger('memphis.view')


class View(object):
    interface.implements(IMemphisView)

    __name__ = ''
    __parent__ = None

    format = format
    template = None

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context

    def update(self):
        return {}

    def render(self):
        params = self.update()

        if self.template is not None:
            kwargs = {'view': self,
                      'context': self.context,
                      'request': self.request}
            if type(params) is dict:
                kwargs.update(params)
            return self.template(**kwargs)

        return u''

    def include(self, name):
        include(name, self.request)

    def renderIncludes(self):
        return renderIncludes(self.request)

    def message(self, msg, type='info'):
        return addMessage(self.request, msg, type)

    def renderMessages(self):
        return renderMessages(self.request)

    def static_url(self, name, path=''):
        return static_url(name, path, self.request)

    def pagelet(self, ptype, context=None):
        if context is None:
            context = self.context

        try:
            pagelet = config.registry.queryMultiAdapter(
                (context, self.request), IPagelet, ptype)
            if pagelet is not None:
                return pagelet()
        except Exception, e:
            log.exception(str(e))

        return u''


static('jquery', 'memphis.view:static/jquery')

library(
    'jquery',
    path="jquery-1.6.4.min.js",
    resource="jquery",
    type="js")

library(
    'jquery-ui',
    path="jquery-ui-1.8.16.min.js",
    type="js",
    resource="jquery",
    require="jquery")

library(
    'jquery-ui',
    path="jquery-ui.css",
    resource="jquery",
    type='css')


static('bootstrap', 'memphis.view:static/bootstrap')

library(
    'lesscss',
    path="less-1.1.3.min.js",
    resource="bootstrap",
    type="js")

library(
    'bootstrap',
    path="bootstrap-1.3.0.min.css",
    resource="bootstrap",
    type="css")

library(
    'bootstrap-js',
    path="bootstrap-1.3.0.js",
    resource="bootstrap",
    type="js",
    require="jquery")

library(
    'bootstrap-less',
    path="lib/bootstrap.less",
    resource="bootstrap",
    type="css",
    extra={'rel': 'stylesheet/less'})
