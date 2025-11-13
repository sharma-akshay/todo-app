pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin:/home/ubuntu/.local/share/pipx/venvs/checkov/bin"
        SECURITY_REPORTS_BASE = "/var/lib/jenkins/security-reports"
    }

    stages {

        /* ------------------------------------------------------------
           1. CHECKOUT CODE
        -------------------------------------------------------------*/
        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/sharma-akshay/todo-app.git',
                    credentialsId: "${GIT_CREDENTIALS}"
            }
        }

        /* ------------------------------------------------------------
           2. DEVSECOPS SCANNERS
        -------------------------------------------------------------*/

        stage('Secret Scan - Gitleaks') {
            steps {
                sh '''
                    echo "=== Running Gitleaks ==="
                    gitleaks detect \
                        --source . \
                        --report-format json \
                        --report-path gitleaks-report.json || true
                '''
            }
        }

        stage('Static Code Analysis - Semgrep') {
            steps {
                sh '''
                    echo "=== Running Semgrep ==="
                    semgrep scan \
                        --config auto \
                        --json > semgrep-report.json || true
                '''
            }
        }

        stage('Dependency Scan - OSV Scanner') {
            steps {
                sh '''
                    echo "=== Running OSV Scanner ==="
                    # Fix: OSV produces invalid output sometimes → wrap safely
                    osv-scanner --json > osv-raw.txt 2>/dev/null || true

                    # Fix JSON: replace first invalid numeric literal if needed
                    sed 's/NaN/"NaN"/g' osv-raw.txt > osv-report.json || cp osv-raw.txt osv-report.json
                '''
            }
        }

        stage('Generate SBOM - Syft') {
            steps {
                sh '''
                    syft dir:. -o json > sbom.json || true
                '''
            }
        }

        /* ------------ FRONTEND + BACKEND SCANS ---------------- */

        stage('Backend SBOM + Grype + Trivy') {
            steps {
                sh '''
                    echo "=== Backend: SBOM ==="
                    syft backend -o json > sbom-backend.json || true

                    echo "=== Backend: Grype ==="
                    grype dir:backend -o json > grype-backend.json || true

                    echo "=== Backend: Trivy ==="
                    trivy fs backend --format json --output trivy-backend.json || true
                '''
            }
        }

        stage('Frontend SBOM + Grype + Trivy') {
            steps {
                sh '''
                    echo "=== Frontend: SBOM ==="
                    syft frontend -o json > sbom-frontend.json || true

                    echo "=== Frontend: Grype ==="
                    grype dir:frontend -o json > grype-frontend.json || true

                    echo "=== Frontend: Trivy ==="
                    trivy fs frontend --format json --output trivy-frontend.json || true
                '''
            }
        }

        stage('Filesystem Scan - Trivy FS') {
            steps {
                sh '''
                    trivy fs . --format json --output trivy-fs-report.json || true
                '''
            }
        }

        stage('IaC Scan - Checkov') {
            steps {
                sh '''
                    checkov -d . -o json > checkov-report.json || true
                '''
            }
        }

        /* ------------------------------------------------------------
           3. SEVERITY GATE  (FAIL PIPELINE ON CRITICAL)
        -------------------------------------------------------------*/
        stage('Severity Gate') {
            steps {
                script {
                    def criticals = sh(
                        script: "jq '.. | objects | select(.Severity?==\"CRITICAL\")' *.json | wc -l",
                        returnStdout: true
                    ).trim()

                    echo "Critical vulnerabilities found: ${criticals}"

                    if (criticals.toInteger() > 0) {
                        error "❌ Critical vulnerabilities detected. Failing the build."
                    }
                }
            }
        }

        /* ------------------------------------------------------------
           4. DOCKER BUILD & DEPLOY
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
                    docker-compose down
                    docker-compose up -d
                '''
            }
        }

        /* ------------------------------------------------------------
           5. GENERATE SECURITY SUMMARY
        -------------------------------------------------------------*/
        stage('Generate Security Summary') {
            steps {
                sh '''
                    mkdir -p tools || true
                    echo "=== Generating Security Summary ==="
                    python3 tools/generate-security-summary.py
                '''
            }
        }
    } // stages end

    /* ------------------------------------------------------------
       6. POST – ARCHIVE & COPY TO NGINX
    -------------------------------------------------------------*/
    post {
        always {
            archiveArtifacts artifacts: '*.json, *.pretty.json, security-summary.md, security-dashboard.html', allowEmptyArchive: true

            script {
                def REPORT_DIR = "${SECURITY_REPORTS_BASE}/${BUILD_NUMBER}"

                // Ensure Jenkins user can write
                sh "sudo mkdir -p ${SECURITY_REPORTS_BASE}"
                sh "sudo chmod -R 777 ${SECURITY_REPORTS_BASE}"

                sh '''
                    set -e
                    BUILD_DIR="${SECURITY_REPORTS_BASE}/${BUILD_NUMBER}"
                    sudo mkdir -p "$BUILD_DIR"
                    sudo cp -v *.json *.pretty.json security-summary.md security-dashboard.html "$BUILD_DIR" 2>/dev/null || true
                    sudo cp -v index.html "$BUILD_DIR" 2>/dev/null || true
                '''

                echo "Security reports available at: http://http://54.210.178.113/security-reports/${BUILD_NUMBER}/index.html"
            }
        }
    }
}
