FROM ubuntu:20.04
COPY requirements.txt /
COPY install.sh /
COPY serv_app.py /
COPY templates /templates
RUN chmod +x  /install.sh
RUN /bin/bash /install.sh
EXPOSE 5000
#ENTRYPOINT ["/serv_app.py"]
# ENTRYPOINT ["python3 "]
# CMD ["serv_app.py"]
#CMD python3 /serv_app.py
CMD ["service", "elasticsearch", "start"]
#ENTRYPOINT ["python3","/serv_app.py"]
# copy everything
# run install.sh
