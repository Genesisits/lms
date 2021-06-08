from django.contrib import admin
from assessment.models import Assessment, BatchAssessment, Answer

admin.site.register(Assessment)


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('trainee', 'assessments', 'get_batches', 'status', 'attendance_update', 'total_score',)
    list_filter = ('trainee', 'assessments', 'status', 'attendance_update', 'total_score',)
    search_fields = ('trainee', 'assessments', 'status', 'get_batches', 'assessments__batches__name')

    def get_batches(self, obj):
        return obj.assessments.batches.name

    get_batches.short_description = 'Batches'


class BatchAssessmentAdmin(admin.ModelAdmin):
    list_display = ('trainer', 'get_assessments', 'get_batches', 'status', 'duration', 'scheduled_at',)
    list_filter = ('trainer', 'status',)
    search_fields = ('trainer', 'get_assessments', 'get_batches', 'status',)

    def get_batches(self, obj):
        return obj.batches.name

    def get_assessments(self, obj):
        return obj.assmt.assessment_name

    get_batches.short_description = 'Batches'
    get_assessments.short_description = 'Assessment'


admin.site.register(Answer, AnswerAdmin)
admin.site.register(BatchAssessment, BatchAssessmentAdmin)
