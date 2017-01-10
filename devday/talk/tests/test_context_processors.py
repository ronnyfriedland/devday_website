from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from attendee.models import Attendee
from talk.models import Speaker

User = get_user_model()


class TestCommitteeMemberContextProcessor(TestCase):
    def test_is_committee_member_is_false_for_anonymous(self):
        response = self.client.get('/')
        self.assertFalse(response.context['is_committee_member'])

    def test_is_committee_member_is_false_for_attendee(self):
        user = User.objects.create_user(email='test@example.org', password='test')
        Attendee.objects.create(user=user)
        self.client.login(username='test@example.org', password='test')
        response = self.client.get('/')
        self.assertFalse(response.context['is_committee_member'])

    def test_is_committee_member_is_false_for_speaker(self):
        user = User.objects.create_user(email='test@example.org', password='test')
        attendee = Attendee.objects.create(user=user)
        Speaker.objects.create(user=attendee, videopermission=True, shirt_size=1)
        self.client.login(username='test@example.org', password='test')
        response = self.client.get('/')
        self.assertFalse(response.context['is_committee_member'])

    def test_is_committee_member_is_true_for_committee_member(self):
        user = User.objects.create_user(email='test@example.org', password='test')
        user.groups.add(Group.objects.get(name='talk_committee'))
        self.client.login(username='test@example.org', password='test')
        response = self.client.get('/')
        self.assertTrue(response.context['is_committee_member'])
