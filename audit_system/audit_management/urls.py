from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    HelloView,
    AuditProjectViewSet,
    AuditTaskViewSet,
    ProjectDocumentViewSet,
    DashboardSummaryView,
    AuditProjectCSVReportView # Added AuditProjectCSVReportView
)

app_name = 'audit_management'

router = DefaultRouter()
router.register(r'projects', AuditProjectViewSet, basename='project')
router.register(r'tasks', AuditTaskViewSet, basename='task')
router.register(r'documents', ProjectDocumentViewSet, basename='document') # Added ProjectDocumentViewSet
# basename is optional but recommended if queryset is not standard or for custom actions

urlpatterns = [
    path('hello/', HelloView.as_view(), name='hello'),
    path('dashboard/summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('reports/projects/csv/', AuditProjectCSVReportView.as_view(), name='report-projects-csv'), # Added
    path('', include(router.urls)), # Include router URLs for the ViewSet
]
