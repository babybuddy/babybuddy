from django.core.wsgi import get_wsgi_application

from dotenv import load_dotenv, find_dotenv

# Environment variables
# Check for and load environment variables from a .env file.
load_dotenv(find_dotenv())

application = get_wsgi_application()
