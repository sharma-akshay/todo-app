pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin:/home/ubuntu/.local/share/pipx/venvs/checkov/bin"
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
                    echo "\\033[1;34m=== Running Gitleaks ===\\033[0m"
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
                    echo "\\033[1;34m=== Running Semgrep ===\\033[0m"
                    semgrep scan \
                        --config auto \
                        --json > semgrep-report.json || true
                '''
            }
        }

        stage('Dependency Vulnerability Scan - OSV-Scanner') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Running OSV Scanner ===\\033[0m"
                    # safer: skip invalid flags
                    osv-scanner -r . --json > osv-report.json 2>/dev/null || true
                '''
            }
        }

        stage('Generate SBOM - Syft') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Generating SBOM Using Syft ===\\033[0m"
                    syft dir:. -o json > sbom.json || true
                '''
            }
        }

        stage('Vulnerability Scan from SBOM - Grype') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Running Grype ===\\033[0m"
                    grype sbom:sbom.json -o json > grype-report.json || true
                '''
            }
        }

        stage('Filesystem Vulnerability Scan - Trivy FS') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Running Trivy FS Scan ===\\033[0m"
                    trivy fs . \
                        --format json \
                        --output trivy-fs-report.json || true
                '''
            }
        }

        stage('IaC Scan - Checkov') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Running Checkov ===\\033[0m"
                    checkov -d . -o json > checkov-report.json || true
                '''
            }
        }

        /* ------------------------------------------------------------
           BUILD BACKEND + FRONTEND IMAGES (fixed)
        -------------------------------------------------------------*/
        stage('Build Docker Images') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Building Docker Images ===\\033[0m"

                    # Build Angular dist
                    cd frontend
                    npm install
                    npm run build || true
                    cd ..

                    # Copy dist into nginx image (YOUR actual image)
                    docker-compose build --no-cache
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    echo "\\033[1;34m=== Deploying Application ===\\033[0m"
                    docker-compose down || true
                    docker-compose up -d --build
                '''
            }
        }

        /* ------------------------------------------------------------
           SECURITY SUMMARY (NO HTML)
        -------------------------------------------------------------*/
        stage('Generate Security Summary') {
            steps {
                sh '''
                    echo "\\033[1;35m=== Building Security Summary ===\\033[0m"

                    python3 tools/generate-security-summary.py \
                        --no-html \
                        --output security-summary.md || true

                    echo "\\033[1;32mSummary created: security-summary.md\\033[0m"
                '''
            }
        }
    }

    /* ------------------------------------------------------------
       POST ACTIONS
    -------------------------------------------------------------*/
    post {
        always {

            echo "\033[1;36mArchiving JSON reports...\033[0m"
            archiveArtifacts artifacts: '*.json, *.md', allowEmptyArchive: true

            echo "\033[1;32mReports archived successfully.\033[0m"

            /* === COLORIZED SEVERITY OUTPUT TO CONSOLE === */
            script {
                sh '''
                    echo ""
                    echo "\\033[1;33m================ SECURITY SEVERITY SUMMARY ================\\033[0m"

                    CRIT=$(grep -R "\"severity\": \"CRITICAL\"" -n . | wc -l || true)
                    HIGH=$(grep -R "\"severity\": \"HIGH\"" -n . | wc -l || true)
                    MED=$(grep -R "\"severity\": \"MEDIUM\"" -n . | wc -l || true)
                    LOW=$(grep -R "\"severity\": \"LOW\"" -n . | wc -l || true)

                    echo "\\033[1;31mCRITICAL: $CRIT\\033[0m"
                    echo "\\033[1;31mHIGH:     $HIGH\\033[0m"
                    echo "\\033[1;33mMEDIUM:   $MED\\033[0m"
                    echo "\\033[1;32mLOW:      $LOW\\033[0m"

                    if [ "$CRIT" -gt 0 ]; then
                        echo "\\033[1;41mBUILD FAILED: Critical vulnerabilities detected!\\033[0m"
                        exit 1
                    fi

                    if [ "$HIGH" -gt 10 ]; then
                        echo "\\033[1;41mBUILD FAILED: Too many high vulnerabilities (>10)!\\033[0m"
                        exit 1
                    fi

                    echo "\\033[1;32mNo blocking vulnerabilities.\\033[0m"
                '''
            }
        }
    }
}
