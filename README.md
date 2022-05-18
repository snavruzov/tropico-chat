Tropico Web Chat API service
===============
Web chat is built on top of the FastAPI using websocket connectivity and redis pub/sub technology to deliver messages in real-time.

Requirements
------------
Tested with all combinations of:
* Python: 3.8
* FastAPI: 0.74^
* PostgreSQL: 14^
* Redis: 5^
* Uvicorn: 0.17^
* RabbitMQ: 6^


Run the project
----------
Make sure you have Docker installed:
```sh
$ docker run hello-world
```

Make sure you are running a docker-compose from the root of the project folder, since the docker-compose will look for its YAML configuration file which is located in the project base directory **/docker-compose.yml**
```sh
$ docker-compose up  
```
