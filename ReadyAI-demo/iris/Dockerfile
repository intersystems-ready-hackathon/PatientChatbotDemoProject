FROM i4h-aihub-142

ENV IRISUSERNAME "SuperUser"
ENV IRISPASSWORD "SYS"

COPY iris.cpf /usr/irissys/IRIS.cpf

WORKDIR /home/irisowner/dev


COPY ./iris.script /opt/irisbuild/iris.script
COPY ./fhirsampledata/patients /tmp/fhirdata
COPY ./projects .

RUN sed -i "s|__APIKEY__|${OPENAI_API_KEY}|g" /opt/irisbuild/iris.script

ENV IRISNAMESPACE "READYAI"
WORKDIR /home/irisowner/dev

RUN iris start IRIS \
    && iris session IRIS < /opt/irisbuild/iris.script\ 
    && rm /opt/irisbuild/iris.script \
    && iris stop IRIS quietly
