from django.contrib import admin
from django.urls import path
from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework import routers

from user.views import (
    TrainerViewSet, LogoutView, MyProfileViewSet, UpgradeUserView, QuestionFeedView,
    AnswerfeedView, ChangePasswordView, TrainerEffectivenessView,
    PasswordResetConfirmView, PasswordResetView
)

from businessGroup.views import (
    BusinessGroupViewSet,  LevelView, ModuleView, DetailView, TraineeListView, UserDetailsViewSet
)
from assessment.views import (
    AssessmentView, BatchAssessmentView, AnswerView, ScoreViewSet, MultipartdataView, CpcViewSet
)
from material.views import MaterialView, FieldViewSet
from user.views import (
    MyTokenObtainPairView, DashboardView
)
from attendance.views import (
    AttendanceCalculateViewSet, AttendanceReport
)
from notifications.views import (
    EmailNotificationsView, EmailTemplateView
)

router = routers.DefaultRouter()
router.register(r'me', MyProfileViewSet)
router.register(r'users', TrainerViewSet)
router.register(r'material', MaterialView)
router.register(r'businessGroup', BusinessGroupViewSet)
router.register(r'level', LevelView)
router.register(r'module', ModuleView)
router.register(r'batch', DetailView)
router.register(r'field', FieldViewSet)
router.register(r'assessment', AssessmentView)
router.register(r'answer', AnswerView)
router.register(r'score', ScoreViewSet)
router.register(r'attendscore', AttendanceCalculateViewSet)
router.register(r'bassessment', BatchAssessmentView)
router.register(r'user_details', UserDetailsViewSet)
router.register(r'questionfeed', QuestionFeedView)
router.register(r'answerfeed', AnswerfeedView)
router.register(r'change_pw', ChangePasswordView)
router.register(r'feed', TrainerEffectivenessView)
router.register(r'user_edit', UpgradeUserView)
router.register(r'files', MultipartdataView)
router.register(r'notification', EmailNotificationsView)
router.register(r'template', EmailTemplateView)
router.register(r'reports', AttendanceReport)
router.register(r'cpc_score', CpcViewSet)


urlpatterns = [
    path('admin/', admin.site.urls),
    url(r'api/', include(router.urls)),
    path('api/login/', MyTokenObtainPairView.as_view(), name='token_obtain'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('reset_password_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name ='password_reset_confirm'),
    path('api/logout/', LogoutView.as_view()),
    path('api/dashboard/', DashboardView.as_view()),
    path('api/trainees/', TraineeListView.as_view()),
    path('password_reset/', PasswordResetView.as_view(), name='rest_password_reset'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
