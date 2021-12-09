FROM python:3.7
MAINTAINER Alex Toptunov 'shuriktoptusha@gmail.com'
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENTRYPOINT [ "python" ]
CMD [ "run.py" ]