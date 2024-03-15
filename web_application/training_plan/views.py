from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from training_plan.models import FitnessClub, Plan, PlanGroup, ClubZone
from . import forms


# Create your views here.
@login_required
def home(request):
    clubs = FitnessClub.objects.all()
    return render(request, 'home.html', {'clubs': clubs})


def plan(request):
    return render(request, 'plan.html')


def client_plan(request):
    date_client_plan = forms.ClientPlan()
    # if request.method == 'POST':
    #     client_id = request.user.id
    #     client_plan_query = Plan.objects.filter(client=client_id)
    #     return render(request, 'client_plan_for_date.html', {'date': date_client_plan})
    return render(request, 'client_plan.html', {'date': date_client_plan})


def client_plan_for_date(request):
    if request.method == 'POST':
        day = request.POST.get('day')
        client_id = request.user.id
        client_plan_query = Plan.objects.filter(client=client_id)
        client_plan_for_date_list = list(filter(lambda x: str(x.start.date()) == day, client_plan_query))
        result = []
        for _ in client_plan_for_date_list:
            dict_client_plan = {'start_date_time': _.start, 'end_date_time': _.end, 'zone': _.club_zone,
                                'fitness_club': _.fitness_club, 'plan_id': _.plan_id}
            result.append(dict_client_plan)
        # day = datetime.datetime.strptime(date_value, '%b %d %Y')day.strftime('%d-%m-%Y')
        if len(result) > 0:
            return render(request, 'client_plan_for_date.html', {'date': day, 'client_plan':
                result})
        else:
            return render(request, 'client_plan_for_date.html', {'date': day})





    return HttpResponseRedirect(reverse('home'))


def client_plan_delete(request):
    plan_id_req = request.POST.get('plan_ident')
    plan_obj = Plan.objects.get(plan_id=plan_id_req)
    plan_obj.delete()
    return render(request, 'client_plan_delete.html')
