pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin:/home/ubuntu/.local/share/pipx/venvs/checkov/bin"

        // 🔥 Create folders for readable reports
        REPORT_DIR = "security-reports"
    }

    stages {

        /* ------------------------------------------------------------
           INIT WORKSPACE
        -------------------------------------------------------------*/
        stage('Init Workspace') {
            steps {
                sh '''
                    echo "=== Preparing report directories ==="
                    rm -rf ${REPORT_DIR}
                    mkdir -p ${REPORT_DIR}/gitleaks
                    mkdir -p ${REPORT_DIR}/semgrep
                    mkdir -p ${REPORT_DIR}/osv
                    mkdir -p ${REPORT_DIR}/sbom
                    mkdir -p ${REPORT_DIR}/grype
                    mkdir -p ${REPORT_DIR}/trivy
                    mkdir -p ${REPORT_DIR}/checkov
                '''
            }
        }

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
                        --report-path ${REPORT_DIR}/gitleaks/gitleaks.json || true
                '''
            }
        }

        stage('Static Code Analysis - Semgrep') {
            steps {
                sh '''
                    echo "=== Running Semgrep ==="
                    semgrep scan --config auto --json > ${REPORT_DIR}/semgrep/semgrep.json || true
                '''
            }
        }

        stage('Dependency Vulnerability Scan - OSV-Scanner') {
            steps {
                sh '''
                    echo "=== Running OSV Scanner ==="
                    osv-scanner -r . --json > ${REPORT_DIR}/osv/osv.json || true
                '''
            }
        }

        stage('Generate SBOM - Syft') {
            steps {
                sh '''
                    echo "=== Generating SBOM Using Syft ==="
                    syft dir:. -o json > ${REPORT_DIR}/sbom/sbom.json || true
                '''
            }
        }

        stage('Vulnerability Scan from SBOM - Grype') {
            steps {
                sh '''
                    echo "=== Running Grype ==="
                    grype sbom:${REPORT_DIR}/sbom/sbom.json -o json > ${REPORT_DIR}/grype/grype.json || true
                '''
            }
        }

        stage('Filesystem Vulnerability Scan - Trivy FS') {
            steps {
                sh '''
                    echo "=== Running Trivy FS Scan ==="
                    trivy fs . \
                        --format json \
                        --output ${REPORT_DIR}/trivy/trivy-fs.json || true
                '''
            }
        }

        stage('IaC Scan - Checkov') {
            steps {
                sh '''
                    echo "=== Running Checkov ==="
                    checkov -d . -o json > ${REPORT_DIR}/checkov/checkov.json || true
                '''
            }
        }

        /* ------------------------------------------------------------
           🔥 REPORT ENHANCEMENT STAGE (HTML + SUMMARY)
        -------------------------------------------------------------*/
        stage('Enhance Reports (HTML + Summary)') {
            steps {
                sh '''
                    echo "=== Generating user-friendly HTML reports ==="

                    # Create HTML versions for easier reading
                    jq '.' ${REPORT_DIR}/semgrep/semgrep.json > ${REPORT_DIR}/semgrep/semgrep.html
                    jq '.' ${REPORT_DIR}/osv/osv.json > ${REPORT_DIR}/osv/osv.html
                    jq '.' ${REPORT_DIR}/grype/grype.json > ${REPORT_DIR}/grype/grype.html
                    jq '.' ${REPORT_DIR}/trivy/trivy-fs.json > ${REPORT_DIR}/trivy/trivy-fs.html
                    jq '.' ${REPORT_DIR}/checkov/checkov.json > ${REPORT_DIR}/checkov/checkov.html

                    # 🔥 Simple severity summary
                    echo "=== Vulnerability Summary ==="
                    echo "Semgrep findings:" 
                    jq '.results | length' ${REPORT_DIR}/semgrep/semgrep.json || true

                    echo "OSV Vulnerabilities:" 
                    jq '.results | length' ${REPORT_DIR}/osv/osv.json || true

                    echo "Grype image vulns:" 
                    jq '.matches | length' ${REPORT_DIR}/grype/grype.json || true

                    echo "Trivy FS issues:" 
                    jq '.Results[].Vulnerabilities | length' ${REPORT_DIR}/trivy/trivy-fs.json || true

                    echo "Checkov IaC findings:" 
                    jq '.summary.failed' ${REPORT_DIR}/checkov/checkov.json || true
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
       POST STEPS - ENHANCED REPORT ARCHIVING
    -------------------------------------------------------------*/
    post {
        always {
            archiveArtifacts artifacts: '${REPORT_DIR}/**', allowEmptyArchive: true
            echo "🔥 Enhanced reports archived successfully in organized folders."
        }
    }
}
