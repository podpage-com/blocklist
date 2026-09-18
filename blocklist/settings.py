import os
from pathlib import Path
import dj_database_url

BASE_DIR=Path(__file__).resolve().parent.parent
DEBUG=os.getenv("DEBUG","0")=="1"
SECRET_KEY=os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG: SECRET_KEY="unsafe-development-key"
    else: raise RuntimeError("SECRET_KEY is required when DEBUG=0")

ALLOWED_HOSTS=[x.strip() for x in os.getenv("ALLOWED_HOSTS","localhost,127.0.0.1").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS=[x.strip() for x in os.getenv("CSRF_TRUSTED_ORIGINS","").split(",") if x.strip()]
INSTALLED_APPS=["django.contrib.admin","django.contrib.auth","django.contrib.contenttypes","django.contrib.sessions","django.contrib.messages","django.contrib.staticfiles","rest_framework","exchange"]
MIDDLEWARE=["django.middleware.security.SecurityMiddleware","whitenoise.middleware.WhiteNoiseMiddleware","django.contrib.sessions.middleware.SessionMiddleware","django.middleware.common.CommonMiddleware","django.middleware.csrf.CsrfViewMiddleware","django.contrib.auth.middleware.AuthenticationMiddleware","django.contrib.messages.middleware.MessageMiddleware","django.middleware.clickjacking.XFrameOptionsMiddleware"]
ROOT_URLCONF="blocklist.urls"
TEMPLATES=[{"BACKEND":"django.template.backends.django.DjangoTemplates","DIRS":[BASE_DIR/"templates"],"APP_DIRS":True,"OPTIONS":{"context_processors":["django.template.context_processors.request","django.contrib.auth.context_processors.auth","django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION="blocklist.wsgi.application"
DATABASES={"default":dj_database_url.config(default=f"sqlite:///{BASE_DIR/'db.sqlite3'}",conn_max_age=600,ssl_require=(not DEBUG and bool(os.getenv("DATABASE_URL"))))}
AUTH_PASSWORD_VALIDATORS=[
 {"NAME":"django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
 {"NAME":"django.contrib.auth.password_validation.MinimumLengthValidator"},
 {"NAME":"django.contrib.auth.password_validation.CommonPasswordValidator"},
 {"NAME":"django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE="en-us"; TIME_ZONE="UTC"; USE_I18N=True; USE_TZ=True
STATIC_URL="static/"; STATIC_ROOT=BASE_DIR/"staticfiles"
STORAGES={"staticfiles":{"BACKEND":"whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD="django.db.models.BigAutoField"
DEFAULT_OBSERVATION_TTL_DAYS=int(os.getenv("DEFAULT_OBSERVATION_TTL_DAYS","7"))
MAX_SYNC_ITEMS=int(os.getenv("MAX_SYNC_ITEMS","10000"))
MAX_METADATA_BYTES=int(os.getenv("MAX_METADATA_BYTES","8192"))
REST_FRAMEWORK={
 "DEFAULT_AUTHENTICATION_CLASSES":["exchange.authentication.ApiKeyAuthentication"],
 "DEFAULT_PERMISSION_CLASSES":["rest_framework.permissions.IsAuthenticated"],
 "DEFAULT_PAGINATION_CLASS":"rest_framework.pagination.PageNumberPagination",
 "PAGE_SIZE":100,"MAX_PAGE_SIZE":1000,
 "DEFAULT_THROTTLE_CLASSES":["rest_framework.throttling.ScopedRateThrottle"],
 "DEFAULT_THROTTLE_RATES":{"read":"120/min","write":"60/min","sync":"12/min"},
}
SECURE_PROXY_SSL_HEADER=("HTTP_X_FORWARDED_PROTO","https")
SESSION_COOKIE_SECURE=not DEBUG
CSRF_COOKIE_SECURE=not DEBUG
SECURE_SSL_REDIRECT=not DEBUG
SECURE_HSTS_SECONDS=0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS="DENY"
