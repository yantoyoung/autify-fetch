* The script is written in Python and tested using Python version 3.12
* The script uses `requests` library to send HTTP requests and `BeautifulSoup4` to parse web pages to find the assets (images, stylesheets and scripts) to download.
* A Dockerfile is included to allow the script to be tested in a Docker container. To build the Docker image:

    ```bash
    docker build -t autify-fetch:1.0 -f Dockerfile .
    ```

* After the image is built, the container can be run as follows:

    ```bash
    docker run -it --rm -v $(pwd):/app autify-fetch:1.0 bash
    ```

  This will mount the current directory to `/app` inside the container, which should have all the required dependencies installed. 

* You should now be in the bash shell inside the container and can run the script from inside the container. Example:

    ```python
    python fetch.py --metadata https://rubyonrails.org
    ```

  Since the current directory is mounted on the container, the files will be saved on it. Using the example above, the script will create a sub-directory named `rubyonrails.org` and save the files under the sub-directory.
