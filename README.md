This is my homework for Python Advanced Course, last upd: 09-12-2021

Examples of usage are stored at `examples` folder.

Short summary:
1. Models and datasets are stored using pickle. databases could be better but on the other hand it's easier to run with less dependencies
2. Models are connected to users while datasets are common for all users. This is done for simplification of usage of standard datasets.
3. However, all the requirements are met and extended with Swagger documentation for easier access to api
4. Datasets sample1 and sample2 are pre-created for easier usage of api as you do not need to create you own dataset to try api

====================
UPDATES OF HW2:
1. Database is used for models managing, with CRUD operations (in models/user_models.py)
2. The app is divided into two parts (for two containers) - public api+datasets and models part. The division could be better but I based on the existing app so it was the best I created.
3. Both apps are stored in Dockerhub at https://hub.docker.com/r/top2know/api_app and https://hub.docker.com/r/top2know/models_app
4. There is docker-compose.yml which includes postgres image for database and runs it all (and it works fine on my computer!)
For easier run you can use docker-compose_local.yml as it doesn't pull images of the app so in case of some changes this method should let check them.

Known problem is that I didn't use .env file so it works locally with the selected user for postgres, hosts and ports, but I may not work on other devices.
As far as the workability of the app was not the main point (because we should try to work with databases and docker) (joke), I hope it is just a small problem that won't make me lose lots of points (I already lost many because of late submission because of lots of reasons).
I know that .env is definitely better and will fix everything but I'm really tired and I really hope I'll still be able to get some above zero points.
Also I didn't use volumes in docker-compose and I could work better with database, but once again I'm overtired and hope for understanding.
If you feel that I try to lie and that my app is not working, you can contact me via Telegram and I'll show you that it really works!

Also I didn't use Telegram bot because I read that it's not obligatory. However, thanks to Swagger you can still check my API (after .env problems).
Thanks for understanding!
