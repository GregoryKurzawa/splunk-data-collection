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
      image: maven:3.8.5-openjdk-11
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
                sh 'python3 test.py'
            }
        }

    }
}

