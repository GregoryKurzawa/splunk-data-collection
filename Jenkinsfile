pipeline {

    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: jnlp
      image: jenkins/inbound-agent
      resources:
        limits:
          memory: 512Mi
          cpu: 500m
        requests:
          memory: 256Mi
          cpu: 250m
    - name: build
      image: 'python:3.14.0a6-alpine3.21'
      command: ["cat"]
      tty: true
'''
        }
    }
    
    stages {

        stage('Hello') {
            steps {
                echo 'Hello World'
            }
        }

        stage('Where') {
            steps {
                where python3
            }
        }

        stage('Python') {
            steps {
                sh 'python3 --version'
            }
        }

    }
}

