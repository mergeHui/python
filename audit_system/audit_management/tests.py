from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import AuditProject, AuditTask, ProjectDocument # Updated imports
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone # For dashboard tests
import datetime # For dashboard tests
import csv # For report tests
import io # For report tests
import os # For file operations
from django.conf import settings # For media root settings


class AuthTests(APITestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'testpassword123'
        self.user = User.objects.create_user(username=self.username, password=self.password, email='testuser@example.com')
        self.hello_url = reverse('audit_management:hello')

    def test_create_user_in_setup(self):
        self.assertIsNotNone(self.user)
        self.assertEqual(User.objects.count(), 1)

    def test_token_obtain(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': self.username, 'password': self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_token_obtain_invalid_credentials(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': self.username, 'password': 'wrongpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        obtain_url = reverse('token_obtain_pair')
        obtain_response = self.client.post(obtain_url, {'username': self.username, 'password': self.password}, format='json')
        refresh_token = obtain_response.data['refresh']
        refresh_url = reverse('token_refresh')
        refresh_response = self.client.post(refresh_url, {'refresh': refresh_token}, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)

    def test_authenticated_endpoint_access_with_token(self):
        obtain_url = reverse('token_obtain_pair')
        obtain_response = self.client.post(obtain_url, {'username': self.username, 'password': self.password}, format='json')
        access_token = obtain_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        response = self.client.get(self.hello_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['message'].startswith(f'Hello, {self.username}'))

    def test_authenticated_endpoint_access_without_token(self):
        self.client.credentials()
        response = self.client.get(self.hello_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuditProjectAPITests(APITestCase):
    def setUp(self):
        self.username = 'projectuser'
        self.password = 'password123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        token_url = reverse('token_obtain_pair')
        token_response = self.client.post(token_url, {'username': self.username, 'password': self.password}, format='json')
        self.access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.project_list_url = reverse('audit_management:project-list')

    def test_list_projects(self):
        AuditProject.objects.create(name='Project Alpha', project_manager=self.user)
        AuditProject.objects.create(name='Project Beta')
        response = self.client.get(self.project_list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(data), 2)

    def test_create_project(self):
        project_data = {'name': 'New Test Project', 'description': 'A test description'}
        response = self.client.post(self.project_list_url, project_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(AuditProject.objects.filter(name='New Test Project').exists())
        self.assertEqual(response.data['name'], project_data['name'])

    def test_create_project_invalid_data_missing_name(self):
        invalid_data = {'description': 'Missing name project'}
        response = self.client.post(self.project_list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_project(self):
        project = AuditProject.objects.create(name='Detail Project', project_manager=self.user)
        detail_url = reverse('audit_management:project-detail', kwargs={'pk': project.pk})
        response = self.client.get(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], project.name)

    def test_update_project_patch(self):
        project = AuditProject.objects.create(name='Update Me Project', status='Pending')
        detail_url = reverse('audit_management:project-detail', kwargs={'pk': project.pk})
        update_data = {'name': 'Updated Project Name', 'status': 'In Progress'}
        response = self.client.patch(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        project.refresh_from_db()
        self.assertEqual(project.name, 'Updated Project Name')
        self.assertEqual(project.status, 'In Progress')

    def test_delete_project(self):
        project = AuditProject.objects.create(name='Delete Me Project')
        detail_url = reverse('audit_management:project-detail', kwargs={'pk': project.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AuditProject.objects.filter(pk=project.pk).exists())

    def test_list_projects_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(self.project_list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuditTaskAPITests(APITestCase):
    def setUp(self):
        self.username = 'taskuser'
        self.password = 'taskpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.project_manager_user = User.objects.create_user(username='task_pm', password='pm_password')
        self.project = AuditProject.objects.create(name='Test Project for Tasks', project_manager=self.project_manager_user)
        token_url = reverse('token_obtain_pair')
        token_response = self.client.post(token_url, {'username': self.username, 'password': self.password}, format='json')
        self.access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.task_list_url = reverse('audit_management:task-list')

    def test_list_tasks(self):
        AuditTask.objects.create(project=self.project, name='Task 1')
        AuditTask.objects.create(project=self.project, name='Task 2')
        response = self.client.get(self.task_list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data if isinstance(response.data, list) else response.data.get('results', [])
        self.assertEqual(len(data), 2)

    def test_create_task(self):
        task_data = {'project': self.project.pk, 'name': 'New API Test Task'}
        response = self.client.post(self.task_list_url, task_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(AuditTask.objects.filter(name='New API Test Task', project=self.project).exists())

    def test_create_task_invalid_data_missing_name(self):
        invalid_data = {'project': self.project.pk}
        response = self.client.post(self.task_list_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_task(self):
        task = AuditTask.objects.create(project=self.project, name='Retrieve Me Task')
        detail_url = reverse('audit_management:task-detail', kwargs={'pk': task.pk})
        response = self.client.get(detail_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], task.name)

    def test_update_task_patch(self):
        task = AuditTask.objects.create(project=self.project, name='Update Me Task', status='To Do')
        detail_url = reverse('audit_management:task-detail', kwargs={'pk': task.pk})
        update_data = {'name': 'Task Name Updated', 'status': 'In Progress'}
        response = self.client.patch(detail_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.name, 'Task Name Updated')
        self.assertEqual(task.status, 'In Progress')

    def test_delete_task(self):
        task = AuditTask.objects.create(project=self.project, name='Delete Me Task')
        detail_url = reverse('audit_management:task-detail', kwargs={'pk': task.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AuditTask.objects.filter(pk=task.pk).exists())

    def test_list_tasks_unauthenticated(self):
        self.client.credentials()
        response = self.client.get(self.task_list_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProjectDocumentAPITests(APITestCase):
    def setUp(self):
        self.username = 'docuser'
        self.password = 'docpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.project_manager_user = User.objects.create_user(username='doc_pm', password='pm_password')
        self.project = AuditProject.objects.create(name='Test Project for Documents', project_manager=self.project_manager_user)
        token_url = reverse('token_obtain_pair')
        token_response = self.client.post(token_url, {'username': self.username, 'password': self.password}, format='json')
        self.access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.document_list_url = reverse('audit_management:document-list')

    def test_create_document_upload_file(self):
        dummy_file = SimpleUploadedFile("test_upload.txt", b"file_content", content_type="text/plain")
        document_data = {'project': self.project.pk, 'name': 'Test Uploaded Doc', 'file': dummy_file}
        response = self.client.post(self.document_list_url, document_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        doc = ProjectDocument.objects.get(name='Test Uploaded Doc')
        self.assertEqual(doc.uploaded_by, self.user)
        self.assertTrue(doc.file.name.endswith('test_upload.txt'))
        # Basic check for file existence (Django's test runner handles temp media)
        self.assertTrue(os.path.exists(os.path.join(settings.MEDIA_ROOT, doc.file.name)))
        doc.file.delete(save=False) # Clean up the file

    def test_create_document_missing_file(self):
        document_data = {'project': self.project.pk, 'name': 'Doc no file'}
        response = self.client.post(self.document_list_url, document_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_document(self):
        dummy_file = SimpleUploadedFile("delete_test.txt", b"content", content_type="text/plain")
        doc = ProjectDocument.objects.create(project=self.project, name='Delete Me Doc', file=dummy_file, uploaded_by=self.user)
        file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
        self.assertTrue(os.path.exists(file_path)) # Check it exists before delete
        detail_url = reverse('audit_management:document-detail', kwargs={'pk': doc.pk})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProjectDocument.objects.filter(pk=doc.pk).exists())
        self.assertFalse(os.path.exists(file_path)) # Check it's deleted


class DashboardAPITests(APITestCase):
    def setUp(self):
        self.username = 'dashboarduser'
        self.password = 'dashpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        token_url = reverse('token_obtain_pair')
        token_response = self.client.post(token_url, {'username': self.username, 'password': self.password}, format='json')
        self.access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.dashboard_url = reverse('audit_management:dashboard-summary')

        # Sample Data
        self.proj1 = AuditProject.objects.create(name="P1", status="Pending")
        self.proj2 = AuditProject.objects.create(name="P2", status="In Progress")
        self.proj3 = AuditProject.objects.create(name="P3", status="Completed")
        AuditProject.objects.create(name="P4", status="In Progress")

        self.task1 = AuditTask.objects.create(project=self.proj1, name="T1 P1", status="To Do")
        self.task2 = AuditTask.objects.create(project=self.proj1, name="T2 P1", status="Completed")
        self.task3 = AuditTask.objects.create(project=self.proj2, name="T1 P2", status="In Progress")
        AuditTask.objects.create(project=self.proj2, name="T2 P2", status="In Progress")
        AuditTask.objects.create(project=self.proj3, name="T1 P3", status="Completed")

        # Overdue task
        yesterday = timezone.now().date() - datetime.timedelta(days=1)
        AuditTask.objects.create(project=self.proj1, name="Overdue T", status="To Do", due_date=yesterday)


    def test_dashboard_summary_statistics(self):
        response = self.client.get(self.dashboard_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        # Project Status Summary
        expected_project_summary = {s['status']: s['count'] for s in data.get('project_status_summary', [])}
        self.assertEqual(expected_project_summary.get('Pending'), 1)
        self.assertEqual(expected_project_summary.get('In Progress'), 2)
        self.assertEqual(expected_project_summary.get('Completed'), 1)

        # Task Status Summary
        expected_task_summary = {s['status']: s['count'] for s in data.get('task_status_summary', [])}
        self.assertEqual(expected_task_summary.get('To Do'), 2) # Includes overdue
        self.assertEqual(expected_task_summary.get('In Progress'), 2)
        self.assertEqual(expected_task_summary.get('Completed'), 2)

        # Overdue Tasks Count
        self.assertEqual(data.get('overdue_tasks_count'), 1)

    def test_dashboard_summary_no_data(self):
        # Clear existing data created by main setUp
        AuditTask.objects.all().delete()
        AuditProject.objects.all().delete()

        response = self.client.get(self.dashboard_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        self.assertEqual(data.get('project_status_summary'), [])
        self.assertEqual(data.get('task_status_summary'), [])
        self.assertEqual(data.get('overdue_tasks_count'), 0)


class ReportAPITests(APITestCase):
    def setUp(self):
        self.username = 'reportuser'
        self.password = 'reportpass123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.pm_user = User.objects.create_user(username='report_pm', password='pm_password')

        token_url = reverse('token_obtain_pair')
        token_response = self.client.post(token_url, {'username': self.username, 'password': self.password}, format='json')
        self.access_token = token_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.report_url = reverse('audit_management:report-projects-csv')

        # Sample Data
        self.proj_csv1 = AuditProject.objects.create(
            name="CSV Project One", status="Completed", project_manager=self.pm_user,
            start_date=datetime.date(2023,1,1), end_date=datetime.date(2023,3,31),
            description="Desc for CSV1", scope="Scope1", objectives="Obj1"
        )
        AuditProject.objects.create(name="CSV Project Two", status="Pending", description="Desc for CSV2")


    def test_audit_project_csv_report(self):
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response['Content-Disposition'], 'attachment; filename="audit_projects_report.csv"')

        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)

        self.assertEqual(len(rows), 3) # Header + 2 data rows
        expected_header = ["Project Name", "Project Manager", "Status", "Start Date", "End Date", "Description", "Scope", "Objectives"]
        self.assertEqual(rows[0], expected_header)

        # Check data for first project
        # Note: Order might not be guaranteed unless queryset in view has order_by
        # The view has .order_by('name'), so "CSV Project One" should be first if "CSV Project Two" is second.
        # Let's find the row for self.proj_csv1 by its name
        row1_data = None
        for row in rows[1:]:
            if row[0] == self.proj_csv1.name:
                row1_data = row
                break
        self.assertIsNotNone(row1_data)
        self.assertEqual(row1_data[1], self.pm_user.username) # Project Manager username
        self.assertEqual(row1_data[2], "Completed")
        self.assertEqual(row1_data[3], "2023-01-01")
        self.assertEqual(row1_data[4], "2023-03-31")
        self.assertEqual(row1_data[5], "Desc for CSV1")


    def test_audit_project_csv_report_no_data(self):
        AuditProject.objects.all().delete()
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        self.assertEqual(len(rows), 1) # Only header
        expected_header = ["Project Name", "Project Manager", "Status", "Start Date", "End Date", "Description", "Scope", "Objectives"]
        self.assertEqual(rows[0], expected_header)

    def test_csv_report_unauthenticated(self):
        self.client.credentials() # Clear authentication
        response = self.client.get(self.report_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
