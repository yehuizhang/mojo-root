# Steering Files Organization

Hierarchical organization for context-aware guidance. Files automatically load based on what you're working on.

## 📁 Structure

```
.kiro/steering/
├── 00-project/          ⚡ Always Active
├── 01-backend/          🐍 Python files
├── 02-frontend/         ⚛️  TypeScript files
└── 03-features/         🎯 Feature-specific
```

## 🎯 When Each Section Activates

| Section | Activation | File Patterns |
|---------|-----------|---------------|
| **00-project/** | Always | All contexts |
| **01-backend/** | Conditional | `**/*.py` |
| **02-frontend/** | Conditional | `**/*.{ts,tsx}` |
| **03-features/** | Conditional | `**/finance/**/*.{py,ts,tsx}` |

## 📚 What's in Each Section

### 00-project/ (Always Active)
Essential project knowledge:
- **architecture.md** - Services, tech stack, patterns, conventions
- **commands.md** - Development, deployment, troubleshooting commands
- **troubleshooting.md** - Common issues and solutions

### 01-backend/ (Python Development)
FastAPI and Python patterns:
- **fastapi-basics.md** - DI, error handling, context, Handler+DAO pattern
- **fastapi-async.md** - Async/await, concurrent operations
- **redis-patterns.md** - Key naming, caching, serialization
- **testing.md** - pytest, mocking, fixtures, coverage

### 02-frontend/ (TypeScript Development)
Next.js and frontend patterns:
- **nextjs-deployment.md** - Deployment, env vars, CORS, CloudFront

### 03-features/ (Feature Work)
Domain-specific knowledge:
- **stock-tracking.md** - Trading strategies, signals, architecture

## 🔍 How to Use

### Automatic Activation
Files load based on what you're working on:
- Editing Python file → Backend patterns load
- Editing TypeScript file → Frontend patterns load
- Working in finance/ folder → Stock tracking loads

### Manual Reference
Reference specific files in chat:
- `#architecture` - Project architecture
- `#commands` - Essential commands
- `#fastapi-basics` - FastAPI patterns
- `#stock-tracking` - Stock tracking domain

## 💡 Tips

1. **Start with 00-project/** - Always available, covers essentials
2. **Backend work?** - 01-backend/ patterns auto-load for .py files
3. **Frontend work?** - 02-frontend/ patterns auto-load for .ts/.tsx files
4. **Feature work?** - 03-features/ loads for specific feature areas
5. **Need everything?** - Reference specific files manually with #

## 🎨 Benefits

1. **Smaller context** - Only load what you need (~75% reduction)
2. **Better organization** - Related patterns grouped
3. **Clear hierarchy** - Numbered folders show importance
4. **Easier navigation** - README guides in each section
5. **Flexible activation** - Automatic or manual inclusion

## Frontmatter Patterns

```yaml
---
inclusion: always          # Always included
---
```

```yaml
---
inclusion: fileMatch       # Included when pattern matches
fileMatchPattern: '**/*.py'
---
```

```yaml
---
inclusion: manual          # Only when explicitly referenced with #
---
```

## Migration Notes

Reorganized from flat structure on 2026-02-01. See `MIGRATION.md` for details.
