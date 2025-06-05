from rest_framework import serializers
from django.contrib.auth.models import User
from .models import AuditProject, AuditTask, ProjectDocument # Added ProjectDocument


class AuditProjectSerializer(serializers.ModelSerializer):
    # To make project_manager more readable in responses, you could use:
    # project_manager_username = serializers.StringRelatedField(source='project_manager.username', read_only=True)
    # project_manager = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    # Or, for simpler setup now, rely on default (which is PrimaryKeyRelatedField)
    # and potentially customize it later in the ViewSet or with a more specific serializer.

    class Meta:
        model = AuditProject
        fields = [
            'id',
            'name',
            'description',
            'scope',
            'objectives',
            'project_manager', # This will be user ID by default
            # 'project_manager_username', # If using StringRelatedField for display
            'status',
            'start_date',
            'end_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at') # These are set automatically

    # Optional: If you want to return the username along with the ID for project_manager
    # without adding a separate field like project_manager_username, you can customize to_representation
    # or use a nested serializer for User (e.g., a simple UserSerializer).
    # For now, keeping it simple as per subtask instructions. Default is fine.
    # Example of more detailed project_manager representation:
    # project_manager = serializers.HyperlinkedRelatedField(view_name='user-detail', read_only=True) # if you have a user-detail view
    # project_manager_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), source='project_manager', write_only=True, allow_null=True)
    # project_manager_name = serializers.StringRelatedField(source='project_manager', read_only=True)

    # def create(self, validated_data):
    #     # Example: if you needed to set the project_manager based on the request user
    #     # if 'project_manager' not in validated_data and self.context['request'].user.is_authenticated:
    #     #     validated_data['project_manager'] = self.context['request'].user
    #     return super().create(validated_data)


class AuditTaskSerializer(serializers.ModelSerializer):
    # project = serializers.PrimaryKeyRelatedField(queryset=AuditProject.objects.all())
    # assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True)
    # project_name = serializers.StringRelatedField(source='project.name', read_only=True)
    # assignee_username = serializers.StringRelatedField(source='assignee.username', read_only=True)

    class Meta:
        model = AuditTask
        fields = [
            'id',
            'project', # This will be project ID by default
            # 'project_name', # If using StringRelatedField for display
            'name',
            'description',
            'assignee', # This will be user ID by default
            # 'assignee_username', # If using StringRelatedField for display
            'status',
            'due_date',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ('created_at', 'updated_at')


class ProjectDocumentSerializer(serializers.ModelSerializer):
    # uploaded_by = serializers.PrimaryKeyRelatedField(read_only=True) # Default is fine
    uploaded_by_username = serializers.StringRelatedField(source='uploaded_by.username', read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectDocument
        fields = [
            'id',
            'project',
            'task',
            'name',
            'description',
            'file', # Handled by DRF's FileField for uploads
            'file_url', # To provide a direct URL to the file
            'uploaded_by', # Will be read_only due to ViewSet override
            'uploaded_by_username', # For easier display on frontend
            'uploaded_at'
        ]
        read_only_fields = ('uploaded_at', 'uploaded_by') # uploaded_by is set in perform_create

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
