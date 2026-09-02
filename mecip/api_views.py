from django.shortcuts import get_object_or_404
from rest_framework import filters, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mecip.api_permissions import RoleBasedModelPermission
from mecip.models import (
    Campus,
    Course,
    Question,
    QuestionAnswerOption,
    Questionnaire,
    Report,
    ReportQuestionAnswer,
)
from mecip.permissions import can_answer_report, can_manage_records, can_view_all_records
from mecip.serializers import (
    AnswerQuestionnaireSerializer,
    CampusSerializer,
    CourseSerializer,
    LoginSerializer,
    QuestionnaireImportSerializer,
    QuestionnaireSerializer,
    ReportSerializer,
)
from mecip.validators import normalize_text_line_endings


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token, _ = Token.objects.get_or_create(user=serializer.validated_data['user'])
        return Response({'token': token.key})


class CampusViewSet(viewsets.ModelViewSet):
    serializer_class = CampusSerializer
    permission_classes = [IsAuthenticated, RoleBasedModelPermission]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    queryset = Campus.objects.order_by('campus_name')
    filter_backends = [filters.SearchFilter]
    search_fields = ['campus_name', 'city']


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, RoleBasedModelPermission]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    queryset = Course.objects.select_related('type_course', 'campus').order_by(
        'type_course__type_name_course'
    )
    filter_backends = [filters.SearchFilter]
    search_fields = ['type_course__type_name_course', 'campus__campus_name']


class ReportViewSet(viewsets.ModelViewSet):
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated, RoleBasedModelPermission]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    filter_backends = [filters.SearchFilter]
    search_fields = ['course__type_course__type_name_course', 'campus__campus_name', 'status']

    def get_queryset(self):
        queryset = Report.objects.select_related(
            'course',
            'campus',
            'questionnaire',
            'assigned_team',
            'assigned_user',
        )
        if can_view_all_records(self.request.user):
            return queryset.order_by('-id')
        if self.action == 'list':
            return queryset.filter(
                assigned_team__users=self.request.user,
            ).distinct().order_by('-id')
        return queryset.order_by('-id')


class QuestionnaireViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionnaireSerializer
    permission_classes = [IsAuthenticated, RoleBasedModelPermission]
    http_method_names = ['get', 'post', 'put', 'patch', 'head', 'options']
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description', 'campus__campus_name']

    def get_queryset(self):
        queryset = Questionnaire.objects.select_related('campus').order_by('name')
        if can_manage_records(self.request.user):
            return queryset
        if self.action == 'list':
            return queryset.filter(
                reports__assigned_team__users=self.request.user,
            ).distinct()
        return queryset

    @action(detail=False, methods=['post'], url_path='importar')
    def importar(self, request):
        many = isinstance(request.data, list)
        serializer = QuestionnaireImportSerializer(data=request.data, many=many)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def responder(self, request, pk=None):
        questionnaire = self.get_object()

        serializer = AnswerQuestionnaireSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report_id = serializer.validated_data.get('report')
        if report_id:
            report = get_object_or_404(
                Report,
                pk=report_id,
                questionnaire=questionnaire,
            )
        else:
            reports = Report.objects.filter(
                questionnaire=questionnaire,
            )
            if not can_manage_records(request.user):
                reports = reports.filter(
                    assigned_team__users=request.user,
                )
            report = reports.first()

        if report is None:
            return Response(
                {'detail': 'Questionario nao atribuido ao usuario.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not can_answer_report(request.user, report):
            return Response(
                {'detail': 'Sem permissao para responder este questionario.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        question = get_object_or_404(
            Question,
            pk=serializer.validated_data['question'],
            section__questionnaire=questionnaire,
        )
        free_text = normalize_text_line_endings(
            serializer.validated_data.get('free_text', '')
        )

        if len(free_text) > questionnaire.argumentation_character_limit:
            return Response(
                {
                    'free_text': [
                        (
                            'A argumentação não pode ultrapassar '
                            f'{questionnaire.argumentation_character_limit} '
                            'caracteres.'
                        ),
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer, _ = ReportQuestionAnswer.objects.get_or_create(report=report, question=question)
        answer.answer = serializer.validated_data.get('answer', '')
        answer.free_text = free_text

        option_id = serializer.validated_data.get('selected_answer_option')
        if option_id:
            option = get_object_or_404(QuestionAnswerOption, pk=option_id, question=question)
            answer.selected_answer_option = option
            answer.answer = option.answer_value

        answer.save()
        return Response({'detail': 'Resposta registrada com sucesso.'})
