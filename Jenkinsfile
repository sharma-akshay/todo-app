pipeline {
  agent any

  stages {

    stage('Pull Code') {
      steps {
        checkout scm
      }
    }

    stage('Build Docker Images') {
      steps {
        sh 'docker compose -f docker-compose.yml build'
      }
    }

    stage('Deploy Application') {
      steps {
        sh 'docker compose -f docker-compose.yml up -d'
      }
    }
  }
}
