""" routes """
from zope import interface
from pyramid.config.util import make_predicates
from pyramid.request import route_request_iface
from pyramid.traversal import DefaultRootFactory
from pyramid.urldispatch import RoutesMapper
from pyramid.interfaces import IRequest, IRouteRequest, IRoutesMapper

from memphis import config
from memphis.view.interfaces import INavigationRoot

# mark pyramid's DefaultRootFactory with INavigationRoot
interface.classImplements(DefaultRootFactory, INavigationRoot)


def registerRoute(name, pattern=None, factory=None, header=None,
                  traverse=None, pregenerator=None, use_global_views=False,
                  xhr=False, request_method=None,
                  path_info=None, request_param=None,
                  accept=None, custom_predicates=()):

    # these are route predicates; if they do not match, the next route
    # in the routelist will be tried
    ignored, predicates, ignored = make_predicates(
        xhr=xhr,
        request_method=request_method,
        path_info=path_info,
        request_param=request_param,
        header=header,
        accept=accept,
        traverse=traverse,
        custom=custom_predicates)

    info = config.DirectiveInfo()
    info.attach(
        config.Action(
            registerRouteImpl,
            (name,pattern,factory,predicates,pregenerator,use_global_views),
            discriminator = ('memphis.view:route', name),
            order = 1))


def registerRouteImpl(name, pattern, factory,
                      predicates, pregenerator, use_global_views):
    request_iface = config.registry.queryUtility(IRouteRequest, name=name)
    if request_iface is None:
        if use_global_views:
            bases = (IRequest,)
        else:
            bases = ()
        request_iface = route_request_iface(name, bases)
        config.registry.registerUtility(request_iface, IRouteRequest, name=name)

    mapper = config.registry.queryUtility(IRoutesMapper)
    if mapper is None:
        mapper = RoutesMapper()
        config.registry.registerUtility(mapper, IRoutesMapper)

    return mapper.connect(name, pattern, factory, predicates=predicates,
                          pregenerator=pregenerator, static=False)
