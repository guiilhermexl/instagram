# Imagem base com PHP + Apache
FROM php:8.2-apache

# Habilita extensões necessárias
RUN docker-php-ext-install pdo pdo_mysql

# Copia os arquivos do projeto para dentro do container
COPY . /var/www/html/

# Ativa mod_rewrite
RUN a2enmod rewrite

# Define o diretório de trabalho
WORKDIR /var/www/html

# Porta que será exposta
EXPOSE 80
