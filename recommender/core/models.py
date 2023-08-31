from django.db import models


class CandidatePages(models.Model):
    page = models.TextField(unique=True)
    rate = models.IntegerField()


class CrawledPages(models.Model):
    page = models.TextField(unique=True)

# RecommendedPages can be created as a database view in PostgreSQL
