pipeline {
    agent any

    stages {
        stage('Prepare Environment') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'ALGORITHM', variable: 'ALGORITHM'),
                        string(credentialsId: 'ACCESS_TOKEN_EXPIRE', variable: 'ACCESS_TOKEN_EXPIRE')
                    ]) {
                        sh """
                        rm .env || true
                        echo "SECRET_KEY=${SECRET_KEY}" >> .env
                        echo "ALGORITHM=${ALGORITHM}" >> .env
                        """
                    }
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t \"bkslf-backend\" .'
            }
        }

        stage('Stop and Remove Existing Container') {
            steps {
                sh 'docker stop bkslf-backend || true'
                sh 'docker rm bkslf-backend || true'
            }
        }

        stage('Run New Container') {
            steps {
                sh 'docker run -v database:/app/database -d --restart always --name \"bkslf-backend\" -p 8404:8404 \"bkslf-backend\"'
            }
        }
    }
}
