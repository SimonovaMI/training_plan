from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from training_plan.models import FitnessClub, Plan, PlanGroup
from . import forms


# Create your views here.
@login_required
def home(request):
    clubs = FitnessClub.objects.all()
    return render(request, 'home.html', {'clubs': clubs})


def plan(request):
    return render(request, 'plan.html')


def client_plan(request):
    form = forms.ClientPlan()
    if request.method == 'POST':
        client_id = request.user.id
        client_plan_query = Plan.objects.filter(client=client_id)
        return render(request, 'client_plan.html', {'date': form.day})

    return render(request, 'client_plan.html', {'date': form})
