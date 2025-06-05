from django.db import models
from django.contrib.auth.models import User

class AuditProject(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    scope = models.TextField(blank=True)
    objectives = models.TextField(blank=True)
    project_manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_projects'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at'] # Optional: default ordering
        verbose_name = "Audit Project"
        verbose_name_plural = "Audit Projects"


class AuditTask(models.Model):
    STATUS_CHOICES = [
        ('To Do', 'To Do'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('Blocked', 'Blocked'),
        ('In Review', 'In Review'),
    ]

    project = models.ForeignKey(
        AuditProject,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assignee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='To Do'
    )
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.project.name} - {self.name}"

    class Meta:
        ordering = ['project', 'created_at'] # Optional: default ordering
        verbose_name = "Audit Task"
        verbose_name_plural = "Audit Tasks"


class ProjectDocument(models.Model):
    project = models.ForeignKey(
        AuditProject,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    task = models.ForeignKey(
        AuditTask,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255, help_text="User-defined name for the document")
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='project_documents/%Y/%m/%d/', help_text="The actual uploaded file")
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Allow blank as it will be set in perform_create
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or str(self.file.name) # Display file name if name field is empty

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Project Document"
        verbose_name_plural = "Project Documents"
