pipeline {
  agent any

  stages {

    stage('Checkout Code') {
      steps {
        git credentialsId: 'github',
        git branch: 'master', url: 'https://github.com/sharma-akshay/todo-app.git'
      }
    }

    stage('Build Docker Images') {
      steps {
        sh 'docker-compose build'
      }
    }

    stage('Deploy') {
      steps {
        sh '''
          docker-compose down
          docker-compose up -d
        '''
      }
    }
  }
}
