from django.contrib import admin

from blockfarm.models import Account

__all__ = 'AccountAdmin',


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
