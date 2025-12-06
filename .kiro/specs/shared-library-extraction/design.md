# Design Document

## Overview

This document outlines the design for extracting the shared module from the mojo-py monorepo into a standalone mojo-shared repository. The shared module contains common utilities, models, and services that are currently used across the API, Chronos, and other components of the mojo system.

The extraction will involve creating a new Python package that can be installed as a dependency, updating import statements in the source repository, and ensuring all functionality remains intact.

## Architecture

### Current State
- **Monorepo Structure**: The shared module exists as `mojo-py/shared/` within the main repository
- **Direct Imports**: Components import from shared using relative paths like `from shared.util.app_context import build_context`
- **Integrated Testing**: Tests for shared components are part of the main test suite
- **Single Deployment**: All components are packaged together

### Target State
- **Separate Repository**: The shared module will exist as an independent `mojo-shared` repository
- **Package Distribution**: The shared module will be a proper Python package installable via pip
- **External Dependency**: The main repository will depend on mojo-shared as an external package
- **Independent Versioning**: The shared library can be versioned and released independently

## Components and Interfaces

### Repository Structure

#### mojo-shared Repository Structure
```
mojo-shared/
├── __init__.py
├── README.md
├── pyproject.toml
├── setup.py
├── requirements.txt
├── .gitignore
├── auth/
│   ├── __init__.py
│   ├── guid.py
│   ├── password_manager.py
│   └── secrete.py
├── aws/
│   ├── __init__.py
│   └── r53.py
├── exceptions/
│   └── __init__.py
├── external/
│   ├── __init__.py
│   ├── bot/
│   ├── monarch/
│   └── weather/
├── model/
│   ├── __init__.py
│   ├── app.py
│   ├── auth.py
│   ├── language.py
│   └── weather.py
├── persistence/
│   ├── __init__.py
│   ├── db_exceptions.py
│   ├── redis_client.py
│   └── sqlite/
├── util/
│   ├── __init__.py
│   ├── app_context.py
│   ├── date_chinese.py
│   ├── file_util.py
│   ├── finance_util.py
│   ├── network.py
│   ├── text_util.py
│   └── time_util.py
├── tests/
│   ├── __init__.py
│   ├── auth/
│   ├── external/
│   ├── model/
│   └── util/
└── resources/
    └── sample_gaode_weather_response.json
```

### Package Configuration

#### pyproject.toml Structure
The new package will use modern Python packaging with pyproject.toml:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "mojo-shared"
version = "0.1.0"
description = "Shared utilities and models for the Mojo ecosystem"
readme = "README.md"
license = { file = "LICENSE" }
authors = [
    { name = "Yehui Zhang", email = "yehuizhang@outlook.com" }
]
requires-python = ">=3.13"
dependencies = [
    # Core dependencies extracted from current requirements
    "boto3",
    "botocore-stubs",
    "redis",
    "SQLAlchemy",
    "bcrypt",
    "PyJWT",
    "cryptography",
    "pydantic",
    "python-telegram-bot",
    "requests",
    "aiohttp",
    "gql",
    "beautifulsoup4",
    "python-dotenv",
    "PyYAML",
    "uuid-utils",
    "google-api-python-client",
    "google-auth",
    "cachetools",
    "simplejson",
]

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
    "coverage",
    "black",
    "flake8",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["*"]
exclude = ["tests*"]
```

### Import Path Migration

#### Current Import Patterns
```python
# Current imports in mojo-py
from shared.util.app_context import build_context
from shared.external.bot.shadow_bot import ShadowBot
from shared.model.app import AppName
from shared.auth.password_manager import PasswordManager
```

#### New Import Patterns
```python
# New imports after extraction (using package name directly)
from mojo-shared.util.app_context import build_context
from mojo-shared.external.bot.shadow_bot import ShadowBot
from mojo-shared.model.app import AppName
from mojo-shared.auth.password_manager import PasswordManager
```

## Data Models

### Package Metadata
- **Package Name**: `mojo-shared`
- **Module Name**: `mojo-shared` (using package name directly as module)
- **Version**: Semantic versioning starting at 0.1.0
- **Python Compatibility**: >=3.13 (updated from original 3.8+ requirement)

### Dependency Mapping
The shared module dependencies will be extracted from the current requirements.txt and categorized:

#### Core Dependencies (Required)
- Authentication: `bcrypt`, `PyJWT`, `cryptography`
- AWS Integration: `boto3`, `botocore-stubs`
- Database: `SQLAlchemy`, `redis`
- HTTP/API: `requests`, `aiohttp`, `pydantic`
- External Services: `python-telegram-bot`, `gql`, `google-api-python-client`
- Utilities: `python-dotenv`, `PyYAML`, `uuid-utils`, `beautifulsoup4`

#### Development Dependencies (Optional)
- Testing: `pytest`, `pytest-asyncio`, `coverage`
- Code Quality: `black`, `flake8`

## Error Handling

### Migration Error Scenarios

#### Import Resolution Failures
- **Problem**: Import statements fail after package extraction
- **Solution**: Comprehensive search and replace of import statements with validation
- **Fallback**: Maintain backward compatibility imports temporarily

#### Dependency Conflicts
- **Problem**: Version conflicts between mojo-shared and main repository dependencies
- **Solution**: Careful dependency version management and testing
- **Mitigation**: Use compatible version ranges rather than pinned versions

#### Missing Resources
- **Problem**: Resource files (like JSON samples) not properly included in package
- **Solution**: Proper MANIFEST.in or pyproject.toml configuration for data files
- **Validation**: Test package installation and resource access

### Runtime Error Handling
- Maintain existing error handling patterns within the shared module
- Ensure all custom exceptions are properly exported
- Preserve logging and debugging capabilities

## Testing Strategy

### Pre-Migration Testing
1. **Baseline Testing**: Run all existing tests to establish current functionality
2. **Dependency Analysis**: Identify all shared module usage across the codebase
3. **Import Mapping**: Create comprehensive list of all import statements to update

### Migration Testing
1. **Package Installation**: Verify mojo-shared installs correctly as a pip package
2. **Import Validation**: Test all new import statements work correctly
3. **Functionality Testing**: Ensure all shared module functionality works identically
4. **Integration Testing**: Verify API and Chronos components work with new package structure

### Post-Migration Validation
1. **End-to-End Testing**: Run complete application test suites
2. **Performance Testing**: Ensure no performance degradation from package extraction
3. **Deployment Testing**: Verify deployment processes work with new dependency structure

### Test Environment Setup
- **Local Development**: Use editable pip install for development workflow
- **CI/CD Integration**: Update build processes to install mojo-shared dependency
- **Version Testing**: Test with different versions of mojo-shared to ensure compatibility

## Implementation Phases

### Phase 1: Repository Setup
1. Create new mojo-shared repository
2. Copy shared module files with proper package structure
3. Create pyproject.toml and packaging configuration
4. Set up basic README and documentation

### Phase 2: Package Development
1. Implement proper __init__.py files for clean imports
2. Configure dependency management
3. Set up testing framework for the new package
4. Create initial package build and distribution

### Phase 3: Integration
1. Update mojo-py repository to use mojo-shared as dependency
2. Replace all import statements
3. Update build and deployment configurations
4. Run comprehensive testing

### Phase 4: Cleanup and Documentation
1. Remove original shared directory from mojo-py
2. Update documentation and README files
3. Create migration guide for other potential consumers
4. Establish versioning and release process