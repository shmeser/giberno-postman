from app_market.models import Vacancy, Profession, Skill, Distributor, Shop
from backend.mixins import MasterRepository


class DistributorsRepository(MasterRepository):
    model = Distributor


class ShopsRepository(MasterRepository):
    model = Shop


class VacanciesRepository(MasterRepository):
    model = Vacancy


class ProfessionsRepository(MasterRepository):
    model = Profession

    def add_suggested_profession(self, name):
        self.model.objects.create(name=name, is_suggested=True)


class SkillsRepository(MasterRepository):
    model = Skill
