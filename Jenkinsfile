pipeline {
    agent any

    stages {
        stage('Prepare Environment') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: 'BKSLF_ADMIN_USERNAME', variable: 'ADMIN_USERNAME'),
                        string(credentialsId: 'BKSLF_ADMIN_PASSWORD', variable: 'ADMIN_PASSWORD'),
                        string(credentialsId: 'BKSLF_ALGORITHM', variable: 'ALGORITHM'),
                        string(credentialsId: 'BKSLF_DATABASE_URL', variable: 'DATABASE_URL'),
                        string(credentialsId: 'BKSLF_SECRET_KEY', variable: 'SECRET_KEY')
                    ]) {
                        sh """
                        rm .env || true
                        echo "ADMIN_USERNAME=${ADMIN_USERNAME}" >> .env
                        echo "ADMIN_PASSWORD=${ADMIN_PASSWORD}" >> .env
                        echo "ALGORITHM=${ALGORITHM}" >> .env
                        echo "DATABASE_URL=${DATABASE_URL}" >> .env
                        echo "SECRET_KEY=${SECRET_KEY}" >> .env
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
                sh 'docker run -v bkslf_database:/app/database -d --restart always --name \"bkslf-backend\" -p 8404:8404 \"bkslf-backend\"'
            }
        }
    }
}
