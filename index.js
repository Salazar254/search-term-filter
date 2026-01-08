const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

const app = express();
const OUTPUT_DIR = path.join(__dirname, 'outputs');
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR);
}

// Multer setup
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, OUTPUT_DIR);
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({ storage: storage }).fields([
    { name: 'terms', maxCount: 1 },
    { name: 'negatives', maxCount: 1 }
]);

app.use(cors());

app.post('/api/upload-and-process', (req, res) => {
    upload(req, res, function(err) {
        if (err) {
            console.error('Upload error:', err);
            return res.status(500).json({ error: 'Upload failed' });
        }
        
        // Check if files were uploaded
        if (!req.files || !req.files.terms || !req.files.negatives) {
            return res.status(400).json({ error: 'Both terms and negatives files are required' });
        }
        
        const termsFile = req.files.terms[0];
        const negativesFile = req.files.negatives[0];
        
        // Generate unique output filenames
        const timestamp = Date.now();
        const outputFile = path.join(OUTPUT_DIR, \eview-\.csv\);
        const auditFile = path.join(OUTPUT_DIR, \udit-\.csv\);
        
        // Call the Python script
        const pythonProcess = spawn('python', [
            path.join(__dirname, '..', '..', 'src', 'main.py'),
            '--terms', termsFile.path,
            '--negatives', negativesFile.path,
            '--output', outputFile,
            '--audit-output', auditFile
        ]);
        
        let stdout = '';
        let stderr = '';
        
        pythonProcess.stdout.on('data', (data) => {
            stdout += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
            if (code === 0) {
                res.json({
                    success: true,
                    reviewUrl: \/outputs/\\,
                    auditUrl: \/outputs/\\,
                    message: stdout
                });
            } else {
                console.error('Python script error:', stderr);
                res.status(500).json({
                    success: false,
                    error: \Processing failed: \\
                });
            }
            
            // Clean up uploaded files after processing
            fs.unlink(termsFile.path, () => {});
            fs.unlink(negativesFile.path, () => {});
        });
    });
});

// Serve output files
app.use('/outputs', express.static(OUTPUT_DIR));

const PORT = process.env.PORT || 3001;
app.listen(PORT, () => {
    console.log(\Server running on port \\);
});
