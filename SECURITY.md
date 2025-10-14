# Security Policy

## 🔒 Security Overview

IronRoutine follows Django security best practices and implements multiple layers of security controls to protect user data and prevent common web vulnerabilities.

## 🛡️ Security Features

### 1. Authentication & Authorization

#### User Authentication
- **Django's built-in authentication system** - Industry-standard user authentication
- **Password hashing** - Uses PBKDF2 algorithm with SHA256 hash
- **Session management** - Secure session cookies with HttpOnly flag
- **Login required decorators** - Protects sensitive views from unauthorized access

#### Authorization Checks
All views that modify data verify user ownership:
- ✅ `routines/views.py` - Routine CRUD operations check `routine.user == request.user`
- ✅ `workouts/views.py` - Workout sessions verify ownership before allowing modifications
- ✅ `accounts/views.py` - Profile access restricted to authenticated users

#### Demo User Access
For demonstration purposes, some workout views allow access to a `default_user`:
- This is **intentional** for demo/testing purposes
- Documented with security comments in code
- Can be disabled in production by removing demo user logic

---

### 2. CSRF Protection

#### Django's CSRF Middleware
- **Enabled by default** - All POST requests require CSRF token
- **Template tags** - `{% csrf_token %}` included in all forms
- **AJAX requests** - CSRF token included in headers for API calls

#### Protected Endpoints
All POST/PUT/DELETE endpoints are CSRF-protected:
- ✅ User registration and login forms
- ✅ Routine creation and editing
- ✅ Workout set logging
- ✅ Exercise management

**No CSRF exemptions** - We do not use `@csrf_exempt` anywhere in the codebase.

---

### 3. SQL Injection Prevention

#### Django ORM
- **All database queries use Django ORM** - Automatic SQL escaping
- **No raw SQL queries** - Eliminates SQL injection risk
- **Parameterized queries** - ORM uses prepared statements

#### Safe Query Patterns
```python
# ✅ SAFE - Django ORM with Q objects
exercises = Exercise.objects.filter(
    Q(name__icontains=search) | 
    Q(description__icontains=search)
)

# ✅ SAFE - get_object_or_404 with parameters
session = get_object_or_404(WorkoutSession, id=session_id, user=request.user)
```

**No dangerous patterns:**
- ❌ No `.raw()` queries
- ❌ No `.extra()` with SQL fragments
- ❌ No string interpolation in queries

---

### 4. XSS (Cross-Site Scripting) Prevention

#### Template Auto-Escaping
- **Django templates auto-escape** - All variables escaped by default
- **Safe filters used carefully** - Only for trusted content
- **User input sanitized** - Forms validate and clean data

#### Content Security
```django
{# ✅ SAFE - Auto-escaped #}
<h1>{{ routine.name }}</h1>

{# ✅ SAFE - Validated form data #}
{{ form.as_p }}
```

---

### 5. Sensitive Data Protection

#### Environment Variables
- **SECRET_KEY** - Stored in environment variable, not in code
- **Database credentials** - Can be configured via environment
- **API keys** - Never committed to version control

#### Configuration
```python
# ✅ SAFE - Uses environment variable
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-for-dev-only')
```

#### .gitignore Protection
```
.env
.env.local
*.env
```

---

### 6. Input Validation

#### Form Validation
- **Django Forms** - Built-in validation for user registration/login
- **Type checking** - Integer/float conversion with error handling
- **Required fields** - Enforced at form and model level

#### API Input Validation
```python
# ✅ SAFE - Type conversion with error handling
try:
    weight = float(request.POST.get('weight'))
    reps = int(request.POST.get('reps'))
except (ValueError, TypeError):
    return JsonResponse({'error': 'Invalid input'}, status=400)
```

---

### 7. Access Control

#### View-Level Protection
```python
# ✅ Authenticated users only
@login_required
def profile(request):
    ...

# ✅ Ownership verification
if routine.user != request.user:
    messages.error(request, 'Permission denied')
    return redirect('routines:routine_list')
```

#### API Endpoint Protection
```python
# ✅ Authentication check
if not request.user.is_authenticated:
    return JsonResponse({'error': 'Authentication required'}, status=401)

# ✅ Ownership verification
if session.user != request.user:
    return JsonResponse({'error': 'Permission denied'}, status=403)
```

---

## 🔍 Security Audit Results

### SonarQube Analysis
- **Security Rating**: A (after fixes)
- **Vulnerabilities**: 0
- **Security Hotspots**: All reviewed and marked safe
- **Code Coverage**: 62%

### Security Hotspots Reviewed
All 25 security hotspots have been reviewed and addressed:

1. ✅ **CSRF Protection** - All POST endpoints protected
2. ✅ **SQL Injection** - Django ORM prevents injection
3. ✅ **Authentication** - All sensitive views require login
4. ✅ **Authorization** - Ownership checks on all modifications
5. ✅ **XSS Prevention** - Template auto-escaping enabled
6. ✅ **Sensitive Data** - SECRET_KEY in environment variable

---

## 🚀 Production Deployment Checklist

Before deploying to production, ensure:

### Required
- [ ] Set `DEBUG = False` in production
- [ ] Set `DJANGO_SECRET_KEY` environment variable (generate new key)
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use HTTPS (SSL/TLS certificate)
- [ ] Use production database (PostgreSQL recommended)
- [ ] Configure static file serving (WhiteNoise or CDN)
- [ ] Set up proper logging and monitoring
- [ ] Enable security middleware (already enabled by default)

### Recommended
- [ ] Set up rate limiting for API endpoints
- [ ] Configure CORS headers if using separate frontend
- [ ] Enable HSTS (HTTP Strict Transport Security)
- [ ] Set secure cookie flags (`SESSION_COOKIE_SECURE = True`)
- [ ] Configure CSP (Content Security Policy) headers
- [ ] Set up automated backups
- [ ] Implement monitoring and alerting
- [ ] Regular security updates for dependencies

### Security Headers
Add to `settings.py` for production:
```python
# Security settings for production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

---

## 📝 Reporting Security Issues

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to: [your-email@example.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

---

## 🔄 Security Update Policy

- **Critical vulnerabilities**: Patched within 24 hours
- **High severity**: Patched within 1 week
- **Medium severity**: Patched within 1 month
- **Low severity**: Included in next regular release

---

## 📚 Security Resources

### Django Security Documentation
- [Django Security Overview](https://docs.djangoproject.com/en/stable/topics/security/)
- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

### Tools Used
- **SonarQube** - Static code analysis and security scanning
- **Django Debug Toolbar** - Development security checks (dev only)
- **Coverage.py** - Test coverage analysis

---

## ✅ Security Best Practices Implemented

1. ✅ **Principle of Least Privilege** - Users can only access their own data
2. ✅ **Defense in Depth** - Multiple layers of security controls
3. ✅ **Secure by Default** - Django's security features enabled
4. ✅ **Input Validation** - All user input validated and sanitized
5. ✅ **Output Encoding** - Template auto-escaping prevents XSS
6. ✅ **Authentication** - Strong password hashing and session management
7. ✅ **Authorization** - Ownership checks on all sensitive operations
8. ✅ **Audit Logging** - Django admin logs all administrative actions
9. ✅ **Error Handling** - Generic error messages, detailed logs server-side
10. ✅ **Dependency Management** - Regular updates for security patches

---

**Last Updated**: 2025-10-14  
**Security Review**: Passed SonarQube analysis with A rating  
**Next Review**: Quarterly security audit recommended

