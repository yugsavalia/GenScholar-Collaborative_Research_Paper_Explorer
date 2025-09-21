from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required

def signup_view(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()       # saves user in DB
            login(request, user)     # log in immediately
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "accounts/signup.html", {"form": form})

