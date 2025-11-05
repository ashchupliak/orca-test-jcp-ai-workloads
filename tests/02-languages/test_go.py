#!/usr/bin/env python3
"""
Go development environment test.
Validates Go toolchain and real-world HTTP server development workflow.
Creates an HTTP server with tests and validates functionality.
"""

import sys
import subprocess
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from common.test_framework import BaseTest, main_template


class GoTest(BaseTest):
    """Test Go development tools with realistic workflow."""

    def __init__(self):
        super().__init__("go_http_server")
        self.work_dir = Path("/tmp/go_test_app")

    def run(self):
        """Run comprehensive Go development workflow."""
        print("Testing Go development environment with HTTP server...")

        # Phase 1: Check basic tools
        self.check_command_exists("go", "Go")
        success, version = self.check_version("go")
        if success:
            for line in version.split('\n'):
                if 'go version' in line.lower():
                    self.result.set_metadata("go_version", line.strip())
                    break

        # Check GOPATH
        import os
        go_path = os.getenv("GOPATH")
        self.result.add_check(
            name="GOPATH_set",
            passed=go_path is not None,
            output=f"GOPATH={go_path}" if go_path else None,
            error="GOPATH environment variable not set" if not go_path else None
        )

        # Phase 2: Create project and initialize module
        self.create_project()

        # Phase 3: Create HTTP server application
        self.create_http_server()

        # Phase 4: Create test suite
        self.create_test_suite()

        # Phase 5: Download dependencies and run tests
        self.run_tests()

        # Phase 6: Build and test the server
        self.build_and_test_server()

        # Cleanup
        self.cleanup()

        return self.result

    def create_project(self):
        """Create Go project and initialize module."""
        print("Creating Go module...")

        self.work_dir.mkdir(parents=True, exist_ok=True)

        def init_module():
            cmd = f"cd {self.work_dir} && go mod init example.com/testserver"
            success, output, error = self.run_command(cmd, timeout=30)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "go_mod_init_time",
            init_module
        )

        self.result.add_check(
            name="go_mod_init",
            passed=success,
            output=f"Module initialized in {duration:.2f}s",
            error=error if not success else None
        )

        if success:
            go_mod_file = self.work_dir / "go.mod"
            if go_mod_file.exists():
                self.result.add_validation("go_mod_created", True)

    def create_http_server(self):
        """Create a realistic Go HTTP server."""
        print("Creating Go HTTP server...")

        server_code = '''package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"sync"
)

// Book represents a book in our system
type Book struct {
	ID     int    `json:"id"`
	Title  string `json:"title"`
	Author string `json:"author"`
	Year   int    `json:"year"`
}

// BookStore manages our book collection
type BookStore struct {
	mu     sync.RWMutex
	books  map[int]Book
	nextID int
}

// NewBookStore creates a new book store
func NewBookStore() *BookStore {
	store := &BookStore{
		books:  make(map[int]Book),
		nextID: 1,
	}

	// Add some initial books
	store.books[1] = Book{ID: 1, Title: "The Go Programming Language", Author: "Donovan & Kernighan", Year: 2015}
	store.books[2] = Book{ID: 2, Title: "Learning Go", Author: "Jon Bodner", Year: 2021}
	store.nextID = 3

	return store
}

// HealthHandler returns health status
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"service": "book-api",
	})
}

// GetBooksHandler returns all books
func (s *BookStore) GetBooksHandler(w http.ResponseWriter, r *http.Request) {
	s.mu.RLock()
	defer s.mu.RUnlock()

	books := make([]Book, 0, len(s.books))
	for _, book := range s.books {
		books = append(books, book)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"books": books,
		"total": len(books),
	})
}

// GetBookHandler returns a specific book
func (s *BookStore) GetBookHandler(w http.ResponseWriter, r *http.Request) {
	idStr := r.URL.Path[len("/api/books/"):]
	id, err := strconv.Atoi(idStr)
	if err != nil {
		http.Error(w, "Invalid book ID", http.StatusBadRequest)
		return
	}

	s.mu.RLock()
	book, exists := s.books[id]
	s.mu.RUnlock()

	if !exists {
		http.Error(w, "Book not found", http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(book)
}

// CreateBookHandler creates a new book
func (s *BookStore) CreateBookHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var book Book
	if err := json.NewDecoder(r.Body).Decode(&book); err != nil {
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	if book.Title == "" || book.Author == "" {
		http.Error(w, "Title and author are required", http.StatusBadRequest)
		return
	}

	s.mu.Lock()
	book.ID = s.nextID
	s.nextID++
	s.books[book.ID] = book
	s.mu.Unlock()

	w.Header().Set("Content-Type", "application/json")
	w.WriteStatus(http.StatusCreated)
	json.NewEncoder(w).Encode(book)
}

func main() {
	store := NewBookStore()

	http.HandleFunc("/health", HealthHandler)
	http.HandleFunc("/api/books", store.GetBooksHandler)
	http.HandleFunc("/api/books/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			store.GetBookHandler(w, r)
		} else if r.Method == http.MethodPost {
			store.CreateBookHandler(w, r)
		}
	})

	port := ":8080"
	fmt.Printf("Server starting on port %s\\n", port)
	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}
'''

        server_file = self.work_dir / "main.go"
        try:
            server_file.write_text(server_code)
            self.result.add_check(
                name="create_go_server",
                passed=True,
                output=f"Created {server_file}"
            )
            self.result.add_validation("server_file", str(server_file))
        except Exception as e:
            self.result.add_check(
                name="create_go_server",
                passed=False,
                error=str(e)
            )

    def create_test_suite(self):
        """Create Go test suite for the HTTP server."""
        print("Creating Go test suite...")

        test_code = '''package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthHandler(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()

	HealthHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var response map[string]string
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if response["status"] != "healthy" {
		t.Errorf("Expected status healthy, got %s", response["status"])
	}
}

func TestGetBooksHandler(t *testing.T) {
	store := NewBookStore()
	req := httptest.NewRequest("GET", "/api/books", nil)
	w := httptest.NewRecorder()

	store.GetBooksHandler(w, req)

	if w.Code != http.StatusOK {
		t.Errorf("Expected status 200, got %d", w.Code)
	}

	var response map[string]interface{}
	if err := json.NewDecoder(w.Body).Decode(&response); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	books := response["books"].([]interface{})
	if len(books) == 0 {
		t.Error("Expected books to be returned")
	}
}

func TestGetBookHandler(t *testing.T) {
	store := NewBookStore()

	tests := []struct {
		name       string
		id         string
		wantStatus int
	}{
		{"Valid book", "1", http.StatusOK},
		{"Non-existent book", "999", http.StatusNotFound},
		{"Invalid ID", "abc", http.StatusBadRequest},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/api/books/"+tt.id, nil)
			w := httptest.NewRecorder()

			store.GetBookHandler(w, req)

			if w.Code != tt.wantStatus {
				t.Errorf("Expected status %d, got %d", tt.wantStatus, w.Code)
			}
		})
	}
}

func TestCreateBookHandler(t *testing.T) {
	store := NewBookStore()

	book := Book{
		Title:  "Test Book",
		Author: "Test Author",
		Year:   2024,
	}

	body, _ := json.Marshal(book)
	req := httptest.NewRequest("POST", "/api/books", bytes.NewReader(body))
	w := httptest.NewRecorder()

	store.CreateBookHandler(w, req)

	if w.Code != http.StatusCreated {
		t.Errorf("Expected status 201, got %d", w.Code)
	}

	var created Book
	if err := json.NewDecoder(w.Body).Decode(&created); err != nil {
		t.Fatalf("Failed to decode response: %v", err)
	}

	if created.Title != book.Title {
		t.Errorf("Expected title %s, got %s", book.Title, created.Title)
	}

	if created.ID == 0 {
		t.Error("Expected book to have an ID")
	}
}

func TestCreateBookHandlerValidation(t *testing.T) {
	store := NewBookStore()

	invalidBook := Book{Title: "No Author"}
	body, _ := json.Marshal(invalidBook)
	req := httptest.NewRequest("POST", "/api/books", bytes.NewReader(body))
	w := httptest.NewRecorder()

	store.CreateBookHandler(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("Expected status 400, got %d", w.Code)
	}
}
'''

        test_file = self.work_dir / "main_test.go"
        try:
            test_file.write_text(test_code)
            self.result.add_check(
                name="create_test_suite",
                passed=True,
                output=f"Created {test_file} with 5 test functions"
            )
            self.result.add_validation("test_file", str(test_file))
        except Exception as e:
            self.result.add_check(
                name="create_test_suite",
                passed=False,
                error=str(e)
            )

    def run_tests(self):
        """Download dependencies and run Go tests."""
        print("Running Go tests...")

        # First, download dependencies
        def download_deps():
            cmd = f"cd {self.work_dir} && go mod tidy"
            success, output, error = self.run_command(cmd, timeout=60)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "go_mod_tidy_time",
            download_deps
        )

        self.result.add_check(
            name="go_mod_tidy",
            passed=success,
            output=f"Dependencies resolved in {duration:.2f}s",
            error=error if not success else None
        )

        # Run tests
        def run_go_test():
            cmd = f"cd {self.work_dir} && go test -v"
            success, output, error = self.run_command(cmd, timeout=60)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "test_execution_time",
            run_go_test
        )

        # Parse test results
        test_passed = success
        pass_rate = "0/0"

        combined_output = output + error
        if "PASS" in combined_output or "ok" in combined_output:
            test_passed = True
            # Count passed tests
            import re
            matches = re.findall(r'--- PASS: Test\w+', combined_output)
            if matches:
                pass_count = len(matches)
                pass_rate = f"{pass_count}/5"

        self.result.add_check(
            name="go_tests",
            passed=test_passed,
            output=f"Tests: {pass_rate}, Duration: {duration:.2f}s",
            error=error if not test_passed else None
        )

        self.result.add_validation("test_pass_rate", pass_rate)

        # Validate output contains expected patterns
        if combined_output:
            patterns = [
                r'TestHealthHandler',
                r'TestGetBooksHandler',
                r'(PASS|ok)',
            ]
            self.validate_output(combined_output, patterns, "go_test_output_validation")

    def build_and_test_server(self):
        """Build Go binary and test HTTP endpoints."""
        print("Building and testing server...")

        # Build the server
        def build_server():
            cmd = f"cd {self.work_dir} && go build -o server main.go"
            success, output, error = self.run_command(cmd, timeout=60)
            return success, output, error

        (success, output, error), duration = self.measure_time(
            "go_build_time",
            build_server
        )

        self.result.add_check(
            name="go_build",
            passed=success,
            output=f"Built in {duration:.2f}s",
            error=error if not success else None
        )

        if not success:
            return

        # Verify binary exists
        binary_path = self.work_dir / "server"
        if not binary_path.exists():
            self.result.add_check(
                name="binary_exists",
                passed=False,
                error="Binary not found after build"
            )
            return

        self.result.add_validation("binary_created", str(binary_path))

        # Start server and test endpoints
        server_process = None
        try:
            server_process = subprocess.Popen(
                [str(binary_path)],
                cwd=self.work_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Wait for server to start
            if self.wait_for_service("127.0.0.1", 8080, timeout=15, service_name="go_http_server"):

                # Small delay to ensure server is ready
                time.sleep(0.5)

                # Test health endpoint
                success, status = self.check_http_endpoint(
                    "http://127.0.0.1:8080/health",
                    expected_status=200,
                    name="health_endpoint"
                )

                # Test books endpoint
                success, status = self.check_http_endpoint(
                    "http://127.0.0.1:8080/api/books",
                    expected_status=200,
                    name="books_endpoint"
                )

                self.result.add_validation("api_endpoints_tested", 2)
            else:
                self.result.add_check(
                    name="go_server_start",
                    passed=False,
                    error="Server failed to start in time"
                )

        except Exception as e:
            self.result.add_check(
                name="server_test",
                passed=False,
                error=f"Error testing server: {str(e)}"
            )
        finally:
            # Stop server
            if server_process:
                server_process.terminate()
                try:
                    server_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server_process.kill()

    def cleanup(self):
        """Clean up test files."""
        try:
            if self.work_dir.exists():
                import shutil
                shutil.rmtree(self.work_dir)
        except Exception:
            pass  # Best effort cleanup


if __name__ == "__main__":
    main_template(GoTest)
