from django.urls import path
from mecip import views

app_name = 'mecip'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),


    # Criar Campus
    path('campus/<int:campus_id>/', views.campus, name='campus'),
    path('campus/create/', views.create, name='create'),
    path('campus/<int:campus_id>/update', views.update, name='update'),

    # Criar Curso
    path('curso/', views.index_course, name='index_course'),
    path('curso/<int:course_id>/', views.course, name='course'),
    path('curso/create/', views.create_course, name='create_course'),
    path('curso/<int:course_id>/update', views.update_course, name='update_course'),

    # Criar Tipo Curso
    path('tipo/', views.index_type_course, name='index_type'),
    path('tipo/<int:type_course_id>/', views.type_course, name='type_course'),
    path('tipo/criar/', views.create_type_course, name='create_type'),
    path('tipo/<int:type_course_id>/editar', views.update_type_course, name='update_type'),

    #usercreation
    path('user/register/', views.register, name='register'),
    path('user/logout/', views.logout_view, name='logout'),

    # Criar Relatório
    path('relatorio/', views.index_report, name='index_report'),
    path('relatorio/<int:report_id>/', views.report, name='report'),
    path('relatorio/criar', views.create_report, name='create_report'),
    path('curso/<int:course_id>/<int:campus_id>/criar/relatorio', views.create_report_params, name='create_report_params'),
    path('relatorio/<int:report_id>/editar', views.update_report, name='update_report'),

    # Criar Equipe
    path('equipe/', views.index_team, name='index_team'),
    path('equipe/<int:team_id>/', views.team, name='team'),
    path('equipe/criar/', views.create_team, name='create_team'),
    path('equipe/<int:team_id>/editar', views.update_team, name='update_team'),
    path('equipe/<int:team_id>/adicionar-usuario/', views.add_user_to_team, name='add_user_to_team'),
    path('equipe/<int:team_id>/remover-usuario/<int:user_id>/', views.remove_user_from_team, name='remove_user_from_team'),

]