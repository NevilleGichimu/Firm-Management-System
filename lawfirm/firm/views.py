from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import PermissionDenied
from datetime import datetime
from django.views.decorators.http import require_POST
from django.http import Http404, JsonResponse
from django.core.serializers import serialize
from .models import (
    User, 
    Diary, 
    Calendar, 
    Task, 
    Case, 
    Document
)
from .forms import (
    LoginForm, 
    DiaryEntryForm, 
    CalendarEventForm, 
    TaskForm, 
    CaseForm, 
    DocumentUploadForm,
    UserCreationForm
)


from .forms import LoginForm  # Import your custom LoginForm

def home(request):
    if request.user.is_authenticated:
        # Redirect logged-in users to their dashboard
        if request.user.role == 'lawyer':
            return redirect('lawyer_dashboard')
        elif request.user.role == 'secretary':
            return redirect('secretary_dashboard')
        elif request.user.role == 'attache':
            return redirect('attache_dashboard')
        elif request.user.role == 'legal_assistant':
            return redirect('legal_assistant_dashboard')

    # Handle login and signup forms
    login_form = LoginForm()

    if request.method == 'POST':
        if 'login' in request.POST:
            login_form = LoginForm(data=request.POST)
            if login_form.is_valid():
                user = login_form.get_user()  # Now this works with your custom LoginForm
                login(request, user)
                messages.success(request, "Logged in successfully!")
                return redirect('home')  # Redirect to home to handle role-based redirection
            else:
                messages.error(request, "Invalid login credentials.")


    return render(request, 'home.html', {
        'login_form': login_form,
    })

def signup(request):
    """
    Handles user signup form submission.
    """
    signup_form = UserCreationForm()

    if request.method == 'POST':
        signup_form = UserCreationForm(request.POST)
        if signup_form.is_valid():
            user = signup_form.save(commit=False)
            user.role = request.POST.get('role')
            user.save()
            login(request, user)
            messages.success(request, "Account created successfully!")
            return redirect('home')
        else:
            messages.error(request, "Error creating account. Please check the form.")
    else:
        signup_form = UserCreationForm()
    
    return render(request, 'signup.html', {'signup_form': signup_form})


@login_required
def lawyer_dashboard(request):
    """
    Dashboard for lawyer 
    """
    # Diary entries
    diary_entries = Diary.objects.filter(user=request.user)

    # Calendar events
    calendar_events = Calendar.objects.filter(user=request.user)
    
    # Task management (can assign to attache and legal assistant)
    tasks= Task.objects.filter(Q(assignor=request.user) | Q(assignee=request.user))
    print(f"Tasks for {request.user.username}: {tasks}") 
    tasks_assigned = Task.objects.filter(
        Q(assignor=request.user) |
        Q(assignee=request.user))
    

    # Case Metrics
    cases = Case.objects.filter(lawyer=request.user)
    total_cases = Case.objects.filter(lawyer=request.user).count()
    open_cases = Case.objects.filter(lawyer=request.user, status='settled').count()
    in_progress_cases = Case.objects.filter(lawyer=request.user, status='in_progress').count()
    settled_cases = Case.objects.filter(lawyer=request.user, status='settled').count()
    closed_cases = Case.objects.filter(lawyer=request.user, status='closed').count()

    # Document Upload Section
    documents = Document.objects.filter(user=request.user)
    document_form = DocumentUploadForm()

    # Analytics and Quick Stats
    total_tasks_assigned = tasks_assigned.count()
    total_tasks_assigned = tasks_assigned.count()
    pending_tasks= tasks_assigned.filter(status='pending').count()
    in_progress_tasks= tasks_assigned.filter(status='in_progress').count()
    on_hold_tasks= tasks_assigned.filter(status='on_hold').count()
    completed_tasks = tasks_assigned.filter(status='completed').count()

    #Diary and calendar Notifications
    meetings_calendar_events = Calendar.objects.filter(user=request.user, event_type='meeting')
    court_appearance_calendar_events = Calendar.objects.filter(user=request.user, event_type='court_appearance')
    deadlines_calendar_events = Calendar.objects.filter(user=request.user, event_type='deadline')
    personal_calendar_events = Calendar.objects.filter(user=request.user, event_type='personal')
    other_calendar_events = Calendar.objects.filter(user=request.user, event_type='other')

    if total_tasks_assigned > 0:
        completed_tasks_percentage = (completed_tasks / total_tasks_assigned) * 100
        in_progress_tasks_percentage = (in_progress_tasks / total_tasks_assigned) * 100
        pending_tasks_percentage = (pending_tasks / total_tasks_assigned) * 100
    else:
        completed_tasks_percentage = 0
        in_progress_tasks_percentage = 0
        pending_tasks_percentage = 0

    context = {
        # Diary Context
        'diary_entries': diary_entries,

        # Calendar Context
        'calendar_events': calendar_events,

        # Task Context
        'tasks_assigned': tasks_assigned,
        'tasks':tasks,
    
        # Document Context
        'documents': documents,
        'document_form': document_form,

        # Case Metrics
        'cases': cases,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'settled_cases': settled_cases,
        'closed_cases': closed_cases,

        # Task Analytics
        'total_tasks_assigned': total_tasks_assigned,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'on_hold_tasks': on_hold_tasks,
        
        # Calendar Notifications
        'meetings_calendar_events': meetings_calendar_events,
        'court_appearance_calendar_events': court_appearance_calendar_events,
        'deadlines_calendar_events': deadlines_calendar_events,
        'personal_calendar_events': personal_calendar_events,
        'other_calendar_events': other_calendar_events,

        
        # Additional secretary-specific data can be added here
        'upcoming_events': calendar_events[:5],  # Next 5 events
        'recent_documents': documents[:3],  # Last 3 uploaded documents

        'completed_tasks_percentage': completed_tasks_percentage,
        'in_progress_tasks_percentage': in_progress_tasks_percentage,
        'pending_tasks_percentage': pending_tasks_percentage,
    }
    

    return render(request, 'dashboards/lawyer/dashboard.html', context)

@login_required
def event_list_json(request):
    """
    Return a JSON response with all calendar events for the logged-in user.
    """
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'description': event.description,
        'location': event.location,
    } for event in events]
    return JsonResponse(event_list, safe=False)

@login_required
def calendar_view(request):
    # Get events for FullCalendar
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'extendedProps': {
            'description': event.description,
            'type': event.event_type,
            'location': event.location,
        }
    } for event in events]
    
    # Get date from request or use today
    selected_date = request.GET.get('date', datetime.today().date())
    
    # Get diary entries for selected date
    diary_entries = Diary.objects.filter(
        user=request.user,
        date=selected_date
    )
    
    # Forms
    event_form = CalendarEventForm()
    diary_form = DiaryEntryForm(initial={'date': selected_date})
    
    context = {
        'events_json': JsonResponse(event_list, safe=False).content.decode('utf-8'),
        'selected_date': selected_date,
        'diary_entries': diary_entries,
        'event_form': event_form,
        'diary_form': diary_form,
    }
    return render(request, 'lawyer/calendar.html', context)

def get_event_color(event_type):
    colors = {
        'meeting': '#3788d8',
        'court': '#d83737',
        'deadline': '#ffc107',
        'reminder': '#6f42c1',
        'other': '#6c757d'
    }
    return colors.get(event_type, '#6c757d')

@login_required
@require_POST
def add_event(request):
    form = CalendarEventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.user = request.user
        event.save()
        return JsonResponse({'success': True, 'event_id': event.id})
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def date_detail(request, date_str):
    try:
        # Parse the date string (expected format: YYYY-MM-DD)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get events and diary entries for the selected date
        events = Calendar.objects.filter(user=request.user, start_time__date=date_obj)
        diary_entries = Diary.objects.filter(user=request.user, date=date_obj)

        # Initialize forms
        diary_form = DiaryEntryForm(initial={'date': date_obj})
        event_form = CalendarEventForm()

        if request.method == 'POST':
            # Process both forms
            diary_form = DiaryEntryForm(request.POST)
            event_form = CalendarEventForm(request.POST)

            diary_valid = diary_form.is_valid()
            event_valid = event_form.is_valid()

            if diary_valid:
                diary_entry = diary_form.save(commit=False)
                diary_entry.user = request.user
                diary_entry.date = date_obj  # Ensure the entry is saved with the correct date
                diary_entry.save()

            if event_valid:
                event = event_form.save(commit=False)
                event.user = request.user
                event.save()

            if diary_valid or event_valid:
                messages.success(request, 'Diary entry and/or event added successfully!')
                return redirect('date_detail', date_str=date_str)
            else:
                messages.error(request, 'There was an error with one or both forms.')

        # Pass forms and data to the template
        context = {
            'date': date_obj,
            'date_str': date_str,  # Pass the original string to templates if needed
            'events': events,
            'diary_entries': diary_entries,
            'diary_form': diary_form,
            'event_form': event_form,
        }
        return render(request, 'lawyer/date_detail.html', context)

    except ValueError:
        raise Http404("Invalid date format. Please use YYYY-MM-DD format.")

@login_required
def create_task(request):
    """Handle task creation with specific assignment rules."""
    if request.method == 'POST':
        form = TaskForm(request.POST, assignor=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assignor = request.user
            
            # Assignment rules
            if request.user.role == 'lawyer':
                task.save()
            elif request.user.role == 'secretary':
                if task.assignee.role in ['attache', 'legal_assistant']:
                    task.save()
                else:
                    messages.error(request, 'You cannot assign tasks to this role.')
                    return redirect('create_task')
            elif request.user.role == 'legal_assistant':
                if task.assignee.role in ['attache', 'secretary']:
                    task.save()
                else:
                    messages.error(request, 'You are not authorized to assign tasks to this role.')
                    return redirect('create_task')
            elif request.user.role == 'attache':
                messages.error(request, 'You are not authorized to assign tasks.')
                return redirect('create_task')
            
            messages.success(request, 'Task created successfully.')
            return redirect('task_list')
    else:
        form = TaskForm(assignor=request.user)

    return render(request, 'lawyer/create_task.html', {'form': form})

@login_required
def task_list(request):
    """Display all tasks relevant to the user."""
    tasks = Task.objects.filter(
        Q(assignor=request.user) | Q(assignee=request.user)
    ).select_related('assignee').order_by('-created_at')
    return render(request, 'lawyer/task_list.html', {'tasks': tasks})

@login_required
def update_task(request, task_id):
    """Update details of a specific task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has permission to update (either assignor or assignee)
    if request.user not in [task.assignor, task.assignee]:
        messages.error(request, 'You are not authorized to update this task.')
        return redirect('task_list')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, assignor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task, assignor=request.user)
    
    return render(request, 'lawyer/update_task.html', {'form': form, 'task': task})

@login_required
def delete_task(request, task_id):
    """Delete a specific task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user is the assignor (only assignor can delete)
    if request.user != task.assignor:
        messages.error(request, 'You are not authorized to delete this task.')
        return redirect('task_list')
    
    task.delete()
    messages.success(request, 'Task deleted successfully')
    return redirect('task_list')

@login_required
def create_case(request):
    if request.user.role != 'lawyer':
        messages.error(request, 'Only lawyers can create cases.')
        return redirect('home')

    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES, request=request)  # Pass request here
        if form.is_valid():
            case = form.save()
            messages.success(request, 'Case created successfully.')
            return redirect('view_case', case_id=case.id)
    else:
        form = CaseForm(request=request)  # Pass request here
    
    return render(request, 'lawyer/create_case.html', {'form': form})

@login_required
def case_list(request):
    """
    List all cases for the current lawyer
    """
    cases = Case.objects.filter(lawyer=request.user).order_by('-created_at')
    return render(request, 'lawyer/case_list.html', {'cases': cases})

@login_required
def view_case(request, case_id):
    """
    View case details with associated documents
    """
    case = get_object_or_404(Case, id=case_id)
    
    # Check permission
    if case.lawyer != request.user:
        raise PermissionDenied
    
    documents = case.documents.all().order_by('-uploaded_at')
    return render(request, 'lawyer/view_case.html', {
        'case': case,
        'documents': documents
    })

@login_required
def update_case(request, case_id):
    case = get_object_or_404(Case, id=case_id, lawyer=request.user)
    
    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES, instance=case, request=request)  # Pass request here
        if form.is_valid():
            form.save()
            messages.success(request, 'Case updated successfully.')
            return redirect('view_case', case_id=case.id)
    else:
        form = CaseForm(instance=case, request=request)  # Pass request here
    
    return render(request, 'lawyer/update_case.html', {
        'form': form,
        'case': case
    })

@login_required
def delete_case(request, case_id):
    """
    Delete a case and its associated documents
    """
    case = get_object_or_404(Case, id=case_id)
    
    # Check permission
    if case.lawyer != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        case.delete()
        messages.success(request, 'Case deleted successfully.')
        return redirect('view_cases')
    
    return render(request, 'lawyer/case/confirm_delete.html', {'case': case})

# Similar structure to lawyer_dashboard, but with secretary-specific restrictions
@login_required
def secretary_dashboard(request):
    """
    Dashboard for secretary
    """
    # Diary entries
    diary_entries = Diary.objects.filter(user=request.user)

    # Calendar events
    calendar_events = Calendar.objects.filter(user=request.user)
    
    # Task management (can assign to attache and legal assistant)
    tasks= Task.objects.filter(Q(assignor=request.user) | Q(assignee=request.user))
    print(f"Tasks for {request.user.username}: {tasks}") 
    tasks_assigned = Task.objects.filter(
        Q(assignor=request.user) |
        Q(assignee=request.user))
    

    # Case Metrics
    cases = Case.objects.filter()
    total_cases = Case.objects.filter().count()
    open_cases = Case.objects.filter(status='settled').count()
    in_progress_cases = Case.objects.filter(status='in_progress').count()
    settled_cases = Case.objects.filter(status='settled').count()
    closed_cases = Case.objects.filter(status='closed').count()

    # Document Upload Section
    documents = Document.objects.filter(user=request.user)
    document_form = DocumentUploadForm()

    # Analytics and Quick Stats
    total_tasks_assigned = tasks_assigned.count()
    total_tasks_assigned = tasks_assigned.count()
    pending_tasks= tasks_assigned.filter(status='pending').count()
    in_progress_tasks= tasks_assigned.filter(status='in_progress').count()
    on_hold_tasks= tasks_assigned.filter(status='on_hold').count()
    completed_tasks = tasks_assigned.filter(status='completed').count()

    #Diary and calendar Notifications
    meetings_calendar_events = Calendar.objects.filter(user=request.user, event_type='meeting')
    court_appearance_calendar_events = Calendar.objects.filter(user=request.user, event_type='court_appearance')
    deadlines_calendar_events = Calendar.objects.filter(user=request.user, event_type='deadline')
    personal_calendar_events = Calendar.objects.filter(user=request.user, event_type='personal')
    other_calendar_events = Calendar.objects.filter(user=request.user, event_type='other')

    if total_tasks_assigned > 0:
        completed_tasks_percentage = (completed_tasks / total_tasks_assigned) * 100
        in_progress_tasks_percentage = (in_progress_tasks / total_tasks_assigned) * 100
        pending_tasks_percentage = (pending_tasks / total_tasks_assigned) * 100
    else:
        completed_tasks_percentage = 0
        in_progress_tasks_percentage = 0
        pending_tasks_percentage = 0

    context = {
        # Diary Context
        'diary_entries': diary_entries,

        # Calendar Context
        'calendar_events': calendar_events,

        # Task Context
        'tasks_assigned': tasks_assigned,
        'tasks':tasks,
    
        # Document Context
        'documents': documents,
        'document_form': document_form,

        # Case Metrics
        'cases': cases,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'settled_cases': settled_cases,
        'closed_cases': closed_cases,

        # Task Analytics
        'total_tasks_assigned': total_tasks_assigned,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'on_hold_tasks': on_hold_tasks,
        
        # Calendar Notifications
        'meetings_calendar_events': meetings_calendar_events,
        'court_appearance_calendar_events': court_appearance_calendar_events,
        'deadlines_calendar_events': deadlines_calendar_events,
        'personal_calendar_events': personal_calendar_events,
        'other_calendar_events': other_calendar_events,

        
        # Additional secretary-specific data can be added here
        'upcoming_events': calendar_events[:5],  # Next 5 events
        'recent_documents': documents[:3],  # Last 3 uploaded documents

        'completed_tasks_percentage': completed_tasks_percentage,
        'in_progress_tasks_percentage': in_progress_tasks_percentage,
        'pending_tasks_percentage': pending_tasks_percentage,
    }
    

    return render(request, 'dashboards/secretary/dashboard.html', context)

@login_required
def event_list_json(request):
    """
    Return a JSON response with all calendar events for the logged-in user.
    """
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'description': event.description,
        'location': event.location,
    } for event in events]
    return JsonResponse(event_list, safe=False)

@login_required
def secretary_calendar_view(request):
    # Get events for FullCalendar
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'extendedProps': {
            'description': event.description,
            'type': event.event_type,
            'location': event.location,
        }
    } for event in events]
    
    # Get date from request or use today
    selected_date = request.GET.get('date', datetime.today().date())
    
    # Get diary entries for selected date
    diary_entries = Diary.objects.filter(
        user=request.user,
        date=selected_date
    )
    
    # Forms
    event_form = CalendarEventForm()
    diary_form = DiaryEntryForm(initial={'date': selected_date})
    
    context = {
        'events_json': JsonResponse(event_list, safe=False).content.decode('utf-8'),
        'selected_date': selected_date,
        'diary_entries': diary_entries,
        'event_form': event_form,
        'diary_form': diary_form,
    }
    return render(request, 'secretary/calendar.html', context)

def get_event_color(event_type):
    colors = {
        'meeting': '#3788d8',
        'court': '#d83737',
        'deadline': '#ffc107',
        'reminder': '#6f42c1',
        'other': '#6c757d'
    }
    return colors.get(event_type, '#6c757d')

@login_required
@require_POST
def add_event(request):
    form = CalendarEventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.user = request.user
        event.save()
        return JsonResponse({'success': True, 'event_id': event.id})
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def secretary_date_detail(request, date_str):
    try:
        # Parse the date string (expected format: YYYY-MM-DD)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get events and diary entries for the selected date
        events = Calendar.objects.filter(user=request.user, start_time__date=date_obj)
        diary_entries = Diary.objects.filter(user=request.user, date=date_obj)

        # Initialize forms
        diary_form = DiaryEntryForm(initial={'date': date_obj})
        event_form = CalendarEventForm()

        if request.method == 'POST':
            # Process both forms
            diary_form = DiaryEntryForm(request.POST)
            event_form = CalendarEventForm(request.POST)

            diary_valid = diary_form.is_valid()
            event_valid = event_form.is_valid()

            if diary_valid:
                diary_entry = diary_form.save(commit=False)
                diary_entry.user = request.user
                diary_entry.date = date_obj  # Ensure the entry is saved with the correct date
                diary_entry.save()

            if event_valid:
                event = event_form.save(commit=False)
                event.user = request.user
                event.save()

            if diary_valid or event_valid:
                messages.success(request, 'Diary entry and/or event added successfully!')
                return redirect('date_detail', date_str=date_str)
            else:
                messages.error(request, 'There was an error with one or both forms.')

        # Pass forms and data to the template
        context = {
            'date': date_obj,
            'date_str': date_str,  # Pass the original string to templates if needed
            'events': events,
            'diary_entries': diary_entries,
            'diary_form': diary_form,
            'event_form': event_form,
        }
        return render(request, 'secretary/date_detail.html', context)

    except ValueError:
        raise Http404("Invalid date format. Please use YYYY-MM-DD format.")# Adjust based on user role

@login_required
def secretary_create_task(request):
    """Handle task creation with specific assignment rules."""
    if request.method == 'POST':
        form = TaskForm(request.POST, assignor=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assignor = request.user
            
            # Assignment rules
            if request.user.role == 'lawyer':
                task.save()
            elif request.user.role == 'secretary':
                if task.assignee.role in ['attache', 'legal_assistant']:
                    task.save()
                else:
                    messages.error(request, 'You cannot assign tasks to this role.')
                    return redirect('create_task')
            elif request.user.role == 'legal_assistant':
                if task.assignee.role in ['attache', 'secretary']:
                    task.save()
                else:
                    messages.error(request, 'You are not authorized to assign tasks to this role.')
                    return redirect('create_task')
            elif request.user.role == 'attache':
                messages.error(request, 'You are not authorized to assign tasks.')
                return redirect('create_task')
            
            messages.success(request, 'Task created successfully.')
            return redirect('task_list')
    else:
        form = TaskForm(assignor=request.user)

    return render(request, 'secretary/create_task.html', {'form': form})

@login_required
def secretary_task_list(request):
    """Display all tasks relevant to the secretary."""
    tasks = Task.objects.filter(
        Q(assignor=request.user) | Q(assignee=request.user)
    ).select_related('assignor', 'assignee').order_by('-created_at')

    # Separate tasks into categories for better clarity
    tasks_assigned_by_secretary = tasks.filter(assignor=request.user)
    tasks_assigned_to_secretary = tasks.filter(assignee=request.user)

    context = {
        'tasks': tasks,
        'tasks_assigned_by_secretary': tasks_assigned_by_secretary,
        'tasks_assigned_to_secretary': tasks_assigned_to_secretary,
    }
    return render(request, 'secretary/task_list.html', context)

@login_required
def secretary_update_task(request, task_id):
    """Update details of a specific task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has permission to update (either assignor or assignee)
    if request.user not in [task.assignor, task.assignee]:
        messages.error(request, 'You are not authorized to update this task.')
        return redirect('task_list')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, assignor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task, assignor=request.user)
    
    return render(request, 'secretary/update_task.html', {'form': form, 'task': task})

@login_required
def secretary_delete_task(request, task_id):
    """Delete a specific task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user is the assignor (only assignor can delete)
    if request.user != task.assignor:
        messages.error(request, 'You are not authorized to delete this task.')
        return redirect('task_list')
    
    task.delete()
    messages.success(request, 'Task deleted successfully')
    return redirect('task_list')


@login_required
def secretary_case_list(request):
    """
    List all cases for all the lawyers
    """
    cases = Case.objects.filter().order_by('-created_at')
    return render(request, 'secretary/case_list.html', {'cases': cases})

@login_required
def secretary_view_case(request, case_id):
    """
    View case details with associated documents
    """
    case = get_object_or_404(Case, id=case_id)
    documents = case.documents.all().order_by('-uploaded_at')
    return render(request, 'secretary/view_case.html', {
        'case': case,
        'documents': documents
    })

@login_required
def secretary_update_case(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES, instance=case, request=request)  # Pass request here
        if form.is_valid():
            form.save()
            messages.success(request, 'Case updated successfully.')
            return redirect('view_case', case_id=case.id)
    else:
        form = CaseForm(instance=case, request=request)  # Pass request here
    
    return render(request, 'secretary/update_case.html', {
        'form': form,
        'case': case
    })

# Legal assistant structure similar to secretary but with restrictions
@login_required
def legal_assistant_dashboard(request):
    """
    Dashboard for legal_assistant
    """
    # Diary entries
    diary_entries = Diary.objects.filter(user=request.user)

    # Calendar events
    calendar_events = Calendar.objects.filter(user=request.user)
    
    # Task management (can assign to attache and legal assistant)
    tasks= Task.objects.filter(Q(assignor=request.user) | Q(assignee=request.user))
    print(f"Tasks for {request.user.username}: {tasks}") 
    tasks_assigned = Task.objects.filter(
        Q(assignor=request.user) |
        Q(assignee=request.user))
    

    # Case Metrics
    cases = Case.objects.filter()
    total_cases = Case.objects.filter().count()
    open_cases = Case.objects.filter(status='settled').count()
    in_progress_cases = Case.objects.filter(status='in_progress').count()
    settled_cases = Case.objects.filter(status='settled').count()
    closed_cases = Case.objects.filter(status='closed').count()

    # Document Upload Section
    documents = Document.objects.filter(user=request.user)
    document_form = DocumentUploadForm()

    # Analytics and Quick Stats
    total_tasks_assigned = tasks_assigned.count()
    total_tasks_assigned = tasks_assigned.count()
    pending_tasks= tasks_assigned.filter(status='pending').count()
    in_progress_tasks= tasks_assigned.filter(status='in_progress').count()
    on_hold_tasks= tasks_assigned.filter(status='on_hold').count()
    completed_tasks = tasks_assigned.filter(status='completed').count()

    #Diary and calendar Notifications
    meetings_calendar_events = Calendar.objects.filter(user=request.user, event_type='meeting')
    court_appearance_calendar_events = Calendar.objects.filter(user=request.user, event_type='court_appearance')
    deadlines_calendar_events = Calendar.objects.filter(user=request.user, event_type='deadline')
    personal_calendar_events = Calendar.objects.filter(user=request.user, event_type='personal')
    other_calendar_events = Calendar.objects.filter(user=request.user, event_type='other')

    if total_tasks_assigned > 0:
        completed_tasks_percentage = (completed_tasks / total_tasks_assigned) * 100
        in_progress_tasks_percentage = (in_progress_tasks / total_tasks_assigned) * 100
        pending_tasks_percentage = (pending_tasks / total_tasks_assigned) * 100
    else:
        completed_tasks_percentage = 0
        in_progress_tasks_percentage = 0
        pending_tasks_percentage = 0

    context = {
        # Diary Context
        'diary_entries': diary_entries,

        # Calendar Context
        'calendar_events': calendar_events,

        # Task Context
        'tasks_assigned': tasks_assigned,
        'tasks':tasks,
    
        # Document Context
        'documents': documents,
        'document_form': document_form,

        # Case Metrics
        'cases': cases,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'settled_cases': settled_cases,
        'closed_cases': closed_cases,

        # Task Analytics
        'total_tasks_assigned': total_tasks_assigned,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'on_hold_tasks': on_hold_tasks,
        
        # Calendar Notifications
        'meetings_calendar_events': meetings_calendar_events,
        'court_appearance_calendar_events': court_appearance_calendar_events,
        'deadlines_calendar_events': deadlines_calendar_events,
        'personal_calendar_events': personal_calendar_events,
        'other_calendar_events': other_calendar_events,

        
        # Additional secretary-specific data can be added here
        'upcoming_events': calendar_events[:5],  # Next 5 events
        'recent_documents': documents[:3],  # Last 3 uploaded documents

        'completed_tasks_percentage': completed_tasks_percentage,
        'in_progress_tasks_percentage': in_progress_tasks_percentage,
        'pending_tasks_percentage': pending_tasks_percentage,
    }
    

    return render(request, 'dashboards/secretary/dashboard.html', context)

@login_required
def event_list_json(request):
    """
    Return a JSON response with all calendar events for the logged-in user.
    """
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'description': event.description,
        'location': event.location,
    } for event in events]
    return JsonResponse(event_list, safe=False)

@login_required
def legal_assistant_calendar_view(request):
    # Get events for FullCalendar
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'extendedProps': {
            'description': event.description,
            'type': event.event_type,
            'location': event.location,
        }
    } for event in events]
    
    # Get date from request or use today
    selected_date = request.GET.get('date', datetime.today().date())
    
    # Get diary entries for selected date
    diary_entries = Diary.objects.filter(
        user=request.user,
        date=selected_date
    )
    
    # Forms
    event_form = CalendarEventForm()
    diary_form = DiaryEntryForm(initial={'date': selected_date})
    
    context = {
        'events_json': JsonResponse(event_list, safe=False).content.decode('utf-8'),
        'selected_date': selected_date,
        'diary_entries': diary_entries,
        'event_form': event_form,
        'diary_form': diary_form,
    }
    return render(request, 'legal_assistant/calendar.html', context)

def get_event_color(event_type):
    colors = {
        'meeting': '#3788d8',
        'court': '#d83737',
        'deadline': '#ffc107',
        'reminder': '#6f42c1',
        'other': '#6c757d'
    }
    return colors.get(event_type, '#6c757d')

@login_required
@require_POST
def add_event(request):
    form = CalendarEventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.user = request.user
        event.save()
        return JsonResponse({'success': True, 'event_id': event.id})
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def legal_assistant_date_detail(request, date_str):
    try:
        # Parse the date string (expected format: YYYY-MM-DD)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get events and diary entries for the selected date
        events = Calendar.objects.filter(user=request.user, start_time__date=date_obj)
        diary_entries = Diary.objects.filter(user=request.user, date=date_obj)

        # Initialize forms
        diary_form = DiaryEntryForm(initial={'date': date_obj})
        event_form = CalendarEventForm()

        if request.method == 'POST':
            # Process both forms
            diary_form = DiaryEntryForm(request.POST)
            event_form = CalendarEventForm(request.POST)

            diary_valid = diary_form.is_valid()
            event_valid = event_form.is_valid()

            if diary_valid:
                diary_entry = diary_form.save(commit=False)
                diary_entry.user = request.user
                diary_entry.date = date_obj  # Ensure the entry is saved with the correct date
                diary_entry.save()

            if event_valid:
                event = event_form.save(commit=False)
                event.user = request.user
                event.save()

            if diary_valid or event_valid:
                messages.success(request, 'Diary entry and/or event added successfully!')
                return redirect('date_detail', date_str=date_str)
            else:
                messages.error(request, 'There was an error with one or both forms.')

        # Pass forms and data to the template
        context = {
            'date': date_obj,
            'date_str': date_str,  # Pass the original string to templates if needed
            'events': events,
            'diary_entries': diary_entries,
            'diary_form': diary_form,
            'event_form': event_form,
        }
        return render(request, 'legal_assistant/date_detail.html', context)

    except ValueError:
        raise Http404("Invalid date format. Please use YYYY-MM-DD format.")# Adjust based on user role

@login_required
def legal_assistant_create_task(request):
    """Handle task creation with specific assignment rules for legal assistants."""
    if request.method == 'POST':
        form = TaskForm(request.POST, assignor=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.assignor = request.user
            
            # Assignment rules for legal assistants
            if task.assignee.role in ['attache', 'secretary', 'legal_assistant']:
                task.save()
                messages.success(request, 'Task created successfully.')
                return redirect('legal_assistant_task_list')
            else:
                messages.error(request, 'You are not authorized to assign tasks to this role.')
                return redirect('legal_assistant_create_task')
    else:
        form = TaskForm(assignor=request.user)

    return render(request, 'legal_assistant/create_task.html', {'form': form})

@login_required
def legal_assistant_task_list(request):
    """Display all tasks relevant to the legal assistant."""
    tasks = Task.objects.filter(
        Q(assignor=request.user) | Q(assignee=request.user)
    ).select_related('assignor', 'assignee').order_by('-created_at')

    # Separate tasks into categories for better clarity
    tasks_assigned_by_legal_assistant = tasks.filter(assignor=request.user)
    tasks_assigned_to_legal_assistant = tasks.filter(assignee=request.user)

    context = {
        'tasks': tasks,
        'tasks_assigned_by_legal_assistant': tasks_assigned_by_legal_assistant,
        'tasks_assigned_to_legal_assistant': tasks_assigned_to_legal_assistant,
    }
    return render(request, 'legal_assistant/task_list.html', context)

@login_required
def legal_assistant_update_task(request, task_id):
    """Update details of a specific task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user has permission to update (either assignor or assignee)
    if request.user not in [task.assignor, task.assignee]:
        messages.error(request, 'You are not authorized to update this task.')
        return redirect('task_list')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, assignor=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully')
            return redirect('task_list')
    else:
        form = TaskForm(instance=task, assignor=request.user)
    
    return render(request, 'legal_assistant/update_task.html', {'form': form, 'task': task})

@login_required
def legal_assistant_delete_task(request, task_id):
    """Delete a specific task."""
    task = get_object_or_404(Task, id=task_id)
    
    # Check if user is the assignor (only assignor can delete)
    if request.user != task.assignor:
        messages.error(request, 'You are not authorized to delete this task.')
        return redirect('task_list')
    
    task.delete()
    messages.success(request, 'Task deleted successfully')
    return redirect('task_list')


@login_required
def legal_assistant_case_list(request):
    """
    List all cases for all the lawyers
    """
    cases = Case.objects.filter().order_by('-created_at')
    return render(request, 'secretary/case_list.html', {'cases': cases})

@login_required
def legal_assistant_view_case(request, case_id):
    """
    View case details with associated documents
    """
    case = get_object_or_404(Case, id=case_id)
    
    documents = case.documents.all().order_by('-uploaded_at')
    return render(request, 'legal_assistant/view_case.html', {
        'case': case,
        'documents': documents
    })

@login_required
def legal_assistant_update_case(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    
    if request.method == 'POST':
        form = CaseForm(request.POST, request.FILES, instance=case, request=request)  # Pass request here
        if form.is_valid():
            form.save()
            messages.success(request, 'Case updated successfully.')
            return redirect('view_case', case_id=case.id)
    else:
        form = CaseForm(instance=case, request=request)  # Pass request here
    
    return render(request, 'legal_assistant/update_case.html', {
        'form': form,
        'case': case
    })

#attache structure is similar to legal assistant

@login_required
def attache_dashboard(request):
    """
    Dashboard for attache
    """
    # Diary entries
    diary_entries = Diary.objects.filter(user=request.user)

    # Calendar events
    calendar_events = Calendar.objects.filter(user=request.user)
    
    # Task management (can assign to attache and legal assistant)
    tasks= Task.objects.filter(Q(assignor=request.user) | Q(assignee=request.user))
    print(f"Tasks for {request.user.username}: {tasks}") 
    tasks_assigned = Task.objects.filter(
        Q(assignor=request.user) |
        Q(assignee=request.user))
    

    # Case Metrics
    cases = Case.objects.filter()
    total_cases = Case.objects.filter().count()
    open_cases = Case.objects.filter(status='settled').count()
    in_progress_cases = Case.objects.filter(status='in_progress').count()
    settled_cases = Case.objects.filter(status='settled').count()
    closed_cases = Case.objects.filter(status='closed').count()

    # Document Upload Section
    documents = Document.objects.filter(user=request.user)
    document_form = DocumentUploadForm()

    # Analytics and Quick Stats
    total_tasks_assigned = tasks_assigned.count()
    total_tasks_assigned = tasks_assigned.count()
    pending_tasks= tasks_assigned.filter(status='pending').count()
    in_progress_tasks= tasks_assigned.filter(status='in_progress').count()
    on_hold_tasks= tasks_assigned.filter(status='on_hold').count()
    completed_tasks = tasks_assigned.filter(status='completed').count()

    #Diary and calendar Notifications
    meetings_calendar_events = Calendar.objects.filter(user=request.user, event_type='meeting')
    court_appearance_calendar_events = Calendar.objects.filter(user=request.user, event_type='court_appearance')
    deadlines_calendar_events = Calendar.objects.filter(user=request.user, event_type='deadline')
    personal_calendar_events = Calendar.objects.filter(user=request.user, event_type='personal')
    other_calendar_events = Calendar.objects.filter(user=request.user, event_type='other')

    if total_tasks_assigned > 0:
        completed_tasks_percentage = (completed_tasks / total_tasks_assigned) * 100
        in_progress_tasks_percentage = (in_progress_tasks / total_tasks_assigned) * 100
        pending_tasks_percentage = (pending_tasks / total_tasks_assigned) * 100
    else:
        completed_tasks_percentage = 0
        in_progress_tasks_percentage = 0
        pending_tasks_percentage = 0

    context = {
        # Diary Context
        'diary_entries': diary_entries,

        # Calendar Context
        'calendar_events': calendar_events,

        # Task Context
        'tasks_assigned': tasks_assigned,
        'tasks':tasks,
    
        # Document Context
        'documents': documents,
        'document_form': document_form,

        # Case Metrics
        'cases': cases,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'in_progress_cases': in_progress_cases,
        'settled_cases': settled_cases,
        'closed_cases': closed_cases,

        # Task Analytics
        'total_tasks_assigned': total_tasks_assigned,
        'completed_tasks': completed_tasks,
        'pending_tasks': pending_tasks,
        'in_progress_tasks': in_progress_tasks,
        'on_hold_tasks': on_hold_tasks,
        
        # Calendar Notifications
        'meetings_calendar_events': meetings_calendar_events,
        'court_appearance_calendar_events': court_appearance_calendar_events,
        'deadlines_calendar_events': deadlines_calendar_events,
        'personal_calendar_events': personal_calendar_events,
        'other_calendar_events': other_calendar_events,

        
        # Additional secretary-specific data can be added here
        'upcoming_events': calendar_events[:5],  # Next 5 events
        'recent_documents': documents[:3],  # Last 3 uploaded documents

        'completed_tasks_percentage': completed_tasks_percentage,
        'in_progress_tasks_percentage': in_progress_tasks_percentage,
        'pending_tasks_percentage': pending_tasks_percentage,
    }
    

    return render(request, 'dashboards/attache/dashboard.html', context)

@login_required
def event_list_json(request):
    """
    Return a JSON response with all calendar events for the logged-in user.
    """
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'description': event.description,
        'location': event.location,
    } for event in events]
    return JsonResponse(event_list, safe=False)

@login_required
def attache_calendar_view(request):
    # Get events for FullCalendar
    events = Calendar.objects.filter(user=request.user)
    event_list = [{
        'id': event.id,
        'title': event.title,
        'start': event.start_time.isoformat(),
        'end': event.end_time.isoformat(),
        'color': get_event_color(event.event_type),
        'extendedProps': {
            'description': event.description,
            'type': event.event_type,
            'location': event.location,
        }
    } for event in events]
    
    # Get date from request or use today
    selected_date = request.GET.get('date', datetime.today().date())
    
    # Get diary entries for selected date
    diary_entries = Diary.objects.filter(
        user=request.user,
        date=selected_date
    )
    
    # Forms
    event_form = CalendarEventForm()
    diary_form = DiaryEntryForm(initial={'date': selected_date})
    
    context = {
        'events_json': JsonResponse(event_list, safe=False).content.decode('utf-8'),
        'selected_date': selected_date,
        'diary_entries': diary_entries,
        'event_form': event_form,
        'diary_form': diary_form,
    }
    return render(request, 'attache/calendar.html', context)

def get_event_color(event_type):
    colors = {
        'meeting': '#3788d8',
        'court': '#d83737',
        'deadline': '#ffc107',
        'reminder': '#6f42c1',
        'other': '#6c757d'
    }
    return colors.get(event_type, '#6c757d')

@login_required
@require_POST
def add_event(request):
    form = CalendarEventForm(request.POST)
    if form.is_valid():
        event = form.save(commit=False)
        event.user = request.user
        event.save()
        return JsonResponse({'success': True, 'event_id': event.id})
    return JsonResponse({'success': False, 'errors': form.errors})

@login_required
def attache_date_detail(request, date_str):
    try:
        # Parse the date string (expected format: YYYY-MM-DD)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Get events and diary entries for the selected date
        events = Calendar.objects.filter(user=request.user, start_time__date=date_obj)
        diary_entries = Diary.objects.filter(user=request.user, date=date_obj)

        # Initialize forms
        diary_form = DiaryEntryForm(initial={'date': date_obj})
        event_form = CalendarEventForm()

        if request.method == 'POST':
            # Process both forms
            diary_form = DiaryEntryForm(request.POST)
            event_form = CalendarEventForm(request.POST)

            diary_valid = diary_form.is_valid()
            event_valid = event_form.is_valid()

            if diary_valid:
                diary_entry = diary_form.save(commit=False)
                diary_entry.user = request.user
                diary_entry.date = date_obj  # Ensure the entry is saved with the correct date
                diary_entry.save()

            if event_valid:
                event = event_form.save(commit=False)
                event.user = request.user
                event.save()

            if diary_valid or event_valid:
                messages.success(request, 'Diary entry and/or event added successfully!')
                return redirect('date_detail', date_str=date_str)
            else:
                messages.error(request, 'There was an error with one or both forms.')

        # Pass forms and data to the template
        context = {
            'date': date_obj,
            'date_str': date_str,  # Pass the original string to templates if needed
            'events': events,
            'diary_entries': diary_entries,
            'diary_form': diary_form,
            'event_form': event_form,
        }
        return render(request, 'attache/date_detail.html', context)

    except ValueError:
        raise Http404("Invalid date format. Please use YYYY-MM-DD format.")# Adjust based on user role


@login_required
def attache_task_list(request):
    """Display all tasks relevant to the attache."""
    tasks = Task.objects.filter(
        Q(assignor=request.user) | Q(assignee=request.user)
    ).select_related('assignor', 'assignee').order_by('-created_at')

    # Separate tasks into categories for better clarity
    tasks_assigned_to_attache = tasks.filter(assignee=request.user)

    context = {
        'tasks': tasks,
        'tasks_assigned_to_attache': tasks_assigned_to_attache,
    }
    return render(request, 'attache/task_list.html', context)


@login_required
def attache_case_list(request):
    """
    List all cases for all the lawyers
    """
    cases = Case.objects.filter().order_by('-created_at')
    return render(request, 'attache/case_list.html', {'cases': cases})

@login_required
def attache_view_case(request, case_id):
    """
    View case details with associated documents
    """
    case = get_object_or_404(Case, id=case_id)
    
    documents = case.documents.all().order_by('-uploaded_at')
    return render(request, 'attache/view_case.html', {
        'case': case,
        'documents': documents
    })

def user_logout(request):
    """Log out the user and redirect to the home page."""
    logout(request)
    return redirect('home')