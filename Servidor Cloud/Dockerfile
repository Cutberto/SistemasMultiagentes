FROM python:2-alpine

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN apk --update add python py-pip openssl ca-certificates py-openssl wget bash linux-headers
RUN apk --update add --virtual build-dependencies libffi-dev openssl-dev python-dev py-pip build-base \
  && pip install --upgrade pip \
  && pip install --upgrade pipenv\
  && pip install --upgrade -r /app/requirements.txt\
  && !pip install mesa
  && apk del build-dependencies 
RUN pip install mesa  

COPY . /app

ENTRYPOINT [ "python" ]

CMD [ "hello.py" ]