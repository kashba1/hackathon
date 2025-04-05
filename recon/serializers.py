from recon.models import AutoReconResult, RawMt940Transaction, RawSapPayment
from rest_framework import serializers


class AutoReconSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutoReconResult
        fields = "__all__"


class RawSapSerializer(serializers.ModelSerializer):
    class Meta:
        model = RawSapPayment
        fields = "__all__"


class RawMt940serializer(serializers.ModelSerializer):
    class Meta:
        model = RawMt940Transaction
        fields = "__all__"
