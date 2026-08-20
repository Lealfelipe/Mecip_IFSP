import pytest
from django.forms.forms import NON_FIELD_ERRORS

from mecip.forms import (
    AttachmentForm,
    AttachmentFormSet,
    CampusForm,
    CourseForm,
    CustomAuthenticationForm,
    QuestionAnswerOptionForm,
    QuestionAnswerOptionFormSet,
    QuestionForm,
    QuestionnaireForm,
    QuestionnaireSectionForm,
    ReferenceAttachmentForm,
    RegisterForm,
    ReportForm,
    ReportQuestionAnswerForm,
    TeamForm,
    TypeCourseForm,
)
from mecip.models import QuestionAnswerOption, ReferenceAttachment
from mecip.permissions import ROLE_EQUIPE
from tests.factories import (
    CampusFactory,
    QuestionAnswerOptionFactory,
    TeamFactory,
    UserFactory,
)


pytestmark = [pytest.mark.django_db, pytest.mark.integration]


def campus_payload(**overrides):
    data = {
        "campus_name": "Campus Sul",
        "city": "Cidade Sul",
        "street": "Rua Principal",
        "neighborhood": "Centro",
        "number": "100",
        "email_campus": "campus-sul@example.com",
        "contact_number": "11999999999",
    }
    data.update(overrides)
    return data


def register_payload(**overrides):
    data = {
        "first_name": "Usuario",
        "last_name": "Formulario",
        "email": "usuario-formulario@example.com",
        "username": "usuario-formulario",
        "password1": "SenhaForte123!",
        "password2": "SenhaForte123!",
    }
    data.update(overrides)
    return data


def report_payload(
    course,
    campus,
    questionnaire,
    team,
    team_user,
    **overrides,
):
    data = {
        "type_course": course.type_course_id,
        "campus": campus.id,
        "year": "2035",
        "questionnaire": questionnaire.id,
        "assigned_team": team.id,
        "assigned_user": team_user.id,
        "due_date": "2035-12-31",
        "notes": "Observacoes do formulario",
        "status": "Pendente",
    }
    data.update(overrides)
    return data


def question_payload(section, **overrides):
    data = {
        "section": section.id,
        "indicator": "Indicador 1",
        "special_condition": "",
        "text": "Pergunta criada pelo formulario",
        "field_type": "text",
        "required": "on",
        "order": "1",
        "choices": "",
    }
    data.update(overrides)
    return data


REQUIRED_FIELD_CASES = (
    pytest.param(
        CampusForm,
        {
            "campus_name",
            "city",
            "street",
            "neighborhood",
            "number",
            "email_campus",
            "contact_number",
        },
        id="campus",
    ),
    pytest.param(
        CourseForm,
        {"type_course", "description", "campus"},
        id="curso",
    ),
    pytest.param(
        RegisterForm,
        {
            "first_name",
            "last_name",
            "email",
            "username",
            "password1",
            "password2",
        },
        id="usuario",
    ),
    pytest.param(
        CustomAuthenticationForm,
        {"username", "password"},
        id="autenticacao",
    ),
    pytest.param(
        ReportForm,
        {"type_course", "campus", "year", "status"},
        id="relatorio",
    ),
    pytest.param(
        QuestionnaireForm,
        {"name"},
        id="questionario",
    ),
    pytest.param(
        ReferenceAttachmentForm,
        {"name", "file"},
        id="anexo-catalogado",
    ),
    pytest.param(
        QuestionnaireSectionForm,
        {"questionnaire", "name", "order"},
        id="secao",
    ),
    pytest.param(
        QuestionForm,
        {"section", "text", "field_type", "order"},
        id="pergunta",
    ),
    pytest.param(
        QuestionAnswerOptionForm,
        {"answer_value"},
        id="alternativa",
    ),
    pytest.param(
        AttachmentForm,
        {"name"},
        id="anexo-direto",
    ),
    pytest.param(
        TypeCourseForm,
        {"type_name_course", "duration", "type_categorie"},
        id="tipo-curso",
    ),
    pytest.param(
        TeamForm,
        {"team_name", "campus"},
        id="equipe",
    ),
)


@pytest.mark.parametrize(
    ("form_class", "required_fields"),
    REQUIRED_FIELD_CASES,
)
def test_formularios_rejeitam_campos_obrigatorios_ausentes(
    form_class,
    required_fields,
):
    form = form_class(data={})

    assert not form.is_valid()
    assert required_fields <= set(form.errors)


def test_campus_form_salva_dados_validos():
    form = CampusForm(data=campus_payload())

    assert form.is_valid(), form.errors

    campus = form.save()

    assert campus.campus_name == "Campus Sul"
    assert campus.city == "Cidade Sul"


def test_campus_form_rejeita_nome_igual_a_cidade():
    form = CampusForm(
        data=campus_payload(
            campus_name="Mesmo nome",
            city="Mesmo nome",
        )
    )

    assert not form.is_valid()
    expected_message = (
        "Nome do Campus não pode ser igual ao nome da Cidade"
    )
    assert expected_message in form.errors["campus_name"]
    assert expected_message in form.errors["city"]


def test_campus_form_rejeita_nome_reservado_abc():
    form = CampusForm(data=campus_payload(campus_name="ABC"))

    assert not form.is_valid()
    assert "Nome inválido" in form.errors["campus_name"]


def test_course_form_salva_vinculo_com_tipo_e_campus(
    campus,
    course_type,
):
    form = CourseForm(
        data={
            "type_course": course_type.id,
            "description": "Curso criado pelo formulario",
            "campus": campus.id,
        }
    )

    assert form.is_valid(), form.errors

    course = form.save()

    assert course.type_course == course_type
    assert course.campus == campus


def test_course_form_rejeita_tipo_duplicado_no_mesmo_campus(course):
    form = CourseForm(
        data={
            "type_course": course.type_course_id,
            "description": "Curso duplicado",
            "campus": course.campus_id,
        }
    )

    assert not form.is_valid()
    assert NON_FIELD_ERRORS in form.errors


def test_register_form_cria_usuario_com_papel_equipe():
    form = RegisterForm(data=register_payload())

    assert form.is_valid(), form.errors

    user = form.save()

    assert user.check_password("SenhaForte123!")
    assert user.groups.filter(name=ROLE_EQUIPE).exists()


def test_register_form_rejeita_email_duplicado():
    UserFactory(email="duplicado@example.com")
    form = RegisterForm(
        data=register_payload(
            email="duplicado@example.com",
            username="outro-usuario",
        )
    )

    assert not form.is_valid()
    assert form.errors.as_data()["email"][0].code == "invalid"
    assert "Já existe este e-mail" in form.errors["email"]


def test_register_form_rejeita_senhas_diferentes():
    form = RegisterForm(
        data=register_payload(password2="OutraSenha123!")
    )

    assert not form.is_valid()
    assert (
        form.errors.as_data()["password2"][0].code
        == "password_mismatch"
    )


def test_authentication_form_autentica_credenciais_validas(rf):
    user = UserFactory(
        username="usuario-login",
        password="SenhaLogin123!",
    )
    request = rf.post("/login/")
    form = CustomAuthenticationForm(
        request=request,
        data={
            "username": "usuario-login",
            "password": "SenhaLogin123!",
        },
    )

    assert form.is_valid(), form.errors
    assert form.get_user() == user
    assert form.fields["username"].label == "Usuário"
    assert form.fields["password"].label == "Senha"


def test_authentication_form_rejeita_credenciais_invalidas(rf):
    UserFactory(
        username="usuario-login",
        password="SenhaLogin123!",
    )
    form = CustomAuthenticationForm(
        request=rf.post("/login/"),
        data={
            "username": "usuario-login",
            "password": "senha-incorreta",
        },
    )

    assert not form.is_valid()
    assert NON_FIELD_ERRORS in form.errors
    assert form.get_user() is None


def test_report_form_cria_relatorio_e_resolve_curso(
    course,
    campus,
    questionnaire,
    team,
    team_user,
):
    form = ReportForm(
        data=report_payload(
            course,
            campus,
            questionnaire,
            team,
            team_user,
        )
    )

    assert "assessment" not in form.fields
    assert form.is_valid(), form.errors

    report = form.save()

    assert report.course == course
    assert report.campus == campus
    assert report.questionnaire == questionnaire
    assert report.assigned_team == team
    assert report.assigned_user == team_user


def test_report_form_rejeita_curso_indisponivel_no_campus(
    course,
    questionnaire,
    team,
    team_user,
):
    unrelated_campus = CampusFactory()
    form = ReportForm(
        data=report_payload(
            course,
            unrelated_campus,
            questionnaire,
            team,
            team_user,
        )
    )

    assert not form.is_valid()
    assert "Curso nao disponivel nesse Campus" in (
        form.errors["type_course"]
    )
    assert "campus" in form.errors


def test_report_form_rejeita_relatorio_duplicado(
    report,
    team_user,
):
    form = ReportForm(
        data=report_payload(
            report.course,
            report.campus,
            report.questionnaire,
            report.assigned_team,
            team_user,
            year=str(report.year),
        )
    )

    assert not form.is_valid()
    expected_message = (
        "Relatorio para este curso, campus e ano ja existe."
    )
    assert expected_message in form.errors["type_course"]
    assert expected_message in form.errors["campus"]
    assert expected_message in form.errors["year"]


def test_report_form_edita_relatorio_e_exibe_avaliacao(report):
    form = ReportForm(
        data=report_payload(
            report.course,
            report.campus,
            report.questionnaire,
            report.assigned_team,
            report.assigned_user,
            year=str(report.year),
            assessment="Avaliacao atualizada",
            notes="Notas atualizadas",
        ),
        instance=report,
    )

    assert "assessment" in form.fields
    assert (
        form.fields["type_course"].initial
        == report.course.type_course
    )
    assert form.is_valid(), form.errors

    updated_report = form.save()

    assert updated_report.assessment == "Avaliacao atualizada"
    assert updated_report.notes == "Notas atualizadas"


def test_questionnaire_form_salva_dados_validos(campus):
    form = QuestionnaireForm(
        data={
            "name": "Questionario do formulario",
            "description": "Descricao",
            "campus": campus.id,
            "active": "on",
        }
    )

    assert form.is_valid(), form.errors

    questionnaire = form.save()

    assert questionnaire.campus == campus
    assert questionnaire.active


def test_reference_attachment_form_salva_upload_valido(
    valid_upload,
):
    form = ReferenceAttachmentForm(
        data={
            "name": "Documento catalogado",
            "description": "Descricao",
            "active": "on",
        },
        files={"file": valid_upload},
    )

    assert form.is_valid(), form.errors

    reference = form.save()

    assert reference.file.name.startswith("reference_attachments/")


def test_reference_attachment_form_edita_sem_novo_arquivo(
    reference_attachment,
):
    original_file = reference_attachment.file.name
    form = ReferenceAttachmentForm(
        data={
            "name": "Documento atualizado",
            "description": "Descricao atualizada",
            "active": "on",
        },
        instance=reference_attachment,
    )

    assert not form.fields["file"].required
    assert form.is_valid(), form.errors

    reference = form.save()

    assert reference.file.name == original_file
    assert reference.name == "Documento atualizado"


@pytest.mark.xfail(
    strict=True,
    reason="ReferenceAttachmentForm não valida extensão ou conteúdo.",
)
def test_reference_attachment_form_rejeita_upload_executavel(
    invalid_upload,
):
    form = ReferenceAttachmentForm(
        data={
            "name": "Arquivo invalido",
            "description": "",
            "active": "on",
        },
        files={"file": invalid_upload},
    )

    assert not form.is_valid()
    assert "file" in form.errors


def test_questionnaire_section_form_salva_equipes_autorizadas(
    questionnaire,
    team,
):
    form = QuestionnaireSectionForm(
        data={
            "questionnaire": questionnaire.id,
            "name": "Secao do formulario",
            "teams": [team.id],
            "order": "1",
        }
    )

    assert form.is_valid(), form.errors

    section = form.save()

    assert section.questionnaire == questionnaire
    assert list(section.teams.all()) == [team]


def test_question_form_salva_pergunta_textual(section):
    form = QuestionForm(data=question_payload(section))

    assert form.is_valid(), form.errors

    question = form.save()

    assert question.section == section
    assert question.field_type == "text"
    assert question.required


def test_question_form_e_formset_salvam_alternativas(section):
    question_form = QuestionForm(
        data=question_payload(section, field_type="choice")
    )
    assert question_form.is_valid(), question_form.errors
    question = question_form.save()
    prefix = "options"
    formset = QuestionAnswerOptionFormSet(
        data={
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": "",
            f"{prefix}-0-answer_value": "Conforme",
            f"{prefix}-0-acceptance_criteria": "Criterio atendido",
        },
        instance=question,
        prefix=prefix,
    )

    assert formset.is_valid(), formset.errors

    [option] = formset.save()

    assert option.question == question
    assert option.answer_value == "Conforme"
    assert option.acceptance_criteria == "Criterio atendido"


def test_question_answer_option_formset_exclui_alternativa(
    multiple_choice_question,
):
    option = QuestionAnswerOptionFactory(
        question=multiple_choice_question
    )
    prefix = "options"
    formset = QuestionAnswerOptionFormSet(
        data={
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "1",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": option.id,
            f"{prefix}-0-answer_value": option.answer_value,
            f"{prefix}-0-acceptance_criteria": (
                option.acceptance_criteria
            ),
            f"{prefix}-0-DELETE": "on",
        },
        instance=multiple_choice_question,
        prefix=prefix,
    )

    assert formset.is_valid(), formset.errors

    formset.save()

    assert not QuestionAnswerOption.objects.filter(pk=option.pk).exists()


@pytest.mark.xfail(
    strict=True,
    reason="Pergunta choice não exige ao menos uma alternativa.",
)
def test_pergunta_de_multipla_escolha_sem_alternativas_e_rejeitada(
    section,
):
    question_form = QuestionForm(
        data=question_payload(section, field_type="choice")
    )
    assert question_form.is_valid(), question_form.errors
    question = question_form.save()
    prefix = "options"
    formset = QuestionAnswerOptionFormSet(
        data={
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": "",
            f"{prefix}-0-answer_value": "",
            f"{prefix}-0-acceptance_criteria": "",
        },
        instance=question,
        prefix=prefix,
    )

    assert not formset.is_valid()


def test_formset_com_upload_cria_referencia_e_remove_upload_direto(
    answer,
    valid_upload,
):
    prefix = f"attachments_{answer.id}"
    formset = AttachmentFormSet(
        data={
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "0",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": "",
            f"{prefix}-0-name": "Novo anexo",
            f"{prefix}-0-description": "Documento enviado",
        },
        files={
            f"{prefix}-0-file": valid_upload,
        },
        instance=answer,
        prefix=prefix,
    )

    assert formset.is_valid(), formset.errors

    [attachment] = formset.save()
    attachment.refresh_from_db()
    reference = ReferenceAttachment.objects.get(name="Novo anexo")

    assert attachment.reference_attachment == reference
    assert not attachment.file
    assert reference.description == "Documento enviado"
    assert reference.file.name.startswith("reference_attachments/")


def test_attachment_form_rejeita_novo_anexo_sem_arquivo():
    form = AttachmentForm(
        data={
            "name": "Anexo sem arquivo",
            "description": "Descricao",
        }
    )

    assert not form.is_valid()
    assert "Selecione um arquivo." in form.errors["file"]


@pytest.mark.xfail(
    strict=True,
    reason="AttachmentForm não valida extensão ou conteúdo.",
)
def test_attachment_form_rejeita_upload_executavel(invalid_upload):
    form = AttachmentForm(
        data={
            "name": "Upload executavel",
            "description": "Descricao",
        },
        files={"file": invalid_upload},
    )

    assert not form.is_valid()
    assert "file" in form.errors


@pytest.mark.xfail(
    strict=True,
    reason=(
        "AttachmentForm converte o arquivo existente em anexo catalogado "
        "ao editar apenas os metadados."
    ),
)
def test_attachment_form_edita_sem_substituir_arquivo(
    direct_attachment,
):
    original_file = direct_attachment.file.name
    form = AttachmentForm(
        data={
            "name": "Anexo atualizado",
            "description": "Descricao atualizada",
        },
        instance=direct_attachment,
    )

    assert form.is_valid(), form.errors

    attachment = form.save()

    assert attachment.file.name == original_file
    assert attachment.name == "Anexo atualizado"


def test_attachment_formset_exclui_anexo_existente(
    answer,
    direct_attachment,
):
    direct_attachment.answer = answer
    direct_attachment.save(update_fields=["answer"])
    prefix = f"attachments_{answer.id}"
    formset = AttachmentFormSet(
        data={
            f"{prefix}-TOTAL_FORMS": "1",
            f"{prefix}-INITIAL_FORMS": "1",
            f"{prefix}-MIN_NUM_FORMS": "0",
            f"{prefix}-MAX_NUM_FORMS": "1000",
            f"{prefix}-0-id": direct_attachment.id,
            f"{prefix}-0-name": direct_attachment.name,
            f"{prefix}-0-description": direct_attachment.description,
            f"{prefix}-0-DELETE": "on",
        },
        instance=answer,
        prefix=prefix,
    )

    assert formset.is_valid(), formset.errors

    formset.save()

    assert not direct_attachment.__class__.objects.filter(
        pk=direct_attachment.pk
    ).exists()


def test_report_question_answer_form_salva_resposta_e_argumentacao(
    answer,
):
    form = ReportQuestionAnswerForm(
        data={
            "answer": "Resposta atualizada",
            "free_text": "Nova argumentacao",
        },
        instance=answer,
    )

    assert form.is_valid(), form.errors

    updated_answer = form.save()

    assert updated_answer.answer == "Resposta atualizada"
    assert updated_answer.free_text == "Nova argumentacao"


def test_type_course_form_salva_tipo_e_categoria(course_category):
    form = TypeCourseForm(
        data={
            "type_name_course": "Engenharia",
            "duration": "8",
            "type_categorie": course_category.id,
        }
    )

    assert form.is_valid(), form.errors

    course_type = form.save()

    assert course_type.type_categorie == course_category
    assert course_type.duration == "8"


def test_type_course_form_rejeita_duracao_acima_do_limite(
    course_category,
):
    form = TypeCourseForm(
        data={
            "type_name_course": "Engenharia",
            "duration": "123",
            "type_categorie": course_category.id,
        }
    )

    assert not form.is_valid()
    assert "duration" in form.errors


@pytest.mark.xfail(
    strict=True,
    reason="Validador de type_name_course está nomeado clean_campus_name.",
)
def test_type_course_form_rejeita_nome_reservado_abc(
    course_category,
):
    form = TypeCourseForm(
        data={
            "type_name_course": "ABC",
            "duration": "8",
            "type_categorie": course_category.id,
        }
    )

    assert not form.is_valid()
    assert "type_name_course" in form.errors


def test_team_form_salva_equipe_vinculada_ao_campus(campus):
    form = TeamForm(
        data={
            "team_name": "Equipe do formulario",
            "campus": campus.id,
        }
    )

    assert "users" not in form.fields
    assert form.is_valid(), form.errors

    team = form.save()

    assert team.campus == campus


def test_team_form_rejeita_nome_duplicado_no_mesmo_campus(team):
    form = TeamForm(
        data={
            "team_name": team.team_name,
            "campus": team.campus_id,
        }
    )

    assert not form.is_valid()
    assert (
        "Já existe uma equipe com este nome neste campus"
        in form.errors["team_name"]
    )


@pytest.mark.xfail(
    strict=True,
    reason="clean_team_name consulta o campus antes de ele ser limpo.",
)
def test_team_form_permite_mesmo_nome_em_campus_diferente():
    existing_team = TeamFactory(team_name="Equipe compartilhada")
    other_campus = CampusFactory()
    form = TeamForm(
        data={
            "team_name": existing_team.team_name,
            "campus": other_campus.id,
        }
    )

    assert form.is_valid(), form.errors


def test_team_form_edita_mesma_instancia_sem_acusar_duplicidade(team):
    form = TeamForm(
        data={
            "team_name": team.team_name,
            "campus": team.campus_id,
        },
        instance=team,
    )

    assert form.is_valid(), form.errors

    updated_team = form.save()

    assert updated_team.pk == team.pk
