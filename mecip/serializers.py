from django.contrib.auth import authenticate
from rest_framework import serializers

from mecip.models import (
    Campus,
    Course,
    Question,
    QuestionAnswerOption,
    Questionnaire,
    QuestionnaireSection,
    Report,
)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if user is None:
            raise serializers.ValidationError('Credenciais invalidas.')
        attrs['user'] = user
        return attrs


class CampusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = (
            'id',
            'campus_name',
            'city',
            'street',
            'neighborhood',
            'number',
            'contact_number',
            'email_campus',
            'created_date',
        )
        read_only_fields = ('id', 'created_date')


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('id', 'type_course', 'description', 'campus', 'created_date')
        read_only_fields = ('id', 'created_date')


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = (
            'id',
            'course',
            'campus',
            'year',
            'questionnaire',
            'assessment',
            'assigned_team',
            'assigned_user',
            'due_date',
            'notes',
            'status',
            'created_date',
        )
        read_only_fields = ('id', 'created_date')


class QuestionnaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questionnaire
        fields = (
            'id',
            'name',
            'description',
            'campus',
            'active',
            'argumentation_character_limit',
            'created_date',
        )
        read_only_fields = ('id', 'created_date')


class ConceptImportSerializer(serializers.Serializer):
    conceito = serializers.CharField()
    criterio_de_aceite = serializers.CharField(allow_blank=True, required=False)


class QuestionnaireImportSerializer(serializers.Serializer):
    questionario = serializers.CharField()
    dimensao = serializers.CharField()
    indicador = serializers.CharField(allow_blank=True, required=False)
    questao = serializers.CharField()
    tipo = serializers.CharField(default='Multipla escolha')
    obrigatoria = serializers.CharField(default='Sim')
    condicao_especial = serializers.CharField(allow_blank=True, allow_null=True, required=False)
    conceitos = ConceptImportSerializer(many=True, required=False)

    def validate(self, attrs):
        field_type = self._map_question_type(attrs.get('tipo'))
        if field_type == 'choice' and not attrs.get('conceitos'):
            raise serializers.ValidationError({
                'conceitos': (
                    'Perguntas de múltipla escolha exigem ao menos uma alternativa.'
                ),
            })
        return attrs

    def create(self, validated_data):
        questionnaire = self._get_or_create_questionnaire(validated_data['questionario'])
        section = self._get_or_create_section(questionnaire, validated_data['dimensao'])
        question = self._get_or_create_question(section, validated_data)
        option_ids = self._sync_options(question, validated_data.get('conceitos', []))

        return {
            'questionnaire_id': questionnaire.id,
            'section_id': section.id,
            'question_id': question.id,
            'option_ids': option_ids,
        }

    def _get_or_create_questionnaire(self, name):
        questionnaire = Questionnaire.objects.filter(name=name).first()
        if questionnaire:
            return questionnaire
        return Questionnaire.objects.create(name=name)

    def _get_or_create_section(self, questionnaire, name):
        section = QuestionnaireSection.objects.filter(
            questionnaire=questionnaire,
            name=name,
        ).first()
        if section:
            return section
        next_order = questionnaire.sections.count() + 1
        return QuestionnaireSection.objects.create(
            questionnaire=questionnaire,
            name=name,
            order=next_order,
        )

    def _get_or_create_question(self, section, data):
        question = Question.objects.filter(
            section=section,
            indicator=data.get('indicador', ''),
            text=data['questao'],
        ).first()
        if question is None:
            question = Question(section=section, text=data['questao'])

        question.indicator = data.get('indicador', '')
        question.special_condition = data.get('condicao_especial') or ''
        question.field_type = self._map_question_type(data.get('tipo'))
        question.required = self._map_required(data.get('obrigatoria'))
        if not question.order:
            question.order = section.questions.count() + 1
        question.save()
        return question

    def _sync_options(self, question, concepts):
        option_ids = []
        for concept in concepts:
            option = QuestionAnswerOption.objects.filter(
                question=question,
                answer_value=concept['conceito'],
            ).first()
            if option is None:
                option = QuestionAnswerOption(question=question, answer_value=concept['conceito'])
            option.acceptance_criteria = concept.get('criterio_de_aceite', '')
            option.save()
            option_ids.append(option.id)
        return option_ids

    def _map_question_type(self, value):
        normalized = (value or '').strip().lower()
        if normalized in ('múltipla escolha', 'multipla escolha', 'choice'):
            return 'choice'
        if normalized in ('texto longo', 'textarea'):
            return 'textarea'
        if normalized in ('sim/não', 'sim/nao', 'boolean'):
            return 'boolean'
        return 'text'

    def _map_required(self, value):
        return (value or '').strip().lower() in ('sim', 'true', '1', 'yes')


class AnswerQuestionnaireSerializer(serializers.Serializer):
    report = serializers.IntegerField(required=False)
    question = serializers.IntegerField()
    answer = serializers.CharField(required=False, allow_blank=True)
    free_text = serializers.CharField(required=False, allow_blank=True)
    selected_answer_option = serializers.IntegerField(required=False, allow_null=True)
