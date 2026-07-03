FROM owasp/modsecurity:nginx

COPY crs/rules/ /etc/modsecurity.d/rules/
COPY crs/crs-setup.conf.example /etc/modsecurity.d/crs-setup.conf

RUN printf '\n\
SecAction "id:900000,phase:1,pass,t:none,nolog,\
setvar:tx.blocking_paranoia_level=2"\n' \
    >> /etc/modsecurity.d/crs-setup.conf

COPY conf/setup.conf.template /etc/nginx/templates/modsecurity.d/setup.conf.template

COPY conf/default.conf.template /etc/nginx/templates/conf.d/default.conf.template

COPY certs/server.crt /etc/nginx/conf/server.crt
COPY certs/server.key /etc/nginx/conf/server.key
