from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from .managers import IPBanManager
from .jobs import IPBanJob


class IPBan(models.Model):
    ip = models.GenericIPAddressField()
    created = models.DateTimeField(default=timezone.now, db_index=True)
    deleted = models.DateTimeField(null=True, blank=True)

    objects = IPBanManager()

    def delete(self, *args, **kwargs):
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return u'{0!s} banned on {1!s}'.format(self.ip, self.created)


@receiver(models.signals.post_save, sender=IPBan)
@receiver(models.signals.pre_delete, sender=IPBan)
def invalidate_ipban_caches(sender, instance, **kwargs):
    IPBanJob().invalidate(instance.ip)
