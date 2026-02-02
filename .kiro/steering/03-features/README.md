# Feature-Specific Knowledge

Domain-specific knowledge for features in the mojo project.

**These files are conditionally active** - they're included when working with specific feature areas.

## Files

- **stock-tracking.md** - Stock tracking assistant domain knowledge, trading strategies, signal generation

## When to Reference

These files are automatically included when working with:
- Finance/stock tracking related files
- Trading strategy implementations
- Signal generation and analysis

## Activation

Add this frontmatter to activate for specific feature files:
```yaml
---
inclusion: fileMatch
fileMatchPattern: '**/finance/**/*.{py,ts,tsx}'
---
```

Or use manual inclusion:
```yaml
---
inclusion: manual
---
```

Then reference with `#stock-tracking` in chat.
