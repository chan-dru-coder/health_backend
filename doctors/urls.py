from django.urls import path
from .views import DoctorListView, DoctorDetailView, DoctorSlotsView, DoctorProfileMeView

urlpatterns = [
    path('', DoctorListView.as_view(), name='doctor_list'),
    path('me/', DoctorProfileMeView.as_view(), name='doctor_profile_me'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor_detail'),
    path('<int:pk>/slots/', DoctorSlotsView.as_view(), name='doctor_slots'),
]
