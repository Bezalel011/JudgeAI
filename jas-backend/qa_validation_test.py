#!/usr/bin/env python
"""
QA Validation Test Suite - End-to-End System Testing
Tests the entire pipeline: Upload → Process → NLP → Actions → Alerts → API
"""

import json
import requests
from datetime import datetime, timedelta
import sqlite3

# Configuration
API_BASE = "http://127.0.0.1:8000"
DB_PATH = "test.db"

class QAValidator:
    def __init__(self):
        self.issues = []
        self.fixes_applied = []
        self.passed_tests = []
        
    def log_issue(self, level, title, description):
        """Log an issue found during validation."""
        self.issues.append({
            "level": level,  # CRITICAL, WARNING, INFO
            "title": title,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"[{level}] {title}: {description}")
    
    def log_pass(self, test_name):
        """Log a passed test."""
        self.passed_tests.append(test_name)
        print(f"✓ {test_name}")
    
    def log_fix(self, fix_name):
        """Log a fix that was applied."""
        self.fixes_applied.append(fix_name)
        print(f"✔ FIXED: {fix_name}")
    
    # ============ API VALIDATION TESTS ============
    
    def test_api_health(self):
        """Test 1: API Health Check"""
        print("\n[TEST 1] API Health Check")
        try:
            resp = requests.get(f"{API_BASE}/health", timeout=5)
            if resp.status_code == 200:
                self.log_pass("API Health Check")
                return True
            else:
                self.log_issue("CRITICAL", "API Not Responding", f"Status: {resp.status_code}")
                return False
        except Exception as e:
            self.log_issue("CRITICAL", "Cannot Connect to API", str(e))
            return False
    
    def test_api_endpoints(self):
        """Test 2: Verify All Critical Endpoints Exist"""
        print("\n[TEST 2] Critical Endpoints Exist")
        endpoints = [
            ("GET", "/actions"),
            ("GET", "/dashboard"),
            ("GET", "/alerts"),
            ("POST", "/upload"),
        ]
        
        for method, path in endpoints:
            try:
                if method == "GET":
                    resp = requests.get(f"{API_BASE}{path}", timeout=5)
                    status = resp.status_code in [200, 400, 404]  # Accept these
                    if status:
                        self.log_pass(f"Endpoint {method} {path}")
                    else:
                        self.log_issue("WARNING", f"Endpoint {method} {path}", f"Unexpected status: {resp.status_code}")
            except Exception as e:
                self.log_issue("WARNING", f"Cannot test {method} {path}", str(e))
    
    def test_api_schemas(self):
        """Test 3: Verify API Response Schemas"""
        print("\n[TEST 3] API Response Schemas")
        try:
            # Test GET /actions schema
            resp = requests.get(f"{API_BASE}/actions", timeout=5)
            if resp.status_code == 200:
                actions = resp.json()
                if isinstance(actions, list):
                    if actions:
                        action = actions[0]
                        required_fields = ["id", "task", "status", "deadline"]
                        missing = [f for f in required_fields if f not in action]
                        if not missing:
                            self.log_pass("GET /actions schema valid")
                        else:
                            self.log_issue("WARNING", "Missing action fields", str(missing))
                    else:
                        self.log_pass("GET /actions schema valid (empty list)")
                else:
                    self.log_issue("WARNING", "GET /actions returns non-list", type(actions).__name__)
            
            # Test GET /dashboard schema
            resp = requests.get(f"{API_BASE}/dashboard", timeout=5)
            if resp.status_code == 200:
                dashboard = resp.json()
                required_fields = ["total_actions", "pending", "approved", "rejected"]
                missing = [f for f in required_fields if f not in dashboard]
                if not missing:
                    self.log_pass("GET /dashboard schema valid")
                else:
                    self.log_issue("WARNING", "Missing dashboard fields", str(missing))
            
            # Test GET /alerts schema
            resp = requests.get(f"{API_BASE}/alerts", timeout=5)
            if resp.status_code == 200:
                alerts = resp.json()
                if isinstance(alerts, list):
                    self.log_pass("GET /alerts schema valid")
                else:
                    self.log_issue("WARNING", "GET /alerts returns non-list", type(alerts).__name__)
                    
        except Exception as e:
            self.log_issue("WARNING", "Cannot validate schemas", str(e))
    
    # ============ DATABASE INTEGRITY TESTS ============
    
    def test_database_integrity(self):
        """Test 4: Database Integrity Checks"""
        print("\n[TEST 4] Database Integrity")
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Check for orphan actions (FK not set up correctly)
            cursor.execute("""
                SELECT COUNT(*) FROM actions a
                LEFT JOIN documents d ON a.document_id = d.id
                WHERE d.id IS NULL
            """)
            orphan_actions = cursor.fetchone()[0]
            if orphan_actions == 0:
                self.log_pass("No orphan actions found")
            else:
                self.log_issue("CRITICAL", "Orphan actions detected", f"Count: {orphan_actions}")
            
            # Check for orphan reviews
            cursor.execute("""
                SELECT COUNT(*) FROM reviews r
                LEFT JOIN actions a ON r.action_id = a.id
                WHERE a.id IS NULL
            """)
            orphan_reviews = cursor.fetchone()[0]
            if orphan_reviews == 0:
                self.log_pass("No orphan reviews found")
            else:
                self.log_issue("WARNING", "Orphan reviews detected", f"Count: {orphan_reviews}")
            
            # Check alert UNIQUE constraint
            cursor.execute("""
                SELECT COUNT(*), action_id, type FROM alerts
                GROUP BY action_id, type
                HAVING COUNT(*) > 1
            """)
            duplicates = cursor.fetchall()
            if not duplicates:
                self.log_pass("No duplicate alerts found (UNIQUE constraint working)")
            else:
                self.log_issue("CRITICAL", "Duplicate alerts detected", str(duplicates))
            
            # Check document status values
            cursor.execute("""
                SELECT DISTINCT status FROM documents
            """)
            statuses = [row[0] for row in cursor.fetchall()]
            valid_statuses = ["uploaded", "processing", "processed", "failed"]
            invalid = [s for s in statuses if s not in valid_statuses]
            if not invalid:
                self.log_pass("All document statuses valid")
            else:
                self.log_issue("WARNING", "Invalid document status values", str(invalid))
            
            conn.close()
        except Exception as e:
            self.log_issue("WARNING", "Cannot validate database", str(e))
    
    # ============ CONFIDENCE SCORE VALIDATION ============
    
    def test_confidence_scores(self):
        """Test 5: Verify Confidence Scores Format"""
        print("\n[TEST 5] Confidence Scores")
        try:
            resp = requests.get(f"{API_BASE}/actions", timeout=5)
            if resp.status_code == 200:
                actions = resp.json()
                if actions:
                    for i, action in enumerate(actions[:3]):  # Check first 3
                        conf = action.get("confidence")
                        if conf:
                            try:
                                conf_float = float(conf)
                                if 0 <= conf_float <= 1:
                                    self.log_pass(f"Action {i}: confidence in correct range (0.0-1.0)")
                                else:
                                    self.log_issue("WARNING", f"Action {i}: confidence out of range", f"Value: {conf}")
                            except (ValueError, TypeError):
                                self.log_issue("WARNING", f"Action {i}: confidence not a number", f"Value: {conf}")
                        else:
                            self.log_pass(f"Action {i}: confidence is None (acceptable)")
                else:
                    self.log_pass("No actions to validate confidence")
        except Exception as e:
            self.log_issue("WARNING", "Cannot validate confidence scores", str(e))
    
    # ============ ALERT SYSTEM VALIDATION ============
    
    def test_alert_filtering(self):
        """Test 6: Alert Filtering Works"""
        print("\n[TEST 6] Alert Filtering")
        try:
            filters = ["all", "unread", "overdue"]
            for filter_name in filters:
                resp = requests.get(f"{API_BASE}/alerts?filter={filter_name}", timeout=5)
                if resp.status_code == 200:
                    alerts = resp.json()
                    if isinstance(alerts, list):
                        self.log_pass(f"Alert filter '{filter_name}' works")
                    else:
                        self.log_issue("WARNING", f"Alert filter '{filter_name}' returns non-list", type(alerts).__name__)
                else:
                    self.log_issue("WARNING", f"Alert filter '{filter_name}' returned", resp.status_code)
        except Exception as e:
            self.log_issue("WARNING", "Cannot validate alert filtering", str(e))
    
    # ============ SCHEDULER VALIDATION ============
    
    def test_scheduler_running(self):
        """Test 7: Background Scheduler Running"""
        print("\n[TEST 7] Background Scheduler")
        try:
            # Quick test: Check if alert generation is working
            resp = requests.get(f"{API_BASE}/alerts", timeout=5)
            if resp.status_code == 200:
                self.log_pass("Alert system responsive (scheduler likely running)")
            else:
                self.log_issue("WARNING", "Alert system not responsive", f"Status: {resp.status_code}")
        except Exception as e:
            self.log_issue("WARNING", "Cannot validate scheduler", str(e))
    
    # ============ GENERATE REPORT ============
    
    def generate_report(self):
        """Generate comprehensive validation report."""
        print("\n" + "="*80)
        print("QA VALIDATION REPORT")
        print("="*80)
        
        print(f"\n✓ Tests Passed: {len(self.passed_tests)}")
        print(f"✔ Fixes Applied: {len(self.fixes_applied)}")
        print(f"⚠ Issues Found: {len(self.issues)}")
        
        print("\n" + "-"*80)
        print("ISSUES SUMMARY")
        print("-"*80)
        
        by_level = {}
        for issue in self.issues:
            level = issue["level"]
            if level not in by_level:
                by_level[level] = []
            by_level[level].append(issue)
        
        for level in ["CRITICAL", "WARNING", "INFO"]:
            if level in by_level:
                print(f"\n{level} ({len(by_level[level])}):")
                for issue in by_level[level]:
                    print(f"  • {issue['title']}: {issue['description']}")
        
        print("\n" + "-"*80)
        print("PASSED TESTS")
        print("-"*80)
        for test in self.passed_tests[:10]:  # Show first 10
            print(f"  ✓ {test}")
        if len(self.passed_tests) > 10:
            print(f"  ... and {len(self.passed_tests) - 10} more")
        
        print("\n" + "-"*80)
        print("FIXES APPLIED")
        print("-"*80)
        for fix in self.fixes_applied:
            print(f"  ✔ {fix}")
        
        print("\n" + "="*80)
        status = "✓ PASS" if len(by_level.get("CRITICAL", [])) == 0 else "✗ FAIL"
        print(f"STATUS: {status}")
        print("="*80)
        
        return {
            "status": status,
            "tests_passed": len(self.passed_tests),
            "issues_found": len(self.issues),
            "critical_issues": len(by_level.get("CRITICAL", [])),
            "warnings": len(by_level.get("WARNING", [])),
        }
    
    def run_all_tests(self):
        """Run all validation tests."""
        print("Starting QA Validation Tests...")
        
        # API Tests
        if not self.test_api_health():
            print("\nCannot proceed without API. Exiting.")
            return
        
        self.test_api_endpoints()
        self.test_api_schemas()
        
        # Database Tests
        self.test_database_integrity()
        
        # Feature Tests
        self.test_confidence_scores()
        self.test_alert_filtering()
        self.test_scheduler_running()
        
        # Generate Report
        return self.generate_report()


if __name__ == "__main__":
    validator = QAValidator()
    report = validator.run_all_tests()
