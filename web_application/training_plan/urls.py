from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('client_plan/client_plan_for_date', views.client_plan_for_date, name='client_plan_for_date'),
    path('client_plan/client_plan_delete', views.client_plan_delete, name='client_plan_delete'),
    path('client_plan/', views.client_plan, name='client_plan'),
    path('plans_for_date_club_zone/plan/plan_add/', views.plan_add, name='plan_add'),
    path('plans_for_date_club_zone/plan/plan_add/plan_info/', views.plan_info, name='plan_info'),
    path('plans_for_date_club_zone/plan/', views.plan, name='plan'),
    path('plans_for_date_club_zone/', views.plans_for_date_club_zone, name='plans_for_date_club_zone')

]
