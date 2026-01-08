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
            return res.status(500).json({ error: "Upload failed: " + err.message });
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
        
        // Call the Python script
        const pythonProcess = spawn("python", [
            path.join(__dirname, "..", "..", "src", "main.py"),
            "--terms", termsFile.path,
            "--negatives", negativesFile.path,
            "--output", outputFile,
            "--audit-output", auditFile
        ]);
        
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
            
            // Clean up uploaded files
            fs.unlink(termsFile.path, () => {});
            fs.unlink(negativesFile.path, () => {});
            
            if (code === 0) {
                res.json({
                    success: true,
                    reviewUrl: "/outputs/" + path.basename(outputFile),
                    auditUrl: "/outputs/" + path.basename(auditFile),
                    message: stdout
                });
            } else {
                res.status(500).json({
                    success: false,
                    error: "Processing failed: " + (stderr || "Unknown error")
                });
            }
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
