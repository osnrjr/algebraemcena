"""
Configurações do projeto Álgebra em Cena (pacote `config`).

Valores sensíveis e de ambiente vêm do `.env` via django-environ (Doc ① §4.4).
Baseline de segurança: Doc ① §12.3. Parâmetros do projeto: PROJECT_SPEC §10.
"""

from pathlib import Path

import environ
from django.contrib.messages import constants as messages
from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

# Transporte (HTTPS)
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=not DEBUG)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0 if DEBUG else 3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=False)
SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False)

# Cookies, sessão e CSRF
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 28800  # 8 h (PROJECT_SPEC §9.3)

# Cabeçalhos
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

# Limites de entrada (Doc ① §15.4)
DATA_UPLOAD_MAX_MEMORY_SIZE = env.int('DATA_UPLOAD_MAX_MEMORY_SIZE', default=1_048_576)
DATA_UPLOAD_MAX_NUMBER_FIELDS = env.int('DATA_UPLOAD_MAX_NUMBER_FIELDS', default=500)

# CSP nativa (Django >= 6.0, Doc ① §14.3). Imposta desde o início: o projeto nasce sem
# estilo/script inline. `media-src 'self'` para os vídeos MP4 (PROJECT_SPEC §10.1).
CDN = 'https://cdn.jsdelivr.net'
# Vídeo de apresentação (landing): IFrame API do YouTube + player em youtube-nocookie.
# A API só é carregada quando o visitante clica em "play" (static/js/player-video.js).
YOUTUBE_API = 'https://www.youtube.com'
YOUTUBE_PLAYER = 'https://www.youtube-nocookie.com'
VIDEO_APRESENTACAO_ID = env('VIDEO_APRESENTACAO_ID', default='7zyystx4zNU')
SECURE_CSP = {
    'default-src': [CSP.SELF],
    'script-src': [CSP.SELF, CSP.NONCE, CDN, YOUTUBE_API],
    'frame-src': [YOUTUBE_PLAYER],
    'style-src': [CSP.SELF, CSP.NONCE, CDN],
    'img-src': [CSP.SELF, 'data:'],
    'font-src': [CSP.SELF, CDN],
    'connect-src': [CSP.SELF],
    'media-src': [CSP.SELF],
    'object-src': [CSP.NONE],
    'base-uri': [CSP.SELF],
    'form-action': [CSP.SELF],
    'frame-ancestors': [CSP.NONE],
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.core',
    'apps.accounts',
    'apps.site',
    'apps.sistemas',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.csp.ContentSecurityPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.template.context_processors.csp',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.site.context_processors.tema',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR / "db.sqlite3"}'),
}

AUTH_USER_MODEL = 'accounts.User'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
PASSWORD_RESET_TIMEOUT = 3600

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

ADMIN_URL = env('ADMIN_URL')

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# E-mail: console no desenvolvimento; SMTP com TLS fora dele (credenciais no .env)
if DEBUG:
    MAILERS = {'default': {'BACKEND': 'django.core.mail.backends.console.EmailBackend'}}
else:
    MAILERS = {
        'default': {
            'BACKEND': 'django.core.mail.backends.smtp.EmailBackend',
            'OPTIONS': {
                'host': env('EMAIL_HOST', default='localhost'),
                'port': env.int('EMAIL_PORT', default=587),
                'username': env('EMAIL_HOST_USER', default=''),
                'password': env('EMAIL_HOST_PASSWORD', default=''),
                'use_tls': True,
            },
        },
    }
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='nao-responda@localhost')

MESSAGE_TAGS = {messages.ERROR: 'danger'}

TENANCY_MODE = env('TENANCY_MODE', default='single')

# Tema padrão do produto (PROJECT_SPEC §4.2)
TEMA_PADRAO = env('TEMA_PADRAO', default='t08')

# Rate limit da aplicação (Doc ① §19; PROJECT_SPEC §10.1). Em produção, usar cache compartilhado.
CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
}
RATELIMIT_LOGIN = '5/m'
RATELIMIT_RESOLVER = '30/m'
TEMA_EXTENSOES = ['apps.sistemas.cores.tokens_css']
RATELIMIT_SENHA = '3/h'
RATELIMIT_EXPERIMENTO = '120/m'   # eventos do vídeo da landing (sendBeacon)
