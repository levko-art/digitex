from django.contrib import admin

from blockfarm.models import Reward

__all__ = 'RewardAdmin',


@admin.register(Reward)
class RewardAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
