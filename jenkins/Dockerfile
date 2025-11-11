FROM jenkins/jenkins:lts as base

USER root

# Install Docker CLI
RUN apt-get update && \
    apt-get install -y docker.io && \
    apt-get clean

# Install Docker Compose v2
RUN mkdir -p /usr/lib/docker/cli-plugins && \
    curl -SL https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-linux-x86_64 \
    -o /usr/lib/docker/cli-plugins/docker-compose && \
    chmod +x /usr/lib/docker/cli-plugins/docker-compose

USER jenkins
