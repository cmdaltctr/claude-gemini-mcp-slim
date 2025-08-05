Title: 009-UV-Dependency-Management-Migration
Date: 2025-08-05
Decision Maker: Dr Muhammad Aizat Hawari

## Context

The project has been evolving towards modern Python tooling practices, and dependency management has been identified as an area for improvement. Currently, the project uses a mixed approach with both pip-based and uv-based workflows, creating inconsistency and potential maintenance issues.

### Current State Analysis

After auditing the codebase, the following pip/pipx/requirements.txt usage was found:

#### Requirements Files
- `requirements.txt`: Core production dependencies
- `requirements-dev.txt`: Development and testing dependencies (includes pip-audit, pip-tools, pip-licenses)

#### GitHub Actions Workflows
- `.github/workflows/dependency.yml`: Heavy pip usage for dependency auditing and updates
- `.github/workflows/test.yml`: Uses pip-audit for security scanning
- `.github/workflows/security.yml`: Uses pip-audit and pip-licenses for compliance

#### Scripts and Documentation
- `scripts/installation.sh`: Transitioning to uv but maintains pip compatibility
- `scripts/setup-dev.sh`: Already using uv for dependency management
- `README.md` and `docs/DEVELOPMENT.md`: Mixed references to both pip and uv - will update soon

#### Configuration Files
- `pyproject.toml`: Already configured for uv with `[tool.uv]` section
- `Makefile`: Fully migrated to uv commands

## Decision

**We decide to fully migrate from pip to uv for all dependency management operations**, while maintaining backward compatibility where necessary for CI/CD and external tooling.

### Migration Strategy

1. **Phase 1: Core Workflow Migration** ✅ (Complete)
   - Makefile migrated to uv commands
   - Development scripts using uv
   - pyproject.toml configured for uv

2. **Phase 2: CI/CD Pipeline Migration** ✅ (Complete)
   - GitHub Actions updated to use uv with astral-sh/setup-uv@v6.4.3
   - Maintained pip-audit usage for security scanning (no uv equivalent)
   - Updated dependency management workflows with uv sync and caching

3. **Phase 3: Documentation and Cleanup** (Current Priority)
   - Update all documentation to reflect uv usage
   - Remove redundant pip references
   - Standardize installation instructions

## Rationale

### Why uv?

1. **Performance**: uv is significantly faster than pip for dependency resolution and installation
2. **Modern Python Tooling**: Better integration with modern Python project standards
3. **Unified Workflow**: Single tool for virtual environment and dependency management
4. **Lockfile Support**: Better dependency reproducibility with uv.lock
5. **Project Consistency**: Already adopted in core development workflows

### Why Not Pure pip?

1. **Speed**: pip is considerably slower for large dependency trees
2. **Resolution**: Less sophisticated dependency resolution
3. **Tooling Integration**: Requires multiple tools (pip, venv, pip-tools) vs. single uv command
4. **Modern Standards**: Moving away from legacy approaches

## Implementation Plan

### Phase 2: CI/CD Migration ✅ (Completed)

#### GitHub Actions Updates
```yaml
# Replace pip installation with uv
- name: Install uv
  uses: astral-sh/setup-uv@v6.4.3
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"

# Replace pip install commands
- name: Install dependencies
  run: uv sync --dev

# Keep pip-audit for security (no uv equivalent)
- name: Security audit
  run: |
    uv add pip-audit
    uv run pip-audit
```

#### Dependency Management Workflow
```yaml
# Update requirements using uv
- name: Update dependencies
  run: |
    uv sync
    uv tree > dependency-tree.txt
```

### Phase 3: Documentation Updates

#### README.md
```bash
# Old (pip)
pip install -e ".[dev]"

# New (uv)
uv sync --dev
```

#### Installation Scripts
```bash
# Unified installation approach
uv sync --dev  # Replaces pip install -r requirements-dev.txt
```

## Consequences

### Positive
- **Faster Development**: Significantly faster dependency operations
- **Better Reproducibility**: uv.lock provides exact dependency versions
- **Simplified Toolchain**: Single tool for Python environment management
- **Modern Standards**: Aligns with current Python packaging best practices
- **Consistent Workflow**: All developers use the same dependency management approach

### Negative
- **Learning Curve**: Developers familiar with pip need to learn uv commands
- **CI/CD Migration**: Requires updating multiple workflow files
- **Tool Availability**: Some tools (pip-audit) still require pip installation
- **Documentation Debt**: Need to update all references consistently

### Neutral
- **Backward Compatibility**: pip can still be used when necessary (e.g., pip-audit)
- **Requirements Files**: Keep requirements.txt for compatibility, but primarily use pyproject.toml

## Migration Checklist

### Completed ✅
- [x] Makefile migrated to uv commands
- [x] Core development scripts using uv
- [x] pyproject.toml configured with uv settings
- [x] setup-dev.sh using uv sync

### Completed ✅
- [x] GitHub Actions workflows migration
- [x] Dependency management automation updates
- [x] Security scanning workflow adjustments (maintained pip-audit compatibility)

### In Progress 🔄
- [ ] README.md installation instructions update
- [ ] DEVELOPMENT.md workflow documentation update
- [ ] Remove obsolete pip references in comments
- [ ] Update installation.sh for full uv adoption
- [ ] Verify all CI/CD pipelines work with uv

## Monitoring and Validation

### Success Criteria
1. All CI/CD pipelines pass with uv-based workflows
2. Development setup time reduced by >50%
3. Dependency resolution conflicts eliminated
4. All documentation consistently references uv
5. New contributors can set up environment with single `uv sync --dev` command

### Risk Mitigation
1. **Rollback Plan**: Keep requirements.txt files as fallback
2. **Gradual Migration**: Phase-based approach allows validation at each step
3. **Tool Compatibility**: Maintain pip for tools without uv equivalents
4. **Documentation**: Clear migration guide for team members

## Related Decisions

This decision builds upon:
- **ADR-005**: Configuration Decoupling Refactor (standardized configuration management)
- **Project Rules**: Use of uv as stated in rule KIYCqBvxoFyB7ce0r7WlYd

## Future Considerations

1. **uv Tool Ecosystem**: Monitor development of uv-native equivalents for pip-audit, pip-licenses
2. **Lock File Management**: Establish practices for uv.lock versioning and updates
3. **Multi-Python Version Testing**: Leverage uv's Python version management capabilities
4. **Performance Monitoring**: Track and document performance improvements from migration

---

**Status**: Phase 2 Complete - Documentation Phase Active
**Next Review**: 2025-08-12 (Focus on Phase 3 completion)
**Owner**: Development Team
