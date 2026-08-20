from datetime import date

import factory
from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from factory.django import DjangoModelFactory

from mecip.models import (
    Attachments,
    Campus,
    Categorie_Course,
    Course,
    Question,
    QuestionAnswerOption,
    Questionnaire,
    QuestionnaireSection,
    ReferenceAttachment,
    Report,
    ReportQuestionAnswer,
    ReportTeamHistory,
    Team,
    Type_Course,
)
from mecip.permissions import (
    ROLE_COORDENADOR,
    ROLE_EQUIPE,
    ROLE_SUPERADMIN,
)


DEFAULT_PASSWORD = "SenhaTeste123!"


def make_uploaded_file(name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(
        name,
        b"conteudo de arquivo para teste",
        content_type="text/plain",
    )


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda number: f"Grupo {number}")


class TeamRoleGroupFactory(GroupFactory):
    name = ROLE_EQUIPE


class CoordinatorRoleGroupFactory(GroupFactory):
    name = ROLE_COORDENADOR


class SuperAdminRoleGroupFactory(GroupFactory):
    name = ROLE_SUPERADMIN


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    username = factory.Sequence(lambda number: f"usuario{number}")
    email = factory.LazyAttribute(
        lambda user: f"{user.username}@example.com"
    )
    first_name = "Usuario"
    last_name = factory.Sequence(lambda number: f"Teste {number}")
    password = DEFAULT_PASSWORD
    is_active = True
    is_staff = False
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop("password")
        return model_class.objects.create_user(
            *args,
            password=password,
            **kwargs,
        )


class TeamUserFactory(UserFactory):
    @factory.post_generation
    def equipe(self, create, extracted, **kwargs):
        if create:
            self.groups.add(TeamRoleGroupFactory())


class CoordinatorFactory(UserFactory):
    @factory.post_generation
    def coordenador(self, create, extracted, **kwargs):
        if create:
            self.groups.add(CoordinatorRoleGroupFactory())


class SuperAdminFactory(UserFactory):
    is_staff = True
    is_superuser = True

    @factory.post_generation
    def superadmin(self, create, extracted, **kwargs):
        if create:
            self.groups.add(SuperAdminRoleGroupFactory())


class CampusFactory(DjangoModelFactory):
    class Meta:
        model = Campus

    campus_name = factory.Sequence(
        lambda number: f"Campus Teste {number}"
    )
    city = factory.Sequence(lambda number: f"Cidade {number}")
    street = "Rua de Teste"
    neighborhood = "Bairro de Teste"
    number = factory.Sequence(lambda value: str(value + 1))
    contact_number = "11999999999"
    email_campus = factory.Sequence(
        lambda number: f"campus{number}@example.com"
    )


class CourseCategoryFactory(DjangoModelFactory):
    class Meta:
        model = Categorie_Course

    categorie = factory.Sequence(
        lambda number: f"Categoria {number}"
    )


class CourseTypeFactory(DjangoModelFactory):
    class Meta:
        model = Type_Course

    type_name_course = factory.Sequence(
        lambda number: f"Tipo de Curso {number}"
    )
    duration = "4"
    type_categorie = factory.SubFactory(CourseCategoryFactory)


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    campus = factory.SubFactory(CampusFactory)
    type_course = factory.SubFactory(CourseTypeFactory)
    description = factory.LazyAttribute(
        lambda course: f"Descricao de {course.type_course.type_name_course}"
    )


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team
        skip_postgeneration_save = True

    team_name = factory.Sequence(lambda number: f"Equipe {number}")
    campus = factory.SubFactory(CampusFactory)

    @factory.post_generation
    def users(self, create, extracted, **kwargs):
        if create and extracted:
            self.users.add(*extracted)


class QuestionnaireFactory(DjangoModelFactory):
    class Meta:
        model = Questionnaire

    name = factory.Sequence(
        lambda number: f"Questionario {number}"
    )
    description = "Questionario criado para teste"
    campus = factory.SubFactory(CampusFactory)
    active = True


class QuestionnaireSectionFactory(DjangoModelFactory):
    class Meta:
        model = QuestionnaireSection
        skip_postgeneration_save = True

    questionnaire = factory.SubFactory(QuestionnaireFactory)
    name = factory.Sequence(lambda number: f"Secao {number}")
    order = factory.Sequence(lambda number: number + 1)

    @factory.post_generation
    def teams(self, create, extracted, **kwargs):
        if create and extracted:
            self.teams.add(*extracted)


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    section = factory.SubFactory(QuestionnaireSectionFactory)
    indicator = factory.Sequence(
        lambda number: f"Indicador {number}"
    )
    special_condition = ""
    text = factory.Sequence(lambda number: f"Pergunta {number}?")
    field_type = "text"
    required = True
    order = factory.Sequence(lambda number: number + 1)
    choices = ""


class TextQuestionFactory(QuestionFactory):
    field_type = "text"


class MultipleChoiceQuestionFactory(QuestionFactory):
    field_type = "choice"


class QuestionAnswerOptionFactory(DjangoModelFactory):
    class Meta:
        model = QuestionAnswerOption

    question = factory.SubFactory(MultipleChoiceQuestionFactory)
    answer_value = factory.Sequence(
        lambda number: f"Alternativa {number}"
    )
    acceptance_criteria = factory.Sequence(
        lambda number: f"Criterio {number}"
    )


class ReportFactory(DjangoModelFactory):
    class Meta:
        model = Report
        skip_postgeneration_save = True

    campus = factory.SubFactory(CampusFactory)
    course = factory.SubFactory(
        CourseFactory,
        campus=factory.SelfAttribute("..campus"),
    )
    questionnaire = factory.SubFactory(
        QuestionnaireFactory,
        campus=factory.SelfAttribute("..campus"),
    )
    year = factory.Sequence(lambda number: 2020 + number)
    assessment = "Avaliacao de teste"
    assigned_team = factory.SubFactory(
        TeamFactory,
        campus=factory.SelfAttribute("..campus"),
    )
    assigned_user = factory.SubFactory(TeamUserFactory)
    due_date = factory.LazyFunction(lambda: date(2026, 12, 31))
    notes = "Observacoes de teste"
    status = "Pendente"

    @factory.post_generation
    def team_membership(self, create, extracted, **kwargs):
        if create and self.assigned_team_id and self.assigned_user_id:
            self.assigned_team.users.add(self.assigned_user)


class ReportQuestionAnswerFactory(DjangoModelFactory):
    class Meta:
        model = ReportQuestionAnswer

    question = factory.SubFactory(TextQuestionFactory)
    report = factory.SubFactory(
        ReportFactory,
        campus=factory.SelfAttribute(
            "..question.section.questionnaire.campus"
        ),
        questionnaire=factory.SelfAttribute(
            "..question.section.questionnaire"
        ),
    )
    selected_answer_option = None
    answer = "Resposta de teste"
    free_text = "Argumentacao de teste"


class ReferenceAttachmentFactory(DjangoModelFactory):
    class Meta:
        model = ReferenceAttachment

    name = factory.Sequence(
        lambda number: f"Anexo catalogado {number}"
    )
    file = factory.Sequence(
        lambda number: make_uploaded_file(f"referencia-{number}.txt")
    )
    description = "Anexo de referencia para teste"
    active = True


class DirectAttachmentFactory(DjangoModelFactory):
    class Meta:
        model = Attachments

    answer = factory.SubFactory(ReportQuestionAnswerFactory)
    reference_attachment = None
    name = factory.Sequence(lambda number: f"Anexo direto {number}")
    file = factory.Sequence(
        lambda number: make_uploaded_file(f"anexo-direto-{number}.txt")
    )
    description = "Upload direto para teste"


class CataloguedAttachmentFactory(DjangoModelFactory):
    class Meta:
        model = Attachments

    answer = factory.SubFactory(ReportQuestionAnswerFactory)
    reference_attachment = factory.SubFactory(
        ReferenceAttachmentFactory
    )
    name = factory.LazyAttribute(
        lambda attachment: attachment.reference_attachment.name
    )
    file = ""
    description = "Anexo selecionado do catalogo"


class ReportTeamHistoryFactory(DjangoModelFactory):
    class Meta:
        model = ReportTeamHistory

    report = factory.SubFactory(ReportFactory)
    team = factory.LazyAttribute(
        lambda history: history.report.assigned_team
    )
