from django.core.management.base import BaseCommand, CommandError
from itinerary.models import Category

class Command(BaseCommand):
    help = 'Loads category files into db'

    def handle(self, *args, **options):
        with open('itinerary/management/commands/categories.csv') as f:
            f.readline()
            categories = {}
            index = 0
            for line in f:
                line_elements = line.strip().split('|')
                
                user_cat, name, fs_id, avg_duration = line_elements
                user_cat = user_cat.strip()
                
                if user_cat not in categories:
                    categories[user_cat] = index
                    index = index + 1

                cat = Category(
                    user_category = user_cat,
                    user_cat_id = categories[user_cat],
                    name = name.strip(),
                    fs_id = fs_id.strip(),
                    avg_duration = int(avg_duration))
                cat.save()
