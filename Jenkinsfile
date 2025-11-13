pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
    }

    stages {

        /* ------------------------------------------------------------
           CHECKOUT CODE
        -------------------------------------------------------------*/
        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://github.com/sharma-akshay/todo-app.git'
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
