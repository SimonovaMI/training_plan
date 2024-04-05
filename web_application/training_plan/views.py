"""
Модуль для отображения(контроллера). Запрос данных с помощью моделей, вывод их в шаблоны (html формы)
"""
from datetime import datetime
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.utils import IntegrityError
from training_plan.models import *
from . import forms


@login_required
def home(request):
    """
    Вывод стартовой страницы
    :param request: параметры запроса
    :return: шаблон home.html, с переданной туда формой выбора даты
    """
    date_plan = forms.PlanDate()
    return render(request, 'home.html', {'date': date_plan})


@login_required
def plans_for_date_club_zone(request):
    """
    Вывод формы выбора фитнес-клуба и его зоны, для конкретного клиента, доступные определяются его клубной картой
    :param request: параметры запроса (выбранный день, пользователь)
    :return: шаблон plans_for_date_club_zone.html либо с сообщением об ошибке, либо с доступными фитнес-клубами и
    соответствующими им зонами клуба
    """
    if request.method == 'POST':
        message = ''
        active_card = False
        clubs = []
        zones = []

        day = request.POST.get('day')
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        user = request.user
        try:
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
                message = ('Обратитесь к администратору. Введенной информации недостаточно для корректной работы '
                           'программы.')
                return render(request, 'plans_for_date_club_zone.html', {'message': message})
        except IOError:
            return render(request, 'plans_for_date_club_zone.html', {'message': 'Что-то пошло не '
                                                                                'так! Проблема с базой данных. '
                                                                                'Обратитесь, пожалуйста, '
                                                                                'к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def plan(request):
    """
    Вывод сетки расписания для фитнес-клуба и выбранной зоны за выбранную дату, по графику работы клуба в этот день
    :param request: параметры запроса (выбранные день, фитнес-клуб, зона клуба)
    :return: шаблон plan.html с сообщением об ошибке или с сеткой расписания по графику работы для фитнес-клуба и его
    выбранной зоны, с указанием количества планирующих посещение. Реализация возможности подачи заявки, работы с
    расписанием для менеджера.
    """
    if request.method == 'POST':
        message = ''
        is_group_zone = False

        day = request.POST.get('plan_date')
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        day = day_date.strftime('%d-%m-%Y')

        fitness_club = request.POST.get('fitness_club')
        try:
            try:
                fitness_club_db = FitnessClub.objects.get(tittle=fitness_club)
            except FitnessClub.DoesNotExist:
                return render(request, 'plan.html', {'day': day, 'message': 'Фитнес-клуб был удален!'
                                                                            'Обратитесь, пожалуйста, к '
                                                                            'администратору!'})

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
                message += 'Фитнес-зоны в выбранном фитнес-клубе нет. Обратитесь, пожалуйста, к администратору!'
            if message:
                return render(request, 'plan.html', {'day': day, 'message': message})

            is_special_day = SpecialDay.objects.filter(day=day_date, fitness_club=fitness_club_db).first()
            try:
                if is_special_day and is_special_day.type_of_day.fitness_club == fitness_club_db:
                    time_slots_for_day = (DayType.objects.filter(
                        day_type_tittle=is_special_day.type_of_day.day_type_tittle,
                        fitness_club=fitness_club_db).first().
                                          time_slots.values())
                else:
                    if day_date.weekday() in [5, 6]:
                        time_slots_for_day = (
                            DayType.objects.filter(day_type_tittle='weekend', fitness_club=fitness_club_db).
                            first().time_slots.values())
                    else:
                        time_slots_for_day = (
                            DayType.objects.filter(day_type_tittle='work_day', fitness_club=fitness_club_db).
                            first().time_slots.values())

                for time_slot in time_slots_for_day:
                    time_slot['start'] = time_slot['start'].strftime('%H:%M')
                    time_slot['end'] = time_slot['end'].strftime('%H:%M')
                    clients_count = 0
                    clients = []
                    if not is_group_zone:
                        clients = (Plan.objects.filter(day=day_date, time_slot=time_slot['time_slot_id'],
                                                       club_zone=fitness_zone_db.zone_id,
                                                       fitness_club=fitness_club_db.club_id)
                                   .values())
                    else:
                        schedule = Schedule.objects.filter(day=day_date, time_slot=time_slot['time_slot_id'],
                                                           club_zone_id=fitness_zone_db.zone_id,
                                                           fitness_club_id=fitness_club_db.club_id).first()

                        if schedule:
                            time_slot['schedule'] = schedule.schedule_id
                            group = Group.objects.get(schedule=schedule)
                            time_slot['group'] = group.tittle
                            if schedule.group_status == 'canceled':
                                group_status = 'отменено'
                            else:
                                group_status = 'планируется'
                            time_slot['group_status'] = group_status
                            if schedule.comment:
                                time_slot['comment'] = schedule.comment
                            else:
                                time_slot['comment'] = ''
                            clients = PlanGroup.objects.filter(schedule=schedule).values()

                    clients_count += len(clients)
                    time_slot['clients_count'] = clients_count

                return render(request, 'plan.html', {'day': day, 'is_group_zone': is_group_zone,
                                                     'time_slots_for_day': time_slots_for_day,
                                                     'zone': fitness_zone_db.zone_id,
                                                     'fitness_club': fitness_club_db.club_id, 'comment': comment})
            except AttributeError:
                return render(request, 'plan.html', {'day': day, 'message': 'Что-то пошло не так! '
                                                                            'Обратитесь, пожалуйста, к '
                                                                            'администратору!'})
        except IOError:
            return render(request, 'plan.html', {'day': day, 'message': 'Что-то пошло не так! '
                                                                        'Обратитесь, пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def plan_add(request):
    """
    Создание заявки на посещение
    :param request: параметры запроса (пользователь, день, признак зоны групповых занятий,
    временной слот, фитнес клуб, зона, расписание)
    :return: шаблон plan_add.html с сообщением об ошибке или об успешном создании
    """
    if request.method == 'POST':
        try:
            if request.POST.get('is_group_zone') == 'True':
                plan_group = PlanGroup()
                try:
                    plan_group.client = User.objects.get(id=request.user.id)
                except User.DoesNotExist:
                    return render(request, 'plan_add.html', {'message': 'Вашу учетную запись удалили. '
                                                                        'Обратитесь, пожалуйста, к администратору!'})
                try:
                    plan_group.schedule = Schedule.objects.get(schedule_id=request.POST.get('schedule'))
                except Schedule.DoesNotExist:
                    return render(request, 'plan_add.html', {'message': 'Расписание удалили. '
                                                                        'Обновите страницу!'})
                try:
                    plan_group.save()
                except IntegrityError:
                    return render(request, 'plan_add.html', {'message': 'Вы уже записаны на этот слот.'
                                                                        ' Пожалуйста, проверьте Ваши планируемые '
                                                                        'посещения.'})
            else:
                plans = Plan()
                try:
                    plans.client = User.objects.get(id=request.user.id)
                except User.DoesNotExist:
                    return render(request, 'plan_add.html', {'message': 'Вашу учетную запись удалили. '
                                                                        'Обратитесь, пожалуйста, к администратору!'})
                plans.day = datetime.strptime(request.POST.get('date'), '%d-%m-%Y').date()
                try:
                    plans.time_slot = TimeSlot.objects.get(time_slot_id=request.POST.get('time_slot_id'))
                except TimeSlot.DoesNotExist:
                    return render(request, 'plan_add.html', {'message': 'Временной слот удалили. '
                                                                        'Обратитесь, пожалуйста, к администратору!'})
                try:
                    plans.fitness_club = FitnessClub.objects.get(club_id=request.POST.get('fitness_club'))
                except FitnessClub.DoesNotExist:
                    return render(request, 'plan_add.html', {'message': 'Фитнес-клуб удалили.'
                                                                        'Обратитесь, пожалуйста, к администратору!'})
                try:
                    plans.club_zone = ClubZone.objects.get(zone_id=request.POST.get('zone'))
                except ClubZone.DoesNotExist:
                    return render(request, 'plan_add.html', {'message': 'Зону фитнес-клуба удалили.'
                                                                        'Обратитесь, пожалуйста, к администратору!'})
                try:
                    plans.save()
                except IntegrityError:
                    return render(request, 'plan_add.html', {'message': 'Вы уже записаны на этот слот.'
                                                                        ' Пожалуйста, проверьте Ваши планируемые '
                                                                        'посещения.'})

            return render(request, 'plan_add.html', {'message': 'Запись успешно добавлена. '})
        except IOError:
            return render(request, 'plan_add.html', {'message': 'Что-то пошло не так! Проблема с '
                                                                'базой данных. Обратитесь, пожалуйста, к '
                                                                'администратору!'})

    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def plan_info(request):
    """
    Вывод для менеджера ФИО и номера телефона для всех планирующих посещение в выбранный временной слот
    :param request: параметры запроса (пользователь, день, признак зоны групповых занятий,
    временной слот, фитнес клуб, зона, расписание)
    :return: шаблон plan_info.html с сообщением об ошибке или демонстрация списка желающих посетить зал (с выводом ФИО
    и номера телефона)
    """
    if request.method == 'POST':
        is_group_zone = request.POST.get('is_group_zone')
        day = request.POST.get('date')
        day_date = datetime.strptime(day, '%d-%m-%Y').date()
        clients_data_list = []
        try:
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
            try:
                for client in clients:
                    clients_data = {'name': User.objects.get(id=client['client_id']).get_full_name(),
                                    'phone': UserAdditionalInfo.objects.get(user=client['client_id']).phone_number}
                    clients_data_list.append(clients_data)

                if len(clients_data_list) == 0:
                    return render(request, 'plan_info.html', {'day': day})
                else:
                    return render(request, 'plan_info.html', {'day': day, 'clients': clients_data_list})
            except User.DoesNotExist:
                return render(request, 'plan_info.html', {'day': day, 'message': 'Учетную '
                                                                                 'запись удалили. Обратитесь, '
                                                                                 'пожалуйста, к администратору.'})
            except UserAdditionalInfo.DoesNotExist:
                return render(request, 'plan_info.html', {'day': day, 'message': 'Учетная '
                                                                                 'запись не содержит допольнительных '
                                                                                 'данных. Обратитесь, '
                                                                                 'пожалуйста, к администратору.'})

        except IOError:
            return render(request, 'plan_info.html', {'day': day, 'message': 'Что-то пошло не так!'
                                                                             ' Проблема с базой данных. Обратитесь, '
                                                                             'пожалуйста, к администратору!'})

    else:
        return HttpResponseRedirect(reverse('home'))


def get_group_status():
    """
    Вывод значения статуса группового занятия
    :return: русско-язычное наименование статуса занятия
    """
    return [x[1] for x in Schedule.GROUP_STATUS]


@login_required
def create_schedule(request):
    """
    Вывод для менеджера шаблона для выбора параметров для создания расписания групповой программы
    :param request: параметры запроса (дата, временной слот, фитнес-клуб, зона клуба)
    :return: шаблон create_schedule.html с указанными параметрами запроса, а также с возможностью выбрать статус
    группового занятия и написать комметарий
    """
    if request.method == 'POST':
        day = request.POST.get('date')
        time_slot_id = request.POST.get('time_slot_id')
        fitness_club = request.POST.get('fitness_club')
        zone = request.POST.get('zone')
        groups = Group.objects.all().values()
        group_status = get_group_status()
        return render(request, 'create_schedule.html', {'day': day, 'time_slot_id': time_slot_id,
                                                        'fitness_club': fitness_club, 'zone': zone, 'groups': groups,
                                                        'group_status': group_status})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def create_schedule_result(request):
    """
    Создание для менеджера расписания и вывод результата этого процесса
    :param request: параметры запроса (дата, временной слот, фитнес-клуб, зона клуба, статус группового занятия,
    комментарий)
    :return: шаблон create_schedule_result.html с ошибкой создания или сообщение об успешном создании расписания
    """
    if request.method == 'POST':
        try:
            day = request.POST.get('date')
            day_date = datetime.strptime(day, '%d-%m-%Y').date()
            time_slot_id = request.POST.get('time_slot_id')
            try:
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
                except IntegrityError:
                    return render(request, 'create_schedule_result.html', {'message': 'Такой слот'
                                                                                      ' в расписании уже есть!'})
                return render(request, 'create_schedule_result.html', {'message': 'Расписание успешно '
                                                                                  'создано.'})
            except TimeSlot.DoesNotExist:
                return render(request, 'create_schedule_result.html', {'message': 'Временной слот удален!'
                                                                                  'Обратитесь, пожалуйста, к '
                                                                                  'администратору'})
            except FitnessClub.DoesNotExist:
                return render(request, 'create_schedule_result.html', {'message': 'Фитнес-клуб удален!'
                                                                                  'Обратитесь, пожалуйста, к '
                                                                                  'администратору'})
            except ClubZone.DoesNotExist:
                return render(request, 'create_schedule_result.html', {'message': 'Зона клуба удалена!'
                                                                                  'Обратитесь, пожалуйста, к '
                                                                                  'администратору'})
            except Group.DoesNotExist:
                render(request, 'create_schedule_result.html', {'message': 'Групповое занятие удалено!'
                                                                           'Обратитесь, пожалуйста, к '
                                                                           'администратору'})
        except IOError:
            render(request, 'create_schedule_result.html', {'message': 'Что-то пошло не так!'
                                                                       ' Проблема с базой данных. Обратитесь, '
                                                                       'пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def delete_schedule(request):
    """
    Удаление для менеджера расписания (если нет записавшихся!), вывод сообщения о результате удаления
    :param request: параметры запроса (идентификатор расписания)
    :return: шаблон delete_schedule.html с сообщением об ошибках или об успешном удалении
    """
    if request.method == 'POST':
        try:
            schedule = request.POST.get('schedule')
            try:
                schedule_obj = Schedule.objects.get(schedule_id=schedule)
                print(PlanGroup.objects.filter(schedule=schedule_obj))
                if len(PlanGroup.objects.filter(schedule=schedule_obj)) != 0:
                    return render(request, 'delete_schedule.html', {'message': 'В расписании есть '
                                                                               'записи. Удалять его нельзя!'})
                schedule_obj.delete()
            except Schedule.DoesNotExist:
                return render(request, 'delete_schedule.html', {'message': 'Расписание уже было удалено!'})
            return render(request, 'delete_schedule.html')
        except IOError:
            return render(request, 'delete_schedule.html', {'message': 'Что-то пошло не так!'
                                                                       ' Проблема с базой данных. Обратитесь, '
                                                                       'пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def revoke_schedule(request):
    """
    Отмена для менеджера расписания. В случае, если на этот слот ничего не планируется. Вывод рузультата отмены
    :param request: параметры запроса (идентификатор расписания)
    :return: шаблон revoke_schedule.html с сообщением об ошибке или об успешной отмене
    """
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        try:
            try:
                schedule_obj = Schedule.objects.get(schedule_id=schedule)
                schedule_obj.group_status = 'canceled'
                schedule_obj.save()
            except Schedule.DoesNotExist:
                return render(request, 'revoke_schedule.html', {'message': 'Расписание было удалено! '
                                                                           'Обновите страницу!'})
            return render(request, 'revoke_schedule.html')
        except IOError:
            return render(request, 'revoke_schedule.html', {'message': 'Что-то пошло не так!'
                                                                       ' Проблема с базой данных. Обратитесь, '
                                                                       'пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def update_schedule(request):
    """
    Изменение для менеджера расписания - комментария и занятия. Форма для изменения
    :param request: параметры запроса (идентификатор расписания)
    :return: шаблон update_schedule.html с сообщением об ошибке или с возможностью задать новую группу, комментарий
    """
    if request.method == 'POST':
        schedule = request.POST.get('schedule')
        try:
            try:
                schedule_obj = Schedule.objects.get(schedule_id=schedule)
                groups = Group.objects.all().values()
                group_status = get_group_status()
                return render(request, 'update_schedule.html', {'schedule': schedule_obj, 'group': groups,
                                                                'group_status': group_status})
            except Schedule.DoesNotExist:
                return render(request, 'update_schedule.html', {'message': 'Расписание удалили. '
                                                                           'Пожалуйста, обновите страницу!'})
        except IOError:
            return render(request, 'update_schedule.html', {'message': 'Что-то пошло не так!'
                                                                       ' Проблема с базой данных. Обратитесь, '
                                                                       'пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def update_schedule_result(request):
    """
    Изменение для менеджера расписания. Вывод сообщения о результатах изменения
    :param request: параметры запроса (расписание, группа, комментарий)
    :return: шаблон update_schedule_result.html с сообщением об ошибке или с сообщением об успешном изменении
    """
    if request.method == 'POST':
        try:
            schedule = request.POST.get('schedule')
            try:
                schedule_obj = Schedule.objects.get(schedule_id=schedule)
            except Schedule.DoesNotExist:
                return render(request, 'update_schedule_result.html', {'message': 'Расписание удалено! '
                                                                                  'Обновите страницу!'})
            group = request.POST.get('group')
            try:
                group_obj = Group.objects.get(tittle=group)
            except Group.DoesNotExist:
                return render(request, 'update_schedule_result.html', {'message': 'Групповое занятие '
                                                                                  'удалено! Обратитесь к '
                                                                                  'администратору!'})
            comment = request.POST.get('comment')
            schedule_obj.group = group_obj
            schedule_obj.comment = comment
            try:
                schedule_obj.save()
            except IntegrityError:
                return render(request, 'update_schedule_result.html', {'message': 'Такой слот'
                                                                                  ' в расписании уже есть!'})
            return render(request, 'update_schedule_result.html', {'message': 'Изменения успешно '
                                                                              'сохранены.'})
        except IOError:
            return render(request, 'update_schedule_result.html', {'message': 'Что-то пошло не так!'
                                                                              ' Проблема с базой данных. Обратитесь, '
                                                                              'пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('home'))


@login_required
def client_plan(request):
    """
    Вывод формы выбора даты для последующего отображения планируемых посещений клиента
    :param request: параметры запроса
    :return: шаблон client_plan.html с формой выбора даты
    """
    date_client_plan = forms.PlanDate()
    return render(request, 'client_plan.html', {'date': date_client_plan})


@login_required
def client_plan_for_date(request):
    """
    Вывод таблицы планируемых посещений клиента с возможностью их удаления
    :param request: параметры запроса (дата, клиент)
    :return: шаблон client_plan_for_date.html с выводом сообщения об ошибке или с таблицей планируемых посещений клиента
    """
    if request.method == 'POST':

        day = request.POST.get('day')
        day_date = datetime.strptime(day, '%Y-%m-%d').date()
        day = day_date.strftime('%d-%m-%Y')
        client_id = request.user.id
        result = []
        try:
            def get_plan_result():
                """
                Получение списка планируемых свободных посещений клиента на выбранную дату
                :return: список планируемых свободных посещений клиента на выбранную дату
                """
                client_plan_for_date_queryset = Plan.objects.filter(client=client_id, day=day_date).all()

                for i in client_plan_for_date_queryset:
                    dict_client_plan = {'start_date_time': i.time_slot.start.strftime('%H:%M'),
                                        'end_date_time': i.time_slot.end.strftime('%H:%M'),
                                        'zone': i.club_zone, 'fitness_club': i.fitness_club, 'plan_id': i.plan_id,
                                        'is_group': 'False'}
                    result.append(dict_client_plan)

            def get_plan_group_result():
                """
                Получение списка планируемых групповых занятий клиента на выбранную дату
                :return: список планируемых групповых занятий клиента на выбранную дату
                """
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
        except IOError:
            return render(request, 'client_plan_for_date.html', {'date': day, 'message': 'Что-то пошло не так!'
                                                                                         'Проблема с базой данных. '
                                                                                         'Обратитесь,'
                                                                                         'пожалуйста, к '
                                                                                         'администратору!'})

    return HttpResponseRedirect(reverse('client_plan'))


@login_required
def client_plan_delete(request):
    """
    Удаление планируемых посещений клиента. Вывод результата удаления
    :param request: параметры запроса (идентификатор заявки, признак группового занятия)
    :return: шаблон client_plan_delete.html с сообщением об ошибке или сообщение об успешном удалении
    """
    if request.method == 'POST':
        plan_id_req = request.POST.get('plan_ident')
        is_group = request.POST.get('is_group')
        try:
            if is_group == 'True':
                try:
                    plan_group_obj = PlanGroup.objects.get(schedule_id=plan_id_req)
                    plan_group_obj.delete()
                except PlanGroup.DoesNotExist:
                    return render(request, 'client_plan_delete.html', {'message': 'Заявка уже удалена. '
                                                                                  'Обновите страницу!'})
            else:
                try:
                    plan_obj = Plan.objects.get(plan_id=plan_id_req)
                    plan_obj.delete()
                except Plan.DoesNotExist:
                    return render(request, 'client_plan_delete.html', {'message': 'Заявка уже удалена. '
                                                                                  'Обновите страницу!'})

            return render(request, 'client_plan_delete.html')
        except IOError:
            return render(request, 'client_plan_delete.html', {'message': 'Что-то пошло не так!'
                                                                          ' Проблема с базой данных. Обратитесь, '
                                                                          'пожалуйста, к администратору!'})
    else:
        return HttpResponseRedirect(reverse('client_plan'))
