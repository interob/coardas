FROM ubuntu:24.04 AS build

RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        sudo bash-completion vim nano gettext wget curl less gawk file iputils-ping \
        python-is-python3 python3-pip \
        ca-certificates unzip pkg-config gnupg git \
        software-properties-common build-essential cmake gcc automake autoconf \
        libtool swig nasm \
        libbz2-dev zlib1g-dev libminizip-dev zip expect \
        libpython3-dev libgdal-dev gdal-bin \
        postgresql-client libpq-dev \
        libpoppler-dev \
        libnetcdf-dev libhdf4-alt-dev libhdf5-serial-dev \
        libfreexl-dev libxml2-dev libxslt1-dev \
        libjpeg-dev libturbojpeg0-dev libpng-dev libgif-dev \
        libzstd-dev libdeflate-dev libgeos-dev libzstd-dev libsqlite3-dev libproj-dev libtiff5-dev \
        zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev \
        libcurl4-openssl-dev libxml2-dev libxslt1-dev libpcre3-dev git \
        p7zip-full libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /tmp

ENV PYTHONUNBUFFERED 1
ENV CPUS 2

RUN pip install numpy --break-system-packages
RUN pip install gdal==$(gdal-config --version) --break-system-packages
