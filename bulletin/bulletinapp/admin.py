from django.contrib import admin
from bulletinapp.models import User, Post, Comment, Class
# Register your models here.
admin.site.register(User)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Class)