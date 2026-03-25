FROM ubuntu:24.04

# Install dependencies including apache2 to satisfy installer check
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    apache2 \
    apache2-utils \
    sudo \
    curl \
    python3 \
    python3-pip \
    build-essential \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create irisowner user
RUN useradd -m -s /bin/bash irisowner

# Set up installation directory
WORKDIR /tmp/iris_install

ARG VERSION=IRISHealth-2026.2.0AI.137.0-dockerubuntux64
# Copy kit
COPY ${VERSION}.tar.gz .
COPY keys/YKD41ISCDevelopment_InterSystemsIRISAdvancedServer_Enterprise_1024_ContainerUbuntu-x64_11-30-2026.key /usr/irissys/mgr/iris.key

# Install IRIS with Apache web server0
RUN mkdir -p /tmp/extract && \
    tar -xzf ${VERSION}.tar.gz -C /tmp/extract && \
    cd /tmp/extract/${VERSION} && \
    ISC_PACKAGE_INSTANCENAME="IRIS" \
    ISC_PACKAGE_INSTALLDIR="/usr/irissys" \
    ISC_PACKAGE_PLATFORM="dockerubuntux64" \
    ISC_PACKAGE_INITIAL_SECURITY="Normal" \
    ISC_PACKAGE_USER_PASSWORD="SYS" \
    ISC_PACKAGE_CSPSYSTEM_PASSWORD="SYS" \
    ./irisinstall_silent && \
    cd / && \
    rm -rf /tmp/iris_install /tmp/extract


# Configure Apache with CSP Gateway
RUN /usr/irissys/bin/cspagent_install.sh --instancename IRIS --host 127.0.0.1 --port 1972 --apachebin /usr/sbin/apache2 --apachectl /usr/sbin/apachectl || true

# Create startup script that starts both IRIS and Apache
RUN echo '#!/bin/bash' > /usr/irissys/iris-main.sh && \
    echo 'iris start IRIS' >> /usr/irissys/iris-main.sh && \
    echo 'apachectl start || true' >> /usr/irissys/iris-main.sh && \
    echo 'trap "iris stop IRIS quietly; apachectl stop" SIGTERM SIGINT' >> /usr/irissys/iris-main.sh && \
    echo 'tail -f /usr/irissys/mgr/messages.log &' >> /usr/irissys/iris-main.sh && \
    echo 'wait' >> /usr/irissys/iris-main.sh && \
    chmod +x /usr/irissys/iris-main.sh

ENV PATH="/usr/irissys/bin:$PATH"
WORKDIR /home/irisowner

EXPOSE 1972 52773

ENTRYPOINT ["/usr/irissys/iris-main.sh"]

