from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ClaimRequestSerializer, ClaimResponseSerializer
from .services import ClaimProcessorService
from .models import Claim

class ClaimCreateView(generics.CreateAPIView):
    """
    Entry point for new claim submissions.
    Extracts idempotency headers and orchestrates with the Service Layer.
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
        
        # Capture the safety key from headers
        idempotency_key = request.headers.get('X-Idempotency-Key')

        # Pass to service with user context for logging
        claim = ClaimProcessorService.process(
            **serializer.validated_data,
            user_id=request.user.id,
            idempotency_key=idempotency_key
        )
        
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