import os
import sys
import site

activate_this = 'C:/Users/SVC-ISCSQL/envlms/Scripts/activate_this.py'
exec(open(activate_this).read(),dict(__file__=activate_this))

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir('C:/Users/envlms/Lib/site-packages')

# Add the app's directory to the PYTHONPATH
sys.path.append('C:/UsersSVC-ISCSQL/lms')
sys.path.append('C:/Users/SVC-ISCSQL/lms/lms')

os.environ['DJANGO_SETTINGS_MODULE'] = 'lms.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
