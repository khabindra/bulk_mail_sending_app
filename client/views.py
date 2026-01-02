
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from mailings.models import MailLog
from users.permissions import IsClientUserRole
from .serializers import ClientSerializer


class ClientMailHistoryAPIView(APIView):
    """
    Client can view their own mail history
    """
    permission_classes = [IsAuthenticated, IsClientUserRole]

    def get(self, request):
        client = request.user.client_profile

        logs = (
            MailLog.objects
            .filter(client=client)
            .select_related('mail_type')
            .order_by('-sent_at')
        )

        data = [
            {
                "id": log.id,
                "mail_type": log.mail_type.name,
                "subject": log.subject,
                "body": log.body,
                "sent_at": log.sent_at,
                "status": log.status,
            }
            for log in logs
        ]

        return Response(data, status=status.HTTP_200_OK)


class ClientDetailAPIView(APIView):
    """
    Retrieve, update, or delete logged-in client profile
    """
    permission_classes = [IsAuthenticated, IsClientUserRole]

    def get_client(self, user):
        return user.client_profile

    def get(self, request):
        client = self.get_client(request.user)
        serializer = ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        client = self.get_client(request.user)
        serializer = ClientSerializer(
            client,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request):
        client = self.get_client(request.user)
        client.delete()

        return Response(
            {"detail": "Client deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
