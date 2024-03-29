""" Form buttons """
import sys, re
from collections import OrderedDict
from memphis import config, view

AC_DEFAULT = 0
AC_PRIMARY = 1
AC_DANGER = 2
AC_SUCCESS = 3
AC_INFO = 4

css = {
    AC_PRIMARY: 'primary',
    AC_DANGER: 'danger',
    AC_SUCCESS: 'success',
    AC_INFO: 'info'}


class Button(object):
    """A simple button in a form."""

    lang = None
    readonly = False
    alt = None
    accesskey = None
    disabled = False
    tabindex = None
    klass = u'btn'

    template = view.template("memphis.form:templates/submit.pt")

    def __init__(self, name='submit', title=None, action=None, actionName=None,
                 actype=AC_DEFAULT, condition=None, **kw):
        self.__dict__.update(kw)

        if title is None:
            title = name.capitalize()
        name = re.sub(r'\s', '_', name)

        self.name = name
        self.title = title
        self.action = action
        self.actionName = actionName
        self.actype = actype
        self.condition = condition

    def __repr__(self):
        return '<%s %r : %r>' %(
            self.__class__.__name__, self.name, self.title)

    def __call__(self, context):
        if self.actionName is not None:
            return getattr(context, self.actionName)()
        elif self.action is not None:
            return self.action(context)
        else:
            raise TypeError("Action is not specified")

    def bind(self, prefix, params, context, request):
        widget = self.__class__.__new__(self.__class__)
        widget.__dict__.update(self.__dict__)

        widget.id = str(prefix + widget.name).replace('.', '-')
        widget.name = str(prefix + widget.name)
        widget.params = params
        widget.context = context
        widget.request = request
        widget.klass = u'%s %s'%(widget.klass, css.get(widget.actype, ''))
        return widget

    def activated(self):
        return self.params.get(self.name, None) is not None

    def render(self):
        return self.template(
            context = self,
            request = self.request)


class Buttons(OrderedDict):
    """Buttons manager"""

    def __init__(self, *args):
        super(Buttons, self).__init__()

        buttons = []
        for arg in args:
            if isinstance(arg, Buttons):
                buttons += arg.values()
            else:
                buttons.append(arg)

        self.add(*buttons)

    def add(self, *btns):
        for btn in btns:
            if btn.name in self:
                raise ValueError("Duplicate name", btn.name)

            self[btn.name] = btn

    def addAction(self, title, **kwargs):
        # Add the title to button constructor keyword arguments
        kwargs['title'] = title
        if 'name' not in kwargs:
            kwargs['name'] = createId(title)

        button = Button(**kwargs)

        self.add(button)

        return button

    def __add__(self, other):
        return self.__class__(self, other)


class Actions(OrderedDict):
    """Form actions manager"""

    prefix = 'buttons.'

    def __init__(self, form, request):
        self.form = form
        self.request = request

        super(Actions, self).__init__()

    def update(self):
        form = self.form
        params = form.getParams()

        # Create a unique prefix.
        prefix = '%s%s'%(form.prefix, self.prefix)

        # Walk through each node, making a widget out of it.
        for field in self.form.buttons.values():
            if field.condition and not field.condition(form):
                continue

            self[field.name] = field.bind(prefix, params, form, self.request)

    def execute(self):
        executed = False
        for action in self.values():
            if action.activated():
                executed = True
                action(self.form)

        if executed:
            self.clear()
            self.update()


_identifier = re.compile('[A-Za-z][a-zA-Z0-9_]*$')

def createId(name):
    if _identifier.match(name):
        return str(name).lower()
    return name.encode('utf-8').encode('hex')


def button(title, **kwargs):
    # install buttons manager
    f_locals = sys._getframe(1).f_locals

    buttons = f_locals.get('buttons')
    if buttons is None:
        buttons = Buttons()
        f_locals['buttons'] = buttons

    btn = buttons.addAction(title, **kwargs)

    def createHandler(func):
        btn.actionName = func.__name__
        return func

    return createHandler
