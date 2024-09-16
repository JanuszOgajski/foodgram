Проект доступен для ознакомления ---> [`Здесь`](https://taski.3utilities.com/)\

## Как развернуть проект?

Перед началом работы нужно выполнить несколько подготовочных шагов, чтобы не отвлекаться от процесса развертывания:

`Шаг 1` Убедитесь что у вас есть доступ к удалённому серверу.\
`Шаг 2` Очистите ваш сервер от лишнего мусора, вот [`тут`](https://gist.github.com/fernandoaleman/4dc2e514f612bc376d0f54cc3d15b608) можно посмотреть как это сделать правильно.\
`Шаг 3` Зарегистрируйтесь на [`DockerHub`](https://hub.docker.com/) без него вам некуда будет загрузить сбилденные образы.

### Установка
1. Склонируйте репозиторий и перейдите в него:
```console
git clone https://github.com/JanuszOgajski/foodgram.git
```
```console
cd foodgram
```
2. Создайте файл `.env`, в нём должны быть указаны переменные окружения, образец заполнения можно посмотреть в файле `.env.example`, который лежит в корневой директории проекта.
3. Установите Docker, последовательно выполняя команды:
```console
sudo apt update
```
```console
sudo apt install curl
```
```console
curl -fsSL https://get.docker.com -o get-docker.sh
```
```console
sudo sh ./get-docker.sh
```
Обязательно проверьте что `Docker` работает:
```console
docker --version
```
Если вы увидели что-то вроде:
```
Docker version 27.1.1, build 6312585
```
Значит `Docker` установлен успешно! Можно переходить к следующему этапу.

### Создание образов Docker
1. Сбилдите образы, замените `username` на ваш логин на DockerHub:
```console
cd foodgram/backend
docker build -t username/foodgram_backend .
cd ../frontend
docker build -t username/foodgram_frontend .
cd ../infra
docker build -t username/foodgram_gateway .
```
2. Загрузите уже готовые образы на DockerHub, замените `username` на ваш логин на DockerHub:
```console
docker push username/foodgram_backend
docker push username/foodgram_frontend
docker push username/foodgram_gateway
```
3. Проверьте что образы действительно загрузились на DockerHub
### Деплой

#### Пояснение:
`ssh-path` - Путь к файлу с закрытым SSH-ключом.\
`ssh` - Файл с закрытым SSH-ключом.\
`user` - Имя вашего пользователя на сервере.\
`host` - IP-адрес вашего сервера.

1. Подключитесь к вашему серверу, например вот так:
```console
ssh -i ssh-path/ssh user@host
```
2. Создайте директорию в которой будет храниться файл с переменными окружения - `.env`,\
а также композиционный файл - `docker-compose.production.yml`:
```console
sudo mkdir foodgram
```
3. Установите на сервер Docker, как делали это на этапе установки, а затем Docker Compose:
```console
sudo apt update
```
```console
sudo apt install curl
```
```console
curl -fsSL https://get.docker.com -o get-docker.sh
```
```console
sudo sh ./get-docker.sh
```
```console
sudo apt install docker-compose
```
Проверьте что Docker Compose работает:
```console
docker-compose --version
```
Вы должны увидеть версию, если ее нет, значит возникла ошибка установки, внимательно проверьте всё ли правильно вы ввели:
```
Docker Compose version v2.29.1
```
4. Скопируйте локальные файлы `docker-compose.production.yml` и `.env` в директорию `foodgram` на сервере.\
Это можно сделать вручную, но удобнее и быстрее всего это будет сделать через консоль:
```console
sudo scp -i ssh-path/ssh docker-compose.production.yml user@host:/home/user/foodgram/docker-compose.production.yml
```
```console
sudo scp -i ssh-path/ssh .env user@host:/home/user/foodgram/.env
```
5. Скачайте все образы с вашего профиля:
```console
sudo docker-compose -f /home/user/foodgram/docker-compose.production.yml pull
```
5. Запустите Docker Compose в фоновом режиме:
```console
sudo docker-compose -f /home/user/foodgram/docker-compose.production.yml up -d
```
6. Выполните миграции, соберите статику и скопируйте ее в `/static/static/`:
```console
sudo docker-compose -f /home/user/foodgram/docker-compose.production.yml exec backend python manage.py migrate
```
```console
sudo docker-compose -f /home/user/foodgram/docker-compose.production.yml exec backend python manage.py collectstatic
```
```console
sudo docker-compose -f /home/user/foodgram/docker-compose.production.yml exec backend cp -r /app/static/. /static/static/
```
7. Загрузите данные из `json` в базу данных:
```console
sudo docker-compose -f /home/user/foodgram/docker-compose.production.yml exec backend python manage.py import_data
```
Вы должны увидеть статус `Success`, если всё прошло гладко:
```
SUCCESSFULLY LOADED `TAG` DATA
SUCCESSFULLY LOADED `INGREDIENT` DATA
```

### Настройка Nginx
1. Откройте конфигурационный файл `Nginx` в редакторе `Nano`:
```console
sudo nano /etc/nginx/sites-enabled/default
```
2. Измените настройки location в секции server:
```console
location / {
    proxy_set_header Host $http_host;
    proxy_pass http://127.0.0.1:8000;
}
```
Не забудьте нажать `Ctrl+S` чтобы сохранить изменения, а затем `Ctrl+X`, чтобы выйти из редактора `Nano`
3. Проверьте правильность конфигурации Nginx:
```console
sudo nginx -t
```
Вот такой ответ вы должны получить, если с конфигом всё нормально:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```
4. Перезагрузите Nginx:
```console
sudo systemctl reload nginx
```
Провертье статус Nginx:
```console
sudo systemctl status nginx
```
Если Nginx запущен и работает как положено ждите такой ответ:
```
● nginx.service - A high performance web server and a reverse proxy server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Fri 2024-08-02 10:32:25 UTC; 22h ago
       Docs: man:nginx(8)
    Process: 38339 ExecStartPre=/usr/sbin/nginx -t -q -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
    Process: 38341 ExecStart=/usr/sbin/nginx -g daemon on; master_process on; (code=exited, status=0/SUCCESS)
   Main PID: 38342 (nginx)
      Tasks: 3 (limit: 2219)
     Memory: 9.0M
        CPU: 2.152s
     CGroup: /system.slice/nginx.service
             ├─38342 "nginx: master process /usr/sbin/nginx -g daemon on; master_process on;"
             ├─38343 "nginx: worker process" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""
             └─38344 "nginx: worker process" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" "" ""
```
Nginx настроен, статика раздаётся, все страницы уже должны быть доступны в том виде, в котором они задумывались.
Теперь если вы перейдете по адресу `https://your-domain...` вам будет доступен полностью рабочий сервис `Foodgram`.

## Настройка CI/CD

`CI/CD` - Непрерывная интеграция и непрерывное развертывание ПО в процессе разработки.

Эта методология позволяет осуществлять автоматическое тестирование, развертывание проекта, файл с настройками находится: `.github/workflows/main.yml`.

Работа скрипта настроена таким образом, что при каждом `push` в проект: 
  1. Запускается тестирование `backend` части проекта.
  2. Автоматически билдятся образы, а затем загружаются на профиль `DockerHub`.
  3. Образы пулятся на сервер, а затем собираются в `контейнеры`.
  4. Выполняются миграции, сбор статики, копирование статики в директорию `/static/static/`.
  5. Json файлы из директории `data/` импортируются и на их основе создаются объекты в бд.

Чтобы настроить `workflow` для работы с проектом, вам нужно добавить переменные-секреты в `Actions Secrets`:
1. В `GitHub` Перейдите в репозиторий с проектом `Foodgram`.
2. Зайдите в настройки проекта.
3. В левой панели ищем настройку `Secrets and variables`, в выкатывающемся окне ищем `Actions` - туда нам и надо.
4. На этой странице находятся все секретные ключи и значения для работы `workflow`. Нужно добавить все секреты которые есть у меня, для этого нужно нажать на `New Repository secret`.
5. Здесь всё просто. Добавляете название ключа и его значение, затем сохраняете. И так со всеми секретными значениями.
6. Вот список всех необходимых секретов, которые нужно создать:

```s
DOCKER_USERNAME     # Ваш логин на DockerHub
DOCKER_PASSWORD     # Пароль DockerHub
HOST_IP             # IP-адрес сервера
HOST_LOGIN          # Имя пользователя на сервере
SSH_KEY             # Закрытый SSH-ключ
SSH_PASSPHRASE      # Пас-фраза от SSH-ключа
TELEGRAM_BOT_TOKEN  # Токен телеграм бота
TELEGRAM_USER_ID    # Уникальный ID пользователя телеграм
```

> [!WARNING]
> Перед тем, как использовать workflow нужно удалить композиционный файл `docker-compose.production.yml` в директории `foodgram` на вашем удаленном сервере, иначе возникнет ошибка о невозможности открытия файла, изза того, что он уже существует в указанной директории.

---

