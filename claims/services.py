import uuid
import logging
from decimal import Decimal
from django.db import transaction
from .models import Claim, IdempotencyRecord
from .gateways import InsurerGateway

# Initialize logger for adjudication tracking
logger = logging.getLogger('claims_processor')

class ClaimProcessorService:
    """
    Implements validation rules and financial balance updates.
    """
    @staticmethod
    @transaction.atomic
    def process(member_id, provider_id, procedure_code, claim_amount, diagnosis_code, user_id, idempotency_key=None):
        """
        The central intelligence unit for claim adjudication.
        """
        log_ctx = {'user_id': user_id}

        # IDEMPOTENCY CHECK
        if idempotency_key:
            existing = IdempotencyRecord.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                logger.info(f"Duplicate request for key {idempotency_key}. Returning cached claim.", extra=log_ctx)
                return Claim.objects.get(id=existing.claim_id)

        # 1. RETRIEVAL via Gateway
        member = InsurerGateway.get_member(member_id)
        provider = InsurerGateway.get_provider(provider_id)
        procedure = InsurerGateway.get_procedure(procedure_code)

        logger.info(f"Adjudicating: Member:{member_id} | Proc:{procedure_code} | Amt:{claim_amount}", extra=log_ctx)

        status = "APPROVED"
        fraud_flag = False
        approved_amount = claim_amount
        comment = "Claim processed and approved via Health Claims Real-Time Engine."

        # RULE 1: ELIGIBILITY
        if not member.is_active:
            logger.warning(f"REJECTED: Member {member_id} is inactive.", extra=log_ctx)
            return ClaimProcessorService._finalize(member, provider, procedure, claim_amount, 0, "REJECTED", False, "Member policy is currently inactive.", diagnosis_code)

        # RULE 2: FRAUD DETECTION
        if claim_amount > (procedure.average_cost * 2):
            fraud_flag = True
            comment = "Flagged: Requested amount is highly suspicious (Exceeds 2x average cost)."
            logger.info(f"FRAUD FLAG: High cost for {procedure_code}", extra=log_ctx)

        # RULE 3: BENEFIT LIMITS
        if member.benefit_balance <= 0:
            logger.warning(f"REJECTED: Member {member_id} balance exhausted.", extra=log_ctx)
            return ClaimProcessorService._finalize(member, provider, procedure, claim_amount, 0, "REJECTED", fraud_flag, "Annual benefit limit exhausted.", diagnosis_code)

        # RULE 4: PARTIAL APPROVAL (CAP)
        if claim_amount > member.benefit_balance:
            status = "PARTIAL"
            approved_amount = member.benefit_balance
            comment = f"Partial approval: Benefit balance capped at {approved_amount}."
            logger.info(f"PARTIAL: Balance cap hit for Member {member_id}", extra=log_ctx)

        # 2. COMMIT: Balance update and claim creation
        member.benefit_balance -= approved_amount
        member.save()

        claim = ClaimProcessorService._finalize(member, provider, procedure, claim_amount, approved_amount, status, fraud_flag, comment, diagnosis_code)

        # SAVE IDEMPOTENCY
        if idempotency_key:
            IdempotencyRecord.objects.create(idempotency_key=idempotency_key, claim_id=claim.id)

        logger.info(f"SUCCESS: Claim {claim.claim_number} finalized as {status}", extra=log_ctx)
        return claim

    @staticmethod
    def _finalize(member, provider, procedure, requested, approved, status, fraud, comment, diagnosis):
        return Claim.objects.create(
            claim_number=f"CLN-{uuid.uuid4().hex[:8].upper()}",
            member=member, provider=provider, procedure=procedure,
            requested_amount=requested, approved_amount=approved,
            status=status, fraud_flag=fraud, comment=comment, diagnosis_code=diagnosis
        )