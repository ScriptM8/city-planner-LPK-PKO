# Dockerfile

FROM python:3.10-slim

# 1. Uzstādām mainīgo, lai apt-get darbotos “non-interactive” režīmā
ENV DEBIAN_FRONTEND=noninteractive

# 2. Instalējam OpenJDK 17 (headless režīms, mazāks apjoms)
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-17-jdk-headless && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Norādam JAVA_HOME (nav obligāti, bet drošības pēc var)
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
