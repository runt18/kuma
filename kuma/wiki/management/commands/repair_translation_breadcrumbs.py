"""
Repair breadcrumb relations for translations that are missing parent topics.
"""
import logging

from django.core.management.base import (BaseCommand)

from kuma.wiki.models import Document


class Command(BaseCommand):

    help = "Repair breadcrumb trails for translations"

    def handle(self, *args, **options):

        # Gather up docs that claim to be translations,
        # but have no topic parents.
        # https://bugzilla.mozilla.org/show_bug.cgi?id=792417#c2
        docs = (Document.objects
                .exclude(parent__exact=None)
                .filter(parent_topic__exact=None))

        logging.debug("Attempting breadcrumb repair for {0!s} translations".format(
                      (docs.count())))

        for doc in docs:
            doc.acquire_translated_topic_parent()
            if not doc.parent_topic:
                # Some translated pages really don't end up needing a
                # breadcrumb repair, but we don't really know until we try and
                # come up empty handed.
                logging.debug(u'\t(root) -> /{0!s}/docs/{1!s}'.format(
                    doc.locale, doc.slug))
            else:
                # We got a new parent topic, so save and report the result
                doc.save()
                logging.debug(u'\t/{0!s}/docs/{1!s} -> /{2!s}/docs/{3!s}'.format(
                    doc.parent_topic.locale, doc.parent_topic.slug,
                    doc.locale, doc.slug))
