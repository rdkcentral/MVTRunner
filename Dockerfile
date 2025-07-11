FROM python:3.12
RUN apt-get update && apt-get install -y \
        sshpass
ARG UNAME=mvt-runner
ARG UID=1000
ARG GID=1000
RUN groupadd -g $GID -o $UNAME && \
	useradd -m -u $UID -g $GID -o -s /bin/bash $UNAME && \
	mkdir /MVT && chown $UNAME:$GID /MVT
USER $UNAME
WORKDIR /MVT
COPY --chown=$UNAME:$GID mvt_requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY --chown=$UNAME:$GID ./ .
ENTRYPOINT ["python3", "-m", "pytest"]

