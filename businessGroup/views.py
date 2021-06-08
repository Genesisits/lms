import logging

from datetime import datetime, timedelta

from rest_framework.views import APIView
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from user.models import LmsUser
from .models import Batch, BusinessGroup, Level, Module, BatchModuleActivation
from .serializers import (
    BatchSerializer, BusinessGroupSerializer,
    LevelSerializer, ModuleSerializer
)
from lms import constants
from notifications.models import EmailNotifications, EmailTemplates
from assessment.models import BatchAssessment, Answer
from material.models import Material

logger = logging.getLogger(__name__)


def bg_name(data: object, instance: object = None) -> object:
    """
    :param data:
    :param instance:
    :return:
    """
    business_group = BusinessGroup.objects.filter(name__iexact=data['name'].strip())
    # all_csm = BusinessGroup.objects.values_list("country_sales_manager__id", flat=True)
    if instance:
        business_group = business_group.exclude(id=instance.id)
        # all_csm = all_csm.exclude(id=instance.id)
    if business_group:
        raise Exception("Business Group with this name already exists")

    # Country sales manager must be business group specific

class BusinessGroupViewSet(viewsets.ModelViewSet):
    queryset = BusinessGroup.objects.all()
    serializer_class = BusinessGroupSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        group = BusinessGroup.objects.all()
        page = self.paginate_queryset(group)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(group, many=True)
        return Response(serializer.data)

    def create(self, request):
        if request.user.is_superuser:
            data = request.data
            try:
                if not bg_name(data, None):
                    serializer = self.serializer_class(data=data)
                    if serializer.is_valid():
                        serializer.save()
                        logger.info("business group created")
                        return Response(serializer.data)
                    logger.error("businessGroup creation error")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error("business group validation error")
                return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        logger.error("user is not admin")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        if request.user.is_superuser:
            data = request.data
            instance = BusinessGroup.objects.get(pk=kwargs.get('pk'))
            try:
                if not bg_name(data, instance):
                    serializer = self.serializer_class(instance, data)
                    if serializer.is_valid():
                        serializer.save()
                        logger.info("business group updated successfully")
                        return Response(serializer.data)
                    logger.error("business group updation error")
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error("business group validation error")
                return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        logger.error("user is not admin")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"data": "business group is not deleted, permission denied"}, status=status.HTTP_400_BAD_REQUEST)


def batch_create_validate(data, instance=None):
    group_name = BusinessGroup.objects.get(id=data.get("business_group"))
    print(group_name)
    c_trainer = data.get('course_trainer')
    # s_trainer = data.get('salesforce_trainer')
    if not data.get("refresher_course"):
        # if len(c_trainer) > group_name.course_trainer_count:
        #     raise Exception("you cannot add more than %s trainers" %group_name.course_trainer_count)
        # if len(s_trainer) > group_name.sfe_trainer_count:
        #     raise Exception("you cannot add more than %s trainers" % group_name.sfe_trainer_count)

        trainees = [name for name in data['trainee']]
        batches = Batch.objects.all()

        bg = batches.filter(business_group=data["business_group"])
        bg_trainee = bg.values_list("trainee__id", flat=True)

        if instance:
            bg = bg.exclude(id=instance.id)
            bg_trainee = bg.values_list("trainee__id", flat=True)

        # trainee cannot be in same business group

        # if not all(tr not in bg_trainee for tr in trainees):
        #     raise Exception("trainee is already in same business group")


class DetailView(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_superuser:
            s_date = datetime.strptime(request.data["start_date"], "%Y-%m-%d").date()
            bg = BusinessGroup.objects.get(id=request.data['business_group'])
            bg_days = bg.days
            if request.data.get("refresher_course"):
                e_date = s_date + timedelta(days=15)
            else:
                e_date = s_date + timedelta(days=bg_days)
            if not self.queryset.filter(name__iexact=request.data["name"].strip()).exists():
                data = request.data
                try:
                    if not batch_create_validate(data):
                        serializer = BatchSerializer(data=data)
                        if serializer.is_valid():
                            serializer.save(end_date=e_date)
                        notify_email("BATCH", "created", serializer.data["id"],
                                     {"batch": request.data["name"],
                                      "date": request.data["start_date"],
                                      "bg": serializer.data["businessGroup"]})
                        notify_email("BATCH", "assessments_list", serializer.data["id"],
                                     {"batch": request.data["name"],
                                      "bg": serializer.data["businessGroup"]})
                        notify_email("BATCH", "prerequisites", serializer.data["id"],
                                     {"batch": request.data["name"],
                                      "bg": serializer.data["businessGroup"]})
                        if serializer.data["is_active"] is True:
                            notify_email("BATCH", "started", serializer.data["id"],
                                         {"batch": request.data["name"],
                                          "bg": serializer.data["businessGroup"]})

                        bg = BusinessGroup.objects.filter(id=serializer.data['business_group'])
                        # for module in bg.values_list('levels__modules', flat=True):
                        #     BatchModuleActivation.objects.create(batch=Batch.objects.get(
                        #         id=serializer.data['id']), module=Module.objects.get(id=module))
                        #     logger.info("batch module activated")
                        return Response(serializer.data)
                except Exception as e:
                    logger.error("batch validation error")
                    return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
            logger.error("Batch name already exists")
            return Response({"error": "Batch name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        logger.error("user is not admin")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        batch = self.queryset
        query = {}
        if request.user.is_course_trainer:
            query['course_trainer'] = request.user

        # if request.user.is_sfe_trainer:
        #     query['salesforce_trainer'] = request.user

        if request.user.is_trainee:
            query['trainee'] = request.user

        if query:
            batch = self.queryset.filter(**query)
            trainer = request.query_params.get("trainer")
            if trainer:
                batch1 = batch.filter(course_trainer=trainer)
                # if len(batch1) == 0:
                #     batch2 = batch.filter(salesforce_trainer=trainer)
                #     batch = batch2
                # else:
                batch = batch1

        page = self.paginate_queryset(batch)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response({"data": "records not found"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        if request.user.is_superuser:
            data = request.data
            data['start_date'] = datetime.strptime(request.data["start_date"], "%d-%m-%Y").date()
            s_date = data["start_date"]
            bg = BusinessGroup.objects.get(id=request.data['business_group'])
            bg_days = bg.days
            if data.get("refresher_course"):
                e_date = s_date + timedelta(days=15)
            else:
                e_date = s_date + timedelta(days=bg_days)
            data["end_date"] = e_date
            instance = self.queryset.get(pk=kwargs.get('pk'))
            if not self.queryset.filter(name__iexact=data["name"]).exclude(id=instance.id).exists():
                try:
                    if not batch_create_validate(data, instance):
                        serializer = BatchSerializer(instance, data)
                        if serializer.is_valid():
                            serializer.save()
                            logger.info("batch is updated")
                            bg = BusinessGroup.objects.filter(id=serializer.data['business_group'])
                            # for module in bg.values_list('levels__modules', flat=True):
                            #     if not BatchModuleActivation.objects.filter(batch=serializer.data['id'],
                            #                                                 module=module).exists():
                            #         BatchModuleActivation.objects.create(batch=Batch.objects.get(
                            #             id=serializer.data['id']), module=Module.objects.get(id=module))
                            #         logger.info("batch module activated")
                            return Response(serializer.data)
                        logger.error("error in batch updation")
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                except Exception as e:
                    logger.error("batch validation error")
                    return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
            logger.error("batch name already exists")
            return Response({"error": "Same name already exists for other batch"},
                            status=status.HTTP_400_BAD_REQUEST)
        logger.error("user is not admin")
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("batch is deleted")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("batch is not deleted")
        return Response({"data": "batch is not deleted"}, status=status.HTTP_400_BAD_REQUEST)


class TraineeListView(APIView):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            if request.user.is_course_trainer:
                batches = self.queryset.filter(course_trainer=request.user)

            # elif request.user.is_sfe_trainer:
            #     batches = self.queryset.filter(salesforce_trainer=request.user)

            trainees = batches.values("trainee__id", "trainee__first_name", "trainee__last_name")
            return Response(trainees, status=status.HTTP_200_OK)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)


class UserDetailsViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = (permissions.IsAuthenticated,)

    @staticmethod
    def sfe_course_details(data, batches):
        """
            Function to return details of SFE/Course Trainer.
        :param data: request queryset data
        :return: Json Response
        """
        logger.info("Requested Data to Search:: %s", data)
        batch = batches.filter(**data)
        trainees_list = LmsUser.objects.filter(id__in=batch.values_list("trainee")).count()
        return Response({"batches": batch.count(), "trainees": trainees_list}, status=status.HTTP_200_OK)
    
    def list(self, request):
        if request.user.is_course_trainer:
            return self.sfe_course_details({"course_trainer": request.user}, self.queryset)
        
        # elif request.user.is_sfe_trainer:
        #     return self.sfe_course_details({"salesforce_trainer": request.user}, self.queryset)
        
        else:
            batches = self.queryset.filter(trainee=request.user)
            details = batches.values(
                "name", "course_trainer__id",
                "course_trainer__first_name",
                "course_trainer__last_name",
            )
            return Response({"data": details}, status=status.HTTP_200_OK)
        return Response({"data": "No records Found"}, status=status.HTTP_204_NO_CONTENT)


class ModuleView(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        if request.user.is_superuser:
            if not self.queryset.filter(name__iexact=request.data["name"].strip()).exists():
                data = request.data
                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                    logger.info("module is created")
                    return Response(serializer.data)
                logger.error("module creation error")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            logger.error("module already exists")
            return Response({"data": "module with this name already exists"},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        if request.user.is_superuser:
            data = request.data
            instance = self.queryset.get(pk=kwargs.get('pk'))
            if not self.queryset.filter(name__iexact=request.data["name"].strip()).exclude(id=instance.id).exists():
                serializer = ModuleSerializer(instance, data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                logger.error("module updation error::%s" % serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response(constants.MODULE_EXISTS_MSG, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("module is not deleted")
        return Response(status=status.HTTP_410_GONE)


class LevelView(viewsets.ModelViewSet):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def list(self, request):
        page = self.paginate_queryset(self.queryset)
        if page is not None:
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(self.queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        if not self.queryset.filter(name__iexact=request.data["name"].strip()).exists():
            if request.user.is_superuser:
                data = request.data
                serializer = self.serializer_class(data=data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                logger.error("level creation error::%s"%serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data":"Level already exists"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        if request.user.is_superuser:
            data = request.data
            instance = self.queryset.get(pk=kwargs.get('pk'))
            if not self.queryset.filter(name__iexact=request.data["name"].strip()).exclude(id=instance.id).exists():
                serializer = self.serializer_class(instance, data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(serializer.data)
                logger.error("level updation errors:: %s" % serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            return Response({"data":"Level already exists"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("level deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"data": "Level delete failed"}, status=status.HTTP_400_BAD_REQUEST)


def assessment_dates(bg):
    """
        Assessments of the group

    :param bg: Business Group
    :return: List of Assessment lists
    """
    if bg == "spine and biologics":
        return format_data_to_string(constants.spine_surgery)
    
    if bg == "surgical synergy":
        return format_data_to_string(constants.spine_surgery)
        
    if bg == "trauma":
        return format_data_to_string(constants.taruma)
    
    if bg == "neurosurgery":
        return format_data_to_string(constants.neurosur)
    
    if bg == "neurovascular":
        return format_data_to_string(constants.neuroscular)
 
    if bg == "neuromodulation":
        return format_data_to_string(constants.neuro_module)
       
    if bg == "ent":
        return format_data_to_string(constants.ent)


def format_data_to_string(dataset):
    """
    
    :param dataset:
    :return:
    """
    data = ""
    for row in dataset:
        for col in row["assign"]:
            data += constants.trigger_str.format(assign=col, weeks=row['weeks'])
    data += constants.assessment_str
    return data


def get_module_users_query(users, admin=None, id=id):
    """
        Functionality to return Batch Users
    :param users: Users Object
    :param admin: Admin Object
    :return: Queryset of Users....
    """
    batch = Batch.objects.filter(id=id)
    trainees = users.filter(id__in=batch.values("trainee"))
    course_trainer = users.filter(id__in=batch.values("course_trainer"))
    # sfe_trainer = users.filter(id__in=batch.values("salesforce_trainer"))
    # csm = users.filter(id__in=batch.values("business_group__country_sales_manager"))
    training_head = users.filter(is_training_head=True)
    results = trainees.union(course_trainer, training_head)
    if admin:
        results.union(admin)
    return results


def get_assessment_users(users, admin, purpose, id=id):
    """
        Functionality to return Users for Assessment....
    :param users:
    :param admin:
    :param purpose:
    :return:
    """
    training_head = users.filter(is_training_head=True)
    assessment = BatchAssessment.objects.filter(id=id)

    if purpose == "created":
        batch = Batch.objects.filter(id=id)

    if purpose in ["approval", "activate", "not_submitted"]:
        batch = Batch.objects.filter(id__in=assessment.values("batches"))

    csm = users.filter(id__in=batch.values("business_group__country_sales_manager"))
    if purpose == "created":
        return csm.union(admin, training_head)

    trainer = users.filter(id__in=assessment.values("trainer"))
    if purpose == "activate":
        trainees = users.filter(id__in=batch.values("trainee"))
        return trainees

    if purpose in ["approval", "activate"]:
        return trainer.union(csm, training_head)

    if purpose == "not_submitted":
        trainees = LmsUser.objects.none()
        for trainee in batch.values("trainee"):
            if trainee not in Answer.objects.filter(
                    status__in=["completed", "reviewing", "reviewed"],
                    trainee=trainee["trainee"], assessments=id).values("trainee"):
                trainees.union(LmsUser.objects.filter(id=trainee["trainee"]))
        return csm.union(training_head, trainer, admin, trainees)


def notify_email(module, purpose, id, required_for=None):
    """
        Functionality to Trigger Email Notifications.
    :param module: Module for Sending Email Notification
    :param purpose: Purpose of the Email notification (Create/Update/Delete/Start/..)
    :param id: Id of the Respective object(Batch ID/ Assessment ID/ User ID,..)
    :param required_for: Extra parameters to send notification to specific users.
    :return: None
    """
    query = {}
    template = EmailTemplates.objects.get(model=module, purpose=purpose)

    users = LmsUser.objects.all()
    admin = users.filter(is_superuser=True)

    if module == "USER" and purpose == "created":
        query = LmsUser.objects.filter(id=id)

    if module == "BATCH" and purpose in ["created", "started"]:
        if purpose == "started":
            query = get_module_users_query(users, admin, id=id)
        else:
            query = get_module_users_query(users, id=id)

    if module == "BATCH" and purpose == "prerequisites":
        batch = Batch.objects.filter(id=id)
        query = users.filter(id__in=batch.values("trainee"))

    if module == "BATCH" and purpose == "assessments_list":
        batch = Batch.objects.filter(id=id)
        course_trainer = users.filter(id__in=batch.values("course_trainer"))
        # sfe_trainer = users.filter(id__in=batch.values("salesforce_trainer"))
        # query = course_trainer.union(sfe_trainer)

    if module == "MATERIAL" and purpose == "created":
        batch = Batch.objects.filter(id=id)
        csm = users.filter(id__in=batch.values("business_group__country_sales_manager"))
        training_head = users.filter(is_training_head=True)
        query = csm.union(training_head, admin)

    if module == "MATERIAL" and purpose == "approval":
        material = Material.objects.filter(id=id)
        batch = Batch.objects.filter(id__in=material.values("as_batch"))
        training_head = users.filter(is_training_head=True)
        csm = users.filter(id__in=batch.values("business_group__country_sales_manager"))
        trainer = users.filter(id__in=material.values("user"))
        query = trainer.union(csm, training_head)

    if (module == "ASSESSMENT" and
            purpose in ["created", "approval", "activate", "not_submitted"]):
        query = get_assessment_users(users, admin, purpose, id=id)

    if module == "ASSESSMENT" and purpose == "deadline":
        assessment = BatchAssessment.objects.filter(id=id)
        batch = Batch.objects.filter(id__in=assessment.values("batches"))
        query = users.filter(id__in=batch.values("trainee"))

    if module == "ASSESSMENT" and purpose in ["required_cutoff", "assessment_completed"]:
        answer = Answer.objects.filter(id=id)
        batch = Batch.objects.filter(id__in=answer.values("assessments__batches"))
        trainee = users.filter(id__in=answer.values("trainee"))
        trainer = users.filter(id__in=answer.values("assessments__trainer"))
        training_head = users.filter(is_training_head=True)
        csm = users.filter(id__in=batch.values("business_group__country_sales_manager"))
        if purpose == "requires_cutoff":
            query = trainee.union(trainer, training_head, csm)
        if purpose == "assessment_completed":
            query = trainer.union(training_head, csm)

    insert_list = []
    for user in query:
        insert_list.append(EmailNotifications(template=template, users=user,
                                              required_data=required_for))
    EmailNotifications.objects.bulk_create(insert_list)
