from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import Member, Provider, Procedure, Claim, IdempotencyRecord
from .services import ClaimProcessorService

User = get_user_model()

class ClaimAdjudicationTests(TestCase):
    """
    Business Logic Tests for the Health Claims Adjudication Engine.
    These tests verify the 4 core rules and the idempotency safety.
    """

    def setUp(self):
        # Create a test user for log context
        self.user = User.objects.create_user(
            username="processor", 
            email="processor@healthclaims.ai", 
            password="password123"
        )

        # 1. Setup Member (Active with 40k balance)
        self.member = Member.objects.create(
            member_id="M123",
            first_name="John",
            last_name="Doe",
            is_active=True,
            benefit_balance=Decimal("40000.00")
        )

        # 2. Setup Provider
        self.provider = Provider.objects.create(
            provider_code="H456",
            name="Agha Khan University Hospital"
        )

        # 3. Setup Procedure (Avg cost 10k)
        self.procedure = Procedure.objects.create(
            code="P001",
            name="Consultation",
            average_cost=Decimal("10000.00")
        )

        self.valid_payload = {
            "member_id": self.member.member_id,
            "provider_id": self.provider.provider_code,
            "procedure_code": self.procedure.code,
            "claim_amount": Decimal("5000.00"),
            "diagnosis_code": "D001",
            "user_id": self.user.id
        }

    def test_rule_1_member_eligibility(self):
        """Rule 1: If member is inactive, status must be REJECTED."""
        self.member.is_active = False
        self.member.save()

        claim = ClaimProcessorService.process(**self.valid_payload)
        
        self.assertEqual(claim.status, "REJECTED")
        self.assertEqual(claim.approved_amount, 0)
        self.assertIn("inactive", claim.comment.lower())

    def test_rule_2_fraud_detection(self):
        """Rule 2: Flag as fraud if amount > 2x procedure average cost."""
        # The avg cost is 10k, so 25k is > 20k
        payload = self.valid_payload.copy()
        payload["claim_amount"] = Decimal("25000.00")

        claim = ClaimProcessorService.process(**payload)
        
        self.assertTrue(claim.fraud_flag)
        self.assertIn("suspicious", claim.comment.lower())

    def test_rule_3_balance_exhausted(self):
        """Rule 3: If balance is 0, status must be REJECTED."""
        self.member.benefit_balance = Decimal("0.00")
        self.member.save()

        claim = ClaimProcessorService.process(**self.valid_payload)
        
        self.assertEqual(claim.status, "REJECTED")
        self.assertEqual(claim.approved_amount, 0)

    def test_rule_4_partial_approval_capping(self):
        """Rule 4: If claim > balance, approve only up to the remaining balance."""
        self.member.benefit_balance = Decimal("2000.00")
        self.member.save()

        # Requesting 5000, but only have 2000 left
        claim = ClaimProcessorService.process(**self.valid_payload)
        
        self.assertEqual(claim.status, "PARTIAL")
        self.assertEqual(claim.approved_amount, Decimal("2000.00"))
        
        # Verify member balance is now 0
        self.member.refresh_from_db()
        self.assertEqual(self.member.benefit_balance, 0)

    def test_successful_approval_flow(self):
        """Tests the happy path: full approval and balance deduction."""
        claim = ClaimProcessorService.process(**self.valid_payload)
        
        self.assertEqual(claim.status, "APPROVED")
        self.assertEqual(claim.approved_amount, Decimal("5000.00"))
        
        # Verify balance was deducted: 40k - 5k = 35k
        self.member.refresh_from_db()
        self.assertEqual(self.member.benefit_balance, Decimal("35000.00"))

    def test_idempotency_prevents_double_deduction(self):
        """Safety: Re-sending the same key should NOT deduct balance twice."""
        key = "unique-request-123"
        
        # First request
        claim1 = ClaimProcessorService.process(**self.valid_payload, idempotency_key=key)
        self.member.refresh_from_db()
        balance_after_first = self.member.benefit_balance # 35,000

        # Second request with SAME key
        claim2 = ClaimProcessorService.process(**self.valid_payload, idempotency_key=key)
        self.member.refresh_from_db()
        
        # Assertions
        self.assertEqual(claim1.id, claim2.id) # Should be the same object
        self.assertEqual(self.member.benefit_balance, balance_after_first) # Balance shouldn't change
        
        # Ensure only 1 record exists in DB for this key
        self.assertEqual(IdempotencyRecord.objects.filter(idempotency_key=key).count(), 1)