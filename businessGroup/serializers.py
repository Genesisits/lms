from django.conf import settings
from rest_framework import serializers

from user.serializers import UserSerializer
from .models import Batch, BusinessGroup, Level, Module


class BusinessGroupSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    # levels = serializers.SlugRelatedField(slug_field='name', queryset=Level.objects.all(), many=True)
    training_head = serializers.PrimaryKeyRelatedField(required=False, read_only=True, allow_null=True)
    trainingHead = UserSerializer(source='training_head', read_only=True)
    bg_name = serializers.SerializerMethodField(source='name', read_only=True)

    class Meta:
        model = BusinessGroup
        fields = ('id', 'name', 'days', 'is_active', 'training_head', 'trainingHead',
                  'bg_name', 'course_trainer_count')

    def get_bg_name(self, obj):
        return obj.name.lower().replace(" ", "_")


class BatchSerializer(serializers.ModelSerializer):
    businessGroup = serializers.ReadOnlyField(source='business_group.name')
    start_date = serializers.DateField(format=settings.DATE_FORMAT)
    end_date = serializers.DateField(format=settings.DATE_FORMAT, allow_null=True, required=False)
    trainees = UserSerializer(source='trainee', many=True, read_only=True)
    created = serializers.SerializerMethodField()
    updated = serializers.SerializerMethodField()
    courseTrainer = UserSerializer(source='course_trainer', many=True, read_only=True)
    # s_f_e_Trainer = UserSerializer(source='salesforce_trainer', many=True, read_only=True)
    trainingHead = UserSerializer(source='business_group.training_head', read_only=True)
    # countrySalesManager = UserSerializer(source='business_group.country_sales_manager', read_only=True)
    # modules = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = '__all__'

    def get_created(self, obj):
        return obj.created_at.strftime('%d-%m-%Y')

    def get_updated(self, obj):
        return obj.updated_at.strftime('%d-%m-%Y')

    # def get_modules(self, obj):
    #     levels = obj.business_group.levels.all()
    #     modules = []
    #     for row in levels:
    #         data = list(row.modules.all().values('name', 'id'))
    #         modules.extend(data)
    #     return modules


class ModuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = Module
        fields = '__all__'


class LevelSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    created = serializers.SerializerMethodField()
    updated = serializers.SerializerMethodField()
    modules = serializers.SlugRelatedField(slug_field='name', queryset=Module.objects.all(),
                                           many=True, allow_empty=False)

    class Meta:
        model = Level
        fields = '__all__'

    def get_created(self, obj):
        return obj.created_at.strftime('%d-%m-%Y')
    
    def get_updated(self, obj):
        return obj.updated_at.strftime('%d-%m-%Y')
