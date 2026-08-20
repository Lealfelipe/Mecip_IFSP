import json
from pathlib import Path

import pytest

from mecip.permissions import (
    ROLE_COORDENADOR,
    ROLE_EQUIPE,
    ROLE_SUPERADMIN,
)
from tests.factories import (
    CampusFactory,
    CataloguedAttachmentFactory,
    CoordinatorFactory,
    DirectAttachmentFactory,
    MultipleChoiceQuestionFactory,
    QuestionAnswerOptionFactory,
    ReferenceAttachmentFactory,
    ReportQuestionAnswerFactory,
    SuperAdminFactory,
    TeamUserFactory,
    TextQuestionFactory,
    UserFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def test_role_factories_assign_expected_roles():
    team_user = TeamUserFactory()
    coordinator = CoordinatorFactory()
    superadmin = SuperAdminFactory()

    assert set(team_user.groups.values_list("name", flat=True)) == {
        ROLE_EQUIPE
    }
    assert set(coordinator.groups.values_list("name", flat=True)) == {
        ROLE_COORDENADOR
    }
    assert set(superadmin.groups.values_list("name", flat=True)) == {
        ROLE_SUPERADMIN
    }
    assert superadmin.is_staff
    assert superadmin.is_superuser


def test_factory_sequences_create_unique_values():
    first_user, second_user = UserFactory.create_batch(2)
    first_campus, second_campus = CampusFactory.create_batch(2)

    assert first_user.username != second_user.username
    assert first_user.email != second_user.email
    assert first_campus.campus_name != second_campus.campus_name
    assert first_campus.email_campus != second_campus.email_campus


def test_shared_fixtures_build_coherent_domain_graph(
    role_groups,
    common_user,
    team_user,
    coordinator,
    superadmin,
    campus,
    course_category,
    course_type,
    course,
    team,
    questionnaire,
    section,
    text_question,
    multiple_choice_question,
    answer_options,
    report,
    answer,
    reference_attachment,
    direct_attachment,
    catalogued_attachment,
    report_team_history,
):
    assert set(role_groups) == {
        ROLE_EQUIPE,
        ROLE_COORDENADOR,
        ROLE_SUPERADMIN,
    }
    assert common_user.groups.count() == 0
    assert course_type.type_categorie == course_category
    assert course.campus == campus
    assert course.type_course == course_type
    assert team.campus == campus
    assert team.users.filter(pk=team_user.pk).exists()
    assert questionnaire.campus == campus
    assert section.questionnaire == questionnaire
    assert section.teams.filter(pk=team.pk).exists()
    assert text_question.section == section
    assert multiple_choice_question.section == section
    assert all(
        option.question == multiple_choice_question
        for option in answer_options
    )
    assert report.course == course
    assert report.campus == campus
    assert report.questionnaire == questionnaire
    assert report.assigned_team == team
    assert report.assigned_user == team_user
    assert answer.report == report
    assert answer.question == text_question
    assert direct_attachment.answer == answer
    assert catalogued_attachment.answer == answer
    assert (
        catalogued_attachment.reference_attachment
        == reference_attachment
    )
    assert report_team_history.report == report
    assert report_team_history.team == team
    assert coordinator.is_authenticated
    assert superadmin.is_superuser


def test_question_factories_create_text_choice_and_options():
    text_question = TextQuestionFactory()
    choice_question = MultipleChoiceQuestionFactory()
    options = QuestionAnswerOptionFactory.create_batch(
        2,
        question=choice_question,
    )

    assert text_question.field_type == "text"
    assert choice_question.field_type == "choice"
    assert choice_question.answer_options.count() == 2
    assert all(option.question == choice_question for option in options)


def test_attachment_factories_use_isolated_media(settings):
    answer = ReportQuestionAnswerFactory()
    reference = ReferenceAttachmentFactory()
    direct = DirectAttachmentFactory(answer=answer)
    catalogued = CataloguedAttachmentFactory(
        answer=answer,
        reference_attachment=reference,
    )

    media_root = Path(settings.MEDIA_ROOT)

    assert Path(direct.file.path).is_file()
    assert Path(direct.file.path).is_relative_to(media_root)
    assert Path(reference.file.path).is_file()
    assert Path(reference.file.path).is_relative_to(media_root)
    assert direct.reference_attachment is None
    assert not catalogued.file
    assert catalogued.attachment_file == reference.file


def test_file_fixtures_represent_valid_and_invalid_inputs(
    valid_upload,
    invalid_upload,
    valid_questionnaire_payload,
    invalid_questionnaire_content,
):
    assert valid_upload.name.endswith(".txt")
    assert valid_upload.content_type == "text/plain"
    assert valid_upload.read()
    assert invalid_upload.name.endswith(".exe")
    assert invalid_upload.content_type == "application/octet-stream"
    assert invalid_upload.read()
    assert valid_questionnaire_payload["questionario"]
    assert valid_questionnaire_payload["conceitos"]

    with pytest.raises(json.JSONDecodeError):
        json.loads(invalid_questionnaire_content)
