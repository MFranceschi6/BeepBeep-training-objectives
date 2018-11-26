FROM python
MAINTAINER "Butter Group"
EXPOSE 5004
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
COPY . .
RUN python setup.py develop
RUN mv docs src/flakon/flakon/static/
CMD ["beepbeep-trainingobjectiveservice"]