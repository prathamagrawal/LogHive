<h1 align="center">LogHive</h1>
<hr> 


### Database Setup:
```postgresql
create schema logs;
```


```bash
alembic revision --autogenerate -m "message"
# to create migrations file 

alembic upgrade head
#to run migrations
```


# Todo 
1. Requeue messages in a different queue to consume in case of any failures - Done ✅
2. Consumer flag to turn on the failure backoff 