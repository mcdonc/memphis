import decimal
import unittest
from memphis import form
from webob.multidict import MultiDict

from base import Base


class DummyRequest(object):
    def __init__(self):
        self.params = {}
        self.cookies = {}
        

def invalid_exc(func, *arg, **kw):
    from memphis.form import Invalid
    try:
        func(*arg, **kw)
    except Invalid, e:
        return e
    else:
        raise AssertionError('Invalid not raised') # pragma: no cover


def strip(str):
    return ' '.join(s.strip() for s in str.split())


class TestTextField(Base):

    def _makeOne(self, name, **kw):
        return form.TextField(name, **kw)

    def test_fields_text(self):
        request = DummyRequest()

        field = self._makeOne('test')
        field = field.bind('', u'content', {})
        field.update(request)

        self.assertEqual(field.serialize(u'value'), u'value')
        self.assertEqual(field.deserialize(u'value'), u'value')
        
        self.assertEqual(strip(field.render(request)),
                         '<input type="text" name="test" title="Test" value="content" id="test" class="text-widget" />')

        field.mode = form.FORM_DISPLAY
        self.assertEqual(strip(field.render(request)),
                         '<span class="uneditable-input" id="test" title="Test"> content </span>')

        
        field = self._makeOne('test')
        field = field.bind('', u'content', {'test': 'form'})
        field.update(request)

        self.assertEqual(strip(field.render(request)),
                         '<input type="text" name="test" title="Test" value="form" id="test" class="text-widget" />')

        field.mode = form.FORM_DISPLAY
        self.assertEqual(strip(field.render(request)),
                         '<span class="uneditable-input" id="test" title="Test"> form </span>')


class TestIntegerField(Base):

    def _makeOne(self, name, **kw):
        return form.IntegerField(name, **kw)

    def test_fields_int(self):
        request = DummyRequest()

        field = self._makeOne('test')
        field = field.bind('', 10, {})
        field.update(request)

        self.assertIs(field.serialize(form.null), form.null)
        self.assertEqual(field.serialize(10), '10')
        self.assertRaises(form.Invalid, field.serialize, u'value')

        self.assertIs(field.deserialize(''), form.null)
        self.assertEqual(field.deserialize('10'), 10)
        self.assertRaises(form.Invalid, field.deserialize, u'value')

        self.assertEqual(
            strip(field.render(request)),
            '<input type="text" name="test" title="Test" value="10" id="test" class="int-widget" />')

class TestFloatField(Base):

    def _makeOne(self, name, **kw):
        return form.FloatField(name, **kw)

    def test_fields_float(self):
        request = DummyRequest()

        field = self._makeOne('test')
        field = field.bind('', 10.34, {})
        field.update(request)

        self.assertIs(field.serialize(form.null), form.null)
        self.assertEqual(field.serialize(10.34), '10.34')
        self.assertRaises(form.Invalid, field.serialize, u'value')

        self.assertIs(field.deserialize(''), form.null)
        self.assertEqual(field.deserialize('10.34'), 10.34)
        self.assertRaises(form.Invalid, field.deserialize, u'value')

        self.assertEqual(
            strip(field.render(request)),
            '<input type="text" name="test" title="Test" value="10.34" id="test" class="float-widget" />')


class TestDeciamlField(Base):

    def _makeOne(self, name, **kw):
        return form.DecimalField(name, **kw)

    def test_fields_decimal(self):
        request = DummyRequest()

        field = self._makeOne('test')
        field = field.bind('', decimal.Decimal('10.34'), {})
        field.update(request)

        self.assertIs(field.serialize(form.null), form.null)
        self.assertEqual(field.serialize(decimal.Decimal('10.34')), '10.34')
        self.assertRaises(form.Invalid, field.serialize, u'value')

        self.assertIs(field.deserialize(''), form.null)
        self.assertEqual(field.deserialize('10.34'), decimal.Decimal('10.34'))
        self.assertRaises(form.Invalid, field.deserialize, u'value')

        self.assertEqual(
            strip(field.render(request)),
            '<input type="text" name="test" title="Test" value="10.34" id="test" class="decimal-widget" />')


class TestLinesField(Base):

    def _makeOne(self, name, **kw):
        return form.LinesField(name, **kw)

    def test_fields_decimal(self):
        request = DummyRequest()

        field = self._makeOne('test')
        field = field.bind('', ['1','2','3'], {})
        field.update(request)

        self.assertIs(field.serialize(form.null), form.null)
        self.assertEqual(field.serialize(['1','2','3']), '1\n2\n3')
        self.assertRaises(form.Invalid, field.serialize, 1)

        self.assertIs(field.deserialize(''), form.null)
        self.assertEqual(field.deserialize('1\n2\n3'), ['1','2','3'])
        self.assertRaises(form.Invalid, field.deserialize, 5)

        self.assertEqual(
            strip(field.render(request)),
            '<textarea rows="5" name="test" title="Test" cols="40" id="test" class="textlines-widget">1 2 3</textarea>')


class TestVocabularyField(Base):

    def test_vocabulary_field(self):
        request = DummyRequest()

        voc = form.SimpleVocabulary.fromItems(
            (1, 'one', 'One'),
            (2, 'two', 'Two'),
            (3, 'three', 'Three'))

        self.assertRaises(ValueError, form.VocabularyField, 'test')
        self.assertRaises(
            NotImplementedError, 
            form.VocabularyField('test', vocabulary=voc).isChecked,
            voc.getTerm(1))

        class MyVocabularyField(form.VocabularyField):
            def isChecked(self, term):
                return term.token == self.value

        field = MyVocabularyField('test', vocabulary=voc)
        field.value = 'one'
        
        self.assertTrue(field.isChecked(voc.getTerm(1)))
        self.assertFalse(field.isChecked(voc.getTerm(2)))

        field.id = 'test'
        field.value = form.null
        field.updateItems()

        self.assertEqual(field.items,
                         [{'checked': False,
                           'description': None,
                           'id': 'test-0',
                           'label': 'One',
                           'name': 'test',
                           'value': 'one'},
                          {'checked': False,
                           'description': None,
                           'id': 'test-1',
                           'label': 'Two',
                           'name': 'test',
                           'value': 'two'},
                          {'checked': False,
                           'description': None,
                           'id': 'test-2',
                           'label': 'Three',
                           'name': 'test',
                           'value': 'three'}])

        field.value = 'one'
        field.updateItems()
        self.assertEqual(field.items,
                         [{'checked': True,
                           'description': None,
                           'id': 'test-0',
                           'label': 'One',
                           'name': 'test',
                           'value': 'one'},
                          {'checked': False,
                           'description': None,
                           'id': 'test-1',
                           'label': 'Two',
                           'name': 'test',
                           'value': 'two'},
                          {'checked': False,
                           'description': None,
                           'id': 'test-2',
                           'label': 'Three',
                           'name': 'test',
                           'value': 'three'}])


class TestBaseChoiceField(Base):

    def _makeOne(self, name, **kw):
        return form.BaseChoiceField(name, **kw)

    def test_basechoice(self):
        request = DummyRequest()

        voc = form.SimpleVocabulary.fromItems(
            (1, 'one', 'One'),
            (2, 'two', 'Two'),
            (3, 'three', 'Three'))

        field = self._makeOne('test', vocabulary=voc)
        field = field.bind('', 1, {})
        field.update(request)

        self.assertIs(field.extract(), form.null)

        field.params = {'test': '--NOVALUE--'}
        self.assertIs(field.extract(), form.null)

        field.params = {'test': 'three'}
        self.assertIs(field.extract(), 'three')

        self.assertIs(field.serialize(form.null), form.null)
        self.assertEqual(field.serialize(1), 'one')
        self.assertRaises(form.Invalid, field.serialize, 10)
        self.assertRaises(form.Invalid, field.serialize, [1, 10])

        self.assertIs(field.deserialize(''), form.null)
        self.assertEqual(field.deserialize('one'), 1)
        self.assertRaises(form.Invalid, field.deserialize, 5)
        self.assertRaises(form.Invalid, field.deserialize, ['one','five'])


class TestBaseMultiChoiceField(Base):

    def _makeOne(self, name, **kw):
        return form.BaseMultiChoiceField(name, **kw)

    def test_basemultichoice(self):
        request = DummyRequest()

        self.assertRaises(ValueError, self._makeOne, 'test')

        voc = form.SimpleVocabulary.fromItems(
            (1, 'one', 'One'),
            (2, 'two', 'Two'),
            (3, 'three', 'Three'))

        orig_field = self._makeOne('test', vocabulary=voc)
        field = orig_field.bind('', [1,3], {})
        field.update(request)

        self.assertIs(field.serialize(form.null), form.null)
        self.assertEqual(field.serialize([1,2]), ['one','two'])
        self.assertRaises(form.Invalid, field.serialize, 1)
        self.assertRaises(form.Invalid, field.serialize, [1, 10])

        self.assertIs(field.deserialize(''), form.null)
        self.assertEqual(field.deserialize(['one','three']), [1,3])
        self.assertRaises(form.Invalid, field.deserialize, 5)
        self.assertRaises(form.Invalid, field.deserialize, ['one','five'])

        field = orig_field.bind('', form.null, {})
        field.update(request)
        self.assertEqual(field.value, [])

        field = orig_field.bind('', [1], {})
        field.update(request)
        self.assertEqual(field.value, ['one'])

        self.assertIs(field.extract(), form.null)

        field.params = MultiDict((('test', field.noValueToken),
                                  ('test', 'one')))
        self.assertEqual(field.extract(), ['one'])


class TestChoiceField(Base):

    def _makeOne(self, name, **kw):
        return form.ChoiceField(name, **kw)

    def test_vocabulary_field(self):
        request = DummyRequest()

        voc = form.SimpleVocabulary.fromItems(
            (1, 'one', 'One'),
            (2, 'two', 'Two'))

        field = self._makeOne('test', vocabulary=voc)
        field = field.bind('', 1, {})
        field.id = 'test'
        field.update(request)

        self.assertEqual(field.items,
                         [{'checked': True,
                           'description': None,
                           'id': 'test-0',
                           'label': 'One',
                           'name': 'test',
                           'value': 'one'},
                          {'checked': False,
                           'description': None,
                           'id': 'test-1',
                           'label': 'Two',
                           'name': 'test',
                           'value': 'two'}])

        field = self._makeOne('test', missing=2, vocabulary=voc)
        field = field.bind('', 1, {})
        field.id = 'test'
        field.update(request)

        self.assertEqual(field.items,
                         [{'checked': False,
                           'description': u'',
                           'id': 'test-novalue',
                           'label': u'select a value ...',
                           'name': 'test',
                           'value': '--NOVALUE--'},
                          {'checked': True,
                           'description': None,
                           'id': 'test-0',
                           'label': 'One',
                           'name': 'test',
                           'value': 'one'},
                          {'checked': False,
                           'description': None,
                           'id': 'test-1',
                           'label': 'Two',
                           'name': 'test',
                           'value': 'two'}])


class TestMultiChoiceField(Base):

    def _makeOne(self, name, **kw):
        return form.MultiChoiceField(name, **kw)

    def test_fields_decimal(self):
        request = DummyRequest()

        voc = form.SimpleVocabulary.fromItems(
            (1, 'one', 'One'),
            (2, 'two', 'Two'),
            (3, 'three', 'Three'))

        field = self._makeOne('test', vocabulary=voc)
        field = field.bind('', [1,3], {})
        field.update(request)

        #print strip(field.render(request))


class TestDateTime(unittest.TestCase):
    def _makeOne(self, name='test', *arg, **kw):
        return form.DateTimeField(name, *arg, **kw)

    def _dt(self):
        import datetime
        return datetime.datetime(2010, 4, 26, 10, 48)

    def _today(self):
        import datetime
        return datetime.date.today()

    def test_ctor_default_tzinfo_None(self):
        import iso8601
        typ = self._makeOne()
        self.assertEqual(typ.default_tzinfo.__class__, iso8601.iso8601.Utc)

    def test_ctor_default_tzinfo_non_None(self):
        import iso8601
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        typ = self._makeOne(default_tzinfo=tzinfo)
        self.assertEqual(typ.default_tzinfo, tzinfo)

    def test_serialize_null(self):
        typ = self._makeOne()
        result = typ.serialize(form.null)
        self.assertEqual(result, form.null)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, 'garbage')
        self.assertEqual(e.msg.interpolate(),
                         '"garbage" is not a datetime object')

    def test_serialize_with_date(self):
        import datetime
        typ = self._makeOne()
        date = self._today()
        result = typ.serialize(date)
        expected = datetime.datetime.combine(date, datetime.time())
        expected = expected.replace(tzinfo=typ.default_tzinfo).isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_naive_datetime(self):
        typ = self._makeOne()
        dt = self._dt()
        result = typ.serialize(dt)
        expected = dt.replace(tzinfo=typ.default_tzinfo).isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_none_tzinfo_naive_datetime(self):
        typ = self._makeOne(default_tzinfo=None)
        dt = self._dt()
        result = typ.serialize(dt)
        self.assertEqual(result, dt.isoformat())

    def test_serialize_with_tzware_datetime(self):
        import iso8601
        typ = self._makeOne()
        dt = self._dt()
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        dt = dt.replace(tzinfo=tzinfo)
        result = typ.serialize(dt)
        expected = dt.isoformat()
        self.assertEqual(result, expected)

    def test_deserialize_date(self):
        import datetime
        import iso8601
        date = self._today()
        typ = self._makeOne()
        formatted = date.isoformat()
        result = typ.deserialize(formatted)
        expected = datetime.datetime.combine(result, datetime.time())
        tzinfo = iso8601.iso8601.Utc()
        expected = expected.replace(tzinfo=tzinfo)
        self.assertEqual(result.isoformat(), expected.isoformat())

    def test_deserialize_invalid_ParseError(self):
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, 'garbage')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_null(self):
        typ = self._makeOne()
        result = typ.deserialize(form.null)
        self.assertEqual(result, form.null)

    def test_deserialize_empty(self):
        typ = self._makeOne()
        result = typ.deserialize('')
        self.assertEqual(result, form.null)

    def test_deserialize_success(self):
        import iso8601
        typ = self._makeOne()
        dt = self._dt()
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        dt = dt.replace(tzinfo=tzinfo)
        iso = dt.isoformat()
        result = typ.deserialize(iso)
        self.assertEqual(result.isoformat(), iso)

    def test_deserialize_naive_with_default_tzinfo(self):
        import iso8601
        tzinfo = iso8601.iso8601.FixedOffset(1, 0, 'myname')
        typ = self._makeOne(default_tzinfo=tzinfo)
        dt = self._dt()
        dt_with_tz = dt.replace(tzinfo=tzinfo)
        iso = dt.isoformat()
        result = typ.deserialize(iso)
        self.assertEqual(result.isoformat(), dt_with_tz.isoformat())

    def test_deserialize_none_tzinfo(self):
        typ = self._makeOne(default_tzinfo=None)
        dt = self._dt()
        iso = dt.isoformat()
        result = typ.deserialize(iso)
        self.assertEqual(result.isoformat(), dt.isoformat())


class TestDate(unittest.TestCase):
    def _makeOne(self, name='test', *arg, **kw):
        return form.DateField(name, *arg, **kw)

    def _dt(self):
        import datetime
        return datetime.datetime(2010, 4, 26, 10, 48)

    def _today(self):
        import datetime
        return datetime.date.today()

    def test_serialize_null(self):
        val = form.null
        typ = self._makeOne()
        result = typ.serialize(val)
        self.assertEqual(result, form.null)

    def test_serialize_with_garbage(self):
        typ = self._makeOne()
        e = invalid_exc(typ.serialize, 'garbage')
        self.assertEqual(e.msg.interpolate(), '"garbage" is not a date object')

    def test_serialize_with_date(self):
        typ = self._makeOne()
        date = self._today()
        result = typ.serialize(date)
        expected = date.isoformat()
        self.assertEqual(result, expected)

    def test_serialize_with_datetime(self):
        typ = self._makeOne()
        dt = self._dt()
        result = typ.serialize(dt)
        expected = dt.date().isoformat()
        self.assertEqual(result, expected)

    def test_deserialize_invalid_ParseError(self):
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, 'garbage')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_invalid_weird(self):
        typ = self._makeOne()
        e = invalid_exc(typ.deserialize, '10-10-10-10')
        self.failUnless('Invalid' in e.msg)

    def test_deserialize_null(self):
        typ = self._makeOne()
        result = typ.deserialize(form.null)
        self.assertEqual(result, form.null)

    def test_deserialize_empty(self):
        typ = self._makeOne()
        result = typ.deserialize('')
        self.assertEqual(result, form.null)

    def test_deserialize_success_date(self):
        typ = self._makeOne()
        date = self._today()
        iso = date.isoformat()
        result = typ.deserialize(iso)
        self.assertEqual(result.isoformat(), iso)

    def test_deserialize_success_datetime(self):
        dt = self._dt()
        typ = self._makeOne()
        iso = dt.isoformat()
        result = typ.deserialize(iso)
        self.assertEqual(result.isoformat(), dt.date().isoformat())
