FROM centos
RUN yum install -y epel-release
RUN yum update -y 
RUN yum install -y crudini gcc libffi-devel  openssl-devel git gcc build-essentials python-devel python-pip
RUN mkdir /opt/fiware
RUN git clone https://github.com/telefonicaid/fiware-glancesync/ /opt/fiware/glancesync/
WORKDIR /opt/fiware/glancesync/
RUN sed -i -e "s/six==1.8.0/six/" requirements.txt
RUN pip install -r requirements.txt
RUN pip install -r test-requirements.txt 
RUN pip install -r fiwareglancesync/scripts/getnids/requirements.txt
ENV GLANCESYNC_SETTINGS_FILE=/opt/fiware/glancesync/fiwareglancesync/app/settings/fiware-glancesync.cfg
ENV GLANCESYNC_LOGGING_SETTINGS_FILE=/opt/fiware/glancesync/fiwareglancesync/app/settings/fiware-glancesync-logging.cfg
ENV GLANCESYNCAPP_DATABASE_PATH=/opt/fiware/glancesync/fiwareglancesync
ENV GLANCESYNCAPP_CONFIG=/opt/fiware/glancesync/fiwareglancesync/app/config.py
RUN mkdir /opt/fiware/glancesync/test_results/
RUN mkdir /opt/fiware/glancesync/coverage/
COPY sonar-project.properties sonar-project.properties
CMD nosetests --with-coverage --cover-package=./ --cover-xml --cover-xml-file=coverage/coverage.xml --with-xunit --xunit-file=test_results/TEST-nosetests.xml --exe

