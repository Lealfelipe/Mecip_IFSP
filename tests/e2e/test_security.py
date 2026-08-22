import re

import pytest
from playwright.sync_api import expect


pytestmark = [
    pytest.mark.e2e,
    pytest.mark.slow,
    pytest.mark.django_db(transaction=True),
]


@pytest.fixture
def questionnaire_delete_page(
    request,
    questionnaire,
    section,
    text_question,
):
    coordinator_page = request.getfixturevalue("coordinator_page")
    e2e_base_url = request.getfixturevalue("e2e_base_url")
    browser_diagnostics = request.getfixturevalue(
        "browser_diagnostics"
    )
    return (
        coordinator_page,
        e2e_base_url,
        questionnaire,
        section,
        text_question,
        browser_diagnostics,
    )


def test_modal_de_exclusao_define_formulario_e_endpoint_corretos(
    questionnaire_delete_page,
):
    (
        coordinator_page,
        e2e_base_url,
        questionnaire,
        section,
        text_question,
        browser_diagnostics,
    ) = questionnaire_delete_page

    response = coordinator_page.goto(
        (
            f"{e2e_base_url}/questionario/"
            f"{questionnaire.id}/editar"
        ),
        wait_until="domcontentloaded",
    )
    assert response is not None
    assert response.ok

    modal = coordinator_page.locator("#questionnaire-delete-modal")
    delete_form = modal.locator("#questionnaire-delete-form")

    coordinator_page.locator(
        '[data-delete-kind="section"]'
    ).click()
    expect(modal).to_be_visible()
    expect(delete_form).to_have_attribute(
        "action",
        re.compile(
            rf"/questionario/{questionnaire.id}/"
            rf"secao/{section.id}/deletar$"
        ),
    )

    coordinator_page.locator(
        "#cancel-questionnaire-delete"
    ).click()
    expect(modal).to_be_hidden()

    coordinator_page.locator(
        '[data-delete-kind="question"]'
    ).click()
    expect(modal).to_be_visible()
    expect(delete_form).to_have_attribute(
        "action",
        re.compile(
            rf"/questionario/{questionnaire.id}/"
            rf"questao/{text_question.id}/deletar$"
        ),
    )

    assert browser_diagnostics.javascript_errors == []
