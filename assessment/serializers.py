from django.conf import settings

from rest_framework import serializers
from businessGroup.serializers import BatchSerializer
from user.serializers import UserSerializer

from .models import (
    Assessment, BatchAssessment, Answer, MultipartData, CpcEvaluate
)


class AssessmentSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    module = serializers.ReadOnlyField(source='as_module.name')
    as_status = serializers.SerializerMethodField()
    created = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = '__all__'

    def get_created(self, obj):
        return obj.created_at.strftime("%d-%m-%Y")

    def get_as_status(self, obj):
        obj = BatchAssessment.objects.filter(assmt=obj.id)
        if obj:
            return obj[0].status
        else:
            return "INITIATE"


class BatchAssessmentSerializer(serializers.ModelSerializer):
    assessment_data = serializers.JSONField(allow_null=True, required=False)
    assessment_name = serializers.ReadOnlyField(source='assmt.assessment_name')
    batch_name = serializers.ReadOnlyField(source='batches.name')
    scheduled_at = serializers.DateField(format=settings.DATE_FORMAT, allow_null=True, required=False)
    end_at = serializers.DateField(format=settings.DATE_FORMAT, required=False)
    module_name = serializers.ReadOnlyField(source='assmt.as_module.name')
    type = serializers.ReadOnlyField(source='assmt.as_type')
    timer = serializers.SerializerMethodField()
    trainer_name = serializers.SerializerMethodField(read_only=True)
    total_questions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BatchAssessment
        fields = "__all__"
        read_only_fields = ("active", "end_at")

    def get_timer(self, obj):
        if obj.duration:
            d = obj.duration.total_seconds()
            return d

    def get_total_questions(self, obj):
        questions = obj.assessment_data
        if questions != None:
            count = len(questions)
            return count
        return 0

    def get_trainer_name(self, obj):
        fn = obj.trainer.first_name
        ln = obj.trainer.last_name
        return fn + " " + ln


class AnswerSerializer(serializers.ModelSerializer):
    answer_data = serializers.JSONField(allow_null=True, required=False)
    total_questions = serializers.SerializerMethodField(read_only=True)
    answered = serializers.SerializerMethodField(read_only=True)
    trainee_name = serializers.SerializerMethodField(read_only=True)
    assessment_name = serializers.ReadOnlyField(source='assessments.assmt.assessment_name')
    assessment_type = serializers.ReadOnlyField(source='assessments.assmt.as_type')
    module_name = serializers.ReadOnlyField(source='assessments.assmt.as_module.name')
    batch_name = serializers.ReadOnlyField(source='assessments.batches.name')
    duration = serializers.ReadOnlyField(allow_null=True)

    class Meta:
        model = Answer
        fields = "__all__"

    def get_trainee_name(self, obj):
        fn = obj.trainee.first_name
        ln = obj.trainee.last_name
        return fn + " " + ln

    def get_total_questions(self, obj):
        answers = obj.answer_data
        if answers != None:
            count = len(answers)
            if "duration" in answers[0]:
                return count - 1
            return count
        return 0

    def get_answered(self, obj):
        count = 0
        answers = obj.answer_data
        types = ["CTA", "MTF", "TRF", "FTB", "TR", "AR", "VR"]
        if answers != None:
            for answer in answers:
                for qstype in types:
                    if qstype in answer:
                        if qstype == "CTA":
                            if len(answer[qstype][0]["answers"]) >= 1:
                                count += 1
                        elif qstype == "FTB":
                            if len(answer[qstype][0]["answers"]) >= 1:
                                count += 1
                        elif qstype == "TRF":
                            if answer[qstype][0]["trf_answers"] != "":
                                count += 1
                        elif qstype == "MTF":
                            for x in range(0, len(answer[qstype][0]["mtf_answers"])):
                                try:
                                    if (len(answer[qstype][0]["mtf_answers"][x]['question']) >= 1) and (
                                            len(answer[qstype][0]["mtf_answers"][x]['answer']) >= 1):
                                        count = count + 1
                                        break
                                except:
                                    continue
                        else:
                            if answer[qstype][0]["answer"] != "":
                                count += 1
            return count
        return 0


class AdminSerializer(serializers.ModelSerializer):
    status = serializers.CharField(write_only=False)
    assessment_name = serializers.ReadOnlyField(source='assmt.assessment_name')
    batch_name = serializers.ReadOnlyField(source='batches.name')
    module_name = serializers.ReadOnlyField(source='assmt.as_module.name')
    type = serializers.ReadOnlyField(source='assmt.as_type')

    class Meta:
        model = BatchAssessment
        fields = ('id', 'assmt', 'trainer', 'batches', 'status', 'assessment_data',
                  'duration', 'scheduled_at', 'end_at', 'active', 'assessment_name',
                  'batch_name', 'module_name', 'type')
        read_only_fields = ('id', 'assmt', 'trainer', 'batches', 'assessment_data',
                            'duration', 'scheduled_at', 'end_at', 'active', 'assessment_name',
                            'batch_name', 'module_name', 'type')


class MultipartDataSerializer(serializers.ModelSerializer):
    file = serializers.FileField(use_url=True)

    class Meta:
        model = MultipartData
        fields = '__all__'

    def get_file_url(self, obj):
        if obj.file:
            return self.context.get('request').build_absolute_uri(obj.file.url)
        return None


class CpcSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    trainer_name = serializers.SerializerMethodField(read_only=True)
    trainee_name = serializers.SerializerMethodField(read_only=True)
    batch_name = serializers.ReadOnlyField(source='cpbatch.name')
    assessment = serializers.ReadOnlyField(source='assessment_is.assmt.assessment_name')

    class Meta:
        model = CpcEvaluate
        fields = "__all__"

    def get_trainee_name(self, obj):
        fn = obj.trainee.first_name
        ln = obj.trainee.last_name
        return fn + " " + ln

    def get_trainer_name(self, obj):
        fn = obj.trainer.first_name
        ln = obj.trainer.last_name
        return fn + " " + ln
