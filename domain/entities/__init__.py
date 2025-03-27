"""
Entidades - Objetos de domínio que possuem identidade e ciclo de vida.
As entidades representam os conceitos centrais do negócio.
""" 

# User
from domain.entities.user import User

# Championship
from domain.entities.championship import (
    Championship,
    ChampionshipStage,
    ChampionshipRound,
    ChampionshipMatch,
    Team
)

# Template
from domain.entities.template import Template, TemplateStage

# FutLiga
from domain.entities.futliga import (
    CustomLeague,
    CustomLeagueLevel,
    CustomLeaguePrize,
    LeagueMember,
    AwardConfig
)

# Prediction
from domain.entities.prediction import Prediction

# Location
from domain.entities.location import Continent, Country, State, City

# Payment
from domain.entities.payment import FutcoinPackage, SubscriptionPlan, Transaction, Payment, PaymentMethod, Subscription 