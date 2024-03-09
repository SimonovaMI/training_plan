from django.contrib.auth.models import AbstractUser, User
from django.db import models


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
    date_created = models.DateField(auto_now_add=True, help_text='Enter the date the fitness club was opened')
    date_terminated = models.DateField(null=True, blank=True, help_text='Enter the date the fitness club was closed',)

    def __str__(self):
        return f'{self.tittle} - {self.address}'

    class Meta:
        managed = True
        db_table = 'fitness_club'
        ordering = ['tittle']


class ClubZone(models.Model):
    zone_id = models.AutoField(primary_key=True)
    tittle = models.CharField(unique=True, max_length=50, help_text='Enter the tittle of the fitness zone')
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Enter the description of '
                                                                                    'the fitness zone')
    fitness_club = models.ManyToManyField(FitnessClub, help_text='Choose the fitness clubs')
    date_created = models.DateField(auto_now_add=True, help_text='Enter the date the zone of the fitness club '
                                                                 'was opened')
    date_terminated = models.DateField(null=True, blank=True, help_text='Enter the date the zone  the fitness club'
                                                                        ' was closed')

    def __str__(self):
        return self.tittle

    class Meta:
        managed = True
        db_table = 'club_zones'
        ordering = ['tittle']


class ClubCard(models.Model):
    card_id = models.AutoField(primary_key=True)
    number_of_card = models.CharField(max_length=20, help_text='Enter a card number')
    fitness_club = models.ManyToManyField(FitnessClub, help_text='Choose the fitness clubs')
    description = models.CharField(max_length=255, blank=True, null=True, help_text='Enter the description of the card')
    date_of_registration = models.DateField(help_text='Enter the date of registration of the card')
    date_of_termination = models.DateField(null=True, blank=True,
                                           help_text='Enter the date of termination of the card')
    date_added = models.DateField(auto_now_add=True, help_text='Enter the date the entry was added')

    def __str__(self):
        return f'{self.number_of_card}'

    class Meta:
        managed = True
        db_table = 'club_cards'
        ordering = ['date_added', 'number_of_card']
        unique_together = ('number_of_card', 'date_of_registration', 'date_of_termination')


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


class Schedule(models.Model):
    schedule_id = models.AutoField(primary_key=True)
    start = models.DateTimeField(help_text='Enter the start')
    end = models.DateTimeField(help_text='Enter the end')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, help_text='Enter the group of the schedule')
    zone = models.ForeignKey(ClubZone, on_delete=models.CASCADE, help_text='Enter the zone of the schedule')
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE, help_text='Enter the zone of the '
                                                                                      'schedule')
    comment = models.CharField(max_length=150, blank=True, null=True, help_text='Enter a comfortable number '
                                                                                'of visitors, trainers name')
    GROUP_STATUS = [('canceled', 'отменено'), ('planned', 'планируется')]
    group_status = models.CharField(max_length=8, choices=GROUP_STATUS, default='planned')

    class Meta:
        managed = True
        db_table = 'schedule'
        ordering = ['start', 'group']
        unique_together = ('group', 'start', 'end')

    def __str__(self):
        start_schedule = str(self.start)[:16]
        return f'{self.group} - {start_schedule}'


class Plan(models.Model):
    plan_id = models.AutoField(primary_key=True)
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    club_zone = models.ForeignKey(ClubZone, on_delete=models.CASCADE)
    fitness_club = models.ForeignKey(FitnessClub, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'plan'
        unique_together = ('client', 'club_zone', 'start', 'end')
        ordering = ('client', 'start')

    def __str__(self):
        start_training = str(self.start)[:16]
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
