# -*- encoding: utf-8 -*-
from __future__ import unicode_literals
from operator import attrgetter
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db.models import permalink
from django.utils.encoding import force_text
from django.utils.text import Truncator
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django_extensions.db.fields.json import JSONField


BILL_STATUS_CHOICES = (
    ('draft', _('Draft')),
    ('published', _('Published')),
    ('closed', _('Closed'))
)


def model_repr(cls, **kwargs):
    values = kwargs.items()
    values = ((force_text(k), Truncator(force_text(v)).chars(50)) for (k, v) in values)
    values = ('='.join(kv) for kv in values)
    values = '; '.join(values)
    return ''.join((cls.__name__, '{', values, '}'))


class TimestampedMixin(models.Model):
    created = models.DateTimeField(_('created'), editable=False, blank=True, auto_now_add=True)
    modified = models.DateTimeField(_('modified'), editable=False, blank=True, auto_now=True)

    class Meta:
        abstract = True


class GenericData(models.Model):
    """
    Attach any data to any object. That's the way we do it, baby.

    TODO We should really come up with a small framework to deal with our generic data stuff.
    """
    data = JSONField(_('data'))
    type = models.CharField(_('type'), max_length=100)
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey('contenttypes.ContentType')
    content_object = GenericForeignKey('content_type', 'object_id')


class Bill(TimestampedMixin):
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'))
    status = models.CharField(_('status'), max_length=20, choices=BILL_STATUS_CHOICES, default='1')

    editors = models.ManyToManyField(
        'auth.Group', verbose_name=_('editors'), blank=True,
        help_text=_('Any users in any of these groups will '
                    'have permission to change this document.'))

    metadata = GenericRelation('GenericData')

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = _('bill')
        verbose_name_plural = _('bills')

    @permalink
    def get_absolute_url(self):
        return 'show_bill', [self.pk], {}

    @property
    def content(self):
        return '\n\n'.join(map(attrgetter('content'), self.segments.all()))


class BillSegment(TimestampedMixin):
    bill = models.ForeignKey('core.Bill', related_name='segments', verbose_name=_('bill'))
    order = models.PositiveIntegerField(_('order'), default=0)
    content = models.TextField(_('content'))

    TYPE_CHOICES = (
        ('title', _('Title')),
        ('article', _('Article')),
    )
    type = models.CharField(_('type'), max_length=64, choices=TYPE_CHOICES)

    class Meta:
        ordering = ('order',)
        verbose_name = _('segment')
        verbose_name_plural = _('segments')

    def __unicode__(self):
        return '{bill}: {content}'.format(
            bill=self.bill, content=Truncator(self.content).chars(100))

    def is_editable(self):
        # Currently, only articles are editable.
        return self.type == 'article'

    def get_absolute_url(self):
        return reverse('show_segment', args=[self.bill.id, self.id])


class CitizenAmendment(TimestampedMixin):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('author'))
    segment = models.ForeignKey('core.BillSegment', related_name='amendments', verbose_name=_('bill segment'))
    content = models.TextField(_('content'))

    class Meta:
        verbose_name = _('citizen amendment')
        verbose_name_plural = _('citizen amendments')

    def __unicode__(self):
        return model_repr(CitizenAmendment, author=self.author,
                          segment=self.segment, content=self.content)

    def original_content(self):
        return self.segment.content

    def html_id(self):
        return 'amendment-{0}'.format(self.pk)

    @permalink
    def get_absolute_url(self):
        return 'show_amendment', [self.pk]


class UpDownVote(TimestampedMixin):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('user'))
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey('contenttypes.ContentType')
    content_object = GenericForeignKey('content_type', 'object_id')
    vote = models.BooleanField(choices=((True, _('Up Vote')), (False, _('Down Vote'))))

    class Meta:
        unique_together = ('user', 'object_id', 'content_type')

    def __unicode__(self):
        return self.user


class Proposition(models.Model):
    bill = models.ForeignKey('core.Bill', verbose_name=_('bill'))
    type = models.CharField(_('type'), max_length=200, null=True, blank=True)
    number = models.CharField(_('number'), max_length=50, null=True, blank=True)
    year = models.CharField(_('year'), max_length=4, null=True, blank=True)
    name_proposition = models.CharField(_('name proposition'), max_length=200, null=True, blank=True)
    id_proposition = models.IntegerField(_('id proposition'), null=True, blank=True)
    id_main_proposition = models.IntegerField(_('id main proposition'), null=True, blank=True)
    name_origin_proposition = models.CharField(_('name origin proposition'), max_length=200, null=True, blank=True)
    theme = models.CharField(_('theme'), max_length=200, null=True, blank=True)
    menu = models.TextField(_('menu'), null=True, blank=True)
    menu_explanation = models.TextField(_('menu_explanation'), null=True, blank=True)
    author = models.CharField(_('author'), max_length=200, null=True, blank=True)
    id_register = models.CharField(_('id register'), max_length=200, null=True, blank=True)
    uf_author = models.CharField(_('uf author'), max_length=200, null=True, blank=True)
    party_author = models.CharField(_('party author'), max_length=200, null=True, blank=True)
    apresentation_date = models.DateField(_('apresentation date'), null=True, blank=True)
    processing_regime = models.CharField(_('processing_regime'), max_length=200, null=True, blank=True)
    last_dispatch_date = models.DateField(_('last dispatch date'), null=True, blank=True)
    last_dispatch = models.TextField(_('last dispatch'), null=True, blank=True)
    appraisal = models.TextField(_('appraisal'), null=True, blank=True)
    indexing = models.TextField(_('indexing'), null=True, blank=True)
    situation = models.CharField(_('situation'), max_length=200, null=True, blank=True)
    content_link = models.URLField(_('content link'), null=True, blank=True)

    class Meta:
        verbose_name = _('proposition')
        verbose_name_plural = _('propositions')

    def __unicode__(self):
        return self.number

