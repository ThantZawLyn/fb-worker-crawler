FROM joyzoursky/python-chromedriver:3.9-selenium

WORKDIR /pysetup
COPY /app/requirements.txt /pysetup/

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update

WORKDIR /usr/src/app
RUN apt-get -y install nodejs
RUN mkdir ./screenshots
RUN ln -sf /usr/share/zoneinfo/Asia/Yangon /etc/localtime

CMD nohup node ./proxy/proxy.js > ./proxy/log


COPY . /app/ /usr/src/app