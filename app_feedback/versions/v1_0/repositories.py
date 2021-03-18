from app_feedback.models import Review
from backend.mixins import MasterRepository


class ReviewsRepository(MasterRepository):
    model = Review
