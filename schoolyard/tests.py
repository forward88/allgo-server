import random

from django.urls import reverse
from django.http import QueryDict
from django.test.runner import DiscoverRunner
from django.utils.dateparse import parse_duration

from rest_framework.test import APITestCase

__all__ = ['reverse_with_query', 'SchoolyardTestRunner', 'DurationTestCase']

def reverse_with_query (view_name, query_params=None, **kwargs):
    path = reverse (view_name, **kwargs)

    query = QueryDict (mutable=True)
    query.update (query_params)

    return f"{path}?{query.urlencode (safe=',')}"

class SchoolyardTestRunner (DiscoverRunner):
    @classmethod
    def add_arguments (this_class, parser):
        parser.add_argument ('-s', '--seed', type=int, metavar='SEED', help='seed to use with the PRNG')

    def __init__ (this, seed=None, **kwargs):
        super ().__init__ (**kwargs)

        if seed is None:
            seed = random.randrange (65536)

        this.seed = seed

    def setup_test_environment (this, **kwargs):
        random.seed (this.seed)

        print (f"random.seed ({this.seed})")

        return super ().setup_test_environment (**kwargs)

class DurationTestCase (APITestCase):
    def assertDurationsEqual (this, a, b):
        return abs (a.total_seconds () - b.total_seconds ()) < 60
