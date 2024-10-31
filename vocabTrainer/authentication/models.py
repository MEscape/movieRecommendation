from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('guest', 'Guest'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(unique=True, null=False)

    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.is_staff = True

        if self.is_staff:
            self.role = 'admin'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.username