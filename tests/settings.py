import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))

TEMPLATE_DEBUG = True


class HighlightBrokenVariable:
    def __contains__(self, item):
        return True

    def __mod__(self, other):
        raise Exception(f'Tried to render non-existent variable {other}')


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': TEMPLATE_DEBUG,
            'string_if_invalid': HighlightBrokenVariable(),
            'context_processors': [
                'tests.context_processors.context_processor_is_called',
            ],
        },
    },
]

SECRET_KEY = "foobar"
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'iommi',
    'archive',
    'authentication',
    'crud',
    # 'forum',  # TODO: using VARBINARY which sqlite doesn't support
    'forum2',
    # 'issues',
    'unread',
    # 'issues',
    'tests',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

IOMMI_DEFAULT_STYLE = 'test'


ROOT_URLCONF = 'tests.urls'
