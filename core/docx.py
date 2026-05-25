from django.utils.dateformat import format as django_date_format
from jinja2 import Environment


def make_jinja_env():
    env = Environment()
    env.filters['date'] = lambda value, fmt='': django_date_format(value, fmt) if value else ''
    return env