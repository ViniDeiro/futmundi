"""
Mapeamento de URLs para os controllers DDD.
"""

from django.urls import path
from presentation.controllers import user_controller

# URLs para os novos controllers DDD
urlpatterns = [
    path('api/users/profile/', user_controller.get_user_profile, name='user_profile'),
    path('api/users/daily-reward/', user_controller.add_daily_reward, name='add_daily_reward'),
    path('api/users/purchase/', user_controller.process_purchase, name='process_purchase'),
] 