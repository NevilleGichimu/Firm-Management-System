from django.contrib import admin
from .models import User, Diary, Calendar, Task, Case, Document

# Register the User model with custom admin options
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'role')
    list_filter = ('role', 'is_active', 'is_staff')

# Register the Diary model
@admin.register(Diary)
class DiaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'content')
    list_filter = ('created_at',)

# Register the Calendar model
@admin.register(Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'start_time', 'end_time', 'event_type')
    search_fields = ('user__username', 'title', 'description')
    list_filter = ('event_type', 'start_time')

# Register the Task model
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assignor', 'assignee', 'status', 'priority', 'due_date')
    search_fields = ('title', 'assignor__username', 'assignee__username')
    list_filter = ('status', 'priority', 'due_date')

# Register the Case model
@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'client_name', 'lawyer', 'case_type', 'status', 'created_at')
    search_fields = ('case_number', 'client_name', 'lawyer__username', 'description')
    list_filter = ('case_type', 'status', 'created_at')

# Register the Document model
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('user', 'document_type', 'uploaded_at', 'case')
    search_fields = ('user__username', 'file', 'description')
    list_filter = ('document_type', 'uploaded_at')


# Register your models here.

