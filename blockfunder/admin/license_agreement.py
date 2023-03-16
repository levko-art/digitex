from django.contrib import admin

from blockfunder.models import LicenseAgreement, LicenseAgreementConfirmation

__all__ = 'LicenseAgreement', 'LicenseAgreementAdmin',


@admin.register(LicenseAgreement)
class LicenseAgreementAdmin(admin.ModelAdmin):
    search_fields = [
        'id__exact'
    ]

    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]


@admin.register(LicenseAgreementConfirmation)
class LicenseAgreementConfirmationAdmin(admin.ModelAdmin):
    search_fields = [
        'id__exact'
    ]

    def get_list_display(self, request):
        return [f.name for f in self.model._meta.fields]
