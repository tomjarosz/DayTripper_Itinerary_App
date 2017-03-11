from django.core.management.base import BaseCommand, CommandError
from itinerary.models import Place
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Deletes Places that were stored more than a week ago'

    def handle(self, *args, **options):
        date_threshold = date.today() - timedelta(days=10)
        places = Place.objects.filter(store_date__lte=date_threshold)
        print('Note: {} places deleted'.format(len(places)))
        places.delete()