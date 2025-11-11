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
        sh 'docker compose build'
      }
    }

    stage('Deploy Application') {
      steps {
        sh 'docker compose up -d'
      }
    }
  }
}
