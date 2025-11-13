pipeline {
    agent any

    environment {
        GIT_CREDENTIALS = "github-token"
        PATH = "/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/home/ubuntu/.local/bin:/home/ubuntu/.local/share/pipx/venvs/checkov/bin"
        // SECURITY_REPORTS_DIR will be resolved on the Jenkins master/agent at runtime
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
                    # If your osv-scanner doesn't like --all, try default invocation fallback
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
           SEVERITY GATE (fail on CRITICAL)
           - examines known JSON outputs for CRITICAL severity and fails the build
        -------------------------------------------------------------*/
        stage('Severity Gate - Fail on CRITICAL') {
            steps {
                sh '''
                  echo "=== Running Severity Gate (fail on CRITICAL) ==="
                  # Look for strings "CRITICAL" or "critical" in common report files.
                  # This is conservative — adjust as needed to match each tool's schema.
                  found=0
                  files="trivy-fs-report.json grype-report.json osv-report.json semgrep-report.json checkov-report.json gitleaks-report.json"
                  for f in $files; do
                    if [ -f "$f" ]; then
                      if jq -e '.. | objects | select(.Severity?=="CRITICAL" or .severity?=="CRITICAL" or .severity?=="critical")' "$f" >/dev/null 2>&1; then
                        echo "CRITICAL severity found in $f"
                        found=1
                      fi
                      # semgrep's severity field can be in 'extra' -> 'severity' or rule-level strings
                      if jq -e '.results[]?.extra?.severity? | select(.=="CRITICAL" or .=="HIGH")' "$f" >/dev/null 2>&1; then
                        echo "HIGH/CRITICAL style finding in semgrep-like file $f"
                        # treat HIGH in semgrep as non-blocking by default — uncomment next line to block on HIGH
                        # found=1
                      fi
                      # gitleaks doesn't use severity - if you want to block on any leak, check length
                      if [ "$f" = "gitleaks-report.json" ]; then
                        n=$(jq '. | length' "$f" 2>/dev/null || echo 0)
                        if [ "$n" -gt 0 ]; then
                          echo "Secrets found by gitleaks: $n (treating as CRITICAL)"
                          found=1
                        fi
                      fi
                    fi
                  done

                  if [ "$found" -eq 1 ]; then
                    echo "Blocking pipeline: critical findings detected."
                    exit 1
                  fi

                  echo "Severity gate passed (no CRITICAL findings)."
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

        stage('SBOM + Image Scans (again after build)') {
            steps {
                sh '''
                    echo "=== Generating SBOM for images and scanning images ==="
                    # generate SBOM from image if needed
                    # try frontend and backend images created by docker-compose
                    # adapt image names if your compose uses different tags
                    syft docker:todo-app-deploy_frontend:latest -o json > sbom-frontend.json 2>/dev/null || true
                    syft docker:todo-app-deploy_backend:latest -o json > sbom-backend.json 2>/dev/null || true
                    grype docker:todo-app-deploy_frontend:latest -o json > grype-frontend.json 2>/dev/null || true
                    grype docker:todo-app-deploy_backend:latest -o json > grype-backend.json 2>/dev/null || true
                    trivy image --ignore-unfixed --format json -o trivy-frontend.json todo-app-deploy_frontend:latest || true
                    trivy image --ignore-unfixed --format json -o trivy-backend.json todo-app-deploy_backend:latest || true
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
           Generate Summary & Simple Dashboard (placed inside stages)
        -------------------------------------------------------------*/
        stage('Generate Security Summary') {
            steps {
                sh '''
                    echo "=== Generating Security Summary ==="
                    # create tools directory tools/generate-security-summary.py in repo and ensure executable
                    python3 tools/generate-security-summary.py || true
                '''
            }
        }

    } // end stages

    /* ------------------------------------------------------------
       POST STEPS - ALWAYS KEEP REPORTS
    -------------------------------------------------------------*/
    post {
        always {
            // keep Jenkins archive as before
            archiveArtifacts artifacts: '*.json, security-summary.md, security-dashboard.html', allowEmptyArchive: true
            echo "Reports archived successfully."

            // Copy reports to a persistent security-reports folder and create index
            script {
                def outDir = "${env.SECURITY_REPORTS_DIR}/${env.BUILD_NUMBER}"
                sh """
                    set -e
                    mkdir -p '${outDir}'
                    # copy any json reports (avoid overwriting unrelated files)
                    cp -v *.json '${outDir}/' 2>/dev/null || true

                    # also copy archived artifacts if present (optional)
                    if [ -d '${env.WORKSPACE}/archive' ]; then
                      cp -v ${env.WORKSPACE}/archive/*.json '${outDir}/' 2>/dev/null || true
                    fi

                    # copy generated summary and dashboard
                    cp -v security-summary.md security-dashboard.html '${outDir}/' 2>/dev/null || true

                    # generate a simple index.html with links to the JSON files and dashboard
                    cd '${outDir}'
                    echo "<html><head><meta charset=\\"utf-8\\"><title>Security Reports - Build ${env.BUILD_NUMBER}</title></head><body><h2>Security Reports - Build ${env.BUILD_NUMBER}</h2><ul>" > index.html
                    for f in *.json *.md *.html; do
                      [ -f \"$f\" ] || continue
                      echo "<li><a href='\$f'>\$f</a></li>" >> index.html
                    done
                    echo "</ul><p>Generated: \$(date -u)</p></body></html>" >> index.html

                    # pretty print any json files for human-readability (jq if present)
                    if command -v jq >/dev/null 2>&1; then
                      for f in *.json; do
                        [ -f \"$f\" ] || continue
                        jq '.' \"$f\" > \"${f}.pretty.json\" || cp \"$f\" \"${f}.pretty.json\"
                      done
                    fi

                    echo "Saved security reports to: ${outDir}"
                """
                // echo path for user convenience
                echo "Security reports copied to: ${env.SECURITY_REPORTS_DIR}/${env.BUILD_NUMBER}"
            }
        }
    }
}
