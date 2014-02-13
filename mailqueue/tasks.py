from celery.task import task
from .models import MailerMessage
import logging

@task(name="tasks.send_mail")
def send_mail(pk):
    try:
      message = MailerMessage.objects.get(pk=pk)
      message._send()
    except Exception as e:
      if message:
        logging.error('Unable to send email via mail queue task, to:%s from:%s subject:%s id:%d exception:%s', message.to_address, message.from_address, message.subject, message.id, e)
      else:
        logging.error('Unable to send email via mail queue task %s', e)

@task()
def clear_sent_messages():
    from mailqueue.models import MailerMessage
    MailerMessage.objects.clear_sent_messages()
