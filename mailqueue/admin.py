from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from .models import MailerMessage, Attachment, Header

class HeaderInline(admin.TabularInline):
    model = Header
    extra = 0

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0

class MailerAdmin(admin.ModelAdmin):
    list_display = ('app', 'id', 'subject', 'to_address', 'sent', 'last_attempt')
    search_fields = ['id', 'to_address', 'subject', 'app', 'bcc_address']
    actions = ['send_failed']
    inlines = [AttachmentInline, HeaderInline]
    list_filter = ['sent']

    def send_failed(self, request, queryset):
        emails = queryset.filter(sent=False)
        for email in emails:
            email.send_mail()
        self.message_user(request, _("Emails queued."))
    send_failed.short_description = _("Send failed")

admin.site.register(MailerMessage, MailerAdmin)