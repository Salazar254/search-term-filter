const express = require("express");
const cors = require("cors");
const multer = require("multer");
const { spawn } = require("child_process");
const path = require("path");
const fs = require("fs");

const app = express();
const OUTPUT_DIR = path.join(__dirname, "outputs");
const UPLOADS_DIR = path.join(__dirname, "uploads");

// Create directories if they don't exist
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}
if (!fs.existsSync(UPLOADS_DIR)) {
    fs.mkdirSync(UPLOADS_DIR, { recursive: true });
}

// Multer setup
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, UPLOADS_DIR);
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + "-" + file.originalname);
    }
});

const upload = multer({ storage: storage }).fields([
    { name: "terms", maxCount: 1 },
    { name: "negatives", maxCount: 1 }
]);

app.use(cors());
app.use(express.json());

app.post("/api/upload-and-process", (req, res) => {
    upload(req, res, function(err) {
        if (err) {
            console.error("Upload error:", err);
            return res.status(500).json({ 
                success: false, 
                error: "Upload failed: " + err.message 
            });
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
        
        // Generate unique output filenames
        const timestamp = Date.now();
        const outputFile = path.join(OUTPUT_DIR, "review-" + timestamp + ".csv");
        const auditFile = path.join(OUTPUT_DIR, "audit-" + timestamp + ".csv");
        
        console.log("Processing files:", {
            terms: termsFile.path,
            negatives: negativesFile.path,
            output: outputFile,
            audit: auditFile
        });
        
        // IMPORTANT: Use the virtual environment Python executable
        const pythonPath = path.join(__dirname, "..", "..", "venv", "Scripts", "python.exe");
        const mainScript = path.join(__dirname, "..", "..", "src", "main.py");
        
        console.log("Python path:", pythonPath);
        console.log("Main script:", mainScript);
        
        // Check if files exist
        if (!fs.existsSync(termsFile.path)) {
            console.error("Terms file not found:", termsFile.path);
            return res.status(500).json({
                success: false,
                error: "Terms file not found after upload"
            });
        }
        
        if (!fs.existsSync(negativesFile.path)) {
            console.error("Negatives file not found:", negativesFile.path);
            return res.status(500).json({
                success: false,
                error: "Negatives file not found after upload"
            });
        }
        
        // Call the Python script with virtual environment
        const pythonProcess = spawn(pythonPath, [
            mainScript,
            "--terms", termsFile.path,
            "--negatives", negativesFile.path,
            "--output", outputFile,
            "--audit-output", auditFile
        ], {
            // Increase buffer size to capture all output
            maxBuffer: 1024 * 1024 * 10 // 10MB
        });
        
        let stdout = "";
        let stderr = "";
        
        pythonProcess.stdout.on("data", (data) => {
            stdout += data.toString();
            console.log("Python stdout:", data.toString());
        });
        
        pythonProcess.stderr.on("data", (data) => {
            stderr += data.toString();
            console.error("Python stderr:", data.toString());
        });
        
        pythonProcess.on("close", (code) => {
            console.log("Python process exited with code " + code);
            console.log("Full stdout:", stdout);
            console.log("Full stderr:", stderr);
            
            // Clean up uploaded files
            fs.unlink(termsFile.path, () => {});
            fs.unlink(negativesFile.path, () => {});
            
            if (code === 0) {
                // Check if output files were created
                if (!fs.existsSync(outputFile)) {
                    console.error("Output file not created:", outputFile);
                    return res.status(500).json({
                        success: false,
                        error: "Output file was not created"
                    });
                }
                
                res.json({
                    success: true,
                    reviewUrl: "/outputs/" + path.basename(outputFile),
                    auditUrl: "/outputs/" + path.basename(auditFile),
                    message: stdout
                });
            } else {
                // Provide detailed error information
                let errorMessage = "Processing failed";
                if (stderr) {
                    errorMessage += ": " + stderr;
                } else if (stdout && stdout.includes("Error")) {
                    // Try to extract error from stdout
                    const lines = stdout.split('\n');
                    const errorLines = lines.filter(line => 
                        line.includes('Error') || 
                        line.includes('error') || 
                        line.includes('Traceback')
                    );
                    if (errorLines.length > 0) {
                        errorMessage += ": " + errorLines.join(' ');
                    }
                }
                
                res.status(500).json({
                    success: false,
                    error: errorMessage,
                    stdout: stdout,
                    stderr: stderr
                });
            }
        });
        
        pythonProcess.on("error", (err) => {
            console.error("Failed to start Python process:", err);
            res.status(500).json({
                success: false,
                error: "Failed to start Python process: " + err.message
            });
        });
    });
});

// Serve output files
app.use("/outputs", express.static(OUTPUT_DIR));

// Health check endpoint
app.get("/api/health", (req, res) => {
    res.json({ status: "ok", timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log("Server running on port " + PORT);
    console.log("Uploads directory: " + UPLOADS_DIR);
    console.log("Outputs directory: " + OUTPUT_DIR);
});
