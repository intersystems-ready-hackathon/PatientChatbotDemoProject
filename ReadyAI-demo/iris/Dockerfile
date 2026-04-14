FROM docker.iscinternal.com/intersystems/irishealth-community:2026.2.0AI.147.0

USER irisowner

ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"


WORKDIR /home/irisowner/dev


COPY ./iris.script /home/irisowner/iris.script
COPY ./fhirsampledata/patients /tmp/fhirdata
COPY ./projects .
ARG OPENAI_API_KEY
RUN sed -i "s|__APIKEY__|${OPENAI_API_KEY}|g" /home/irisowner/iris.script

ENV IRISNAMESPACE "READYAI"
WORKDIR /home/irisowner/dev

RUN export PATH=/usr/irissys/bin:$PATH 

RUN iris start IRIS \
    && iris session IRIS < /home/irisowner/iris.script\ 
    && rm /home/irisowner/iris.script \
    && iris stop IRIS quietly
