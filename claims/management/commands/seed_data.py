from django.core.management.base import BaseCommand
from claims.models import Member, Provider, Procedure

class Command(BaseCommand):
    help = 'Seeds diverse scenarios for Ginja AI Claims Demo Adjudication'

    def handle(self, *args, **kwargs):
        # All monetary values in this seed data are in Kenyan Shillings (KES).
        self.stdout.write("Cleaning existing records...")
        Member.objects.all().delete()
        Provider.objects.all().delete()
        Procedure.objects.all().delete()

        # 1. THE STANDARD (A claim that has a Full Approval)
        Member.objects.create(member_id="M123", first_name="Nemwel", last_name="Active", benefit_balance=50000.00, is_active=True)

        # 2. THE BROKE (A claim with Zero Balance Rejection)
        Member.objects.create(member_id="M777", first_name="John", last_name="Empty", benefit_balance=0.00, is_active=True)

        # 3. THE INACTIVE (A claim with Eligibility Rejection)
        Member.objects.create(member_id="M999", first_name="Sarah", last_name="Expired", benefit_balance=100000.00, is_active=False)

        # 4. THE LOW LIMIT (A claim with Partial Approval/Capping)
        Member.objects.create(member_id="M555", first_name="Alice", last_name="Capped", benefit_balance=2000.00, is_active=True)

        # PROVIDER
        Provider.objects.create(provider_code="H456", name="Aga Khan University Hospital")

        # PROCEDURES
        Procedure.objects.create(code="P001", name="Dental Surgery", average_cost=5000.00) # Threshold for fraud: KES 10k
        Procedure.objects.create(code="P002", name="Consultation", average_cost=1500.00)

        self.stdout.write(self.style.SUCCESS('Successfully seeded all Adjudication Scenarios!'))