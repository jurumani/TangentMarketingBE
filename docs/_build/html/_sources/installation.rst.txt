Boilerplate Installation
=========================

This section outlines how to install and configure the Django Boilerplate project.

Installation Steps
------------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/your-repo-url.git
      cd your-repo-directory

2. Install dependencies:

   .. code-block:: bash

      pip install -r requirements.txt

3. Set up the database:

   .. code-block:: bash

      python manage.py migrate

4. Create a superuser:

   .. code-block:: bash

      python manage.py createsuperuser

Running the Project
-------------------

1. Start the Django development server:

   .. code-block:: bash

      python manage.py runserver

2. Start Celery worker:

   .. code-block:: bash

      celery -A core worker --loglevel=info

3. Start Celery Beat:

   .. code-block:: bash

      celery -A core beat --loglevel=info

4. Start Flower:

   .. code-block:: bash

      celery -A core flower --loglevel=info

Configuration
-------------

You can adjust configurations for Celery, Redis, and the Django project in ``settings.py``.
