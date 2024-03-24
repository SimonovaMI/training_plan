from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.utils import timezone


class FitnessClub(models.Model):
    club_id = models.AutoField(primary_key=True)
    tittle = models.CharField(max_length=255, help_text='Enter the tittle of the fitness club', unique=True)
    post_index = models.CharField(max_length=10, blank=True, null=True, help_text='Enter the post code of the '
                                                                                  'fitness club')
    country = models.CharField(max_length=45, blank=True, null=True, help_text='Enter the country of the fitness club')
    city = models.CharField(max_length=45, blank=True, null=True, help_text='Enter the city of the fitness club')
    address = models.CharField(max_length=255, blank=True, null=True, help_text='Enter the address of the fitness club')
    phone_number = models.CharField(max_length=12, blank=True, null=True, help_text='Enter the phone number of the '
                                                                                    'fitness club in form like this - '
                                                                                    '+79991112233')
    email = models.CharField(max_length=50, blank=True, null=True, help_text='Enter the email of the fitness club in '
                                                                             'form like this address@mail.ru')
    date_created = models.DateField(help_text='Enter the date the fitness club was opened')
    date_terminated = models.DateField(null=True, blank=True, help_text='Enter the date the fitness club was closed', )
    comment = models.TextField(help_text='Enter information about the fitness club, zones', blank=True, null=True)

    def __str__(self):
        return f'{self.tittle} - {self.address}'

    class Meta:
        managed = True
        db_table = 'fitness_club'
        ordering = ['tittle']
        constraints = [
            CheckConstraint(
                check=Q(date_terminated__gt=F('date_created')),
                name='check_date_terminated_greater_than_date_created_club',
                violation_error_message='Date of termination must be greater than date of creation'
            ),
        ]


class ClubZone(models.Model):
    zone_id = models.AutoField(primary_key=True)
    tittle = models.CharField(unique=True, max_length=50, help_text='Enter the tittle of the fitness zone')
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Enter the description of '
                                                                                    'the fitness zone')
    fitness_club = models.ManyToManyField(FitnessClub, help_text='Choose the fitness clubs')
    date_created = models.DateField(help_text='Enter the date the zone of the fitness club '
                                              'was opened')
    date_terminated = models.DateField(null=True, blank=True, help_text='Enter the date the zone  the fitness club'
                                                                        ' was closed')

    def __str__(self):
        return self.tittle

    class Meta:
        managed = True
        db_table = 'club_zones'
        ordering = ['tittle']
        constraints = [
            CheckConstraint(
                check=Q(date_terminated__gt=F('date_created')),
                name='check_date_terminated_greater_than_date_created_zone',
                violation_error_message='Date of termination must be greater than date of creation'
            ),
        ]


class ClubCard(models.Model):
    card_id = models.AutoField(primary_key=True)
    number_of_card = models.CharField(max_length=20, help_text='Enter a card number')
    fitness_club = models.ManyToManyField(FitnessClub, help_text='Choose the fitness clubs')
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Enter the description of the card')
    date_of_registration = models.DateField(help_text='Enter the date of registration of the card')
    date_of_termination = models.DateField(help_text='Enter the date of termination of the card')
    date_added = models.DateField(auto_now_add=True, help_text='Enter the date the entry was added')

    def __str__(self):
        return f'{self.number_of_card}'

    class Meta:
        managed = True
        db_table = 'club_cards'
        ordering = ['date_added', 'number_of_card']
        unique_together = ('number_of_card', 'date_of_registration', 'date_of_termination')
        constraints = [
            CheckConstraint(
                check=Q(date_of_termination__gt=F('date_of_registration')),
                name='check_date_terminated_greater_than_date_registered',
                violation_error_message='Date of termination must be greater than date of registration'
            ),
        ]


class UserAdditionalInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    birthdate = models.DateField(help_text='Enter the birthdate')
    phone_number = models.CharField(max_length=12, help_text='Enter the phone number of the client')
    club_cards = models.ManyToManyField(ClubCard, help_text='Enter the club cards of the user')

    def __str__(self):
        return f'{self.user.username}'


class Group(models.Model):
    group_id = models.AutoField(primary_key=True)
    tittle = models.CharField(max_length=50, help_text='Enter the title of the group', unique=True)
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Enter the description of the '
                                                                                    'group')
    club_zones = models.ManyToManyField(ClubZone, help_text='Enter the club zones of the group')

    class Meta:
        managed = True
        db_table = 'groups'
        ordering = ['tittle']

    def __str__(self):
        return f'{self.tittle}'


class TimeSlot(models.Model):
    time_slot_id = models.AutoField(primary_key=True)
    start = models.TimeField()
    end = models.TimeField()

    class Meta:
        managed = True
        db_table = 'time_slots'
        unique_together = ('start', 'end')
        ordering = ['start']
        constraints = [
            CheckConstraint(
                check=Q(end__gt=F('start')),
                name='check_end_greater_than_start',
                violation_error_message='End must be greater than start'
            ),
        ]

    def __str__(self):
        return f'{self.start} - {self.end}'


class DayType(models.Model):
    day_type_id = models.AutoField(primary_key=True)
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE)
    DAY_TYPE_TITTLES = [('work_day', 'будни'), ('weekend', 'выходной'), ('holiday', 'праздник'), ('special_day',
                                                                                                  'предпраздничный день')]
    day_type_tittle = models.CharField(max_length=50, choices=DAY_TYPE_TITTLES, unique=True)
    time_slots = models.ManyToManyField(TimeSlot, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'day_type'
        ordering = ['day_type_tittle']

    def __str__(self):
        return f'{self.fitness_club} - {self.day_type_tittle}'


class SpecialDay(models.Model):
    special_day_id = models.AutoField(primary_key=True)
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE)
    day = models.DateField()
    type_of_day = models.ForeignKey(DayType, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'special_days'
        unique_together = ('fitness_club', 'day')
        ordering = ['day']

    def __str__(self):
        return f'{self.fitness_club} - {self.day}'


class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    day = models.DateField()
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, help_text='Enter the group of the schedule')
    club_zone = models.ForeignKey(ClubZone, on_delete=models.CASCADE, help_text='Enter the zone of the schedule')
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE, help_text='Enter the zone of the '
                                                                                      'schedule')
    comment = models.CharField(max_length=150, blank=True, null=True, help_text='Enter a comfortable number '
                                                                                'of visitors, trainers name')
    GROUP_STATUS = {'canceled': 'отменено', 'planned': 'планируется'}
    group_status = models.CharField(max_length=8, choices=GROUP_STATUS, default='planned')

    class Meta:
        managed = True
        db_table = 'schedule'
        ordering = ['day', 'time_slot', 'group']
        unique_together = ('group', 'time_slot', 'day')

    def __str__(self):
        start_schedule = f'{self.day} - {self.time_slot.start}'
        return f'{self.group} - {start_schedule}'


class Plan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    day = models.DateField(default=timezone.now)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    club_zone = models.ForeignKey(ClubZone, on_delete=models.CASCADE)
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'plan'
        unique_together = ('client', 'club_zone', 'day', 'time_slot')
        ordering = ('client', 'day', 'time_slot')

    def __str__(self):
        start_training = f'{self.day} - {self.time_slot.start}'
        return f'{self.client} - {self.club_zone} - {start_training}'


class PlanGroup(models.Model):
    plan_group_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'plan_groups'
        unique_together = ('client', 'schedule')
        ordering = ('client', 'schedule')

    def __str__(self):
        return f'{self.client} - {self.schedule}'
