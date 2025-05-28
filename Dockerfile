FROM python:3.10-slim

# Instala Chrome headless
RUN apt-get update && apt-get install -y wget gnupg unzip curl     && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -     && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list     && apt-get update && apt-get install -y google-chrome-stable     && rm -rf /var/lib/apt/lists/*

# Instala chromedriver
RUN CHROMEDRIVER_VERSION=$(curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE) &&     wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip &&     unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ &&     chmod +x /usr/local/bin/chromedriver

# Instala dependências do Python
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copia a aplicação
COPY . .

# Porta do servidor Flask
ENV PORT 5000
CMD ["python", "id.py"]
