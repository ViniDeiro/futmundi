"""
Mapeamento de URLs para os controllers DDD.
"""

from django.urls import path
from presentation.controllers import (
    user_controller,
    championship_controller,
    league_controller,
    prediction_controller,
    team_controller,
    payment_controller,
    admin_controller,
    location_controller,
    scope_controller,
    template_controller
)

# URLs para os controllers DDD
urlpatterns = [
    # User Controller
    path('api/users/profile/', user_controller.get_user_profile, name='user_profile'),
    path('api/users/daily-reward/', user_controller.add_daily_reward, name='add_daily_reward'),
    path('api/users/purchase/', user_controller.process_purchase, name='process_purchase'),
    
    # Championship Controller
    path('api/championships/', championship_controller.get_championship_list, name='championship_list'),
    path('api/championships/<int:championship_id>/', championship_controller.get_championship_detail, name='championship_detail'),
    path('api/championships/create/', championship_controller.create_championship, name='create_championship'),
    path('api/championships/<int:championship_id>/update/', championship_controller.update_championship, name='update_championship'),
    path('api/championships/<int:championship_id>/stages/', championship_controller.get_stages_by_championship, name='championship_stages'),
    path('api/stages/<int:stage_id>/rounds/', championship_controller.get_rounds_by_stage, name='stage_rounds'),
    path('api/rounds/<int:round_id>/matches/', championship_controller.get_matches_by_round, name='round_matches'),
    path('api/matches/<int:match_id>/update-result/', championship_controller.update_match_result, name='update_match_result'),
    
    # League Controller
    path('api/leagues/', league_controller.get_league_list, name='league_list'),
    path('api/leagues/<int:league_id>/', league_controller.get_league_detail, name='league_detail'),
    path('api/leagues/create/', league_controller.create_league, name='create_league'),
    path('api/leagues/join/', league_controller.join_league, name='join_league'),
    path('api/leagues/user/', league_controller.get_user_leagues, name='user_leagues'),
    path('api/leagues/<int:league_id>/leaderboard/', league_controller.get_league_leaderboard, name='league_leaderboard'),
    path('api/leagues/<int:league_id>/leave/', league_controller.leave_league, name='leave_league'),
    
    # Prediction Controller
    path('api/predictions/round/<int:round_id>/', prediction_controller.get_user_predictions, name='user_predictions'),
    path('api/predictions/create/', prediction_controller.create_prediction, name='create_prediction'),
    path('api/predictions/round/<int:round_id>/summary/', prediction_controller.get_round_predictions_summary, name='round_predictions_summary'),
    path('api/predictions/championship/<int:championship_id>/summary/', prediction_controller.get_championship_predictions_summary, name='championship_predictions_summary'),
    path('api/predictions/match/<int:match_id>/statistics/', prediction_controller.get_prediction_statistics, name='prediction_statistics'),
    path('api/predictions/match/<int:match_id>/calculate-points/', prediction_controller.calculate_prediction_points, name='calculate_prediction_points'),
    
    # Team Controller
    path('api/teams/championship/<int:championship_id>/', team_controller.get_teams_by_championship, name='championship_teams'),
    path('api/teams/<int:team_id>/', team_controller.get_team_detail, name='team_detail'),
    path('api/teams/create/', team_controller.create_team, name='create_team'),
    path('api/teams/<int:team_id>/update/', team_controller.update_team, name='update_team'),
    path('api/teams/add-to-championship/', team_controller.add_team_to_championship, name='add_team_to_championship'),
    
    # Payment Controller
    path('api/payments/methods/', payment_controller.get_payment_methods, name='payment_methods'),
    path('api/payments/methods/add/', payment_controller.add_payment_method, name='add_payment_method'),
    path('api/payments/methods/<int:payment_method_id>/remove/', payment_controller.remove_payment_method, name='remove_payment_method'),
    path('api/payments/subscription/process/', payment_controller.process_subscription_payment, name='process_subscription_payment'),
    path('api/payments/history/', payment_controller.get_payment_history, name='payment_history'),
    path('api/payments/subscription/plans/', payment_controller.get_subscription_plans, name='subscription_plans'),
    path('api/payments/subscription/user/', payment_controller.get_user_subscription, name='user_subscription'),
    path('api/payments/subscription/cancel/', payment_controller.cancel_subscription, name='cancel_subscription'),
    
    # Admin Controller
    path('api/admin/dashboard/', admin_controller.get_admin_dashboard, name='admin_dashboard'),
    path('api/admin/user-stats/', admin_controller.get_user_stats, name='admin_user_stats'),
    path('api/admin/system-settings/', admin_controller.get_system_settings, name='get_system_settings'),
    path('api/admin/system-settings/update/', admin_controller.update_system_settings, name='update_system_settings'),
    path('api/admin/notifications/send/', admin_controller.send_system_notification, name='send_system_notification'),
    path('api/admin/championships/<int:championship_id>/activity/', admin_controller.get_championship_activity, name='championship_activity'),
    path('api/admin/rounds/<int:round_id>/calculate-points/', admin_controller.calculate_round_points, name='admin_calculate_round_points'),
    
    # Location Controller
    path('api/locations/countries/', location_controller.get_countries, name='get_countries'),
    path('api/locations/countries/<str:country_code>/states/', location_controller.get_states_by_country, name='get_states_by_country'),
    path('api/locations/countries/<str:country_code>/states/<str:state_code>/cities/', location_controller.get_cities_by_state, name='get_cities_by_state'),
    path('api/locations/update-user-location/', location_controller.update_user_location, name='update_user_location'),
    path('api/locations/search-cities/', location_controller.search_cities, name='search_cities'),
    
    # Scope Controller
    path('api/scopes/', scope_controller.get_all_scopes, name='get_all_scopes'),
    path('api/roles/', scope_controller.get_all_roles, name='get_all_roles'),
    path('api/roles/create/', scope_controller.create_role, name='create_role'),
    path('api/roles/<int:role_id>/update/', scope_controller.update_role, name='update_role'),
    path('api/roles/assign/', scope_controller.assign_role_to_user, name='assign_role_to_user'),
    path('api/roles/remove/', scope_controller.remove_role_from_user, name='remove_role_from_user'),
    path('api/users/<int:user_id>/roles/', scope_controller.get_user_roles, name='get_user_roles'),
    path('api/permissions/check/', scope_controller.check_user_permission, name='check_user_permission'),
    
    # Template Controller
    path('api/templates/', template_controller.get_all_templates, name='get_all_templates'),
    path('api/templates/<int:template_id>/', template_controller.get_template_detail, name='get_template_detail'),
    path('api/templates/type/<str:template_type>/', template_controller.get_templates_by_type, name='get_templates_by_type'),
    path('api/templates/create/', template_controller.create_template, name='create_template'),
    path('api/templates/<int:template_id>/update/', template_controller.update_template, name='update_template'),
    path('api/templates/<int:template_id>/delete/', template_controller.delete_template, name='delete_template'),
    path('api/templates/<int:template_id>/render/', template_controller.render_template, name='render_template'),
    path('api/templates/render-by-type/', template_controller.render_template_by_type, name='render_template_by_type'),
] 