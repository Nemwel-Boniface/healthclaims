from rest_framework import serializers
from .models import Claim

class ClaimRequestSerializer(serializers.Serializer):
    """
    Validates the structure of the incoming POST request from hospitals.
    Strict typing here prevents dirty data from reaching the Service Layer.
    """
    member_id = serializers.CharField()
    provider_id = serializers.CharField()
    diagnosis_code = serializers.CharField()
    procedure_code = serializers.CharField()
    claim_amount = serializers.DecimalField(max_digits=12, decimal_places=2)

class ClaimResponseSerializer(serializers.ModelSerializer):
    """
    Standardizes the API response for the Health Claims platform.
    """
    class Meta:
        model = Claim
        fields = ('id', 'claim_number', 'status', 'fraud_flag', 'approved_amount', 'comment')