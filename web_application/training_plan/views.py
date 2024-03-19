from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from training_plan.models import *
from . import forms
from datetime import datetime
from django.db.utils import IntegrityError


@login_required
def home(request):
    date_plan = forms.PlanDate()
    return render(request, 'home.html', {'date': date_plan})


def plan(request):
    fitness_zone_db = []
    day = request.POST.get('plan_date')
    day_date = datetime.strptime(day, "%Y-%m-%d").date()
    user = request.user
    user_cards = user.useradditionalinfo.club_cards.values()
    message = ''
    active_card = False

    for card in user_cards:
        if card['date_of_registration'] <= day_date < card['date_of_termination']:
            active_card = True
    if not active_card:
        message += 'На выбранную дату у Вас нет действующей клубной карты. '

    fitness_club = request.POST.get('fitness_club')
    fitness_club_db = FitnessClub.objects.get(tittle=fitness_club)
    comment = fitness_club_db.comment
    if fitness_club_db.date_terminated is None:
        if fitness_club_db.date_created > day_date:
            message += 'Фитнес-клуб в выбранную дату закрыт. '
    else:
        if fitness_club_db.date_created > day_date or day_date >= fitness_club_db.date_terminated:
            message += 'Фитнес-клуб в выбранную дату закрыт. '

    fitness_zone = request.POST.get('fitness_zone')
    is_group_zone = False
    is_fitness_zone_exist = ClubZone.objects.filter(tittle=fitness_zone).filter(fitness_club=fitness_club_db.club_id)
    if len(is_fitness_zone_exist) != 0:
        fitness_zone_db = ClubZone.objects.get(tittle=fitness_zone)
        is_group_zone = Schedule.objects.filter(club_zone_id=fitness_zone_db.zone_id).exists()
        if fitness_zone_db.date_terminated is None:
            if fitness_zone_db.date_created > day_date:
                message += 'Фитнес-зона в выбранную дату закрыта. '
        else:
            if fitness_zone_db.date_created > day_date or day_date >= fitness_zone_db.date_terminated:
                message += 'Фитнес-зона в выбранную дату закрыта. '
    else:
        message += 'Фитнес-зоны в выбранном фитнес-клубе нет. '
    if len(message) != 0:
        return render(request, 'plan.html', {'day': day, 'message': message})
    is_special_day = SpecialDay.objects.filter(day=day_date)
    if len(is_special_day) != 0:
        is_special_day = SpecialDay.objects.filter(day=day_date).first()
        time_slots_for_day = DayType.objects.filter(
            day_type_tittle=is_special_day.type_of_day.day_type_tittle).first().time_slots.values()

    else:
        if day_date.weekday() in [5, 6]:
            time_slots_for_day = DayType.objects.filter(day_type_tittle='weekend').first().time_slots.values()

        else:
            time_slots_for_day = DayType.objects.filter(day_type_tittle='work_day').first().time_slots.values()
    clients_count = 0
    clients_data_list = []
    for time_slot in time_slots_for_day:
        time_slot['start'] = time_slot['start'].strftime("%H:%M")
        time_slot['end'] = time_slot['end'].strftime("%H:%M")
        clients_count = 0
        clients_data_list = []
        clients = []
        if not is_group_zone:
            clients = (Plan.objects.filter(day=day_date, time_slot=time_slot['time_slot_id'],
                                           club_zone=fitness_zone_db.zone_id, fitness_club=fitness_club_db.club_id)
                       .values())
        else:
            schedule = Schedule.objects.filter(day=day_date, time_slot=time_slot['time_slot_id'],
                                               club_zone_id=fitness_zone_db.zone_id,
                                               fitness_club_id=fitness_club_db.club_id).first()

            if schedule:
                time_slot['schedule'] = schedule.schedule_id
                group = Group.objects.get(schedule=schedule)
                time_slot['group'] = group.tittle
                time_slot['group_status'] = schedule.group_status
                time_slot['comment'] = schedule.comment
                clients = PlanGroup.objects.filter(schedule=schedule).values()

        clients_count += len(clients)
        time_slot['clients_count'] = clients_count
        for client in clients:
            clients_data = {'name': User.objects.get(id=client['client_id']).get_full_name(),
                            'phone': UserAdditionalInfo.objects.get(user=client['client_id']).phone_number}
            clients_data_list.append(clients_data)
            time_slot['clients_data'] = clients_data_list

    return render(request, 'plan.html', {'day': day, 'is_group_zone': is_group_zone,
                                         'time_slots_for_day': time_slots_for_day, 'zone': fitness_zone_db.zone_id,
                                         'fitness_club': fitness_club_db.club_id, 'comment': comment})


def client_plan(request):
    date_client_plan = forms.PlanDate()
    return render(request, 'client_plan.html', {'date': date_client_plan})


def client_plan_for_date(request):
    if request.method == 'POST':
        day = request.POST.get('day')
        client_id = request.user.id
        client_plan_query = Plan.objects.filter(client=client_id)
        client_plan_for_date_list = list(filter(lambda x: str(x.day) == day, client_plan_query))
        result = []
        for _ in client_plan_for_date_list:
            dict_client_plan = {'start_date_time': _.time_slot.start.strftime("%H:%M"),
                                'end_date_time': _.time_slot.end.strftime("%H:%M"),
                                'zone': _.club_zone, 'fitness_club': _.fitness_club, 'plan_id': _.plan_id,
                                'is_group': 'False'}
            result.append(dict_client_plan)
        client_plan_group_query = PlanGroup.objects.filter(client=client_id)
        client_id_schedule = [x.schedule_id for x in client_plan_group_query]
        schedules = Schedule.objects.all()
        schedule_for_day = list(filter(lambda x: str(x.day) == day, schedules))
        client_in_schedule = list(filter(lambda x: x.schedule_id in client_id_schedule, schedule_for_day))
        for _ in client_in_schedule:
            dict_client_plan = {'start_date_time': _.time_slot.start.strftime("%H:%M"),
                                'end_date_time': _.time_slot.end.strftime("%H:%M"), 'zone': _.club_zone_id,
                                'fitness_club': _.fitness_club_id, 'plan_id': _.schedule_id, 'is_group': 'True'}
            result.append(dict_client_plan)
        if len(result) > 0:
            return render(request, 'client_plan_for_date.html', {'date': day, 'client_plan':
                result})
        else:
            return render(request, 'client_plan_for_date.html', {'date': day})

    return HttpResponseRedirect(reverse('home'))


def client_plan_delete(request):
    plan_id_req = request.POST.get('plan_ident')
    is_group = request.POST.get('is_group')
    if is_group == 'True':
        plan_group_obj = PlanGroup.objects.get(plan_group_id=plan_id_req)
        plan_group_obj.delete()
    else:
        plan_obj = Plan.objects.get(plan_id=plan_id_req)
        plan_obj.delete()

    return render(request, 'client_plan_delete.html')


def plans_for_date_club_zone(request):
    day = request.POST.get('day')
    user = request.user
    user_info = user.useradditionalinfo
    cards = list(user_info.club_cards.all())
    clubs = []
    zones = []
    for card in cards:
        card_clubs = card.fitness_club.values()
        clubs += card_clubs
    clubs_id = [club['club_id'] for club in clubs]
    club_zones = ClubZone.objects.all()
    for club in clubs_id:
        zones += club_zones.filter(fitness_club=club)

    clubs = [club['tittle'] for club in clubs]
    return render(request, 'plans_for_date_club_zone.html', {'clubs': clubs, 'zones': set(zones), 'day': day})


def plan_add(request):
    if request.method == "POST":
        if request.POST.get('is_group_zone'):
            plan_group = PlanGroup()
            plan_group.client = User.objects.get(id=request.user.id)
            plan_group.schedule = Schedule.objects.get(schedule_id=request.POST.get('schedule'))
            try:
                plan_group.save()
            except IntegrityError as e:
                return render(request, 'plan_add.html', {'message': 'Вы уже записаны на этот слот.'
                                                                    ' Пожалуйста, проверьте Ваши планируемые посещения.'})
        else:
            plan = Plan()
            plan.client = User.objects.get(id=request.user.id)
            plan.day = request.POST.get('date')
            plan.time_slot = TimeSlot.objects.get(time_slot_id=request.POST.get('time_slot_id'))
            plan.fitness_club = FitnessClub.objects.get(club_id=request.POST.get('fitness_club'))
            plan.club_zone = ClubZone.objects.get(zone_id=request.POST.get('zone'))
            try:
                plan.save()
            except IntegrityError as e:
                return render(request, 'plan_add.html', {'message': 'Вы уже записаны на этот слот.'
                                                                    ' Пожалуйста, проверьте Ваши планируемые посещения.'})

    return render(request, 'plan_add.html', {'message': 'Запись успешно добавлена. '})


def plan_info(request):
    clients_data = request.POST.get('clients_data')
    print(clients_data)
    return render(request, 'plan_info.html')
