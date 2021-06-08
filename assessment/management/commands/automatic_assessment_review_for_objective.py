import logging

from django.core.management.base import BaseCommand
from django.db.models import Q

from assessment.models import Answer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "object assessment automate review"

    def handle(self, *args, **kwargs):
        assess = Answer.objects.filter(Q(assessments__assmt__as_type="objective"),
                                       Q(status="completed") | Q(status="reviewing"))
        for data in assess:
            i_d = data.id
            sub = data.answer_data
            if sub:
                for index, val in enumerate(sub):
                    if "TRF" in val:
                        original = data.assessments.assessment_data
                        for ok in original:
                            if "TRF" in ok:
                                if ok["TRF"][0]["question_text"] == val["TRF"][0]["question_text"]:
                                    correct = ok["TRF"][0]["correct_answers"]
                                    ansed = str(val["TRF"][0]["trf_answers"]).lower()
                        if correct == ansed:
                            marks = val["TRF"][0]["weightage"]
                            data.answer_data[index]["TRF"][0]["marks"] = marks
                            data.save()
                        else:
                            marks = 0
                            data.answer_data[index]["TRF"][0]["marks"] = marks
                            data.save()

                    if "FTB" in val:
                        original = data.assessments.assessment_data
                        for ok in original:
                            if "FTB" in ok:
                                if ok["FTB"][0]["question_text"] == val["FTB"][0]["question_text"]:
                                    c_a = ok["FTB"][0]["correct_answers"].split(",")
                        c_k = val["FTB"]
                        c_c = c_k[0]["answers"]
                        c_b = []
                        c_b.extend(c_c)
                        total = []
                        for item in c_a:
                            for b_a in c_b:
                                total.append(bool(item.strip().lower() == b_a.strip().lower()))
                                c_b.remove(b_a)
                                break
                        weight = float(val["FTB"][0]["weightage"])
                        correct = total.count(True)
                        marks = weight / len(c_a) * correct
                        data.answer_data[index]["FTB"][0]["marks"] = marks
                        data.save()

                    if "CTA" in val:
                        original = data.assessments.assessment_data
                        for ok in original:
                            if "CTA" in ok:
                                if ok["CTA"][0]["question_text"] == val["CTA"][0]["question_text"]:
                                    c_a = ok["CTA"][0]["correct_answers"]
                        c_a.sort()
                        c_b = []
                        c_k = val["CTA"]
                        for c in c_k[0]["cta"]:
                            if c["value"] is True:
                                c_b.append(c["key"])
                        total = []
                        c_b.sort()
                        for ans in c_a:
                            for value in c_b:
                                total.append(bool(ans.strip() == value.strip()))
                                c_b.remove(value)
                                break
                        weight = float(val["CTA"][0]["weightage"])
                        correct = total.count(True)
                        marks = weight / len(c_a) * correct
                        data.answer_data[index]["CTA"][0]["marks"] = marks
                        data.save()

                    if "MTF" in val:
                        answered = val["MTF"][0]["mtf_answers"]
                        if answered[0]["question"] is "":
                            marks = 0
                        else:
                            original = data.assessments.assessment_data
                            corrected = []
                            for ok in original:
                                if "MTF" in ok:
                                    correct = ok["MTF"][0]["questions"]
                                    for qs in correct:
                                        for anr in answered:
                                            if (qs["question"] == anr["question"]) and (
                                                    qs.get("answer").lower() == (anr.get("answer").lower() if anr.get("answer") is not None else None)):
                                                corrected.append(anr)
                            weight = float(val["MTF"][0]["weightage"])
                            total = len(answered)
                            scored = len(corrected)
                            marks = weight / total * scored
                        data.answer_data[index]["MTF"][0]["marks"] = marks
                        data.save()
                            
            query = Answer.objects.get(id=i_d)
            total_marks = []
            total_weight = []
            for value in query.answer_data:
                for val in value.values():
                    if type(val) is list:
                        total_marks.append(float(val[0]["marks"]))
                        total_weight.append(float(val[0]["weightage"]))
                    if type(val) is dict:
                        total_marks.append(float(value['marks']))
                        total_weight.append(float(value["weightage"]))
            total_score = sum(total_marks) / sum(total_weight) * 100
            query.total_score = total_score
            query.save()
            query.status = "reviewed"
            query.save()
            logger.info("assessment is reviewed")
        logger.error("assessment review")
