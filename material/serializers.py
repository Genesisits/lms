from rest_framework import serializers

from .models import Material, FieldStudyObservation
from user.serializers import UserSerializer
from businessGroup.serializers import BatchSerializer


class MaterialSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    batch = serializers.ReadOnlyField(source="as_batch.name")
    modules = serializers.ReadOnlyField(source="as_module.name")
    trainer = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Material
        fields = '__all__'
        read_only_fields = ('file_status', 'comment')
        extra_kwargs = {'as_batch': {'required': True, 'allow_null': False, 'allow_empty': False},
                        'as_module': {'required': True, 'allow_null': False, 'allow_empty': False}}

    def get_file(self, obj):
        return self.context.get('request').build_absolute_uri(obj.file.url)

    def get_trainer(self, obj):
        fn = obj.user.first_name
        ln = obj.user.last_name
        return fn + " " + ln


class AdminSerializer(serializers.ModelSerializer):
    file_status = serializers.CharField(write_only=False)
    batch = serializers.ReadOnlyField(source='as_batch.name')
    comment = serializers.CharField(allow_null=True)

    class Meta:
        model = Material
        fields = ('id',  'user', 'batch', "as_batch", 'as_module', 'file', 'comment', 'file_status',)
        read_only_fields = ('id', 'user', 'batch', 'as_module', 'file',)


class FieldStudySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    trainer = UserSerializer(read_only=True)
    trainee_name = serializers.SerializerMethodField(read_only=True)
    batch_name = BatchSerializer(source='batch', many=True, read_only=True)
    assessment = serializers.ReadOnlyField(source='assessment_is.assmt.assessment_name')

    class Meta:
        model = FieldStudyObservation
        fields = "__all__"

    def get_file(self, obj):
        return self.context.get('request').build_absolute_uri(obj.file.url)

    def get_trainee_name(self, obj):
        fn = obj.trainee.first_name
        ln = obj.trainee.last_name
        return fn + " " + ln
