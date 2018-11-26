FROM python
MAINTAINER "Butter Group"
EXPOSE 5004
ADD requirements.txt ./app/
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
RUN python setup.py develop
RUN mkdir -p src/flakon/flakon/static
RUN mv docs src/flakon/flakon/static/
CMD ["beepbeep-trainingobjectiveservice"]