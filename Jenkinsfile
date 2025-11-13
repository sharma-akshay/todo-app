pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        SECURITY_BASE_DIR = "/var/lib/jenkins/security-reports"
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
                    echo -e "\\033[1;34m=== Running Gitleaks ===\\033[0m"
                    gitleaks detect --source . --report-format json --report-path gitleaks-report.json || true
                '''
            }
        }

        stage('Static Code Analysis - Semgrep') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Running Semgrep ===\\033[0m"
                    semgrep scan --config auto --json > semgrep-report.json || true
                '''
            }
        }

        stage('Dependency Scan - OSV-Scanner') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Running OSV Scanner ===\\033[0m"
                    osv-scanner --json > osv-report.json || true
                '''
            }
        }

        stage('Generate SBOM - Syft') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Generating SBOM Using Syft ===\\033[0m"
                    syft dir:. -o json > sbom.json || true
                '''
            }
        }

        stage('SBOM Vulnerability Scan - Grype') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Running Grype ===\\033[0m"
                    grype sbom:sbom.json -o json > grype-report.json || true
                '''
            }
        }

        stage('Filesystem Scan - Trivy') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Running Trivy FS Scan ===\\033[0m"
                    trivy fs . --format json --output trivy-fs-report.json || true
                '''
            }
        }

        stage('IaC Scan - Checkov') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Running Checkov ===\\033[0m"
                    checkov -d . -o json > checkov-report.json || true
                '''
            }
        }

        /* ------------------------------------------------------------
           DOCKER BUILD & DEPLOY
        -------------------------------------------------------------*/

        stage('Build Docker Images') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Building Docker Images ===\\033[0m"
                    docker-compose build --no-cache
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    echo -e "\\033[1;34m=== Deploying Application ===\\033[0m"
                    docker-compose down || true
                    docker-compose up -d
                '''
            }
        }
    }

    /* ------------------------------------------------------------
       POST ACTIONS
    -------------------------------------------------------------*/
    post {
        always {
            /* Archive JSON in Jenkins UI */
            echo "\033[1;36mArchiving JSON reports...\033[0m"
            archiveArtifacts artifacts: '*.json', allowEmptyArchive: true

            /* Copy to per-build folder (no sudo) */
            script {
                def buildDir = "${SECURITY_BASE_DIR}/${env.BUILD_NUMBER}"

                sh """
                    mkdir -p ${SECURITY_BASE_DIR}
                    mkdir -p ${buildDir}

                    cp -v *.json ${buildDir}/ || true
                """

                echo "\033[1;32mReports saved to: ${buildDir}\033[0m"
            }

            /* SEVERITY SUMMARY (console output) */
            script {
                sh """
                    echo "\\n\\033[1;33m================ SECURITY SEVERITY SUMMARY ================\\033[0m"

                    CRIT=\$(grep -R \"CRITICAL\" -n ./*.json | wc -l)
                    HIGH=\$(grep -R \"HIGH\" -n ./*.json | wc -l)
                    MED=\$(grep -R \"MEDIUM\" -n ./*.json | wc -l)
                    LOW=\$(grep -R \"LOW\" -n ./*.json | wc -l)

                    echo -e "\\033[1;31mCRITICAL: \$CRIT\\033[0m"
                    echo -e "\\033[1;31mHIGH:     \$HIGH\\033[0m"
                    echo -e "\\033[1;33mMEDIUM:   \$MED\\033[0m"
                    echo -e "\\033[1;32mLOW:      \$LOW\\033[0m"

                    if [ \$CRIT -gt 0 ]; then
                        echo -e "\\033[1;31mBUILD FAILED – CRITICAL VULNERABILITIES FOUND\\033[0m"
                        exit 1
                    fi

                    echo -e "\\033[1;32mNo blocking vulnerabilities.\\033[0m"
                """
            }

            /* Cleanup old folders — keep last 20 builds */
            script {
                sh """
                    ls -1 ${SECURITY_BASE_DIR} | sort -n | head -n -20 | xargs -I {} rm -rf ${SECURITY_BASE_DIR}/{} || true
                """
            }
        }
    }
}
