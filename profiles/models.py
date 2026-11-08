from django.db import models


class ProfileSubmissionStatistics(models.Model):
    student = models.OneToOneField(
        'accounts.Student',
        on_delete=models.CASCADE,
        related_name='statistics'
    )

    rating = models.FloatField(default=0.0)
    max_rating = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.student.handle} Statistics"
    
class FavProblem(models.Model):
    handle = models.ForeignKey(
        'accounts.Student',
        to_field='handle',
        on_delete=models.CASCADE,
        related_name='favorite_problems'
    )

    problem_id = models.ForeignKey(
        'problems.Element',
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )

    fav_category = models.CharField(max_length=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['handle', 'problem_id'],
                name='unique_handle_favorite_problem'
            )
        ]

    def __str__(self):
        return f"{self.handle.handle} - {self.problem_id.pname}"