"""
Создание форм для обмена данными
"""
from django import forms
import datetime
from django.forms import DateInput


class PlanDate(forms.Form):
    """
    Создание формы ввода даты
    """
    day = forms.DateField(label=('Выберите интересующую Вас дату:'), initial=datetime.date.today,
                          widget=DateInput(attrs={'type': 'date'}))
