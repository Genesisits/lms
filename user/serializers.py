from django.conf import settings
from django.contrib.auth.hashers import make_password

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.encoding import force_str
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from rest_framework.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.core.exceptions import ValidationError

from .models import LmsUser, QuestionFeed, AnswerFeed

UserModel = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True,
                                   validators=[UniqueValidator(queryset=LmsUser.objects.all())])
    first_name = serializers.CharField(required=True)
    date_of_join = serializers.DateField(format=settings.DATE_FORMAT, required=True)
    date_joined = serializers.DateTimeField(format=settings.DATE_FORMAT, read_only=True)

    class Meta:
        model = LmsUser

        fields = ('id', 'username', 'password', 'last_login', 'is_superuser', 'first_name',
                  'last_name', 'email', 'is_active', 'date_of_join', 'mobile_number', 'gender',
                  'image', 'location', 'is_course_trainer', 'is_sfe_trainer', 'is_trainee',
                  'is_country_sales_manager', 'is_training_head', 'designation', 'escalation_status', 'date_joined')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value: str) -> str:
        """
        Hash value passed by user.

        :param value: password of a user
        :return: a hashed version of the password
        """
        return make_password(value)

    def validate(self, data):
        if self.initial_data["is_training_head"] is True:
            if LmsUser.objects.filter(is_training_head=True).exists():
                raise Exception("Training head must be single and already created")
            else:
                return data
        else:
            return data


class MyInfoSerializer(serializers.ModelSerializer):
    image = serializers.FileField(allow_empty_file=True, required=False, allow_null=True)
    image_url = serializers.SerializerMethodField(read_only=True, allow_null=True)
    username = serializers.CharField(required=False)
    first_name = serializers.CharField(required=False)
    # password = serializers.CharField(required=False)
    gender = serializers.CharField(required=False)
    mobile_number = serializers.CharField(required=False)

    class Meta:
        model = LmsUser
        read_only_fields = ('is_course_trainer', 'is_sfe_trainer', 'is_trainee', 'is_country_sales_manager',
                            'is_training_head', 'is_superuser', 'is_active')
        fields = (
            'id', 'username', 'last_login', 'is_superuser', 'first_name', 'last_name', 'email', 'is_active',
            'date_of_join', 'mobile_number', 'gender', 'image', 'location', 'is_course_trainer', 'is_sfe_trainer',
            'is_trainee', 'is_country_sales_manager', 'is_training_head', 'designation', 'escalation_status',
            'image_url')

    def to_representation(self, instance):
        representation = super(MyInfoSerializer, self).to_representation(instance)
        domain_name = ''
        if instance.image:
            full_path = domain_name + instance.image.url
            representation['image'] = full_path
        else:
            representation['image'] = None
        return representation

    def get_image_url(self, obj):
        if obj.image:
            return self.context.get('request').build_absolute_uri(obj.image.url)
        return None


class UpgradeSerializer(serializers.ModelSerializer):
    role_status = serializers.SerializerMethodField()

    class Meta:
        model = LmsUser
        fields = (
            'id', 'last_login', 'is_superuser', 'first_name', 'last_name', 'email', 'is_active',
            'date_of_join', 'mobile_number', 'gender', 'location', 'is_course_trainer', 'is_sfe_trainer',
            'is_trainee', 'is_country_sales_manager', 'is_training_head', 'designation', 'role_status'
        )

        extra_kwargs = {'username': {'required': False}, 'first_name': {'required': False},
                        'password': {'required': False}, 'gender': {'required': False},
                        'mobile_number': {'required': False}}

        read_only_fields = (
            'is_superuser', 'is_course_trainer', 'is_sfe_trainer',
            'is_trainee', 'is_country_sales_manager', 'is_training_head',
        )

    def get_role_status(self, obj):
        role = 'Trainee'
        if obj.is_course_trainer:
            role = 'Trainer'
        if obj.is_sfe_trainer:
            role = 'SFE Trainer'
        if obj.is_country_sales_manager:
            role = 'Country Sales Manager'
        if obj.is_training_head:
            role = 'Training Head'
        if obj.is_superuser:
            role = 'Admin'
        return role


class AdminUpgradeSerializer(serializers.ModelSerializer):

    class Meta:
        model = LmsUser
        fields = (
            'id', 'last_login', 'is_superuser', 'first_name', 'last_name', 'email', 'is_active',
            'date_of_join', 'mobile_number', 'gender', 'location', 'is_course_trainer', 'is_sfe_trainer',
            'is_trainee', 'is_country_sales_manager', 'is_training_head', 'designation',
        )

        extra_kwargs = {'username': {'required': False}, 'first_name': {'required': False},
                        'password': {'required': False}, 'gender': {'required': False},
                        'mobile_number': {'required': False}}

        read_only_fields = ('is_superuser',)


class QuestionfeedSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)

    class Meta:
        model = QuestionFeed
        fields = ('id', 'question_text')


class AnswerfeedSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    feedback_answers = serializers.CharField(max_length=150, allow_null=False, allow_blank=False, required=True)
    comment = serializers.CharField(max_length=300, allow_null=False, required=True, allow_blank=False)

    class Meta:
        model = AnswerFeed
        fields = ('id', 'trainee', 'trainer', 'module', 'batch','question', 'feedback_answers', 'comment')


class MyTokenObtainPairSerializer(TokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        data['user'] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.ModelSerializer):
    def validate_password(self, value: str) -> str:
        """
        Hash value passed by user.

        :param value: password of a user
        :return: a hashed version of the password
        """
        return make_password(value)

    class Meta:
        model = LmsUser
        fields = ('id', 'username', 'password')
        read_only_fields = ('id', 'username')


class PasswordResetSerializer(serializers.Serializer):

    """
    Serializer for requesting a password reset e-mail.
    """

    email = serializers.EmailField()

    password_reset_form_class = PasswordResetForm

    def validate_email(self, value):
        # Create PasswordResetForm with the serializer
        self.reset_form = self.password_reset_form_class(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError('Error')

        if not LmsUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('Invalid e-mail address')

        return value

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def save(self):
        request = self.context.get('request')
        # Set some values to trigger the send_email method.
        opts = {
            'use_https': request.is_secure(),
            'from_email': getattr(settings, 'DEFAULT_FROM_EMAIL'),
            'request': request,
        }
        self.reset_form.save(**opts)


INTERNAL_RESET_SESSION_TOKEN = '_password_reset_token'


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    new_password1 = serializers.CharField(max_length=128, style={'input_type': 'password'})
    new_password2 = serializers.CharField(max_length=128, style={'input_type': 'password'})
    uid = serializers.CharField()
    token = serializers.CharField()

    set_password_form_class = SetPasswordForm
    _errors = {}
    user = None
    set_password_form = None

    def custom_validation(self, attrs):
        pass

    def validate(self, attrs):

        # Decode the uidb64 (allauth use base36) to uid to get User object
        try:
            uid = force_str(uid_decoder(attrs['uid']))
            self.user = UserModel._default_manager.get(pk=uid)
        except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
            raise ValidationError({'uid': ['Invalid value']})

        if not default_token_generator.check_token(self.user, attrs['token']):
            raise ValidationError({'token': ['Invalid value']})

        self.custom_validation(attrs)
        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs,
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        return self.set_password_form.save()

