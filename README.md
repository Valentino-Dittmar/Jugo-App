# IBCS Compliance Checker 
This repo contains the code for IBCS Compliance Checker web app. This web application is made as a proof-of-concept for developing an AI-powered tool to analyze the IBCS compliance of dashboards regarding the color rule and time-structure rule.

## :computer: Tech Stack
- Python
- Flask
- HTML, CSS, JavaScript
- Ultralytics YOLO
- OpenAI API

### AI Models Used
- Object detection: YOLOv5 and YOLOv8
- Text-on-image recognition and text output: GPT-4.1

## :bulb: Prerequisites

Before you begin, ensure you have the following installed: 
- [Python](https://www.python.org/downloads/release/python-380/) (version 3.8 or higher) 
- Necessary extensions (requirements.txt)
- [Git](https://git-scm.com/)


## :fast_forward: Getting Started

Follow these steps to set up the project repository on your local machine.

### Cloning the Repository
```bash
git clone https://github.com/Valentino-Dittmar/Jugo-App.git
```

### Installation
Install the project dependencies using pip install:

``` bash
pip install -r requirements.txt
```

### Running the Development Server
```bash
python app.py
```

## :bangbang: Important Note on API Connection
If you are cloning this repository and want to run the application locally or deploy it on your own platform, you will need to get your own API token from [OpenAI](https://openai.com/index/openai-api/).