from django.contrib import admin

from blockfarm.models import Transaction

__all__ = 'TransactionAdmin',


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    search_fields = [
        'id__exact'
    ]

    list_filter = [
        'type',
        'status',
        'program',
    ]

    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
