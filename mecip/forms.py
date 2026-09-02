from typing import Any
from mecip.models import Campus, Course, Report, Type_Course, Team, Questionnaire, QuestionnaireSection, Question, ReportQuestionAnswer, Attachments, QuestionAnswerOption, ReferenceAttachment
from mecip.validators import validate_pdf_upload
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from mecip.permissions import ROLE_EQUIPE, assign_role


class CampusForm(forms.ModelForm):


    class Meta:
        model = Campus
        fields = (
            'campus_name', 'city', 'street', 'neighborhood', 
            'number', 'email_campus', 'contact_number',
        )
        labels = {
            'campus_name': 'Nome do Campus',
            'city': 'Cidade',
            'street': 'Rua',
            'neighborhood': 'Bairro',
            'number': 'Número',
            'email_campus': 'Email do Campus',
            'contact_number': 'Número de Contato',
        }

    def clean(self): ##funcao  para receber os dados do formularios
        cleaned_data = self.cleaned_data
        campus_name = cleaned_data.get('campus_name')
        city = cleaned_data.get('city')

        if campus_name == city:
            msg = ValidationError('Nome do Campus não pode ser igual ao nome da Cidade')
            self.add_error(
                'campus_name',
                msg
            )
            self.add_error(
                'city',
                msg
            )

        return super().clean()
    def clean_campus_name(self): ###funcao para validação de dados
        campus_name = self.cleaned_data.get('campus_name')

        if campus_name == 'ABC':
            self.add_error(
                'campus_name',
                ValidationError(
                    'Nome inválido',
                    code= 'invalid'
                )
            )

        return campus_name
    
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = (
            'type_course', 'description', 'campus'
        )
        labels = {
            'type_course': 'Nome do Curso',
            'description': 'Descrição do Curso',
            'campus': 'Campus Pertencente'
        }

    def clean(self): ##funcao  para receber os dados do formularios
        cleaned_data = self.cleaned_data
        type_course = cleaned_data.get('type_course')
        campus = cleaned_data.get('campus')

        if type_course == campus:
            msg = ValidationError('Curso não pode ter o mesmo nome do Campus')
            self.add_error(
                'type_course',
                msg
            )

        return super().clean()
    def clean_campus_name(self): ###funcao para validação de dados
        type_course = self.cleaned_data.get('type_course')

        if type_course == 'ABC':
            self.add_error(
                'type_course',
                ValidationError(
                    'Nome inválido',
                    code= 'invalid'
                )
            )

        return type_course
    
    def clean_unique_together(self):
        cleaned_data = super().clean()
        type_course = cleaned_data.get('type_course')
        campus = cleaned_data.get('campus')

        if Course.objects.filter(type_course=type_course, campus=campus).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Curso já cadastrado para esse Campus existe.')

        return cleaned_data


class RegisterForm(UserCreationForm):
    
    first_name = forms.CharField(
        required=True,
        min_length=3,
        label= 'Nome'
    )
    last_name = forms.CharField(
        required=True,
        min_length=3,
        label= 'Sobrenome'
    )
    email = forms.EmailField(
        required=True,
        label= 'Email'
    )
    password1 = forms.CharField(
        label='Senha',  
        strip=False,
        widget=forms.PasswordInput,
        help_text='Sua senha não pode ser muito semelhante ao seu outro dados pessoais.',
    )
    password2 = forms.CharField(
        label='Confirme sua senha',  
        strip=False,
        widget=forms.PasswordInput,
        help_text='Digite a mesma senha para verificação.',
    )

    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email',
            'username', 'password1', 'password2',
        )
        labels = {
            'username': 'Usuário',
        }
            
            

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            self.add_error(
                'email',
                ValidationError('Já existe este e-mail', code='invalid')
            )

        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            assign_role(user, ROLE_EQUIPE)
        return user

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuário'
        self.fields['password'].label = 'Senha'


class ReportForm(forms.ModelForm):

    type_course = forms.ModelChoiceField(
        queryset=Type_Course.objects.all(),
        label='Nome do Curso'
    )

    class Meta:
        model = Report
        fields = (
            'type_course', 'campus', 'year', 'questionnaire', 'assessment', 'assigned_team', 'assigned_user', 'due_date', 'notes', 'status'
        )
        labels = {
            'campus': 'Campus Pertencente',
            'year': 'Ano',
            'questionnaire': 'Questionário',
            'assessment': 'Avaliação',
            'assigned_team': 'Equipe Atribuída',
            'assigned_user': 'Usuário Atribuído',
            'due_date': 'Prazo',
            'notes': 'Observações',
            'status': 'Status',
        }

    questionnaire = forms.ModelChoiceField(
        queryset=Questionnaire.objects.filter(active=True),
        required=False,
        label='Questionário'
    )

    assessment = forms.CharField(
        required=False,
        widget= forms.Textarea,
        label= 'Avaliação'
    )
    
    # ocultar o campo assessment
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['type_course'].initial = self.instance.course.type_course
        if not self.instance.pk:
            self.fields.pop('assessment')

    def clean(self):
        cleaned_data = super().clean()
        type_course = cleaned_data.get('type_course')
        campus = cleaned_data.get('campus')
        year = cleaned_data.get('year')

        if type_course and campus and year:
            course = Course.objects.filter(type_course=type_course, campus=campus).first()
            if not course:
                msg = ValidationError('Curso nao disponivel nesse Campus')
                self.add_error('type_course', msg)
                self.add_error('campus', msg)
                return cleaned_data
            if Report.objects.filter(
                course=course,
                campus=campus,
                year=year,
            ).exclude(pk=self.instance.pk).exists():
                msg = ValidationError('Relatorio para este curso, campus e ano ja existe.')
                self.add_error('type_course', msg)
                self.add_error('campus', msg)
                self.add_error('year', msg)

        return cleaned_data


    def save(self, commit=True):
        report = super().save(commit=False)
        type_course = self.cleaned_data.get('type_course')
        campus = self.cleaned_data.get('campus')

        if type_course and campus:
            report.course = Course.objects.filter(type_course=type_course, campus=campus).first()

        if commit:
            report.save()
            self.save_m2m()

        return report


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = (
            'name',
            'description',
            'campus',
            'argumentation_character_limit',
            'active',
        )
        labels = {
            'name': 'Nome do Questionário',
            'description': 'Descrição',
            'campus': 'Campus',
            'argumentation_character_limit': (
                'Limite de caracteres para "Explore sua argumentação"'
            ),
            'active': 'Ativo',
        }
        help_texts = {
            'argumentation_character_limit': (
                'Informe um valor entre 1 e 100.000 caracteres. '
                'Respostas existentes não serão cortadas automaticamente.'
            ),
        }
        widgets = {
            'argumentation_character_limit': forms.NumberInput(
                attrs={'min': 1, 'max': 100000}
            ),
        }


class PdfUploadValidationMixin:
    def clean_file(self):
        file = self.cleaned_data.get("file")
        uploaded_file = self.files.get(self.add_prefix("file"))

        if uploaded_file:
            validate_pdf_upload(uploaded_file)

        return file


class ReferenceAttachmentForm(
    PdfUploadValidationMixin,
    forms.ModelForm,
):
    class Meta:
        model = ReferenceAttachment
        fields = ('name', 'file', 'description', 'active')
        labels = {
            'name': 'Nome do anexo',
            'file': 'Arquivo',
            'description': 'Descricao',
            'active': 'Ativo',
        }
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.pdf'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['file'].required = False


class QuestionnaireSectionForm(forms.ModelForm):
    class Meta:
        model = QuestionnaireSection
        fields = ('questionnaire', 'name', 'teams', 'order')
        labels = {
            'questionnaire': 'Questionário',
            'name': 'Nome da seção',
            'teams': 'Equipes autorizadas',
            'order': 'Ordem',
        }
        widgets = {
            'teams': forms.CheckboxSelectMultiple,
        }


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('section', 'indicator', 'special_condition', 'text', 'field_type', 'required', 'order')
        labels = {
            'section': 'Seção',
            'indicator': 'Indicador',
            'special_condition': 'Condição especial',
            'text': 'Pergunta',
            'field_type': 'Tipo',
            'required': 'Obrigatória',
            'order': 'Ordem',
        }


class QuestionAnswerOptionForm(forms.ModelForm):
    class Meta:
        model = QuestionAnswerOption
        fields = ('answer_value', 'acceptance_criteria')
        labels = {
            'answer_value': 'Alternativa',
            'acceptance_criteria': 'Critério de aceitação',
        }
        widgets = {
            'acceptance_criteria': forms.Textarea(attrs={'rows': 2}),
        }


class BaseQuestionAnswerOptionFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()

        if any(self.errors) or self.instance.field_type != 'choice':
            return

        active_forms = [
            form
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        ]
        if not active_forms:
            raise ValidationError(
                'Perguntas de múltipla escolha exigem ao menos uma alternativa.'
            )


QuestionAnswerOptionFormSet = forms.inlineformset_factory(
    Question,
    QuestionAnswerOption,
    form=QuestionAnswerOptionForm,
    formset=BaseQuestionAnswerOptionFormSet,
    extra=1,
    can_delete=True,
)


class AttachmentForm(
    PdfUploadValidationMixin,
    forms.ModelForm,
):
    class Meta:
        model = Attachments
        fields = ('name', 'file', 'description')
        labels = {
            'name': 'Nome do anexo',
            'file': 'Arquivo',
            'description': 'Descrição',
        }
        widgets = {
            'file': forms.FileInput(attrs={'accept': '.pdf'}),
            'description': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not self.has_changed():
            return cleaned_data

        file = cleaned_data.get('file')

        if not file and not self.instance.pk:
            self.add_error('file', ValidationError('Selecione um arquivo.'))

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        uploaded_file = self.files.get(self.add_prefix('file'))

        if uploaded_file and commit:
            reference_attachment = ReferenceAttachment.objects.create(
                name=instance.name,
                file=uploaded_file,
                description=instance.description,
            )
            instance.reference_attachment = reference_attachment
            instance.file = ''

        if commit:
            instance.save()

        return instance


AttachmentFormSet = forms.inlineformset_factory(
    ReportQuestionAnswer,
    Attachments,
    form=AttachmentForm,
    extra=1,
    can_delete=True,
)


class ReportQuestionAnswerForm(forms.ModelForm):
    class Meta:
        model = ReportQuestionAnswer
        fields = ('answer', 'free_text')
        labels = {
            'answer': 'Resposta',
            'free_text': 'Explore sua argumentação',
        }
        widgets = {
            'answer': forms.Textarea(attrs={'rows': 3}),
            'free_text': forms.Textarea(attrs={'rows': 3}),
        }


class TypeCourseForm(forms.ModelForm):
    class Meta:
        model = Type_Course
        fields = (
            'type_name_course', 'duration', 'type_categorie'
        )
        labels = {
            'type_name_course': 'Nome do Curso',
            'duration': 'Duração em Semestre',
            'type_categorie': 'Nivel do Curso',
        }

    def clean(self): ##funcao  para receber os dados do formularios
        cleaned_data = self.cleaned_data
        type_name_course = cleaned_data.get('type_name_course')
        type_categorie = cleaned_data.get('type_categorie')

        if type_name_course == type_categorie:
            msg = ValidationError('Nome do curso não pode ter o mesmo nome do Nível')
            self.add_error(
                'type_name_course',
                msg
            )

        return super().clean()
    def clean_type_name_course(self):
        type_name_course = self.cleaned_data.get('type_name_course')

        normalized_name = ''.join(type_name_course.split()).casefold()
        if normalized_name == 'abc':
            raise ValidationError(
                'Nome inválido',
                code='invalid',
            )

        return type_name_course


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = (
            'team_name', 'campus'
        )
        labels = {
            'team_name': 'Nome da Equipe',
            'campus': 'Campus Pertencente',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Caso usem campos extras em outro form, mantenha sem erro
        if 'users' in self.fields:
            self.fields['users'].disabled = True
            self.fields['users'].help_text = 'Use a opção "Gerenciar Usuários" para gerenciar membros da equipe'

    def clean(self):
        cleaned_data = self.cleaned_data
        team_name = cleaned_data.get('team_name')
        campus = cleaned_data.get('campus')

        if team_name == campus:
            msg = ValidationError('Nome da equipe não pode ter o mesmo nome do Campus')
            self.add_error(
                'team_name',
                msg
            )
        return super().clean()
