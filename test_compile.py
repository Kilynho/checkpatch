#!/usr/bin/env python3
"""
Unit tests for compilation module.

These tests verify the compilation functionality without requiring
an actual Linux kernel source tree.
"""

import unittest
import tempfile
import os
from pathlib import Path
import shutil
import json

# Import compilation functions
from compile import (
    CompilationResult,
    summarize_results,
    save_json_report,
    restore_backups
)


class TestCompilationResult(unittest.TestCase):
    """Test CompilationResult class."""
    
    def test_compilation_result_success(self):
        """Test creating a successful compilation result."""
        result = CompilationResult(
            file_path="/path/to/file.c",
            success=True,
            duration=1.5,
            stdout="compilation output",
            stderr=""
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.file_path, "/path/to/file.c")
        self.assertEqual(result.duration, 1.5)
        self.assertEqual(result.stdout, "compilation output")
    
    def test_compilation_result_failure(self):
        """Test creating a failed compilation result."""
        result = CompilationResult(
            file_path="/path/to/file.c",
            success=False,
            duration=2.0,
            error_message="error: undefined reference"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.error_message, "error: undefined reference")
    
    def test_to_dict(self):
        """Test converting result to dictionary."""
        result = CompilationResult(
            file_path="/path/to/file.c",
            success=True,
            duration=1.0
        )
        
        data = result.to_dict()
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data["file"], "/path/to/file.c")
        self.assertTrue(data["success"])
        self.assertEqual(data["duration"], 1.0)


class TestSummarizeResults(unittest.TestCase):
    """Test result summarization."""
    
    def test_summarize_empty_results(self):
        """Test summarizing empty results list."""
        summary = summarize_results([])
        
        self.assertEqual(summary["total"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["success_rate"], 0)
    
    def test_summarize_all_successful(self):
        """Test summarizing all successful results."""
        results = [
            CompilationResult("/file1.c", True, 1.0),
            CompilationResult("/file2.c", True, 2.0),
            CompilationResult("/file3.c", True, 1.5)
        ]
        
        summary = summarize_results(results)
        
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["success_rate"], 100.0)
        self.assertEqual(summary["total_duration"], 4.5)
        self.assertEqual(summary["avg_duration"], 1.5)
    
    def test_summarize_mixed_results(self):
        """Test summarizing mixed success/failure results."""
        results = [
            CompilationResult("/file1.c", True, 1.0),
            CompilationResult("/file2.c", False, 2.0),
            CompilationResult("/file3.c", True, 1.5),
            CompilationResult("/file4.c", False, 0.5)
        ]
        
        summary = summarize_results(results)
        
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["successful"], 2)
        self.assertEqual(summary["failed"], 2)
        self.assertEqual(summary["success_rate"], 50.0)


class TestSaveJsonReport(unittest.TestCase):
    """Test JSON report generation."""
    
    def test_save_json_report(self):
        """Test saving compilation results to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "compile.json"
            
            results = [
                CompilationResult("/file1.c", True, 1.0),
                CompilationResult("/file2.c", False, 2.0, error_message="compilation error")
            ]
            
            save_json_report(results, output_path)
            
            # Verify file was created
            self.assertTrue(output_path.exists())
            
            # Load and verify content
            with open(output_path) as f:
                data = json.load(f)
            
            self.assertIn("summary", data)
            self.assertIn("results", data)
            self.assertEqual(len(data["results"]), 2)
            self.assertEqual(data["summary"]["total"], 2)
            self.assertEqual(data["summary"]["successful"], 1)
            self.assertEqual(data["summary"]["failed"], 1)


class TestRestoreBackups(unittest.TestCase):
    """Test backup restoration functionality."""
    
    def test_restore_existing_backups(self):
        """Test restoring files from backups."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.c"
            test_file.write_text("modified content")
            
            # Create backup
            backup_file = Path(tmpdir) / "test.c.bak"
            backup_file.write_text("original content")
            
            # Restore backup
            restore_backups([test_file])
            
            # Verify restoration
            self.assertEqual(test_file.read_text(), "original content")
    
    def test_restore_nonexistent_backups(self):
        """Test restoring when no backups exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.c"
            test_file.write_text("content")
            
            # Try to restore (should not fail)
            restore_backups([test_file])
            
            # File should remain unchanged
            self.assertEqual(test_file.read_text(), "content")


class TestCompilationIntegration(unittest.TestCase):
    """Integration tests for compilation workflow."""
    
    def test_full_workflow_data_structures(self):
        """Test the data structures used in compilation workflow."""
        # Simulate the workflow data
        results = [
            CompilationResult("/kernel/init/main.c", True, 1.2),
            CompilationResult("/kernel/init/version.c", False, 0.8, 
                            error_message="error: implicit function declaration")
        ]
        
        # Test summary generation
        summary = summarize_results(results)
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["successful"], 1)
        
        # Test JSON export
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "compile.json"
            save_json_report(results, json_path)
            
            with open(json_path) as f:
                data = json.load(f)
            
            self.assertEqual(len(data["results"]), 2)
            self.assertEqual(data["results"][0]["success"], True)
            self.assertEqual(data["results"][1]["success"], False)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
