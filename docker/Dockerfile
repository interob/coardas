FROM python:3.11-slim-bullseye AS build

ENV PYTHONUNBUFFERED 1
ENV CPUS 2

RUN apt-get update -y && \
    apt-get install --no-install-recommends -y \
        sudo bash-completion vim nano gettext wget file \
        ca-certificates unzip pkg-config gnupg git \
        software-properties-common build-essential cmake gcc automake autoconf \
        libtool swig nasm \
        libbz2-dev zlib1g-dev libminizip-dev zip expect \
        libpython3-dev \
        libpq-dev \
        libpoppler-dev \
        libnetcdf-dev libhdf4-alt-dev libhdf5-serial-dev \
        libfreexl-dev libxml2-dev libxslt1-dev \
        libjpeg-dev libpng-dev libgif-dev \
        && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

WORKDIR /tmp

ENV ZSTD_VERSION 1.5.4
RUN wget -q -O zstd-${ZSTD_VERSION}.tar.gz https://github.com/facebook/zstd/releases/download/v${ZSTD_VERSION}/zstd-${ZSTD_VERSION}.tar.gz \
    && tar -zxf zstd-${ZSTD_VERSION}.tar.gz \
    && cd zstd-${ZSTD_VERSION} \
    && echo "building ZSTD ${ZSTD_VERSION}..." \
    && make \
    && make install

ENV LIBDEFLATE_VERSION 1.17
RUN wget -q https://github.com/ebiggers/libdeflate/archive/refs/tags/v${LIBDEFLATE_VERSION}.tar.gz \
    && tar -zxf v${LIBDEFLATE_VERSION}.tar.gz \
    && cd libdeflate-${LIBDEFLATE_VERSION} \
    && echo "building libdeflate ${LIBDEFLATE_VERSION}..." \
    && cmake -B build && cmake --build build \
    && cd build && make && make install

ENV GEOS_VERSION 3.11.2
RUN wget -q https://download.osgeo.org/geos/geos-${GEOS_VERSION}.tar.bz2 \
    && tar -xjf geos-${GEOS_VERSION}.tar.bz2  \
    && cd geos-${GEOS_VERSION} \
    && ./configure --prefix=/usr/local \
    && echo "building geos ${GEOS_VERSION}..." \
    && make --quiet -j${CPUS} && make --quiet install

ENV SQLITE_VERSION 3400100
ENV SQLITE_YEAR 2022
RUN wget -q https://sqlite.org/${SQLITE_YEAR}/sqlite-autoconf-${SQLITE_VERSION}.tar.gz \
    && tar -xzf sqlite-autoconf-${SQLITE_VERSION}.tar.gz && cd sqlite-autoconf-${SQLITE_VERSION} \
    && ./configure --prefix=/usr/local \
    && echo "building SQLITE ${SQLITE_VERSION}..." \
    && make --quiet -j${CPUS} && make --quiet install

RUN wget -q https://www.openssl.org/source/openssl-1.1.1t.tar.gz \
    && tar -xzvf openssl-1.1.1t.tar.gz \
    && cd openssl-1.1.1t \
    && ./config \
    && make install

ENV NGHTTP2_VERSION 1.52.0
RUN wget -q https://github.com/nghttp2/nghttp2/releases/download/v${NGHTTP2_VERSION}/nghttp2-${NGHTTP2_VERSION}.tar.gz \
    && tar -xzf nghttp2-${NGHTTP2_VERSION}.tar.gz \
    && cd nghttp2-${NGHTTP2_VERSION} \
    && echo "building NGHTTP2 ${NGHTTP2_VERSION}..." \
    && ./configure --enable-lib-only --prefix=/usr/local \
    && make --quiet -j${CPUS} && make --quiet install

ENV CURL_VERSION 8.0.1
RUN wget -q https://curl.haxx.se/download/curl-${CURL_VERSION}.tar.gz \
    && tar -xzf curl-${CURL_VERSION}.tar.gz && cd curl-${CURL_VERSION} \
    && ./configure --prefix=/usr/local --with-openssl --enable-versioned-symbols \
    && echo "building CURL ${CURL_VERSION}..." \
    && make --quiet -j${CPUS} \
    && make --quiet install

ENV LIBTIFF_VERSION=4.5.0
RUN wget -q https://download.osgeo.org/libtiff/tiff-${LIBTIFF_VERSION}.tar.gz \
    && tar -xzf tiff-${LIBTIFF_VERSION}.tar.gz \
    && cd tiff-${LIBTIFF_VERSION} \
    && ./configure --prefix=/usr/local \
    && echo "building libtiff ${LIBTIFF_VERSION}..." \
    && make --quiet -j${CPUS} && make --quiet install

ENV PROJ_VERSION 9.2.0
RUN wget -q https://download.osgeo.org/proj/proj-${PROJ_VERSION}.tar.gz \
    && tar -xzf proj-${PROJ_VERSION}.tar.gz \
    && cd proj-${PROJ_VERSION} && mkdir build && cd build \
    && cmake -DBUILD_TESTING=OFF .. && cmake --build . && cmake --build . --target install \
    && ldconfig
    
RUN projsync --all --system-directory

ENV LIBGEOTIFF_VERSION=1.7.1
RUN wget -q https://github.com/OSGeo/libgeotiff/releases/download/${LIBGEOTIFF_VERSION}/libgeotiff-${LIBGEOTIFF_VERSION}.tar.gz \
    && tar -xzf libgeotiff-${LIBGEOTIFF_VERSION}.tar.gz \
    && cd libgeotiff-${LIBGEOTIFF_VERSION} \
    && ./configure --prefix=/usr/local --with-zlib --with-jpeg \
    && echo "building libgeotiff ${LIBGEOTIFF_VERSION}..." \
    && make --quiet -j${CPUS} && make --quiet install

ENV RTTOPO_VERSION 1.1.0
RUN wget -q https://git.osgeo.org/gitea/rttopo/librttopo/archive/librttopo-${RTTOPO_VERSION}.tar.gz \
    && tar -xzvf librttopo-${RTTOPO_VERSION}.tar.gz && cd librttopo \
    && ./autogen.sh && ./configure \
    && make && make install \
    && ldconfig

RUN python3 -m pip install numpy

ENV GDAL_VERSION 3.6.3
RUN wget -q https://download.osgeo.org/gdal/${GDAL_VERSION}/gdal-${GDAL_VERSION}.tar.gz \
    && tar -xzf gdal-${GDAL_VERSION}.tar.gz
RUN cd gdal-${GDAL_VERSION} && mkdir build && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release .. \
    && cmake --build . && cmake --build . --target install \
    && ldconfig
