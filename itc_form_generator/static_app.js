/* ITC Form Generator — Application JavaScript
 * Upload page functionality + Results page functionality
 * Extracted and updated for Flask API endpoints
 */

// ==============================
// Upload Page Functions
// ==============================
        function setupDropZone(dropZoneId, inputId, filenameId) {
            const dropZone = document.getElementById(dropZoneId);
            const input = document.getElementById(inputId);
            const filenameEl = document.getElementById(filenameId);

            if (!dropZone || !input || !filenameEl) {
                console.error('Drop zone elements not found:', dropZoneId, inputId, filenameId);
                return;
            }

            // Drag and drop support
            dropZone.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.add('dragover');
            });

            dropZone.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
            });

            dropZone.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.classList.remove('dragover');
                if (e.dataTransfer.files.length) {
                    input.files = e.dataTransfer.files;
                    updateFilename();
                }
            });

            // File input change event - this is the key one!
            input.addEventListener('change', function(e) {
                console.log('File selected:', inputId, this.files[0]?.name);
                updateFilename();
            });

            function updateFilename() {
                if (input.files && input.files.length > 0) {
                    const fileName = input.files[0].name;
                    filenameEl.textContent = '\u2713 ' + fileName;
                    filenameEl.style.color = '#22c55e';
                    filenameEl.style.fontWeight = 'bold';
                    dropZone.classList.add('has-file');
                    console.log('Filename updated:', fileName);
                } else {
                    filenameEl.textContent = '';
                    dropZone.classList.remove('has-file');
                }
            }
        }

        // Initialize drop zones immediately (elements exist before script runs)
        setupDropZone('sooDropZone', 'sooFile', 'sooFilename');
        setupDropZone('pointsDropZone', 'pointsFile', 'pointsFilename');
        setupDropZone('exampleDropZone', 'exampleFile', 'exampleFilename');
        console.log('Drop zones initialized');

        // AI checkbox toggle info box
        const aiCheckbox = document.getElementById('useAiCheckbox');
        const aiInfoBox = document.getElementById('aiInfoBox');
        aiCheckbox.addEventListener('change', () => {
            aiInfoBox.style.display = aiCheckbox.checked ? 'block' : 'none';
        });

        // Load learned examples stats
        async function loadExamplesStats() {
            try {
                const response = await fetch('/api/examples/stats');
                const data = await response.json();

                const statsDiv = document.getElementById('learnedExamplesStats');
                const contentDiv = document.getElementById('examplesContent');

                if (data.total_examples > 0) {
                    statsDiv.style.display = 'block';

                    let systemTags = '';
                    for (const [sys, count] of Object.entries(data.by_system || {})) {
                        systemTags += `<span style="background: #dcfce7; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 5px;">${sys}: ${count}</span>`;
                    }

                    let sourceTags = '';
                    for (const [src, count] of Object.entries(data.by_source || {})) {
                        sourceTags += `<span style="background: #dbeafe; padding: 2px 8px; border-radius: 10px; font-size: 12px; margin-right: 5px;">${src}: ${count}</span>`;
                    }

                    contentDiv.innerHTML = `
                        <div style="display: flex; gap: 20px; margin-bottom: 10px;">
                            <div><strong>${data.total_examples}</strong> example forms</div>
                            <div><strong>${data.total_items_learned}</strong> check items learned</div>
                        </div>
                        <div style="margin-bottom: 8px;"><strong>By System:</strong> ${systemTags || 'None'}</div>
                        <div><strong>By Source:</strong> ${sourceTags || 'None'}</div>
                    `;
                }
            } catch (error) {
                console.log('No examples data yet');
            }
        }
        loadExamplesStats();

        // Handle example form upload
        document.getElementById('exampleForm').addEventListener('submit', async function(e) {
            e.preventDefault();

            // Debug logging
            console.log('Form submit triggered');

            const fileInput = document.getElementById('exampleFile');
            const sourceInput = document.querySelector('input[name="source"]');

            console.log('File selected:', fileInput.files.length > 0 ? fileInput.files[0].name : 'NONE');
            console.log('Source value:', sourceInput.value);

            if (!fileInput.files.length) {
                alert('Please select an Excel or CSV file first');
                return;
            }

            if (!sourceInput.value.trim()) {
                alert('Please enter a Source/Company name');
                return;
            }

            const formData = new FormData(this);

            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Uploading & Learning...';

            try {
                console.log('Sending fetch request...');
                const response = await fetch('/upload-example', {
                    method: 'POST',
                    body: formData
                });

                console.log('Response status:', response.status);
                const result = await response.json();
                console.log('Response data:', result);

                if (result.success) {
                    let message = `Successfully learned from "${result.filename}"\n\n`;
                    message += `Extracted:\n`;
                    message += `- ${result.items_learned} check items\n`;
                    message += `- ${result.sections_learned} sections\n`;

                    if (result.equipment_type) {
                        message += `\nDetected Equipment:\n`;
                        message += `- Type: ${result.equipment_type}\n`;
                        if (result.level) message += `- Level: ${result.level}\n`;
                        if (result.variant) message += `- Variant: ${result.variant}\n`;
                    }

                    if (result.section_names && result.section_names.length > 0) {
                        message += `\nSections Found:\n`;
                        message += result.section_names.slice(0, 5).map(s => `- ${s}`).join('\n');
                    }

                    alert(message);
                    this.reset();
                    document.getElementById('exampleFilename').textContent = '';
                    document.getElementById('exampleDropZone').classList.remove('has-file');
                    loadExamplesStats();
                } else {
                    alert('Failed to process example: ' + (result.error || 'Unknown error'));
                }
            } catch (error) {
                console.error('Upload error:', error);
                alert('Upload failed: ' + error.message + '\n\nCheck browser console (F12) for details.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Upload & Learn from Example';
            }
        });

        // Progress tracking
        const form = document.getElementById('uploadForm');
        const progressOverlay = document.getElementById('progressOverlay');
        const progressBar = document.getElementById('progressBar');
        const progressPercent = document.getElementById('progressPercent');
        const progressTime = document.getElementById('progressTime');
        const progressStatus = document.getElementById('progressStatus');

        let startTime;
        let progressInterval;
        let currentProgress = 0;

        const statusMessages = [
            'Initializing...',
            'Reading document...',
            'Parsing systems and equipment...',
            'Extracting setpoints and parameters...',
            'Generating PFI forms...',
            'Generating FPT forms...',
            'Generating IST forms...',
            'Generating CXC forms...',
            'Rendering HTML output...',
            'Finalizing...'
        ];

        function formatTime(seconds) {
            if (seconds < 60) return seconds + 's';
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return mins + 'm ' + secs + 's';
        }

        function updateProgress() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            progressTime.textContent = 'Elapsed: ' + formatTime(elapsed);

            // Simulate progress (actual progress is indeterminate)
            if (currentProgress < 90) {
                currentProgress += Math.random() * 3;
                if (currentProgress > 90) currentProgress = 90;
                progressBar.style.width = currentProgress + '%';
                progressPercent.textContent = Math.floor(currentProgress) + '%';
            }

            // Update status message based on progress
            const statusIndex = Math.min(Math.floor(currentProgress / 10), statusMessages.length - 1);
            progressStatus.textContent = statusMessages[statusIndex];
        }

        form.addEventListener('submit', function(e) {
            // Show progress overlay
            progressOverlay.classList.add('active');
            startTime = Date.now();
            currentProgress = 0;
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';

            // Start progress updates
            progressInterval = setInterval(updateProgress, 200);

            // Store start time for results page
            sessionStorage.setItem('formGenStartTime', startTime);
        });

        // RSB/ATS Template Level Toggle
        document.getElementById('rsbLevel').addEventListener('change', function() {
            const l4Options = document.getElementById('rsbL4Options');
            const l3Options = document.getElementById('rsbL3Options');
            if (this.value === 'L3') {
                l4Options.style.display = 'none';
                l3Options.style.display = 'block';
            } else {
                l4Options.style.display = 'block';
                l3Options.style.display = 'none';
            }
        });

        document.getElementById('atsLevel').addEventListener('change', function() {
            const l4Options = document.getElementById('atsL4Options');
            const l3Options = document.getElementById('atsL3Options');
            if (this.value === 'L3') {
                l4Options.style.display = 'none';
                l3Options.style.display = 'block';
            } else if (this.value === 'L4') {
                l4Options.style.display = 'block';
                l3Options.style.display = 'none';
            } else {
                // L2 or L2C - hide both
                l4Options.style.display = 'none';
                l3Options.style.display = 'none';
            }
        });

        // Generate RSB Form
        function generateRSBForm() {
            const level = document.getElementById('rsbLevel').value;
            let url = '/api/rsb/generate?format=html&level=' + level;

            if (level === 'L4') {
                const formType = document.getElementById('rsbFormType').value;
                url += '&form_type=' + formType;
            } else {
                const area = document.getElementById('rsbArea').value;
                const number = document.getElementById('rsbNumber').value;
                const variant = document.getElementById('rsbVariant').value;
                url += '&area=' + area + '&number=' + number + '&variant=' + variant;
            }

            window.open(url, '_blank');
        }

        // Generate ATS Form
        function generateATSForm() {
            const level = document.getElementById('atsLevel').value;
            let url = '/api/ats/generate?format=html&level=' + level;

            if (level === 'L4') {
                const category = document.getElementById('atsCategory').value;
                url += '&category=' + category;
            } else if (level === 'L3') {
                const area = document.getElementById('atsArea').value;
                const identifier = document.getElementById('atsIdentifier').value;
                const variant = document.getElementById('atsVariant').value;
                url += '&area=' + area + '&identifier=' + identifier + '&variant=' + variant;
            }
            // L2 and L2C don't need additional params

            window.open(url, '_blank');
        }

        // Multi-file display update function
        function updateMultiFileDisplay(inputId, displayId) {
            const input = document.getElementById(inputId);
            const display = document.getElementById(displayId);
            const dropZone = input.parentElement;

            if (input.files && input.files.length > 0) {
                let fileNames = [];
                for (let i = 0; i < input.files.length; i++) {
                    fileNames.push('✓ ' + input.files[i].name);
                }
                display.innerHTML = fileNames.join('<br>');
                display.style.color = '#22c55e';
                display.style.fontWeight = 'bold';
                dropZone.classList.add('has-file');
                console.log('Files selected:', input.files.length, fileNames);
            } else {
                display.textContent = '';
                dropZone.classList.remove('has-file');
            }
        }

        // Add more SOO file inputs
        let sooFileCount = 1;
        function addSooFile() {
            sooFileCount++;
            const container = document.getElementById('sooFilesList');
            const newEntry = document.createElement('div');
            newEntry.className = 'soo-file-entry';
            newEntry.style.marginBottom = '10px';
            newEntry.innerHTML = `
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="file" name="soo_files" accept=".pdf,.md,.txt"
                           style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                    <span style="color: #666; font-size: 12px;">SOO #${sooFileCount}</span>
                    <button type="button" onclick="this.parentElement.parentElement.remove()"
                            style="padding: 4px 8px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">✕</button>
                </div>
            `;
            container.appendChild(newEntry);
        }

        // Add more Points file inputs
        let pointsFileCount = 1;
        function addPointsFile() {
            pointsFileCount++;
            const container = document.getElementById('pointsFilesList');
            const newEntry = document.createElement('div');
            newEntry.className = 'points-file-entry';
            newEntry.style.marginBottom = '10px';
            newEntry.innerHTML = `
                <div style="display: flex; gap: 10px; align-items: center;">
                    <input type="file" name="points_files" accept=".csv,.tsv,.txt,.xlsx"
                           style="flex: 1; padding: 8px; border: 2px solid #ddd; border-radius: 6px; font-size: 13px;">
                    <span style="color: #666; font-size: 12px;">Points #${pointsFileCount}</span>
                    <button type="button" onclick="this.parentElement.parentElement.remove()"
                            style="padding: 4px 8px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px;">✕</button>
                </div>
            `;
            container.appendChild(newEntry);
        }

        // Handle integrated form submission
        document.getElementById('integratedForm').addEventListener('submit', function(e) {
            const sooInputs = document.querySelectorAll('input[name="soo_files"]');
            let hasFile = false;
            sooInputs.forEach(input => {
                if (input.files && input.files.length > 0) hasFile = true;
            });

            if (!hasFile) {
                e.preventDefault();
                alert('Please select at least one SOO document');
                return;
            }

            // Show progress overlay
            progressOverlay.classList.add('active');
            document.querySelector('.progress-title').textContent = '🔗 Generating Integrated Form';
            document.querySelector('.progress-subtitle').textContent = 'Processing SOO documents...';
            startTime = Date.now();
            currentProgress = 0;
            progressBar.style.width = '0%';
            progressPercent.textContent = '0%';
            progressInterval = setInterval(updateProgress, 200);
            sessionStorage.setItem('formGenStartTime', startTime);
        });

// ==============================
// Results Page Functions  
// ==============================
        // Load and display feedback learning dashboard
        async function loadLearningDashboard() {
            try {
                const response = await fetch('/api/feedback/stats');
                const data = await response.json();

                const dashboard = document.getElementById('learningDashboard');

                const progressBarColor = data.learning_status.level === 'trained' ? '#22c55e' :
                                         data.learning_status.level === 'improving' ? '#3b82f6' : '#f59e0b';

                let systemsHtml = '';
                for (const [system, count] of Object.entries(data.by_system || {})) {
                    systemsHtml += `<span class="feedback-tag">${system}: ${count}</span>`;
                }

                let typesHtml = '';
                const typeEmoji = { positive: '👍', negative: '👎', suggestion: '💡', correction: '✏️' };
                for (const [type, count] of Object.entries(data.by_type || {})) {
                    typesHtml += `<span class="feedback-tag">${typeEmoji[type] || '📝'} ${type}: ${count}</span>`;
                }

                let recentHtml = '';
                if (data.recent_feedback && data.recent_feedback.length > 0) {
                    recentHtml = '<div class="recent-feedback"><strong>Recent Feedback:</strong><ul>';
                    for (const fb of data.recent_feedback.slice(0, 5)) {
                        const emoji = typeEmoji[fb.feedback_type] || '📝';
                        recentHtml += `<li>${emoji} <strong>[${fb.system_type}]</strong> ${fb.feedback_text}</li>`;
                    }
                    recentHtml += '</ul></div>';
                }

                dashboard.innerHTML = `
                    <div class="learning-stats">
                        <div class="learning-progress">
                            <div class="progress-header">
                                <span class="progress-label">Learning Progress</span>
                                <span class="progress-value">${data.learning_status.progress}%</span>
                            </div>
                            <div class="progress-bar-bg">
                                <div class="progress-bar-fill" style="width: ${data.learning_status.progress}%; background: ${progressBarColor};"></div>
                            </div>
                            <p class="progress-message">${data.learning_status.message}</p>
                        </div>

                        <div class="stats-grid">
                            <div class="stat-mini">
                                <span class="stat-mini-value">${data.total_feedback}</span>
                                <span class="stat-mini-label">Total Feedback</span>
                            </div>
                            <div class="stat-mini">
                                <span class="stat-mini-value">${data.recent_count}</span>
                                <span class="stat-mini-label">This Week</span>
                            </div>
                            <div class="stat-mini">
                                <span class="stat-mini-value">${Object.keys(data.by_system || {}).length}</span>
                                <span class="stat-mini-label">Systems Learned</span>
                            </div>
                        </div>

                        ${systemsHtml ? `<div class="feedback-tags"><strong>By System:</strong> ${systemsHtml}</div>` : ''}
                        ${typesHtml ? `<div class="feedback-tags"><strong>By Type:</strong> ${typesHtml}</div>` : ''}
                        ${recentHtml}

                        <div class="ai-context-preview" id="aiContextPreview"></div>
                    </div>
                `;

                // Load AI context for the first system
                if (Object.keys(data.by_system || {}).length > 0) {
                    const firstSystem = Object.keys(data.by_system)[0];
                    loadAIContext(firstSystem);
                }

            } catch (error) {
                console.error('Failed to load learning dashboard:', error);
                document.getElementById('learningDashboard').innerHTML =
                    '<p style="color: #666;">No feedback data yet. Submit feedback below to start improving AI generation!</p>';
            }
        }

        async function loadAIContext(systemType) {
            try {
                const response = await fetch(`/api/feedback/context?system_type=${encodeURIComponent(systemType)}`);
                const data = await response.json();

                const preview = document.getElementById('aiContextPreview');
                if (!preview) return;

                if (data.ai_context && data.ai_context.trim()) {
                    preview.innerHTML = `
                        <details class="ai-context-details">
                            <summary>🤖 AI Context for ${systemType} (Click to expand)</summary>
                            <pre class="ai-context-code">${escapeHtml(data.ai_context)}</pre>
                            <p class="ai-context-note">
                                <strong>This context is added to AI prompts</strong> when generating forms for ${systemType} systems,
                                helping the AI learn from your feedback and produce better check items.
                            </p>
                        </details>
                    `;
                } else {
                    preview.innerHTML = `
                        <p class="ai-context-empty">
                            💡 No feedback yet for ${systemType} systems. Submit feedback to help the AI learn!
                        </p>
                    `;
                }
            } catch (error) {
                console.error('Failed to load AI context:', error);
            }
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Load dashboard on page load
        loadLearningDashboard();

        // Feedback form handling
        let selectedFeedbackType = '';
        const feedbackForm = document.getElementById('feedbackForm');
        const feedbackSuccess = document.getElementById('feedbackSuccess');
        const typeButtons = document.querySelectorAll('.feedback-type-btn');

        typeButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                typeButtons.forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                selectedFeedbackType = btn.dataset.type;
            });
        });

        feedbackForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            if (!selectedFeedbackType) {
                alert('Please select a feedback type');
                return;
            }

            const feedbackText = document.getElementById('feedbackText').value.trim();
            if (!feedbackText) {
                alert('Please enter your feedback');
                return;
            }

            const submitBtn = document.getElementById('submitFeedback');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            try {
                const response = await fetch('/api/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        feedback_type: selectedFeedbackType,
                        system_type: document.getElementById('systemType').value || 'General',
                        system_name: document.getElementById('systemType').options[document.getElementById('systemType').selectedIndex]?.text || 'General',
                        form_type: 'ITC',
                        section_name: document.getElementById('sectionName').value,
                        feedback_text: feedbackText,
                        suggested_improvement: document.getElementById('suggestedImprovement').value
                    })
                });

                if (response.ok) {
                    feedbackSuccess.classList.add('show');
                    feedbackForm.reset();
                    typeButtons.forEach(b => b.classList.remove('selected'));
                    selectedFeedbackType = '';

                    setTimeout(() => {
                        feedbackSuccess.classList.remove('show');
                    }, 5000);
                } else {
                    throw new Error('Failed to submit feedback');
                }
            } catch (error) {
                alert('Failed to submit feedback. Please try again.');
                console.error(error);
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Submit Feedback';
            }
        });

