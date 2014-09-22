from django.db import models

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=128, unique=True)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)

    def _str_(self):
        return self.name

    @staticmethod
    def encode(name):
        return name.replace(' ', '_')

    @staticmethod
    def decode(name):
        return name.replace('_', ' ')

class Page(models.Model):
    category = models.ForeignKey(Category)
    title = models.CharField(max_length=128)
    url = models.URLField()
    views = models.IntegerField(default=0)

    def category_name(self):
        return self.category.name
    category_name.short_description = 'Category'

    def _str_(self):
        return self.title
