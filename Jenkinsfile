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
                    osv-scanner -r . --json > osv-report.json || true
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
                    echo "=== Running Trivy FS ==="
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
           BUILD & DEPLOY
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
                    echo "=== Deploying Using docker-compose ==="
                    docker-compose down || true
                    docker-compose up -d
                '''
            }
        }

        /* ------------------------------------------------------------
           ALWAYS RUN — GENERATE SUMMARY
        -------------------------------------------------------------*/
        stage('Generate Security Summary') {
            when { always() }
            steps {
                sh '''
                    echo "=== Generating Security Summary ==="
                    python3 tools/generate-security-summary.py
                '''
            }
        }
    }

    /* ------------------------------------------------------------
       POST ACTIONS
    -------------------------------------------------------------*/
    post {
        always {

            archiveArtifacts artifacts: '*.json, *.md, *.html', allowEmptyArchive: true

            script {
                def OUTDIR = "${SECURITY_REPORTS_ROOT}/${BUILD_NUMBER}"

                sh """
                    mkdir -p '${OUTDIR}'
                    cp -v *.json '${OUTDIR}'/ 2>/dev/null || true
                    cp -v *.md '${OUTDIR}'/ 2>/dev/null || true
                    cp -v *.html '${OUTDIR}'/ 2>/dev/null || true

                    cd '${OUTDIR}'

                    echo "<html><body><h2>Build ${BUILD_NUMBER} Reports</h2><ul>" > index.html

                    for f in *.json *.md *.html; do
                        if [ -f "\$f" ]; then
                            echo "<li><a href='\$f'>\$f</a></li>" >> index.html
                        fi
                    done

                    echo "</ul></body></html>" >> index.html
                """

                echo "Security Reports at → ${SECURITY_REPORTS_ROOT}/${BUILD_NUMBER}"
                echo "Accessible via Nginx: http://YOUR-IP/security-reports/${BUILD_NUMBER}/index.html"
            }
        }
    }
}
