from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('plan/', views.plan, name='plan'),
    path('client_plan/client_plan_for_date', views.client_plan_for_date, name='client_plan_for_date'),
    path('client_plan/client_plan_delete', views.client_plan_delete, name='client_plan_delete'),
    path('client_plan/', views.client_plan, name='client_plan'),

]
