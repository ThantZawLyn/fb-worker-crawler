# fb-worker-crawler
docker build -t mglue/fb-worker-base-image:latest -f Dockerfile .
docker push mglue/fb-worker-base-image:latest
=============
docker build -t mglue/fb-worker:latest -f Dockerfile .