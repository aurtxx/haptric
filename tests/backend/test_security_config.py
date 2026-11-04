import pytest
from django.conf import settings
from django.test import override_settings
from django.test.client import Client


@pytest.mark.django_db
def test_configured_frontend_origin_gets_credentialed_cors_header():
    with override_settings(CORS_ALLOWED_ORIGINS=["http://127.0.0.1:5174"], CORS_ALLOW_CREDENTIALS=True):
        response = Client().get("/health/", HTTP_ORIGIN="http://127.0.0.1:5174")
    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "http://127.0.0.1:5174"
    assert response["Access-Control-Allow-Credentials"] == "true"


def test_cors_and_csrf_defaults_never_use_wildcards():
    assert "*" not in settings.CORS_ALLOWED_ORIGINS
    assert "*" not in settings.CSRF_TRUSTED_ORIGINS
    assert settings.CORS_ALLOW_CREDENTIALS is True
