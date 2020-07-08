FROM rust

WORKDIR /home/qacaller


COPY . .
COPY ./config  /usr/local/cargo/config
ENV QAACOUNTPRO_RS_ROOT=/home/project/qaaccpro_rs
ENV QAACOUNTPRO_RS_RELEASE=/home/project/qaaccpro_rs/target/release/examples
ENV QAACOUNTPRO_RS_MAIN=arp_actor_single

RUN echo \
    deb http://mirrors.163.com/debian/ buster main contrib non-free\
    deb http://mirrors.163.com/debian/ buster-updates main contrib non-free\
    deb http://mirrors.163.com/debian/ buster-backports main contrib non-free\
    deb http://mirrors.163.com/debian-security buster/updates main contrib non-free\
    > /etc/apt/sources.list

RUN apt-get update\
    && apt-get install -y build-essential\
    && apt-get install -y pkg-config\
    && apt-get install -y libssl-dev\
    && apt-get install -y openssl\
    && apt-get install -y python3.7 python3.7-dev python3.7-distutils\
    && apt-get install -y python3-pip

RUN python3.7 -m pip install -r requirements.txt -i https://pypi.douban.com/simple\
    && git clone https://yutiansut:6b4bc9ab4ce95028e68d20ddd2a56ba6bc7d4045@github.com/yutiansut/qaaccountpro-rs.git $QAACOUNTPRO_RS_ROOT\
    && cd $QAACOUNTPRO_RS_ROOT\
    && cargo update\
    && cargo build --example arp_actor_single --release


EXPOSE 8864
