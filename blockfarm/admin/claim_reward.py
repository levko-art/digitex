from django.contrib import admin

from blockfarm.models import ClaimReward

__all__ = 'ClaimRewardAdmin',


@admin.register(ClaimReward)
class ClaimRewardAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
