#!/usr/bin/env python3
import requests
import json
import time
import os
import sys
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = None
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                BACKEND_URL = line.strip().split('=')[1].strip('"\'')
                break
except Exception as e:
    print(f"Error reading frontend/.env: {e}")
    sys.exit(1)

if not BACKEND_URL:
    print("Error: Could not find REACT_APP_BACKEND_URL in frontend/.env")
    sys.exit(1)

API_URL = f"{BACKEND_URL}/api"
print(f"Using API URL: {API_URL}")

# Test credentials
USERNAME = "admin"
PASSWORD = "admin123"

# Store auth token
auth_token = None

# Helper functions
def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_result(endpoint, status, message=""):
    status_str = "✅ PASS" if status else "❌ FAIL"
    print(f"{status_str} - {endpoint} {message}")
    return status

def make_request(method, endpoint, data=None, headers=None, files=None, expected_status=200):
    url = f"{API_URL}{endpoint}"
    
    if not headers and auth_token:
        headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        if method.lower() == "get":
            response = requests.get(url, headers=headers)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers, files=files)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers)
        elif method.lower() == "delete":
            response = requests.delete(url, json=data, headers=headers)
        else:
            print(f"Unsupported method: {method}")
            return False, None
        
        if response.status_code == expected_status:
            try:
                return True, response.json()
            except:
                return True, response.text
        else:
            print(f"  Expected status {expected_status}, got {response.status_code}")
            print(f"  Response: {response.text}")
            return False, None
    except Exception as e:
        print(f"  Request error: {e}")
        return False, None

# Test functions
def test_health_check():
    print_header("Testing Health Check Endpoints")
    
    # Test root health check
    success, data = make_request("get", "/")
    status1 = print_result("/", success, "- Root health check")
    
    # Test detailed health check
    success, data = make_request("get", "/health")
    status2 = print_result("/health", success, "- Detailed health check")
    
    return status1 and status2

def test_authentication():
    print_header("Testing Authentication Endpoints")
    global auth_token
    
    # Test login
    success, data = make_request("post", "/auth/login", {
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if success and "access_token" in data:
        auth_token = data["access_token"]
        print(f"  Got auth token: {auth_token[:10]}...")
    
    status1 = print_result("/auth/login", success, "- Login")
    
    # Test get current user
    success, data = make_request("get", "/auth/me")
    status2 = print_result("/auth/me", success, "- Get current user")
    
    if success:
        print(f"  Logged in as: {data.get('username')} (role: {data.get('role')})")
    
    # Test 2FA setup (we won't enable it)
    success, data = make_request("post", "/auth/setup-2fa")
    status3 = print_result("/auth/setup-2fa", success, "- Setup 2FA")
    
    return status1 and status2 and status3

def test_dashboard():
    print_header("Testing Dashboard Endpoints")
    
    # Test dashboard stats
    success, data = make_request("get", "/dashboard/stats")
    status1 = print_result("/dashboard/stats", success, "- Get dashboard statistics")
    
    if success:
        print(f"  Active sessions: {data.get('active_sessions')}")
        print(f"  CPU usage: {data.get('cpu_usage_percent')}%")
        print(f"  Memory usage: {data.get('memory_usage_percent')}%")
    
    # Test current metrics
    success, data = make_request("get", "/dashboard/metrics/current")
    status2 = print_result("/dashboard/metrics/current", success, "- Get current metrics")
    
    # Test metrics history
    success, data = make_request("get", "/dashboard/metrics/history")
    status3 = print_result("/dashboard/metrics/history", success, "- Get metrics history")
    
    # Test system health
    success, data = make_request("get", "/dashboard/health")
    status4 = print_result("/dashboard/health", success, "- Get system health")
    
    return status1 and status2 and status3 and status4

def test_file_management():
    print_header("Testing File Management Endpoints")
    
    # Test list files
    success, data = make_request("get", "/files/list")
    status1 = print_result("/files/list", success, "- List files")
    
    # Test create directory
    dir_name = f"test_dir_{int(time.time())}"
    success, data = make_request("post", "/files/create-directory", {"path": dir_name})
    status2 = print_result("/files/create-directory", success, f"- Create directory '{dir_name}'")
    
    # Test upload file (create a temporary file)
    temp_file_path = "/tmp/test_upload.txt"
    with open(temp_file_path, "w") as f:
        f.write("This is a test file for RDP Stealth API testing.")
    
    files = {
        'file': ('test_upload.txt', open(temp_file_path, 'rb'), 'text/plain')
    }
    
    form_data = {
        'path': dir_name,
        'encrypt': 'true'
    }
    
    # We need to make a direct request for file upload
    url = f"{API_URL}/files/upload"
    headers = {"Authorization": f"Bearer {auth_token}"}
    
    try:
        response = requests.post(
            url, 
            files=files,
            data=form_data,
            headers=headers
        )
        success = response.status_code == 200
        if success:
            upload_data = response.json()
        else:
            upload_data = None
    except Exception as e:
        print(f"  Upload error: {e}")
        success = False
        upload_data = None
    
    status3 = print_result("/files/upload", success, "- Upload file")
    
    # Clean up the temporary file
    os.remove(temp_file_path)
    
    # Test file operations
    if success and upload_data:
        file_path = upload_data.get('path')
        
        # Test get file info
        success, data = make_request("get", f"/files/info/{file_path}")
        status4 = print_result("/files/info", success, "- Get file info")
        
        # Test storage stats
        success, data = make_request("get", "/files/storage-stats")
        status5 = print_result("/files/storage-stats", success, "- Get storage stats")
        
        # Test file operations history
        success, data = make_request("get", "/files/operations")
        status6 = print_result("/files/operations", success, "- Get file operations history")
        
        # Test delete file
        success, data = make_request("delete", "/files/delete", {"file_path": file_path})
        status7 = print_result("/files/delete", success, "- Delete file")
        
        # Test delete directory
        success, data = make_request("delete", "/files/delete", {"file_path": dir_name})
        status8 = print_result("/files/delete", success, "- Delete directory")
        
        return status1 and status2 and status3 and status4 and status5 and status6 and status7 and status8
    else:
        return status1 and status2 and status3

def test_rdp_management():
    print_header("Testing RDP Management Endpoints")
    
    # Test create RDP connection
    connection_data = {
        "host": "test-rdp-server.example.com",
        "port": 3389,
        "username": "rdp_user",
        "password": "rdp_password",
        "quality": "high"
    }
    
    success, data = make_request("post", "/rdp/connections", connection_data)
    status1 = print_result("/rdp/connections (POST)", success, "- Create RDP connection")
    
    connection_id = None
    if success and data:
        connection_id = data.get('id')
        print(f"  Created connection ID: {connection_id}")
    
    # Test list RDP connections
    success, data = make_request("get", "/rdp/connections")
    status2 = print_result("/rdp/connections (GET)", success, "- List RDP connections")
    
    if success and data:
        print(f"  Found {len(data)} RDP connections")
    
    # Test RDP statistics
    success, data = make_request("get", "/rdp/statistics")
    status3 = print_result("/rdp/statistics", success, "- Get RDP statistics")
    
    # Test connection status and termination if we have a connection ID
    if connection_id:
        # Test get connection status
        success, data = make_request("get", f"/rdp/connections/{connection_id}/status")
        status4 = print_result(f"/rdp/connections/{connection_id}/status", success, "- Get connection status")
        
        # Test terminate connection
        success, data = make_request("delete", f"/rdp/connections/{connection_id}")
        status5 = print_result(f"/rdp/connections/{connection_id} (DELETE)", success, "- Terminate connection")
        
        return status1 and status2 and status3 and status4 and status5
    else:
        return status1 and status2 and status3

def test_session_management():
    print_header("Testing Session Management Endpoints")
    
    # Test get active sessions
    success, data = make_request("get", "/sessions/active")
    status1 = print_result("/sessions/active", success, "- Get active sessions")
    
    if success and data:
        sessions = data.get('sessions', [])
        print(f"  Found {len(sessions)} active sessions")
    
    # Test get session history
    success, data = make_request("get", "/sessions/history")
    status2 = print_result("/sessions/history", success, "- Get session history")
    
    # Test session statistics
    success, data = make_request("get", "/sessions/statistics")
    status3 = print_result("/sessions/statistics", success, "- Get session statistics")
    
    return status1 and status2 and status3

def test_logs():
    print_header("Testing Logs Endpoints")
    
    # Test get logs
    success, data = make_request("get", "/logs/")
    status1 = print_result("/logs/", success, "- Get logs")
    
    if success and data:
        print(f"  Found {len(data)} log entries")
    
    # Test log levels
    success, data = make_request("get", "/logs/levels")
    status2 = print_result("/logs/levels", success, "- Get log levels")
    
    # Test log sources
    success, data = make_request("get", "/logs/sources")
    status3 = print_result("/logs/sources", success, "- Get log sources")
    
    # Test log statistics
    success, data = make_request("get", "/logs/statistics")
    status4 = print_result("/logs/statistics", success, "- Get log statistics")
    
    # Test add log entry
    log_data = {
        "level": "INFO",
        "source": "SYSTEM",
        "message": "Test log entry from API test script"
    }
    
    success, data = make_request("post", "/logs/add", log_data)
    status5 = print_result("/logs/add", success, "- Add log entry")
    
    # Test realtime logs
    success, data = make_request("get", "/logs/realtime")
    status6 = print_result("/logs/realtime", success, "- Get realtime logs")
    
    return status1 and status2 and status3 and status4 and status5 and status6

def test_settings():
    print_header("Testing Settings Endpoints")
    
    # Test get all settings
    success, data = make_request("get", "/settings/")
    status1 = print_result("/settings/", success, "- Get all settings")
    
    # Test get security settings
    success, data = make_request("get", "/settings/security")
    status2 = print_result("/settings/security", success, "- Get security settings")
    
    # Test get RDP settings
    success, data = make_request("get", "/settings/rdp")
    status3 = print_result("/settings/rdp", success, "- Get RDP settings")
    
    # Test get file settings
    success, data = make_request("get", "/settings/files")
    status4 = print_result("/settings/files", success, "- Get file settings")
    
    # Test get notification settings
    success, data = make_request("get", "/settings/notifications")
    status5 = print_result("/settings/notifications", success, "- Get notification settings")
    
    # Test get system settings
    success, data = make_request("get", "/settings/system")
    status6 = print_result("/settings/system", success, "- Get system settings")
    
    # Test update RDP settings
    if success and data:
        rdp_settings = data
        # Make a small change
        rdp_settings["default_quality"] = "medium" if rdp_settings.get("default_quality") == "high" else "high"
        
        success, update_data = make_request("put", "/settings/rdp", rdp_settings)
        status7 = print_result("/settings/rdp (PUT)", success, "- Update RDP settings")
    else:
        status7 = False
    
    return status1 and status2 and status3 and status4 and status5 and status6 and status7

def run_all_tests():
    print_header("RDP Stealth API Test Suite")
    print(f"Testing API at: {API_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run all tests
    health_status = test_health_check()
    auth_status = test_authentication()
    
    # Only continue if authentication works
    if not auth_status:
        print("\n❌ Authentication failed. Cannot continue with other tests.")
        return False
    
    dashboard_status = test_dashboard()
    file_status = test_file_management()
    rdp_status = test_rdp_management()
    session_status = test_session_management()
    logs_status = test_logs()
    settings_status = test_settings()
    
    # Print summary
    print_header("Test Summary")
    print(f"Health Check:       {'✅ PASS' if health_status else '❌ FAIL'}")
    print(f"Authentication:     {'✅ PASS' if auth_status else '❌ FAIL'}")
    print(f"Dashboard:          {'✅ PASS' if dashboard_status else '❌ FAIL'}")
    print(f"File Management:    {'✅ PASS' if file_status else '❌ FAIL'}")
    print(f"RDP Management:     {'✅ PASS' if rdp_status else '❌ FAIL'}")
    print(f"Session Management: {'✅ PASS' if session_status else '❌ FAIL'}")
    print(f"Logs:               {'✅ PASS' if logs_status else '❌ FAIL'}")
    print(f"Settings:           {'✅ PASS' if settings_status else '❌ FAIL'}")
    
    overall_status = all([
        health_status, auth_status, dashboard_status, file_status,
        rdp_status, session_status, logs_status, settings_status
    ])
    
    print("\nOverall Test Result: " + ("✅ PASS" if overall_status else "❌ FAIL"))
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_status

if __name__ == "__main__":
    run_all_tests()