from django.contrib import admin

from kuma.core.urlresolvers import reverse

from .models import Key, KeyAction


def history_link(self):
    url = '{0!s}?{1!s}'.format(reverse('admin:authkeys_keyaction_changelist'),
                     'key__exact={0!s}'.format((self.id)))
    count = self.history.count()
    what = (count == 1) and 'action' or 'actions'
    return '<a href="{0!s}">{1!s}&nbsp;{2!s}</a>'.format(url, count, what)

history_link.allow_tags = True
history_link.short_description = 'Usage history'


class KeyAdmin(admin.ModelAdmin):
    fields = ('description',)
    list_display = ('id', 'user', 'created', history_link, 'key',
                    'description')
    ordering = ('-created', 'user')
    search_fields = ('key', 'description', 'user__username')


def key_link(self):
    key = self.key
    url = reverse('admin:authkeys_key_change',
                  args=[key.id])
    return '<a href="{0!s}">{1!s} (#{2!s})</a>'.format(url, key.user, key.id)

key_link.allow_tags = True
key_link.short_description = 'Key'


def content_object_link(self):
    obj = self.content_object
    url_key = 'admin:{0!s}_{1!s}_change'.format(obj._meta.app_label,
                                      obj._meta.model_name)
    url = reverse(url_key, args=[obj.id])
    return '<a href="{0!s}">{1!s} (#{2!s})</a>'.format(url, self.content_type, obj.pk)

content_object_link.allow_tags = True
content_object_link.short_description = 'Object'


class KeyActionAdmin(admin.ModelAdmin):
    fields = ('notes',)
    list_display = ('id', 'created', key_link, 'action',
                    content_object_link, 'notes')
    list_filter = ('action', 'content_type')
    ordering = ('-id',)
    search_fields = ('action', 'key__key', 'key__user__username', 'notes')


admin.site.register(Key, KeyAdmin)
admin.site.register(KeyAction, KeyActionAdmin)
