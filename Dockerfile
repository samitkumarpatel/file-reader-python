FROM python:3.12.3
RUN mkdir /usr/application
WORKDIR /usr/application
ADD file-processor-v1.py  requirment.txt /usr/application/
RUN pip3 install -r requirment.txt

ENTRYPOINT [ "python3","file-processor-v1.py" ]