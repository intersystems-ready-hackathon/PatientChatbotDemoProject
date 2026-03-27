FROM i4h-aihub-140

ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"

COPY iris.cpf /usr/irissys/IRIS.cpf
# COPY iris.cpf /usr/irissys/mgr/IRIS.cpf
# COPY iris.cpf /dur/IRIS.cpf
WORKDIR /home/irisowner/dev


COPY ./iris.script /opt/irisbuild/iris.script
COPY ./roleSetup.script /opt/irisbuild/roleSetup.script
COPY ./fhirsampledata/patients /tmp/fhirdata
COPY ./projects .

ENV IRISNAMESPACE "READYAI"
WORKDIR /home/irisowner/dev

RUN iris start IRIS \
    && iris session IRIS < /opt/irisbuild/iris.script\ 
    && iris session IRIS < /opt/irisbuild/roleSetup.script \
    && iris stop IRIS quietly
