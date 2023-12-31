from builtins import str
from builtins import object
import datetime
import re
from datetime import date
from decimal import Decimal

from django import forms
from django.db import models
from django.forms.models import (_get_foreign_key, inlineformset_factory,
    modelformset_factory, modelformset_factory)
from django.test import TestCase, skipUnlessDBFeature

from modeltests.model_formsets.models import (
    Author, BetterAuthor, Book, BookWithCustomPK, Editor,
    BookWithOptionalAltEditor, AlternateBook, AuthorMeeting, CustomPrimaryKey,
    Place, Owner, Location, OwnerProfile, Restaurant, Product, Price,
    MexicanRestaurant, ClassyMexicanRestaurant, Repository, Revision,
    Person, Membership, Team, Player, Poet, Poem, Post)

class DeletionTests(TestCase):
    def test_deletion(self):
        PoetFormSet = modelformset_factory(Poet, can_delete=True)
        poet = Poet.objects.create(name='test')
        data = {
            'form-TOTAL_FORMS': u'1',
            'form-INITIAL_FORMS': u'1',
            'form-MAX_NUM_FORMS': u'0',
            'form-0-id': str(poet.pk),
            'form-0-name': u'test',
            'form-0-DELETE': u'on',
        }
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        formset.save()
        self.assertTrue(formset.is_valid())
        self.assertEqual(Poet.objects.count(), 0)

    def test_add_form_deletion_when_invalid(self):
        """
        Make sure that an add form that is filled out, but marked for deletion
        doesn't cause validation errors.
        """
        PoetFormSet = modelformset_factory(Poet, can_delete=True)
        data = {
            'form-TOTAL_FORMS': u'1',
            'form-INITIAL_FORMS': u'0',
            'form-MAX_NUM_FORMS': u'0',
            'form-0-id': u'',
            'form-0-name': u'x' * 1000,
        }
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        # Make sure this form doesn't pass validation.
        self.assertEqual(formset.is_valid(), False)
        self.assertEqual(Poet.objects.count(), 0)

        # Then make sure that it *does* pass validation and delete the object,
        # even though the data isn't actually valid.
        data['form-0-DELETE'] = 'on'
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        self.assertEqual(formset.is_valid(), True)
        formset.save()
        self.assertEqual(Poet.objects.count(), 0)

    def test_change_form_deletion_when_invalid(self):
        """
        Make sure that an add form that is filled out, but marked for deletion
        doesn't cause validation errors.
        """
        PoetFormSet = modelformset_factory(Poet, can_delete=True)
        poet = Poet.objects.create(name='test')
        data = {
            'form-TOTAL_FORMS': u'1',
            'form-INITIAL_FORMS': u'1',
            'form-MAX_NUM_FORMS': u'0',
            'form-0-id': str(poet.id),
            'form-0-name': u'x' * 1000,
        }
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        # Make sure this form doesn't pass validation.
        self.assertEqual(formset.is_valid(), False)
        self.assertEqual(Poet.objects.count(), 1)

        # Then make sure that it *does* pass validation and delete the object,
        # even though the data isn't actually valid.
        data['form-0-DELETE'] = 'on'
        formset = PoetFormSet(data, queryset=Poet.objects.all())
        self.assertEqual(formset.is_valid(), True)
        formset.save()
        self.assertEqual(Poet.objects.count(), 0)

class ModelFormsetTest(TestCase):
    def test_simple_save(self):
        qs = Author.objects.all()
        AuthorFormSet = modelformset_factory(Author, extra=3)

        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label> <input id="id_form-0-name" type="text" name="form-0-name" maxlength="100" /><input type="hidden" name="form-0-id" id="id_form-0-id" /></p>')
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label> <input id="id_form-1-name" type="text" name="form-1-name" maxlength="100" /><input type="hidden" name="form-1-id" id="id_form-1-id" /></p>')
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_form-2-name">Name:</label> <input id="id_form-2-name" type="text" name="form-2-name" maxlength="100" /><input type="hidden" name="form-2-id" id="id_form-2-id" /></p>')

        data = {
            'form-TOTAL_FORMS': '3', # the number of forms rendered
            'form-INITIAL_FORMS': '0', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-name': 'Charles Baudelaire',
            'form-1-name': 'Arthur Rimbaud',
            'form-2-name': '',
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 2)
        author1, author2 = saved
        self.assertEqual(author1, Author.objects.get(name='Charles Baudelaire'))
        self.assertEqual(author2, Author.objects.get(name='Arthur Rimbaud'))

        authors = list(Author.objects.order_by('name'))
        self.assertEqual(authors, [author2, author1])

        # Gah! We forgot Paul Verlaine. Let's create a formset to edit the
        # existing authors with an extra form to add him. We *could* pass in a
        # queryset to restrict the Author objects we edit, but in this case
        # we'll use it to display them in alphabetical order by name.

        qs = Author.objects.order_by('name')
        AuthorFormSet = modelformset_factory(Author, extra=1, can_delete=False)

        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label> <input id="id_form-0-name" type="text" name="form-0-name" value="Arthur Rimbaud" maxlength="100" /><input type="hidden" name="form-0-id" value="%d" id="id_form-0-id" /></p>' % author2.id)
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label> <input id="id_form-1-name" type="text" name="form-1-name" value="Charles Baudelaire" maxlength="100" /><input type="hidden" name="form-1-id" value="%d" id="id_form-1-id" /></p>' % author1.id)
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_form-2-name">Name:</label> <input id="id_form-2-name" type="text" name="form-2-name" maxlength="100" /><input type="hidden" name="form-2-id" id="id_form-2-id" /></p>')

        data = {
            'form-TOTAL_FORMS': '3', # the number of forms rendered
            'form-INITIAL_FORMS': '2', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-id': str(author2.id),
            'form-0-name': 'Arthur Rimbaud',
            'form-1-id': str(author1.id),
            'form-1-name': 'Charles Baudelaire',
            'form-2-name': 'Paul Verlaine',
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        # Only changed or new objects are returned from formset.save()
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        author3 = saved[0]
        self.assertEqual(author3, Author.objects.get(name='Paul Verlaine'))

        authors = list(Author.objects.order_by('name'))
        self.assertEqual(authors, [author2, author1, author3])

        # This probably shouldn't happen, but it will. If an add form was
        # marked for deletion, make sure we don't save that form.

        qs = Author.objects.order_by('name')
        AuthorFormSet = modelformset_factory(Author, extra=1, can_delete=True)

        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 4)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label> <input id="id_form-0-name" type="text" name="form-0-name" value="Arthur Rimbaud" maxlength="100" /></p>\n'
            '<p><label for="id_form-0-DELETE">Delete:</label> <input type="checkbox" name="form-0-DELETE" id="id_form-0-DELETE" /><input type="hidden" name="form-0-id" value="%d" id="id_form-0-id" /></p>' % author2.id)
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label> <input id="id_form-1-name" type="text" name="form-1-name" value="Charles Baudelaire" maxlength="100" /></p>\n'
            '<p><label for="id_form-1-DELETE">Delete:</label> <input type="checkbox" name="form-1-DELETE" id="id_form-1-DELETE" /><input type="hidden" name="form-1-id" value="%d" id="id_form-1-id" /></p>' % author1.id)
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_form-2-name">Name:</label> <input id="id_form-2-name" type="text" name="form-2-name" value="Paul Verlaine" maxlength="100" /></p>\n'
            '<p><label for="id_form-2-DELETE">Delete:</label> <input type="checkbox" name="form-2-DELETE" id="id_form-2-DELETE" /><input type="hidden" name="form-2-id" value="%d" id="id_form-2-id" /></p>' % author3.id)
        self.assertEqual(formset.forms[3].as_p(),
            '<p><label for="id_form-3-name">Name:</label> <input id="id_form-3-name" type="text" name="form-3-name" maxlength="100" /></p>\n'
            '<p><label for="id_form-3-DELETE">Delete:</label> <input type="checkbox" name="form-3-DELETE" id="id_form-3-DELETE" /><input type="hidden" name="form-3-id" id="id_form-3-id" /></p>')

        data = {
            'form-TOTAL_FORMS': '4', # the number of forms rendered
            'form-INITIAL_FORMS': '3', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-id': str(author2.id),
            'form-0-name': 'Arthur Rimbaud',
            'form-1-id': str(author1.id),
            'form-1-name': 'Charles Baudelaire',
            'form-2-id': str(author3.id),
            'form-2-name': 'Paul Verlaine',
            'form-3-name': 'Walt Whitman',
            'form-3-DELETE': 'on',
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        # No objects were changed or saved so nothing will come back.

        self.assertEqual(formset.save(), [])

        authors = list(Author.objects.order_by('name'))
        self.assertEqual(authors, [author2, author1, author3])

        # Let's edit a record to ensure save only returns that one record.

        data = {
            'form-TOTAL_FORMS': '4', # the number of forms rendered
            'form-INITIAL_FORMS': '3', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-id': str(author2.id),
            'form-0-name': 'Walt Whitman',
            'form-1-id': str(author1.id),
            'form-1-name': 'Charles Baudelaire',
            'form-2-id': str(author3.id),
            'form-2-name': 'Paul Verlaine',
            'form-3-name': '',
            'form-3-DELETE': '',
        }

        formset = AuthorFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        # One record has changed.

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0], Author.objects.get(name='Walt Whitman'))

    def test_commit_false(self):
        # Test the behavior of commit=False and save_m2m

        author1 = Author.objects.create(name='Charles Baudelaire')
        author2 = Author.objects.create(name='Paul Verlaine')
        author3 = Author.objects.create(name='Walt Whitman')

        meeting = AuthorMeeting.objects.create(created=date.today())
        meeting.authors = Author.objects.all()

        # create an Author instance to add to the meeting.

        author4 = Author.objects.create(name=u'John Steinbeck')

        AuthorMeetingFormSet = modelformset_factory(AuthorMeeting, extra=1, can_delete=True)
        data = {
            'form-TOTAL_FORMS': '2', # the number of forms rendered
            'form-INITIAL_FORMS': '1', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-id': str(meeting.id),
            'form-0-name': '2nd Tuesday of the Week Meeting',
            'form-0-authors': [author2.id, author1.id, author3.id, author4.id],
            'form-1-name': '',
            'form-1-authors': '',
            'form-1-DELETE': '',
        }
        formset = AuthorMeetingFormSet(data=data, queryset=AuthorMeeting.objects.all())
        self.assertTrue(formset.is_valid())

        instances = formset.save(commit=False)
        for instance in instances:
            instance.created = date.today()
            instance.save()
        formset.save_m2m()
        self.assertQuerysetEqual(instances[0].authors.all(), [
            '<Author: Charles Baudelaire>',
            '<Author: John Steinbeck>',
            '<Author: Paul Verlaine>',
            '<Author: Walt Whitman>',
        ])

    def test_max_num(self):
        # Test the behavior of max_num with model formsets. It should allow
        # all existing related objects/inlines for a given object to be
        # displayed, but not allow the creation of new inlines beyond max_num.

        author1 = Author.objects.create(name='Charles Baudelaire')
        author2 = Author.objects.create(name='Paul Verlaine')
        author3 = Author.objects.create(name='Walt Whitman')

        qs = Author.objects.order_by('name')

        AuthorFormSet = modelformset_factory(Author, max_num=None, extra=3)
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 6)
        self.assertEqual(len(formset.extra_forms), 3)

        AuthorFormSet = modelformset_factory(Author, max_num=4, extra=3)
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 4)
        self.assertEqual(len(formset.extra_forms), 1)

        AuthorFormSet = modelformset_factory(Author, max_num=0, extra=3)
        formset = AuthorFormSet(queryset=qs)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(len(formset.extra_forms), 0)

        AuthorFormSet = modelformset_factory(Author, max_num=None)
        formset = AuthorFormSet(queryset=qs)
        self.assertQuerysetEqual(formset.get_queryset(), [
            '<Author: Charles Baudelaire>',
            '<Author: Paul Verlaine>',
            '<Author: Walt Whitman>',
        ])

        AuthorFormSet = modelformset_factory(Author, max_num=0)
        formset = AuthorFormSet(queryset=qs)
        self.assertQuerysetEqual(formset.get_queryset(), [
            '<Author: Charles Baudelaire>',
            '<Author: Paul Verlaine>',
            '<Author: Walt Whitman>',
        ])

        AuthorFormSet = modelformset_factory(Author, max_num=4)
        formset = AuthorFormSet(queryset=qs)
        self.assertQuerysetEqual(formset.get_queryset(), [
            '<Author: Charles Baudelaire>',
            '<Author: Paul Verlaine>',
            '<Author: Walt Whitman>',
        ])

    def test_custom_save_method(self):
        class PoetForm(forms.ModelForm):
            def save(self, commit=True):
                # change the name to "Vladimir Mayakovsky" just to be a jerk.
                author = super(PoetForm, self).save(commit=False)
                author.name = u"Vladimir Mayakovsky"
                if commit:
                    author.save()
                return author

        PoetFormSet = modelformset_factory(Poet, form=PoetForm)

        data = {
            'form-TOTAL_FORMS': '3', # the number of forms rendered
            'form-INITIAL_FORMS': '0', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-name': 'Walt Whitman',
            'form-1-name': 'Charles Baudelaire',
            'form-2-name': '',
        }

        qs = Poet.objects.all()
        formset = PoetFormSet(data=data, queryset=qs)
        self.assertTrue(formset.is_valid())

        poets = formset.save()
        self.assertEqual(len(poets), 2)
        poet1, poet2 = poets
        self.assertEqual(poet1.name, 'Vladimir Mayakovsky')
        self.assertEqual(poet2.name, 'Vladimir Mayakovsky')

    def test_model_inheritance(self):
        BetterAuthorFormSet = modelformset_factory(BetterAuthor)
        formset = BetterAuthorFormSet()
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label> <input id="id_form-0-name" type="text" name="form-0-name" maxlength="100" /></p>\n'
            '<p><label for="id_form-0-write_speed">Write speed:</label> <input type="text" name="form-0-write_speed" id="id_form-0-write_speed" /><input type="hidden" name="form-0-author_ptr" id="id_form-0-author_ptr" /></p>')

        data = {
            'form-TOTAL_FORMS': '1', # the number of forms rendered
            'form-INITIAL_FORMS': '0', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-author_ptr': '',
            'form-0-name': 'Ernest Hemingway',
            'form-0-write_speed': '10',
        }

        formset = BetterAuthorFormSet(data)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        author1, = saved
        self.assertEqual(author1, BetterAuthor.objects.get(name='Ernest Hemingway'))
        hemingway_id = BetterAuthor.objects.get(name="Ernest Hemingway").pk

        formset = BetterAuthorFormSet()
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-name">Name:</label> <input id="id_form-0-name" type="text" name="form-0-name" value="Ernest Hemingway" maxlength="100" /></p>\n'
            '<p><label for="id_form-0-write_speed">Write speed:</label> <input type="text" name="form-0-write_speed" value="10" id="id_form-0-write_speed" /><input type="hidden" name="form-0-author_ptr" value="%d" id="id_form-0-author_ptr" /></p>' % hemingway_id)
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_form-1-name">Name:</label> <input id="id_form-1-name" type="text" name="form-1-name" maxlength="100" /></p>\n'
            '<p><label for="id_form-1-write_speed">Write speed:</label> <input type="text" name="form-1-write_speed" id="id_form-1-write_speed" /><input type="hidden" name="form-1-author_ptr" id="id_form-1-author_ptr" /></p>')

        data = {
            'form-TOTAL_FORMS': '2', # the number of forms rendered
            'form-INITIAL_FORMS': '1', # the number of forms with initial data
            'form-MAX_NUM_FORMS': '', # the max number of forms
            'form-0-author_ptr': hemingway_id,
            'form-0-name': 'Ernest Hemingway',
            'form-0-write_speed': '10',
            'form-1-author_ptr': '',
            'form-1-name': '',
            'form-1-write_speed': '',
        }

        formset = BetterAuthorFormSet(data)
        self.assertTrue(formset.is_valid())
        self.assertEqual(formset.save(), [])

    def test_inline_formsets(self):
        # We can also create a formset that is tied to a parent model. This is
        # how the admin system's edit inline functionality works.

        AuthorBooksFormSet = inlineformset_factory(Author, Book, can_delete=False, extra=3)
        author = Author.objects.create(name='Charles Baudelaire')

        formset = AuthorBooksFormSet(instance=author)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label> <input id="id_book_set-0-title" type="text" name="book_set-0-title" maxlength="100" /><input type="hidden" name="book_set-0-author" value="%d" id="id_book_set-0-author" /><input type="hidden" name="book_set-0-id" id="id_book_set-0-id" /></p>'  % author.id)
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label> <input id="id_book_set-1-title" type="text" name="book_set-1-title" maxlength="100" /><input type="hidden" name="book_set-1-author" value="%d" id="id_book_set-1-author" /><input type="hidden" name="book_set-1-id" id="id_book_set-1-id" /></p>' % author.id)
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label> <input id="id_book_set-2-title" type="text" name="book_set-2-title" maxlength="100" /><input type="hidden" name="book_set-2-author" value="%d" id="id_book_set-2-author" /><input type="hidden" name="book_set-2-id" id="id_book_set-2-id" /></p>' % author.id)

        data = {
            'book_set-TOTAL_FORMS': '3', # the number of forms rendered
            'book_set-INITIAL_FORMS': '0', # the number of forms with initial data
            'book_set-MAX_NUM_FORMS': '', # the max number of forms
            'book_set-0-title': 'Les Fleurs du Mal',
            'book_set-1-title': '',
            'book_set-2-title': '',
        }

        formset = AuthorBooksFormSet(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        book1, = saved
        self.assertEqual(book1, Book.objects.get(title='Les Fleurs du Mal'))
        self.assertQuerysetEqual(author.book_set.all(), ['<Book: Les Fleurs du Mal>'])

        # Now that we've added a book to Charles Baudelaire, let's try adding
        # another one. This time though, an edit form will be available for
        # every existing book.

        AuthorBooksFormSet = inlineformset_factory(Author, Book, can_delete=False, extra=2)
        author = Author.objects.get(name='Charles Baudelaire')

        formset = AuthorBooksFormSet(instance=author)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label> <input id="id_book_set-0-title" type="text" name="book_set-0-title" value="Les Fleurs du Mal" maxlength="100" /><input type="hidden" name="book_set-0-author" value="%d" id="id_book_set-0-author" /><input type="hidden" name="book_set-0-id" value="%d" id="id_book_set-0-id" /></p>' % (author.id, book1.id))
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label> <input id="id_book_set-1-title" type="text" name="book_set-1-title" maxlength="100" /><input type="hidden" name="book_set-1-author" value="%d" id="id_book_set-1-author" /><input type="hidden" name="book_set-1-id" id="id_book_set-1-id" /></p>' % author.id)
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label> <input id="id_book_set-2-title" type="text" name="book_set-2-title" maxlength="100" /><input type="hidden" name="book_set-2-author" value="%d" id="id_book_set-2-author" /><input type="hidden" name="book_set-2-id" id="id_book_set-2-id" /></p>' % author.id)

        data = {
            'book_set-TOTAL_FORMS': '3', # the number of forms rendered
            'book_set-INITIAL_FORMS': '1', # the number of forms with initial data
            'book_set-MAX_NUM_FORMS': '', # the max number of forms
            'book_set-0-id': str(book1.id),
            'book_set-0-title': 'Les Fleurs du Mal',
            'book_set-1-title': 'Les Paradis Artificiels',
            'book_set-2-title': '',
        }

        formset = AuthorBooksFormSet(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        book2, = saved
        self.assertEqual(book2, Book.objects.get(title='Les Paradis Artificiels'))

        # As you can see, 'Les Paradis Artificiels' is now a book belonging to
        # Charles Baudelaire.
        self.assertQuerysetEqual(author.book_set.order_by('title'), [
            '<Book: Les Fleurs du Mal>',
            '<Book: Les Paradis Artificiels>',
        ])

    def test_inline_formsets_save_as_new(self):
        # The save_as_new parameter lets you re-associate the data to a new
        # instance.  This is used in the admin for save_as functionality.
        AuthorBooksFormSet = inlineformset_factory(Author, Book, can_delete=False, extra=2)
        author = Author.objects.create(name='Charles Baudelaire')

        data = {
            'book_set-TOTAL_FORMS': '3', # the number of forms rendered
            'book_set-INITIAL_FORMS': '2', # the number of forms with initial data
            'book_set-MAX_NUM_FORMS': '', # the max number of forms
            'book_set-0-id': '1',
            'book_set-0-title': 'Les Fleurs du Mal',
            'book_set-1-id': '2',
            'book_set-1-title': 'Les Paradis Artificiels',
            'book_set-2-title': '',
        }

        formset = AuthorBooksFormSet(data, instance=Author(), save_as_new=True)
        self.assertTrue(formset.is_valid())

        new_author = Author.objects.create(name='Charles Baudelaire')
        formset = AuthorBooksFormSet(data, instance=new_author, save_as_new=True)
        saved = formset.save()
        self.assertEqual(len(saved), 2)
        book1, book2 = saved
        self.assertEqual(book1.title, 'Les Fleurs du Mal')
        self.assertEqual(book2.title, 'Les Paradis Artificiels')

        # Test using a custom prefix on an inline formset.

        formset = AuthorBooksFormSet(prefix="test")
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_test-0-title">Title:</label> <input id="id_test-0-title" type="text" name="test-0-title" maxlength="100" /><input type="hidden" name="test-0-author" id="id_test-0-author" /><input type="hidden" name="test-0-id" id="id_test-0-id" /></p>')
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_test-1-title">Title:</label> <input id="id_test-1-title" type="text" name="test-1-title" maxlength="100" /><input type="hidden" name="test-1-author" id="id_test-1-author" /><input type="hidden" name="test-1-id" id="id_test-1-id" /></p>')

    def test_inline_formsets_with_custom_pk(self):
        # Test inline formsets where the inline-edited object has a custom
        # primary key that is not the fk to the parent object.

        AuthorBooksFormSet2 = inlineformset_factory(Author, BookWithCustomPK, can_delete=False, extra=1)
        author = Author.objects.create(pk=1, name='Charles Baudelaire')

        formset = AuthorBooksFormSet2(instance=author)
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_bookwithcustompk_set-0-my_pk">My pk:</label> <input type="text" name="bookwithcustompk_set-0-my_pk" id="id_bookwithcustompk_set-0-my_pk" /></p>\n'
            '<p><label for="id_bookwithcustompk_set-0-title">Title:</label> <input id="id_bookwithcustompk_set-0-title" type="text" name="bookwithcustompk_set-0-title" maxlength="100" /><input type="hidden" name="bookwithcustompk_set-0-author" value="1" id="id_bookwithcustompk_set-0-author" /></p>')

        data = {
            'bookwithcustompk_set-TOTAL_FORMS': '1', # the number of forms rendered
            'bookwithcustompk_set-INITIAL_FORMS': '0', # the number of forms with initial data
            'bookwithcustompk_set-MAX_NUM_FORMS': '', # the max number of forms
            'bookwithcustompk_set-0-my_pk': '77777',
            'bookwithcustompk_set-0-title': 'Les Fleurs du Mal',
        }

        formset = AuthorBooksFormSet2(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        book1, = saved
        self.assertEqual(book1.pk, 77777)

        book1 = author.bookwithcustompk_set.get()
        self.assertEqual(book1.title, 'Les Fleurs du Mal')

    def test_inline_formsets_with_multi_table_inheritance(self):
        # Test inline formsets where the inline-edited object uses multi-table
        # inheritance, thus has a non AutoField yet auto-created primary key.

        AuthorBooksFormSet3 = inlineformset_factory(Author, AlternateBook, can_delete=False, extra=1)
        author = Author.objects.create(pk=1, name='Charles Baudelaire')

        formset = AuthorBooksFormSet3(instance=author)
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_alternatebook_set-0-title">Title:</label> <input id="id_alternatebook_set-0-title" type="text" name="alternatebook_set-0-title" maxlength="100" /></p>\n'
            '<p><label for="id_alternatebook_set-0-notes">Notes:</label> <input id="id_alternatebook_set-0-notes" type="text" name="alternatebook_set-0-notes" maxlength="100" /><input type="hidden" name="alternatebook_set-0-author" value="1" id="id_alternatebook_set-0-author" /><input type="hidden" name="alternatebook_set-0-book_ptr" id="id_alternatebook_set-0-book_ptr" /></p>')

        data = {
            'alternatebook_set-TOTAL_FORMS': '1', # the number of forms rendered
            'alternatebook_set-INITIAL_FORMS': '0', # the number of forms with initial data
            'alternatebook_set-MAX_NUM_FORMS': '', # the max number of forms
            'alternatebook_set-0-title': 'Flowers of Evil',
            'alternatebook_set-0-notes': 'English translation of Les Fleurs du Mal'
        }

        formset = AuthorBooksFormSet3(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 1)
        book1, = saved
        self.assertEqual(book1.title, 'Flowers of Evil')
        self.assertEqual(book1.notes, 'English translation of Les Fleurs du Mal')

    @skipUnlessDBFeature('ignores_nulls_in_unique_constraints')
    def test_inline_formsets_with_nullable_unique_together(self):
        # Test inline formsets where the inline-edited object has a
        # unique_together constraint with a nullable member

        AuthorBooksFormSet4 = inlineformset_factory(Author, BookWithOptionalAltEditor, can_delete=False, extra=2)
        author = Author.objects.create(pk=1, name='Charles Baudelaire')

        data = {
            'bookwithoptionalalteditor_set-TOTAL_FORMS': '2', # the number of forms rendered
            'bookwithoptionalalteditor_set-INITIAL_FORMS': '0', # the number of forms with initial data
            'bookwithoptionalalteditor_set-MAX_NUM_FORMS': '', # the max number of forms
            'bookwithoptionalalteditor_set-0-author': '1',
            'bookwithoptionalalteditor_set-0-title': 'Les Fleurs du Mal',
            'bookwithoptionalalteditor_set-1-author': '1',
            'bookwithoptionalalteditor_set-1-title': 'Les Fleurs du Mal',
        }
        formset = AuthorBooksFormSet4(data, instance=author)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 2)
        book1, book2 = saved
        self.assertEqual(book1.author_id, 1)
        self.assertEqual(book1.title, 'Les Fleurs du Mal')
        self.assertEqual(book2.author_id, 1)
        self.assertEqual(book2.title, 'Les Fleurs du Mal')

    def test_inline_formsets_with_custom_save_method(self):
        AuthorBooksFormSet = inlineformset_factory(Author, Book, can_delete=False, extra=2)
        author = Author.objects.create(pk=1, name='Charles Baudelaire')
        book1 = Book.objects.create(pk=1, author=author, title='Les Paradis Artificiels')
        book2 = Book.objects.create(pk=2, author=author, title='Les Fleurs du Mal')
        book3 = Book.objects.create(pk=3, author=author, title='Flowers of Evil')

        class PoemForm(forms.ModelForm):
            def save(self, commit=True):
                # change the name to "Brooklyn Bridge" just to be a jerk.
                poem = super(PoemForm, self).save(commit=False)
                poem.name = u"Brooklyn Bridge"
                if commit:
                    poem.save()
                return poem

        PoemFormSet = inlineformset_factory(Poet, Poem, form=PoemForm)

        data = {
            'poem_set-TOTAL_FORMS': '3', # the number of forms rendered
            'poem_set-INITIAL_FORMS': '0', # the number of forms with initial data
            'poem_set-MAX_NUM_FORMS': '', # the max number of forms
            'poem_set-0-name': 'The Cloud in Trousers',
            'poem_set-1-name': 'I',
            'poem_set-2-name': '',
        }

        poet = Poet.objects.create(name='Vladimir Mayakovsky')
        formset = PoemFormSet(data=data, instance=poet)
        self.assertTrue(formset.is_valid())

        saved = formset.save()
        self.assertEqual(len(saved), 2)
        poem1, poem2 = saved
        self.assertEqual(poem1.name, 'Brooklyn Bridge')
        self.assertEqual(poem2.name, 'Brooklyn Bridge')

        # We can provide a custom queryset to our InlineFormSet:

        custom_qs = Book.objects.order_by('-title')
        formset = AuthorBooksFormSet(instance=author, queryset=custom_qs)
        self.assertEqual(len(formset.forms), 5)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label> <input id="id_book_set-0-title" type="text" name="book_set-0-title" value="Les Paradis Artificiels" maxlength="100" /><input type="hidden" name="book_set-0-author" value="1" id="id_book_set-0-author" /><input type="hidden" name="book_set-0-id" value="1" id="id_book_set-0-id" /></p>')
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label> <input id="id_book_set-1-title" type="text" name="book_set-1-title" value="Les Fleurs du Mal" maxlength="100" /><input type="hidden" name="book_set-1-author" value="1" id="id_book_set-1-author" /><input type="hidden" name="book_set-1-id" value="2" id="id_book_set-1-id" /></p>')
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label> <input id="id_book_set-2-title" type="text" name="book_set-2-title" value="Flowers of Evil" maxlength="100" /><input type="hidden" name="book_set-2-author" value="1" id="id_book_set-2-author" /><input type="hidden" name="book_set-2-id" value="3" id="id_book_set-2-id" /></p>')
        self.assertEqual(formset.forms[3].as_p(),
            '<p><label for="id_book_set-3-title">Title:</label> <input id="id_book_set-3-title" type="text" name="book_set-3-title" maxlength="100" /><input type="hidden" name="book_set-3-author" value="1" id="id_book_set-3-author" /><input type="hidden" name="book_set-3-id" id="id_book_set-3-id" /></p>')
        self.assertEqual(formset.forms[4].as_p(),
            '<p><label for="id_book_set-4-title">Title:</label> <input id="id_book_set-4-title" type="text" name="book_set-4-title" maxlength="100" /><input type="hidden" name="book_set-4-author" value="1" id="id_book_set-4-author" /><input type="hidden" name="book_set-4-id" id="id_book_set-4-id" /></p>')

        data = {
            'book_set-TOTAL_FORMS': '5', # the number of forms rendered
            'book_set-INITIAL_FORMS': '3', # the number of forms with initial data
            'book_set-MAX_NUM_FORMS': '', # the max number of forms
            'book_set-0-id': str(book1.id),
            'book_set-0-title': 'Les Paradis Artificiels',
            'book_set-1-id': str(book2.id),
            'book_set-1-title': 'Les Fleurs du Mal',
            'book_set-2-id': str(book3.id),
            'book_set-2-title': 'Flowers of Evil',
            'book_set-3-title': 'Revue des deux mondes',
            'book_set-4-title': '',
        }
        formset = AuthorBooksFormSet(data, instance=author, queryset=custom_qs)
        self.assertTrue(formset.is_valid())

        custom_qs = Book.objects.filter(title__startswith='F')
        formset = AuthorBooksFormSet(instance=author, queryset=custom_qs)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_book_set-0-title">Title:</label> <input id="id_book_set-0-title" type="text" name="book_set-0-title" value="Flowers of Evil" maxlength="100" /><input type="hidden" name="book_set-0-author" value="1" id="id_book_set-0-author" /><input type="hidden" name="book_set-0-id" value="3" id="id_book_set-0-id" /></p>')
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_book_set-1-title">Title:</label> <input id="id_book_set-1-title" type="text" name="book_set-1-title" maxlength="100" /><input type="hidden" name="book_set-1-author" value="1" id="id_book_set-1-author" /><input type="hidden" name="book_set-1-id" id="id_book_set-1-id" /></p>')
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_book_set-2-title">Title:</label> <input id="id_book_set-2-title" type="text" name="book_set-2-title" maxlength="100" /><input type="hidden" name="book_set-2-author" value="1" id="id_book_set-2-author" /><input type="hidden" name="book_set-2-id" id="id_book_set-2-id" /></p>')

        data = {
            'book_set-TOTAL_FORMS': '3', # the number of forms rendered
            'book_set-INITIAL_FORMS': '1', # the number of forms with initial data
            'book_set-MAX_NUM_FORMS': '', # the max number of forms
            'book_set-0-id': str(book3.id),
            'book_set-0-title': 'Flowers of Evil',
            'book_set-1-title': 'Revue des deux mondes',
            'book_set-2-title': '',
        }
        formset = AuthorBooksFormSet(data, instance=author, queryset=custom_qs)
        self.assertTrue(formset.is_valid())

    def test_custom_pk(self):
        # We need to ensure that it is displayed

        CustomPrimaryKeyFormSet = modelformset_factory(CustomPrimaryKey)
        formset = CustomPrimaryKeyFormSet()
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-my_pk">My pk:</label> <input id="id_form-0-my_pk" type="text" name="form-0-my_pk" maxlength="10" /></p>\n'
            '<p><label for="id_form-0-some_field">Some field:</label> <input id="id_form-0-some_field" type="text" name="form-0-some_field" maxlength="100" /></p>')

        # Custom primary keys with ForeignKey, OneToOneField and AutoField ############

        place = Place.objects.create(pk=1, name=u'Giordanos', city=u'Chicago')

        FormSet = inlineformset_factory(Place, Owner, extra=2, can_delete=False)
        formset = FormSet(instance=place)
        self.assertEqual(len(formset.forms), 2)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_owner_set-0-name">Name:</label> <input id="id_owner_set-0-name" type="text" name="owner_set-0-name" maxlength="100" /><input type="hidden" name="owner_set-0-place" value="1" id="id_owner_set-0-place" /><input type="hidden" name="owner_set-0-auto_id" id="id_owner_set-0-auto_id" /></p>')
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_owner_set-1-name">Name:</label> <input id="id_owner_set-1-name" type="text" name="owner_set-1-name" maxlength="100" /><input type="hidden" name="owner_set-1-place" value="1" id="id_owner_set-1-place" /><input type="hidden" name="owner_set-1-auto_id" id="id_owner_set-1-auto_id" /></p>')

        data = {
            'owner_set-TOTAL_FORMS': '2',
            'owner_set-INITIAL_FORMS': '0',
            'owner_set-MAX_NUM_FORMS': '',
            'owner_set-0-auto_id': '',
            'owner_set-0-name': u'Joe Perry',
            'owner_set-1-auto_id': '',
            'owner_set-1-name': '',
        }
        formset = FormSet(data, instance=place)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        owner1, = saved
        self.assertEqual(owner1.name, 'Joe Perry')
        self.assertEqual(owner1.place.name, 'Giordanos')

        formset = FormSet(instance=place)
        self.assertEqual(len(formset.forms), 3)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_owner_set-0-name">Name:</label> <input id="id_owner_set-0-name" type="text" name="owner_set-0-name" value="Joe Perry" maxlength="100" /><input type="hidden" name="owner_set-0-place" value="1" id="id_owner_set-0-place" /><input type="hidden" name="owner_set-0-auto_id" value="%d" id="id_owner_set-0-auto_id" /></p>'
            % owner1.auto_id)
        self.assertEqual(formset.forms[1].as_p(),
            '<p><label for="id_owner_set-1-name">Name:</label> <input id="id_owner_set-1-name" type="text" name="owner_set-1-name" maxlength="100" /><input type="hidden" name="owner_set-1-place" value="1" id="id_owner_set-1-place" /><input type="hidden" name="owner_set-1-auto_id" id="id_owner_set-1-auto_id" /></p>')
        self.assertEqual(formset.forms[2].as_p(),
            '<p><label for="id_owner_set-2-name">Name:</label> <input id="id_owner_set-2-name" type="text" name="owner_set-2-name" maxlength="100" /><input type="hidden" name="owner_set-2-place" value="1" id="id_owner_set-2-place" /><input type="hidden" name="owner_set-2-auto_id" id="id_owner_set-2-auto_id" /></p>')

        data = {
            'owner_set-TOTAL_FORMS': '3',
            'owner_set-INITIAL_FORMS': '1',
            'owner_set-MAX_NUM_FORMS': '',
            'owner_set-0-auto_id': str(owner1.auto_id),
            'owner_set-0-name': u'Joe Perry',
            'owner_set-1-auto_id': '',
            'owner_set-1-name': u'Jack Berry',
            'owner_set-2-auto_id': '',
            'owner_set-2-name': '',
        }
        formset = FormSet(data, instance=place)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        owner2, = saved
        self.assertEqual(owner2.name, 'Jack Berry')
        self.assertEqual(owner2.place.name, 'Giordanos')

        # Ensure a custom primary key that is a ForeignKey or OneToOneField get rendered for the user to choose.

        FormSet = modelformset_factory(OwnerProfile)
        formset = FormSet()
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_form-0-owner">Owner:</label> <select name="form-0-owner" id="id_form-0-owner">\n'
            '<option value="" selected="selected">---------</option>\n'
            '<option value="%d">Joe Perry at Giordanos</option>\n'
            '<option value="%d">Jack Berry at Giordanos</option>\n'
            '</select></p>\n'
            '<p><label for="id_form-0-age">Age:</label> <input type="text" name="form-0-age" id="id_form-0-age" /></p>'
            % (owner1.auto_id, owner2.auto_id))

        owner1 = Owner.objects.get(name=u'Joe Perry')
        FormSet = inlineformset_factory(Owner, OwnerProfile, max_num=1, can_delete=False)
        self.assertEqual(FormSet.max_num, 1)

        formset = FormSet(instance=owner1)
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_ownerprofile-0-age">Age:</label> <input type="text" name="ownerprofile-0-age" id="id_ownerprofile-0-age" /><input type="hidden" name="ownerprofile-0-owner" value="%d" id="id_ownerprofile-0-owner" /></p>'
            % owner1.auto_id)

        data = {
            'ownerprofile-TOTAL_FORMS': '1',
            'ownerprofile-INITIAL_FORMS': '0',
            'ownerprofile-MAX_NUM_FORMS': '1',
            'ownerprofile-0-owner': '',
            'ownerprofile-0-age': u'54',
        }
        formset = FormSet(data, instance=owner1)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        profile1, = saved
        self.assertEqual(profile1.owner, owner1)
        self.assertEqual(profile1.age, 54)

        formset = FormSet(instance=owner1)
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_ownerprofile-0-age">Age:</label> <input type="text" name="ownerprofile-0-age" value="54" id="id_ownerprofile-0-age" /><input type="hidden" name="ownerprofile-0-owner" value="%d" id="id_ownerprofile-0-owner" /></p>'
            % owner1.auto_id)

        data = {
            'ownerprofile-TOTAL_FORMS': '1',
            'ownerprofile-INITIAL_FORMS': '1',
            'ownerprofile-MAX_NUM_FORMS': '1',
            'ownerprofile-0-owner': str(owner1.auto_id),
            'ownerprofile-0-age': u'55',
        }
        formset = FormSet(data, instance=owner1)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        profile1, = saved
        self.assertEqual(profile1.owner, owner1)
        self.assertEqual(profile1.age, 55)

    def test_unique_true_enforces_max_num_one(self):
        # ForeignKey with unique=True should enforce max_num=1

        place = Place.objects.create(pk=1, name=u'Giordanos', city=u'Chicago')

        FormSet = inlineformset_factory(Place, Location, can_delete=False)
        self.assertEqual(FormSet.max_num, 1)

        formset = FormSet(instance=place)
        self.assertEqual(len(formset.forms), 1)
        self.assertEqual(formset.forms[0].as_p(),
            '<p><label for="id_location_set-0-lat">Lat:</label> <input id="id_location_set-0-lat" type="text" name="location_set-0-lat" maxlength="100" /></p>\n'
            '<p><label for="id_location_set-0-lon">Lon:</label> <input id="id_location_set-0-lon" type="text" name="location_set-0-lon" maxlength="100" /><input type="hidden" name="location_set-0-place" value="1" id="id_location_set-0-place" /><input type="hidden" name="location_set-0-id" id="id_location_set-0-id" /></p>')

    def test_foreign_keys_in_parents(self):
        self.assertEqual(type(_get_foreign_key(Restaurant, Owner)), models.ForeignKey)
        self.assertEqual(type(_get_foreign_key(MexicanRestaurant, Owner)), models.ForeignKey)

    def test_unique_validation(self):
        FormSet = modelformset_factory(Product, extra=1)
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-slug': 'car-red',
        }
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        product1, = saved
        self.assertEqual(product1.slug, 'car-red')

        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-slug': 'car-red',
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.errors, [{'slug': [u'Product with this Slug already exists.']}])

    def test_unique_together_validation(self):
        FormSet = modelformset_factory(Price, extra=1)
        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-price': u'12.00',
            'form-0-quantity': '1',
        }
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        price1, = saved
        self.assertEqual(price1.price, Decimal('12.00'))
        self.assertEqual(price1.quantity, 1)

        data = {
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-price': u'12.00',
            'form-0-quantity': '1',
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.errors, [{'__all__': [u'Price with this Price and Quantity already exists.']}])

    def test_unique_together_with_inlineformset_factory(self):
        # Also see bug #8882.

        repository = Repository.objects.create(name=u'Test Repo')
        FormSet = inlineformset_factory(Repository, Revision, extra=1)
        data = {
            'revision_set-TOTAL_FORMS': '1',
            'revision_set-INITIAL_FORMS': '0',
            'revision_set-MAX_NUM_FORMS': '',
            'revision_set-0-repository': repository.pk,
            'revision_set-0-revision': '146239817507f148d448db38840db7c3cbf47c76',
            'revision_set-0-DELETE': '',
        }
        formset = FormSet(data, instance=repository)
        self.assertTrue(formset.is_valid())
        saved = formset.save()
        self.assertEqual(len(saved), 1)
        revision1, = saved
        self.assertEqual(revision1.repository, repository)
        self.assertEqual(revision1.revision, '146239817507f148d448db38840db7c3cbf47c76')

        # attempt to save the same revision against against the same repo.
        data = {
            'revision_set-TOTAL_FORMS': '1',
            'revision_set-INITIAL_FORMS': '0',
            'revision_set-MAX_NUM_FORMS': '',
            'revision_set-0-repository': repository.pk,
            'revision_set-0-revision': '146239817507f148d448db38840db7c3cbf47c76',
            'revision_set-0-DELETE': '',
        }
        formset = FormSet(data, instance=repository)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset.errors, [{'__all__': [u'Revision with this Repository and Revision already exists.']}])

        # unique_together with inlineformset_factory with overridden form fields
        # Also see #9494

        FormSet = inlineformset_factory(Repository, Revision, fields=('revision',), extra=1)
        data = {
            'revision_set-TOTAL_FORMS': '1',
            'revision_set-INITIAL_FORMS': '0',
            'revision_set-MAX_NUM_FORMS': '',
            'revision_set-0-repository': repository.pk,
            'revision_set-0-revision': '146239817507f148d448db38840db7c3cbf47c76',
            'revision_set-0-DELETE': '',
        }
        formset = FormSet(data, instance=repository)
        self.assertFalse(formset.is_valid())

    def test_callable_defaults(self):
        # Use of callable defaults (see bug #7975).

        person = Person.objects.create(name='Ringo')
        FormSet = inlineformset_factory(Person, Membership, can_delete=False, extra=1)
        formset = FormSet(instance=person)

        # Django will render a hidden field for model fields that have a callable
        # default. This is required to ensure the value is tested for change correctly
        # when determine what extra forms have changed to save.

        self.assertEqual(len(formset.forms), 1) # this formset only has one form
        form = formset.forms[0]
        now = form.fields['date_joined'].initial()
        result = form.as_p()
        result = re.sub(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?', '__DATETIME__', result)
        self.assertEqual(result,
            '<p><label for="id_membership_set-0-date_joined">Date joined:</label> <input type="text" name="membership_set-0-date_joined" value="__DATETIME__" id="id_membership_set-0-date_joined" /><input type="hidden" name="initial-membership_set-0-date_joined" value="__DATETIME__" id="initial-membership_set-0-id_membership_set-0-date_joined" /></p>\n'
            '<p><label for="id_membership_set-0-karma">Karma:</label> <input type="text" name="membership_set-0-karma" id="id_membership_set-0-karma" /><input type="hidden" name="membership_set-0-person" value="%d" id="id_membership_set-0-person" /><input type="hidden" name="membership_set-0-id" id="id_membership_set-0-id" /></p>'
            % person.id)

        # test for validation with callable defaults. Validations rely on hidden fields

        data = {
            'membership_set-TOTAL_FORMS': '1',
            'membership_set-INITIAL_FORMS': '0',
            'membership_set-MAX_NUM_FORMS': '',
            'membership_set-0-date_joined': str(now.strftime('%Y-%m-%d %H:%M:%S')),
            'initial-membership_set-0-date_joined': str(now.strftime('%Y-%m-%d %H:%M:%S')),
            'membership_set-0-karma': '',
        }
        formset = FormSet(data, instance=person)
        self.assertTrue(formset.is_valid())

        # now test for when the data changes

        one_day_later = now + datetime.timedelta(days=1)
        filled_data = {
            'membership_set-TOTAL_FORMS': '1',
            'membership_set-INITIAL_FORMS': '0',
            'membership_set-MAX_NUM_FORMS': '',
            'membership_set-0-date_joined': str(one_day_later.strftime('%Y-%m-%d %H:%M:%S')),
            'initial-membership_set-0-date_joined': str(now.strftime('%Y-%m-%d %H:%M:%S')),
            'membership_set-0-karma': '',
        }
        formset = FormSet(filled_data, instance=person)
        self.assertFalse(formset.is_valid())

        # now test with split datetime fields

        class MembershipForm(forms.ModelForm):
            date_joined = forms.SplitDateTimeField(initial=now)
            class Meta(object):
                model = Membership
            def __init__(self, **kwargs):
                super(MembershipForm, self).__init__(**kwargs)
                self.fields['date_joined'].widget = forms.SplitDateTimeWidget()

        FormSet = inlineformset_factory(Person, Membership, form=MembershipForm, can_delete=False, extra=1)
        data = {
            'membership_set-TOTAL_FORMS': '1',
            'membership_set-INITIAL_FORMS': '0',
            'membership_set-MAX_NUM_FORMS': '',
            'membership_set-0-date_joined_0': str(now.strftime('%Y-%m-%d')),
            'membership_set-0-date_joined_1': str(now.strftime('%H:%M:%S')),
            'initial-membership_set-0-date_joined': str(now.strftime('%Y-%m-%d %H:%M:%S')),
            'membership_set-0-karma': '',
        }
        formset = FormSet(data, instance=person)
        self.assertTrue(formset.is_valid())

    def test_inlineformset_factory_with_null_fk(self):
        # inlineformset_factory tests with fk having null=True. see #9462.
        # create some data that will exbit the issue
        team = Team.objects.create(name=u"Red Vipers")
        Player(name="Timmy").save()
        Player(name="Bobby", team=team).save()

        PlayerInlineFormSet = inlineformset_factory(Team, Player)
        formset = PlayerInlineFormSet()
        self.assertQuerysetEqual(formset.get_queryset(), [])

        formset = PlayerInlineFormSet(instance=team)
        players = formset.get_queryset()
        self.assertEqual(len(players), 1)
        player1, = players
        self.assertEqual(player1.team, team)
        self.assertEqual(player1.name, 'Bobby')

    def test_model_formset_with_custom_pk(self):
        # a formset for a Model that has a custom primary key that still needs to be
        # added to the formset automatically
        FormSet = modelformset_factory(ClassyMexicanRestaurant, fields=["tacos_are_yummy"])
        self.assertEqual(sorted(FormSet().forms[0].fields.keys()), ['restaurant', 'tacos_are_yummy'])

    def test_prevent_duplicates_from_with_the_same_formset(self):
        FormSet = modelformset_factory(Product, extra=2)
        data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '',
            'form-0-slug': 'red_car',
            'form-1-slug': 'red_car',
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset._non_form_errors,
            [u'Please correct the duplicate data for slug.'])

        FormSet = modelformset_factory(Price, extra=2)
        data = {
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-MAX_NUM_FORMS': '',
            'form-0-price': '25',
            'form-0-quantity': '7',
            'form-1-price': '25',
            'form-1-quantity': '7',
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset._non_form_errors,
            [u'Please correct the duplicate data for price and quantity, which must be unique.'])

        # Only the price field is specified, this should skip any unique checks since
        # the unique_together is not fulfilled. This will fail with a KeyError if broken.
        FormSet = modelformset_factory(Price, fields=("price",), extra=2)
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',
            'form-0-price': '24',
            'form-1-price': '24',
        }
        formset = FormSet(data)
        self.assertTrue(formset.is_valid())

        FormSet = inlineformset_factory(Author, Book, extra=0)
        author = Author.objects.create(pk=1, name='Charles Baudelaire')
        book1 = Book.objects.create(pk=1, author=author, title='Les Paradis Artificiels')
        book2 = Book.objects.create(pk=2, author=author, title='Les Fleurs du Mal')
        book3 = Book.objects.create(pk=3, author=author, title='Flowers of Evil')

        book_ids = author.book_set.order_by('id').values_list('id', flat=True)
        data = {
            'book_set-TOTAL_FORMS': '2',
            'book_set-INITIAL_FORMS': '2',
            'book_set-MAX_NUM_FORMS': '',

            'book_set-0-title': 'The 2008 Election',
            'book_set-0-author': str(author.id),
            'book_set-0-id': str(book_ids[0]),

            'book_set-1-title': 'The 2008 Election',
            'book_set-1-author': str(author.id),
            'book_set-1-id': str(book_ids[1]),
        }
        formset = FormSet(data=data, instance=author)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset._non_form_errors,
            [u'Please correct the duplicate data for title.'])
        self.assertEqual(formset.errors,
            [{}, {'__all__': [u'Please correct the duplicate values below.']}])

        FormSet = modelformset_factory(Post, extra=2)
        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',

            'form-0-title': 'blah',
            'form-0-slug': 'Morning',
            'form-0-subtitle': 'foo',
            'form-0-posted': '2009-01-01',
            'form-1-title': 'blah',
            'form-1-slug': 'Morning in Prague',
            'form-1-subtitle': 'rawr',
            'form-1-posted': '2009-01-01'
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset._non_form_errors,
            [u'Please correct the duplicate data for title which must be unique for the date in posted.'])
        self.assertEqual(formset.errors,
            [{}, {'__all__': [u'Please correct the duplicate values below.']}])

        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',

            'form-0-title': 'foo',
            'form-0-slug': 'Morning in Prague',
            'form-0-subtitle': 'foo',
            'form-0-posted': '2009-01-01',
            'form-1-title': 'blah',
            'form-1-slug': 'Morning in Prague',
            'form-1-subtitle': 'rawr',
            'form-1-posted': '2009-08-02'
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset._non_form_errors,
            [u'Please correct the duplicate data for slug which must be unique for the year in posted.'])

        data = {
            'form-TOTAL_FORMS': '2',
            'form-INITIAL_FORMS': '0',
            'form-MAX_NUM_FORMS': '',

            'form-0-title': 'foo',
            'form-0-slug': 'Morning in Prague',
            'form-0-subtitle': 'rawr',
            'form-0-posted': '2008-08-01',
            'form-1-title': 'blah',
            'form-1-slug': 'Prague',
            'form-1-subtitle': 'rawr',
            'form-1-posted': '2009-08-02'
        }
        formset = FormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(formset._non_form_errors,
            [u'Please correct the duplicate data for subtitle which must be unique for the month in posted.'])
