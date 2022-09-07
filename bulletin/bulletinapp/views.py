from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django import forms
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile, Class, Post, Comment
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe


class ClassForm(forms.ModelForm):
    class Meta:
        model = Class
        fields = ['name']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text']
        widgets = {
            'title': forms.TextInput(attrs={
            'class': 'form-item'
            }),
            'text': forms.Textarea(attrs={
            'rows': 20,
            'class': 'form-item'
            })
         }
        labels = {
            "title": mark_safe('Title <br>'),
            "text": mark_safe('Text <br>')
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
            'rows': 5,
            'class': 'form-item'
            })
         }
        labels = {
            "text": mark_safe('Text <br>')
        }
#        exclude = ['commenter', 'class']

def welcome(request):
    return render(request, "bulletin/welcome.html")


@login_required
def index(request):
    userprofile = get_object_or_404(UserProfile, pk=request.user)
    classes = None
    if userprofile.is_instructor:
        classes = Class.objects.filter(instructor=userprofile)
    else:
        classes = Class.objects.filter(students=userprofile)
    return render(request, "bulletin/index.html", {
        "userprofile": userprofile,
        "classes": classes,
        "is_instructor": userprofile.is_instructor,
        "userprofile": userprofile
    })


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "bulletin/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "bulletin/login.html")


def logout_view(request):
    logout(request)
    return render(request, "bulletin/welcome.html")

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        category = request.POST["category"]
        is_instructor = False
        is_student = False
        if category == "instructor":
            is_instructor = True
            is_student = False
        elif category == "student":
            is_instructor = False
            is_student = True
        else:
            return render(request, "bulletin/register.html", {
                "message": "Select a user type."
            })
        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "bulletin/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            userProfile = UserProfile(user=user, is_instructor=is_instructor, is_student=is_student)
            userProfile.save()
        except IntegrityError:
            return render(request, "bulletin/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "bulletin/register.html")

@login_required
def new_class(request):
    if request.method == "POST":
        userprofile = get_object_or_404(UserProfile, pk=request.user)
        form = ClassForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data["name"]
            code = get_random_string(length=6, allowed_chars='1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            code_list = Class.objects.all().values_list('class_code')
            while (code in code_list):
                code = get_random_string(length=6, allowed_chars='1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            new_class = Class(name=name, class_code=code, instructor=userprofile)
            new_class.save()
            return HttpResponseRedirect(reverse("index"))
        else:
            return HttpResponse("Failed to create new class.")
    else:
        form = ClassForm()
        return render(request, "bulletin/new_class.html", {
            "form": form
        })


@login_required
def class_view(request, class_code):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            the_class = get_object_or_404(Class, class_code=class_code)
            title = form.cleaned_data["title"]
            text = form.cleaned_data["text"]
            date = datetime.now().strftime("%x")
            poster = get_object_or_404(UserProfile, pk=request.user)
            post = Post(which_class=the_class,title=title, text=text, poster=poster, date=date)
            post.save()
        else:
            return HttpResponse("Failed to submit post")
        return HttpResponseRedirect(reverse("class_view", args=[class_code]))
    else:
        form = PostForm()
        the_class = get_object_or_404(Class, class_code=class_code)
        posts = Post.objects.filter(which_class=the_class)
        userprofile = get_object_or_404(UserProfile, user=request.user)
        return render(request, "bulletin/class_view.html", {
            'class': the_class,
            'form': form,
            'posts': posts,
            'userprofile':userprofile
        })

def post(request, post_id):
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            text = form.cleaned_data["text"]
            commenter = get_object_or_404(UserProfile, pk=request.user)
            post = get_object_or_404(Post, post_id=post_id)
            comment = Comment(text=text, commenter=commenter, post=post)
            comment.save()
        else:
            for field in form:
                print("Field Error:", field.name,  field.errors)
            return HttpResponse("Failed to submit comment")
        return HttpResponseRedirect(reverse("post", args=[post_id]))
    else:
        #post = Post.objects.get(pk=post_id)
        post = get_object_or_404(Post, post_id=post_id)
        comment = CommentForm()
        comments = Comment.objects.filter(post=post)
        return render(request, "bulletin/post.html", {
            'post': post,
            'comment': comment,
            'comments':comments
        })

def join_class(request):
    if request.method == 'POST':
        code = request.POST["code"]
        joined_class = get_object_or_404(Class, class_code=code)
        userprofile = get_object_or_404(UserProfile, pk=request.user)
        joined_class.students.add(userprofile)
        joined_class.save()
        return HttpResponseRedirect(reverse(index))
    else:
        return render(request, "bulletin/join_class.html")

