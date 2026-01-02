from rest_framework import serializers
from .models import SenderEmail, MailLog

class SenderEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SenderEmail
        fields = ['id', 'name', 'email']

class MailLogListSerializer(serializers.ModelSerializer):
    # IMPROVEMENT: Use source for read-only nested data
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = MailLog
        fields = [
            'id', 'client', 'client_name', 'subject', 'status', 'status_display',
            'sent_at', 'campaign_name', 'mail_type'
        ]

class MailLogDetailSerializer(serializers.ModelSerializer):
    # IMPROVEMENT: Include nested objects for better detail view context
    client_name = serializers.CharField(source='client.company_name', read_only=True)
    mail_type_name = serializers.CharField(source='mail_type.name', read_only=True)
    sender_info = serializers.SerializerMethodField()

    class Meta:
        model = MailLog
        fields = '__all__'
        read_only_fields = ['id', 'sent_at'] # sent_at is auto_now_add

    def get_sender_info(self, obj):
        if obj.sender_email:
            return SenderEmailSerializer(obj.sender_email).data
        return None

# class AdminBulkMailSerializer(serializers.Serializer):
#     # IMPROVEMENT: Tighten validation. client_id should likely be an Integer or a CSV string.
#     # Assuming CSV string based on your view logic.
#     client_id = serializers.CharField(help_text="Comma separated IDs or single ID")
#     mail_type_id = serializers.IntegerField()
#     sender_id = serializers.IntegerField()
#     subject = serializers.CharField(required=False, allow_blank=True)
#     message = serializers.CharField(required=False, allow_blank=True)
    
#     attachment_ids = serializers.ListField(
#         child=serializers.IntegerField(),
#         required=False
#     )
#     def validate_client_id(self, value):
#         """Ensure client_ids are integers"""
#         try:
#             # Basic validation logic can go here, or leave it to the view
#             return value
#         except ValueError:
#             raise serializers.ValidationError("Invalid ID format.")



# serializers.py
class AdminBulkMailSerializer(serializers.Serializer):
    # campaign_name is new updated one-------------------------
    campaign_name = serializers.CharField(required=False, allow_blank=True)
    client_id = serializers.CharField(help_text="Comma separated IDs or single ID")
    mail_type_id = serializers.IntegerField()
    sender_id = serializers.IntegerField()
    subject = serializers.CharField(required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    
    # ✅ REMOVED: attachment_ids field completely
    
    def validate_client_id(self, value):
        """Ensure client_ids are integers"""
        try:
            # Try to parse as integers
            
            return value
        except ValueError:
            raise serializers.ValidationError("Invalid client ID format. Use comma-separated integers.")
    
    def validate_mail_type_id(self, value):
        """Validate mail_type exists"""
        from templates.models import MailType
        if not MailType.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid mail_type_id")
        return value
    



class EmailPreviewSerializer(serializers.Serializer):
    client_id = serializers.IntegerField()
    mail_type_id = serializers.IntegerField()
    sender_id = serializers.IntegerField()
    message = serializers.CharField(required=False, allow_blank=True)
    
class EmailPreviewResponseSerializer(serializers.Serializer):
    """
    Serializer to structure the JSON response
    """
    subject = serializers.CharField()
    recipient_email = serializers.CharField()
    recipient_name = serializers.CharField()
    html_content = serializers.CharField(help_text="The rendered HTML to display in an iframe")