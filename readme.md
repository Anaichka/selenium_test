To run script in docker container execute these commands:

> sudo docker build -t selenium_test .

> sudo docker run --rm -v "$(pwd):/app" selenium_test

OR

If you have installed chromedriver, just run **main.py**

The example result is stored in the **data.json**
