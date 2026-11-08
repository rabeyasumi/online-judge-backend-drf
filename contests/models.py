from django.db import models


class Contest(models.Model):
    cname = models.CharField(max_length=150)
    tag = models.CharField(max_length=50)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_rated = models.BooleanField(default=False)
    rating_processed = models.BooleanField(default=False)

    def __str__(self):
        return self.cname


class GlobalStanding(models.Model):
    """One row per student. Updated only when a rated contest is processed
    (admin action / `manage.py process_ratings`), never on submit."""

    student = models.OneToOneField(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='global_standing'
    )
    rating = models.FloatField(default=0.0)
    rated_contests = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.handle} - Global Rating"


class RatingChange(models.Model):
    """History row: global rating before and after one contest."""

    student = models.ForeignKey(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='rating_changes'
    )
    contest = models.ForeignKey(
        Contest,
        on_delete=models.CASCADE,
        related_name='rating_changes'
    )
    old_rating = models.FloatField()
    new_rating = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'contest'],
                name='unique_student_contest_rating_change'
            )
        ]

    @property
    def rating_change(self):
        return self.new_rating - self.old_rating

    def __str__(self):
        return f"{self.student.handle} - {self.contest.cname}"


