from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.utils import IntegrityError
from training_plan.models import *
from . import forms
from .models import Schedule


@login_required
def home(request):
    date_plan = forms.PlanDate()
    return render(request, 'home.html', {'date': date_plan})


@login_required
def plan(request):
    if request.method == 'POST':
        message = ''
        is_group_zone = False

        day = request.POST.get('plan_date')
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        day = day_date.strftime('%d-%m-%Y')

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
        fitness_zone_db = ClubZone.objects.filter(tittle=fitness_zone, fitness_club=fitness_club_db.club_id).first()
        if fitness_zone_db:
            is_group_zone = Schedule.objects.filter(club_zone_id=fitness_zone_db.zone_id).exists()
            if not fitness_zone_db.date_terminated:
                if fitness_zone_db.date_created > day_date:
                    message += 'Фитнес-зона в выбранную дату закрыта. '
            else:
                if fitness_zone_db.date_created > day_date or day_date >= fitness_zone_db.date_terminated:
                    message += 'Фитнес-зона в выбранную дату закрыта. '
        else:
            message += 'Фитнес-зоны в выбранном фитнес-клубе нет. '

        if message:
            return render(request, 'plan.html', {'day': day, 'message': message})

        is_special_day = SpecialDay.objects.filter(day=day_date).first()
        if is_special_day:
            time_slots_for_day = DayType.objects.filter(
                day_type_tittle=is_special_day.type_of_day.day_type_tittle).first().time_slots.values()
        else:
            if day_date.weekday() in [5, 6]:
                time_slots_for_day = DayType.objects.filter(day_type_tittle='weekend').first().time_slots.values()
            else:
                time_slots_for_day = DayType.objects.filter(day_type_tittle='work_day').first().time_slots.values()

        for time_slot in time_slots_for_day:
            time_slot['start'] = time_slot['start'].strftime('%H:%M')
            time_slot['end'] = time_slot['end'].strftime('%H:%M')
            clients_count = 0
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
                    time_slot['group_status'] = Schedule.GROUP_STATUS[schedule.group_status]
                    if schedule.comment:
                        time_slot['comment'] = schedule.comment
                    else:
                        time_slot['comment'] = ''
                    clients = PlanGroup.objects.filter(schedule=schedule).values()

            clients_count += len(clients)
            time_slot['clients_count'] = clients_count

        return render(request, 'plan.html', {'day': day, 'is_group_zone': is_group_zone,
                                             'time_slots_for_day': time_slots_for_day, 'zone': fitness_zone_db.zone_id,
                                             'fitness_club': fitness_club_db.club_id, 'comment': comment})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def plans_for_date_club_zone(request):
    if request.method == 'POST':
        message = ''
        active_card = False
        clubs = []
        zones = []

        day = request.POST.get('day')
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        user = request.user
        try:
            user_info = user.useradditionalinfo
            cards = list(user_info.club_cards.all())

            for card in cards:
                if card.date_of_registration <= day_date < card.date_of_termination:
                    active_card = True
                    card_clubs = card.fitness_club.values()
                    clubs += card_clubs
            if not active_card:
                message += 'На выбранную дату у Вас нет действующей клубной карты. '

            clubs_id = [club['club_id'] for club in clubs]
            club_zones = ClubZone.objects.all()
            for club in clubs_id:
                zones += club_zones.filter(fitness_club=club)

            clubs = [club['tittle'] for club in clubs]
            if message:
                return render(request, 'plans_for_date_club_zone.html', {'message': message})
            else:
                return render(request, 'plans_for_date_club_zone.html', {'clubs': clubs,
                                                                         'zones': set(zones), 'day': day})
        except UserAdditionalInfo.DoesNotExist:
            message = 'Обратитесь к администратору. Введенной информации недостаточно для корректной работы программы.'
            return render(request, 'plans_for_date_club_zone.html', {'message': message})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def plan_add(request):
    if request.method == 'POST':
        if request.POST.get('is_group_zone') == 'True':
            plan_group = PlanGroup()
            plan_group.client = User.objects.get(id=request.user.id)
            plan_group.schedule = Schedule.objects.get(schedule_id=request.POST.get('schedule'))
            # print(f'''{plan_group.client} {plan_group.schedule.day} {plan_group.schedule.time_slot}
            # {plan_group.schedule.club_zone} {plan_group.schedule.fitness_club}''')
            print(Plan.objects.filter(client=plan_group.client, day=plan_group.schedule.day,
                                      time_slot=plan_group.schedule.time_slot, club_zone=plan_group.schedule.club_zone,
                                      fitness_club=plan_group.schedule.fitness_club))
            try:
                # if Plan.objects.filter(client=plan_group.client, day=plan_group.schedule.day,
                #                        time_slot=plan_group.schedule.time_slot, club_zone=plan_group.schedule.club_zone,
                #                        fitness_club=plan_group.schedule.fitness_club):
                #     print("yes")
                #     raise IntegrityError()
                plan_group.save()
            except IntegrityError as e:
                return render(request, 'plan_add.html', {'message': 'Вы уже записаны на этот слот.'
                                                                    ' Пожалуйста, проверьте Ваши планируемые посещения.'})
        else:
            plan = Plan()
            plan.client = User.objects.get(id=request.user.id)
            plan.day = datetime.strptime(request.POST.get('date'), '%d-%m-%Y').date()
            plan.time_slot = TimeSlot.objects.get(time_slot_id=request.POST.get('time_slot_id'))
            plan.fitness_club = FitnessClub.objects.get(club_id=request.POST.get('fitness_club'))
            plan.club_zone = ClubZone.objects.get(zone_id=request.POST.get('zone'))
            try:
                plan.save()
            except IntegrityError as e:
                return render(request, 'plan_add.html', {'message': 'Вы уже записаны на этот слот.'
                                                                    ' Пожалуйста, проверьте Ваши планируемые посещения.'})

        return render(request, 'plan_add.html', {'message': 'Запись успешно добавлена. '})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def plan_info(request):
    if request.method == 'POST':
        is_group_zone = request.POST.get('is_group_zone')
        day = request.POST.get('date')
        day_date = datetime.strptime(day, '%d-%m-%Y').date()
        clients_data_list = []

        if is_group_zone == 'False':
            zone = request.POST.get('zone')
            fitness_club = request.POST.get('fitness_club')
            time_slot_id = request.POST.get('time_slot_id')

            clients = (Plan.objects.filter(day=day_date, time_slot=TimeSlot.objects.get(time_slot_id=time_slot_id),
                                           club_zone=ClubZone.objects.get(zone_id=zone),
                                           fitness_club=FitnessClub.objects.get(club_id=fitness_club)).values())
        else:
            schedule = request.POST.get('schedule')
            clients = PlanGroup.objects.filter(schedule=schedule).values()

        for client in clients:
            clients_data = {'name': User.objects.get(id=client['client_id']).get_full_name(),
                            'phone': UserAdditionalInfo.objects.get(user=client['client_id']).phone_number}
            clients_data_list.append(clients_data)

        if len(clients_data_list) == 0:
            return render(request, 'plan_info.html', {'day': day})
        else:
            return render(request, 'plan_info.html', {'day': day, 'clients': clients_data_list})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def client_plan(request):
    date_client_plan = forms.PlanDate()
    return render(request, 'client_plan.html', {'date': date_client_plan})


@login_required
def client_plan_for_date(request):
    if request.method == 'POST':
        day = request.POST.get('day')
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        day = day_date.strftime('%d-%m-%Y')
        client_id = request.user.id

        result = []

        def get_plan_result():
            client_plan_for_date_queryset = Plan.objects.filter(client=client_id, day=day_date).all()

            for i in client_plan_for_date_queryset:
                dict_client_plan = {'start_date_time': i.time_slot.start.strftime('%H:%M'),
                                    'end_date_time': i.time_slot.end.strftime('%H:%M'),
                                    'zone': i.club_zone, 'fitness_club': i.fitness_club, 'plan_id': i.plan_id,
                                    'is_group': 'False'}
                result.append(dict_client_plan)

        def get_plan_group_result():
            client_plan_group_query = PlanGroup.objects.filter(client=client_id)
            client_id_schedule = [x.schedule_id for x in client_plan_group_query]
            schedules = Schedule.objects.filter(day=day_date).all()
            client_in_schedule = list(filter(lambda x: x.schedule_id in client_id_schedule, schedules))

            for i in client_in_schedule:
                print(i.schedule_id)
                client_plan_dict = {'start_date_time': i.time_slot.start.strftime('%H:%M'),
                                    'end_date_time': i.time_slot.end.strftime('%H:%M'), 'zone': i.club_zone,
                                    'fitness_club': i.fitness_club, 'plan_id': i.schedule_id, 'is_group': 'True'}
                result.append(client_plan_dict)

        get_plan_result()
        get_plan_group_result()

        if len(result) > 0:
            return render(request, 'client_plan_for_date.html', {'date': day, 'client_plan': result})
        else:
            return render(request, 'client_plan_for_date.html', {'date': day})

    return HttpResponseRedirect(reverse('client_plan'))


@login_required
def client_plan_delete(request):
    if request.method == 'POST':
        plan_id_req = request.POST.get('plan_ident')
        is_group = request.POST.get('is_group')
        if is_group == 'True':
            plan_group_obj = PlanGroup.objects.get(schedule_id=plan_id_req)
            plan_group_obj.delete()
        else:
            plan_obj = Plan.objects.get(plan_id=plan_id_req)
            plan_obj.delete()

        return render(request, 'client_plan_delete.html')
    else:
        return HttpResponseRedirect(reverse('client_plan'))


@login_required
def create_schedule(request):
    if request.method == 'POST':
        day = request.POST.get('date')
        time_slot_id = request.POST.get('time_slot_id')
        fitness_club = request.POST.get('fitness_club')
        zone = request.POST.get('zone')
        groups = Group.objects.all().values()
        group_status = Schedule.GROUP_STATUS.values()
        return render(request, 'create_schedule.html', {'day': day, 'time_slot_id': time_slot_id,
                                                        'fitness_club': fitness_club, 'zone': zone, 'groups': groups,
                                                        'group_status': group_status})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def delete_schedule(request):
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        schedule_obj = Schedule.objects.get(schedule_id=schedule)
        schedule_obj.delete()
        return render(request, 'delete_schedule.html')
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def revoke_schedule(request):
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        schedule_obj = Schedule.objects.get(schedule_id=schedule)
        schedule_obj.group_status = 'canceled'
        schedule_obj.save()
        return render(request, 'revoke_schedule.html')
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def update_schedule(request):
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        schedule_obj = Schedule.objects.get(schedule_id=schedule)
        groups = Group.objects.all().values()
        group_status = Schedule.GROUP_STATUS.values()
        return render(request, 'update_schedule.html', {'schedule': schedule_obj, 'group': groups,
                                                        'group_status': group_status})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def update_schedule_result(request):
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        schedule_obj = Schedule.objects.get(schedule_id=schedule)
        group = request.POST.get('group')
        group_obj = Group.objects.get(tittle=group)
        comment = request.POST.get('comment')
        schedule_obj.group = group_obj
        schedule_obj.comment = comment
        try:
            schedule_obj.save()
        except IntegrityError as e:
            return render(request, 'update_schedule_result.html', {'message': 'Такой слот'
                                                                              ' в расписании уже есть!'})
        return render(request, 'update_schedule_result.html', {'message': 'Изменения успешно '
                                                                          'сохранены.'})


@login_required
def create_schedule_result(request):
    if request.method == 'POST':
        day = request.POST.get('date')
        day_date = datetime.strptime(day, '%d-%m-%Y').date()
        time_slot_id = request.POST.get('time_slot_id')
        time_slot_obj = TimeSlot.objects.get(time_slot_id=time_slot_id)
        fitness_club_id = request.POST.get('fitness_club')
        fitness_club_obj = FitnessClub.objects.get(club_id=fitness_club_id)
        zone_id = request.POST.get('zone')
        zone_obj = ClubZone.objects.get(zone_id=zone_id)
        group = request.POST.get('groups')
        group_obj = Group.objects.get(tittle=group)
        group_status = request.POST.get('group_status')
        if group_status == 'отменено':
            group_status = 'canceled'
        else:
            group_status = 'planned'

        comment = request.POST.get('comment')

        schedule_obj = Schedule()
        schedule_obj.day = day_date
        schedule_obj.time_slot = time_slot_obj
        schedule_obj.group = group_obj
        schedule_obj.club_zone = zone_obj
        schedule_obj.fitness_club = fitness_club_obj
        schedule_obj.comment = comment
        schedule_obj.group_status = group_status
        try:
            schedule_obj.save()
        except IntegrityError as e:
            return render(request, 'create_schedule_result.html', {'message': 'Такой слот'
                                                                              ' в расписании уже есть!'})
        return render(request, 'create_schedule_result.html', {'message': 'Расписание успешно '
                                                                          'создано.'})

    return render(request, 'create_schedule_result.html')
