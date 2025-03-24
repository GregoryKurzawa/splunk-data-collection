pipeline {

    agent {
        kubernetes {
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: build
      image: 'hub.docker.com/python/3.14.0a6-alpine3.21'
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
                sh 'python --version'
            }
        }

    }
}

