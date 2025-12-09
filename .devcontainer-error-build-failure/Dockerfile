FROM ubuntu:22.04

# This Dockerfile will fail during build due to non-existent package

RUN apt-get update

# Attempt to install a package that doesn't exist - will cause build failure
RUN apt-get install -y this-package-definitely-does-not-exist-xyz123

# This line will never be reached
RUN echo "Build succeeded"
