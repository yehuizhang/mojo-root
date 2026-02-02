---
inclusion: fileMatch
fileMatchPattern: '**/*.{ts,tsx}'
---
# Next.js Deployment Patterns

## Environment Variables

### NEXT_PUBLIC_* Variables
- Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser
- Must be available at **both build time and runtime**
- Baked into the JavaScript bundle during build

### Configuration Required

**Dockerfile:**
```dockerfile
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
```

**docker-compose.yml:**
```yaml
build:
  args:
    - NEXT_PUBLIC_API_URL=https://api.yehuizhang.com
environment:
  - NEXT_PUBLIC_API_URL=https://api.yehuizhang.com
```

### Why Both Build Args and Environment?
- **Build args**: Bake values into JavaScript bundle at build time
- **Runtime env**: Available to server-side code and API routes
- For `NEXT_PUBLIC_*` variables, both are needed for consistency

## Deployment Workflow

### After Code Changes
1. Rebuild container: `./build.sh web down && ./build.sh web up`
2. Invalidate CloudFront cache: `aws cloudfront create-invalidation --distribution-id E27QEWNM1GENUR --paths "/*"`
3. Wait 1-3 minutes for invalidation to complete
4. Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows/Linux)

### After Environment Variable Changes
1. Update both `build.args` and `environment` in docker-compose.yml
2. Rebuild container (build args changed, so rebuild is required)
3. Invalidate CloudFront cache
4. Hard refresh browser

## Health Checks

### Alpine-based Images
- Use `wget` instead of `curl` (curl not available in alpine)
- Health check: `wget --no-verbose --tries=1 --spider http://localhost:3000/api/health`

### Health Endpoint
Create `/app/api/health/route.ts`:
```typescript
import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'mojo-next',
  })
}
```

## CORS Configuration

### Cross-Origin Requests
When Next.js frontend and FastAPI backend are on different domains:
- Frontend: `https://yehuizhang.com`
- API: `https://api.yehuizhang.com`

### FastAPI CORS Setup
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yehuizhang.com",
        "http://localhost:3000",  # Local development
    ],
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### nginx OPTIONS Handling
nginx must handle OPTIONS preflight requests separately:
```nginx
if ($request_method = 'OPTIONS') {
    add_header 'Access-Control-Allow-Origin' 'https://yehuizhang.com' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, PATCH, OPTIONS' always;
    add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    add_header 'Access-Control-Max-Age' 600 always;
    return 204;
}
```

### Why OPTIONS Handling is Required
- Browser sends OPTIONS preflight before actual request
- Checks if cross-origin request is allowed
- Required when using `credentials: 'include'` or custom headers
- nginx CloudFront verification would block OPTIONS without special handling

### CORS and API Tools
- CORS only affects browsers
- Postman, curl, and other API clients ignore CORS
- Specific origins don't block API testing tools

## CloudFront Integration

### Distribution ID
- E27QEWNM1GENUR

### Cache Invalidation
```bash
# Invalidate all paths
aws cloudfront create-invalidation --distribution-id E27QEWNM1GENUR --paths "/*"

# Check status
aws cloudfront get-invalidation --distribution-id E27QEWNM1GENUR --id <INVALIDATION_ID>
```

### When to Invalidate
- After deploying new code
- After changing environment variables
- After updating static assets
- When users report seeing old content

### Cache Behavior
- CloudFront caches at edge locations
- Default TTL varies by content type
- HTML pages: shorter TTL recommended
- Static assets (`_next/static/*`): longer TTL with immutable cache headers

## Troubleshooting

### "Failed to fetch" Errors
1. Check browser console for actual error
2. Look for CORS errors
3. Verify API URL in network tab
4. Check if CloudFront cache is stale
5. Verify environment variables in container: `docker exec nextjs-app printenv | grep NEXT_PUBLIC`

### Container Restarts
After restarting Next.js container:
1. Restart nginx: `docker compose -f docker-compose.ssl.yml restart nginx`
2. Invalidate CloudFront cache
3. Hard refresh browser

### Build Script Issues
If `./build.sh web down` shows "Command is not supported":
- Ensure two-word commands have `exit 0` after execution
- Prevents falling through to second case statement
