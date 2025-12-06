# Design Document

## Overview

The test directory consolidation feature will safely merge the duplicate `test` and `tests` directories in the mojo-shared project into a single standardized `tests` directory. The solution prioritizes data safety through backup mechanisms and validation steps while maintaining the existing test structure and functionality.

## Architecture

The consolidation process follows a three-phase approach:

1. **Analysis Phase**: Scan both directories to identify files, conflicts, and dependencies
2. **Backup Phase**: Create safety backups before any modifications
3. **Consolidation Phase**: Merge directories with conflict resolution and validation

## Components and Interfaces

### Directory Scanner Component

**Purpose**: Analyze the current state of both test directories

**Interface**:
- `scan_directory(path: str) -> DirectoryStructure`
- `identify_conflicts(test_dir: DirectoryStructure, tests_dir: DirectoryStructure) -> ConflictReport`
- `validate_python_packages(directory: DirectoryStructure) -> ValidationResult`

**Responsibilities**:
- Recursively scan directory structures
- Identify duplicate files between directories
- Detect missing __init__.py files
- Generate conflict reports with file metadata

### Backup Manager Component

**Purpose**: Create and manage safety backups

**Interface**:
- `create_backup(source_paths: List[str]) -> BackupInfo`
- `restore_backup(backup_info: BackupInfo) -> bool`
- `cleanup_backup(backup_info: BackupInfo) -> bool`

**Responsibilities**:
- Create timestamped backups of both test directories
- Provide rollback capability in case of failures
- Clean up backups after successful consolidation

### File Consolidator Component

**Purpose**: Execute the actual directory merge operation

**Interface**:
- `consolidate_directories(source_dirs: List[str], target_dir: str, conflict_resolution: ConflictResolution) -> ConsolidationResult`
- `resolve_conflicts(conflicts: ConflictReport, strategy: ConflictStrategy) -> ResolutionPlan`
- `validate_consolidation(target_dir: str) -> ValidationResult`

**Responsibilities**:
- Copy files from source directories to target
- Handle file conflicts using specified strategy
- Maintain directory structure and permissions
- Validate successful consolidation

## Data Models

### DirectoryStructure
```python
@dataclass
class DirectoryStructure:
    path: str
    files: List[FileInfo]
    subdirectories: Dict[str, DirectoryStructure]
    
@dataclass
class FileInfo:
    name: str
    path: str
    size: int
    modified_time: datetime
    checksum: str
```

### ConflictReport
```python
@dataclass
class ConflictReport:
    duplicate_files: List[FileConflict]
    missing_init_files: List[str]
    
@dataclass
class FileConflict:
    filename: str
    test_dir_file: FileInfo
    tests_dir_file: FileInfo
    recommended_action: ConflictAction
```

### ConsolidationResult
```python
@dataclass
class ConsolidationResult:
    success: bool
    files_moved: int
    conflicts_resolved: int
    errors: List[str]
    backup_info: BackupInfo
```

## Error Handling

### File Operation Errors
- **Permission Errors**: Check and report file/directory permissions before operations
- **Disk Space Errors**: Validate sufficient disk space for backup and consolidation
- **File Lock Errors**: Detect and handle files in use by other processes

### Validation Errors
- **Import Errors**: Test Python imports after consolidation to ensure package integrity
- **Missing Files**: Verify all expected files are present after consolidation
- **Corruption Errors**: Use checksums to verify file integrity during operations

### Recovery Strategy
- Automatic rollback to backup state on critical failures
- Detailed error logging for troubleshooting
- Graceful degradation with partial success reporting

## Testing Strategy

### Unit Tests
- Directory scanner functionality with mock file systems
- Backup manager operations with temporary directories
- File consolidator logic with controlled test scenarios
- Conflict resolution strategies with various file combinations

### Integration Tests
- End-to-end consolidation with real directory structures
- Backup and restore operations with actual files
- Python import validation after consolidation
- Error handling with simulated failure conditions

### Validation Tests
- Verify all original test files are preserved
- Confirm Python package structure remains intact
- Test that consolidated tests can be executed successfully
- Validate no test functionality is lost during consolidation

## Implementation Considerations

### Conflict Resolution Strategy
The system will use "newest file wins" as the default strategy:
- Compare modification timestamps of conflicting files
- Preserve the file with the most recent modification time
- Log all conflict resolutions for user review

### Directory Structure Preservation
- Maintain exact subdirectory hierarchy from both source directories
- Ensure all __init__.py files are present for Python package integrity
- Preserve file permissions and metadata where possible

### Performance Optimization
- Use file checksums to avoid unnecessary copies of identical files
- Implement progress reporting for large directory operations
- Batch file operations to minimize I/O overhead