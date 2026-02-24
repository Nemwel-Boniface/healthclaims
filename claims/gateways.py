from .models import Member, Provider, Procedure
from rest_framework.exceptions import NotFound

class InsurerGateway:
    """
    Implement the Gateway Pattern.
    This class isolates the 'where' and 'how' we find data. 
    If Health claims eventually moves Member data to an external API, 
    we only have to change this file, leaving our Services untouched.
    """
    @staticmethod
    def get_member(member_id):
        try:
            return Member.objects.get(member_id=member_id)
        except Member.DoesNotExist:
            raise NotFound(f"Member with ID {member_id} not found in our records.")

    @staticmethod
    def get_provider(provider_code):
        try:
            return Provider.objects.get(provider_code=provider_code)
        except Provider.DoesNotExist:
            raise NotFound(f"Healthcare Provider {provider_code} is not registered.")

    @staticmethod
    def get_procedure(procedure_code):
        try:
            return Procedure.objects.get(code=procedure_code)
        except Procedure.DoesNotExist:
            raise NotFound(f"Medical Procedure code {procedure_code} is invalid.")