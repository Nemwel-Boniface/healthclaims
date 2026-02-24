from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ClaimRequestSerializer, ClaimResponseSerializer
from .services import ClaimProcessorService
from .models import Claim

class ClaimCreateView(generics.CreateAPIView):
    """
    API endpoint that allows hospitals/providers to submit a new health claim.
    
    Attributes of this view:
        permission_classes: Ensures only authenticated staff can submit claims.
        serializer_class: Uses the ClaimRequestSerializer to validate incoming JSON data.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ClaimRequestSerializer

    def create(self, request, *args, **kwargs):
        """
        Overrides the default create method to bypass standard model creation.
        Instead, it handsoff the validated data to the ClaimProcessorService 
        to execute business rules (fraud checks, balance deductions, etc.).
        """
        # Initialize serializer with request data
        serializer = self.get_serializer(data=request.data)
        
        # Trigger validation; raises 400 Bad Request if data is malformed
        serializer.is_valid(raise_exception=True)
        
        # Hand off to the Service Layer (The Brain) for adjudication
        # **serializer.validated_data unpacks keys as arguments to the service
        claim = ClaimProcessorService.process(**serializer.validated_data)
        
        # Return the processed claim using the response serializer
        return Response(
            ClaimResponseSerializer(claim).data, 
            status=status.HTTP_201_CREATED
        )

class ClaimDetailView(generics.RetrieveAPIView):
    """
    API endpoint to retrieve the status and details of a specific claim.
    
    Attributes:
        lookup_field: Uses the 'id' (UUID) to identify the record in the database.
    """
    permission_classes = [IsAuthenticated]
    queryset = Claim.objects.all()
    serializer_class = ClaimResponseSerializer
    lookup_field = 'id'