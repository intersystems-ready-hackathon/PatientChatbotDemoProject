FROM docker.iscinternal.com/docker-intersystems/intersystems/irishealth:2026.2.0AI.146.0

USER irisowner

ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"


WORKDIR /home/irisowner/dev

COPY keys/IRISHealth.key /usr/irissys/mgr/iris.key

COPY ./iris.script /home/irisowner/iris.script
COPY ./fhirsampledata/patients /tmp/fhirdata
COPY ./projects .
ARG OPENAI_API_KEY
RUN sed -i "s|__APIKEY__|${OPENAI_API_KEY}|g" /home/irisowner/iris.script

ENV IRISNAMESPACE "READYAI"
WORKDIR /home/irisowner/dev

RUN iris start IRIS \
    && iris session IRIS < /home/irisowner/iris.script\ 
    && rm /home/irisowner/iris.script \
    && iris stop IRIS quietly
