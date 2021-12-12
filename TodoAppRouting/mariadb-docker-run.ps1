
# MARIADB ENV VARS
$CONTAINER_NAME = 'todoapp-routing-mariadb'
$MARIADB_ROOT_PASSWORD = 'root'
$MARIADB_USER = 'dev'
$MARIADB_PASSWORD = 'dev'
$MARIADB_DATABASE = 'todoapp_routing'
$TZ = 'Asia/Seoul'

# RUN MARIADB 10.4 Docker
docker run --name $CONTAINER_NAME `
    -e MARIADB_ROOT_PASSWORD=$MARIADB_ROOT_PASSWORD `
    -e MARIADB_USER=$MARIADB_USER `
    -e MARIADB_PASSWORD=$MARIADB_PASSWORD `
    -e MARIADB_DATABASE=$MARIADB_DATABASE `
    -e TZ=$TZ `
    -d -p 0.0.0.0:3306:3306 mariadb:10.4