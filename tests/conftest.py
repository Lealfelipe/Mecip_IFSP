import json
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from mecip.permissions import (
    ROLE_COORDENADOR,
    ROLE_EQUIPE,
    ROLE_SUPERADMIN,
)
from tests.factories import (
    CampusFactory,
    CataloguedAttachmentFactory,
    CoordinatorFactory,
    CoordinatorRoleGroupFactory,
    CourseCategoryFactory,
    CourseFactory,
    CourseTypeFactory,
    DirectAttachmentFactory,
    MultipleChoiceQuestionFactory,
    QuestionAnswerOptionFactory,
    QuestionnaireFactory,
    QuestionnaireSectionFactory,
    ReferenceAttachmentFactory,
    ReportFactory,
    ReportQuestionAnswerFactory,
    ReportTeamHistoryFactory,
    SuperAdminFactory,
    SuperAdminRoleGroupFactory,
    TeamFactory,
    TeamRoleGroupFactory,
    TeamUserFactory,
    TextQuestionFactory,
    UserFactory,
)


FIXTURE_FILES = Path(__file__).parent / "fixtures"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticate_api_client(api_client):
    def authenticate(user):
        token, _ = Token.objects.get_or_create(user=user)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )
        return api_client

    return authenticate


@pytest.fixture
def role_groups(db):
    return {
        ROLE_EQUIPE: TeamRoleGroupFactory(),
        ROLE_COORDENADOR: CoordinatorRoleGroupFactory(),
        ROLE_SUPERADMIN: SuperAdminRoleGroupFactory(),
    }


@pytest.fixture
def common_user(db):
    return UserFactory()


@pytest.fixture
def team_user(db):
    return TeamUserFactory()


@pytest.fixture
def coordinator(db):
    return CoordinatorFactory()


@pytest.fixture
def superadmin(db):
    return SuperAdminFactory()


@pytest.fixture
def campus(db):
    return CampusFactory()


@pytest.fixture
def course_category(db):
    return CourseCategoryFactory()


@pytest.fixture
def course_type(db, course_category):
    return CourseTypeFactory(type_categorie=course_category)


@pytest.fixture
def course(db, campus, course_type):
    return CourseFactory(campus=campus, type_course=course_type)


@pytest.fixture
def team(db, campus, team_user):
    return TeamFactory(campus=campus, users=(team_user,))


@pytest.fixture
def questionnaire(db, campus):
    return QuestionnaireFactory(campus=campus)


@pytest.fixture
def section(db, questionnaire, team):
    return QuestionnaireSectionFactory(
        questionnaire=questionnaire,
        teams=(team,),
    )


@pytest.fixture
def text_question(db, section):
    return TextQuestionFactory(section=section)


@pytest.fixture
def multiple_choice_question(db, section):
    return MultipleChoiceQuestionFactory(section=section)


@pytest.fixture
def answer_options(db, multiple_choice_question):
    return QuestionAnswerOptionFactory.create_batch(
        2,
        question=multiple_choice_question,
    )


@pytest.fixture
def report(
    db,
    campus,
    course,
    questionnaire,
    team,
    team_user,
):
    return ReportFactory(
        campus=campus,
        course=course,
        questionnaire=questionnaire,
        assigned_team=team,
        assigned_user=team_user,
    )


@pytest.fixture
def answer(db, report, text_question):
    return ReportQuestionAnswerFactory(
        report=report,
        question=text_question,
    )


@pytest.fixture
def reference_attachment(db):
    return ReferenceAttachmentFactory()


@pytest.fixture
def direct_attachment(db, answer):
    return DirectAttachmentFactory(answer=answer)


@pytest.fixture
def catalogued_attachment(db, answer, reference_attachment):
    return CataloguedAttachmentFactory(
        answer=answer,
        reference_attachment=reference_attachment,
    )


@pytest.fixture
def report_team_history(db, report, team):
    return ReportTeamHistoryFactory(report=report, team=team)


@pytest.fixture
def valid_upload_path():
    return FIXTURE_FILES / "upload_valid.txt"


@pytest.fixture
def invalid_upload_path():
    return FIXTURE_FILES / "upload_invalid.exe"


@pytest.fixture
def valid_upload(valid_upload_path):
    return SimpleUploadedFile(
        valid_upload_path.name,
        valid_upload_path.read_bytes(),
        content_type="text/plain",
    )


@pytest.fixture
def invalid_upload(invalid_upload_path):
    return SimpleUploadedFile(
        invalid_upload_path.name,
        invalid_upload_path.read_bytes(),
        content_type="application/octet-stream",
    )


@pytest.fixture
def valid_questionnaire_json_path():
    return FIXTURE_FILES / "questionnaire_valid.json"


@pytest.fixture
def invalid_questionnaire_json_path():
    return FIXTURE_FILES / "questionnaire_invalid.json"


@pytest.fixture
def valid_questionnaire_payload(valid_questionnaire_json_path):
    return json.loads(
        valid_questionnaire_json_path.read_text(encoding="utf-8")
    )


@pytest.fixture
def invalid_questionnaire_content(invalid_questionnaire_json_path):
    return invalid_questionnaire_json_path.read_text(encoding="utf-8")
