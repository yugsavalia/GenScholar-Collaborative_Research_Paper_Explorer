from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
import json
import re
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from allauth.account.forms import SignupForm
from allauth.account.adapter import get_adapter
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import PendingEmailVerification, EmailOTP
import os

def validate_email_strict(email):
    """
    Strict email validation helper.
    Validates that email contains a valid domain extension (.com, .in, .org, .net, etc.)
    """
    import re
    
    if not email:
        return False, "Email is required."
    
    email = email.strip().lower()
    
    if not email:
        return False, "Email cannot be empty."
    
    # Must contain exactly one '@'
    if email.count('@') != 1:
        return False, "Invalid email format. Email must contain exactly one '@' symbol."
    
    local_part, domain = email.split('@')
    
    # Local part validation
    if not local_part:
        return False, "Invalid email format. Email must have characters before '@'."
    
    # Domain must not be empty
    if not domain:
        return False, "Invalid email format. Email must have characters after '@'."
    
    # Domain must contain a dot
    if '.' not in domain:
        return False, "Invalid email format. Email must contain a valid domain extension (e.g., .com, .org)."
    
    # Split domain correctly – last dot is TLD
    try:
        domain_name, tld = domain.rsplit('.', 1)
    except ValueError:
        return False, "Invalid email structure."
    
    # Domain name must exist
    if not domain_name:
        return False, "Invalid email format. Domain name missing before extension."
    
    # TLD constraints: 2–3 letters only
    if not tld.isalpha():
        return False, "Invalid domain extension. Must contain only letters (e.g., .com, .in)."
    
    if len(tld) < 2 or len(tld) > 3:
        return False, "Invalid domain extension. Must be 2–3 letters only (e.g., .com, .org)."
    
    # List of common valid TLDs
    valid_tlds = {
        # Common gTLDs
        'com', 'org', 'net', 'edu', 'gov', 'mil',
        # Country codes (common ones)
        'in', 'uk', 'us', 'ca', 'au', 'de', 'fr', 'it', 'es', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi', 'pl', 'cz', 'ie', 'pt', 'gr', 'ro', 'hu', 'bg', 'hr', 'sk', 'si', 'lt', 'lv', 'ee', 'lu', 'mt', 'cy',
        'jp', 'cn', 'kr', 'tw', 'hk', 'sg', 'my', 'th', 'id', 'ph', 'vn', 'nz', 'za', 'eg', 'ma', 'ng', 'ke', 'tz', 'gh', 'et', 'ug', 'zm', 'zw', 'mw', 'mz', 'ao', 'bw', 'na', 'sz', 'ls', 'mg', 'mu', 'sc', 'km', 'dj', 'so', 'er', 'sd', 'ly', 'tn', 'dz', 'mr', 'ml', 'ne', 'td', 'cf', 'cm', 'gq', 'ga', 'cg', 'cd', 'bi', 'rw', 'ss', 'bf', 'ci', 'sn', 'gm', 'gn', 'gw', 'sl', 'lr', 'tg', 'bj', 'cv',
        'mx', 'br', 'ar', 'cl', 'co', 'pe', 've', 'ec', 'uy', 'py', 'bo', 'cr', 'pa', 'ni', 'hn', 'sv', 'gt', 'bz', 'do', 'cu', 'jm', 'tt', 'bb', 'gd', 'lc', 'vc', 'ag', 'bs', 'dm', 'ht', 'pr', 'vi',
        'ru', 'ua', 'by', 'kz', 'ge', 'am', 'az', 'tm', 'tj', 'kg', 'uz', 'mn', 'af', 'pk', 'bd', 'lk', 'np', 'bt', 'mv', 'mm', 'la', 'kh', 'bn',
        'il', 'jo', 'lb', 'sy', 'iq', 'ir', 'sa', 'ae', 'om', 'ye', 'kw', 'qa', 'bh', 'tr', 'cy',
        # Other common TLDs
        'io', 'co', 'me', 'tv', 'cc', 'ws', 'info', 'biz', 'name', 'pro', 'mobi', 'tel', 'asia', 'jobs', 'travel', 'xxx', 'aero', 'museum', 'coop', 'int'
    }
    
    # Validate TLD is in the list of valid extensions
    if tld not in valid_tlds:
        return False, "Invalid email format. Email must contain a valid domain extension such as .com, .in, .org, .net."
    
    # Global strict regex (prevents double dots, invalid chars, etc.)
    full_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,3}$"
    if not re.match(full_regex, email):
        return False, "Invalid email format. Please enter a valid email address."
    
    return True, ""

    
def request_email_verification(request):
    """First step: Request email verification before signup."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        if not email:
            messages.error(request, 'Email is required.')
            return render(request, 'accounts/request_email_verification.html')
        
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Invalid email address.')
            return render(request, 'accounts/request_email_verification.html')
        
        # Check if email already exists
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'accounts/request_email_verification.html')
        
        # Delete any existing pending verification for this email
        PendingEmailVerification.objects.filter(email=email).delete()
        
        # Generate token
        token = PendingEmailVerification.generate_token(email)
        
        # Store pending verification
        PendingEmailVerification.objects.create(
            email=email,
            token=token
        )
        
        # Build verification URL - point to frontend
        frontend_base_url = os.getenv('FRONTEND_BASE_URL', 'http://localhost:5173')
        verify_url = f"{frontend_base_url}/auth?tab=create&token={token}"
        
        # Determine from_email
        from_email = settings.DEFAULT_FROM_EMAIL
        if not from_email or '@localhost' in from_email or from_email == 'no-reply@localhost':
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Send verification email
        subject = "Verify your email for GenScholar"
        message = f"""Hello,

Please verify your email address to create your GenScholar account.

Click the link below to verify your email:
{verify_url}

This link will expire in 24 hours.

If you did not request this, you can safely ignore this email.

Thanks,
GenScholar Team"""
        
        # Debug: Print email configuration
        print(f"DEBUG: Sending email from {from_email} to {email}")
        print(f"DEBUG: EMAIL_BACKEND={settings.EMAIL_BACKEND}")
        print(f"DEBUG: EMAIL_HOST={settings.EMAIL_HOST}")
        print(f"DEBUG: EMAIL_PORT={settings.EMAIL_PORT}")
        print(f"DEBUG: EMAIL_USE_TLS={settings.EMAIL_USE_TLS}")
        
        try:
            # Verify email settings are loaded
            if not settings.EMAIL_HOST:
                raise ValueError("EMAIL_HOST is not configured in settings")
            if not settings.EMAIL_HOST_USER:
                raise ValueError("EMAIL_HOST_USER is not configured in settings")
            if not settings.EMAIL_HOST_PASSWORD:
                raise ValueError("EMAIL_HOST_PASSWORD is not configured in settings")
            
            # Use Django's email backend directly with explicit connection
            from django.core.mail import get_connection
            connection = get_connection(
                backend=settings.EMAIL_BACKEND,
                host=settings.EMAIL_HOST,
                port=settings.EMAIL_PORT,
                username=settings.EMAIL_HOST_USER,
                password=settings.EMAIL_HOST_PASSWORD,
                use_tls=settings.EMAIL_USE_TLS,
            )
            
            result = send_mail(
                subject,
                message,
                from_email,
                [email],
                fail_silently=False,
                connection=connection,
            )
            print(f"✓ Email sent successfully to {email} (result: {result})")
            messages.success(request, f'Verification link sent to {email}. Please check your email.')
        except Exception as e:
            error_msg = str(e)
            print(f"✗ ERROR sending verification email: {error_msg}")
            print(f"  From: {from_email}")
            print(f"  To: {email}")
            print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
            print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
            print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
            print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
            print(f"  EMAIL_HOST_PASSWORD: {'SET (' + str(len(settings.EMAIL_HOST_PASSWORD)) + ' chars)' if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
            print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
            import traceback
            traceback.print_exc()
            # Show error to user but don't reveal sensitive details
            if "authentication" in error_msg.lower() or "535" in error_msg or "534" in error_msg or "535-5.7.8" in error_msg:
                messages.error(request, 'Email authentication failed. Please verify your SMTP credentials are correct.')
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower() or "refused" in error_msg.lower():
                messages.error(request, 'Could not connect to email server. Please check your internet connection and that SMTP is accessible.')
            elif "ssl" in error_msg.lower() or "tls" in error_msg.lower():
                messages.error(request, 'SSL/TLS connection error. Please check EMAIL_USE_TLS setting.')
            else:
                messages.error(request, f'Failed to send verification email. Please check the server console for details. Error: {error_msg[:150]}')
            return render(request, 'accounts/request_email_verification.html')
        
        return render(request, 'accounts/request_email_verification.html', {'email_sent': True, 'email': email})
    
    return render(request, 'accounts/request_email_verification.html')


def verify_email_token(request):
    """Second step: Verify email token and show signup form."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    token = request.GET.get('token', '')
    
    if not token:
        messages.error(request, 'Invalid verification link.')
        return redirect('request_email_verification')
    
    # Verify token
    email = PendingEmailVerification.verify_token(token)
    
    if not email:
        messages.error(request, 'Invalid or expired verification link.')
        return redirect('request_email_verification')
    
    # Check if pending verification exists and is not expired
    try:
        pending = PendingEmailVerification.objects.get(email=email, token=token)
        if pending.is_expired():
            pending.delete()
            messages.error(request, 'Verification link has expired. Please request a new one.')
            return redirect('request_email_verification')
    except PendingEmailVerification.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('request_email_verification')
    
    # Store verified email in session for signup
    request.session['verified_email'] = email
    request.session['verification_token'] = token
    
    # Show signup form with pre-filled email
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            # Ensure email matches verified email
            if form.cleaned_data.get('email', '').lower() != email.lower():
                messages.error(request, 'Email must match the verified email address.')
                return render(request, 'accounts/signup.html', {
                    'form': form,
                    'verified_email': email,
                    'token': token
                })
            
            user = form.save(request)
            
            # Mark email as verified in allauth
            from allauth.account.models import EmailAddress
            try:
                email_address = EmailAddress.objects.get(user=user, email=user.email)
                email_address.verified = True
                email_address.primary = True
                email_address.save()
            except EmailAddress.DoesNotExist:
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=True,
                    primary=True
                )
            
            # Delete pending verification
            pending.delete()
            
            # Clear session
            request.session.pop('verified_email', None)
            request.session.pop('verification_token', None)
            
            # Login user
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('dashboard')
    else:
        # Pre-fill form with verified email
        form = SignupForm(initial={'email': email})
    
    return render(request, 'accounts/signup.html', {
        'form': form,
        'verified_email': email,
        'token': token
    })


def signup_view(request):
    """Redirect to email verification request."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('request_email_verification')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # authenticate() sets user.backend automatically, but we can use it explicitly
            login(request, user, backend=user.backend)
            return redirect('dashboard')
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'accounts/login.html')


# JSON API Views for frontend integration

@ensure_csrf_cookie
def api_csrf_view(request):
    """JSON API endpoint to get CSRF token and ensure cookie is set."""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    token = get_token(request)
    response = JsonResponse({"success": True, "data": {"csrf_token": token}})
    # Cookie is already set by @ensure_csrf_cookie, but we can also set it explicitly
    response.set_cookie(
        'csrftoken',
        token,
        secure=True,
        samesite='None',
        httponly=False
    )
    return response


def api_login_view(request):
    """JSON API endpoint for user login. Accepts username OR email as identifier."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    
    try:
        data = json.loads(request.body)
        identifier = data.get('identifier')  # Can be username or email
        password = data.get('password')
        
        if not identifier or not password:
            return JsonResponse({"success": False, "message": "Email/username and password are required"}, status=400)
        
        if len(password) > 15:
            return JsonResponse({"success": False, "message": "Password must be at most 15 characters long"}, status=400)
        
        # authenticate() will try all backends, including our UsernameOrEmailBackend
        # Pass identifier as username parameter - our backend will handle username OR email
        user = authenticate(request, username=identifier, password=password)
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


def api_signup_view(request):
    """JSON API endpoint for user signup. Requires verified OTP, username, and password."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    
    try:
        data = json.loads(request.body)
        username = data.get('username', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')

        # -----------------------
        # REQUIRED FIELD CHECKS
        # -----------------------
        if not username:
            return JsonResponse({"success": False, "message": "Username is required"}, status=400)

        if not email:
            return JsonResponse({"success": False, "message": "Email is required"}, status=400)

        # Normalize email
        email = email.strip().lower()

        # Strict email validation
        is_valid, error_msg = validate_email_strict(email)
        if not is_valid:
            return JsonResponse({"success": False, "message": error_msg}, status=400)

        # Email already registered?
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({"success": False, "message": "Email already exists"}, status=400)

        if not password:
            return JsonResponse({"success": False, "message": "Password is required"}, status=400)
        if not confirm_password:
            return JsonResponse({"success": False, "message": "Please confirm your password"}, status=400)

        # Check password match
        if password != confirm_password:
            return JsonResponse({"success": False, "message": "Passwords do not match"}, status=400)

        # -----------------------
        # OTP CHECK
        # -----------------------
        try:
            email_otp = EmailOTP.objects.get(email=email)
            if not email_otp.is_verified:
                return JsonResponse({"success": False, "message": "Email verification required. Please verify your email with OTP first."}, status=400)
        except EmailOTP.DoesNotExist:
            return JsonResponse({"success": False, "message": "Email verification required. Please verify your email with OTP first."}, status=400)

        # -----------------------
        # USERNAME VALIDATION
        # -----------------------
        if len(username) < 3:
            return JsonResponse({"success": False, "message": "Username must be at least 3 characters long"}, status=400)

        if len(username) > 15:
            return JsonResponse({"success": False, "message": "Username must be at most 15 characters long"}, status=400)

        if User.objects.filter(username__iexact=username).exists():
            return JsonResponse({"success": False, "message": "Username already exists"}, status=400)

        # -----------------------
        # PASSWORD VALIDATION
        # -----------------------
        username_lower = username.lower()
        password_lower = password.lower()

        # Must not equal username
        if password_lower == username_lower:
            return JsonResponse({"success": False, "message": "Password must not equal the username"}, status=400)

        # Must not contain username
        if username_lower in password_lower:
            return JsonResponse({"success": False, "message": "Password must not contain the username"}, status=400)

        # Must not contain reversed username
        if username_lower[::-1] in password_lower:
            return JsonResponse({"success": False, "message": "Password must not contain the reversed username"}, status=400)

        # Length
        if len(password) < 8:
            return JsonResponse({"success": False, "message": "Password must be at least 8 characters long"}, status=400)

        if len(password) > 15:
            return JsonResponse({"success": False, "message": "Password must be at most 15 characters long"}, status=400)

        # Uppercase
        if not re.search(r"[A-Z]", password):
            return JsonResponse({"success": False, "message": "Password must contain at least one uppercase letter"}, status=400)

        # Lowercase
        if not re.search(r"[a-z]", password):
            return JsonResponse({"success": False, "message": "Password must contain at least one lowercase letter"}, status=400)

        # Number
        if not re.search(r"\d", password):
            return JsonResponse({"success": False, "message": "Password must contain at least one number"}, status=400)

        # Special character
        if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]", password):
            return JsonResponse({"success": False, "message": "Password must contain at least one special character"}, status=400)

        # -----------------------
        # CREATE USER
        # -----------------------
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Mark email verified in allauth
        from allauth.account.models import EmailAddress
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True}
        )

        # Delete OTP after successful signup
        email_otp.delete()

        # Auto-login
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        return JsonResponse({
            "success": True,
            "data": {"user": {"id": user.id, "username": user.username}}
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


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


def resend_verification_email_view(request):
    """Resend email verification for a user."""
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                adapter = get_adapter(request)
                adapter.send_confirmation_mail(request, user, signup=True)
                messages.success(request, f'Verification email sent to {email}')
            except User.DoesNotExist:
                messages.error(request, 'User not found')
        else:
            messages.error(request, 'Email is required')
    return redirect('signup')


@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def api_request_email_verification_view(request):
    """API endpoint to send OTP email for verification."""
    if request.method == "OPTIONS":
        return HttpResponse(status=200)
    
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        
        if not email:
            return JsonResponse({"success": False, "message": "Email is required"}, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"success": False, "message": "Invalid email address"}, status=400)
        
        # Check if email already exists
        if User.objects.filter(email__iexact=email).exists():
            return JsonResponse({"success": False, "message": "An account with this email already exists"}, status=400)
        
        # Delete any existing OTP for this email
        EmailOTP.objects.filter(email=email).delete()
        
        # Generate 6-digit OTP
        otp = EmailOTP.generate_otp()
        
        # Store OTP
        EmailOTP.objects.create(
            email=email,
            otp=otp,
            is_verified=False
        )
        
        # Determine from_email
        from_email = settings.DEFAULT_FROM_EMAIL
        if not from_email or '@localhost' in from_email or from_email == 'no-reply@localhost':
            from_email = settings.DEFAULT_FROM_EMAIL
        
        # Send OTP email
        subject = "Your GenScholar Verification Code"
        message = f"""Your 6-digit verification code is: {otp}
This code expires in 10 minutes."""
        
        # Use Django's email backend directly with explicit connection
        from django.core.mail import get_connection
        connection = get_connection(
            backend=settings.EMAIL_BACKEND,
            host=settings.EMAIL_HOST,
            port=settings.EMAIL_PORT,
            username=settings.EMAIL_HOST_USER,
            password=settings.EMAIL_HOST_PASSWORD,
            use_tls=settings.EMAIL_USE_TLS,
        )
        
        try:
            result = send_mail(
                subject,
                message,
                from_email,
                [email],
                fail_silently=False,
                connection=connection,
            )
            print(f"✓ OTP email sent successfully to {email} (result: {result})")
            return JsonResponse({
                "success": True,
                "data": {"message": f"OTP sent to {email}"}
            })
        except Exception as e:
            error_msg = str(e)
            print(f"✗ ERROR sending OTP email: {error_msg}")
            import traceback
            traceback.print_exc()
            # Provide helpful error messages
            if "authentication" in error_msg.lower() or "535" in error_msg or "534" in error_msg or "535-5.7.8" in error_msg:
                return JsonResponse({
                    "success": False,
                    "message": "Email authentication failed. Please verify your SMTP credentials are correct."
                }, status=500)
            elif "connection" in error_msg.lower() or "timeout" in error_msg.lower() or "refused" in error_msg.lower():
                return JsonResponse({
                    "success": False,
                    "message": "Could not connect to email server. Please check your internet connection and that SMTP is accessible."
                }, status=500)
            else:
                return JsonResponse({
                    "success": False,
                    "message": f"Failed to send OTP email: {error_msg[:150]}"
                }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def api_verify_email_token_view(request):
    """API endpoint to verify email token and return token for signup."""
    token = request.GET.get('token', '')
    
    if not token:
        return JsonResponse({"success": False, "message": "Token is required"}, status=400)
    
    # Verify token
    email = PendingEmailVerification.verify_token(token)
    
    if not email:
        return JsonResponse({"success": False, "message": "Invalid or expired verification token"}, status=400)
    
    # Check if pending verification exists and is not expired
    try:
        pending = PendingEmailVerification.objects.get(email=email, token=token)
        if pending.is_expired():
            pending.delete()
            return JsonResponse({"success": False, "message": "Verification token has expired. Please request a new one."}, status=400)
    except PendingEmailVerification.DoesNotExist:
        return JsonResponse({"success": False, "message": "Invalid verification token"}, status=400)
    
    return JsonResponse({
        "success": True,
        "data": {
            "email": email,
            "token": token,
            "message": "Email verified successfully"
        }
    })


@require_http_methods(["POST"])
def api_verify_otp_view(request):
    """API endpoint to verify OTP."""
    if request.user.is_authenticated:
        return JsonResponse({
            "success": True,
            "data": {"user": {"id": request.user.id, "username": request.user.username}}
        })
    
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip().lower()
        otp = data.get('otp', '').strip()
        
        if not email:
            return JsonResponse({"success": False, "message": "Email is required"}, status=400)
        
        if not otp:
            return JsonResponse({"success": False, "message": "OTP is required"}, status=400)
        
        if len(otp) != 6 or not otp.isdigit():
            return JsonResponse({"success": False, "message": "Invalid OTP format"}, status=400)
        
        try:
            validate_email(email)
        except ValidationError:
            return JsonResponse({"success": False, "message": "Invalid email address"}, status=400)
        
        # Check if OTP exists for this email
        try:
            email_otp = EmailOTP.objects.get(email=email)
        except EmailOTP.DoesNotExist:
            return JsonResponse({"success": False, "message": "OTP not sent for this email"}, status=400)
        
        # Check if OTP is expired
        if email_otp.is_expired():
            email_otp.delete()
            return JsonResponse({"success": False, "message": "OTP expired"}, status=400)
        
        # Verify OTP
        if email_otp.otp != otp:
            return JsonResponse({"success": False, "message": "Invalid OTP"}, status=400)
        
        # Mark as verified
        email_otp.is_verified = True
        email_otp.save()
        
        return JsonResponse({
            "success": True,
            "data": {
                "email": email,
                "message": "OTP verified successfully"
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@require_http_methods(["GET"])
def api_profile_view(request):
    """JSON API endpoint to get current user profile with stats."""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "message": "Not authenticated"}, status=401)
    
    try:
        user = request.user
        
        # Get stats from related models
        from chat.models import ChatMessage
        from pdfs.models import PDFFile
        
        total_messages = ChatMessage.objects.filter(user=user).count()
        total_pdfs_uploaded = PDFFile.objects.filter(uploaded_by=user).count()
        
        # Build profile data
        profile_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name or "",
            "last_name": user.last_name or "",
            "date_joined": user.date_joined.isoformat() if user.date_joined else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "stats": {
                "total_messages": total_messages,
                "total_pdfs_uploaded": total_pdfs_uploaded,
            }
        }
        
        return JsonResponse({
            "success": True,
            "data": {"profile": profile_data}
        })
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# -----------------------
# UPDATE CREDENTIALS API
# -----------------------
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import re
import json
from django.db import transaction

@require_http_methods(["POST"])
@login_required
def api_update_credentials_view(request):
    try:
        data = json.loads(request.body or "{}")
    except Exception:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    new_username = (data.get("new_username") or "").strip()
    new_password = (data.get("new_password") or "").strip()

    user = request.user
    errors = []

    # ---------- Username validation ----------
    if new_username:
        if len(new_username) < 3:
            errors.append("Username must be at least 3 characters long")
        elif User.objects.filter(username__iexact=new_username).exclude(pk=user.pk).exists():
            errors.append("Username already exists")

    # ---------- Password validation ----------
    if new_password:

        # Must not equal username
        if new_password.lower() == (new_username or user.username).lower():
            errors.append("Password must not equal the username")

        uname = (new_username or user.username).lower()

        # Must not contain username
        if uname in new_password.lower():
            errors.append("Password must not contain the username")

        # Must not contain reversed username
        if uname[::-1] in new_password.lower():
            errors.append("Password must not contain the reversed username")

        # Specific policies one by one (because tests expect separate messages)
        if len(new_password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", new_password):
            errors.append("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", new_password):
            errors.append("Password must contain at least one lowercase letter")

        if not re.search(r"\d", new_password):
            errors.append("Password must contain at least one number")

        if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]", new_password):
            errors.append("Password must contain at least one special character")

    # ---------- Return first error ----------
    if errors:
        return JsonResponse({"success": False, "message": errors[0]}, status=400)

    # ---------- Save changes ----------
    try:
        with transaction.atomic():
            if new_username:
                user.username = new_username
            if new_password:
                user.set_password(new_password)
            user.save()
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

    # ---------- SUCCESS FORMAT required by tests ----------
    return JsonResponse({
        "success": True,
        "data": {
            "message": "Credentials updated successfully. Please log in again."
        }
    }, status=200)
