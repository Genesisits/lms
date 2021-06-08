import logging
import os
import xlwt

from datetime import date, timedelta

from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from businessGroup.models import Batch
from attendance.serializers import AttendanceSerializer
from attendance .models import Attendance
from assessment.views import bar_graph, generate_reports, individual_scores, batch_scores,\
    batch_attendance, assessments_scores, trainee_percentages, trainee_reports, trainer_batches,\
    full_batch_reports
from user.views import prepair_report, bg_donut_reports, assessments_percentage, consolidated_graphs,\
    total_percentage, batches_count, batches_user_count
from lms.constants import QUARTERLY, HALFYEARLY

logger = logging.getLogger(__name__)


def attendance_calculate(trainee):
    batches = Batch.objects.filter(trainee=trainee)
    for batch in batches:
        total_attend = int((date.today()-batch.start_date).days+1)
        attended = Attendance.objects.filter(trainees=trainee, attendances='present', batches=batch.id).count()
        percent = attended/total_attend*100
        return percent


class AttendanceCalculateViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        if request.user.is_trainee:
            return Response(attendance_calculate(request.user.id), status=status.HTTP_200_OK)
        return Response({"data": "user is not trainee"}, status=status.HTTP_400_BAD_REQUEST)


def attendance(timespan, request):
    today = date.today()
    if (today.month - timespan) < 1:
        start_date = date(today.year-(int((today.month-timespan) / 12)+1), today.month-timespan+12, today.day)
    else:
        start_date = date(today.year, today.month - timespan, today.day)

    percents = []
    
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
    for batch in batches:
        trainees = batch.trainee.all()
        batch_trainees.append({"batch": batch.name, "trainees": len(trainees)})
        for trainee in trainees:
            attendances = Attendance.objects.filter(schedule__range=(start_date, today),
                                                    batches=batch, trainees=trainee.id)
            present = attendances.filter(attendances='present').count()
            atotal = (today - batch.start_date).days
            percent = present / atotal * 100 if atotal != 0 else 0
            percents.append({"batch": batch, "trainee": trainee.first_name, "percent": percent})
    datasets, labels, total_data = generate_reports(percents=percents, batches=batches)
    resp = bar_graph(labels, datasets,
                    "Attendance Percentage", 2, "Trainee Count", "Batch Names", True)
    for mark in resp['data']['datasets']:
        for index, batche in enumerate(resp['data']['labels']):
            trainees_details.append({"batch": batche, "label": mark["label"], "total": mark["data"][index]})
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


class AttendanceReport(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        reports = {}
        sheet = request.query_params.get("excel")
        full_reports = request.query_params.get("full_batch_reports")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        batchind = request.query_params.get("batchindividualscore")
        batchsc = request.query_params.get("batchscores")
        batchassc = request.query_params.get("batchassessscore")
        batchatnd = request.query_params.get("batchattnd")
        assessment_scores = request.query_params.get("scores")
        attendance_scores = request.query_params.get("attendance")
        qassessment_scores = request.query_params.get("qscores")
        hassessment_scores = request.query_params.get("hscores")
        qattendance_scores = request.query_params.get("qattendance")
        hattendance_scores = request.query_params.get("hattendance")
        bg = request.query_params.get("bg")
        bg_user = request.query_params.get("bg_user")
        bu = request.query_params.get("bu")
        trainee_percents = request.query_params.get("trainee_percents")
        assessment_percents = request.query_params.get("assessment_percents")
        qoverall_scores = request.query_params.get("qoverall")
        hoverall_scores = request.query_params.get("hoverall")
        trainer_batch = request.query_params.get("batches")
        trainee = request.query_params.get("trainee")
        assessment = request.query_params.get("assessment")
        if request.user.is_superuser:
            # if qoverall_scores:
            #     reports = total_percentage(QUARTERLY, request)
            #     name = "total percentages"
            # if hoverall_scores:
            #     reports = total_percentage(HALFYEARLY, request)
            #     name = " halfyearly total percentages"
            if bg:
                reports = batches_count()
                name = "businessGroup_batches"
            if bg_user:
                reports = batches_user_count()
                name = "businessGroup_users"
            # if batchind:
            #     reports = individual_scores(batchind)
            #     name = "trainee scores"
            # if batchsc:
            #     reports = batch_scores(batchsc)
            #     name = "batch total scores"
            # if batchassc:
            #     reports = assessments_scores(batchassc)
            #     name = "assesmsent scores"
            # if batchatnd:
            #     reports = batch_attendance(batchatnd)
            #     name = "batch attendance"
            # if qassessment_scores:
            #     reports = prepair_report(QUARTERLY, request)
            #     name = "trainee count"
            # if hassessment_scores:
            #     reports = prepair_report(HALFYEARLY, request)
            #     name = "halfyearly trainee count"
            # if qattendance_scores:
            #     reports = attendance(QUARTERLY, request)
            #     name = "attendance report"
            # if hattendance_scores:
            #     reports = attendance(HALFYEARLY, request)
            #     name = "halfyearly atendance report"
            # if start_date:
            #     reports = consolidated_graphs(start_date, end_date)
            #     name = "consolidated_graphs"
            # if full_reports:
            #     reports = full_batch_reports(full_reports)
            #     name = "full_batch_reports"
            logger.info({"batch": trainer_batch} if trainer_batch else "no trainer_batch")
            if trainer_batch:
                if not start_date:
                    start_date = None
                if not end_date:
                    end_date = None
                if not trainee:
                    trainee = None
                if not assessment:
                    assessment = None
                if not bu:
                    bu = None
                reports = trainer_batches(batch=trainer_batch, trainee_id=trainee,
                                          assessment=assessment, timespan1=start_date,
                                          timespan2=end_date, bg=bu)
                name = "batch trainee scores"
                logger.info("report" if reports else "report error")
        if request.user.is_course_trainer or request.user.is_sfe_trainer:
            if qoverall_scores:
                reports = total_percentage(QUARTERLY, request)
                name = "overall percentages"
            if hoverall_scores:
                reports = total_percentage(HALFYEARLY, request)
                name = "half yearly overall percentages"
            if qassessment_scores:
                reports = prepair_report(QUARTERLY, request)
                name = "assessment based reports"
            if hassessment_scores:
                reports = prepair_report(HALFYEARLY, request)
                name = "halfyearly assessment reports"
            if qattendance_scores:
                reports = attendance(QUARTERLY, request)
                name = "quarterly attendance"
            if hattendance_scores:
                reports = attendance(HALFYEARLY, request)
                name = "halfyearly attendance"
            if trainee_percents:
                reports = trainee_percentages(request.user)
                name = "trainee scores"
            if assessment_percents:
                reports = assessments_percentage(request.user)
                name = "assessment_percentages"
            if trainer_batch:
                if not start_date:
                    start_date = None
                if not end_date:
                    end_date = None
                if not trainee:
                    trainee = None
                if not assessment:
                    assessment = None
                if not bu:
                    bu = None
                reports = trainer_batches(trainer=request.user.id, batch=trainer_batch, trainee_id=trainee,
                                          assessment=assessment, timespan1=start_date,
                                          timespan2=end_date, bg=bu)
                name = "batch trainee scores"
        if request.user.is_trainee:
            if assessment_scores:
                reports = trainee_reports(request.user)
                name = "trainee reports"
            # if attendance_scores:
            #     reports = trainee_attendance(request.user.id)
        logger.info("quarterly and half yearly attendance reports")

        if sheet:
            xls_response = HttpResponse(content_type='application/ms-excel')
            file_name = name + str(date.today()) + ".xls"
            file_name = file_name.replace(" ", "_")
            xls_response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
            wb = xlwt.Workbook(os.path.join(settings.MEDIA_ROOT, file_name))
            row_num = 0
            font_style = xlwt.XFStyle()
            font_style.font.bold = True

            # style_pass = xlwt.easyxf('pattern: pattern solid, fore_colour green;')
            # style_fail = xlwt.easyxf('pattern: pattern solid, fore_colour red;')
            style_pass = xlwt.easyxf("align:wrap on; font: bold on, color-index green")
            style_fail = xlwt.easyxf("align:wrap on; font: bold on, color-index red")

            if not type(reports) is list:
                ws = wb.add_sheet('new')

                if not reports.get('bar_graph'):
                    graph_source = reports.get('data')
                else:
                    graph_source = reports.get('bar_graph').get('data')
                add_excel(graph_source, ws, row_num, font_style, style_pass, style_fail)

            else:
                for report in reports:
                    for batch in report:
                        if not type(report[batch]) is list:
                            if len(batch) < 31:
                                ws = wb.add_sheet(batch)
                            else:
                                ws = wb.add_sheet(batch[:30])
                            graph_source = report[batch]['bar_graph']['data']
                            add_excel(graph_source, ws, row_num, font_style, style_pass, style_fail)
                        else:
                            for graph in report[batch]:
                                if len(batch) < 31:
                                    ws = wb.add_sheet(batch)
                                else:
                                    ws = wb.add_sheet(batch[:30])
                                graph_source = graph['data']
                                add_excel(graph_source, ws, row_num, font_style, style_pass, style_fail)

            wb.save(os.path.join(settings.MEDIA_ROOT, file_name))
            return Response({"excel": os.path.join(settings.MEDIA_URL, file_name)})
              
        return Response(reports, status=status.HTTP_200_OK)


def add_excel(graph_source, ws, row_num, font_style, style_pass, style_fail):
    column_names = graph_source.get('datasets')
    columns = ['Name']

    for col in column_names:
        columns.append(col.get('label'))

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    row_names = []
    if graph_source.get('labels'):
        for index, row in enumerate(graph_source.get('labels')):
            names = [row]
            for marks in graph_source.get('datasets'):
                if type(marks.get('data')[index]) != str:
                    mark = "NA" if int(marks.get('data')[index]) == 0 else marks.get('data')[index]
                else:
                    mark = marks.get('data')[index]
                names.append(mark)
            row_names.append(names)
    else:
        for index in range(len(graph_source['datasets'][0]['data'])):
            names = [index + 1]
            for marks in graph_source.get('datasets'):
                mark = marks.get('data')[index]
                names.append(mark)
            row_names.append(names)

    for row in row_names:
        row_num += 1
        for col_num in range(len(row)):
            if type(row[col_num]) is not str:
                if row[col_num] >= 80:
                    ws.write(row_num, col_num, row[col_num], style=style_pass)
                elif row[col_num] < 80:
                    ws.write(row_num, col_num, row[col_num], style_fail)
                else:
                    ws.write(row_num, col_num, row[col_num], font_style)
            else:
                ws.write(row_num, col_num, row[col_num], font_style)
    return ws


def trainee_attendance(trainee):
    """
    Trainee attendance report for dashboard
    :param request:
    :return:
    """
    today = date.today()
    data = []
    batches = Batch.objects.filter(trainee=trainee)
    for batch in batches:
        start_date = batch.start_date
        trainee_aggregate = []
        present_list = []
        absent_list = []
        attendance = Attendance.objects.filter(trainees=trainee, batches=batch)
        total = attendance.count()
        for n in range(int((today - start_date).days) + 1):
            day = start_date + timedelta(n)
            attendances = attendance.filter(schedule=day)
            present = attendances.filter(attendances='present')
            absent = attendances.filter(attendances='absent')
            if present.exists():
                present_list.append(present)
            if absent.exists():
                absent_list.append(absent)
        trainee_aggregate.append(
            {
                "days_present": len(present_list),
                "days_absent": len(absent_list),
                "attendance_percentage": len(present_list) / total * 100 if total != 0 else None
            }
        )
        data.append({"batch": batch.name, "trainee_attendance": trainee_aggregate})
    return data
