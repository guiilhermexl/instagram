FROM php:8.2-apache

# Copia todos os arquivos do seu projeto para dentro do container
COPY . /var/www/html/

# Dá permissões para o Apache
RUN chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html

# Ativa o módulo de reescrita (opcional se for usar rotas amigáveis)
RUN a2enmod rewrite
