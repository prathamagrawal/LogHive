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