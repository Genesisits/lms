# File to maintain all the constants...

# User Choices
GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
PASSWORD_MSG = "is your lms login password"
PASSWORD_SUB = "LMS User Registration"

# Assessment Constants
ASSESSMENT_LIST = ['A11', 'A12', 'A13', 'A2', 'A31', 'A32', 'A33', 'A34', 'Overall_Technical', 'Overall_SoftSkills']
VERIFY_INIT = 'INITIATED'
VERIFY_PENDING = 'PENDING'
VERIFICATION_STATUS = (
    ('IN PROGRESS', 'in progress'),
    (VERIFY_INIT, 'initiated'),
    ('APPROVED', 'approved'),
    ('PENDING', 'pending'),
    ('NOT APPROVED', 'not approved'),
)

TYPE_OBJECTIVE = 'objective'
TYPE_DESCRIPTIVE = 'descriptive'
TYPE_FIELD_TRIP = 'observation'
TYPE_ATTENDANCE = 'attendance'
TYPE_FOJT = "fojt"

TYPE_CHOICES = (
        (TYPE_OBJECTIVE, 'objective'),
        (TYPE_DESCRIPTIVE, 'descriptive'),
        (TYPE_FIELD_TRIP, 'observation'),
        (TYPE_ATTENDANCE, 'attendance'),
        (TYPE_FOJT, 'fojt')
    )

ANSWER_INACTIVE = 'inactive'
ANSWER_CHOICES = (
    ("pending", "pending"),
    ("inprogress", "inprogress"),
    ("completed", "completed"),
    ("reviewing", "reviewing"),
    ("reviewed", "reviewed")
)

# Attendance Constants
ATTENDANCE_CHOICES = (
    ('absent', 'Absent'),
    ('present', 'Present')
)

ASSESSMENT_MSG = "is activated and available to answer"
ASSESSMENT_ACTIVATION_MSG = "assessment activation"
ASSESSMENT_ACTIVATED_MSG = "assessment_activated"
ASSESSMENT_NOT_SUBMITTED = "is not submitted by"
ASSESSMENT_DUE_ON = "assessment submission date"
ASSESSMENT_LAST_DAY_MSG = "Reminder.. your assessment submission lastday is today"
ASSESSMENT_LAST_DAY_SUBJECT = "Assessment About to be deactivated, Can't submit further"
ASSESSMENT_MARKS_LESS = "didn't get required marks in"
ASSESSMENT = "ASSESSMENT"
ASSESSMENT_FAIL = "assessment_fail"

# Business Group Constants

SURGICAL_SYNERGY = "surgical synergy"

assessment_str = "Assessments need to be ready before they trigger"
trigger_str = "{assign} will trigger on {weeks} week \n"

spine_surgery = [
    {"assign": ["A11"], "weeks": "5th"}, {"assign": ["A12"], "weeks": "9th"},
    {"assign": ["A13", "A2"], "weeks": "10th"}, {"assign": ["A31", "A32", "A33"], "weeks": "24th"},
    {"assign": ["A34"], "weeks": "15th"}
]

taruma = [
    {"assign": ["A11"], "weeks": "3rd"}, {"assign": ["A12"], "weeks": "4th"}, {"assign": ["A13"], "weeks": "1st"},
    {"assign": ["A2"], "weeks": "9th"}, {"assign": ["A33", "A34"], "weeks": "12th"}
]

neurosur = [
    {"assign": ["A11", "A12", "A2"], "weeks": "9th"}, {"assign": ["A13"], "weeks": "1st"},
    {"assign": ["A31", "A32"], "weeks": "18th"}, {"assign": ["A33"], "weeks": "24th"},
    {"assign": ["A34"], "weeks": "19th"}
]

neuroscular = [
    {"assign": ["A11", "A12"], "weeks": "4th"}, {"assign": ["A13"], "weeks": "1st"}, {"assign": ["A2"], "weeks": "9th"},
    {"assign": ["A31", "A32", "A33"], "weeks": "8th"}, {"assign": ["A34"], "weeks": "6th"}
]

neuro_module = [
    {"assign": ["A11"], "weeks": "4th"}, {"assign": ["A12"], "weeks": "3rd"}, {"assign": ["A13"], "weeks": "1st"},
    {"assign": ["A2"], "weeks": "6th"}, {"assign": ["A33"], "weeks": "15th"}, {"assign": ["A34"], "weeks": "10th"}
]

ent = [
    {"assign": ["A11", "A12"], "weeks": "1st"}, {"assign": ["A13"], "weeks": "3rd"}, {"assign": ["A2"], "weeks": "4th"},
    {"assign": ["A31", "A32"], "weeks": "5th"}, {"assign": ["A33"], "weeks": "16th"},
    {"assign": ["A34"], "weeks": "9th"}
]

# Error Messages of Model Creations
MODULE_EXISTS_MSG = "Module with this name already exists"

# Material Upload Email Message
MATERIAL_MESSAGE = "Material is uploaded"
MATERIAL_SUBJECT = "Material upload"
MATERIAL_STATUS_MSG = "Material status is"
MATERIAL_STATUS_SUB = "Material status"

# VIDEO EXTENSIONS
VIDEO_EXTENSIONS = (".mp4", ".3gp", ".wmv", ".avi", ".flv", ".mkv")
VIDEO_ERR_MSG = "File size shouldn't be greater than {mb}"

# Email Settings
EMAIL_MSG = "LMS Shiksha"


# BATCH CONSTANTS
BATCH_CREATED_MESSAGE = "is created. Access the material and get ready with prerequisites.Batch Starts from"
BATCH_CREATED_SUBJECT = "batch creation"

# MODULE STARTED
MODULE_SUBJECT = "Module {module} Started"
MODULE_1_MSG = "is started in"


# GRAPH COLORS
GRAPH_COLORS = ['#374C80', '#7A5195', '#BC5090', '#EF5675', '#d67e27', '#00876C', '#004C6D', '#D43D51', '#1f77b4', '#ff7f0e', '#2ca02c', '#c02324', '#9467bd', '#8c564b', '#7f7f7f', '#afbd22', '#17becf', '#d6d627']

# IMAGE EXTENSIONS
VALID_EXTENSIONS = ['.jpg', '.gif', '.png', '.tif', 'jpeg']

# NOTIFICATION CHOICES
CHOICE_FIELDS = (("USER", "user"),
                 ("MODULE", "module"),
                 ("LEVEL", "level"),
                 ("BUSINESSGROUP", "businessgroup"),
                 ("BATCH", "batch"),
                 ("ASSESSMENT", "assessment"),
                 ("BATCHASSESSMENT", "batchassessment"),
                 ("ANSWER", "answer"),
                 ("FEEDBACK", "feedback"),
                 ("ATTENDANCE", "attendance"),
                 ("MATERIAL", "material"),
                 ("FIELDSTUDY", "fieldstudy"),
                 )

# MONTHS
QUARTERLY = 3
HALFYEARLY = 6
