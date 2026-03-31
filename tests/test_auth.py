import pytest
from tests.conftest import requires_iris, IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, USERS


pytestmark = requires_iris


def _connect(username, password):
    import iris

    return iris.connect(IRIS_HOST, IRIS_PORT, IRIS_NAMESPACE, username, password)


def _get_roles(conn):
    import iris

    return iris.createIRIS(conn).classMethodValue("Utils.GetRoles", "GetRoles")


def test_doctor_login_succeeds():
    username, password = USERS["doctor"]
    conn = _connect(username, password)
    assert conn is not None
    conn.close()


def test_nurse_login_succeeds():
    username, password = USERS["nurse"]
    conn = _connect(username, password)
    assert conn is not None
    conn.close()


def test_invalid_credentials_raise():
    username, password = USERS["invalid"]
    with pytest.raises(Exception):
        _connect(username, password)


def test_get_roles_doctor_contains_doctor_role(iris_conn_doctor):
    roles = _get_roles(iris_conn_doctor)
    assert "Doctor" in roles, f"Expected 'Doctor' in roles, got: {roles}"


def test_get_roles_nurse_contains_nurse_role(iris_conn_nurse):
    roles = _get_roles(iris_conn_nurse)
    assert "Nurse" in roles, f"Expected 'Nurse' in roles, got: {roles}"


def test_get_roles_nurse_does_not_contain_doctor(iris_conn_nurse):
    roles = _get_roles(iris_conn_nurse)
    assert "Doctor" not in roles, f"Nurse should not have Doctor role, got: {roles}"


def test_get_roles_doctor_does_not_contain_nurse(iris_conn_doctor):
    roles = _get_roles(iris_conn_doctor)
    assert "Nurse" not in roles, f"Doctor should not have Nurse role, got: {roles}"


def test_login_page_role_routing_doctor():
    username, password = USERS["doctor"]
    conn = _connect(username, password)
    roles = _get_roles(conn)
    conn.close()
    assert "Doctor" in roles
    assert "Nurse" not in roles


def test_login_page_role_routing_nurse():
    username, password = USERS["nurse"]
    conn = _connect(username, password)
    roles = _get_roles(conn)
    conn.close()
    assert "Nurse" in roles
    assert "Doctor" not in roles
