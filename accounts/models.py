from django.db import models
from django.conf import settings
from django.db.models.signals import post_save  
from django.dispatch import receiver        

class Student(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile'
    )
    name = models.CharField(max_length=100)
    handle = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.handle
    
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_student_profile(sender, instance, created, **kwargs):
    if created:
        
        Student.objects.get_or_create(
            user=instance,
            defaults={
                'name': instance.username,
                'handle': instance.username
            }
        )