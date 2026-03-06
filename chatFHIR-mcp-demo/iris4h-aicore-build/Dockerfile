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


# Copy kit
COPY IRISHealth-2026.2.0AI.124.0-dockerubuntux64.tar.gz .
COPY keys/YKAS011IRISforHealthwithFHIRBuilder_Adv.Server_InterSystemsIRISAdvancedServer_Enterprise_256_ContainerUbuntu-x64_11-30-2026.ISCkey /usr/irissys/mgr/iris.key

# Install IRIS with Apache web server0
RUN mkdir -p /tmp/extract && \
    tar -xzf IRISHealth-2026.2.0AI.124.0-dockerubuntux64.tar.gz -C /tmp/extract && \
    cd /tmp/extract/IRISHealth-*-dockerubuntux64 && \
    ISC_PACKAGE_INSTANCENAME="IRIS" \
    ISC_PACKAGE_INSTALLDIR="/usr/irissys" \
    ISC_PACKAGE_PLATFORM="dockerubuntux64" \
    ISC_PACKAGE_INITIAL_SECURITY="Normal" \
    ISC_PACKAGE_USER_PASSWORD="SYS" \
    ISC_PACKAGE_CSPSYSTEM_PASSWORD="SYS" \
    ./irisinstall_silent && \
    cd / && \
    rm -rf /tmp/iris_install /tmp/extract

# Add Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install iris_llm Python dependencies and the wheel
RUN pip3 install --break-system-packages pydantic langchain-core
# RUN ls /usr/irissys/dev/python/
RUN pip3 install --break-system-packages /usr/irissys/dev/python/iris_llm-*.whl

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
WORKDIR /usr/irissys

EXPOSE 1972 52773

ENTRYPOINT ["/usr/irissys/iris-main.sh"]