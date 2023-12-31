# -*- coding: utf-8 -*-
from builtins import str
from builtins import object
from django.conf import settings
from django.forms import TextInput, Media, TextInput, CharField, Form, MultiWidget
from django.utils.unittest import TestCase


class FormsMediaTestCase(TestCase):
    # Tests for the media handling on widgets and forms
    def setUp(self):
        super(FormsMediaTestCase, self).setUp()
        self.original_media_url = settings.MEDIA_URL
        settings.MEDIA_URL = 'http://media.example.com/media/'

    def tearDown(self):
        settings.MEDIA_URL = self.original_media_url
        super(FormsMediaTestCase, self).tearDown()

    def test_construction(self):
        # Check construction of media objects
        m = Media(css={'all': ('path/to/css1','/path/to/css2')}, js=('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3'))
        self.assertEqual(str(m), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        class Foo(object):
            css = {
               'all': ('path/to/css1','/path/to/css2')
            }
            js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        m3 = Media(Foo)
        self.assertEqual(str(m3), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # A widget can exist without a media definition
        class MyWidget(TextInput):
            pass

        w = MyWidget()
        self.assertEqual(str(w.media), '')

    def test_media_dsl(self):
        ###############################################################
        # DSL Class-based media definitions
        ###############################################################

        # A widget can define media if it needs to.
        # Any absolute path will be preserved; relative paths are combined
        # with the value of settings.MEDIA_URL
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        w1 = MyWidget1()
        self.assertEqual(str(w1.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # Media objects can be interrogated by media type
        self.assertEqual(str(w1.media['css']), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />""")

        self.assertEqual(str(w1.media['js']), """<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

    def test_combine_media(self):
        # Media objects can be combined. Any given media resource will appear only
        # once. Duplicated media definitions are ignored.
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget2(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css2','/path/to/css3')
                }
                js = ('/path/to/js1','/path/to/js4')

        class MyWidget3(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w1 = MyWidget1()
        w2 = MyWidget2()
        w3 = MyWidget3()
        self.assertEqual(str(w1.media + w2.media + w3.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

        # Check that media addition hasn't affected the original objects
        self.assertEqual(str(w1.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # Regression check for #12879: specifying the same CSS or JS file
        # multiple times in a single Media instance should result in that file
        # only being included once.
        class MyWidget4(TextInput):
            class Media(object):
                css = {'all': ('/path/to/css1', '/path/to/css1')}
                js = ('/path/to/js1', '/path/to/js1')

        w4 = MyWidget4()
        self.assertEqual(str(w4.media), """<link href="/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>""")

    def test_media_property(self):
        ###############################################################
        # Property-based media definitions
        ###############################################################

        # Widget media can be defined as a property
        class MyWidget4(TextInput):
            def _media(self):
                return Media(css={'all': ('/some/path',)}, js = ('/some/js',))
            media = property(_media)

        w4 = MyWidget4()
        self.assertEqual(str(w4.media), """<link href="/some/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/js"></script>""")

        # Media properties can reference the media of their parents
        class MyWidget5(MyWidget4):
            def _media(self):
                return super(MyWidget5, self).media + Media(css={'all': ('/other/path',)}, js = ('/other/js',))
            media = property(_media)

        w5 = MyWidget5()
        self.assertEqual(str(w5.media), """<link href="/some/path" type="text/css" media="all" rel="stylesheet" />
<link href="/other/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/js"></script>
<script type="text/javascript" src="/other/js"></script>""")

    def test_media_property_parent_references(self):
        # Media properties can reference the media of their parents,
        # even if the parent media was defined using a class
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget6(MyWidget1):
            def _media(self):
                return super(MyWidget6, self).media + Media(css={'all': ('/other/path',)}, js = ('/other/js',))
            media = property(_media)

        w6 = MyWidget6()
        self.assertEqual(str(w6.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/other/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/other/js"></script>""")

    def test_media_inheritance(self):
        ###############################################################
        # Inheritance of media
        ###############################################################

        # If a widget extends another but provides no media definition, it inherits the parent widget's media
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget7(MyWidget1):
            pass

        w7 = MyWidget7()
        self.assertEqual(str(w7.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # If a widget extends another but defines media, it extends the parent widget's media by default
        class MyWidget8(MyWidget1):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w8 = MyWidget8()
        self.assertEqual(str(w8.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_media_inheritance_from_property(self):
        # If a widget extends another but defines media, it extends the parents widget's media,
        # even if the parent defined media using a property.
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget4(TextInput):
            def _media(self):
                return Media(css={'all': ('/some/path',)}, js = ('/some/js',))
            media = property(_media)

        class MyWidget9(MyWidget4):
            class Media(object):
                css = {
                    'all': ('/other/path',)
                }
                js = ('/other/js',)

        w9 = MyWidget9()
        self.assertEqual(str(w9.media), """<link href="/some/path" type="text/css" media="all" rel="stylesheet" />
<link href="/other/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/js"></script>
<script type="text/javascript" src="/other/js"></script>""")

        # A widget can disable media inheritance by specifying 'extend=False'
        class MyWidget10(MyWidget1):
            class Media(object):
                extend = False
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w10 = MyWidget10()
        self.assertEqual(str(w10.media), """<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_media_inheritance_extends(self):
        # A widget can explicitly enable full media inheritance by specifying 'extend=True'
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget11(MyWidget1):
            class Media(object):
                extend = True
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w11 = MyWidget11()
        self.assertEqual(str(w11.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_media_inheritance_single_type(self):
        # A widget can enable inheritance of one media type by specifying extend as a tuple
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget12(MyWidget1):
            class Media(object):
                extend = ('css',)
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w12 = MyWidget12()
        self.assertEqual(str(w12.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_multi_media(self):
        ###############################################################
        # Multi-media handling for CSS
        ###############################################################

        # A widget can define CSS media for multiple output media types
        class MultimediaWidget(TextInput):
            class Media(object):
                css = {
                   'screen, print': ('/file1','/file2'),
                   'screen': ('/file3',),
                   'print': ('/file4',)
                }
                js = ('/path/to/js1','/path/to/js4')

        multimedia = MultimediaWidget()
        self.assertEqual(str(multimedia.media), """<link href="/file4" type="text/css" media="print" rel="stylesheet" />
<link href="/file3" type="text/css" media="screen" rel="stylesheet" />
<link href="/file1" type="text/css" media="screen, print" rel="stylesheet" />
<link href="/file2" type="text/css" media="screen, print" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_multi_widget(self):
        ###############################################################
        # Multiwidget media handling
        ###############################################################

        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget2(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css2','/path/to/css3')
                }
                js = ('/path/to/js1','/path/to/js4')

        class MyWidget3(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        # MultiWidgets have a default media definition that gets all the
        # media from the component widgets
        class MyMultiWidget(MultiWidget):
            def __init__(self, attrs=None):
                widgets = [MyWidget1, MyWidget2, MyWidget3]
                super(MyMultiWidget, self).__init__(widgets, attrs)

        mymulti = MyMultiWidget()
        self.assertEqual(str(mymulti.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_form_media(self):
        ###############################################################
        # Media processing for forms
        ###############################################################

        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget2(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css2','/path/to/css3')
                }
                js = ('/path/to/js1','/path/to/js4')

        class MyWidget3(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        # You can ask a form for the media required by its widgets.
        class MyForm(Form):
            field1 = CharField(max_length=20, widget=MyWidget1())
            field2 = CharField(max_length=20, widget=MyWidget2())
        f1 = MyForm()
        self.assertEqual(str(f1.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

        # Form media can be combined to produce a single media definition.
        class AnotherForm(Form):
            field3 = CharField(max_length=20, widget=MyWidget3())
        f2 = AnotherForm()
        self.assertEqual(str(f1.media + f2.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

        # Forms can also define media, following the same rules as widgets.
        class FormWithMedia(Form):
            field1 = CharField(max_length=20, widget=MyWidget1())
            field2 = CharField(max_length=20, widget=MyWidget2())
            class Media(object):
                js = ('/some/form/javascript',)
                css = {
                    'all': ('/some/form/css',)
                }
        f3 = FormWithMedia()
        self.assertEqual(str(f3.media), """<link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<link href="/some/form/css" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>
<script type="text/javascript" src="/some/form/javascript"></script>""")

        # Media works in templates
        from django.template import Template, Context
        self.assertEqual(Template("{{ form.media.js }}{{ form.media.css }}").render(Context({'form': f3})), """<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>
<script type="text/javascript" src="/some/form/javascript"></script><link href="http://media.example.com/media/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<link href="/some/form/css" type="text/css" media="all" rel="stylesheet" />""")


class StaticFormsMediaTestCase(TestCase):
    # Tests for the media handling on widgets and forms
    def setUp(self):
        super(StaticFormsMediaTestCase, self).setUp()
        self.original_media_url = settings.MEDIA_URL
        self.original_static_url = settings.STATIC_URL
        settings.MEDIA_URL = 'http://media.example.com/static/'
        settings.STATIC_URL = 'http://media.example.com/static/'

    def tearDown(self):
        settings.MEDIA_URL = self.original_media_url
        settings.STATIC_URL = self.original_static_url
        super(StaticFormsMediaTestCase, self).tearDown()

    def test_construction(self):
        # Check construction of media objects
        m = Media(css={'all': ('path/to/css1','/path/to/css2')}, js=('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3'))
        self.assertEqual(str(m), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        class Foo(object):
            css = {
               'all': ('path/to/css1','/path/to/css2')
            }
            js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        m3 = Media(Foo)
        self.assertEqual(str(m3), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # A widget can exist without a media definition
        class MyWidget(TextInput):
            pass

        w = MyWidget()
        self.assertEqual(str(w.media), '')

    def test_media_dsl(self):
        ###############################################################
        # DSL Class-based media definitions
        ###############################################################

        # A widget can define media if it needs to.
        # Any absolute path will be preserved; relative paths are combined
        # with the value of settings.MEDIA_URL
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        w1 = MyWidget1()
        self.assertEqual(str(w1.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # Media objects can be interrogated by media type
        self.assertEqual(str(w1.media['css']), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />""")

        self.assertEqual(str(w1.media['js']), """<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

    def test_combine_media(self):
        # Media objects can be combined. Any given media resource will appear only
        # once. Duplicated media definitions are ignored.
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget2(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css2','/path/to/css3')
                }
                js = ('/path/to/js1','/path/to/js4')

        class MyWidget3(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w1 = MyWidget1()
        w2 = MyWidget2()
        w3 = MyWidget3()
        self.assertEqual(str(w1.media + w2.media + w3.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

        # Check that media addition hasn't affected the original objects
        self.assertEqual(str(w1.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # Regression check for #12879: specifying the same CSS or JS file
        # multiple times in a single Media instance should result in that file
        # only being included once.
        class MyWidget4(TextInput):
            class Media(object):
                css = {'all': ('/path/to/css1', '/path/to/css1')}
                js = ('/path/to/js1', '/path/to/js1')

        w4 = MyWidget4()
        self.assertEqual(str(w4.media), """<link href="/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>""")

    def test_media_property(self):
        ###############################################################
        # Property-based media definitions
        ###############################################################

        # Widget media can be defined as a property
        class MyWidget4(TextInput):
            def _media(self):
                return Media(css={'all': ('/some/path',)}, js = ('/some/js',))
            media = property(_media)

        w4 = MyWidget4()
        self.assertEqual(str(w4.media), """<link href="/some/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/js"></script>""")

        # Media properties can reference the media of their parents
        class MyWidget5(MyWidget4):
            def _media(self):
                return super(MyWidget5, self).media + Media(css={'all': ('/other/path',)}, js = ('/other/js',))
            media = property(_media)

        w5 = MyWidget5()
        self.assertEqual(str(w5.media), """<link href="/some/path" type="text/css" media="all" rel="stylesheet" />
<link href="/other/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/js"></script>
<script type="text/javascript" src="/other/js"></script>""")

    def test_media_property_parent_references(self):
        # Media properties can reference the media of their parents,
        # even if the parent media was defined using a class
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget6(MyWidget1):
            def _media(self):
                return super(MyWidget6, self).media + Media(css={'all': ('/other/path',)}, js = ('/other/js',))
            media = property(_media)

        w6 = MyWidget6()
        self.assertEqual(str(w6.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/other/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/other/js"></script>""")

    def test_media_inheritance(self):
        ###############################################################
        # Inheritance of media
        ###############################################################

        # If a widget extends another but provides no media definition, it inherits the parent widget's media
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget7(MyWidget1):
            pass

        w7 = MyWidget7()
        self.assertEqual(str(w7.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>""")

        # If a widget extends another but defines media, it extends the parent widget's media by default
        class MyWidget8(MyWidget1):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w8 = MyWidget8()
        self.assertEqual(str(w8.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_media_inheritance_from_property(self):
        # If a widget extends another but defines media, it extends the parents widget's media,
        # even if the parent defined media using a property.
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget4(TextInput):
            def _media(self):
                return Media(css={'all': ('/some/path',)}, js = ('/some/js',))
            media = property(_media)

        class MyWidget9(MyWidget4):
            class Media(object):
                css = {
                    'all': ('/other/path',)
                }
                js = ('/other/js',)

        w9 = MyWidget9()
        self.assertEqual(str(w9.media), """<link href="/some/path" type="text/css" media="all" rel="stylesheet" />
<link href="/other/path" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/some/js"></script>
<script type="text/javascript" src="/other/js"></script>""")

        # A widget can disable media inheritance by specifying 'extend=False'
        class MyWidget10(MyWidget1):
            class Media(object):
                extend = False
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w10 = MyWidget10()
        self.assertEqual(str(w10.media), """<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_media_inheritance_extends(self):
        # A widget can explicitly enable full media inheritance by specifying 'extend=True'
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget11(MyWidget1):
            class Media(object):
                extend = True
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w11 = MyWidget11()
        self.assertEqual(str(w11.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_media_inheritance_single_type(self):
        # A widget can enable inheritance of one media type by specifying extend as a tuple
        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget12(MyWidget1):
            class Media(object):
                extend = ('css',)
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        w12 = MyWidget12()
        self.assertEqual(str(w12.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_multi_media(self):
        ###############################################################
        # Multi-media handling for CSS
        ###############################################################

        # A widget can define CSS media for multiple output media types
        class MultimediaWidget(TextInput):
            class Media(object):
                css = {
                   'screen, print': ('/file1','/file2'),
                   'screen': ('/file3',),
                   'print': ('/file4',)
                }
                js = ('/path/to/js1','/path/to/js4')

        multimedia = MultimediaWidget()
        self.assertEqual(str(multimedia.media), """<link href="/file4" type="text/css" media="print" rel="stylesheet" />
<link href="/file3" type="text/css" media="screen" rel="stylesheet" />
<link href="/file1" type="text/css" media="screen, print" rel="stylesheet" />
<link href="/file2" type="text/css" media="screen, print" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_multi_widget(self):
        ###############################################################
        # Multiwidget media handling
        ###############################################################

        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget2(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css2','/path/to/css3')
                }
                js = ('/path/to/js1','/path/to/js4')

        class MyWidget3(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        # MultiWidgets have a default media definition that gets all the
        # media from the component widgets
        class MyMultiWidget(MultiWidget):
            def __init__(self, attrs=None):
                widgets = [MyWidget1, MyWidget2, MyWidget3]
                super(MyMultiWidget, self).__init__(widgets, attrs)

        mymulti = MyMultiWidget()
        self.assertEqual(str(mymulti.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

    def test_form_media(self):
        ###############################################################
        # Media processing for forms
        ###############################################################

        class MyWidget1(TextInput):
            class Media(object):
                css = {
                   'all': ('path/to/css1','/path/to/css2')
                }
                js = ('/path/to/js1','http://media.other.com/path/to/js2','https://secure.other.com/path/to/js3')

        class MyWidget2(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css2','/path/to/css3')
                }
                js = ('/path/to/js1','/path/to/js4')

        class MyWidget3(TextInput):
            class Media(object):
                css = {
                   'all': ('/path/to/css3','path/to/css1')
                }
                js = ('/path/to/js1','/path/to/js4')

        # You can ask a form for the media required by its widgets.
        class MyForm(Form):
            field1 = CharField(max_length=20, widget=MyWidget1())
            field2 = CharField(max_length=20, widget=MyWidget2())
        f1 = MyForm()
        self.assertEqual(str(f1.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

        # Form media can be combined to produce a single media definition.
        class AnotherForm(Form):
            field3 = CharField(max_length=20, widget=MyWidget3())
        f2 = AnotherForm()
        self.assertEqual(str(f1.media + f2.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>""")

        # Forms can also define media, following the same rules as widgets.
        class FormWithMedia(Form):
            field1 = CharField(max_length=20, widget=MyWidget1())
            field2 = CharField(max_length=20, widget=MyWidget2())
            class Media(object):
                js = ('/some/form/javascript',)
                css = {
                    'all': ('/some/form/css',)
                }
        f3 = FormWithMedia()
        self.assertEqual(str(f3.media), """<link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<link href="/some/form/css" type="text/css" media="all" rel="stylesheet" />
<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>
<script type="text/javascript" src="/some/form/javascript"></script>""")

        # Media works in templates
        from django.template import Template, Context
        self.assertEqual(Template("{{ form.media.js }}{{ form.media.css }}").render(Context({'form': f3})), """<script type="text/javascript" src="/path/to/js1"></script>
<script type="text/javascript" src="http://media.other.com/path/to/js2"></script>
<script type="text/javascript" src="https://secure.other.com/path/to/js3"></script>
<script type="text/javascript" src="/path/to/js4"></script>
<script type="text/javascript" src="/some/form/javascript"></script><link href="http://media.example.com/static/path/to/css1" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css2" type="text/css" media="all" rel="stylesheet" />
<link href="/path/to/css3" type="text/css" media="all" rel="stylesheet" />
<link href="/some/form/css" type="text/css" media="all" rel="stylesheet" />""")

