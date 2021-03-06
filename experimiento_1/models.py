import json
from datetime import datetime, timedelta
from random import randint

from django.db import models as django_models
from django.forms import Textarea
from model_utils import FieldTracker
from otree import strict_templates
from otree.api import (
    models,
    BaseConstants,
    BaseSubsession,
    BaseGroup,
    BasePlayer, widgets,
)
from otree.models import subsession

author = 'Your name here'

doc = """
Your app description
"""


class Constants(BaseConstants):
    players_per_group = None
    name_in_url = 'experimiento_1'
    num_rounds = 1
    experiment_days = 15


class Subsession(BaseSubsession):
    tipo_de_juego = models.IntegerField(default=1)
    resultados_anteriores = models.StringField(blank=True)
    etapa_actual = models.IntegerField(default=1)

    def vars_for_admin_report(self):
        survey_keys = []
        survey_items = []
        for player in self.get_players():
            survey_item = {}
            survey_data = json.loads(player.survey) if player.survey else {}
            for key, value in survey_data.items():
                if type(value) == dict:
                    keys = []
                    for key2, v2 in value.items():
                        if type(v2) == dict:
                            v2 = v2.get("")
                        survey_item[key + "__" + key2] = v2
                        if key2 not in keys:
                            keys.append(key2)
                    survey_keys.append({
                        'title':  key,
                        'values': keys
                    })
                else:
                    survey_item[key] = value
                    survey_keys.append({'title': key})
            survey_items.append(survey_item)
        survey_values = []
        for s_item in survey_items:
            s_item_array = []
            for item in survey_keys:
                if 'values' in item:
                    for v in item['values']:
                        s_item_array.append(s_item.get(item['title'] + "__" + v))
                else:
                    s_item_array.append(s_item.get(item['title']))
            survey_values.append(s_item_array)
        return dict(survey_keys=json.dumps(survey_keys), survey_values=json.dumps(survey_values))


class Group(BaseGroup):

    def players_info(self):
        query = Player.objects.filter(group_id=self.id)
        user_number = query.count()
        money_decisions_group = [
            query.filter(money_decision=0).count(),
            query.filter(money_decision=1).count(),
            query.filter(money_decision=2).count()
        ]

        return [int((value / user_number) * 100) for value in money_decisions_group]


CONTRACT_TYPE = [
    (0, 'Contrato informal (CI)'),
    (1, 'Contrato formal (CF)'),
]

MONEY_DECISION_CHOICES = [
    (0, 'Retirar los $4.000 al finalizar cada sesión.'),
    (1, 'Usted podrá guardar una parte de su pago y por cada $100 que usted decida guardar'
        ' nosotros le daremos ${price_session} más. Podrá retirar en esta sesión una parte de su '
        'pago y el monto guardado solo podrá recibirlo al finalizar las tres sesiones.'),
    (2, 'Usted podrá guardar la totalidad de su pago y retirarlo al finalizar las tres sesiones. '
        'Recuerde que por cada $100 nosotros le daremos ${price_session} más.'),
]


class Player(BasePlayer):
    num_temporal = models.IntegerField(
        label="Por favor, ingrese el numero de identificación temporal que le llegó en el correo de invitación")
    accepts_data = models.BooleanField(
        label="¿Autoriza el uso de los datos recolectados para futuros estudios?",
        choices=[
            [True, "Sí"],
            [False, "No"],
        ],
        default=True)
    accepts_terms = models.BooleanField()

    money_decision = models.IntegerField(choices=MONEY_DECISION_CHOICES, blank=False,
                                         verbose_name="Como desea reclamar su dinero?",
                                         widget=widgets.RadioSelect)
    contract_type = models.IntegerField(choices=CONTRACT_TYPE)
    experiment_start_date = django_models.DateTimeField(auto_now=True)
    intermedio = models.IntegerField(default=0)
    percentage_saved = models.IntegerField(max=100, min=0, default=0, verbose_name="Porcentaje guardado")
    file_session_1 = models.LongStringField(default="", verbose_name="Ingrese el texto del documento",
                                            widget=Textarea(attrs={'rows': 40, 'cols': 40}))
    file_session_2 = models.LongStringField(default="", verbose_name="Ingrese el texto del documento",
                                            widget=Textarea(attrs={'rows': 40, 'cols': 40}))
    file_session_3 = models.LongStringField(default="", verbose_name="Ingrese el texto del documento",
                                            widget=Textarea(attrs={'rows': 40, 'cols': 40}))
    monto_session_2 = django_models.IntegerField(default=0)
    updated_at = django_models.DateTimeField(auto_now=True)
    disbursement = models.CurrencyField(null=True, doc="Valor retirado", default=0)
    survey = models.LongStringField()
    tracker = FieldTracker()

    def start(self):
        if not self.contract_type:
            self.experiment_start_date = datetime.now()
            self.contract_type = randint(0, 1)
            self.save()

    @property
    def intermedio_actual(self):
        return self.intermedio + 1

    @property
    def experiment_end_date(self):
        return self.experiment_start_date + timedelta(days=Constants.experiment_days)





