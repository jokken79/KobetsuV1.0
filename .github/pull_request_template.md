## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Please mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] Dependency update
- [ ] CI/CD improvement

## Related Issues

<!-- Link to related issues -->
Fixes #(issue number)

## Changes Made

<!-- List the specific changes made in this PR -->

-
-
-

## Testing

### Test Configuration

- **Python version**: 3.11
- **Node.js version**: 20
- **PostgreSQL version**: 15

### Tests Performed

<!-- Describe the tests you ran to verify your changes -->

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] E2E tests pass (if applicable)

### Test Coverage

<!-- Include test coverage if applicable -->
- Current coverage: X%
- Previous coverage: Y%

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Checklist

### Code Quality

- [ ] My code follows the style guidelines of this project
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes

### Legal Compliance (if modifying contract logic)

- [ ] Changes comply with 労働者派遣法第26条 requirements
- [ ] All 16 required contract fields are maintained
- [ ] Document generation templates updated if needed

### Security

- [ ] No sensitive data (passwords, API keys) included in code
- [ ] Input validation added for new endpoints
- [ ] SQL injection prevention verified (if database queries modified)
- [ ] Authentication/authorization properly implemented

### Performance

- [ ] No N+1 query problems introduced
- [ ] Database indexes added if needed
- [ ] Frontend bundle size impact assessed
- [ ] API response times acceptable

### Database Changes (if applicable)

- [ ] Migration created and tested
- [ ] Migration is reversible
- [ ] Migration tested with production-like data volume
- [ ] Database backup plan considered

### Documentation

- [ ] API documentation updated
- [ ] README updated if needed
- [ ] CLAUDE.md updated if architecture changed
- [ ] Comments added for complex logic

## Deployment Notes

<!-- Any special instructions for deployment -->

- [ ] Environment variables added/changed
- [ ] Database migrations required
- [ ] Breaking changes communicated
- [ ] Rollback plan prepared

## Additional Notes

<!-- Any additional information that reviewers should know -->

---

**Reviewer Guidelines:**
- Check that all tests pass in CI
- Verify no security vulnerabilities introduced
- Ensure code follows project conventions
- Validate database migration if present
- Test functionality manually if critical path