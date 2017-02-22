from django.db import models
from django.utils import timezone

# Create your models here.

class City(models.Model):
    city_name = models.CharField(max_length=200)
    country_name = models.CharField(max_length=200)
    city_lat = models.FloatField()
    city_lng = models.FloatField()

    def __str__(self):
        return str(self.city_name + ", " + self.country_name)

class Place(models.Model):
    id_str = models.CharField(max_length=200, primary_key=True)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    lat =  models.FloatField()
    lng = models.FloatField()
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    postal_code = models.CharField(max_length=200)
    category = models.CharField(max_length=200)
    rating = models.IntegerField()
    checkins = models.IntegerField()
    description = models.CharField(max_length = 200, null=True)
    url = models.CharField(max_length = 500, null=True)

    def __str__(self):
        return str(self.id_str + self.name)

    def is_open_dow(self, dow):
        return Place_hours.objects.filter(place_id=self.id_str, d_of_w_open=dow).exists()

    def is_open_dow_time(self, dow, time):
        data = Place_hours.objects.filter(place_id=self.id_str, d_of_w_open=dow, open_time__lte=time, close_time__gte=time)
        return data.exists()


class Place_hours(models.Model):
    place_id = models.ForeignKey(Place, on_delete=models.CASCADE)
    d_of_w_open = models.IntegerField()
    open_time = models.TimeField()
    close_time = models.TimeField()
    

class UserQuery(models.Model):
    query_date = models.DateTimeField(default=timezone.now)
    query_city = models.CharField(max_length=200)
    city = models.ForeignKey(City, on_delete=models.CASCADE)    
    arrival_date = models.DateField()
    time_start = models.TimeField()
    time_end = models.TimeField()
    category_ids = models.CharField(max_length=200)
    mode_transportation = models.CharField(max_length=200)
    starting_location = models.CharField(max_length=200, null=True)
    start_lat = models.FloatField(null=True)
    start_lng = models.FloatField(null=True)

    def __str__(self):
        return str(str(self.query_date) +', '+ self.query_city +', '+ self.city.city_name)


class Category(models.Model):
    user_category = models.CharField(max_length=200)
    user_cat_id = models.IntegerField()
    name = models.CharField(max_length=200)
    fs_id = models.CharField(max_length=200)
    avg_duration = models.IntegerField()

    def __str__(self):
        return str(self.user_category +', '+ self.name)
