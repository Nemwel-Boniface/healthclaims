from django.db import models
from app.abstracts import TimeStampedModel, UniversalIdModel

class Member(UniversalIdModel, TimeStampedModel):
    """
    This represents the insurance policy holder. 
    We track benefit limits and real-time balances here to prevent over-disbursement.
    """
    member_id = models.CharField(max_length=50, unique=True) # External reference (e.g., M123)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True) # Used for Rule 1: Eligibility
    benefit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=40000.00)
    benefit_balance = models.DecimalField(max_digits=12, decimal_places=2, default=40000.00)

    def __str__(self):
        return f"{self.member_id} - {self.first_name}"

class Provider(UniversalIdModel, TimeStampedModel):
    """
    This represents the medical facility (Hospital/Clinic) submitting the claim.
    """
    provider_code = models.CharField(max_length=50, unique=True) # e.g., H456
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Procedure(UniversalIdModel, TimeStampedModel):
    """
    Medical services or treatments (e.g., Dental Surgery).
    average_cost is the benchmark for our Fraud Detection engine.
    """
    code = models.CharField(max_length=20, unique=True) # e.g., P001
    name = models.CharField(max_length=255)
    average_cost = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Claim(UniversalIdModel, TimeStampedModel):
    """
    This is the immutable ledger of all claim submissions and their adjudication results.
    """
    STATUS_CHOICES = [
        ('APPROVED', 'Approved'),
        ('PARTIAL', 'Partial'),
        ('REJECTED', 'Rejected'),
    ]

    # Unique human-friendly ID (e.g., CLN-A1B2C3D4)
    claim_number = models.CharField(max_length=20, unique=True, editable=False)
    
    # Associations which protect & prevents deletion of members/providers with active history
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='claims')
    provider = models.ForeignKey(Provider, on_delete=models.PROTECT, related_name='claims')
    procedure = models.ForeignKey(Procedure, on_delete=models.PROTECT, related_name='claims')
    
    diagnosis_code = models.CharField(max_length=50)
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    fraud_flag = models.BooleanField(default=False) # Flagged if amount > 2x average_cost
    comment = models.TextField(blank=True, null=True) # Adjudication reasoning

    class Meta:
        db_table = "claims"