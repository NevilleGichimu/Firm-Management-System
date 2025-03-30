import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
import os
from datetime import date

class User(AbstractUser):
    """
    Custom user model for the legal practice management system.
    """
    ROLE_CHOICES = (
        ('lawyer', 'Lawyer'),
        ('secretary', 'Secretary'),
        ('attache', 'Attaché'),
        ('legal_assistant', 'Legal Assistant'),
    )

    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='lawyer'
    )
    phone_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True
    )
    # Override related_name for groups and user_permissions to avoid conflicts
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",  # Custom related_name to avoid conflict
        blank=True,
        help_text="The groups this user belongs to.",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_set",  # Custom related_name to avoid conflict
        blank=True,
        help_text="Specific permissions for this user.",
        verbose_name="user permissions",
    )
    
    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

class Calendar(models.Model):
    """
    Calendar events for tracking appointments, meetings, and deadlines.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='calendar_events'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    # Optional fields for event categorization
    EVENT_TYPES = (
        ('meeting', 'Meeting'),
        ('court_appearance', 'Court Appearance'),
        ('deadline', 'Deadline'),
        ('personal', 'Personal'),
        ('other', 'Other')
    )
    event_type = models.CharField(
        max_length=20, 
        choices=EVENT_TYPES, 
        default='other'
    )
    location = models.CharField(max_length=200, blank=True, null=True)
    is_all_day = models.BooleanField(default=False) 
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time}"
    

class Diary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=date.today)
    title = models.CharField(max_length=200, default="Untitled")  # Add default value
    content = models.TextField()
    related_event = models.ForeignKey(
        Calendar, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Diary Entries'

    def __str__(self):
        return f"{self.title} - {self.date}"

class Task(models.Model):
    """
    Tasks that can be assigned between different roles in the legal practice.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold')
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    assignor = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='assigned_tasks',
        null=True
    )
    assignee = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='received_tasks',
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        default='medium'
    )
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - Assigned to {self.assignee.username}"

class Case(models.Model):
    """
    Legal cases managed by lawyers in the practice.
    """
    CASE_TYPES = (
        ('civil', 'Civil'),
        ('criminal', 'Criminal'),
        ('family', 'Family'),
        ('corporate', 'Corporate'),
        ('other', 'Other')
    )
    
    STATUS_CHOICES = (
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('settled', 'Settled'),
        ('closed', 'Closed')
    )
    
    # Unique case identifier
    case_number = models.CharField(
        max_length=50, 
        unique=True, 
        default=uuid.uuid4
    )
    
    # Case Details
    client_name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Relationships
    lawyer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        related_name='cases',
        null=True
    )
    
    # Categorization
    case_type = models.CharField(
        max_length=20, 
        choices=CASE_TYPES, 
        default='other'
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='open'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional Case Metadata
    client_contact_info = models.CharField(
        max_length=200, 
        blank=True, 
        null=True
    )
    initial_consultation_date = models.DateField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Cases'
    
    def __str__(self):
        return f"Case {self.case_number} - {self.client_name}"

class Document(models.Model):
    """
    Documents uploaded by various users in the legal practice.
    """
    DOCUMENT_TYPES = (
        ('case_document', 'Case Document'),
        ('client_communication', 'Client Communication'),
        ('legal_research', 'Legal Research'),
        ('correspondence', 'Correspondence'),
        ('task_document', 'Task Document'),
        ('other', 'Other')
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='documents'
    )
    
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        max_length=255
    )
    
    document_type = models.CharField(
        max_length=30, 
        choices=DOCUMENT_TYPES, 
        default='other'
    )
    
    description = models.TextField(
        blank=True, 
        null=True
    )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Optional linking to a specific case
    case = models.ForeignKey(
        Case, 
        on_delete=models.SET_NULL, 
        related_name='documents', 
        null=True, 
        blank=True
    )
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.document_type} - {self.file.name}"

    def filename(self):
        return os.path.basename(self.file.name)