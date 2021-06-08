from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets, status
from .serializers import *


class EmailTemplateView(viewsets.ModelViewSet):
    queryset = EmailTemplates.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        if request.user.is_superuser:
            data = request.data
            serializer = EmailTemplateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "only admin have rights"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_superuser:
            # when using self.queryset data is not updating
            templates = EmailTemplates.objects.all()
            serializer = self.serializer_class(templates, many=True)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response({"data": "login user must be admin"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        data = request.data
        instance = EmailTemplates.objects.get(pk=kwargs.get('pk'))
        if request.user.is_superuser:
            serializer =self.serializer_class(instance, data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"data": "data is not deleted"}, status=status.HTTP_400_BAD_REQUEST)


class EmailNotificationsView(viewsets.ModelViewSet):
    queryset = EmailNotifications.objects.all()
    serializer_class = EmailNotificationsSerializer
    permission_classes = (IsAuthenticated,)

    def create(self, request):
        if request.user.is_superuser:
            data = request.data
            serializer = EmailNotificationsSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "only admin have rights"}, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        if request.user.is_superuser:
            # self.queryset is not updating immediately
            notifications = EmailNotifications.objects.all()
            serializer = self.serializer_class(notifications, many=True)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response({"data": "login user must be admin"}, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, **kwargs):
        data = request.data
        instance = EmailNotifications.objects.get(pk=kwargs.get('pk'))
        if request.user.is_superuser:
            serializer =self.serializer_class(instance, data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"data": "permission denied"}, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"data": "data is not deleted"}, status=status.HTTP_400_BAD_REQUEST)
