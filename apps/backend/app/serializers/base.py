"""
Base serializer with common meta options and utilities.
"""
from rest_framework import serializers


class BaseSerializer(serializers.ModelSerializer):
    """
    Base serializer for all model serializers.
    Provides common meta options and utility methods.
    """

    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        """
        Optionally allow filtering fields via 'fields' kwarg.
        Usage: MySerializer(instance, fields=['id', 'name'])
        """
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            # Drop any fields that are not specified in the `fields` argument
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
