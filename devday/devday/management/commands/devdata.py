from datetime import datetime
from os import makedirs
from os.path import isfile, join
from shutil import copyfile

import errno
import random

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.utils import timezone

from cms import api
from cms.constants import TEMPLATE_INHERITANCE_MAGIC
from cms.models import Page

from attendee.models import Attendee
from event.models import Event
from talk.models import Speaker, Talk

from devday.management.commands.words import Words


class Command(BaseCommand):
    help = 'Fill database with data suitable for development'
    rng = random.Random()
    rng.seed(1)  # we want reproducable pseudo-random numbers here
    speaker_placeholder_file = 'icons8-contacts-26.png'
    speaker_placeholder_source_path = join(settings.STATICFILES_DIRS[0],
                                           'img', speaker_placeholder_file)
    speaker_portrait_media_dir = 'speakers'
    speaker_portrait_media_path = join(speaker_portrait_media_dir,
                                       speaker_placeholder_file)
    speaker_portrait_dir = join(settings.MEDIA_ROOT,
                                speaker_portrait_media_dir)
    speaker_portrait_path = join(settings.MEDIA_ROOT,
                                 speaker_portrait_media_path)

    def handleCreateUser(self):
        User = get_user_model()

        try:
            user = User.objects.get(email=settings.ADMINUSER_EMAIL)
            print "Create admin user: {} already present" \
                  .format(settings.ADMINUSER_EMAIL)
        except ObjectDoesNotExist:
            print "Create admin user"
            user = User.objects.create_user(settings.ADMINUSER_EMAIL,
                                            password='admin')
            user.is_superuser = True
            user.is_staff = True
            user.save()

    def handleUpdateSite(self):
        print "Update site"
        site = Site.objects.get(pk=1)
        site.domain = 'devday.de'
        site.name = 'Dev Data'
        site.save()

    def handleCreatePages(self):
        npage = Page.objects.count()
        if npage > 0:
            print "Create pages: {} page objects already exist, skipping" \
                  .format(npage)
            return
        print "Creating pages"
        api.create_page(title="Dev Data 2019", language='de', published=True,
                        template='devday_index.html', parent=None)
        api.create_page(title="Deutsche Homepage", language="de",
                        template=TEMPLATE_INHERITANCE_MAGIC, redirect="/",
                        slug="de", in_navigation=False, parent=None)
        api.create_page(title="Sessions", language="de", published=True,
                        template=TEMPLATE_INHERITANCE_MAGIC,
                        in_navigation=True, parent=None)
        archive = api.create_page(title="Archiv", language="de",
                                  published=True,
                                  template=TEMPLATE_INHERITANCE_MAGIC,
                                  in_navigation=True, parent=None)
        api.create_page(title="Dev Data 2017", language="de", published=True,
                        template=TEMPLATE_INHERITANCE_MAGIC,
                        redirect="/devdata17/talk", in_navigation=True,
                        parent=archive)
        api.create_page(title="Dev Data 2018", language="de", published=True,
                        template=TEMPLATE_INHERITANCE_MAGIC,
                        redirect="/devdata18/talk", in_navigation=True,
                        parent=archive)
        api.create_page(title="Sponsoring", language="de", published=True,
                        template=TEMPLATE_INHERITANCE_MAGIC,
                        reverse_id="sponsoring", parent=None)

    def handleCreateAttendees(self):
        User = get_user_model()
        nuser = User.objects.count()
        if nuser > 3:
            print "Create attendees: {} users already exist, skipping" \
                  .format(nuser)
            return
        events = Event.objects.all()
        first = ["Alexander", "Barbara", "Christian", "Daniela", "Erik",
                 "Fatima", "Georg", "Heike", "Ingo", "Jana", "Klaus", "Lena",
                 "Martin", "Natalie", "Olaf", "Peggy", "Quirin", "Rosa",
                 "Sven", "Tanja", "Ulrich", "Veronika", "Werner", "Xena",
                 "Yannick", "Zahra"]
        last = ["Schneider", "Meier", "Schulze", "Fischer", "Weber",
                "Becker", "Lehmann", "Koch", "Richter", "Neumann",
                "Fuchs", "Vogel", "Keller", "Jung", "Hahn",
                "Schubert", "Winkler", "Berger", "Lorenz", "Albrecht"]
        print "Creating {:d} attendees".format(len(first) * len(last))
        for f in first:
            for l in last:
                user = User.objects.create_user("{}.{}@example.com"
                                                .format(f.lower(), l.lower()),
                                                password='attendee',
                                                first_name=f, last_name=l)
                user.save()
                for e in events:
                    if self.rng.random() < 0.8:
                        a = Attendee(user=user, event=e)
                        a.save()

    def handleCreateSpeakers(self):
        nspeaker = Speaker.objects.count()
        if nspeaker > 1:
            print "Create speakers: {} speakers already exist, skipping" \
                  .format(nspeaker)
            return
        nspeakerperevent = 50
        nspeaker = Event.objects.count() * nspeakerperevent
        attendees = self.rng.sample(Attendee.objects.all(), nspeaker)
        print "Creating {} speakers for {} events" \
              .format(nspeakerperevent, Event.objects.count())
        if not isfile(self.speaker_portrait_path):
            try:
                makedirs(self.speaker_portrait_dir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
            copyfile(self.speaker_placeholder_source_path,
                     self.speaker_portrait_path)
        for attendee in attendees:
            speaker = Speaker(user=attendee, shirt_size=3,
                              videopermission=True, shortbio="My short bio")
            # https://stackoverflow.com/a/5256094
            speaker.portrait = speaker.portrait.field \
                .attr_class(speaker, speaker.portrait.field,
                            self.speaker_portrait_media_path)
            speaker.save()

    def createTalk(self, speaker):
        talk = Talk(speaker=speaker, title=Words.sentence(self.rng),
                    abstract='A very short abstract.',
                    remarks='A very short remark.')
        talk.save()
        return talk

    def handleCreateTalk(self):
        """
        Create talks. With a probability of 10%, a speaker will submit two
        talks, with a probability of 75% will submit one talk, and with a
        remaining probability of 5% will not submit any talk for the event the
        speaker registered for.
        """
        ntalk = Talk.objects.count()
        if ntalk > 1:
            print "Create talks: {} talks already exist, skipping" \
                  .format(ntalk)
            return
        print "Creating one talk per speaker"
        for speaker in Speaker.objects.all():
            p = self.rng.random()
            if p < 0.85:
                self.createTalk(speaker)
            if p < 0.10:
                self.createTalk(speaker)

    def handle(self, *args, **options):
        self.handleCreateUser()
        self.handleUpdateSite()
        self.handleCreatePages()
        self.handleCreateAttendees()
        self.handleCreateSpeakers()
        self.handleCreateTalk()
