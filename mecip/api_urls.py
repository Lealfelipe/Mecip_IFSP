from django.urls import include, path
from rest_framework.routers import DefaultRouter

from mecip.api_views import (
    CampusViewSet,
    CourseViewSet,
    LoginAPIView,
    QuestionnaireViewSet,
    ReportViewSet,
)

router = DefaultRouter()
router.register('campus', CampusViewSet, basename='api-campus')
router.register('cursos', CourseViewSet, basename='api-cursos')
router.register('relatorios', ReportViewSet, basename='api-relatorios')
router.register('questionarios', QuestionnaireViewSet, basename='api-questionarios')

urlpatterns = [
    path('auth/login/', LoginAPIView.as_view(), name='api-login'),
    path('', include(router.urls)),
]
