FROM ghcr.io/openconfig/gnmic:0.45.0 AS gnmic

FROM ghcr.io/srl-labs/network-multitool:v0.9.0
USER root

RUN apk add --no-cache \
    bash \
    bind-tools \
    curl \
    git \
    iperf3 \
    iproute2 \
    iputils \
    jq \
    make \
    openssh-client \
    procps \
    python3 \
    tcpdump \
    traceroute

COPY --from=gnmic /app/gnmic /usr/local/bin/gnmic
COPY dns_server.py netbox_bootstrap.py probe_exporter.py ssh_config bob1_model.json /opt/ai5049/
COPY welcome.sh /etc/profile.d/ai5049.sh
RUN chmod 0755 /usr/local/bin/gnmic /opt/ai5049/dns_server.py /opt/ai5049/netbox_bootstrap.py /opt/ai5049/probe_exporter.py \
    && chmod 0600 /opt/ai5049/ssh_config \
    && chmod 0644 /etc/profile.d/ai5049.sh
