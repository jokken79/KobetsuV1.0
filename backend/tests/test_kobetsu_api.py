"""
Tests for Kobetsu Keiyakusho API endpoints.
"""
import pytest
from fastapi.testclient import TestClient


class TestKobetsuAPI:
    """Test cases for Kobetsu API endpoints."""

    def test_list_contracts_empty(self, client: TestClient, auth_headers: dict):
        """Test listing contracts when database is empty."""
        response = client.get("/api/v1/kobetsu", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_create_contract(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test creating a new contract."""
        response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["contract_number"].startswith("KOB-")
        assert data["status"] == "draft"
        assert data["worksite_name"] == sample_contract_data["worksite_name"]
        assert data["number_of_workers"] == len(sample_contract_data["employee_ids"])

    def test_create_contract_validation_error(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Test contract creation with invalid data."""
        invalid_data = {
            "factory_id": 1,
            "employee_ids": [],  # Empty - should fail
            "work_content": "短い",  # Too short
        }
        response = client.post(
            "/api/v1/kobetsu",
            json=invalid_data,
            headers=auth_headers
        )
        assert response.status_code == 422  # Validation error

    def test_get_contract_by_id(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test getting a contract by ID."""
        # Create contract first
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]

        # Get contract
        response = client.get(
            f"/api/v1/kobetsu/{contract_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == contract_id

    def test_get_contract_not_found(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent contract."""
        response = client.get("/api/v1/kobetsu/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_update_contract(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict,
        sample_update_data: dict
    ):
        """Test updating a contract."""
        # Create contract first
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]

        # Update contract
        response = client.put(
            f"/api/v1/kobetsu/{contract_id}",
            json=sample_update_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["work_content"] == sample_update_data["work_content"]
        assert float(data["hourly_rate"]) == sample_update_data["hourly_rate"]

    def test_activate_contract(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test activating a draft contract."""
        # Create contract
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]

        # Activate
        response = client.post(
            f"/api/v1/kobetsu/{contract_id}/activate",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"

    def test_delete_draft_contract(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test deleting a draft contract."""
        # Create contract
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]

        # Delete (soft)
        response = client.delete(
            f"/api/v1/kobetsu/{contract_id}",
            headers=auth_headers
        )
        assert response.status_code == 204

    def test_get_stats(self, client: TestClient, auth_headers: dict):
        """Test getting contract statistics."""
        response = client.get("/api/v1/kobetsu/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_contracts" in data
        assert "active_contracts" in data
        assert "expiring_soon" in data

    def test_duplicate_contract(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test duplicating a contract."""
        # Create contract
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]
        original_number = create_response.json()["contract_number"]

        # Duplicate
        response = client.post(
            f"/api/v1/kobetsu/{contract_id}/duplicate",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["contract_number"] != original_number
        assert data["status"] == "draft"

    def test_list_contracts_with_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test listing contracts with filters."""
        # Create contract
        client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )

        # List with status filter
        response = client.get(
            "/api/v1/kobetsu",
            params={"status": "draft"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == "draft"

    def test_unauthorized_access(self, client: TestClient):
        """Test that unauthorized requests are rejected."""
        response = client.get("/api/v1/kobetsu")
        assert response.status_code == 403  # No auth header


class TestKobetsuEmployees:
    """Test cases for employee management within contracts."""

    def test_get_employees(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test getting employees for a contract."""
        # Create contract
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]

        # Get employees
        response = client.get(
            f"/api/v1/kobetsu/{contract_id}/employees",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_add_employee(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test adding an employee to a contract."""
        # Create contract
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]

        # Add employee
        response = client.post(
            f"/api/v1/kobetsu/{contract_id}/employees/99",
            headers=auth_headers
        )
        assert response.status_code == 201

    def test_remove_employee(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_contract_data: dict
    ):
        """Test removing an employee from a contract."""
        # Create contract with employees
        create_response = client.post(
            "/api/v1/kobetsu",
            json=sample_contract_data,
            headers=auth_headers
        )
        contract_id = create_response.json()["id"]
        employee_id = sample_contract_data["employee_ids"][0]

        # Remove employee
        response = client.delete(
            f"/api/v1/kobetsu/{contract_id}/employees/{employee_id}",
            headers=auth_headers
        )
        assert response.status_code == 204
