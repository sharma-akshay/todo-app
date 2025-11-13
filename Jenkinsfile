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
                    osv-scanner --all > osv-report.json || true
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
    }

    /* ------------------------------------------------------------
       POST STEPS - ALWAYS KEEP REPORTS
    -------------------------------------------------------------*/
    post {
        always {
            archiveArtifacts artifacts: '*.json', allowEmptyArchive: true
            echo "Reports archived successfully."
        }
    }
}
