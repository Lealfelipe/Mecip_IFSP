import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from mecip.forms import AttachmentFormSet
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
    Team,
    Type_Course,
)
from mecip.permissions import ROLE_COORDENADOR, ROLE_EQUIPE


class APIPermissionsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        equipe_group, _ = Group.objects.get_or_create(name=ROLE_EQUIPE)
        coordenador_group, _ = Group.objects.get_or_create(name=ROLE_COORDENADOR)

        cls.equipe = User.objects.create_user('equipe', password='senha123')
        cls.coordenador = User.objects.create_user('coord', password='senha123')
        cls.superadmin = User.objects.create_superuser('admin', 'admin@example.com', 'senha123')
        cls.outro = User.objects.create_user('outro', password='senha123')

        cls.equipe.groups.add(equipe_group)
        cls.coordenador.groups.add(coordenador_group)
        cls.outro.groups.add(equipe_group)

        cls.campus = Campus.objects.create(
            campus_name='Campus Centro',
            city='Cidade',
            street='Rua A',
            neighborhood='Bairro',
            number='100',
            contact_number='11999999999',
            email_campus='campus@example.com',
        )
        categoria = Categorie_Course.objects.create(categorie='Graduacao')
        tipo = Type_Course.objects.create(
            type_name_course='Sistemas',
            duration='8',
            type_categorie=categoria,
        )
        cls.course = Course.objects.create(
            type_course=tipo,
            campus=cls.campus,
            description='Curso de Sistemas',
        )
        cls.questionnaire = Questionnaire.objects.create(
            name='Questionario MEC',
            description='Questionario base',
            campus=cls.campus,
        )
        section = QuestionnaireSection.objects.create(
            questionnaire=cls.questionnaire,
            name='Secao 1',
            order=1,
        )
        cls.question = Question.objects.create(
            section=section,
            text='Pergunta 1',
            field_type='text',
            required=True,
            order=1,
        )
        cls.team = Team.objects.create(team_name='Equipe 1', campus=cls.campus)
        cls.team.users.add(cls.equipe)
        cls.report = Report.objects.create(
            course=cls.course,
            campus=cls.campus,
            year=2026,
            questionnaire=cls.questionnaire,
            assessment='Avaliacao',
            assigned_team=cls.team,
            assigned_user=cls.equipe,
        )

    def test_anexo_catalogado_armazena_apenas_a_referencia(self):
        reference = ReferenceAttachment.objects.create(
            name='Documento catalogado',
            file='reference_attachments/documento.pdf',
        )
        answer = ReportQuestionAnswer.objects.create(
            report=self.report,
            question=self.question,
            answer='Resposta',
        )

        attachment = Attachments.objects.create(
            answer=answer,
            reference_attachment=reference,
            name=reference.name,
        )

        self.assertFalse(attachment.file)
        self.assertEqual(attachment.reference_attachment, reference)
        self.assertEqual(
            attachment.attachment_file.name,
            reference.file.name,
        )

    def test_upload_direto_nao_exige_anexo_catalogado(self):
        answer = ReportQuestionAnswer.objects.create(
            report=self.report,
            question=self.question,
            answer='Resposta',
        )
        attachment = Attachments.objects.create(
            answer=answer,
            name='Upload direto',
            file='answer_attachments/upload.pdf',
        )

        self.assertIsNone(attachment.reference_attachment)
        self.assertEqual(
            attachment.attachment_file.name,
            'answer_attachments/upload.pdf',
        )

    def test_upload_do_formset_e_inserido_na_base_de_referencias(self):
        answer = ReportQuestionAnswer.objects.create(
            report=self.report,
            question=self.question,
            answer='Resposta',
        )
        prefix = f'attachments_{answer.id}'

        with tempfile.TemporaryDirectory() as media_root:
            with self.settings(MEDIA_ROOT=media_root):
                formset = AttachmentFormSet(
                    data={
                        f'{prefix}-TOTAL_FORMS': '1',
                        f'{prefix}-INITIAL_FORMS': '0',
                        f'{prefix}-MIN_NUM_FORMS': '0',
                        f'{prefix}-MAX_NUM_FORMS': '1000',
                        f'{prefix}-0-id': '',
                        f'{prefix}-0-name': 'Novo anexo',
                        f'{prefix}-0-description': 'Documento enviado',
                    },
                    files={
                        f'{prefix}-0-file': SimpleUploadedFile(
                            'documento.txt',
                            b'conteudo',
                        ),
                    },
                    instance=answer,
                    prefix=prefix,
                )

                self.assertTrue(formset.is_valid(), formset.errors)
                [attachment] = formset.save()
                attachment.refresh_from_db()

                reference = ReferenceAttachment.objects.get(
                    name='Novo anexo',
                )
                self.assertEqual(
                    attachment.reference_attachment,
                    reference,
                )
                self.assertFalse(attachment.file)
                self.assertEqual(
                    reference.description,
                    'Documento enviado',
                )
                self.assertTrue(
                    reference.file.name.startswith(
                        'reference_attachments/',
                    )
                )

    def test_permite_relatorios_do_mesmo_curso_em_anos_diferentes(self):
        report = Report.objects.create(
            course=self.course,
            campus=self.campus,
            year=2027,
            assessment='Avaliacao de 2027',
        )

        self.assertEqual(report.year, 2027)

    def test_impede_relatorios_duplicados_no_mesmo_ano(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Report.objects.create(
                    course=self.course,
                    campus=self.campus,
                    year=2026,
                    assessment='Relatorio duplicado',
                )

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

    def test_login_com_credenciais_validas(self):
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'equipe',
            'password': 'senha123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data)

    def test_login_com_credenciais_invalidas(self):
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'equipe',
            'password': 'errada',
        })
        self.assertEqual(response.status_code, 400)

    def test_acesso_sem_token_retorna_401(self):
        response = self.client.get('/api/v1/campus/')
        self.assertEqual(response.status_code, 401)

    def test_equipe_pode_listar_mas_nao_criar_campus(self):
        self.authenticate(self.equipe)
        self.assertEqual(self.client.get('/api/v1/campus/').status_code, 200)
        response = self.client.post('/api/v1/campus/', {
            'campus_name': 'Novo',
            'city': 'Cidade',
            'street': 'Rua',
            'neighborhood': 'Bairro',
            'number': '10',
            'contact_number': '1100000000',
            'email_campus': 'novo@example.com',
        })
        self.assertEqual(response.status_code, 403)

    def test_coordenador_pode_criar_e_atualizar_campus(self):
        self.authenticate(self.coordenador)
        response = self.client.post('/api/v1/campus/', {
            'campus_name': 'Campus Norte',
            'city': 'Cidade',
            'street': 'Rua',
            'neighborhood': 'Bairro',
            'number': '10',
            'contact_number': '1100000000',
            'email_campus': 'norte@example.com',
        })
        self.assertEqual(response.status_code, 201)
        response = self.client.patch(f"/api/v1/campus/{response.data['id']}/", {'city': 'Outra'})
        self.assertEqual(response.status_code, 200)

    def test_superadmin_pode_criar_e_atualizar_questionario(self):
        self.authenticate(self.superadmin)
        response = self.client.post('/api/v1/questionarios/', {
            'name': 'Novo Questionario',
            'description': 'Descricao',
            'campus': self.campus.id,
            'active': True,
        })
        self.assertEqual(response.status_code, 201)
        response = self.client.patch(f"/api/v1/questionarios/{response.data['id']}/", {'active': False})
        self.assertEqual(response.status_code, 200)

    def test_equipe_responde_questionario_atribuido(self):
        self.authenticate(self.equipe)
        response = self.client.post(f'/api/v1/questionarios/{self.questionnaire.id}/responder/', {
            'report': self.report.id,
            'question': self.question.id,
            'answer': 'Resposta da equipe',
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ReportQuestionAnswer.objects.filter(
                report=self.report,
                question=self.question,
                answer='Resposta da equipe',
            ).exists()
        )

    def test_equipe_nao_responde_questionario_de_outro_usuario(self):
        self.authenticate(self.outro)
        response = self.client.post(f'/api/v1/questionarios/{self.questionnaire.id}/responder/', {
            'report': self.report.id,
            'question': self.question.id,
            'answer': 'Resposta indevida',
        })
        self.assertEqual(response.status_code, 404)

    def test_coordenador_importa_questionario_com_secao_questao_e_alternativas(self):
        self.authenticate(self.coordenador)
        response = self.client.post('/api/v1/questionarios/importar/', {
            'questionario': 'Instrumento de Avaliacao',
            'dimensao': 'DIMENSAO 1',
            'indicador': 'Indicador 1.1',
            'questao': 'politicas institucionais no ambito do curso',
            'tipo': 'Multipla escolha',
            'obrigatoria': 'Sim',
            'condicao_especial': None,
            'conceitos': [
                {
                    'conceito': '1',
                    'criterio_de_aceite': 'Criterio 1',
                },
                {
                    'conceito': '2',
                    'criterio_de_aceite': 'Criterio 2',
                },
            ],
        }, format='json')

        self.assertEqual(response.status_code, 201)
        question = Question.objects.get(pk=response.data['question_id'])
        self.assertEqual(question.indicator, 'Indicador 1.1')
        self.assertEqual(question.field_type, 'choice')
        self.assertTrue(question.required)
        self.assertEqual(question.answer_options.count(), 2)
        self.assertTrue(
            QuestionAnswerOption.objects.filter(
                question=question,
                answer_value='1',
                acceptance_criteria='Criterio 1',
            ).exists()
        )

    def test_equipe_nao_importa_questionario(self):
        self.authenticate(self.equipe)
        response = self.client.post('/api/v1/questionarios/importar/', {
            'questionario': 'Bloqueado',
            'dimensao': 'DIMENSAO',
            'questao': 'Pergunta',
        }, format='json')

        self.assertEqual(response.status_code, 403)
