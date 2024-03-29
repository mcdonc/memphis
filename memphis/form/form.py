"""Form implementation"""
from zope import interface
from collections import OrderedDict
from pyramid import security
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPForbidden
from webob.multidict import UnicodeMultiDict, MultiDict

from memphis import view, config
from memphis.form.field import Field, Fieldset
from memphis.form.button import Buttons, Actions
from memphis.form.interfaces import _, Invalid, FORM_INPUT, FORM_DISPLAY
from memphis.form.interfaces import IForm, IInputForm, IDisplayForm

CSRF = None

def setCsrfUtility(util):
    global CSRF
    CSRF = util


class FormErrorMessage(view.Message):
    config.adapter(None, name='form-error')

    formErrorsMessage = _(u'Please fix indicated errors.')

    template = view.template('memphis.form:templates/form-error.pt')

    def render(self, message):
        self.errors = [
            err for err in message
            if not isinstance(err, Invalid) or err.field is None]

        return self.template(
            message = self.formErrorsMessage,
            errors = self.errors,
            request = self.request)


class FormWidgets(OrderedDict):

    mode = FORM_INPUT
    prefix = 'widgets.'
    fieldsets = ()

    def __init__(self, fields, form, request):
        self.fields = fields
        self.form = form
        self.request = request

        super(FormWidgets, self).__init__()

    def update(self):
        params = self.form.getParams()
        content = self.form.getContent()
        prefix = '%s%s'%(self.form.prefix, self.prefix)
        
        self.fieldset = self.fields.bind(content, params)
        self.fieldsets = fieldsets = []

        # Walk through each field, making a widget out of it.
        for fieldset in self.fieldset.fieldsets():
            widgets = []

            for widget in fieldset.fields():
                if widget.mode is None:
                    widget.mode = self.mode
                widget.id = ('%s%s'%(prefix, widget.name)).replace('.', '-')
                widget.update(self.request)
                widgets.append(widget)
                self[widget.name] = widget

            fieldsets.append(
                {'fieldset': fieldset,
                 'name': fieldset.name,
                 'legend': fieldset.legend,
                 'widgets': widgets})

    def extract(self):
        data, errors = self.fieldset.extract()

        # additional form validation
        self.form.validate(data, errors)

        # set errors to fields
        for err in errors:
            if isinstance(err.field, Field) and err.field.error is None:
                err.field.error = err

        return data, errors


class Form(view.View):
    """A form

    """

    interface.implements(IForm, IInputForm)

    fields = Fieldset()
    buttons = None

    #: Form label
    label = None

    #: Form description
    description = ''

    #: Form prefix, it used for html elements `id` generations.
    prefix = 'form.'

    #: Instance of py:class:`memphis.form.Actions` class
    actions = None

    #: Instance of py:class:`FormWidgets` class
    widgets  = None

    #: Form content, it should be `None` or dictionary with data for fields.
    content = None

    #: Form mode. It can be py:data::`memphis.form.FORM_INPUT` or 
    #: py:data::`memphis.form.FORM_DISPLAY`
    mode = FORM_INPUT

    method = 'post'
    enctype = 'multipart/form-data'
    accept = None
    acceptCharset = None

    csrf = False
    csrfname = 'csrf-token'

    params = UnicodeMultiDict(MultiDict({}), 'utf-8')

    def __init__(self, context, request):
        super(Form, self).__init__(context, request)

        if self.buttons is None:
            self.buttons = Buttons()

    @reify
    def action(self):
        return self.request.url

    @reify
    def name(self):
        return self.prefix.strip('.')

    @reify
    def id(self):
        return self.name.replace('.', '-')

    def getContent(self):
        return self.content

    def getParams(self):
        if self.method == 'post':
            return self.request.POST
        elif self.method == 'get':
            return self.request.GET
        elif self.method == 'params':
            return self.params
        else:
            return self.params

    def updateWidgets(self):
        self.widgets = FormWidgets(self.fields, self, self.request)
        self.widgets.mode = self.mode
        self.widgets.update()

    def updateActions(self):
        self.actions = Actions(self, self.request)
        self.actions.update()

    @property
    def token(self):
        if CSRF is not None:
            return CSRF.generate(self.tokenData)

    @reify
    def tokenData(self):
        return '%s.%s:%s'%(self.__module__,self.__class__.__name__,
                           security.authenticated_userid(self.request))

    def validate(self, data, errors):
        self.validateToken()

    def validateToken(self):
        # check csrf token
        if self.csrf:
            token = self.getParams().get(self.csrfname, None)
            if token is not None:
                if CSRF is not None:
                    if CSRF.get(token) == self.tokenData:
                        return

            raise HTTPForbidden("Form authenticator is not found.")

    def extract(self):
        return self.widgets.extract()

    def update(self):
        self.updateWidgets()
        self.updateActions()

        self.actions.execute()

    def render(self):
        if self.template is None:
            return self.pagelet(FORM_VIEW, self)

        kwargs = {'view': self,
                  'context': self.context,
                  'request': self.request}

        return self.template(**kwargs)


class DisplayForm(Form):
    interface.implements(IDisplayForm)

    mode = FORM_DISPLAY

    def getParams(self):
        return self.params


FORM_VIEW = 'form-view'
FORM_ACTIONS = 'form-actions'
FORM_WIDGET = 'form-widget'
FORM_DISPLAY_WIDGET = 'form-display-widget'

view.pageletType(FORM_VIEW, IForm, 'Form view')
view.pageletType(FORM_ACTIONS, IForm, 'Form actions')
view.pageletType(FORM_WIDGET, Field, 'Form widget')
view.pageletType(FORM_DISPLAY_WIDGET, Field, 'Form display widget')

view.registerPagelet(
    'form-view', IInputForm,
    template = view.template('memphis.form:templates/form.pt'))

view.registerPagelet(
    'form-view', IDisplayForm,
    template = view.template('memphis.form:templates/form-display.pt'))

view.registerPagelet(
    'form-actions', IInputForm,
    template = view.template('memphis.form:templates/form-actions.pt'))

view.registerPagelet(
    'form-widget', Field,
    template = view.template('memphis.form:templates/widget.pt'))

view.registerPagelet(
    'form-display-widget', Field,
    template = view.template('memphis.form:templates/widget-display.pt'))
