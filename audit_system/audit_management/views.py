from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, parsers # Added parsers for FileUpload
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


import csv
import io
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, Q

from .models import AuditProject, AuditTask, ProjectDocument # Added ProjectDocument
from .serializers import AuditProjectSerializer, AuditTaskSerializer, ProjectDocumentSerializer # Added ProjectDocumentSerializer


class HelloView(APIView):
    """
    A simple view to test JWT authentication.
    """
    permission_classes = (IsAuthenticated,) # Ensures only authenticated users can access

    def get(self, request):
        content = {
            'message': f'Hello, {request.user.username}! You are authenticated.',
            'user_id': request.user.id,
            'user_email': request.user.email,
            # Add any other user details you want to return
        }
        return Response(content)


class AuditProjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AuditProjects to be viewed or edited.
    """
    queryset = AuditProject.objects.all().order_by('-created_at') # Added default ordering
    serializer_class = AuditProjectSerializer
    permission_classes = [IsAuthenticated] # Ensures only authenticated users can access

    # Optional: You could override methods like perform_create to set project_manager automatically
    # def perform_create(self, serializer):
    #     if self.request.user.is_authenticated:
    #         serializer.save(project_manager=self.request.user)
    #     else:
    #         # Handle cases where user might not be set, or raise PermissionDenied
    #         # This depends on how strictly you want to enforce project_manager assignment
    #         serializer.save()


class AuditTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows AuditTasks to be viewed or edited.
    Note: For a more advanced setup, consider using drf-nested-routers
    to allow accessing tasks via /api/audit/projects/<project_pk>/tasks/.
    For now, tasks are accessed via /api/audit/tasks/.
    """
    queryset = AuditTask.objects.all().select_related('project', 'assignee').order_by('project__name', 'created_at')
    serializer_class = AuditTaskSerializer
    permission_classes = [IsAuthenticated]

    # Optional: Filter queryset based on the project if a project_pk is in URL
    # def get_queryset(self):
    #     """
    #     Optionally restricts the returned tasks to a given project,
    #     by filtering against a `project_pk` query parameter in the URL.
    #     """
    #     queryset = super().get_queryset()
    #     project_pk = self.kwargs.get('project_pk') # If using nested routers
    #     if project_pk:
    #         queryset = queryset.filter(project__pk=project_pk)
    #     return queryset


class ProjectDocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows ProjectDocuments to be viewed or edited.
    Handles file uploads.
    """
    queryset = ProjectDocument.objects.all().select_related('project', 'task', 'uploaded_by').order_by('-uploaded_at')
    serializer_class = ProjectDocumentSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser] # Add parsers for file uploads

    def perform_create(self, serializer):
        """
        Automatically set the uploaded_by field to the current user.
        """
        serializer.save(uploaded_by=self.request.user)


class DashboardSummaryView(APIView):
    """
    Provides aggregated statistics for the dashboard.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Project Status Statistics
        project_status_summary = list(
            AuditProject.objects.values('status')
            .annotate(count=Count('status'))
            .order_by('status')
        ) # Using list() to execute the query and make it serializable

        # Task Status Statistics
        task_status_summary = list(
            AuditTask.objects.values('status')
            .annotate(count=Count('status'))
            .order_by('status')
        )

        # Overdue Tasks Count
        # Tasks are overdue if their due_date is in the past and their status is not 'Completed' or 'Cancelled' (or any other final state)
        # Note: Adjust 'final_statuses' based on your actual workflow for tasks.
        final_statuses = ['Completed'] # Add other statuses like 'Cancelled' if applicable
        overdue_tasks_count = AuditTask.objects.filter(
            due_date__lt=timezone.now().date(),
        ).exclude(status__in=final_statuses).count()

        # Recently Completed Projects (e.g., in the last 30 days) - Example of another stat
        # recent_completion_cutoff = timezone.now() - timezone.timedelta(days=30)
        # recently_completed_projects_count = AuditProject.objects.filter(
        #     status='Completed',
        #     end_date__gte=recent_completion_cutoff
        # ).count()


        # Example Response Structure:
        # {
        #   "project_summary": [
        #     {"status": "Pending", "count": 10},
        #     {"status": "In Progress", "count": 5}, ...
        #   ],
        #   "task_summary": [
        #     {"status": "To Do", "count": 50},
        #     {"status": "In Progress", "count": 25}, ...
        #   ],
        #   "overdue_tasks_count": 15
        # }
        return Response({
            "project_status_summary": project_status_summary,
            "task_status_summary": task_status_summary,
            "overdue_tasks_count": overdue_tasks_count,
            # "recently_completed_projects_count": recently_completed_projects_count,
        })


class AuditProjectCSVReportView(APIView):
    """
    Generates a CSV report of all audit projects.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_projects_report.csv"'

        writer = csv.writer(response)

        # Define CSV header
        header = [
            "Project Name",
            "Project Manager",
            "Status",
            "Start Date",
            "End Date",
            "Description",
            "Scope",
            "Objectives"
        ]
        writer.writerow(header)

        # Fetch projects and select relevant fields
        # Using select_related for project_manager to optimize DB query if accessing user.username
        projects = AuditProject.objects.all().select_related('project_manager').order_by('name')

        for project in projects:
            manager_username = project.project_manager.username if project.project_manager else ""
            writer.writerow([
                project.name,
                manager_username,
                project.status,
                project.start_date.strftime('%Y-%m-%d') if project.start_date else "",
                project.end_date.strftime('%Y-%m-%d') if project.end_date else "",
                project.description or "",
                project.scope or "",
                project.objectives or ""
            ])

        return response
