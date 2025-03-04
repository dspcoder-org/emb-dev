# Docker Image for question development 

map local directory to /tmp, image will treat /tmp as azure storage

    docker build --platform linux/amd64 -t dspcoder-dev .

    docker run -d --name dspcoder-dev-container -p 8080:8080 -p 9090:9090 dspcoder-dev

    docker cp /path/to/host/folder dspcoder-dev-container:/tmp/