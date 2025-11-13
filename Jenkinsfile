pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin:/home/ubuntu/.local/share/pipx/venvs/checkov/bin"
        SECURITY_REPORTS_DIR = "${env.JENKINS_HOME ?: '/var/lib/jenkins'}/security-reports"
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

        stage('Dependency Vulnerability Scan - OSV-Scanner') {
            steps {
                sh '''
                    echo "=== Running OSV Scanner ==="
                    # Fallback in case --all not supported
                    osv-scanner --all > osv-report.json 2>/dev/null || osv-scanner > osv-report.json 2>/dev/null || true
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
                    trivy fs . \
                        --format json \
                        --output trivy-fs-report.json || true
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
                    docker-compose down
                    docker-compose up -d
                '''
            }
        }

        /* ------------------------------------------------------------
           GENERATE SECURITY SUMMARY (MOVED INSIDE stages{})
        -------------------------------------------------------------*/
        stage('Generate Security Summary') {
            steps {
                sh '''
                    echo "=== Generating Security Summary ==="
                    python3 tools/generate-security-summary.py
                '''
            }
        }
    }

    /* ------------------------------------------------------------
       POST STEPS - ALWAYS KEEP REPORTS
    -------------------------------------------------------------*/
    post {
        always {
            archiveArtifacts artifacts: '*.json, security-summary.md', allowEmptyArchive: true
            echo "Reports archived successfully."

            script {
                def outDir = "${env.SECURITY_REPORTS_DIR}/${env.BUILD_NUMBER}"
                sh """
                    set -e
                    mkdir -p '${outDir}'
                    cp -v *.json '${outDir}/' 2>/dev/null || true

                    if [ -d '${env.WORKSPACE}/archive' ]; then
                      cp -v ${env.WORKSPACE}/archive/*.json '${outDir}/' 2>/dev/null || true
                    fi

                    cd '${outDir}'
                    echo "<html><head><meta charset=\\"utf-8\\"><title>Security Reports - Build ${env.BUILD_NUMBER}</title></head><body><h2>Security Reports - Build ${env.BUILD_NUMBER}</h2><ul>" > index.html
                    for f in *.json; do
                      [ -f "\$f" ] || continue
                      echo "<li><a href='\$f'>\$f</a></li>" >> index.html
                    done
                    echo "</ul><p>Generated: \$(date -u)</p></body></html>" >> index.html

                    if command -v jq >/dev/null 2>&1; then
                      for f in *.json; do
                        [ -f "\$f" ] || continue
                        jq '.' "\$f" > "\${f}.pretty.json" || cp "\$f" "\${f}.pretty.json"
                      done
                    fi

                    echo "Saved security reports to: ${outDir}"
                """

                echo "Security reports copied to: ${env.SECURITY_REPORTS_DIR}/${env.BUILD_NUMBER}"
            }
        }
    }
}
