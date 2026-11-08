from django.db import models


class Element(models.Model):
    pname = models.CharField(max_length=200)
    description = models.TextField()
    author = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    rating = models.IntegerField()
    time_limit = models.FloatField(default=2.0)
    memory_limit = models.IntegerField(default=256)
    source = models.CharField(
        max_length=50,
        default='manual'
    )

    external_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        unique=True
    )

    contest = models.ForeignKey(
        'contests.Contest',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='problems'
    )

    def __str__(self):
        return self.pname
    
class TestCase(models.Model):
    problem = models.ForeignKey(
        Element,
        on_delete=models.CASCADE,
        related_name='test_cases'
    )
    input_data = models.TextField()
    expected_output = models.TextField()

    def __str__(self):
        return f"{self.problem.pname} - TestCase {self.id}"