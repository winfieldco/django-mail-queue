#---------------------------------------------#
#
# Mailer will queue up emails, Try to send them
# and keep track of if they are sent or not.
# Should be executed with a cron job.
#
#---------------------------------------------#
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import datetime
import logging
import os

logger = logging.getLogger(__name__)

from django.utils import timezone
from django.db import models
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import celery

from . import defaults
from .utils import get_storage

class MailerMessageManager(models.Manager):
    def send_queued(self, limit=None):
        if limit is None:
            limit = getattr(settings, 'MAILQUEUE_LIMIT', defaults.MAILQUEUE_LIMIT)

        for email in self.filter(sent=False)[:limit]:
            email.send_mail()

    def clear_sent_messages(self, offset=None):
        """ Deletes sent MailerMessage records """
        if offset is None:
            offset = getattr(settings, 'MAILQUEUE_CLEAR_OFFSET', defaults.MAILQUEUE_CLEAR_OFFSET)

        if type(offset) is int:
            offset = datetime.timedelta(hours=offset)

        delete_before = timezone.now() - offset
        self.filter(sent=True, last_attempt__lte=delete_before).delete()


@python_2_unicode_compatible
class MailerMessage(models.Model):
    subject = models.CharField(_('Subject'), max_length=250, blank=True)
    to_address = models.TextField(_('To'))
    bcc_address = models.TextField(_('BCC'), blank=True)
    from_address = models.EmailField(_('From'), max_length=250)
    reply_to = models.TextField(_('Reply to'), max_length=250, blank=True, null=True)
    content = models.TextField(_('Content'), blank=True)
    html_content = models.TextField(_('HTML Content'), blank=True)
    app = models.CharField(_('App'), max_length=250, blank=True)
    sent = models.BooleanField(_('Sent'), default=False, editable=False)
    last_attempt = models.DateTimeField(_('Last attempt'), auto_now=False, auto_now_add=False, blank=True, null=True, editable=False)

    objects = MailerMessageManager()

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')

    def __str__(self):
        return self.subject

    def add_header(self, name, value):

        if self.pk is None:
            self._save_without_sending()

        Header.objects.create(email=self, name=name, value=value)

    def add_attachment(self, attachment):
        """
        Takes a Django `File` object and creates an attachment for this mailer message.
        """
        if self.pk is None:
            self._save_without_sending()

        Attachment.objects.create(email=self, file_attachment=attachment)

    def _save_without_sending(self, *args, **kwargs):
        """
        Saves the MailerMessage instance without sending the e-mail. This ensures
        other models (e.g. `Attachment`) have something to relate to in the database.
        """
        self.do_not_send = True
        super(MailerMessage, self).save(*args, **kwargs)

    def send_mail(self):
        """ Public api to send mail.  Makes the determinination
         of using celery or not and then calls the appropriate methods.
        """

        if getattr(settings, 'MAILQUEUE_CELERY', defaults.MAILQUEUE_CELERY):
            from mailqueue.tasks import send_mail
            send_mail.delay(self.pk)
        else:
            self._send()

    def _send(self):
        if not self.sent:

            self.last_attempt = timezone.now()

            headers = {}
            for header in self.header_set.all():
                headers[header.name] = header.value            

            subject, from_email = self.subject, self.from_address
            text_content = self.content
            
            msg = EmailMultiAlternatives(subject, text_content, from_email, headers=headers)
            
            if self.reply_to:
                msg.extra_headers.update({"reply-to": self.reply_to})

            if self.html_content:
                html_content = self.html_content
                msg.attach_alternative(html_content, "text/html")

            msg.to = [email.strip() for email in self.to_address.split(',') if email.strip()]
            msg.bcc = [email.strip() for email in self.bcc_address.split(',') if email.strip()]

            # Add any additional attachments
            for attachment in self.attachment_set.all():
                msg.attach_file(os.path.join(settings.MEDIA_ROOT, attachment.file_attachment.name))
            try:
                msg.send()
                self.sent = True
            except Exception as e:
                self.do_not_send = True
                raise Exception('Mail Queue Exception: {0}'.format(e))
            self.save()

@python_2_unicode_compatible
class Header(models.Model):
    name = models.CharField(_('Name'), max_length=250)
    value = models.CharField(_('Value'), max_length=250)
    email = models.ForeignKey(MailerMessage, blank=True, null=True)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class Attachment(models.Model):
    file_attachment = models.FileField(storage=get_storage(), upload_to='mail-queue/attachments', blank=True, null=True)
    email = models.ForeignKey(MailerMessage, blank=True, null=True)

    class Meta:
        verbose_name = _('Attachment')
        verbose_name_plural = _('Attachments')

    def __str__(self):
        return self.file_attachment.name

@receiver(post_save, sender=MailerMessage)
def send_post_save(sender, instance, signal, *args, **kwargs):
    if getattr(instance, "do_not_send", False):
        instance.do_not_send = False
        return

    if not getattr(settings, 'MAILQUEUE_QUEUE_UP', defaults.MAILQUEUE_QUEUE_UP):
        # If mail queue up is set, wait for the cron or management command
        # to send any email.
        instance.send_mail()
