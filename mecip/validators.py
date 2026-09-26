from pathlib import Path
import unicodedata

from django.core.exceptions import ValidationError


MAXIMUM_PDF_SIZE = 10_000_000


def normalize_text_line_endings(value):
    return (value or '').replace('\r\n', '\n').replace('\r', '\n')


def normalize_team_name(value):
    decomposed_value = unicodedata.normalize("NFKD", value or "")
    return "".join(
        character
        for character in decomposed_value
        if (
            not unicodedata.combining(character)
            and not character.isspace()
        )
    ).casefold()


def normalize_course_category_name(value):
    decomposed = unicodedata.normalize('NFKD', value or '')
    without_accents = ''.join(
        character
        for character in decomposed
        if not unicodedata.combining(character)
    )
    return ' '.join(without_accents.split()).casefold()


def validate_pdf_upload(uploaded_file):
    if Path(uploaded_file.name).suffix != ".pdf":
        raise ValidationError(
            "Envie um arquivo com extensão final .pdf em letras minúsculas.",
            code="invalid_pdf_extension",
        )

    if uploaded_file.size > MAXIMUM_PDF_SIZE:
        raise ValidationError(
            "O arquivo deve ter no máximo 10.000.000 bytes.",
            code="pdf_too_large",
        )
