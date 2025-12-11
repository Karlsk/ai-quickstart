#!/usr/bin/env python
"""
Quick API Test Script

A simple script to quickly test all API endpoints.
Run: python quick_api_test.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.RESET}")


def api_info_test():
    """Test: GET /"""
    print_header("Test 1: Get API Info")
    
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print_success(f"API is running: {data['name']}")
            print_info(f"Version: {data['version']}")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False


def create_workflow() -> str:
    """Test: POST /workflows"""
    print_header("Test 2: Create Workflow")
    
    workflow_id = f"test_workflow_{int(time.time())}"
    
    payload = {
        "workflow_id": workflow_id,
        "entry_point": "planner",
        "state_schema": {
            "input": {
                "type": "str",
                "description": "User input query"
            },
            "planner_result": {
                "type": "dict",
                "description": "Result from planner"
            }
        },
        "nodes": [
            {
                "name": "planner",
                "type": "plan",
                "config": {
                    "graph_db_name": "knowledge_graph",
                    "event_name": "plan_event"
                }
            },
            {
                "name": "executor",
                "type": "worker",
                "config": {
                    "sub_type": "rag",
                    "rag_config": {"model": "gpt-4"}
                }
            }
        ],
        "edges": [
            {"source": "planner", "target": "executor"},
            {"source": "executor", "target": "END"}
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/workflows", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Workflow created: {data['workflow_id']}")
            print_info(f"Nodes: {data['data']['nodes_count']}, Edges: {data['data']['edges_count']}")
            return workflow_id
        else:
            print_error(f"Failed: {response.text}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def list_workflows() -> bool:
    """Test: GET /workflows"""
    print_header("Test 3: List Workflows")
    
    try:
        response = requests.get(f"{BASE_URL}/workflows")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Total workflows: {data['total']}")
            for wf in data['workflows']:
                print_info(f"  - {wf}")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def get_workflow(workflow_id: str) -> bool:
    """Test: GET /workflows/{workflow_id}"""
    print_header(f"Test 4: Get Workflow Details: {workflow_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/workflows/{workflow_id}")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Workflow: {data['workflow_id']}")
            print_info(f"Entry point: {data['entry_point']}")
            print_info(f"Nodes: {len(data['nodes'])}, Edges: {len(data['edges'])}")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def execute_workflow(workflow_id: str) -> bool:
    """Test: POST /workflows/{workflow_id}/execute"""
    print_header(f"Test 5: Execute Workflow: {workflow_id}")
    
    payload = {
        "workflow_id": workflow_id,
        "input_data": {
            "input": "Analyze this specific user behavior data"
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/workflows/{workflow_id}/execute",
            json=payload
        )
        if response.status_code == 200:
            data = response.json()
            print_success("Workflow executed successfully")
            print_info(f"Status: {data['status']}")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def get_operator_logs(workflow_id: str) -> bool:
    """Test: GET /workflows/{workflow_id}/operator-logs"""
    print_header(f"Test 6: Get Operator Logs: {workflow_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/workflows/{workflow_id}/operator-logs")
        if response.status_code == 200:
            data = response.json()
            print_success(f"Operator logs retrieved")
            print_info(f"Total nodes: {data['total_nodes']}")
            for node_name in data['operator_logs'].keys():
                print_info(f"  - {node_name}")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def get_execution_history(workflow_id: str) -> bool:
    """Test: GET /workflows/{workflow_id}/execution-history"""
    print_header(f"Test 7: Get Execution History: {workflow_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/workflows/{workflow_id}/execution-history"
        )
        if response.status_code == 200:
            data = response.json()
            print_success(f"Execution history retrieved")
            print_info(f"Total logs: {data['total_logs']}")
            for idx, log in enumerate(data['logs'], 1):
                print_info(f"  [{idx}] {log['node_name']} ({log['node_type']}) - {log['execution_time_ms']:.2f}ms")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def get_workflow_logs(workflow_id: str) -> bool:
    """Test: GET /workflows/{workflow_id}/logs"""
    print_header(f"Test 8: Get Complete Logs: {workflow_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/workflows/{workflow_id}/logs")
        if response.status_code == 200:
            data = response.json()
            print_success("Complete logs retrieved")
            print_info(f"Operator logs - Total nodes: {len(data['operator_logs'])}")
            print_info(f"Execution history - Total logs: {data['total_executions']}")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def delete_workflow(workflow_id: str) -> bool:
    """Test: DELETE /workflows/{workflow_id}"""
    print_header(f"Test 9: Delete Workflow: {workflow_id}")
    
    try:
        response = requests.delete(f"{BASE_URL}/workflows/{workflow_id}")
        if response.status_code == 200:
            data = response.json()
            print_success("Workflow deleted successfully")
            return True
        else:
            print_error(f"Failed: {response.text}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print_header("🚀 API Quick Test Suite")
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1: API Info
    tests_total += 1
    if api_info_test():
        tests_passed += 1
    
    # Test 2: Create Workflow
    tests_total += 1
    workflow_id = create_workflow()
    if workflow_id:
        tests_passed += 1
    else:
        print_error("Cannot continue without workflow")
        return
    
    # Test 3: List Workflows
    tests_total += 1
    if list_workflows():
        tests_passed += 1
    
    # Test 4: Get Workflow
    tests_total += 1
    if get_workflow(workflow_id):
        tests_passed += 1
    
    # Test 5: Execute Workflow
    tests_total += 1
    if execute_workflow(workflow_id):
        tests_passed += 1
    
    # Test 6: Get Operator Logs
    tests_total += 1
    if get_operator_logs(workflow_id):
        tests_passed += 1
    
    # Test 7: Get Execution History
    tests_total += 1
    if get_execution_history(workflow_id):
        tests_passed += 1
    
    # Test 8: Get Complete Logs
    tests_total += 1
    if get_workflow_logs(workflow_id):
        tests_passed += 1
    
    # Test 9: Delete Workflow
    tests_total += 1
    if delete_workflow(workflow_id):
        tests_passed += 1
    
    # Summary
    print_header("📊 Test Results")
    print_info(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print_success("All tests passed! ✨")
    else:
        print_error(f"Some tests failed: {tests_total - tests_passed} failed")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
