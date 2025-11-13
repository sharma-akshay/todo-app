pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin:/home/ubuntu/.local/share/pipx/venvs/checkov/bin"
        SECURITY_REPORTS_ROOT = "/var/lib/jenkins/security-reports"
    }

    stages {

        /* ------------------------------------------------------------
           CHECKOUT CODE
        -------------------------------------------------------------*/
        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/sharma-akshay/todo-app.git',
                    credentialsId: "${GIT_CREDENTIALS}"
            }
        }

        /* ------------------------------------------------------------
           DEVSECOPS SCANNERS
        -------------------------------------------------------------*/

        stage('Secret Scan - Gitleaks') {
            steps {
                sh '''
                    echo "=== Running Gitleaks ==="
                    gitleaks detect --source . \
                        --report-format json \
                        --report-path gitleaks-report.json || true
                '''
            }
        }

        stage('Static Code Analysis - Semgrep') {
            steps {
                sh '''
                    echo "=== Running Semgrep ==="
                    semgrep scan --config auto --json > semgrep-report.json || true
                '''
            }
        }

        stage('Dependency Vulnerability Scan - OSV-Scanner') {
            steps {
                sh '''
                    echo "=== Running OSV Scanner ==="
                    # fallback-safe OSV command
                    osv-scanner --json . > osv-report.json 2>/dev/null || true
                '''
            }
        }

        stage('Generate SBOM - Syft') {
            steps {
                sh '''
                    echo "=== Generating SBOM Using Syft ==="
                    syft dir:. -o json > sbom.json || true
                '''
            }
        }

        stage('Vulnerability Scan from SBOM - Grype') {
            steps {
                sh '''
                    echo "=== Running Grype on SBOM ==="
                    grype sbom:sbom.json -o json > grype-report.json || true
                '''
            }
        }

        stage('Filesystem Vulnerability Scan - Trivy FS') {
            steps {
                sh '''
                    echo "=== Running Trivy FS Scan ==="
                    trivy fs . --format json --output trivy-fs-report.json || true
                '''
            }
        }

        stage('IaC Scan - Checkov') {
            steps {
                sh '''
                    echo "=== Running Checkov ==="
                    checkov -d . -o json > checkov-report.json || true
                '''
            }
        }

        /* ------------------------------------------------------------
           DOCKER BUILD & DEPLOY (FRONTEND + BACKEND)
        -------------------------------------------------------------*/

        stage('Build Docker Images') {
            steps {
                sh '''
                    echo "=== Building Docker Images ==="
                    docker-compose build --no-cache
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    echo "=== Deploying Application ==="
                    docker-compose down || true
                    docker-compose up -d
                '''
            }
        }

        /* ------------------------------------------------------------
           GENERATE SECURITY SUMMARY
        -------------------------------------------------------------*/
        stage('Generate Security Summary') {
            steps {
                sh '''
                    echo "=== Generating Security Summary ==="
                    python3 tools/generate-security-summary.py || true
                '''
            }
        }
    }

    /* ------------------------------------------------------------
       POST STEPS - ALWAYS KEEP REPORTS
    -------------------------------------------------------------*/
    post {
        always {

            archiveArtifacts artifacts: '*.json, *.pretty.json, security-summary.md, security-dashboard.html', allowEmptyArchive: true
            echo "Reports archived successfully."

            script {
                def reportDir = "${SECURITY_REPORTS_ROOT}/${BUILD_NUMBER}"

                sh """
                    echo "Creating report dir: ${reportDir}"
                    sudo mkdir -p "${reportDir}"
                    sudo chmod 777 "${reportDir}"

                    # Copy JSON + HTML + MD reports
                    cp -v *.json "${reportDir}/" 2>/dev/null || true
                    cp -v *.pretty.json "${reportDir}/" 2>/dev/null || true
                    cp -v security-summary.md "${reportDir}/" 2>/dev/null || true
                    cp -v security-dashboard.html "${reportDir}/" 2>/dev/null || true

                    # Build HTML index
                    cd "${reportDir}"
                    echo "<html><head><title>Security Reports - Build ${BUILD_NUMBER}</title></head><body><h2>Security Reports - Build ${BUILD_NUMBER}</h2><ul>" > index.html

                    for file in *; do
                        if [ -f "\$file" ]; then
                            echo "<li><a href='\$file'>\$file</a></li>" >> index.html
                        fi
                    done

                    echo "</ul><p>Generated: $(date -u)</p></body></html>" >> index.html

                    echo "Saved reports to: ${reportDir}"
                """

                echo "Security reports available at: ${SECURITY_REPORTS_ROOT}/${BUILD_NUMBER}"
            }
        }
    }
}
