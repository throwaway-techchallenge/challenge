from django.urls import path
from citizens.rest import views

urlpatterns = [
    path(
        'citizens/<citizen_a_id>/<citizen_b_id>/',
        views.TwoCitizensDetailsView.as_view(),
        name='two_citizens'
    ),
    path(
        'citizens/<citizen_id>/',
        views.SingleCitizenDetailsView.as_view(),
        name='single_citizen'
    ),
    path(
        'company_employees/<company_id>/',
        views.CompanyEmployeesView.as_view(),
        name='company_employees'
    ),
]
