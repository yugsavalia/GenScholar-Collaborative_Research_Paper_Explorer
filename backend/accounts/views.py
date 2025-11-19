from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.views.decorators.csrf import csrf_protect
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'accounts/login.html')


# JSON API Views for frontend integration

def api_csrf_view(request):
    """JSON API endpoint to get CSRF token."""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    token = get_token(request)
    response = JsonResponse({"success": True, "data": {"csrf_token": token}})
    response.set_cookie('csrftoken', token, samesite='Lax')
    return response


@csrf_exempt
def api_login_view(request):
    """JSON API endpoint for user login."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return JsonResponse({"success": False, "message": "Username and password are required"}, status=400)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({
                "success": True,
                "data": {"user": {"id": user.id, "username": user.username}}
            })
        else:
            return JsonResponse({"success": False, "message": "Invalid credentials"}, status=401)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def api_signup_view(request):
    """JSON API endpoint for user signup."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    
    try:
        data = json.loads(request.body)
        form = UserCreationForm(data)
        
        if form.is_valid():
            user = form.save()
            login(request, user)
            return JsonResponse({
                "success": True,
                "data": {"user": {"id": user.id, "username": user.username}}
            }, status=201)
        else:
            # Get first error message from form
            errors = form.errors.as_data()
            error_message = "Invalid input"
            if errors:
                first_field = list(errors.keys())[0]
                first_error = list(errors[first_field])[0]
                error_message = str(first_error)
            return JsonResponse({"success": False, "message": error_message}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def api_logout_view(request):
    """JSON API endpoint for user logout."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({"success": True, "data": {"message": "Logged out successfully"}})
    else:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)


def api_get_user_view(request):
    """JSON API endpoint to get current user."""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    else:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)
