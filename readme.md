To run script in docker container execute this commands:

docker build -t selenium_test .

sudo docker run --rm -v "$(pwd):/app" selenium_test

OR

If you have installed chromedriver, just run main.py