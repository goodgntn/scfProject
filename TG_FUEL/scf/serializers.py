from dataclasses import field
from rest_framework import serializers
from scf.models import mytable

class mytableSerializer(serializers.ModelSerializer):
    class Meta:
        model=mytable
        field=  '__all__' 


class file_serializer(serializers.Serializer):
    file = serializers.FileField(required=False)
    class Meta:
        filed = '__all__'


class file_ml_model(serializers.Serializer):
    file = serializers.FileField(required=False)
    class Meta:
        field = '__all__'