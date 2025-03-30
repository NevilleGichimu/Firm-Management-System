from django.urls import path
from firm import views
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from firm.views import add_event

urlpatterns = [
    # Home and Authentication
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),

    # Lawyer URLs
    path('lawyer/dashboard/', views.lawyer_dashboard, name='lawyer_dashboard'),
    path('lawyer/task/create/', views.create_task, name='create_task'),
    path('lawyer/task/list/', views.task_list, name='task_list'),
    path('lawyer/task/update/<int:task_id>/', views.update_task, name='update_task'),
    path('lawyer/task/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    path('lawyer/case/create/', views.create_case, name='create_case'),
    path('lawyer/case/list/', views.case_list, name='view_cases'),
    path('lawyer/case/update/<int:case_id>/', views.update_case, name='update_case'),
    path('lawyer/case/delete/<int:case_id>/', views.delete_case, name='delete_case'),
    path('lawyer/case/view/<int:case_id>/', views.view_case, name='view_case'),
    path('lawyer/calendar/', views.calendar_view, name='calendar'),
    path('lawyer/calendar/events/add/', add_event, name='add_event'),
    path('lawyer/calendar/<str:date_str>/', views.date_detail, name='date_detail'),
    path('lawyer/calendar/week/<int:year>/<int:week>/', views.calendar_view, name='week_view'),
    path('lawyer/calendar/month/<int:year>/<int:month>/', views.calendar_view, name='month_view'),
    path('api/events/', views.event_list_json, name='event_list_json'),

    # Secretary URLs
    path('secretary/dashboard/', views.secretary_dashboard, name='secretary_dashboard'),
    path('secretary/calendar/create/', views.secretary_calendar_view, name='secretary_calendar'),
    path('secretary/calender/<str:date_str>/', views.secretary_date_detail, name='secretary_date_detail'),
    path('secretary/calendar/events/add/', add_event, name='add_event'),
    path('secretary/calendar/week/<int:year>/<int:week>/', views.secretary_calendar_view, name='secretary_week_view'),
    path('secretary/calendar/month/<int:year>/<int:month>/', views.secretary_calendar_view, name='secretary_month_view'),
    path('secretary/task/create/', views.secretary_create_task, name='secretary_create_task'),
    path('secretary/task/list/', views.secretary_task_list, name='secretary_task_list'),
    path('secretary/task/update/<int:task_id>/', views.secretary_update_task, name='secretary_update_task'),
    path('secretary/task/delete/<int:task_id>/', views.secretary_delete_task, name='secretary_delete_task'),
    path('secretary/case/list/', views.secretary_case_list, name='secretary_view_cases'),
    path('secretary/case/update/<int:case_id>/', views.secretary_update_case, name='secretary_update_case'),
    path('secretary/case/view/<int:case_id>/', views.secretary_view_case, name='secretary_view_case'),
    path('api/events/', views.event_list_json, name='event_list_json'),

    # Legal Assistant URLs
    path('legal-assistant/dashboard/', views.legal_assistant_dashboard, name='legal_assistant_dashboard'),
    path('legal-assistant/calendar/create/', views.legal_assistant_calendar_view, name='legal_assistant_calendar'),
    path('legal_assistant/calendar/<str:date_str>/', views.legal_assistant_date_detail, name='legal_assistant_date_detail'),
    path('legal-assistant/calendar/events/add/', add_event, name='add_event'),
    path('legal-assistant/calendar/week/<int:year>/<int:week>/', views.legal_assistant_calendar_view, name='legal_assistant_week_view'),
    path('legal-assistant/calendar/month/<int:year>/<int:month>/', views.legal_assistant_calendar_view, name='legal_assistant_month_view'),
    path('legal-assistant/task/create/', views.legal_assistant_create_task, name='legal_assistant_create_task'),
    path('legal-assistant/task/list/', views.legal_assistant_task_list, name='legal_assistant_task_list'),
    path('legal-assistant/task/update/<int:task_id>/', views.legal_assistant_update_task, name='legal_assistant_update_task'),
    path('legal-assistant/task/delete/<int:task_id>/', views.legal_assistant_delete_task, name='legal_assistant_delete_task'),
    path('legal-assistant/case/list/', views.legal_assistant_case_list, name='legal_assistant_view_cases'),
    path('legal-assistant/case/update/<int:case_id>/', views.legal_assistant_update_case, name='legal_assistant_update_case'),
    path('legal-assistant/case/view/<int:case_id>/', views.legal_assistant_view_case, name='legal_assistant_view_case'),
    path('api/events/', views.event_list_json, name='event_list_json'),

    # Attache URLs
    path('attache/dashboard/', views.attache_dashboard, name='attache_dashboard'),
    path('attache/calendar/create/', views.attache_calendar_view, name='attache_calendar'),
    path('attache/calendar/<str:date_str>/', views.attache_date_detail, name='attache_date_detail'),
    path('attache/calendar/events/add/', add_event, name='add_event'),
    path('attache/calendar/week/<int:year>/<int:week>/', views.attache_calendar_view, name='attache_week_view'),
    path('attache/calendar/month/<int:year>/<int:month>/', views.attache_calendar_view, name='attache_month_view'),
    path('attache/task/list/', views.attache_task_list, name='attache_task_list'),
    path('attache/case/list/', views.attache_case_list, name='attache_view_cases'),
    path('attache/case/view/<int:case_id>/', views.attache_view_case, name='attache_view_case'),
    path('api/events/', views.event_list_json, name='event_list_json'),

   
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)