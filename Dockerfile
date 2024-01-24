FROM ubuntu:rolling
ENV LANG="C.UTF-8" DEBIAN_FRONTEND="noninteractive"
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02apt-speedup && echo "Acquire::http {No-Cache=True;};" > /etc/apt/apt.conf.d/no-cache && echo 'Acquire::Languages "none";' > /etc/apt/apt.conf.d/no-lang
RUN apt-get -y update && apt-get -y upgrade && apt-get clean
RUN apt-get install -y qgis-server fonts-open-sans && apt-get clean
RUN apt-get install -y mapproxy make && apt-get clean
#RUN apt-get install -y make python3-pip && apt-get clean && pip install MapProxy --break-system-packages
ENV QGIS_SERVER_ADDRESS=0.0.0.0
EXPOSE 8000/tcp
USER ubuntu:ubuntu
