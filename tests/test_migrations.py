import pytest
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor


pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.integration,
]

MIGRATE_FROM = [('mecip', '0031_attachments_reference_attachment')]
MIGRATE_TO = [('mecip', '0032_populate_missing_choice_options')]
MIGRATE_TEAM_FROM = [('mecip', '0032_populate_missing_choice_options')]
MIGRATE_TEAM_TO = [('mecip', '0033_team_normalized_name')]
MIGRATE_LATEST = MIGRATE_TEAM_TO


@pytest.fixture(autouse=True)
def restore_latest_migration():
    yield
    MigrationExecutor(connection).migrate(MIGRATE_LATEST)


def test_migration_popula_somente_perguntas_choice_sem_alternativas():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_FROM)
    old_apps = executor.loader.project_state(MIGRATE_FROM).apps

    Questionnaire = old_apps.get_model('mecip', 'Questionnaire')
    QuestionnaireSection = old_apps.get_model(
        'mecip',
        'QuestionnaireSection',
    )
    Question = old_apps.get_model('mecip', 'Question')
    QuestionAnswerOption = old_apps.get_model(
        'mecip',
        'QuestionAnswerOption',
    )

    questionnaire = Questionnaire.objects.create(name='Questionário legado')
    section = QuestionnaireSection.objects.create(
        questionnaire=questionnaire,
        name='Seção legada',
    )
    choice_without_options = Question.objects.create(
        section=section,
        text='Escolha sem alternativas',
        field_type='choice',
    )
    choice_with_options = Question.objects.create(
        section=section,
        text='Escolha já válida',
        field_type='choice',
    )
    existing_option = QuestionAnswerOption.objects.create(
        question=choice_with_options,
        answer_value='Alternativa existente',
        acceptance_criteria='Critério existente',
    )
    text_without_options = Question.objects.create(
        section=section,
        text='Pergunta textual',
        field_type='text',
    )

    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_TO)
    new_apps = executor.loader.project_state(MIGRATE_TO).apps
    MigratedOption = new_apps.get_model('mecip', 'QuestionAnswerOption')

    created_option = MigratedOption.objects.get(
        question_id=choice_without_options.pk,
    )
    assert created_option.answer_value == 'Alternativa pendente de revisão'
    assert created_option.acceptance_criteria == ''

    existing_options = MigratedOption.objects.filter(
        question_id=choice_with_options.pk,
    )
    assert list(existing_options.values_list('id', flat=True)) == [
        existing_option.pk,
    ]
    assert existing_options.get().answer_value == 'Alternativa existente'
    assert existing_options.get().acceptance_criteria == 'Critério existente'

    assert not MigratedOption.objects.filter(
        question_id=text_without_options.pk,
    ).exists()


def test_migration_normaliza_equipes_e_cria_constraint_por_campus():
    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_TEAM_FROM)
    old_apps = executor.loader.project_state(MIGRATE_TEAM_FROM).apps

    Campus = old_apps.get_model('mecip', 'Campus')
    Team = old_apps.get_model('mecip', 'Team')

    first_campus = Campus.objects.create(
        campus_name='Campus A',
        city='Cidade A',
        street='Rua A',
        neighborhood='Centro',
        number='1',
        contact_number='1111',
        email_campus='campus-a@example.com',
    )
    second_campus = Campus.objects.create(
        campus_name='Campus B',
        city='Cidade B',
        street='Rua B',
        neighborhood='Centro',
        number='2',
        contact_number='2222',
        email_campus='campus-b@example.com',
    )
    first_team = Team.objects.create(
        team_name='Équipe A',
        campus=first_campus,
    )
    second_team = Team.objects.create(
        team_name='Equipe B',
        campus=first_campus,
    )
    equivalent_other_campus = Team.objects.create(
        team_name=' EQUIPE A ',
        campus=second_campus,
    )

    executor = MigrationExecutor(connection)
    executor.migrate(MIGRATE_TEAM_TO)
    new_apps = executor.loader.project_state(MIGRATE_TEAM_TO).apps
    MigratedTeam = new_apps.get_model('mecip', 'Team')

    assert (
        MigratedTeam.objects.get(pk=first_team.pk).normalized_name
        == 'equipea'
    )
    assert (
        MigratedTeam.objects.get(pk=second_team.pk).normalized_name
        == 'equipeb'
    )
    assert (
        MigratedTeam.objects.get(
            pk=equivalent_other_campus.pk,
        ).normalized_name
        == 'equipea'
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            MigratedTeam.objects.create(
                team_name='Outra grafia',
                normalized_name='equipea',
                campus_id=first_campus.pk,
            )
