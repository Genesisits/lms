import logging
import random
import string

from datetime import date

from django.contrib.auth import logout as django_logout
from rest_framework.views import APIView
from rest_framework_simplejwt import authentication
from rest_framework.response import Response
from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.pagination import LimitOffsetPagination
from rest_framework_simplejwt.views import TokenViewBase
from assessment.views import scores_list, bar_graph, color_pick, generate_reports, \
    individual_scores, batch_scores, batch_attendance, assessments_scores
from .serializers import *
from businessGroup.models import BusinessGroup
from assessment.models import *
from businessGroup.views import notify_email
from .validations import *
from django.db.models.query_utils import Q
from django.contrib.auth.tokens import default_token_generator
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.views.decorators.debug import sensitive_post_parameters

logger = logging.getLogger(__name__)
UserModel = get_user_model()

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'new_password1', 'new_password2',
    ),
)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)
    authentication_classes = (authentication.JWTAuthentication,)

    def post(self, request):
        django_logout(request)
        logger.info("logged out successfully")
        return Response(status=204)


class TrainerViewSet(viewsets.ModelViewSet):
    queryset = LmsUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        if request.user.is_superuser and self.request.query_params.get("email"):
            if not self.queryset.filter(email=self.request.query_params.get("email")).exists():
                return Response({"data": "No matching email found"}, status=status.HTTP_200_OK)
            return Response(
                {"data": "A Email already associated to this account"}, status=status.HTTP_409_CONFLICT
            )

        bg = request.query_params.get("bg")
        refresher = request.query_params.get("refresher")
        bg_name = request.query_params.get("bg_name")
        batch = request.query_params.get("batch")
        csm = request.query_params.get("csm")
        if request.user.is_superuser or request.user.is_sfe_trainer or request.user.is_course_trainer:
            if bg:
                query = LmsUser.objects.all()
                all_batches = Batch.objects.all()
                batches = all_batches.filter(business_group=bg, refresher_course=False)
                trainers = query.filter(Q(is_course_trainer=True) | Q(is_sfe_trainer=True))
                bg_trainees = batches.values_list("trainee", flat=True)
                trainees = query.filter(is_trainee=True)
                # if bg and refresher:
                #     trainees = query.filter(is_trainee=True)
                # else:
                #     trainees = query.filter(is_trainee=True).exclude(id__in=bg_trainees)
                if batch:
                    batch_trainees = query.filter(
                        id__in=Batch.objects.filter(id=batch).values_list("trainee", flat=True))
                    trainees = trainees | batch_trainees
                users = trainers | trainees
            elif csm and bg_name:
                if bg_name.lower() == "refreshment course":
                    users = self.queryset.filter(is_country_sales_manager=True)
                else:
                    bg_no_csm = BusinessGroup.objects.filter(country_sales_manager=None).values_list("id", flat=True)
                    bg_csm = BusinessGroup.objects.all().exclude(id__in=bg_no_csm).values_list("country_sales_manager", flat=True)
                    users = self.queryset.filter(is_country_sales_manager=True).exclude(id__in=bg_csm)
            else:
                users = self.queryset

            page = self.paginate_queryset(users)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(users, many=True, context={'request': request})
            return Response(serializer.data)
        else:
            serializer = UserSerializer(request.user, context={'request': request})
            return Response(serializer.data)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request):
        if request.user.is_superuser:
            if not self.queryset.filter(
                    Q(mobile_number=request.data["mobile_number"]) |
                    Q(email=request.data["email"]) |
                    Q(username=request.data["username"])).exists():
                pwd = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))
                data = request.data
                data['password'] = pwd
                try:
                    serializer = UserSerializer(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        if not data["is_training_head"] or not data["is_country_sales_manager"]:
                            notify_email(module="USER", purpose="created", id=serializer.data["id"],
                                         required_for={"password": pwd, "email": request.data["email"]})
                        return Response(serializer.data, status=status.HTTP_200_OK)
                    logger.error("user creation error:: %s" % serializer.errors)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error("material size validation error")
                    return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
            elif self.queryset.filter(Q(mobile_number=request.data["mobile_number"])).exists():
                logger.info("User with Same Details exists")
                return Response({"data": "Mobile Number already exists"}, status=status.HTTP_400_BAD_REQUEST)
            elif self.queryset.filter(Q(email=request.data["email"])).exists():
                logger.info("User with Same Details exists")
                return Response({"data": "Email Id already exists"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)

    def update(self, request, **kwargs):
        data = request.data
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = UserSerializer(instance, data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status.HTTP_200_OK)
        logger.error("user update error: %s" % serializer.errors)
        return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("user is not deleted")
        return Response({"data": "unable to delete User"}, status.HTTP_403_FORBIDDEN)


class DashboardView(APIView):
    queryset = LmsUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.is_superuser:
            ctrainer = self.queryset.filter(is_course_trainer=True).count()
            strainer = self.queryset.filter(is_sfe_trainer=True).count()
            tot_trainer = ctrainer + strainer
            return Response(
                {
                    'trainee_list': LmsUser.objects.filter(is_trainee=True).count(),
                    'ctrainer_list': ctrainer,
                    'strainer_list': strainer,
                    'trainers': tot_trainer,
                    'bg_list': BusinessGroup.objects.all().count(),
                    'Batches': Batch.objects.all().count(),
                    'users': LmsUser.objects.all().count()
                }
            )
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)


class MyProfileViewSet(viewsets.ModelViewSet):
    queryset = LmsUser.objects.all()
    serializer_class = MyInfoSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        serializer = self.serializer_class(request.user, context={'request': request})
        logger.info("user data")
        return Response(serializer.data)

    def update(self, request, **kwargs):
        data = request.data
        instance = LmsUser.objects.get(pk=kwargs.get('pk'))
        if data.get('image') or instance.image:
            try:
                validate_image_extension(data.get("image"))
                serializer = self.serializer_class(instance, data, context={'request': request})
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                logger.error("User update error: %s" % serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = UpgradeSerializer(instance, data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            logger.error("User update error: %s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.error("user updation error")
        return Response({"data": "user update error"}, status=status.HTTP_400_BAD_REQUEST)


class UpgradeUserView(viewsets.ModelViewSet):
    queryset = LmsUser.objects.all()
    serializer_class = UpgradeSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        # Unable to get all users when using self.query_set as per the bug
        # https: // trello.com / c / eFuPtnqA / 213
        # So calling all objects
        users = LmsUser.objects.all()
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data)

    def update(self, request, **kwargs):
        data = request.data
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if not self.queryset.filter(mobile_number=data["mobile_number"]).exclude(id=instance.id).exists():
            serializer = AdminUpgradeSerializer(instance, data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error("upgrade serializer error: %s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_200_OK)
        logger.info("mobile number already exists: %s" % data)
        return Response({"data": "Mobile Number already exists"}, status=status.HTTP_400_BAD_REQUEST)


class QuestionFeedView(viewsets.ModelViewSet):
    queryset = QuestionFeed.objects.all()
    serializer_class = QuestionfeedSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_superuser:
            data = request.data
            serializer = self.serializer_class(data=data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            logger.error("question creation error: %s" % serializer.errors)
            return Response(serializer.errors, status.HTTP_400_BAD_REQUEST)
        logger.error("permission denied")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_superuser or request.user.is_trainee:
            serializer = self.serializer_class(QuestionFeed.objects.all(), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error("permission denied")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        data = request.data
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            serializer = self.serializer_class(instance, data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error("question update error")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.error("permission denied")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("question is not deleted")
        return Response(status=status.HTTP_403_FORBIDDEN)


class AnswerfeedView(viewsets.ModelViewSet):
    queryset = AnswerFeed.objects.all()
    serializer_class = AnswerfeedSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_trainee:
            data = request.data
            if not self.queryset.filter(
                    trainee=request.user.id, trainer=data["trainer"],
                    module=data["module"]).exists():
                d_data = []
                for row in data['question']:
                    d_data.append(
                        {
                            "trainer": data.get('trainer'),
                            "module": data.get('module'),
                            "batch": data.get('batch'),
                            "question": row.get('question'),
                            "feedback_answers": row.get('answer'),
                            "comment": row.get('comment')
                        }
                    )
                serializer = self.serializer_class(data=d_data, many=True)
                if serializer.is_valid():
                    serializer.save(trainee=request.user)
                    return Response(serializer.data)
                logger.error("answer creation error: %s" % serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {"ERROR": "Trainee already gave feedback to this trainer for this module"},
                status=status.HTTP_400_BAD_REQUEST
            )
        logger.error("permission denied")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_superuser:
            serializer = self.serializer_class(AnswerFeed.objects.all(), many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        logger.error("Error Permission Denied for fetching Answers")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        data = request.data
        instance = self.queryset.get(pk=kwargs.get('pk'))
        if request.user.is_superuser or request.user.is_trainee:
            serializer = self.serializer_class(instance, data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data)
            logger.error("Answer update error:%s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        logger.error("permission denied")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("answer deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"data": "answer is not deleted, permission denied"},
                        status=status.HTTP_400_BAD_REQUEST)


class MyTokenObtainPairView(TokenViewBase):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = MyTokenObtainPairSerializer


token_obtain_pair = MyTokenObtainPairView.as_view()


class TrainerEffectivenessView(viewsets.ModelViewSet):
    queryset = AnswerFeed.objects.all()
    serializer_class = AnswerfeedSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        if request.user.is_superuser:
            batch = request.query_params.get("batch")
            module = request.query_params.get("module")
            batch_obj = Batch.objects.filter(id=batch)
            ct = list(batch_obj.values_list('course_trainer', flat=True))
            sft = list(batch_obj.values_list('salesforce_trainer', flat=True))
            total_trainees = len(list(batch_obj.values_list('trainee', flat=True)))
            respond_trainees = []
            trainers = []
            trainers.extend(ct)
            trainers.extend(sft)
            t_list = []
            net_scorelist = []
            datasets = []
            bg_color = []

            for trainer in trainers:
                feedbacks = self.queryset.filter(trainer=trainer, module=module, batch=batch, question=5)
                promotors = feedbacks.filter(feedback_answers__in=[9, 10]).count()
                detractors = feedbacks.filter(feedback_answers__in=[0, 1, 2, 3, 4, 5, 6]).count()
                trainees = len(set(feedbacks.values_list('trainee', flat=True)))
                respond_trainees.append({"trainer": LmsUser.objects.get(id=trainer).first_name,
                                         "trainees": trainees})
                net_score = ((promotors - detractors) / trainees) * 100 if trainees != 0 else 0
                t_list.append(LmsUser.objects.get(id=trainer).username)
                net_scorelist.append(net_score)
                bg_color.append(color_pick(datasets))

            datasets.append(
                {
                    "label": "feedback Score",
                    "backgroundColor": bg_color,
                    "data": net_scorelist
                }
            )
            resp = bar_graph(t_list, datasets, "TrainerEffectivenessView", 20, "Trainers", "Feedback Percentage", False)
            info = {"batch": batch_obj.get(id=batch).name,
                    "total_trainees": total_trainees, "responded_trainees": respond_trainees}
            return Response({"graph": resp, "info": info}, status=status.HTTP_200_OK)
        logger.error("user is not admin")
        return Response({"data": "user must be admin"}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(viewsets.ModelViewSet):
    queryset = LmsUser.objects.all()
    serializer_class = ChangePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, **kwargs):
        data = request.data
        instance = self.queryset.get(pk=kwargs.get('pk'))
        serializer = self.serializer_class(instance, data)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": "password changed successfully"}, status=status.HTTP_200_OK)
        logger.error("password update error: %s" % serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def bg_donut_reports():
    bgl = []
    bgs = BusinessGroup.objects.all()
    for bg in bgs:
        batch = Batch.objects.filter(business_group=bg.id)
        if len(batch) != 0:
            bgl.append(bg.id)
    results = []
    c_trainees = []
    completed_trainees = []
    bg_names = bgs.filter(id__in=bgl).values_list("name", flat=True)
    for bg in bgl:
        complete_trainees = 0
        batch = Batch.objects.filter(business_group=bg)
        trainees = batch.values_list('trainee', flat=True)
        c_trainees.append(trainees.count())
        for x in trainees:
            score_data = scores_list(x, bg)
            myvalues = [i['trainee_status'] for i in score_data if 'trainee_status' in i]
            if myvalues[0] == "CLEARED":
                complete_trainees += 1
        completed_trainees.append(complete_trainees)

    # d_data = {
    #         "total_trainees": c_trainees,
    #         "completed_trainees": completed_trainees
    #     }
    data = {
        "labels": bg_names,
        "datasets": [
            {
                "label": "Total_Trainees",
                "backgroundColor": '#199C49',
                "data": c_trainees
            },

            {
                "label": "Completed_Trainees",
                "backgroundColor": '#338AFF',
                "data": completed_trainees
            },
        ]
    }
    results.append(
        {
            "data": data,
            "options": {
                "scales": {
                    "xAxes": [
                        {"ticks": {"beginAtZero": True,
                                   "stepSize": 2},
                         "scaleLabel": {
                             "display": True,
                             "labelString": "Business Groups"
                         }
                         },
                    ],
                    "yAxes": [
                        {"ticks": {"beginAtZero": True,
                                   "stepSize": 2},
                         "scaleLabel": {
                             "display": True,
                             "labelString": "Trainee Count"
                         }
                         },
                    ]
                },
                "title": {
                    "display": True,
                    # "text": bg.name
                }
            }
        }
    )
    return results


def assessments_percentage(trainer):
    """
        report for batch and scores of Assessment in trainer portal
    :param request:
    :return:
    """
    if trainer.is_course_trainer or trainer.is_sfe_trainer:
        d_data = []
        if trainer.is_course_trainer:
            trainer = trainer
            batches = Batch.objects.filter(course_trainer=trainer)
        if trainer.is_sfe_trainer:
            trainer = trainer
            batches = Batch.objects.filter(salesforce_trainer=trainer)
        for batch in batches:
            assessments = BatchAssessment.objects.filter(batches=batch)

            scored_dict = {
                "assessment": [assess.assmt.assessment_name for assess in assessments]
            }
            datasets = generate_reports(assessments=assessments)
            d_data.append(bar_graph(scored_dict["assessment"], datasets,
                                    "Assessment Scores", 5, "assessments", "", True))
        return d_data


def prepair_report(timespan, request):
    today = date.today()

    if (today.month - timespan) < 1:
        start_date = date(
            today.year - (int((today.month - timespan) / 12) + 1),
            today.month - timespan + 12, today.day
        )
    else:
        start_date = date(today.year, today.month - timespan, today.day)

    percents = []

    if request.user.is_superuser:
        batches = Batch.objects.filter(end_date__gte=start_date)

    if request.user.is_course_trainer or request.user.is_sfe_trainer:
        batches = Batch.objects.filter(
            Q(course_trainer=request.user, is_active=True) |
            Q(course_trainer=request.user, end_date__gte=start_date) |
            Q(salesforce_trainer=request.user, is_active=True) |
            Q(salesforce_trainer=request.user, end_date__gte=start_date)
        )
    total_batches = len(batches)
    trainees_details = []
    batch_trainees = []
    for batch in batches:
        trainees = Batch.objects.filter(name=batch).values_list('trainee', flat=True)
        batch_trainees.append({"batch": batch.name, "trainees": len(trainees)})
        for trainee in trainees:
            scores = Answer.objects.filter(assessments__batches=batch,
                                           trainee=trainee).values_list('total_score', flat=True)
            maximum = len(scores) * 100
            scored = sum(scores)
            percent = scored / maximum * 100 if maximum != 0 else 0
            user = LmsUser.objects.get(id=trainee)
            percents.append({"batch": batch, "trainee": user.first_name + " " + user.last_name, "percent": percent})
    datasets, labels, total_data = generate_reports(percents=percents, batches=batches)
    resp = bar_graph(labels, datasets,
                     "Score Percentage", 20, "Batch Names", "Trainee Count", True)
    for mark in resp['data']['datasets']:
        for index, batche in enumerate(resp['data']['labels']):
            trainees_details.append({"batch": batche, "label": mark["label"], "trainees": mark["data"][index]})
    for detail in trainees_details:
        users = []
        for label in total_data:
            if detail['label'] == label['label']:
                for trainee in label['trainees']:
                    if detail['batch'] == trainee['batch']:
                        users.append(trainee['trainee'])
        detail.update({"users": users})
    respons = {"bar_graph": resp, "graph_info": {"total_batches": total_batches,
                                                 "total_trainees": batch_trainees,
                                                 "trainee_details": trainees_details}}
    return respons


def consolidated_graphs(timespan1, timespan2):
    batches = Batch.objects.filter(end_date__gte=timespan1, start_date__lte=timespan2)
    reports = []
    for batch in batches:
        trainee_scores = individual_scores(batch.id)
        assessments_trainees = assessments_scores(batch.id)
        batch_trainees = batch_scores(batch.id)
        batch_trainees_attendance = batch_attendance(batch.id)
        reports.append({batch.name: [trainee_scores, assessments_trainees, batch_trainees, batch_trainees_attendance]})
    return reports


def total_percentage(timespan, request):
    today = date.today()

    if (today.month - timespan) < 1:
        start_date = date(
            today.year - (int((today.month - timespan) / 12) + 1),
            today.month - timespan + 12, today.day
        )
    else:
        start_date = date(today.year, today.month - timespan, today.day)

    if request.user.is_superuser:
        batches = Batch.objects.filter(end_date__gte=start_date, is_active=True)

    if request.user.is_course_trainer or request.user.is_sfe_trainer:
        batches = Batch.objects.filter(
            Q(course_trainer=request.user, is_active=True) |
            Q(course_trainer=request.user, end_date__gte=start_date) |
            Q(salesforce_trainer=request.user, is_active=True) |
            Q(salesforce_trainer=request.user, end_date__gte=start_date)
        )
    total_batches = len(batches)
    trainees_details = []
    batch_trainees = []
    overall_technical_score = []
    overall_softskills_score = []
    trainees_names = []
    for batch in batches:
        trainees = Batch.objects.filter(name=batch.name).values_list('trainee', flat=True)
        batch_trainees.append({"batch": batch.name, "trainees": len(trainees)})
        for trainee in trainees:
            scores = scores_list(trainee, batch.business_group, batch.id)
            for i in scores:
                technical = i['overall_technical'] if 'overall_technical' in i else 0
                softskills = i['overall_soft_skills'] if 'overall_soft_skills' in i else 0
            overall_technical_score.append(technical)
            overall_softskills_score.append(softskills)
            user = LmsUser.objects.get(id=trainee)
            trainee_name = user.first_name + " " + user.last_name
            trainees_names.append(trainee_name)
            trainees_details.append({"batch": batch.name, "trainee": trainee_name,
                                     "o_technical": technical, "o_softskills": softskills})
    data = {
        "labels": trainees_names,
        "datasets": [
            {
                "label": "overall_technical_score",
                "backgroundColor": '#199C49',
                "data": overall_technical_score
            },

            {
                "label": "overall_softskills_score",
                "backgroundColor": '#338AFF',
                "data": overall_softskills_score
            },
        ]
    }
    results = {
        "data": data,
            "options": {
                "scales": {
                    "xAxes": [
                        {"ticks": {"beginAtZero": True,
                                   "stepSize": 2},
                         "scaleLabel": {
                             "display": True,
                             "labelString": "Trainees"
                         }
                         },
                    ],
                    "yAxes": [
                        {"ticks": {"beginAtZero": True,
                                   "stepSize": 2},
                         "scaleLabel": {
                             "display": True,
                             "labelString": "Overall Percentages"
                         }
                         },
                    ]
                },
                "title": {
                    "display": True,
                }
            }
        }
    d_data = {"bar_graph": results, "graph_info": {"total_batches": total_batches,
                                                   "trainees": batch_trainees,
                                                   "trainee_details": trainees_details}}
    return d_data


def batches_count():
    bgl = []
    bgs = BusinessGroup.objects.all()
    for bg in bgs:
        batch = Batch.objects.filter(business_group=bg.id)
        bgl.append(len(batch))
    bg_names = bgs.values_list("name", flat=True)
    data = {
        "labels": bg_names,
        "datasets": [
            {
                "label": "Batches Count",
                "backgroundColor": random.sample(constants.GRAPH_COLORS, len(bgl)),
                "data": bgl
            },
        ]
    }
    results = {
            "data": data,
            "options": {
                "responsive": "true",
                "title": {
                    "display": "true",
                    "position": "top",
                    "text": "Trainings in Shiksha",
                    "fontSize": 18,
                    "fontColor": "#111"
                },
                "legend": {
                    "display": "true",
                    # "position": "bottom",
                    "labels": {
                        "fontColor": "#333",
                        "fontSize": 16
                    }
                }
            }
        }
    return results


def batches_user_count():
    bgl = []
    users = []
    bgs = BusinessGroup.objects.all()
    for bg in bgs:
        batch = Batch.objects.filter(business_group=bg.id)
        bgl.append(len(batch))
        users.append(len(batch.values("course_trainer", "trainee")))
    bg_names = bgs.values_list("name", flat=True)
    data = {
        "labels": bg_names,
        "datasets": [
            {
                "label": "Trainings Done",
                # "backgroundColor": random.sample(constants.GRAPH_COLORS, len(bgl)),
                "data": bgl,
                "borderColor": "#3e95cd",
                "fill": "false"
            },
            {
                "label": "Employees Engaged",
                # "backgroundColor": random.sample(constants.GRAPH_COLORS, len(bgl)),
                "data": users,
                "borderColor": "#8e5ea2",
                "fill": "false"
            },
        ]
    }
    results = {
            "data": data,
            "options": {
                "responsive": "true",
                "title": {
                    "display": "true",
                    "position": "top",
                    "text": "Employees Engaged / Trainings Done",
                    "fontSize": 18,
                    "fontColor": "#111"
                },
                "legend": {
                    "display": "true",
                    "position": "bottom",
                    "labels": {
                        "fontColor": "#333",
                        "fontSize": 16
                    }
                }
            }
        }
    return results


class PasswordResetView(GenericAPIView):

    """
    Calls Django Auth PasswordResetForm save method.
    Accepts the following POST parameters: email
    Returns the success/fail message.
    """

    serializer_class = PasswordResetSerializer
    permission_classes = (AllowAny,)
    allowed_methods = ('POST', 'GET', 'OPTIONS', 'HEAD')

    def post(self, request, *args, **kwargs):
        # Create a serializer with request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()
        # Return the success message with OK HTTP status
        return Response(
            {"success": "Password reset e-mail has been sent."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(GenericAPIView):

    """
    Password reset e-mail link is confirmed, therefore this resets the user's password.
    Accepts the following POST parameters: new_password1, new_password2
    Accepts the following Django URL arguments: token, uid
    Returns the success/fail message.
    """

    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)
    token_generator = default_token_generator
    form_class = SetPasswordForm
    allowed_methods = ('POST', 'GET', 'OPTIONS', 'HEAD')

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": "Password has been reset with the new password."})
