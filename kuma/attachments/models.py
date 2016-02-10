import os
from datetime import datetime

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .utils import attachment_upload_to, full_attachment_url


class Attachment(models.Model):
    """
    An attachment which can be inserted into one or more wiki documents.

    There is no direct database-level relationship between attachments
    and documents; insertion of an attachment is handled through
    markup in the document.
    """
    current_revision = models.ForeignKey(
        'AttachmentRevision',
        null=True,
        blank=True,
        related_name='current_for+',
    )
    # These get filled from the current revision.
    title = models.CharField(max_length=255, db_index=True)

    # This is somewhat like the bookkeeping we do for Documents, but
    # is also slightly more permanent because storing this ID lets us
    # map from old MindTouch file URLs (which are based on the ID) to
    # new kuma file URLs.
    mindtouch_attachment_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource",
        null=True, blank=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    class Meta(object):
        permissions = (
            ("disallow_add_attachment", "Cannot upload attachment"),
        )

    def __unicode__(self):
        return self.title

    def get_file_url(self):
        return full_attachment_url(self.id, self.current_revision.filename)

    def attach(self, document, user, revision):
        """
        When an attachment revision form is saved, this is used to attach
        the new attachment revision to the given document via an intermediate
        model that stores some extra data like the user and the revision's
        filename.
        """
        # First let's see if there is already an intermediate object available
        # for the current attachment, a.k.a. this was a previous uploaded file
        try:
            document_attachment = (document.files.through.objects
                                                         .get(pk=self.pk))
        except MultipleObjectsReturned:
            # There may be multiple uploaded files referenced in the document
            # content which could have created multiple of the intermediates
            # TODO: what to do with the others?
            document_attachment = (document.files.through.objects
                                                         .filter(pk=self.pk)
                                                         .first())
        except document.files.through.DoesNotExist:
            # no previous uploads found, create a new document-attachment
            document.files.through.objects.create(file=self,
                                                  document=document,
                                                  attached_by=user,
                                                  name=revision.filename,
                                                  is_original=True)
        else:
            document_attachment.is_original = True
            document_attachment.attached_by = user
            document_attachment.name = revision.filename
            document_attachment.save()


class AttachmentRevision(models.Model):
    """
    A revision of an attachment.
    """
    DEFAULT_MIME_TYPE = 'application/octet-stream'

    attachment = models.ForeignKey(Attachment, related_name='revisions')

    file = models.FileField(upload_to=attachment_upload_to, max_length=500)

    title = models.CharField(max_length=255, null=True, db_index=True)

    mime_type = models.CharField(
        max_length=255,
        db_index=True,
        blank=True,
        default=DEFAULT_MIME_TYPE,
        help_text=_('The MIME type is used when serving the attachment. '
                    'Automatically populated by inspecting the file on '
                    'upload. Please only override if needed.'),
    )
    # Does not allow wiki markup
    description = models.TextField(blank=True)

    created = models.DateTimeField(default=datetime.now)
    comment = models.CharField(max_length=255, blank=True)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='created_attachment_revisions',
    )
    is_approved = models.BooleanField(default=True, db_index=True)

    # As with document revisions, bookkeeping for the MindTouch
    # migration.
    #
    # TODO: Do we actually need full file revision history from
    # MindTouch?
    mindtouch_old_id = models.IntegerField(
        help_text="ID for migrated MindTouch resource revision",
        null=True, blank=True, db_index=True, unique=True)
    is_mindtouch_migration = models.BooleanField(
        default=False, db_index=True,
        help_text="Did this revision come from MindTouch?")

    class Meta:
        verbose_name = _('attachment revision')
        verbose_name_plural = _('attachment revisions')

    def __unicode__(self):
        return (u'%s (file: "%s", ID: #%s)' %
                (self.title, self.filename, self.pk))

    @property
    def filename(self):
        return os.path.split(self.file.path)[-1]

    def save(self, *args, **kwargs):
        super(AttachmentRevision, self).save(*args, **kwargs)
        if self.is_approved and (
                not self.attachment.current_revision or
                self.attachment.current_revision.id < self.id):
            self.make_current()

    def make_current(self):
        """Make this revision the current one for the attachment."""
        self.attachment.title = self.title
        self.attachment.current_revision = self
        self.attachment.save()

    def get_previous(self):
        return self.attachment.revisions.filter(
            is_approved=True,
            created__lt=self.created,
        ).order_by('-created').first()
