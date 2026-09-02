from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from mecip.models import (
    Question,
    Questionnaire,
    QuestionnaireSection,
    ReferenceAttachment,
    Report,
    ReportQuestionAnswer,
    Team,
)
from mecip.validators import normalize_team_name
from tests.factories import (
    CampusFactory,
    DirectAttachmentFactory,
    QuestionAnswerOptionFactory,
    ReportQuestionAnswerFactory,
    ReportTeamHistoryFactory,
    TeamFactory,
    TeamUserFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.unit]


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("Équipe A", "equipea"),
        (" EQUIPE A ", "equipea"),
        ("e q u i p e a", "equipea"),
        ("ÉQUIPE\tA", "equipea"),
    ),
)
def test_normalizacao_do_nome_da_equipe(value, expected):
    assert normalize_team_name(value) == expected


def test_team_model_rejeita_nome_equivalente_no_mesmo_campus():
    existing_team = TeamFactory(team_name="Équipe A")
    duplicate = Team(
        team_name=" equipea ",
        campus=existing_team.campus,
    )

    with pytest.raises(ValidationError) as error:
        duplicate.full_clean()

    assert (
        "Já existe uma equipe com este nome neste campus"
        in error.value.message_dict["team_name"]
    )


def test_team_orm_rejeita_nome_equivalente_no_mesmo_campus():
    existing_team = TeamFactory(team_name="Équipe A")

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Team.objects.create(
                team_name=" EQUIPE A ",
                campus=existing_team.campus,
            )


def test_team_orm_permite_nome_equivalente_em_campus_diferente():
    TeamFactory(team_name="Équipe A")
    other_campus = CampusFactory()

    created_team = Team.objects.create(
        team_name=" equipea ",
        campus=other_campus,
    )

    assert created_team.normalized_name == "equipea"


def test_constraint_de_banco_rejeita_normalizacao_duplicada():
    first_team = TeamFactory(team_name="Equipe A")
    second_team = TeamFactory(
        team_name="Equipe B",
        campus=first_team.campus,
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Team.objects.filter(pk=second_team.pk).update(
                normalized_name=first_team.normalized_name,
            )


def test_relatorio_mesmo_curso_campus_em_ano_diferente_e_criado(
    report,
):
    new_report = Report.objects.create(
        course=report.course,
        campus=report.campus,
        year=report.year + 1,
        assessment="Avaliacao do ano seguinte",
    )

    assert new_report.year == report.year + 1


def test_relatorio_mesmo_curso_campus_e_ano_viola_unicidade(
    report,
):
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Report.objects.create(
                course=report.course,
                campus=report.campus,
                year=report.year,
                assessment="Relatorio duplicado",
            )


def test_modelos_aplicam_valores_padrao(course, campus):
    questionnaire = Questionnaire.objects.create(
        name="Questionario com defaults",
        campus=campus,
    )
    section = QuestionnaireSection.objects.create(
        questionnaire=questionnaire,
        name="Secao com defaults",
    )
    question = Question.objects.create(
        section=section,
        text="Pergunta com defaults",
    )
    default_report = Report.objects.create(
        course=course,
        campus=campus,
        year=2099,
        assessment="Avaliacao",
    )
    reference = ReferenceAttachment.objects.create(
        name="Referencia com defaults",
        file="reference_attachments/default.txt",
    )

    assert questionnaire.description == ""
    assert questionnaire.active
    assert questionnaire.argumentation_character_limit == 2000
    assert section.order == 0
    assert question.indicator == ""
    assert question.special_condition == ""
    assert question.field_type == "text"
    assert question.required
    assert question.order == 0
    assert question.choices == ""
    assert default_report.status == "Pendente"
    assert reference.description == ""
    assert reference.active


def test_secoes_e_perguntas_sao_ordenadas_por_ordem(
    questionnaire,
):
    later_section = QuestionnaireSection.objects.create(
        questionnaire=questionnaire,
        name="Secao posterior",
        order=2,
    )
    first_section = QuestionnaireSection.objects.create(
        questionnaire=questionnaire,
        name="Secao inicial",
        order=1,
    )
    second_question = Question.objects.create(
        section=first_section,
        text="Segunda pergunta",
        order=2,
    )
    first_question = Question.objects.create(
        section=first_section,
        text="Primeira pergunta",
        order=1,
    )
    later_question = Question.objects.create(
        section=later_section,
        text="Pergunta da secao posterior",
        order=1,
    )

    assert list(questionnaire.sections.all()) == [
        first_section,
        later_section,
    ]
    assert list(
        Question.objects.filter(
            section__questionnaire=questionnaire
        )
    ) == [
        first_question,
        second_question,
        later_question,
    ]


def test_representacoes_textuais_dos_modelos_descrevem_objetos(
    campus,
    course_category,
    course_type,
    course,
    team,
    questionnaire,
    section,
    text_question,
    multiple_choice_question,
    report,
    reference_attachment,
):
    option = QuestionAnswerOptionFactory(
        question=multiple_choice_question,
        answer_value="Conforme",
    )
    answer = ReportQuestionAnswerFactory(
        report=report,
        question=multiple_choice_question,
        selected_answer_option=option,
        answer=option.answer_value,
    )
    attachment = DirectAttachmentFactory(answer=answer)
    history = ReportTeamHistoryFactory(report=report, team=team)

    expected_values = (
        (campus, f"{campus.campus_name} {campus.city}"),
        (course_category, course_category.categorie),
        (course_type, course_type.type_name_course),
        (course, course.type_course.type_name_course),
        (questionnaire, questionnaire.name),
        (section, f"{questionnaire.name} - {section.name}"),
        (
            text_question,
            f"{text_question.order} - {text_question.text[:50]}",
        ),
        (option, option.answer_value),
        (
            answer,
            f"{report} - {multiple_choice_question.text[:40]}",
        ),
        (reference_attachment, reference_attachment.name),
        (attachment, attachment.name),
        (report, f"{course} {campus} - {report.year}"),
        (team, team.team_name),
        (
            history,
            f"{report} -> {team} ({history.start_date.isoformat()})",
        ),
    )

    for instance, expected in expected_values:
        assert str(instance) == expected


def test_equipe_associa_usuarios_e_historico_ordena_mais_recente(
    report,
):
    member = TeamUserFactory()
    first_team = TeamFactory(
        campus=report.campus,
        users=(member,),
    )
    second_team = TeamFactory(campus=report.campus)
    current_time = timezone.now()
    older_history = ReportTeamHistoryFactory(
        report=report,
        team=first_team,
        start_date=current_time - timedelta(days=1),
    )
    newer_history = ReportTeamHistoryFactory(
        report=report,
        team=second_team,
        start_date=current_time,
    )

    assert first_team.users.filter(pk=member.pk).exists()
    assert member.teams.filter(pk=first_team.pk).exists()
    assert list(report.team_history.all()) == [
        newer_history,
        older_history,
    ]


def test_resposta_armazena_alternativa_e_argumentacao(
    report,
    multiple_choice_question,
):
    option = QuestionAnswerOptionFactory(
        question=multiple_choice_question,
    )
    answer = ReportQuestionAnswer.objects.create(
        report=report,
        question=multiple_choice_question,
        selected_answer_option=option,
        answer=option.answer_value,
        free_text="Argumentacao complementar",
    )

    assert answer.selected_answer_option == option
    assert answer.answer == option.answer_value
    assert answer.free_text == "Argumentacao complementar"
    assert option.report_answers.get() == answer
    assert report.answers.get(question=multiple_choice_question) == answer


def test_resposta_duplicada_para_relatorio_e_pergunta_viola_unicidade(
    report,
    text_question,
):
    ReportQuestionAnswer.objects.create(
        report=report,
        question=text_question,
        answer="Primeira resposta",
    )

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ReportQuestionAnswer.objects.create(
                report=report,
                question=text_question,
                answer="Resposta duplicada",
            )
