import logging

import time
from datetime import date, datetime, timedelta
from operator import itemgetter
from random import sample, choice
from statistics import mean

from django.core.mail import send_mail

import rest_framework
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status
from rest_framework.pagination import LimitOffsetPagination

from businessGroup.models import Batch
from .models import (
    Assessment, BatchAssessment, Answer, MultipartData, CpcEvaluate
)
from .serializers import (
    AssessmentSerializer, BatchAssessmentSerializer, AnswerSerializer,
    AdminSerializer, MultipartDataSerializer, CpcSerializer
)
from user.models import LmsUser
from businessGroup.views import notify_email
from attendance.models import Attendance
from lms.constants import GRAPH_COLORS, ASSESSMENT_LIST, VERIFY_INIT

logger = logging.getLogger('loggers.log')


class AssessmentView(viewsets.ModelViewSet):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_superuser:
            if not self.queryset.filter(assessment_name__iexact=request.data["assessment_name"]).exists():
                serializer = self.serializer_class(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    logger.info("assessment created")
                    return Response(serializer.data)
                logger.error("assessment creation error")
                return Response(serializer.errors)
            else:
                logger.error("assessment already exists")
                return Response({"data": "Assessment with same name already exists"},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        question = self.queryset.all()
        if request.user.is_course_trainer:
            question = question.filter(assessment_name__in=("A11", "A12", "A2", "A31", "A32"))
        # if request.user.is_sfe_trainer:
        #     question = question.filter(assessment_name__in=("A13", "A33", "A34"))
        page = self.paginate_queryset(question)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            logger.info("assessment list")
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(question, many=True)
        return Response(serializer.data)

    def update(self, request, **kwargs):
        data = request.data
        instance = Assessment.objects.get(pk=kwargs.get('pk'))
        if request.user.is_superuser:
            serializer = AssessmentSerializer(instance, data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                logger.info("asessment updated successfully")
                return Response(serializer.data)
            logger.error("assessment update error")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("assessment deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("assessment is not deleted")
        return Response({"data": "assessment is not deleted"}, status=status.HTTP_400_BAD_REQUEST)


def question_shuffling(assessment):
    for data in assessment:
        if "assessment_data" in data:
            objective = data['assessment_data']
            questions = sample(objective, len(objective))
            data['assessment_data'] = questions
            
            for question in questions:
                if "CTA" in question:
                    choices = [c for value in question["CTA"] for c in value['choice_list']]
                    cta = sample(choices, len(choices))
                    question["CTA"][0]['choice_list'] = cta
                    question["CTA"][0].pop("correct_answers")
                    
                if "MTF" in question:
                    mtf = [p for q in question['MTF'] for p in q['questions']]
                    matches = sample(mtf, len(mtf))
                    match_questions = [c_a['question'] for c_a in matches]
                    match_questions = [i for i in match_questions if i]
                    match_answers = [c_b['answer'] for c_b in matches]
                    match_answers = [i for i in match_answers if i]
                    sampled = sample(match_answers, len(match_answers))
                    qs = []
                    for vale in match_questions:
                        for val in sampled:
                            qs.append({"question": vale, "answer": val})
                            sampled.remove(val)
                            break
                    question['MTF'][0]['questions'] = qs
                    
                if "TRF" in question:
                    question["TRF"][0].pop("correct_answers")
                    
                if "FTB" in question:
                    question["FTB"][0].pop("correct_answers")


class BatchAssessmentView(viewsets.ModelViewSet):
    queryset = BatchAssessment.objects.all()
    serializer_class = BatchAssessmentSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            data = request.data
            if data.get("assessment_data"):
                for question in data.get("assessment_data"):
                    if "CTA" in question:
                        len_questions = len(question["CTA"][0]["correct_answers"])
                        question["CTA"][0].update({"answers_length": len_questions})
            if data.get("submit"):
                data["status"] = "APPROVED"
            if data.get("draft"):
                data["status"] = VERIFY_INIT
            if data.get("scheduled_at"):
                data['scheduled_at'] = datetime.strptime(request.data["scheduled_at"], "%d-%m-%Y").date()
            if not BatchAssessment.objects.filter(assmt=data["assmt"], batches=data["batches"]).exists():
                end_at = Batch.objects.get(id=data["batches"]).end_date
                serializer = BatchAssessmentSerializer(data=data)
                if serializer.is_valid():
                    serializer.save(trainer=request.user, end_at=end_at)
                    notify_email(module="ASSESSMENT", purpose="created", id=data["batches"],
                                 required_for={"assessment": serializer.data["assessment_name"],
                                               "batch": serializer.data["batch_name"]})
                    return Response(serializer.data)
                return Response(serializer.errors)
            return Response({"data": "This assessment already created for this batch"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        assessments = BatchAssessment.objects.all()

        if request.user.is_trainee:
            assessment_id = request.query_params.get("id")
            ass = []
            if assessment_id:
                ass = assessments.filter(id=assessment_id)
            else:
                query_data = assessments.filter(batches__trainee=request.user,
                                                status="APPROVED", end_at__gte=date.today())
                assessment_data = query_data.filter(active=True) | query_data.filter(
                    batches__refresher_course=True)
                for assess in assessment_data:
                    if not Answer.objects.filter(assessments__id=assess.id,
                                                 trainee=request.user.id).exists():
                        ass.append(assess)
            serializer = BatchAssessmentSerializer(ass, many=True)
            question_shuffling(serializer.data)
        elif request.user.is_course_trainer or request.user.is_sfe_trainer:
            batch = request.query_params.get("batch")
            assessment = request.query_params.get("assessment")
            if batch:
                if not assessments.filter(batches=batch, assmt=assessment).exists():
                    return Response({"data": "This Assessment can be created for this batch"}, status=status.HTTP_200_OK)
                return Response(
                    {"data": "This Assessment already created for this batch"}, status=status.HTTP_409_CONFLICT
                )
            assessment = assessments.filter(trainer=request.user)
            serializer = BatchAssessmentSerializer(assessment, many=True)
        elif request.user.is_superuser:
            assessment = assessments.exclude(status="IN PROGRESS")
            serializer = BatchAssessmentSerializer(assessment, many=True)
        return Response(serializer.data)

    def update(self, request, **kwargs):
        data = request.data
        if data.get("assessment_data"):
            for question in data.get("assessment_data"):
                if "CTA" in question:
                    len_questions = len(question["CTA"][0]["correct_answers"])
                    question["CTA"][0].update({"answers_length": len_questions})
        instance = BatchAssessment.objects.get(pk=kwargs.get('pk'))
        if data.get("submit"):
            data["status"] = "APPROVED"
        if data.get("draft"):
            data["status"] = VERIFY_INIT
        if data.get("scheduled_at"):
            data['scheduled_at'] = datetime.strptime(request.data["scheduled_at"], "%d-%m-%Y").date()
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            old_data = data.get("o_data")
            if old_data:
                logger.info("old question here", old_data)
                if type(old_data) is list:
                    if old_data and old_data[0] in instance.assessment_data:
                        for ind, qs in enumerate(instance.assessment_data):
                            if old_data[0] == qs:
                               instance.assessment_data[ind] = data["assessment_data"][0]
                else:
                    if old_data in instance.assessment_data:
                        for ind, qs in enumerate(instance.assessment_data):
                            if old_data == qs:
                               instance.assessment_data[ind] = data["assessment_data"][0]
                assessment = []
                assessment.extend(instance.assessment_data)
                for question in data.get("assessment_data"):
                    if question not in assessment:
                        assessment.append(question)
                data["assessment_data"] = assessment
            serializer = BatchAssessmentSerializer(instance, data)
            if serializer.is_valid():
                serializer.save(trainer=request.user)
                logger.info("assessment updated successfully")
                return Response(serializer.data)
            logger.error("assessment update error")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_superuser:
            serializer = AdminSerializer(instance, data)
            if serializer.is_valid():
                serializer.save()
                notify_email(module="ASSESSMENT", purpose="approval", id=serializer.data["id"],
                             required_for={"assessment": serializer.data["assessment_name"],
                                           "batch": serializer.data["batch_name"],
                                           "status": serializer.data["status"]})
                logger.info("admin updated status")
                return Response(serializer.data)
            logger.info("admin updation error")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("batch assessment deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("batch assessment is not deleted")
        return Response({"data": "assessment is not deleted"}, status=status.HTTP_400_BAD_REQUEST)


class AnswerView(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_trainee:
            data = request.data
            # if "CTA" in data.get("answer_data")[0]:
            #     batch_assessment = BatchAssessment.objects.get(id=data["assessments"]).assessment_data
            #     for question in batch_assessment:
            #         if "CTA" in question:
            #             if question["CTA"][0]["question_text"] == data["answer_data"][0]["CTA"][0]["question_text"]:
            #                 cta_answers = []
            #                 for cta in data["answer_data"][0]["CTA"][0]['cta']:
            #                     if cta['value'] is True:
            #                         cta_answers.append(cta)
            #                 len_answers = len(cta_answers)
            #                 len_questions = len(question["CTA"][0]["correct_answers"])
            #                 if not len_answers <= len_questions:
            #                     return Response({"data": "There are only %s answers for this question" % len_questions},
            #                                     status=status.HTTP_400_BAD_REQUEST)
            if data.get("total_data"):
                data["total_data"] = emptyAnswers(data["total_data"])
            if BatchAssessment.objects.get(id=data["assessments"]).end_at >= date.today():
                if not Answer.objects.filter(assessments=data["assessments"], trainee=request.user.id).exists():
                    stat = "inprogress"
                    if data.get("submit") is True:
                        stat = "completed"
                    ans_data = answer(data)
                    serializer = AnswerSerializer(data=ans_data)
                    if serializer.is_valid():
                        serializer.save(trainee=request.user, status=stat)
                        instance = Answer.objects.get(id=serializer.data["id"])
                        if serializer.data["submit"] is True:
                            instance.status = "completed"
                            ianswer = instance.answer_data
                            for x in ianswer:
                                if "duration" in x:
                                    ianswer.remove(x)
                            types = ["CTA", "MTF", "TRF", "FTB", "TR", "AR", "VR"]
                            for ans in ianswer:
                                for ans_type in types:
                                    if ans_type in ans:
                                        ans[ans_type][0].update({"marks": 0})
                            instance.answer_data = ianswer
                            instance.save()
                            notify_email(module="ASSESSMENT", purpose="assessment_completed",
                                         id=instance.id,
                                         required_for={"assessment": serializer.data["assessment_name"],
                                                       "batch": serializer.data["batch_name"],
                                                       "user": serializer.data["trainee_name"]})
                        return Response(serializer.data)
                    return Response(serializer.errors)
                return Response({"data": "Duplicate request! you already submitted the assessment"},
                                status=rest_framework.status.HTTP_400_BAD_REQUEST)
            return Response({"data": "Assessment submission date is completed"},
                            status=rest_framework.status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_trainee:
            data = Answer.objects.filter(trainee=request.user)
            ans = request.query_params.get("id")
            if ans:
                ans_data = data.get(id=ans)
                answer = ans_data.answer_data
                for x in answer:
                    if "duration" in x:
                        ans_data.duration = x
                        answer.remove(x)
                ans_data.answer_data = answer
                serializer = AnswerSerializer(ans_data)
            else:
                serializer = AnswerSerializer(data, many=True)
            return Response(serializer.data)

        elif request.user.is_course_trainer or request.user.is_sfe_trainer:
            data = Answer.objects.filter(assessments__trainer=request.user)
            serializer = AnswerSerializer(data, many=True)
            return Response(serializer.data)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        data = request.data
        instance = Answer.objects.get(pk=kwargs.get('pk'))
        if request.user.is_trainee:
            # if "CTA" in data.get("answer_data")[0]:
            #     batch_assessment = BatchAssessment.objects.get(id=instance.assessments.id).assessment_data
            #     for question in batch_assessment:
            #         if "CTA" in question:
            #             if question["CTA"][0]["question_text"] == data["answer_data"][0]["CTA"][0]["question_text"]:
            #                 cta_answers = []
            #                 for cta in data["answer_data"][0]["CTA"][0]['cta']:
            #                     if cta['value'] is True:
            #                         cta_answers.append(cta)
            #                 len_answers = len(cta_answers)
            #                 len_questions = len(question["CTA"][0]["correct_answers"])
            #                 if not len_answers <= len_questions:
            #                     return Response({"data": "There are only %s answers for this question" %len_questions},
            #                                     status=status.HTTP_400_BAD_REQUEST)
            data["total_data"] = instance.answer_data
            ans_data = answer(data)
            serializer = AnswerSerializer(instance, ans_data)
            if serializer.is_valid():
                serializer.save(trainee=request.user)
                if serializer.data["submit"] is True:
                    instance.status = "completed"
                    ianswer = instance.answer_data
                    for x in ianswer:
                        if "duration" in x:
                            ianswer.remove(x)
                    types = ["CTA", "MTF", "TRF", "FTB", "TR", "AR", "VR"]
                    for ans in ianswer:
                        for ans_type in types:
                            if ans_type in ans:
                                ans[ans_type][0].update({"marks": 0})
                    instance.answer_data = ianswer
                    instance.save()
                    notify_email(module="ASSESSMENT", purpose="assessment_completed",
                                 id=instance.id,
                                 required_for={"assessment": serializer.data["assessment_name"],
                                               "batch": serializer.data["batch_name"],
                                               "user": serializer.data["trainee_name"]})
                logger.info("answer updated successfully")
                return Response(serializer.data)
            logger.error("answer update error")
            return Response(serializer.errors)

        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            asmt_name = instance.assessments.assmt.assessment_name
            previous_answer = Answer.objects.filter(assessments__batches=instance.assessments.batches,
                                                    trainee=instance.trainee)
            if asmt_name == "A12":
                if previous_answer.filter(assessments__assmt__assessment_name="A11"):
                    if previous_answer.get(assessments__assmt__assessment_name="A11").status != "reviewed":
                        return Response({"data": "A11 assessment need to be reviewed"},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"data": "A11 assessment need to be reviewed"},
                                    status=status.HTTP_400_BAD_REQUEST)
            if asmt_name == "A32":
                if previous_answer.filter(assessments__assmt__assessment_name="A31"):
                    if previous_answer.get(assessments__assmt__assessment_name="A31").status != "reviewed":
                        return Response({"data": "A31 assessment need to be reviewed"},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"data": "A31 assessment need to be reviewed"},
                                    status=status.HTTP_400_BAD_REQUEST)
            instance.reviewing = True
            instance.save()
            marks = []
            weight = []
            if not data.get("status"):
                data["status"] = "reviewing"
            data = reviewAssessment(data)
            serializer = AnswerSerializer(instance, data)
            if serializer.is_valid():
                for value in serializer.validated_data["answer_data"]:
                    if "type" in value.keys():
                        for val in value.values():
                            if type(val[0]) is dict:
                                marks.append(float(val[0]['marks']))
                                weight.append(float(val[0]["weightage"]))
                serializer.save(total_score=sum(marks)/sum(weight)*100)
                if serializer.data["status"] == "reviewed":
                    messagealert(serializer.data)
                logger.info("marks updated successfully")
                return Response(serializer.data)
            logger.error("score is not updated")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_course_trainer or request.user.is_sfe_trainer or request.user.is_trainee:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("answer is deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("answer is not deleted")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)


def messagealert(assessment_data):
    answer = Answer.objects.filter(trainee=assessment_data["trainee"],
                                   assessments__batches__name=assessment_data["batch_name"])
    scores = []
    assessments = []
    if assessment_data["assessment_name"] == "A12":
        assessments = ["A11", "A12"]
    elif assessment_data["assessment_name"] == "A13":
        assessments = ["A13"]
    elif assessment_data["assessment_name"] == "A32":
        assessments = ["A31", "A32"]
    elif assessment_data["assessment_name"] == "A34":
        assessments = ["A34"]

    for val in assessments:
        score = answer.get(assessments__assmt__assessment_name=val).total_score
        scores.append(score)
    if len(scores) != 0:
        if float(mean(scores)) < 80:
            user = LmsUser.objects.get(id=assessment_data["trainee"])
            notify_email(module="ASSESSMENT", purpose="required_cutoff", id=assessment_data["id"],
                         required_for={"assessment": assessments,
                                       "user": user.first_name + " " + user.last_name,
                                       "batch": answer.get(
                                           assessments__assmt__assessment_name=assessments[0]
                                       ).assessments.batches.name})


class MultipartdataView(viewsets.ModelViewSet):
    queryset = MultipartData.objects.all()
    serializer_class = MultipartDataSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        logger.error("File Upload view here::%s" % request.data)
        data = request.data
        if data.get('audio'):
            data['file'] = data.get('audio')
        serializer = self.serializer_class(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        data = MultipartData.objects.all()
        serializer = self.serializer_class(data, many=True, context={'request': request})
        return Response(serializer.data)

    def update(self, request, **kwargs):
        logger.info("Error Hit here for File upload::%s" % request.data)
        data = request.data
        if data.get('audio'):
            data['file'] = data.get('audio')
        instance = MultipartData.objects.get(pk=kwargs.get('pk'))
        serializer = self.serializer_class(instance, data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        logger.info("file deleted successfully")
        return Response(status=status.HTTP_204_NO_CONTENT)


def scores_list(trainee, bg, batch):
    scores = []
    m1_tech_scores = []
    m2_tech_scores = []
    m3_tech_scores = []
    m1_ss_scores = []
    m33_ss_scores = []
    m34_ss_scores = []
    assessments = []
    answers = Answer.objects.filter(trainee=trainee, assessments__batches__business_group=bg,
                                    assessments__batches=batch)
    scores.append({"trainee": trainee})
    for answer in answers:
        assessment = answer.assessments.assmt.assessment_name
        assessments.append(
            {assessment: float(answer.total_score)}
        )
        if (assessment == "A11") or (assessment == "A12"):
            m1_tech_scores.append(float(answer.total_score))
        if assessment == "A2":
            m2_tech_scores.append(float(answer.total_score))
        if (assessment == "A31") or (assessment == "A32"):
            m3_tech_scores.append(float(answer.total_score))
        if assessment == "A13":
            m1_ss_scores.append(float(answer.total_score))
        if assessment == "A33":
            m33_ss_scores.append(float(answer.total_score))
        if assessment == "A34":
            m34_ss_scores.append(float(answer.total_score))
    scores.append({"assessment_scores": assessments})
    scores.extend([
        {"module_scores": [
            {"m1_technical": mean(m1_tech_scores) if m1_tech_scores else "NA"},
            {"m2_technical": mean(m2_tech_scores) if m2_tech_scores else "NA"},
            {"m3_technical": mean(m3_tech_scores) if m3_tech_scores else "NA"},
            {"m1_soft_skills": mean(m1_ss_scores) if m1_ss_scores else "NA"},
            {"m33_soft_skills": mean(m33_ss_scores) if m33_ss_scores else "NA"},
            {"m34_soft_skills": mean(m34_ss_scores) if m34_ss_scores else "NA"},
        ]}
    ])
    if m1_tech_scores and m2_tech_scores and m3_tech_scores:
        technical = (33 * (mean(m1_tech_scores)) / 100
                     ) + (33 * (mean(m2_tech_scores)) / 100
                          ) + (33 * (mean(m3_tech_scores)) / 100)
    else:
        technical = "NA"
    if m1_ss_scores and m33_ss_scores and m34_ss_scores:
        softskills = (33 * (mean(m1_ss_scores)) / 100
                      ) + (33 * (mean(m33_ss_scores)) / 100
                           ) + (33 * (mean(m34_ss_scores)) / 100)
    else:
        softskills = "NA"
    scores.extend([
        {"overall_scores": [
            {"overall_technical": round(technical, 2) if type(technical) is float else technical},
            {"overall_soft_skills": round(softskills, 2) if type(softskills) is float else softskills}
        ]}
    ])
    if Batch.objects.get(id=batch).end_date >= date.today():
        if softskills == "NA" or technical == "NA":
            scores.append({"trainee_status": "PURSUING"})
        else:
            if all(
                    [
                        (80 * (mean(m1_tech_scores) if m1_tech_scores else 0) / 100) >= 80,
                        (mean(m2_tech_scores) if m2_tech_scores else 0) == 100,
                        (80 * (mean(m3_tech_scores) if m3_tech_scores else 0) / 100) >= 80,
                        (technical if technical else 0) >= 85,
                        (80 * (mean(m1_ss_scores) if m1_ss_scores else 0) / 100) >= 80,
                        (mean(m33_ss_scores) if m33_ss_scores else 0) == 100,
                        (80 * (mean(m34_ss_scores) if m34_ss_scores else 0) / 100) >= 80,
                        (softskills if softskills else 0) >= 80,
                    ]
            ):
                scores.append({"trainee_status": "CLEARED"})
            else:
                scores.append({"trainee_status": "NOT CLEARED"})
    else:
        scores.append({"trainee_status": "NOT CLEARED"})
    return scores


class ScoreViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        if request.user.is_trainee:
            scores = []
            batches = Batch.objects.filter(trainee=request.user.id)
            for batch in batches:
                scores.append(scores_list(request.user.id, batch.business_group, batch.id))
            return Response(scores)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)


def color_pick(datasets):
    color = choice(GRAPH_COLORS)
    while color in list(map(itemgetter('backgroundColor'), datasets)):
        color = choice(GRAPH_COLORS)
        if color not in list(map(itemgetter('backgroundColor'), datasets)):
            break
    return color


def generate_reports(percents=None, batches=None, assessments=None):
    total_data = []
    datasets = []
    labels = []
    if assessments:
        filter_data = [{"total_score": 100}, {"total_score__range": (80, 99)}, {"total_score__lt": 80}]
    else:
        filter_data = [{"percent": 100}, {"percent__range": (80, 99)}, {"percent__lt": 80}]
    for data in filter_data:
        if ("percent" in data.keys()) or ("total_score" in data.keys()):
            key = "Fulfilled"
        elif ("percent__range" in data.keys()) or ("total_score__range" in data.keys()):
            key = "Above_80"
        else:
            key = "Below_80"
        score_data = []
        trainees_data = []
        if batches:
            for batch in batches:
                if list(data.keys())[0] == 'percent':
                    score_data.append(len([d for d in percents if (d['percent'] == 100) and (d['batch'] == batch)]))
                    for d in percents:
                        if d['percent'] == 100 and d['batch'] == batch:
                            if type(batch) is str or type(batch) is int:
                                trainees_data.append({"trainee": d['trainee'], "batch": batch})
                            else:
                                trainees_data.append({"trainee": d['trainee'], "batch": batch.name})
                    if type(batch) is str or type(batch) is int:
                        labels.append(Batch.objects.get(id=batch).name)
                    else:
                        labels.append(batch.name)
                elif list(data.keys())[0] == 'percent__range':
                    score_data.append(len([d for d in percents if (100 > d['percent'] >= 80) and (d['batch'] == batch)]))
                    for d in percents:
                        if (100 > d['percent'] >= 80) and (d['batch'] == batch):
                            if type(batch) is str or type(batch) is int:
                                trainees_data.append({"trainee": d['trainee'], "batch": batch})
                            else:
                                trainees_data.append({"trainee": d['trainee'], "batch": batch.name})
                else:
                    score_data.append(len([d for d in percents if (1 <= d['percent'] < 80) and (d['batch'] == batch)]))
                    for d in percents:
                        if (1 <= d['percent'] < 80) and (d['batch'] == batch):
                            if type(batch) is str or type(batch) is int:
                                trainees_data.append({"trainee": d['trainee'], "batch": batch})
                            else:
                                trainees_data.append({"trainee": d['trainee'], "batch": batch.name})
        if assessments:
            for assess in assessments:
                data['assessments'] = assess
                score_data.append(Answer.objects.filter(**data).count())
        datasets.append({"label": key, "backgroundColor": color_pick(datasets), "data": score_data})
        total_data.append({"label": key, "trainees": trainees_data})
    return datasets, labels, total_data


def bar_graph(labels, datasets, text, stepsize, xlabel, ylabel, beginsato):
    resp = {
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "options": {
            "title": {
                "display": True,
                "text": text,
                "padding": "20"
            },
            "hover": {
                "animationDuration": 0
            },
            "scales": {
                "xAxes": [
                    {"ticks": {"beginAtZero": beginsato,
                               "stepSize": stepsize
                               },
                     "scaleLabel": {
                         "display": "true",
                         "labelString": xlabel
                        },
                     "barPercentage": "0.8",
                     "categoryPercentage": "0.5",
                     "maxBarThickness": "15"
                     }
                ],
                "yAxes": [
                    {"ticks": {"beginAtZero": beginsato,
                               "stepSize": stepsize
                               },
                     "scaleLabel": {
                         "display": "true",
                         "labelString": ylabel
                     }
                     }
                ]
            }
        }
    }
    return resp


def trainee_reports(trainee):
    datasets = []
    batch = Batch.objects.filter(trainee=trainee)
    total_batches = len(batch)
    batches = batch.values_list("name", flat=True)
    filter_data = ASSESSMENT_LIST
    batch_marks = []
    b_asmts = []
    b_headers = []
    headers = [{"text": "Assessment", "value": "assessment"}]
    batches = [x.capitalize() for x in batches]
    for dat in filter_data:
        assess = []
        assess_marks = []
        for bat in batch:
            if dat is "Overall_Technical":
                score = scores_list(trainee, bat.business_group, bat.id)
                assess.append(score[3]["overall_scores"][0]["overall_technical"])
            elif dat is "Overall_SoftSkills":
                score = scores_list(trainee, bat.business_group, bat.id)
                assess.append(score[3]["overall_scores"][1]["overall_soft_skills"])
            else:
                score = Answer.objects.filter(
                    assessments__assmt__assessment_name=dat,
                    trainee=trainee,
                    assessments__batches=bat.id
                )
                if score:
                    total_score = score.values_list("total_score", flat=True)[0]
                    assess.append(total_score)
                else:
                    total_score = "NA"
                    assess.append(total_score)

            if bat.name not in b_headers:
                b_headers.append(bat.name)
                headers.append({'text': bat.name.capitalize(), 'value': bat.name.replace(' ', '_')})

            if dat not in b_asmts:
                b_asmts.append(dat)
                batch_marks.append(
                    {"assessment": dat, bat.name.replace(' ', '_'): total_score }
                )
            else:
                for row in batch_marks:
                    if row['assessment'] == dat:
                        row[bat.name.replace(' ', '_')] = total_score

        key = dat
        values = assess
        datasets.append(
            {
                "label": key,
                "backgroundColor": color_pick(datasets),
                "data": values
            }
        )
    res = bar_graph(batches, datasets, "Trainee Scores", 20, "Assessments for Batches", "Scores", True)
    graph_data = {"total_batches": total_batches, "batch_wise_marks": batch_marks}
    response = {"bar_graph": res, "graph_info": graph_data, "headers": headers}
    return response


def trainee_percentages(trainer):
    trainees = []
    total_batches = Batch.objects.all()
    batches = total_batches.filter(course_trainer=trainer) | total_batches.filter(
        salesforce_trainer=trainer)
    trainee_data = batches.values_list("trainee", flat=True)
    batch_data = batches.values("trainee", "id")

    datasets = []
    for trainee in trainee_data:
        trainees.append(LmsUser.objects.get(id=trainee).first_name)
    batches_count = len(batches)
    total_trainees = len(trainee_data)
    trainees_details = []
    trainees_assess = []
    filter_data = ASSESSMENT_LIST
    for dat in filter_data:
        assess = []
        for train_batch in batch_data:
            if trainer.is_course_trainer:
                batch = batches.get(course_trainer=trainer.id,
                                    trainee=train_batch.get("trainee"),
                                    id=train_batch.get("id"))
            if trainer.is_sfe_trainer:
                batch = batches.get(salesforce_trainer=trainer.id,
                                    trainee=train_batch.get("trainee"),
                                    id=train_batch.get("id"))
            answers = Answer.objects.filter(assessments__assmt__assessment_name=dat,
                                            trainee=train_batch.get("trainee"),
                                            assessments__batches=batch.id)
            assess.append(answers.values("total_score")[0]["total_score"] if answers.exists() else 0)
        key = dat
        values = assess
        datasets.append(
            {
                "label": key,
                "backgroundColor": color_pick(datasets),
                "data": values
            }
        )
    resp = bar_graph(trainees, datasets, "Trainee Scores", 20, "Trainees", "Assessment Percentage", True)
    for index, trainee in enumerate(resp['data']['labels']):
        for mark in resp['data']['datasets']:
            trainees_details.append({"assessment": mark["label"], "marks": mark["data"][index]})
        trainees_assess.append({"trainee": trainee, "assessments": trainees_details})
        trainees_details = []
    respons = {"bar_graph": resp, "graph_info": {"total_batches": batches_count,
                                                 "total_trainees": total_trainees,
                                                 "trainee_details": trainees_assess}}
    return respons


def trainer_batches(batch, bg=None, trainee_id=None, assessment=None, timespan1=None, timespan2=None, trainer=None):
    total_batches = Batch.objects.all()
    if bg:
        total_batches = total_batches.filter(business_group=bg)
    if batch == 'all':
        batches = total_batches
    else:
        batches = total_batches.filter(id=batch)
    if timespan1 and not timespan2:
        batches = Batch.objects.filter(end_date__gte=timespan1, start_date__lte=date.today())
    if timespan1 and timespan2:
        batches = Batch.objects.filter(end_date__gte=timespan1, start_date__lte=timespan2)

    batch_reports = []

    if trainer:
        batches = batches.filter(course_trainer=trainer) | batches.filter(salesforce_trainer=trainer)

    for batch in batches:
        trainees = []
        datasets = []
        trainees_details = []
        trainees_assess = []
        if assessment:
            filter_data = [assessment]
        else:
            filter_data = ASSESSMENT_LIST
        batch_dataset = Batch.objects.filter(id=batch.id)
        if trainee_id:
            batch_data = [{"trainee": trainee_id, "id": batch.id}]
            trainees.append(LmsUser.objects.get(
                id=trainee_id).first_name.capitalize() + LmsUser.objects.get(id=trainee_id).last_name.capitalize())
            total_trainees = 1
        else:
            trainee_data = batch_dataset.values_list("trainee", flat=True)
            batch_data = batch_dataset.values("trainee", "id")
            for trainee in trainee_data:
                trainees.append(LmsUser.objects.get(id=trainee).first_name.capitalize() +
                                LmsUser.objects.get(id=trainee).last_name.capitalize())
            total_trainees = len(trainee_data)
        for dat in filter_data:
            assess = []
            for train_batch in batch_data:
                if dat is "Overall_Technical":
                    total = scores_list(train_batch.get("trainee"), batch.business_group, batch.id)
                    assess.append(total[3]["overall_scores"][0]["overall_technical"])
                elif dat is "Overall_SoftSkills":
                    total = scores_list(train_batch.get("trainee"), batch.business_group, batch.id)
                    assess.append(total[3]["overall_scores"][1]["overall_soft_skills"])
                else:
                    answers = Answer.objects.filter(assessments__assmt__assessment_name=dat,
                                                    trainee=train_batch.get("trainee"),
                                                    assessments__batches=batch.id)
                    assess.append(answers.values("total_score")[0]["total_score"] if answers.exists() else 0)
            key = dat
            values = assess
            datasets.append(
                {
                    "label": key,
                    "backgroundColor": color_pick(datasets),
                    "data": values
                }
            )
        resp = bar_graph(trainees, datasets, batch.name.capitalize(), 20, "Trainees", "Scores", True)
        for index, trainee in enumerate(resp['data']['labels']):
            for mark in resp['data']['datasets']:
                trainees_details.append({"assessment": mark["label"], "marks": mark["data"][index]})
            trainees_assess.append({"trainee": trainee, "assessments": trainees_details})
            trainees_details = []
        respons = {"bar_graph": resp, "graph_info": {"batch_name": batch.name.capitalize(),
                                                     "total_trainees": total_trainees,
                                                     "trainee_details": trainees_assess}}
        batch_reports.append({batch.name: respons})
    return batch_reports


def full_batch_reports(batch):
    reports = []
    reports.append(individual_scores(batch))
    reports.append(batch_scores(batch))
    reports.append(assessments_scores(batch))
    return reports


def mail(users):
    send_mail('assessment cutoff', 'assessment is not passed', 'feedback@clusterit.io',
              users, fail_silently=False)


def individual_scores(batch):
    percents = []
    for trainee in Batch.objects.filter(id=batch).values_list('trainee', flat=True):
        scores = Answer.objects.filter(trainee=trainee,
                                       assessments__batches=batch).values_list('total_score', flat=True)
        maximum = len(scores) * 100
        scored = sum(scores)
        percent = scored / maximum * 100 if maximum != 0 else 0
        percents.append(
            {
                "batch": batch,
                "trainee": trainee,
                "percent": percent
            }
        )
    datasets, labels, total_data = generate_reports(percents, [batch])
    res = bar_graph(None, datasets, [Batch.objects.get(id=batch).name, "Score Percentage"], 20,
                    "Classification of Assessment Percentage", "Trainee Count", True)
    return res


def assessments_scores(batch):
    datasets = []
    filter_data = ASSESSMENT_LIST
    batches = Batch.objects.filter(id=batch)
    trainees = batches.values_list('trainee', flat=True)
    trainee_names = batches.values_list('trainee__first_name', flat=True)
    for data in filter_data:
        assess = []
        for trainee in trainees:
            answers = Answer.objects.filter(assessments__assmt__assessment_name=data,
                                            trainee=trainee, assessments__batches=batch)
            assess.append(answers.values("total_score")[0]["total_score"] if answers.exists() else 0)
        datasets.append(
            {
                "label": data,
                "backgroundColor": color_pick(datasets),
                "data": assess
            }
        )
    res = bar_graph(trainee_names, datasets, [Batch.objects.get(id=batch).name, "Trainee Scores"],
                    20, "Trainees", "Scores", True)
    return res


def batch_scores(batch):
    assessments = BatchAssessment.objects.filter(batches=batch)
    scored_dict = {
        "assessment": [assess.assmt.assessment_name for assess in assessments]
    }
    datasets, labels, total_data = generate_reports(assessments=assessments)
    d_data = bar_graph(scored_dict["assessment"], datasets,
                       [Batch.objects.get(id=batch).name, 'Assessment Scores'],
                       20, "Assessment Names", "Trainee Count", True)
    logger.info("batch base scores of assessments")
    return d_data


def batch_attendance(batch):
    percents = []
    today = date.today()
    batches = Batch.objects.get(id=batch)
    start_date = batches.start_date
    for trainee in batches.trainee.all():
        attendance = Attendance.objects.filter(schedule__range=(start_date, today), trainees=trainee)
        # total = attendance.count()
        atotal = (today - batches.start_date).days
        present = attendance.filter(schedule__range=(start_date, today), trainees=trainee,
                                    attendances='present').count()
        percent = present / atotal * 100 if atotal != 0 else 0
        percents.append(
            {
                "batch": batch,
                "trainee": trainee,
                "percent": percent
            }
        )
    datasets, labels, total_data = generate_reports(percents, [batch])
    res = bar_graph(None, datasets, "Attendance Percentage", 20,
                    "Classification of Attendance Percentage", "Trainee Count", True)
    logger.info("attendance report for trainer")
    return res


def answer(data):
    if data.get("answer_data"):
        answers = data.get("answer_data")[0]
        assess_data = data.get("total_data")
        timer = data.get("duration")
        qs_index = data.get("tabIndex")
        if timer is not None:
            sec = time.strptime(timer.split(',')[0],'%H:%M:%S')
            seconds = timedelta(hours=sec.tm_hour, minutes=sec.tm_min,
                                seconds=sec.tm_sec).total_seconds()
        duration = None
        if timer is None:
            timer = timer
            seconds = data.get("seconds")

        types = ["CTA", "MTF", "TRF", "FTB", "TR", "AR", "VR"]
        for qstype in types:
            if qstype in answers:
                if (qstype == "CTA") or (qstype == "FTB"):
                    answer = answers[qstype][0].pop("answers")
                    if qstype == "CTA":
                        cta = answers[qstype][0].pop("cta")
                elif qstype == "TRF":
                    if answers[qstype][0].get("trf_answers") is True or \
                            answers[qstype][0].get("trf_answers") is False:
                        answer = answers[qstype][0].pop("trf_answers")
                    else:
                        answer = ""

                elif qstype == "MTF":
                    answer = answers[qstype][0].pop("mtf_answers")
                else:
                    answer = answers[qstype][0].pop("answer") if answers[qstype][0].get("answer") else ""

        for ans in assess_data:
            for qstype in types:
                if qstype in ans:
                    ans_data = ans[qstype][0]
                    if (qstype == "CTA") or (qstype == "FTB"):
                        old_answer = ans_data.pop("answers")
                        if qstype == "CTA":
                            old_cta = ans_data.pop("cta")
                    elif qstype == "TRF":
                        old_answer = ans_data.pop("trf_answers")
                    elif qstype == "MTF":
                        old_answer = ans_data.pop("mtf_answers")
                    else:
                        old_answer = ans_data.pop("answer")

                    if answers == ans:
                        if (qstype == "CTA") or (qstype == "FTB"):
                            ans_data.update({"answers": answer})
                            if qstype == "CTA":
                                ans_data.update({'cta': cta})
                        elif qstype == "TRF":
                            ans_data.update({"trf_answers": answer})
                        elif qstype == "MTF":
                            ans_data.update({"mtf_answers": answer})
                        else:
                            if answer != "":
                                ans_data.update({"answer": answer})
                            else:
                                ans_data.update({"answer": old_answer})

                    else:
                        if (qstype == "CTA") or (qstype == "FTB"):
                            ans_data.update({"answers": old_answer})
                            if qstype == "CTA":
                                ans_data.update({'cta': old_cta})
                        elif qstype == "TRF":
                            ans_data.update({"trf_answers": old_answer})
                        elif qstype == "MTF":
                            ans_data.update({"mtf_answers": old_answer})
                        else:
                            ans_data.update({"answer": old_answer})

            if "duration" in ans.keys():
                duration = timer
                ans.update({"duration": timer, "seconds": seconds, "tabindex":qs_index})
        if duration is None:
            assess_data.append({"duration": timer, "seconds": seconds, "tabindex":qs_index})
        if "duration" in assess_data[-1]:
            data["total_data"] = assess_data[-1:] + assess_data[:-1]
        data["answer_data"] = data.get("total_data")
        return data
    else:
        data["answer_data"] = data.get("total_data")
        return data


def emptyAnswers(total_data):
    for data in total_data:
        if "FTB" in data:
            data["FTB"][0].update({"answers": ""})
        if "TRF" in data:
            data["TRF"][0].update({"trf_answers": ""})
        if "CTA" in data:
            data["CTA"][0].update({"answers": [], "cta": ""})
        if "MTF" in data:
            data["MTF"][0].update(
                {"mtf_answers": [
                    {"question": "", "answer": ""}, {"question": "", "answer": ""}]})
        if "TR" in data:
            data["TR"][0].update({"answer": ""})
        if "VR" in data:
            data["VR"][0].update({"answer": ""})
        if "AR" in data:
            data["AR"][0].update({"answer": ""})
    return total_data


def reviewAssessment(data):
    if data.get("answer_data"):
        answers = data.get("answer_data")[0]
        assess_data = data.get("total_data")
        types = ["CTA", "MTF", "TRF", "FTB", "TR", "AR", "VR"]
        for qstype in types:
            if qstype in answers:
                answer = answers[qstype][0].pop("marks")

        for ans in assess_data:
            for qstype in types:
                if qstype in ans:
                    ans_data = ans[qstype][0]
                    old_answer = ans_data.pop("marks")
                    if answers == ans:
                        ans_data.update({"marks": answer})
                    else:
                        ans_data.update({"marks": old_answer})
        data["total_data"] = assess_data
        data["answer_data"] = data["total_data"]
        return data


class CpcViewSet(viewsets.ModelViewSet):
    queryset = CpcEvaluate.objects.all()
    serializer_class = CpcSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_sfe_trainer:
            data = request.data
            if data.get("score"):
                if not self.queryset.filter(trainee=data["trainee"],
                                            cpbatch=data["cpbatch"],
                                            assessment_is=data["assessment_is"]).exists():
                    if int(data['trainee']) in Batch.objects.filter(
                            id=int(data['cpbatch'])).values_list('trainee', flat=True):
                        serializer = self.serializer_class(data=data)
                        if serializer.is_valid():
                            serializer.save(trainer=request.user)
                            answers = Answer.objects.filter(
                                trainee=data["trainee"], assessments=data["assessment_is"]
                            )
                            if not answers.exists():
                                Answer.objects.create(
                                    trainee=LmsUser.objects.get(id=data["trainee"]),
                                    assessments=BatchAssessment.objects.get(id=data["assessment_is"]),
                                    status="reviewed", total_score=data["score"], submit=True
                                )
                            return Response(serializer.data, status=status.HTTP_200_OK)
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    logger.error("trainee or trainer is not in batch")
                    return Response({"data": "Trainee or trainer is not in batch"},
                                    status=status.HTTP_400_BAD_REQUEST)
                logger.error("marks already gien for the trainee")
                return Response({"data": "marks already given for the trainee"},
                                status=status.HTTP_400_BAD_REQUEST)
            logger.error("score is required field")
            return Response({"data": "score is required field"}, status=status.HTTP_400_BAD_REQUEST)
        logger.error("user is not sfe trainer")
        return Response({"data": "user is not sfe trainer"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_trainee:
            files = self.queryset.filter(trainee=request.user)
        if request.user.is_sfe_trainer:
            files = self.queryset.filter(trainer=request.user)
        page = self.paginate_queryset(files)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            logger.info("field trip observation video of trainee ")
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(files, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, **kwargs):
        if request.user.is_sfe_trainer:
            data = request.data
            instance = self.queryset.get(pk=kwargs.get('pk'))
            serializer = self.serializer_class(instance, data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error("field trip is not updated: %s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "Sales Force trainer only can update the field study"},
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_sfe_trainer:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("Attendance data deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("Attendance data not deleted")
        return Response({"data": "Attendance data not deleted, permission denied"},
                        status=status.HTTP_400_BAD_REQUEST)
