from django.contrib import admin

from blockfarm.models import Program

__all__ = 'ProgramAdmin',


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    search_fields = [
        'id__exact'
    ]

    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
