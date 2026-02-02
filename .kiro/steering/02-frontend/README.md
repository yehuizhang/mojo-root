# Frontend Development Patterns

Next.js deployment and frontend patterns.

**These files are conditionally active** - they're included when working with TypeScript/Next.js files.

## Files

- **nextjs-deployment.md** - Deployment workflows, environment variables, CORS, CloudFront

## When to Reference

These files are automatically included when working with:
- TypeScript files (`**/*.ts`, `**/*.tsx`)
- Next.js components and pages
- Frontend deployment and configuration

## Activation

Add this frontmatter to activate for TypeScript files:
```yaml
---
inclusion: fileMatch
fileMatchPattern: '**/*.{ts,tsx}'
---
```
