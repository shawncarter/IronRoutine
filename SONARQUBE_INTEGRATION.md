# SonarQube Integration Guide

## Overview

This project uses SonarQube for continuous code quality analysis. Every push to the repository triggers an automated scan that checks for:

- **Code Smells**: Maintainability issues
- **Bugs**: Potential runtime errors
- **Vulnerabilities**: Security issues
- **Security Hotspots**: Security-sensitive code that needs review
- **Code Coverage**: Test coverage metrics
- **Duplications**: Duplicate code blocks
- **Cognitive Complexity**: Code complexity metrics

## Quick Start

### Viewing Analysis Results

1. Visit your SonarQube server: `https://qube.shawncarter.co.uk`
2. Navigate to the **IronRoutine** project
3. View the dashboard for overall metrics
4. Click on **Issues** to see detailed findings

### GitHub Actions Workflow

The project includes an automated workflow (`.github/workflows/sonarqube.yml`) that:

1. Runs on every push to `main` or `develop` branches
2. Runs on every pull request
3. Performs a full SonarQube scan
4. Checks the Quality Gate status
5. Fails the build if Quality Gate fails

### Required Secrets

Add these secrets to your GitHub repository settings:

- `SONAR_TOKEN`: Your SonarQube authentication token
- `SONAR_HOST_URL`: Your SonarQube server URL (e.g., `https://qube.shawncarter.co.uk`)

## Code Quality Standards

### Critical Issues (Must Fix)

- **Cognitive Complexity > 15**: Functions that are too complex
- **Duplicate Strings**: String literals used 3+ times
- **Security Vulnerabilities**: Any security issues

### Major Issues (Should Fix)

- **Accessibility Issues**: Missing ARIA labels, keyboard support
- **Code Smells**: Maintainability issues
- **Unused Variables**: Dead code

### Minor Issues (Nice to Fix)

- **Code Style**: Formatting and convention issues
- **Performance**: Minor optimization opportunities

## Best Practices

### 1. Fix Issues Before Merging

- Review SonarQube findings before creating a PR
- Address all Critical and Major issues
- Document any intentional exceptions

### 2. Use Constants for Repeated Strings

```python
# ❌ Bad
return redirect('routines:routine_list')
return redirect('routines:routine_list')

# ✅ Good
ROUTINE_LIST_URL = 'routines:routine_list'
return redirect(ROUTINE_LIST_URL)
```

### 3. Reduce Cognitive Complexity

```python
# ❌ Bad - Complexity 23
def complex_function(request):
    if condition1:
        if condition2:
            if condition3:
                # deeply nested logic
                pass

# ✅ Good - Extract helper functions
def _validate_input(data):
    """Validate input data"""
    pass

def _process_data(data):
    """Process validated data"""
    pass

def simple_function(request):
    if not _validate_input(request.POST):
        return error_response()
    return _process_data(request.POST)
```

### 4. Fix Accessibility Issues

```html
<!-- ❌ Bad -->
<span role="button" onclick="doSomething()">Click me</span>

<!-- ✅ Good -->
<button type="button" onclick="doSomething()">Click me</button>
```

## Exclusions

The following files/directories are excluded from analysis:

- `**/migrations/**` - Django migrations
- `**/static/**` - Static assets
- `**/templates/**` - HTML templates (analyzed separately)
- `**/venv/**` - Virtual environment
- `**/node_modules/**` - Node modules
- `**/__pycache__/**` - Python cache
- Utility scripts: `build_exercise_db.py`, `scraper.py`, `retry_failures.py`, etc.

## Local Analysis

To run SonarQube analysis locally:

```bash
# Install SonarScanner
# macOS
brew install sonar-scanner

# Linux
# Download from https://docs.sonarqube.org/latest/analysis/scan/sonarscanner/

# Run analysis
sonar-scanner \
  -Dsonar.projectKey=IronRoutine \
  -Dsonar.sources=. \
  -Dsonar.host.url=https://qube.shawncarter.co.uk \
  -Dsonar.login=YOUR_TOKEN
```

## Metrics Explained

### Reliability Rating

- **A**: 0 bugs
- **B**: At least 1 minor bug
- **C**: At least 1 major bug
- **D**: At least 1 critical bug
- **E**: At least 1 blocker bug

### Security Rating

- **A**: 0 vulnerabilities
- **B**: At least 1 minor vulnerability
- **C**: At least 1 major vulnerability
- **D**: At least 1 critical vulnerability
- **E**: At least 1 blocker vulnerability

### Maintainability Rating

Based on technical debt ratio:

- **A**: ≤ 5% technical debt
- **B**: 6-10% technical debt
- **C**: 11-20% technical debt
- **D**: 21-50% technical debt
- **E**: > 50% technical debt

### Coverage

- **Target**: ≥ 80% code coverage
- **Minimum**: ≥ 60% code coverage

## Troubleshooting

### Quality Gate Failing

1. Check the SonarQube dashboard for specific issues
2. Review the **Issues** tab for detailed findings
3. Fix Critical and Major issues first
4. Re-run the analysis

### Analysis Not Running

1. Check GitHub Actions logs
2. Verify `SONAR_TOKEN` and `SONAR_HOST_URL` secrets are set
3. Ensure SonarQube server is accessible
4. Check network connectivity

### False Positives

If an issue is a false positive:

1. Add a comment explaining why
2. Mark as "Won't Fix" or "False Positive" in SonarQube
3. Document in code comments

## Resources

- [SonarQube Documentation](https://docs.sonarqube.org/)
- [SonarQube Python Rules](https://rules.sonarsource.com/python/)
- [SonarQube JavaScript Rules](https://rules.sonarsource.com/javascript/)
- [SonarQube HTML Rules](https://rules.sonarsource.com/html/)

## Recent Improvements

### Fixed Issues (Latest Scan)

✅ **14 Critical/Major Issues Fixed**:
- Refactored high cognitive complexity functions (25 → 15, 16 → 15)
- Eliminated duplicate string literals (13 occurrences)
- Fixed accessibility issues (6 instances)
- Removed unused variables (2 instances)
- Fixed unnecessary f-strings

**Technical Debt Eliminated**: ~53 minutes

### Current Status

- **Total Issues**: 147 (down from 161)
- **Critical Issues**: 19 (mostly in utility scripts)
- **Major Issues**: 28
- **Minor Issues**: 100

## Contributing

When contributing to this project:

1. Run local SonarQube analysis before committing
2. Fix all new Critical and Major issues
3. Aim for zero new issues in your PR
4. Document any intentional exceptions
5. Keep cognitive complexity ≤ 15
6. Use constants for repeated strings (3+ occurrences)

