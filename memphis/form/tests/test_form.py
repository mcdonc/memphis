import unittest
from pyramid.httpexceptions import HTTPForbidden


class TestFormWidgets(unittest.TestCase):
    def _makeOne(self, fields, form, request):
        from memphis.form.form import FormWidgets
        return FormWidgets(fields, form, request)

    def test_ctor(self):
        request = DummyRequest()
        form = DummyForm()
        fields = DummyFields()
        inst = self._makeOne(fields, form, request)
        self.assertEqual(inst.fields, fields)
        self.assertEqual(inst.form, form)
        self.assertEqual(inst.request, request)


class TestForm(unittest.TestCase):

    def test_basics(self):
        from memphis.form.form import Form

        request = DummyRequest()
        form = Form(None, request)
        
        request.url = '/test/form'
        self.assertEqual(form.action, request.url)

        self.assertEqual(form.name, 'form')

        form = Form(None, request)
        form.prefix = 'my.test.form.'
        self.assertEqual(form.name, 'my.test.form')

        self.assertEqual(form.id, 'my-test-form')

    def test_getContent(self):
        from memphis.form.form import Form

        request = DummyRequest()
        form = Form(None, request)

        self.assertIsNone(form.getContent())

        form_content = {}
        form.content = form_content
        self.assertIs(form.getContent(), form_content)

    def test_csrf_token(self):
        from memphis.form import form

        class MyForm(form.Form):
            pass

        request = DummyRequest()
        form_ob = MyForm(None, request)

        self.assertIsNone(form.CSRF)
        self.assertIsNone(form_ob.token)
        
        retData = False
        class CsrfService(object):
            def generate(self, data):
                return 'csrf-token:%s'%data
            def get(self, token):
                if retData:
                    return token.split(':', 1)[-1]

        form.setCsrfUtility(CsrfService())

        token = form_ob.token
        self.assertIsNotNone(token)
        self.assertIsNone(form_ob.validateToken())

        request.POST = {}

        form_ob.csrf = True
        self.assertRaises(HTTPForbidden, form_ob.validateToken)
        self.assertRaises(HTTPForbidden, form_ob.validate, {}, [])

        request.POST = {form_ob.csrfname: token}
        self.assertRaises(HTTPForbidden, form_ob.validateToken)

        retData = True
        self.assertIsNone(form_ob.validateToken())

    def test_csrf_tokenData(self):
        from memphis.form import form

        class MyForm(form.Form):
            pass

        request = DummyRequest()
        form_ob = MyForm(None, request)

        self.assertEqual(form_ob.tokenData, 'test_form.MyForm:None')

        def authId(request):
            return 'userId'

        orig_func = form.security.authenticated_userid
        form.security.authenticated_userid = authId

        form_ob = MyForm(None, request)
        self.assertEqual(form_ob.tokenData, 'test_form.MyForm:userId')

        form.security.authenticated_userid = orig_func

    def test_getParams(self):
        from memphis.form.form import Form, DisplayForm

        request = DummyRequest()

        form = Form(None, request)
        disp_form = DisplayForm(None, request)

        self.assertEqual(form.method, 'post')

        post = {'post': 'info'}
        request.POST = post

        self.assertIs(form.getParams(), post)
        self.assertIs(disp_form.getParams(), Form.params)

        get = {'get': 'info'}
        request.GET = get
        form.method = 'get'
        self.assertIs(form.getParams(), get)

        form.method = 'unknown'
        self.assertEqual(dict(form.getParams()), {})

    def test_form_params_method(self):
        from memphis.form.form import Form

        form = Form(None, None)
        form.method = 'params'
        params = {'post': 'info'}
        form.params = params

        self.assertIs(form.getParams(), params)

    def test_form_mode(self):
        from memphis.form.form import Form, DisplayForm, \
            FORM_INPUT, FORM_DISPLAY

        request = DummyRequest()

        form = Form(None, request)
        self.assertEqual(form.mode, FORM_INPUT)

        form = DisplayForm(None, request)
        self.assertEqual(form.mode, FORM_DISPLAY)

    def test_form_update_widgets(self):
        from memphis import form

        request = DummyRequest()
        request.POST = {}

        form_ob = form.Form(None, request)
        form_ob.update()

        self.assertIsInstance(form_ob.widgets, form.FormWidgets)
        self.assertEqual(form_ob.widgets.mode, form_ob.mode)
        
        form_ob.mode = form.FORM_DISPLAY
        form_ob.update()
        self.assertEqual(form_ob.widgets.mode, form.FORM_DISPLAY)

        self.assertEqual(len(form_ob.widgets), 0)

        form_ob.fields = form.Fieldset(form.TextField('test'))
        form_ob.update()
        self.assertEqual(len(form_ob.widgets), 1)
        self.assertIn('test', form_ob.widgets)

        self.assertIsInstance(form_ob.widgets['test'], form.TextField)
        self.assertEqual(form_ob.widgets['test'].name, 'test')
        self.assertEqual(form_ob.widgets['test'].id, 'form-widgets-test')

    def test_form_extract(self):
        from memphis import form

        request = DummyRequest()
        request.POST = {}

        form_ob = form.Form(None, request)
        form_ob.fields = form.Fieldset(form.TextField('test'))
        form_ob.update()

        data, errors = form_ob.extract()
        self.assertEqual(errors[0].msg, 'Required')

        request.POST = {'test': 'Test string'}
        form_ob.update()
        data, errors = form_ob.extract()
        self.assertEqual(data['test'], 'Test string')

    def test_form_render(self):
        from memphis import form

        request = DummyRequest()

        form_ob = form.Form(None, request)
        form_ob.fields = form.Fieldset(form.TextField('test'))
        form_ob.update()

        html = form_ob.render()
        
        def template(**data):
            return 'Form rendered'

        form_ob.template = template
        self.assertEqual(form_ob.render(), 'Form rendered')


class DummyRequest(object):
    def __init__(self):
        self.params = {}
        self.cookies = {}
        self.POST = {}
        

class DummyForm(object):
    prefix = 'prefix'
    def getParams(self): # pragma: no cover
        return None
    def getContent(self): # pragma: no cover
        return None


class DummyFieldset(object):
    def fieldsets(self): # pragma: no cover
        return []


class DummyFields(object):
    def __init__(self, fieldset=None):
        if fieldset is None:
            fieldset = DummyFieldset()
        self.fieldset = fieldset
        
    def bind(self, content, params): # pragma: no cover
        self.content = content
        self.params = params
        return self.fieldset
    

