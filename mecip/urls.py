from django.urls import path
from mecip import views

app_name = 'mecip'

urlpatterns = [
    path('', views.dashboard, name='connected_index'),
    path('', views.login_view, name='index'),
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
    path('relatorio/<int:report_id>/atribuir/', views.assign_report, name='assign_report'),
    path('relatorio/<int:report_id>/questionario/', views.view_questionnaire, name='view_questionnaire'),
    path('relatorio/<int:report_id>/responder/', views.answer_questionnaire, name='answer_questionnaire'),
    path('relatorio/<int:report_id>/avancar-status/', views.advance_report_status, name='advance_report_status'),
    path('relatorio/<int:report_id>/status/<str:action>/', views.change_report_status, name='change_report_status'),
    path('relatorio/<int:report_id>/pdf/download/', views.report_pdf_download, name='report_pdf_download'),
    path('relatorio/criar', views.create_report, name='create_report'),
    path('curso/<int:course_id>/<int:campus_id>/criar/relatorio', views.create_report_params, name='create_report_params'),
    path('relatorio/<int:report_id>/editar', views.update_report, name='update_report'),
    path('api/course/<int:course_id>/campuses/', views.get_campus_for_course, name='get_campus_for_course'),
    path('api/campus/<int:campus_id>/courses/', views.get_courses_for_campus, name='get_courses_for_campus'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Base de Anexos de Referencia
    path('anexos-referencia/', views.index_reference_attachment, name='index_reference_attachment'),
    path('anexos-referencia/criar/', views.create_reference_attachment, name='create_reference_attachment'),
    path('anexos-referencia/<int:reference_attachment_id>/editar/', views.update_reference_attachment, name='update_reference_attachment'),
    path('anexos-referencia/<int:reference_attachment_id>/excluir/', views.delete_reference_attachment, name='delete_reference_attachment'),

    # Criar Equipe
    path('equipe/', views.index_team, name='index_team'),
    path('equipe/<int:team_id>/', views.team, name='team'),
    path('equipe/criar/', views.create_team, name='create_team'),
    path('equipe/<int:team_id>/editar', views.update_team, name='update_team'),
    path('equipe/<int:team_id>/adicionar-usuario/', views.add_user_to_team, name='add_user_to_team'),
    path('equipe/<int:team_id>/remover-usuario/<int:user_id>/', views.remove_user_from_team, name='remove_user_from_team'),

    # Criar Questionário
    path('questionario/', views.index_questionnaire, name='index_questionnaire'),
    path('questionario/<int:questionnaire_id>/', views.questionnaire, name='questionnaire'),
    path('questionario/criar/', views.create_questionnaire, name='create_questionnaire'),
    path('questionario/<int:questionnaire_id>/editar', views.update_questionnaire, name='update_questionnaire'),
    path('questionario/<int:questionnaire_id>/secao/criar/', views.create_questionnaire_section, name='create_questionnaire_section'),
    path('questionario/<int:questionnaire_id>/secao/<int:section_id>/editar', views.update_questionnaire_section, name='update_questionnaire_section'),
    path('questionario/<int:questionnaire_id>/secao/<int:section_id>/deletar', views.delete_questionnaire_section, name='delete_questionnaire_section'),

    # Criar Questão
    path('questionario/<int:questionnaire_id>/questao/criar/', views.create_question, name='create_question'),
    path('questionario/<int:questionnaire_id>/questao/<int:question_id>/editar', views.update_question, name='update_question'),
    path('questionario/<int:questionnaire_id>/questao/<int:question_id>/deletar', views.delete_question, name='delete_question'),

]
