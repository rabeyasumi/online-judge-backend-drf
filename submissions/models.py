from django.db import models
from django.utils import timezone

VERDICT_CHOICES = [
    ('Pending', 'Pending'),
    ('Accepted', 'Accepted'),
    ('Wrong Answer', 'Wrong Answer'),
    ('Compilation Error', 'Compilation Error'),
    ('Time Limit Exceeded', 'Time Limit Exceeded'),
    ('Runtime Error', 'Runtime Error'),
    ('Memory Limit Exceeded', 'Memory Limit Exceeded'),
    ('Judge Error', 'Judge Error'),
]

class Submission(models.Model):
    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    element = models.ForeignKey(
        'problems.Element',
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    contest = models.ForeignKey(
        'contests.Contest',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='submissions'
    )

    code = models.TextField()
    language = models.CharField(max_length=50)

    verdict = models.CharField(
        max_length=50,
        choices=VERDICT_CHOICES,
        default='Pending'
    )

    execution_time = models.FloatField(
        null=True,
        blank=True
    )

    memory = models.FloatField(
        null=True,
        blank=True
    )
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.student.handle} - {self.element.pname}"
    
class Standings(models.Model):
    contest = models.ForeignKey(
        'contests.Contest',
        on_delete=models.CASCADE,
        related_name='standings'
    )

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='standings'
    )

    solved = models.IntegerField(default=0)
    penalty = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    rank = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['contest', 'student'],
                name='unique_contest_student'
            )
        ]

    def __str__(self):
        return f"{self.contest.cname} - {self.student.handle}"
    
