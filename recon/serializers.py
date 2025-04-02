from recon.models import AutoReconResult
from rest_framework import serializers


class AutoReconSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoReconResult
        fields = "__all__"
