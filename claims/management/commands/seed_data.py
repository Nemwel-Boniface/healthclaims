from django.core.management.base import BaseCommand
from claims.models import Member, Provider, Procedure

class Command(BaseCommand):
    """
    Custom Django Management Command to provide a 'Ready-to-Test' environment.
    Usage: python manage.py seed_data
    """
    help = 'Seeds initial data for Ginja AI Claims Demo'

    def handle(self, *args, **kwargs):
        self.stdout.write("Cleaning existing records...")
        Member.objects.all().delete()
        Provider.objects.all().delete()
        Procedure.objects.all().delete()

        # Create M123 - The Standard Test Member
        Member.objects.create(
            member_id="M123", 
            first_name="Nemwel", 
            last_name="Dev", 
            benefit_balance=40000.00,
            is_active=True
        )

        # Create H456 - The Standard Test Provider
        Provider.objects.create(
            provider_code="H456", 
            name="Aga Khan University Hospital"
        )

        # Create P001 - The Standard Test Procedure (Avg Cost: 5k)
        Procedure.objects.create(
            code="P001", 
            name="Dental Surgery", 
            average_cost=5000.00
        )

        self.stdout.write(self.style.SUCCESS('Successfully seeded Ginja Health Claims data!'))