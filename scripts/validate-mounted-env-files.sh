#!/bin/bash
# Validate Mounted Environment Files Script
# Ensures proper LF line endings and validates environment setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if file has LF line endings
check_lf_endings() {
    local file="$1"
    if file "$file" | grep -q "CRLF"; then
        return 1
    else
        return 0
    fi
}

# Convert CRLF to LF
convert_to_lf() {
    local file="$1"
    log_info "Converting $file to LF line endings..."
    if command -v dos2unix >/dev/null 2>&1; then
        dos2unix "$file"
    else
        # Fallback method using sed
        sed -i 's/\r$//' "$file"
    fi
}

# Validate required files
validate_files() {
    log_info "Validating environment files..."
    
    local errors=0
    local files_to_check=(
        "requirements.txt"
        ".gitignore"
        "README.md"
        "app/main.py"
        "scripts/go_live_validation.py"
        "scripts/validate-mounted-env-files.sh"
    )
    
    for file in "${files_to_check[@]}"; do
        if [[ -f "$file" ]]; then
            if check_lf_endings "$file"; then
                log_success "$file: LF line endings ✓"
            else
                log_warning "$file: CRLF line endings detected"
                convert_to_lf "$file"
                if check_lf_endings "$file"; then
                    log_success "$file: Converted to LF ✓"
                else
                    log_error "$file: Failed to convert to LF ✗"
                    ((errors++))
                fi
            fi
        else
            log_warning "$file: Not found"
        fi
    done
    
    return $errors
}

# Validate Python environment
validate_python_env() {
    log_info "Validating Python environment..."
    
    # Check Python version
    if command -v python3 >/dev/null 2>&1; then
        local python_version=$(python3 --version | cut -d' ' -f2)
        log_success "Python: $python_version ✓"
    else
        log_error "Python3 not found ✗"
        return 1
    fi
    
    # Check pip
    if command -v pip3 >/dev/null 2>&1; then
        log_success "pip3: Available ✓"
    else
        log_error "pip3 not found ✗"
        return 1
    fi
    
    # Check virtual environment
    if [[ -d ".venv" ]] || [[ -d "venv" ]]; then
        log_success "Virtual environment: Found ✓"
    else
        log_warning "Virtual environment: Not found"
    fi
    
    return 0
}

# Validate application structure
validate_app_structure() {
    log_info "Validating application structure..."
    
    local required_dirs=(
        "app"
        "scripts"
        "tests"
    )
    
    local required_files=(
        "app/main.py"
        "requirements.txt"
        "run.ps1"
    )
    
    local errors=0
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            log_success "Directory: $dir ✓"
        else
            log_error "Directory: $dir not found ✗"
            ((errors++))
        fi
    done
    
    for file in "${required_files[@]}"; do
        if [[ -f "$file" ]]; then
            log_success "File: $file ✓"
        else
            log_error "File: $file not found ✗"
            ((errors++))
        fi
    done
    
    return $errors
}

# Validate Docker configuration
validate_docker_config() {
    log_info "Validating Docker configuration..."
    
    if [[ -f "scripts/openhands_docker_compose.yml" ]]; then
        log_success "Docker Compose file: Found ✓"
        
        # Check if docker is available
        if command -v docker >/dev/null 2>&1; then
            log_success "Docker: Available ✓"
        else
            log_warning "Docker: Not available (optional)"
        fi
        
        # Check if docker-compose is available
        if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
            log_success "Docker Compose: Available ✓"
        else
            log_warning "Docker Compose: Not available (optional)"
        fi
    else
        log_warning "Docker Compose file: Not found"
    fi
    
    return 0
}

# Main validation function
main() {
    log_info "Starting environment validation..."
    echo "========================================"
    
    local total_errors=0
    
    # Run all validations
    validate_files || ((total_errors += $?))
    validate_python_env || ((total_errors += $?))
    validate_app_structure || ((total_errors += $?))
    validate_docker_config || ((total_errors += $?))
    
    echo "========================================"
    
    if [[ $total_errors -eq 0 ]]; then
        log_success "Environment validation completed successfully! ✓"
        log_info "All files have proper LF line endings and structure is valid."
        return 0
    else
        log_error "Environment validation completed with $total_errors errors! ✗"
        return 1
    fi
}

# Run main function
main "$@"
