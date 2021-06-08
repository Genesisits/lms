import logging

from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.pagination import LimitOffsetPagination

from user.models import LmsUser
from businessGroup.models import Batch
from .serializers import MaterialSerializer, AdminSerializer, FieldStudySerializer
from .models import Material, FieldStudyObservation
from assessment.models import Answer, BatchAssessment
from businessGroup.views import notify_email

logger = logging.getLogger(__name__)


class MaterialView(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            if request.data.get('newbatch'):
                try:
                    instance = Material.objects.get(pk=request.data.get('pk'))
                    batch = Batch.objects.get(id=request.data.get('newbatch'))
                    logger.info("material Copy Started")
                    instance.pk = None
                    instance.id = None
                    instance.save()
                    instance.as_batch = batch
                    instance.save()
                    serializer = MaterialSerializer(instance, many=True, context={'request': request})
                    logger.info("material Copy done")
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                except Exception as e:
                    logger.error("material size validation error")
                    return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
            try:
                serializer = self.serializer_class(data=request.data, context={'request': request})
                if serializer.is_valid():
                    serializer.save(user=request.user)
                    notify_email(module="MATERIAL", purpose="created", id=serializer.data["as_batch"],
                                 required_for={"batch": serializer.data["batch"]})
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                logger.error("material serializer error: %s" % serializer.errors)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error("material size validation error")
                return Response({"data": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "no data found"}, status=status.HTTP_200_OK)

    def list(self, request):
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            assignment = Material.objects.filter(user=request.user)
            page = self.paginate_queryset(assignment)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                logger.info("material list")
                return self.get_paginated_response(serializer.data)
        elif request.user.is_superuser:
            page = self.paginate_queryset(self.queryset)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                logger.info("material_list")
                return self.get_paginated_response(serializer.data)
        else:
            batch = Batch.objects.filter(trainee=request.user)
            assignment = Material.objects.filter(as_batch__in=batch, file_status='approved'.upper())
            page = self.paginate_queryset(assignment)
            if page is not None:
                serializer = self.serializer_class(page, many=True, context={'request': request})
                logger.info("material_list")
                return self.get_paginated_response(serializer.data)
            serializer = MaterialSerializer(assignment, many=True, context={'request': request})
            return Response(serializer.data)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        data = request.data
        instance = Material.objects.get(pk=kwargs.get('pk'))
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            serializer = MaterialSerializer(instance, data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.info("Error while uploading material: %s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif request.user.is_superuser:
            if data["file_status"] == "APPROVED":
                data["comment"] = None
            serializer = AdminSerializer(instance, data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                notify_email(module="MATERIAL", purpose="approval", id=serializer.data["id"],
                             required_for={"batch": serializer.data["batch"],
                                           "status": serializer.data["file_status"]})
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error("material updation error: %s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"data": "Material successfully deleted"}, status=status.HTTP_204_NO_CONTENT
            )
        logger.error("material is not deleted")
        return Response(
            {"data": "Material not deleted, Permission denied"}, status=status.HTTP_403_FORBIDDEN
        )


class FieldViewSet(viewsets.ModelViewSet):
    queryset = FieldStudyObservation.objects.all()
    serializer_class = FieldStudySerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def create(self, request):
        if request.user.is_course_trainer:
            data = request.data
            if data["score"]:
                if not self.queryset.filter(trainee=data["trainee"], batch=data["batch"]).exists():
                    if int(data['trainee']) in Batch.objects.filter(
                            id=int(data['batch'])).values_list('trainee', flat=True):
                        serializer = self.serializer_class(data=data, context={'request': request})
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
                            if float(serializer.data["score"]) < 100:
                                notify_email(module="ASSESSMENT", purpose="required_cutoff",
                                             id=Answer.objects.get(trainee=data["trainee"],
                                                                   assessments=data["assessment_is"]).id,
                                             required_for={"assessment": serializer.data["assessment"],
                                                           "batch": serializer.data["batch_name"][0]["name"],
                                                           "user": serializer.data["trainee_name"]})
                            return Response(serializer.data, status=status.HTTP_200_OK)
                        logger.error("video not sent to trainee")
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    logger.error("trainee or trainer is not in batch")
                    return Response({"data": "Trainee or trainer is not in batch"},
                                    status=status.HTTP_400_BAD_REQUEST)
                logger.error("File is already sent to this trainee")
                return Response({"data": "File is already sent to this trainee"},
                                status=status.HTTP_400_BAD_REQUEST)
            logger.error("score is required field")
            return Response({"data": "score is required field"}, status=status.HTTP_400_BAD_REQUEST)
        logger.error("user is not course trainer")
        return Response({"data": "user is not course trainer"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_trainee:
            files = self.queryset.filter(trainee=request.user)
        if request.user.is_course_trainer:
            files = self.queryset.filter(trainer=request.user)
        page = self.paginate_queryset(files)
        if page is not None:
            serializer = self.serializer_class(page, many=True, context={'request': request})
            logger.info("field trip observation video of trainee ")
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(files, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, **kwargs):
        if request.user.is_course_trainer:
            data = request.data
            instance = self.queryset.get(pk=kwargs.get('pk'))
            serializer = self.serializer_class(instance, data, context={'request': request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            logger.error("field trip is not updated: %s" % serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "course trainer only can update the field study"},
                        status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, **kwargs):
        if request.user.is_course_trainer:
            instance = self.get_object()
            self.perform_destroy(instance)
            logger.info("field trip data deleted successfully")
            return Response(status=status.HTTP_204_NO_CONTENT)
        logger.error("field trip data not deleted")
        return Response({"data": "Field trip data not deleted, permission denied"},
                        status=status.HTTP_400_BAD_REQUEST)
