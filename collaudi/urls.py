from django.urls import path

from . import views

urlpatterns = [
    path('', views.ProjectListView.as_view(), name='project-list'),
    path('calcolatore/', views.CalculatorView.as_view(), name='calculator'),
    path('progetti/nuovo/', views.ProjectCreateView.as_view(), name='project-create'),
    path('progetti/<int:pk>/', views.ProjectDetailView.as_view(), name='project-detail'),
    path('progetti/<int:pk>/modifica/', views.ProjectUpdateView.as_view(), name='project-update'),
    path('progetti/<int:pk>/elimina/', views.ProjectDeleteView.as_view(), name='project-delete'),
    path('progetti/<int:pk>/report.pdf', views.project_report_pdf, name='project-report-pdf'),
    path('progetti/<int:project_pk>/tratte/nuova/', views.FiberTestCreateView.as_view(), name='fibertest-create'),
    path('tratte/<int:pk>/modifica/', views.FiberTestUpdateView.as_view(), name='fibertest-update'),
    path('tratte/<int:pk>/elimina/', views.FiberTestDeleteView.as_view(), name='fibertest-delete'),
    path('tratte/<int:pk>/misure/', views.fibertest_measurements, name='fibertest-measurements'),
    path('fibre/<int:pk>/modifica/', views.strand_update, name='strand-update'),
]
