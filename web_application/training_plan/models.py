

from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.utils import timezone


class FitnessClub(models.Model):
    club_id = models.AutoField(primary_key=True)
    tittle = models.CharField(max_length=255, unique=True, verbose_name='Название клуба')
    post_index = models.CharField(max_length=10, blank=True, null=True, verbose_name='Почтовый индекс')
    country = models.CharField(max_length=45, blank=True, null=True, verbose_name='Страна')
    city = models.CharField(max_length=45, blank=True, null=True, verbose_name='Город')
    address = models.CharField(max_length=255, blank=True, null=True, verbose_name='Адрес')
    phone_number = models.CharField(max_length=12, blank=True, null=True, verbose_name='Телефон')
    email = models.CharField(max_length=50, blank=True, null=True, verbose_name='Эл. почта',
                             help_text='Введите адрес электронной почты, вида adress@mai.ru')
    date_created = models.DateField(verbose_name='Дата открытия')
    date_terminated = models.DateField(null=True, blank=True, verbose_name='Дата закрытия')
    comment = models.TextField(verbose_name='Комментарий',
                               help_text='Введите информацию о фитнес-клубе, о зонах посещения', blank=True, null=True)

    def __str__(self):
        return f'{self.tittle} - {self.address}'

    class Meta:
        managed = True
        verbose_name = 'Фитнес-клуб'
        verbose_name_plural = 'Фитнес-клубы'
        db_table = 'fitness_club'
        ordering = ['tittle']
        constraints = [
            CheckConstraint(
                check=Q(date_terminated__gt=F('date_created')),
                name='check_date_terminated_greater_than_date_created_club',
                violation_error_message='Дата закрытия должна быть больше даты открытия'
            ),
        ]


class ClubZone(models.Model):
    zone_id = models.AutoField(primary_key=True)
    tittle = models.CharField(unique=True, max_length=50, verbose_name='Название зоны фитнес-клуба')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='Описание')
    fitness_club = models.ManyToManyField(FitnessClub, help_text='Выберите фитнес-клубы, где есть создаваемая зона',
                                          verbose_name='Фитнес-клубы')
    date_created = models.DateField(verbose_name='Дата открытия')
    date_terminated = models.DateField(null=True, blank=True, verbose_name='Дата закрытия')

    def __str__(self):
        return self.tittle

    class Meta:
        verbose_name = 'Зона фитнес-клуба'
        verbose_name_plural = 'Зоны фитнес-клуба'
        managed = True
        db_table = 'club_zones'
        ordering = ['tittle']
        constraints = [
            CheckConstraint(
                check=Q(date_terminated__gt=F('date_created')),
                name='check_date_terminated_greater_than_date_created_zone',
                violation_error_message='Дата закрытия должна быть больше даты открытия'
            ),
        ]


class ClubCard(models.Model):
    card_id = models.AutoField(primary_key=True)
    number_of_card = models.CharField(max_length=20, verbose_name='Номер карты')
    fitness_club = models.ManyToManyField(FitnessClub, verbose_name='Фитнес-клубы')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='Описание условий карты')
    date_of_registration = models.DateField(verbose_name='Дата начала действия')
    date_of_termination = models.DateField(verbose_name='Дата окончания действия')
    date_added = models.DateField(auto_now_add=True, verbose_name='Дата добавления карты в систему')

    def __str__(self):
        return f'{self.number_of_card}'

    class Meta:
        verbose_name = 'Клубная карта'
        verbose_name_plural = 'Клубные карты'
        managed = True
        db_table = 'club_cards'
        ordering = ['date_added', 'number_of_card']
        unique_together = ('number_of_card', 'date_of_registration', 'date_of_termination')
        constraints = [
            CheckConstraint(
                check=Q(date_of_termination__gt=F('date_of_registration')),
                name='check_date_terminated_greater_than_date_registered',
                violation_error_message='Дата окончания действия карты должна быть больше даты начала'
            ),
        ]


class UserAdditionalInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthdate = models.DateField(help_text='Enter the birthdate', verbose_name='Дата рождения')
    phone_number = models.CharField(max_length=12, help_text='Enter the phone number of the client',
                                    verbose_name='Номер телефона')
    club_cards = models.ManyToManyField(ClubCard, help_text='Enter the club cards of the user',
                                        verbose_name='Клубные карты')

    def __str__(self):
        return f'{self.user.username}'

    class Meta:
        verbose_name = 'Информация о клиенте'
        verbose_name_plural = 'Информация о клиенте'


class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    tittle = models.CharField(max_length=50, unique=True,
                              verbose_name='Название группы')
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name='Описание')
    club_zones = models.ManyToManyField(ClubZone, verbose_name='Зоны клуба')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        managed = True
        db_table = 'groups'
        ordering = ['tittle']

    def __str__(self):
        return f'{self.tittle}'


class TimeSlot(models.Model):
    time_slot_id = models.AutoField(primary_key=True)
    start = models.TimeField(verbose_name='Начало')
    end = models.TimeField(verbose_name='Конец')

    class Meta:
        verbose_name = 'Временной слот'
        verbose_name_plural = 'Временные слоты'
        managed = True
        db_table = 'time_slots'
        unique_together = ('start', 'end')
        ordering = ['start']
        constraints = [
            CheckConstraint(
                check=Q(end__gt=F('start')),
                name='check_end_greater_than_start',
                violation_error_message='Конец должен быть больше чем начало'
            ),
        ]

    def __str__(self):
        return f'{self.start} - {self.end}'


class DayType(models.Model):
    day_type_id = models.AutoField(primary_key=True)
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE, verbose_name='Фитнес-клуб')
    DAY_TYPE_TITTLES = [('work_day', 'будни'), ('weekend', 'выходной'), ('holiday', 'праздник'), ('special_day',
                                                                                                  'предпраздничный день')]
    day_type_tittle = models.CharField(max_length=50, choices=DAY_TYPE_TITTLES, verbose_name='Тип дня')
    time_slots = models.ManyToManyField(TimeSlot, blank=True, null=True, verbose_name='Временные слоты')

    class Meta:
        verbose_name = 'Тип дня'
        verbose_name_plural = 'Типы дней'
        managed = True
        db_table = 'day_type'
        ordering = ['day_type_tittle']
        unique_together = ('fitness_club', 'day_type_tittle')

    def __str__(self):
        return f'{self.fitness_club} - {[x[1] for x in DayType.DAY_TYPE_TITTLES if x[0] == self.day_type_tittle][0]}'


class SpecialDay(models.Model):
    special_day_id = models.AutoField(primary_key=True)
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE, verbose_name='Фитнес-клуб')
    day = models.DateField(verbose_name='День')
    type_of_day = models.ForeignKey(DayType, on_delete=models.CASCADE, verbose_name='Тип дня')

    class Meta:
        verbose_name = 'Особый день'
        verbose_name_plural = 'Особые дни'
        managed = True
        db_table = 'special_days'
        unique_together = ('fitness_club', 'day')
        ordering = ['day']

    def __str__(self):
        return f'{self.fitness_club} - {self.day}'


class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    day = models.DateField(verbose_name='День')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, verbose_name='Временной слот')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, verbose_name='Группа')
    club_zone = models.ForeignKey(ClubZone, on_delete=models.CASCADE, verbose_name='Зона клуба')
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE, verbose_name='Фитнес-клуб')
    comment = models.CharField(max_length=150, blank=True, null=True, help_text='Введите комфортное число клиентов, '
                                                                                'тренера', verbose_name='Комментарий')
    GROUP_STATUS = [('canceled', 'отменено'), ('planned', 'планируется')]
    group_status = models.CharField(max_length=8, choices=GROUP_STATUS, default='planned', verbose_name='Статус группы')

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        managed = True
        db_table = 'schedule'
        ordering = ['day', 'time_slot', 'group']
        unique_together = ('fitness_club', 'club_zone', 'time_slot', 'day')

    def __str__(self):
        start_schedule = f'{self.day} - {self.time_slot.start}'
        return f'{self.group} - {start_schedule}'


class Plan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент')
    day = models.DateField(default=timezone.now, verbose_name='День')
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, verbose_name='Временной слот')
    club_zone = models.ForeignKey(ClubZone, on_delete=models.CASCADE, verbose_name='Зона фитнес-клуба')
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE, verbose_name='Фитнес-клуб')

    class Meta:
        verbose_name = 'Планирование свободного посещения'
        verbose_name_plural = 'Планирование свободного посещения'
        managed = True
        db_table = 'plan'
        unique_together = ('client', 'club_zone', 'day', 'time_slot')
        ordering = ('client', 'day', 'time_slot')

    def __str__(self):
        start_training = f'{self.day} - {self.time_slot.start}'
        return f'{self.client} - {self.club_zone} - {start_training}'


class PlanGroup(models.Model):
    plan_group_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Клиент')
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE, verbose_name='Расписание')

    class Meta:
        verbose_name = 'Планирование посещения группового занятия'
        verbose_name_plural = 'Планирование посещения группового занятия'
        managed = True
        db_table = 'plan_groups'
        unique_together = ('client', 'schedule')
        ordering = ('client', 'schedule')

    def __str__(self):
        return f'{self.client} - {self.schedule}'
