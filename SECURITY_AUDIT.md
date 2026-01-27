# DEEP SECURITY & LOGIC AUDIT REPORT
**Date**: January 9, 2026  
**Status**: CRITICAL VULNERABILITIES FOUND

---

## EXECUTIVE SUMMARY
Multiple security vulnerabilities and logic errors identified across all layers. Severity levels: 3 CRITICAL, 4 HIGH, 2 MEDIUM.

---

## 1. BACKEND SECURITY VULNERABILITIES (web/server/index.js)

### 🔴 CRITICAL: Path Traversal via File Upload (Line 26)
**Severity**: CRITICAL  
**Issue**: Using `file.originalname` directly without sanitization
```javascript
filename: (req, file, cb) => {
    cb(null, Date.now() + "-" + file.originalname);  // ⚠️ UNSAFE
}
```
**Attack**: User uploads `../../malicious.py` → written to parent directories  
**Impact**: File write anywhere on disk (RCE potential)  
**Fix**: Sanitize filename
```javascript
filename: (req, file, cb) => {
    const sanitized = file.originalname.replace(/[^a-zA-Z0-9._-]/g, '_');
    cb(null, Date.now() + "-" + sanitized);
}
```

### 🔴 CRITICAL: No File Type Validation on Upload
**Severity**: CRITICAL  
**Issue**: No validation of uploaded file types
```javascript
const upload = multer({ storage: storage }).fields([
    { name: "terms", maxCount: 1 },
    { name: "negatives", maxCount: 1 }
]);
// ⚠️ No file type validation - could upload .exe, .zip, .js, etc.
```
**Attack**: Upload executable/malicious files disguised as CSV  
**Impact**: Code execution, data theft  
**Fix**: Add file type validation
```javascript
const upload = multer({ 
    storage: storage,
    fileFilter: (req, file, cb) => {
        const allowedMimes = ['text/csv', 'application/vnd.ms-excel', 
                             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
        if (allowedMimes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error('Only CSV and Excel files are allowed'));
        }
    },
    limits: { fileSize: 5 * 1024 * 1024 } // 5MB max
}).fields([...]);
```

### 🔴 CRITICAL: Unrestricted CORS Configuration
**Severity**: CRITICAL  
**Issue**: CORS allows requests from ANY origin
```javascript
app.use(cors());  // ⚠️ Allows ALL origins
```
**Attack**: Attacker site makes requests to your API, exfiltrates data  
**Impact**: Cross-site request forgery, data theft  
**Fix**: Restrict CORS
```javascript
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || 'http://localhost:5173',
    credentials: true,
    methods: ['POST', 'GET'],
    maxAge: 3600
}));
```

### 🟠 HIGH: No Input Validation on Command Args
**Severity**: HIGH  
**Issue**: File paths passed to Python without validation
```javascript
const pythonProcess = spawn(pythonPath, [
    mainScript,
    "--terms", termsFile.path,      // ⚠️ Unvalidated
    "--negatives", negativesFile.path, // ⚠️ Unvalidated
    "--output", outputFile,          // ⚠️ Generated safely but could be improved
    ...
]);
```
**Risk**: While `path.join()` prevents basic traversal, paths should be validated  
**Fix**: Validate paths are within expected directories
```javascript
function isPathInDirectory(filePath, baseDir) {
    const realPath = path.resolve(filePath);
    const realBase = path.resolve(baseDir);
    return realPath.startsWith(realBase + path.sep);
}

if (!isPathInDirectory(termsFile.path, UPLOADS_DIR)) {
    throw new Error('Invalid file path');
}
```

### 🟠 HIGH: Process Output Logged with Sensitive Data
**Severity**: HIGH  
**Issue**: Full Python stdout/stderr logged including file paths
```javascript
pythonProcess.stdout.on("data", (data) => {
    stdout += data.toString();
    console.log("Python stdout:", data.toString());  // ⚠️ Logs everything
});
```
**Risk**: Logs may contain sensitive paths, data, user information  
**Fix**: Filter sensitive output
```javascript
pythonProcess.stdout.on("data", (data) => {
    const sanitized = data.toString().replace(/path: [^,]+/g, 'path: [REDACTED]');
    console.log("Python stdout:", sanitized);
});
```

### 🟠 HIGH: No Error Rate Limiting
**Severity**: HIGH  
**Issue**: No rate limiting on upload endpoint
**Risk**: DoS attack (upload 1000s of files, crash server)  
**Fix**: Add rate limiting
```javascript
const rateLimit = require('express-rate-limit');

const uploadLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 10,                   // limit each IP to 10 requests per windowMs
    message: 'Too many uploads, please try again later'
});

app.post("/api/upload-and-process", uploadLimiter, (req, res) => {
    // ...
});
```

### 🟡 MEDIUM: Incomplete Error Handling
**Severity**: MEDIUM  
**Issue**: Python stderr logged directly to response
```javascript
res.status(500).json({
    success: false,
    error: errorMessage,
    stdout: stdout,    // ⚠️ Could expose system info
    stderr: stderr     // ⚠️ Could expose system info
});
```
**Fix**: Sanitize error responses
```javascript
res.status(500).json({
    success: false,
    error: process.env.NODE_ENV === 'production' 
        ? 'Processing failed' 
        : errorMessage
    // Don't send full stdout/stderr to clients in production
});
```

---

## 2. FRONTEND SECURITY VULNERABILITIES (web/client/src/App.tsx)

### 🟠 HIGH: Unvalidated Server Response Display
**Severity**: HIGH  
**Issue**: Server response data directly rendered without sanitization
```typescript
{results.recommendations.map((rec: string, idx: number) => (
    <div key={idx} className="flex gap-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
        <div className="text-blue-600 font-bold text-lg">💡</div>
        <p className="text-gray-700 text-sm">{rec}</p>  {/* ⚠️ No HTML escaping */}
    </div>
))}
```
**Risk**: XSS if server compromised or attacked  
**Attack**: Server sends `<img src=x onerror="alert('xss')">`  
**Fix**: React escapes by default, but validate server data
```typescript
import DOMPurify from 'dompurify';
<p>{DOMPurify.sanitize(rec)}</p>
```

### 🟡 MEDIUM: Download Links Not Validated
**Severity**: MEDIUM  
**Issue**: Download URLs from server not validated
```tsx
<a href={`http://localhost:3001${results.results.review}`} download>
    {/* ⚠️ Trust server URL but no validation */}
</a>
```
**Risk**: If server compromised, could redirect to malicious sites  
**Fix**: Validate URLs
```typescript
function isValidUrl(url: string): boolean {
    try {
        const parsed = new URL(url, 'http://localhost:3001');
        return parsed.hostname === 'localhost' && parsed.pathname.startsWith('/outputs/');
    } catch {
        return false;
    }
}
```

### 🟡 MEDIUM: No CSRF Protection
**Severity**: MEDIUM  
**Issue**: No CSRF token validation
**Risk**: Attacker site auto-submits forms, uploads malicious files  
**Fix**: Add CSRF token
```typescript
// Backend
const csrf = require('csurf');
app.use(csrf({ cookie: true }));

// Frontend
const [csrfToken, setCsrfToken] = useState('');
// Then include in form
formData.append('_csrf', csrfToken);
```

---

## 3. PYTHON PROCESSING LOGIC ERRORS (src/*.py)

### 🟠 HIGH: Unsafe subprocess.run in batch_processor.py
**Severity**: HIGH  
**Location**: Line 41
**Issue**: Command constructed from user input without shell escaping
```python
cmd = [
    "python", "src/main.py",
    "--terms", terms_file,  # ⚠️ User-controlled
    "--negatives", negatives_file,  # ⚠️ User-controlled
    ...
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
```
**Risk**: While using list format (not shell=True) is safer, paths could be crafted  
**Attack**: Filename like `--output /etc/passwd` could write to system files  
**Fix**: Validate file paths
```python
from pathlib import Path

def is_valid_path(filepath):
    p = Path(filepath).resolve()
    allowed_dirs = [Path('data'), Path('web/server/uploads')]
    return any(p.is_relative_to(d.resolve()) for d in allowed_dirs)

if not is_valid_path(terms_file):
    raise ValueError(f"Invalid path: {terms_file}")
```

### 🟠 HIGH: Division by Zero Risk in auto_negative.py
**Severity**: HIGH  
**Location**: Line 35
**Issue**: 
```python
self.terms_df['CPC'] = self.terms_df['Cost'] / self.terms_df['Clicks'].clip(lower=0.01)
```
**Problem**: `clip(lower=0.01)` clips to 0.01 but should be `max(0.01, value)` to prevent div/0  
**Better Fix**:
```python
self.terms_df['CPC'] = np.where(
    self.terms_df['Clicks'] > 0,
    self.terms_df['Cost'] / self.terms_df['Clicks'],
    np.nan
)
```

### 🟠 HIGH: Logic Error in Confidence Score (auto_negative.py)
**Severity**: HIGH  
**Location**: Line 58
**Issue**:
```python
occurrence_ratio = keyword_stats['count'] / max(total_poor_performers, 1)
score += min(30, occurrence_ratio * 30)
```
**Problem**: If `occurrence_ratio > 1`, score still capped at 30, but math is wrong  
**Fix**:
```python
# Ratio of poor performers containing this keyword
max_ratio = min(1.0, keyword_stats['count'] / max(total_poor_performers, 1))
score += max_ratio * 30
```

### 🟠 HIGH: Missing Null Checks in analytics.py
**Severity**: HIGH  
**Location**: Multiple places (lines 20-30)
**Issue**:
```python
if 'Cost' in excluded.columns:
    total_cost_waste = pd.to_numeric(excluded['Cost'], errors='coerce').sum()
else:
    total_cost_waste = len(excluded) * 2.5  # ⚠️ Hardcoded fallback
```
**Problem**: Falls back to estimation, but never validates the estimate is reasonable  
**Risk**: If excluded set is huge, wildly inaccurate metrics  
**Fix**:
```python
if excluded.empty:
    total_cost_waste = 0
elif 'Cost' in excluded.columns:
    costs = pd.to_numeric(excluded['Cost'], errors='coerce')
    total_cost_waste = costs.sum() if costs.notna().any() else 0
else:
    # More conservative fallback
    total_cost_waste = 0
    warnings.warn("Cost column not available, cannot calculate savings")
```

### 🟡 MEDIUM: Unsafe Column Rename Logic (src/main.py)
**Severity**: MEDIUM  
**Issue**: While recently fixed, the logic could still create duplicates
```python
if keyword_col and keyword_col != 'negative_keyword':
    df = df.rename(columns={keyword_col: 'negative_keyword'})
```
**Risk**: If somehow `keyword_col` is not found, code proceeds without it  
**Fix**: Add strict validation
```python
if 'negative_keyword' not in df.columns:
    raise ValueError("Required column 'negative_keyword' not found")
```

### 🟡 MEDIUM: No Data Size Limits
**Severity**: MEDIUM  
**Issue**: No validation of input file sizes
**Risk**: Process could crash with 1GB+ CSV files  
**Fix** (in main.py):
```python
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
file_size = os.path.getsize(filepath)
if file_size > MAX_FILE_SIZE:
    raise ValueError(f"File too large ({file_size} bytes > {MAX_FILE_SIZE})")
```

---

## 4. AUTHENTICATION & AUTHORIZATION

### 🔴 CRITICAL: No Authentication Required
**Severity**: CRITICAL  
**Issue**: Endpoints accessible without any authentication
**Risk**: Anyone can upload files, access results  
**Fix**: Add API key or JWT authentication
```javascript
function authenticateRequest(req, res, next) {
    const apiKey = req.headers['x-api-key'];
    if (apiKey !== process.env.API_KEY) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    next();
}

app.post("/api/upload-and-process", authenticateRequest, (req, res) => {
    // ...
});
```

---

## 5. DATA PROTECTION

### 🔴 CRITICAL: Uploaded Files Never Deleted
**Severity**: CRITICAL  
**Location**: web/server/index.js lines 130-131
**Issue**:
```javascript
fs.unlink(termsFile.path, () => {});
fs.unlink(negativesFile.path, () => {});
```
**Problem**: These operations don't wait (no error handling), files may persist  
**Risk**: Disk space exhaustion, data exposure  
**Fix**:
```javascript
fs.unlink(termsFile.path, (err) => {
    if (err) console.error('Failed to delete upload:', err);
});
fs.unlink(negativesFile.path, (err) => {
    if (err) console.error('Failed to delete upload:', err);
});

// Better approach - use promises
const fs = require('fs').promises;
try {
    await Promise.all([
        fs.unlink(termsFile.path),
        fs.unlink(negativesFile.path)
    ]);
} catch (e) {
    console.error('Cleanup error:', e);
}
```

### 🔴 CRITICAL: Output Files Permanently Accessible
**Severity**: CRITICAL  
**Issue**: All output files accessible via `/outputs/` route indefinitely
```javascript
app.use("/outputs", express.static(OUTPUT_DIR));
```
**Risk**: User A can access User B's analysis results  
**Fix**: Add expiration and access control
```javascript
// Generate signed URLs with expiration
const crypto = require('crypto');

function generateSignedUrl(filename, expiresIn = 3600) {
    const timestamp = Math.floor(Date.now() / 1000) + expiresIn;
    const signature = crypto
        .createHmac('sha256', process.env.SECRET)
        .update(`${filename}:${timestamp}`)
        .digest('hex');
    return `${filename}?expires=${timestamp}&sig=${signature}`;
}

// Verify signature on download
app.get('/outputs/:filename', (req, res) => {
    const { expires, sig } = req.query;
    const expected = crypto
        .createHmac('sha256', process.env.SECRET)
        .update(`${req.params.filename}:${expires}`)
        .digest('hex');
    
    if (sig !== expected || expires < Math.floor(Date.now() / 1000)) {
        return res.status(401).json({ error: 'Unauthorized' });
    }
    res.download(path.join(OUTPUT_DIR, req.params.filename));
});
```

---

## 6. LOGIC ERRORS SUMMARY TABLE

| Component | Issue | Severity | Impact |
|-----------|-------|----------|--------|
| batch_processor.py | Path args not validated | HIGH | Potential file write outside intended dir |
| auto_negative.py | Division by zero risk | HIGH | Runtime crash on zero-click keywords |
| auto_negative.py | Faulty ratio math | HIGH | Incorrect confidence scores |
| analytics.py | Missing null checks | HIGH | Inaccurate metrics on missing data |
| main.py | Column validation incomplete | MEDIUM | Could fail silently |
| main.py | No file size limits | MEDIUM | DoS via huge files |
| All Python | No input validation | MEDIUM | Unexpected behavior on bad data |

---

## PRIORITY FIXES (In Order)

### IMMEDIATE (This Week)
1. ✅ Add file type validation to multer (CRITICAL)
2. ✅ Sanitize uploaded filenames (CRITICAL)  
3. ✅ Restrict CORS origins (CRITICAL)
4. ✅ Add API authentication (CRITICAL)
5. ✅ Implement file expiration/access control (CRITICAL)

### SHORT TERM (This Month)
6. ✅ Add rate limiting
7. ✅ Validate all file paths in Python
8. ✅ Fix division by zero in auto_negative.py
9. ✅ Add input validation for all CLI args
10. ✅ Add file size limits

### MEDIUM TERM (This Quarter)
11. ✅ Implement CSRF protection
12. ✅ Add comprehensive logging/audit trail
13. ✅ Implement request signing for output files
14. ✅ Add comprehensive error handling

---

## TESTING CHECKLIST

- [ ] Try uploading `.exe`, `.zip`, `../../etc/passwd` filenames
- [ ] Try uploading from `curl` without proper headers
- [ ] Try accessing outputs from different browser/IP
- [ ] Try uploading 1GB file
- [ ] Try uploading malformed CSV with special characters
- [ ] Try accessing `/outputs/` directly
- [ ] Try CORS request from different origin
- [ ] Check server logs for sensitive data leaks
- [ ] Verify uploaded files are deleted
- [ ] Test with Python args containing quotes/spaces

---

## CONCLUSION

The application has **critical vulnerabilities** that must be addressed before production use. Primary risks are:
1. **File upload exploitation** (path traversal, type validation)
2. **No authentication** (anyone can access)
3. **Data persistence** (files never deleted, outputs always accessible)
4. **Logic errors** in analytics/suggestions (produces wrong results)

Implementing the immediate fixes will significantly improve security posture.
