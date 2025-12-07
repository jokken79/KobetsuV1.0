"""
Tests de seguridad para endpoints críticos
Verifica que todos los endpoints protegidos requieren autenticación
"""
import pytest
from fastapi.testclient import TestClient


class TestSecurityEndpoints:
    """Tests de seguridad para endpoints protegidos."""

    def test_delete_all_requires_auth(self, client: TestClient):
        """DELETE /delete-all DEBE requerir autenticación."""
        response = client.delete("/api/v1/kobetsu/delete-all")

        # Debe rechazar sin auth - 401 o 403
        assert response.status_code in [401, 403, 405], \
            f"DELETE /delete-all debería requerir auth, got {response.status_code}"

    def test_kobetsu_list_requires_auth(self, client: TestClient):
        """GET /kobetsu requiere autenticación."""
        response = client.get("/api/v1/kobetsu")
        assert response.status_code in [401, 403]

    def test_kobetsu_create_requires_auth(self, client: TestClient):
        """POST /kobetsu requiere autenticación."""
        response = client.post("/api/v1/kobetsu", json={})
        assert response.status_code in [401, 403, 422]

    def test_kobetsu_get_by_id_requires_auth(self, client: TestClient):
        """GET /kobetsu/{id} requiere autenticación."""
        response = client.get("/api/v1/kobetsu/1")
        assert response.status_code in [401, 403]

    def test_kobetsu_update_requires_auth(self, client: TestClient):
        """PUT /kobetsu/{id} requiere autenticación."""
        response = client.put("/api/v1/kobetsu/1", json={})
        assert response.status_code in [401, 403, 422]

    def test_kobetsu_delete_requires_auth(self, client: TestClient):
        """DELETE /kobetsu/{id} requiere autenticación."""
        response = client.delete("/api/v1/kobetsu/1")
        assert response.status_code in [401, 403]

    def test_kobetsu_stats_requires_auth(self, client: TestClient):
        """GET /kobetsu/stats requiere autenticación."""
        response = client.get("/api/v1/kobetsu/stats")
        assert response.status_code in [401, 403]

    def test_kobetsu_activate_requires_auth(self, client: TestClient):
        """POST /kobetsu/{id}/activate requiere autenticación."""
        response = client.post("/api/v1/kobetsu/1/activate")
        assert response.status_code in [401, 403]

    def test_kobetsu_renew_requires_auth(self, client: TestClient):
        """POST /kobetsu/{id}/renew requiere autenticación."""
        response = client.post("/api/v1/kobetsu/1/renew")
        assert response.status_code in [401, 403]

    def test_factory_list_requires_auth(self, client: TestClient):
        """GET /factories requiere autenticación."""
        response = client.get("/api/v1/factories")
        assert response.status_code in [401, 403]

    def test_factory_create_requires_auth(self, client: TestClient):
        """POST /factories requiere autenticación."""
        response = client.post("/api/v1/factories", json={})
        assert response.status_code in [401, 403, 422]

    def test_employee_list_requires_auth(self, client: TestClient):
        """GET /employees requiere autenticación."""
        response = client.get("/api/v1/employees")
        assert response.status_code in [401, 403]

    def test_import_requires_auth(self, client: TestClient):
        """POST /import/* requiere autenticación."""
        response = client.post("/api/v1/import/employees/preview")
        assert response.status_code in [401, 403, 422]


class TestAuthEndpointSecurity:
    """Tests de seguridad para endpoints de autenticación."""

    def test_login_returns_generic_error(self, client: TestClient):
        """Login no debe revelar si el usuario existe."""
        # Usuario que no existe
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@test.com", "password": "wrongpass"}
        )

        # El mensaje no debe indicar específicamente qué falló
        if response.status_code in [400, 401]:
            data = response.json()
            detail = str(data.get("detail", "")).lower()

            # No debe decir "user not found" explícitamente
            assert "user not found" not in detail
            assert "no such user" not in detail
            # Mensajes genéricos son aceptables
            assert "invalid" in detail or "incorrect" in detail or "credentials" in detail

    def test_login_with_valid_credentials(
        self,
        client: TestClient,
        test_user
    ):
        """Login con credenciales válidas debe retornar tokens."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_wrong_password(
        self,
        client: TestClient,
        test_user
    ):
        """Login con contraseña incorrecta debe fallar."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )

        assert response.status_code in [400, 401]

    def test_login_with_inactive_user(
        self,
        client: TestClient,
        test_inactive_user
    ):
        """Login con usuario inactivo debe fallar."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "testpassword"}
        )

        assert response.status_code in [400, 401, 403]


class TestTokenSecurity:
    """Tests de seguridad para manejo de tokens."""

    def test_invalid_token_rejected(self, client: TestClient):
        """Token inválido debe ser rechazado."""
        response = client.get(
            "/api/v1/kobetsu",
            headers={"Authorization": "Bearer invalid-token-here"}
        )

        assert response.status_code in [401, 403]

    def test_expired_token_rejected(self, client: TestClient):
        """Token expirado debe ser rechazado."""
        # Token JWT malformado o expirado
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxMDAwMDAwMDAwfQ.invalid"

        response = client.get(
            "/api/v1/kobetsu",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code in [401, 403]

    def test_malformed_auth_header_rejected(self, client: TestClient):
        """Header de auth malformado debe ser rechazado."""
        # Sin "Bearer"
        response = client.get(
            "/api/v1/kobetsu",
            headers={"Authorization": "some-token"}
        )

        assert response.status_code in [401, 403]

    def test_valid_token_accepted(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Token válido debe ser aceptado."""
        response = client.get("/api/v1/kobetsu", headers=auth_headers)

        assert response.status_code == 200


class TestAccessControl:
    """Tests para control de acceso basado en roles."""

    def test_admin_can_access_all(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Usuario admin debe poder acceder a todos los recursos."""
        endpoints = [
            "/api/v1/kobetsu",
            "/api/v1/kobetsu/stats",
            "/api/v1/factories",
            "/api/v1/employees",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200, f"Admin debería acceder a {endpoint}"

    def test_health_endpoints_public(self, client: TestClient):
        """Endpoints de health deben ser públicos."""
        public_endpoints = [
            "/health",
            "/ready",
        ]

        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"{endpoint} debería ser público"


class TestInputValidation:
    """Tests para validación de entrada (prevención de inyección)."""

    def test_sql_injection_in_search(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Búsqueda debe sanitizar entrada contra SQL injection."""
        # Intento de SQL injection
        malicious_search = "'; DROP TABLE kobetsu_keiyakusho; --"

        response = client.get(
            "/api/v1/kobetsu",
            params={"search": malicious_search},
            headers=auth_headers
        )

        # Debe procesar la búsqueda sin error (ORM previene SQL injection)
        assert response.status_code in [200, 422]

    def test_xss_in_input_fields(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Campos de texto deben aceptar pero no ejecutar scripts."""
        # Intento de XSS
        sample_contract_data["work_content"] = "<script>alert('xss')</script>Test content"

        response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )

        # El contenido se guarda como texto, no se ejecuta
        if response.status_code == 201:
            data = response.json()
            # El script debe estar escapado o como texto plano
            assert "alert" not in data.get("work_content", "") or \
                   "<script>" in data.get("work_content", "")
