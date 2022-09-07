from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    def __str__(self):
        return self.username

class UserProfile(models.Model):
    is_student = models.BooleanField(default=True)
    is_instructor = models.BooleanField(default=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)

    def __str__(self):
        return str(self.user)

class Class(models.Model):
    class_code = models.CharField(max_length=6)
    name = models.CharField(max_length=50)
    instructor = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="classes_teaching")
    students = models.ManyToManyField(UserProfile, related_name="classes_taking", symmetrical=False)

    def __str__(self):
        return self.name

class Post(models.Model):
    which_class = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="posts")
    title = models.CharField(max_length=100)
    #image = models.ImageField(upload_to='images', blank=True)
    text = models.CharField(max_length=15000)
    poster = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="posts")
    date = models.CharField(max_length=10)
    post_id = models.AutoField(primary_key=True)

    def __str__(self):
        return self.which_class.name + " post by " + self.poster.user.username


class Comment(models.Model):
    auto_increment_id = models.AutoField(primary_key=True)
    text = models.TextField(max_length=500)
    post = models.ForeignKey(to=Post, on_delete=models.CASCADE, related_name="comments")
    commenter = models.ForeignKey(to=UserProfile, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return f"{self.commenter} comments: {self.text} on {self.post}"