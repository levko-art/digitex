from rest_framework import serializers


class FixedDecimalField(serializers.DecimalField):
    def __init__(self, *args, **kwargs):
        kwargs['max_digits'] = 36
        kwargs['decimal_places'] = 18
        super().__init__(*args, **kwargs)
