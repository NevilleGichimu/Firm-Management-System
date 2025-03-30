from django import forms
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ValidationError
from .models import Diary, Calendar, Task, Case, Document
import os

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    """
    Form for creating new users in the legal practice management system.
    """
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Username', 
            'class': 'form-control'
        })
    )
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email',
            'class': 'form-control'
        })
    )
    role = forms.ChoiceField(
        choices=[
            ('lawyer', 'Lawyer'),
        ('secretary', 'Secretary'),
        ('attache', 'Attaché'),
        ('legal_assistant', 'Legal Assistant'),]
    ),
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Phone Number',
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password',
            'class': 'form-control'
        })
    )
    profile_picture = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control-file'
        })
    )
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone_number', 'password', ''
        'profile_picture')
        labels = {
            'role': 'Role',
            'phone_number': 'Phone Number',
            'profile_picture': 'Profile Picture'
        }
    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken.")
        return username
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already taken.")
        return email
    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        return password
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
    



class LoginForm(forms.Form):
    """
    Login form for all users in the legal practice management system.
    """
    username = forms.CharField(
        max_length=150, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Username', 
            'class': 'form-control'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Password', 
            'class': 'form-control'
        })
    )
    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        self.user_cache = authenticate(username=username, password=password)
        if self.user_cache is None:
            raise forms.ValidationError("Invalid login credentials.")
        return cleaned_data

    def get_user(self):
        return self.user_cache

class DiaryEntryForm(forms.ModelForm):
    """
    Form for creating diary entries for all roles.
    """
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Write your diary entry here...',
            'rows': 4,
            'class': 'form-control'
        }),
        max_length=1000
    )
    fields = ['date', 'title', 'content', 'related_event']
    widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'content': forms.Textarea(attrs={'rows': 4}),
        }
    class Meta:
        model = Diary
        fields = ['content']

    def clean_content(self):
        content = self.cleaned_data['content']
        if len(content) < 10:
            raise ValidationError("Diary entry must be at least 10 characters long.")
        return content

class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = Calendar
        fields = ['title', 'description','start_time', 'end_time', 'event_type', 'location', 'is_all_day']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }



class TaskForm(forms.ModelForm):
    """
    Form for creating tasks with role-based assignment restrictions.
    """
    def __init__(self, *args, **kwargs):
        assignor = kwargs.pop('assignor', None)
        super().__init__(*args, **kwargs)

        # Dynamically filter assignees based on assignor's role
        if assignor:
            if assignor.role == 'lawyer':
                # Lawyer can assign to everyone
                self.fields['assignee'].queryset = User.objects.exclude(username=assignor.username)
            elif assignor.role == 'secretary':
                # Secretary can assign to attache and legal assistant
                self.fields['assignee'].queryset = User.objects.filter(
                    role__in=['attache', 'legal_assistant']
                )
            else:
                # Other roles cannot assign tasks
                self.fields['assignee'].queryset = User.objects.none()

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Task Title',
            'class': 'form-control'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Task Description (Optional)',
            'rows': 3,
            'class': 'form-control'
        })
    )
    due_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )
    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'assignee']

class CaseForm(forms.ModelForm):
    """
    Form for creating and managing legal cases.
    """
    case_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'placeholder': 'Case Number',
            'class': 'form-control'
        })
    )
    client_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Client Name',
            'class': 'form-control'
        })
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Case Description',
            'rows': 4,
            'class': 'form-control'
        })
    )
    case_type = forms.ChoiceField(
        choices=[
            ('civil', 'Civil'),
            ('criminal', 'Criminal'),
            ('family', 'Family'),
            ('corporate', 'Corporate'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    documents = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        required=False,
        help_text="Upload documents (optional)"
    )

    class Meta:
        model = Case
        fields = ['case_number', 'client_name', 'description', 'case_type']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)  # Get request from kwargs
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        case = super().save(commit=False)
        if self.request:
            case.lawyer = self.request.user
        
        if commit:
            case.save()
            
            # Handle document uploads
            if 'documents' in self.files:
                for file in self.files.getlist('documents'):
                    Document.objects.create(
                        file=file,
                        case=case,
                        user=self.request.user,  # Now properly using request.user
                        document_type='case_document'
                    )
        return case

class DocumentUploadForm(forms.ModelForm):
    """
    Form for uploading documents with file type and size validation.
    """
    file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control-file'
        }),
        help_text="Upload PDF, DOC, or DOCX files (Max 10MB)"
    )
    document_type = forms.ChoiceField(
        choices=[
            ('case_document', 'Case Document'),
            ('client_communication', 'Client Communication'),
            ('legal_research', 'Legal Research'),
            ('correspondence', 'Correspondence'),
            ('other', 'Other')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Document Description (Optional)',
            'rows': 3,
            'class': 'form-control'
        })
    )

    class Meta:
        model = Document
        fields = ['file', 'document_type', 'description']

    def clean_file(self):
        file = self.cleaned_data['file']
        
        # File type validation
        allowed_extensions = ['.pdf', '.doc', '.docx']
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            raise ValidationError("Only PDF, DOC, and DOCX files are allowed.")
        
        # File size validation (10MB max)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError("File size must be under 10MB.")
        
        return file