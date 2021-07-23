# lms
LMS Server Application

# Need to follow the below protocols to create a branch.

# Developers should checkout the code from dev branch only

`Follow the protocols while creating the branch`.

If we are creating a feature It should start with feature/
If we are working on a bug the branch name should start with bug/
If it's a enhancement, It should start with enhancement/

Eg : feature_<ticketId>_<username>
  
After creating branch, Please do map the Projects and MileStones,

# Project Setup.
create virtualenv
`virtualenv --python=python3 <env name>`
Eg: virtualenv --python=python3 venv

Activate environment
`source venv\bin\acivate` If Linux
`venv\Scripts\activate` If Windows

After activating the virtualenvironment install packages
`pip install -r requirements.txt`

After successful isntallation of packages, need to run the server.

`python manage.py runserver`

Once we map the miles stones and project, it will automate the remaining proces..
=======
# lms server
