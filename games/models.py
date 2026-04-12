from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    steam_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    price = models.FloatField(default=0)
    image = models.URLField()

    def __str__(self):
        return self.name


class PriceHistory(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    price = models.FloatField()
    date = models.DateTimeField(auto_now_add=True)


class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.query}"