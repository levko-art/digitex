from django.contrib import admin

from blockfarm.models import Wallet

__all__ = 'WalletAdmin',


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    search_fields = [
        'id__exact',
    ]
    list_filter = [
        'type',
    ]

    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
