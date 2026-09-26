from django.urls import path, include

urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('students.urls')),
    path('', include('teachers.urls')),
    path('courses/', include('courses.urls')),  # Inclusion des URLs du module courses
    # path('', include('courses.urls')),
    # path('', include('trs.urls')),
    # path('', include('assignments.urls')),
    # path('', include('exams.urls')),
    # path('', include('attendance.urls')),
    # path('', include('finance.urls')),
    # path('', include('admissions.urls')),
]
