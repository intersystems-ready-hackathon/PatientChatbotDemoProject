FROM iris4h-aihub

ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"

COPY iris.cpf /usr/irissys/IRIS.cpf
# COPY iris.cpf /usr/irissys/mgr/IRIS.cpf
# COPY iris.cpf /dur/IRIS.cpf

COPY ./projects/CHATFHIR/SetupRequestBodies /tmp/SetupRequestBodies
COPY ./iris.script /opt/irisbuild/iris.script
COPY ./projects/CHATFHIR/fhirsampledata /opt/irisbuild/fhirsampledata
COPY ./projects/CHATFHIR/src /opt/irisbuild/src

ENV IRISNAMESPACE "CHATFHIR"
WORKDIR /home/irisowner/dev

RUN iris start IRIS \
    && iris session IRIS < /opt/irisbuild/iris.script\ 
    && iris stop IRIS quietly
