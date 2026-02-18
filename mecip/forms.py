from typing import Any
from mecip.models import Campus, Curso, Relatorio, Type_Course
from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm


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
            msg = ValidationError('Nome não pode ser igual ao sobrenome')
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
        model = Curso
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

        if Curso.objects.filter(type_course=type_course, campus=campus).exclude(pk=self.instance.pk).exists():
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

class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuário'
        self.fields['password'].label = 'Senha'


class ReportForm(forms.ModelForm):

    class Meta:
        model = Relatorio
        fields = (
            'course', 'campus', 'assessment'
        )
        labels = {
            'course': 'Nome do Curso',
            'campus': 'Campus Pertencente',
            'assessment': 'Avaliação',
        }

    assessment = forms.CharField(
        required=False,
        widget= forms.Textarea,
        label= 'Avaliação'
    )
    
    # ocultar o campo assessment
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  
            self.fields.pop('assessment')

    def clean_unique_together(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        campus = cleaned_data.get('campus')

        if Relatorio.objects.filter(course=course, campus=campus).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Relatório para este curso e campus já existe.')

        return cleaned_data
    

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
    
    def clean_campus_name(self): ###funcao para validação de dados
        type_name_course = self.cleaned_data.get('type_name_course')

        if type_name_course == 'ABC':
            self.add_error(
                'type_name_course',
                ValidationError(
                    'Nome inválido',
                    code= 'invalid'
                )
            )

        return type_name_course
