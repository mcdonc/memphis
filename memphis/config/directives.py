""" directives """
import sys, inspect, imp, logging
from zope import interface
from pkgutil import walk_packages

import api

log = logging.getLogger('memphis.config')


def action(func):
    """ Execute arbitrary action during configration process. """
    info = DirectiveInfo(allowed_scope=('module', 'function call'))
    info.attach(Action(func))
    return func


class IEventDescriptor(interface.Interface):
    """ event descriptor """

    name = interface.Attribute('Name')

    title = interface.Attribute('Event title')

    category = interface.Attribute('Event category')

    instance = interface.Attribute('Event class or interface')


class EventDescriptor(object):
    interface.implements(IEventDescriptor)

    def __init__(self, inst, title, category):
        self.instance = inst
        self.title = title
        self.category = category
        self.description = inst.__doc__
        self.name = '%s.%s'%(inst.__module__, inst.__name__)


events = {}

def event(title='', category=''):
    """ Register event object, it is used for introspection only. """
    info = DirectiveInfo(allowed_scope=('class',))

    def descriminator(action):
        return ('memphis.config:event', action.info.context)

    info.attach(
        ClassAction(
            _event, (title, category),
            discriminator = descriminator)
        )

def _event(klass, title, category):
    ev = EventDescriptor(klass, title, category)
    events[klass] = ev
    events[ev.name] = ev


def adapter(*required, **kw):
    """ Register adapter """
    info = DirectiveInfo()

    required = tuple(required)
    name = kw.get('name', '')

    def descriminator(action):
        return ('memphis.config:adapter',
                required, _getProvides(action.info.context), name)

    if info.scope in ('module', 'function call'): # function decorator
        def wrapper(func):
            info.attach(
                Action(
                    _register,
                    ('registerAdapter', func, required), {'name': name},
                    discriminator = ('memphis.config:adapter',
                                     required, _getProvides(func), name))
                )
            return func
        return wrapper
    else:
        info.attach(
            ClassAction(
                _adapts, (required, name),
                discriminator = descriminator)
            )


def subscriber(*required):
    """ Register event subscriber. """
    info = DirectiveInfo(allowed_scope=('module', 'function call'))

    def wrapper(func):
        info.attach(
            Action(
                _register, ('registerHandler', func, required),
                discriminator = ('memphis.config:subscriber',
                                 func, tuple(required)))
            )
        return func
    return wrapper


def _register(methodName, *args, **kw):
    method = getattr(api.registry, methodName)
    method(*args, **kw)


def _adapts(factory, required, name):
    api.registry.registerAdapter(factory, required, name=name)


def _getProvides(factory):
    provides = None
    p = list(interface.implementedBy(factory))
    if len(p) == 1:
        return p[0]
    else:
        raise TypeError(
            "The adapter factory doesn't implement a single interface "
            "and no provided interface was specified.")


ACTIONS = {}

class Action(object):

    def __init__(self, callable, args=(), kw={},
                 discriminator=None, order=0, info=None):
        self.callable = callable
        self.args = args
        self.kw = kw
        self.order = order
        self.info = info
        self._discriminator = discriminator

    @property
    def discriminator(self):
        if callable(self._discriminator):
            return self._discriminator(self)
        return self._discriminator

    def __call__(self):
        if self.callable:
            try:
                self.callable(*self.args, **self.kw)
            except: # pragma: no cover
                log.exception(self.discriminator)
                raise


class ClassAction(Action):

    def __call__(self):
        try:
            self.callable(self.info.context, *self.args, **self.kw)
        except: # pragma: no cover
            log.exception(self.discriminator)
            raise


class DirectiveInfo(object):

    def __init__(self, depth=1, moduleLevel = False, allowed_scope=None):
        scope, module, f_locals, f_globals, codeinfo = \
            getFrameInfo(sys._getframe(depth+1))

        if allowed_scope and scope not in allowed_scope:
            raise TypeError("This directive is not allowed "
                            "to run in this scope: %s"%scope)

        if scope == 'module':
            self.name = f_locals['__name__']
        else:
            self.name = codeinfo[2]

        self.locals = f_locals
        self.scope = scope
        self.module = module
        self.codeinfo = codeinfo

        api.mods.add(self.module.__name__)

    @property
    def context(self):
        if self.scope == 'module':
            return self.module
        else:
            return getattr(self.module, self.name)

    def attach(self, action):
        action.info = self

        data = ACTIONS.setdefault(self.module.__name__, [])
        data.append(action)


def getFrameInfo(frame):
    """code from venusian package
    Return (kind,module,locals,globals) for a frame

    'kind' is one of "exec", "module", "class", "function call", or "unknown".
    """

    f_locals = frame.f_locals
    f_globals = frame.f_globals

    sameNamespace = f_locals is f_globals
    hasModule = '__module__' in f_locals
    hasName = '__name__' in f_globals

    sameName = hasModule and hasName
    sameName = sameName and f_globals['__name__']==f_locals['__module__']

    module = hasName and sys.modules.get(f_globals['__name__']) or None

    namespaceIsModule = module and module.__dict__ is f_globals

    frameinfo = inspect.getframeinfo(frame)
    try:
        sourceline = frameinfo[3][0].strip()
    except: # pragma: no cover
        sourceline = frameinfo[3]

    codeinfo = frameinfo[0], frameinfo[1], frameinfo[2], sourceline

    if not namespaceIsModule: # pragma: no cover
        # some kind of funky exec
        kind = "exec"
    elif sameNamespace and not hasModule:
        kind = "module"
    elif sameName and not sameNamespace:
        kind = "class"
    elif not sameNamespace:
        kind = "function call"
    else:  # pragma: no cover
        # How can you have f_locals is f_globals, and have '__module__' set?
        # This is probably module-level code, but with a '__module__' variable.
        kind = "unknown"
    return kind, module, f_locals, f_globals, codeinfo


def scan(package, seen, exclude_filter=None):
    if isinstance(package, basestring):
        __import__(package)
        package = sys.modules[package]

    actions = []

    pkgname = package.__name__
    if pkgname in seen:
        return actions

    seen.add(pkgname)

    if pkgname in ACTIONS:
        actions.extend(ACTIONS[pkgname])

    if hasattr(package, '__path__'): # package, not module
        results = walk_packages(package.__path__, package.__name__+'.')

        for importer, modname, ispkg in results:
            if modname in seen: # pragma: no cover
                continue

            seen.add(modname)

            if exclude_filter is not None and modname != pkgname:
                if not exclude_filter(modname):
                    continue

            loader = importer.find_module(modname)
            if loader is not None:
                module_type = loader.etc[2]
                if module_type in (imp.PY_SOURCE, imp.PKG_DIRECTORY):
                    __import__(modname)
                    module = sys.modules[modname]
                    if modname in ACTIONS:
                        actions.extend(ACTIONS[modname])

    return actions


def resolveConflicts(actions):
    # code from zope.configuration package

    # organize actions by discriminators
    unique = {}
    output = []
    for i in range(len(actions)):
        action = actions[i]
        discriminator = action.discriminator

        order = action.order or i
        a = unique.setdefault(discriminator, [])
        a.append((action.info.codeinfo[0], order, action))

    # Check for conflicts
    conflicts = {}
    for discriminator, dups in unique.items():
        # We need to sort the actions by the paths so that the shortest
        # path with a given prefix comes first:
        dups.sort()
        basepath, order, action = dups[0]

        output.append((order, action))
        if len(dups) > 1:
            conflicts[discriminator] = [action.info for _i1, _i2, action in dups]

    if conflicts:
        raise ConflictError(conflicts)

    # Now put the output back in the original order, and return it:
    r = []
    output.sort()
    for order, action in output:
        r.append(action)

    return r


class ConflictError(TypeError):

    def __init__(self, conflicts):
        self._conflicts = conflicts

    def __str__(self):
        r = ["Conflicting configuration actions\n"]
        items = self._conflicts.items()
        items.sort()
        for discriminator, infos in items:
            r.append("  For: %s\n" % (discriminator, ))
            for info in infos:
                filename, line, function, source = info.codeinfo
                s = ' File "%s", line %d, in %s\n' \
                    '      %s\n'% (filename, line, function, source)

                for line in unicode(s).rstrip().split(u'\n'):
                    r.append(u"    "+line)
                r.append(u'')

        return "\n".join(r)
