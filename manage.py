#!/usr/bin/env python
import sys

from dotenv import load_dotenv, find_dotenv

if __name__ == "__main__":
    # Environment variables
    # Check for and load environment variables from a .env file.
    load_dotenv(find_dotenv())

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )
        raise
    execute_from_command_line(sys.argv)
