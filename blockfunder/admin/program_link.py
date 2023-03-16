from django.contrib import admin

from blockfunder.models import ProgramLink

__all__ = 'ProgramLinkAdmin',


@admin.register(ProgramLink)
class ProgramLinkAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
