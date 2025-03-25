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
      image: 'artifactory.cloud.cms.gov/docker-remote/chainguard/python:latest'
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

        stage('Python') {
            steps {
                sh 'python3 --version'
            }
        }

    }
}

