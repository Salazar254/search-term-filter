const express = require("express");
const cors = require("cors");
const multer = require("multer");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs").promises;
const fsSync = require("fs");
const rateLimit = require("express-rate-limit");

const app = express();
const OUTPUT_DIR = path.join(__dirname, "outputs");
const UPLOADS_DIR = path.join(__dirname, "uploads");
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

// Security: Create directories if they don't exist
(async () => {
    try {
        await fs.mkdir(OUTPUT_DIR, { recursive: true });
        await fs.mkdir(UPLOADS_DIR, { recursive: true });
    } catch (e) {
        console.error("Directory creation error:", e);
    }
})();

// Security: Sanitize filename
function sanitizeFilename(originalname) {
    return originalname
        .replace(/\.\./g, '')           // Remove ..
        .replace(/[^\w.-]/g, '_')       // Replace special chars
        .substring(0, 255);              // Limit length
}

// Multer setup with security
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, UPLOADS_DIR);
    },
    filename: (req, file, cb) => {
        const sanitized = sanitizeFilename(file.originalname);
        cb(null, Date.now() + "-" + sanitized);
    }
});

const upload = multer({ 
    storage: storage,
    fileFilter: (req, file, cb) => {
        // Check MIME type
        const validMimes = ['text/csv', 'text/plain', 'application/vnd.ms-excel', 
                           'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                           'application/octet-stream'];
        
        // Also check file extension
        const ext = path.extname(file.originalname).toLowerCase();
        const validExts = ['.csv', '.xlsx', '.xls'];
        
        if (!validMimes.includes(file.mimetype) && !validExts.includes(ext)) {
            return cb(new Error(`Only CSV and Excel files allowed (${ext} is not allowed)`));
        }
        cb(null, true);
    },
    limits: { fileSize: MAX_FILE_SIZE }
}).fields([
    { name: "terms", maxCount: 1 },
    { name: "negatives", maxCount: 1 }
]);

// Security: CORS with restricted origins
const allowedOrigins = (process.env.ALLOWED_ORIGINS || 'http://localhost:5173').split(',');
app.use(cors({
    origin: allowedOrigins,
    credentials: true,
    methods: ['POST', 'GET'],
    maxAge: 3600
}));

// Security: Rate limiting
const uploadLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    max: 10,
    message: 'Too many upload requests, please try again later'
});

// Security: API Key authentication
function authenticateRequest(req, res, next) {
    const apiKey = req.headers['x-api-key'];
    if (!apiKey || apiKey !== (process.env.API_KEY || 'dev-key-change-in-production')) {
        return res.status(401).json({ error: 'Unauthorized: Missing or invalid API key' });
    }
    next();
}

app.use(express.json());

app.post("/api/upload-and-process", uploadLimiter, authenticateRequest, (req, res) => {
    upload(req, res, async function(err) {
        try {
            if (err instanceof multer.MulterError) {
                if (err.code === 'LIMIT_FILE_SIZE') {
                    return res.status(400).json({ success: false, error: 'File too large (max 5MB)' });
                }
                return res.status(400).json({ success: false, error: 'File upload error: ' + err.message });
            } else if (err) {
                return res.status(400).json({ success: false, error: err.message });
            }
            
            // Check if files were uploaded
            if (!req.files || !req.files.terms || !req.files.negatives) {
                return res.status(400).json({ 
                    success: false, 
                    error: "Both terms and negatives files are required" 
                });
            }
            
            const termsFile = req.files.terms[0];
            const negativesFile = req.files.negatives[0];
            
            // Security: Validate paths are in UPLOADS_DIR
            function isPathInDirectory(filePath, baseDir) {
                const realPath = path.resolve(filePath);
                const realBase = path.resolve(baseDir);
                return realPath.startsWith(realBase + path.sep);
            }
            
            if (!isPathInDirectory(termsFile.path, UPLOADS_DIR) || 
                !isPathInDirectory(negativesFile.path, UPLOADS_DIR)) {
                return res.status(400).json({ success: false, error: 'Invalid file path' });
            }
            
            // Generate unique output filenames
            const timestamp = Date.now();
            const outputFile = path.join(OUTPUT_DIR, "review-" + timestamp + ".csv");
            const auditFile = path.join(OUTPUT_DIR, "audit-" + timestamp + ".csv");
            const analyticsFile = path.join(OUTPUT_DIR, "analytics-" + timestamp + ".json");
            const suggestionsFile = path.join(OUTPUT_DIR, "suggestions-" + timestamp + ".csv");
            
            // IMPORTANT: Use the virtual environment Python executable
            const pythonPath = path.join(__dirname, "..", "..", "venv", "Scripts", "python.exe");
            const mainScript = path.join(__dirname, "..", "..", "src", "main.py");
            
            // Check if critical files exist
            if (!fsSync.existsSync(pythonPath)) {
                return res.status(500).json({
                    success: false,
                    error: "Python environment not configured"
                });
            }
            
            if (!fsSync.existsSync(mainScript)) {
                return res.status(500).json({
                    success: false,
                    error: "Processing script not found"
                });
            }
            
            // Call the Python script
            const pythonProcess = spawn(pythonPath, [
                mainScript,
                "--terms", termsFile.path,
                "--negatives", negativesFile.path,
                "--output", outputFile,
                "--audit-output", auditFile,
                "--analytics-output", analyticsFile,
                "--suggestions-output", suggestionsFile
            ], {
                maxBuffer: 1024 * 1024 * 10, // 10MB buffer
                timeout: 60000 // 60 second timeout
            });
            
            let stdout = "";
            let stderr = "";
            
            pythonProcess.stdout.on("data", (data) => {
                stdout += data.toString();
                // Don't log to console in production for security
                if (process.env.NODE_ENV !== 'production') {
                    console.log("Python:", data.toString().substring(0, 200));
                }
            });
            
            pythonProcess.stderr.on("data", (data) => {
                stderr += data.toString();
            });
            
            pythonProcess.on("close", async (code) => {
                try {
                    // Clean up uploaded files - use promises for proper async handling
                    const cleanupPromises = [
                        fs.unlink(termsFile.path).catch(err => 
                            console.error('Cleanup error:', err.message)
                        ),
                        fs.unlink(negativesFile.path).catch(err => 
                            console.error('Cleanup error:', err.message)
                        )
                    ];
                    await Promise.all(cleanupPromises);
                    
                    if (code === 0) {
                        // Check if output files were created
                        if (!fsSync.existsSync(outputFile)) {
                            return res.status(500).json({
                                success: false,
                                error: "Output file was not created"
                            });
                        }
                        
                        // Load analytics if available
                        let analyticsData = null;
                        if (fsSync.existsSync(analyticsFile)) {
                            try {
                                const analyticsContent = fsSync.readFileSync(analyticsFile, 'utf8');
                                analyticsData = JSON.parse(analyticsContent);
                            } catch (e) {
                                console.log("Could not parse analytics file");
                            }
                        }
                        
                        res.json({
                            success: true,
                            results: {
                                review: "/outputs/" + path.basename(outputFile),
                                audit: "/outputs/" + path.basename(auditFile),
                                analysis: "/outputs/" + path.basename(analyticsFile),
                                analytics: "/outputs/" + path.basename(analyticsFile),
                                suggestions: "/outputs/" + path.basename(suggestionsFile),
                                editor: "/outputs/" + path.basename(outputFile)
                            },
                            metrics: analyticsData?.metrics || {},
                            total_terms_analyzed: analyticsData?.total_terms_analyzed || 0,
                            terms_excluded: analyticsData?.terms_excluded || 0,
                            terms_remaining: analyticsData?.terms_remaining || 0,
                            recommendations: analyticsData?.recommendation || []
                        });
                    } else {
                        // Error response - don't expose raw stderr in production
                        let errorMessage = "Processing failed";
                        if (process.env.NODE_ENV !== 'production' && stderr) {
                            errorMessage += ": " + stderr.substring(0, 200);
                        }
                        
                        res.status(500).json({
                            success: false,
                            error: errorMessage
                        });
                    }
                } catch (cleanupErr) {
                    console.error("Error during cleanup:", cleanupErr);
                    res.status(500).json({
                        success: false,
                        error: "Processing completed but cleanup failed"
                    });
                }
            });
            
            pythonProcess.on("error", (err) => {
                console.error("Failed to start Python process:", err);
                res.status(500).json({
                    success: false,
                    error: "Failed to start processing"
                });
            });
            
        } catch (e) {
            console.error("Endpoint error:", e);
            res.status(500).json({
                success: false,
                error: "Internal server error"
            });
        }
    });
});

// Security: Protect output files with authentication
app.get("/outputs/:filename", authenticateRequest, (req, res) => {
    const filename = path.basename(req.params.filename); // Prevent directory traversal
    const filepath = path.join(OUTPUT_DIR, filename);
    
    // Verify path is in OUTPUT_DIR
    if (!filepath.startsWith(OUTPUT_DIR)) {
        return res.status(403).json({ error: 'Forbidden' });
    }
    
    // Check file exists
    fsSync.stat(filepath, (err, stats) => {
        if (err) {
            return res.status(404).json({ error: 'File not found' });
        }
        
        // Optional: Add file expiration (24 hours)
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours
        const fileAge = Date.now() - stats.mtime;
        
        if (fileAge > maxAge) {
            // Optionally delete expired files
            fs.unlink(filepath).catch(() => {});
            return res.status(410).json({ error: 'File has expired' });
        }
        
        res.download(filepath);
    });
});

// Health check endpoint
app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log("Server running on port " + PORT);
    console.log("Mode:", process.env.NODE_ENV || 'development');
    if (process.env.NODE_ENV !== 'production') {
        console.log("WARNING: Running in development mode. Change NODE_ENV for production.");
    }
});
