from django.contrib import admin

from .models import Attachment, AttachmentRevision


class AttachmentRevisionInline(admin.StackedInline):
    model = AttachmentRevision
    extra = 1
    can_delete = False


class AttachmentAdmin(admin.ModelAdmin):
    fields = ('current_revision', 'mindtouch_attachment_id')
    list_display = ('title', 'slug', 'modified', 'mindtouch_attachment_id')
    ordering = ('title',)
    search_fields = ('title',)
    raw_id_fields = ['current_revision']
    inlines = [
        AttachmentRevisionInline,
    ]


class AttachmentRevisionAdmin(admin.ModelAdmin):
    fields = ('attachment', 'file', 'title', 'slug',
              'mime_type', 'description', 'is_approved')
    list_display = ('title', 'created')
    ordering = ('-created', 'title')
    search_fields = ('title', 'description')
    raw_id_fields = ['attachment']

admin.site.register(Attachment, AttachmentAdmin)
admin.site.register(AttachmentRevision, AttachmentRevisionAdmin)
