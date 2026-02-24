import uuid
from decimal import Decimal
from django.db import transaction
from .models import Claim
from .gateways import InsurerGateway

class ClaimProcessorService:
    """
    The central intelligence unit for adjudication. 
    Implements validation rules and financial balance updates.
    """
    @staticmethod
    @transaction.atomic # Ensures balance deduction and claim creation are 'all or nothing'
    def process(member_id, provider_id, procedure_code, claim_amount, diagnosis_code):
        # 1. RETRIEVAL: Get entity context via the claims InsurerGateway
        member = InsurerGateway.get_member(member_id)
        provider = InsurerGateway.get_provider(provider_id)
        procedure = InsurerGateway.get_procedure(procedure_code)

        # Adjudication State Defaults
        status = "APPROVED"
        fraud_flag = False
        approved_amount = claim_amount
        comment = "Claim processed and approved via Health Claims Real-Time Engine."

        # RULE 1: ELIGIBILITY CHECK
        # Rejects the claim immediately if the member's policy is lapsed or inactive.
        if not member.is_active:
            return ClaimProcessorService._finalize(
                member, provider, procedure, claim_amount, 0, "REJECTED", False, "Member policy is currently inactive.", diagnosis_code
            )

        # RULE 2: FRAUD DETECTION
        # Signals potential fraud if claim > 2x the standard average cost for the procedure.
        if claim_amount > (procedure.average_cost * 2):
            fraud_flag = True
            comment = "Flagged: Requested amount is highly suspicious (Exceeds 2x average cost)."

        # RULE 3: BENEFIT LIMITS
        # Rejection if balance is already 0.
        if member.benefit_balance <= 0:
            return ClaimProcessorService._finalize(
                member, provider, procedure, claim_amount, 0, "REJECTED", fraud_flag, "Annual benefit limit exhausted.", diagnosis_code
            )

        # RULE 4: PARTIAL APPROVAL (CAP)
        # If the claim exceeds remaining balance, we only pay out the remaining balance.
        if claim_amount > member.benefit_balance:
            status = "PARTIAL"
            approved_amount = member.benefit_balance
            comment = f"Partial approval: Benefit balance capped at {approved_amount}."

        # 2. COMMIT: Atomically update the member's wallet
        member.benefit_balance -= approved_amount
        member.save()

        # 3. RECORD: Create the final Claim audit record
        return ClaimProcessorService._finalize(
            member, provider, procedure, claim_amount, approved_amount, status, fraud_flag, comment, diagnosis_code
        )

    @staticmethod
    def _finalize(member, provider, procedure, requested, approved, status, fraud, comment, diagnosis):
        """
        Internal helper to persist the result in the Database.
        """
        return Claim.objects.create(
            claim_number=f"CLN-{uuid.uuid4().hex[:8].upper()}",
            member=member, 
            provider=provider, 
            procedure=procedure,
            requested_amount=requested, 
            approved_amount=approved,
            status=status, 
            fraud_flag=fraud, 
            comment=comment, 
            diagnosis_code=diagnosis
        )