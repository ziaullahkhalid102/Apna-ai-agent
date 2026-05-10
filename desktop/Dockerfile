FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1
ENV VNC_PORT=5900
ENV NOVNC_PORT=6080
ENV RESOLUTION=1920x1080x24

# ── System packages ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    # VNC + Desktop
    tigervnc-standalone-server \
    tigervnc-common \
    dbus-x11 \
    xfce4 \
    xfce4-terminal \
    xfce4-goodies \
    # noVNC
    novnc \
    websockify \
    # Browser
    wget \
    curl \
    gnupg \
    ca-certificates \
    # Development tools
    git \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    # Editors
    nano \
    vim \
    # Supervisor
    supervisor \
    # Utils
    xdg-utils \
    net-tools \
    procps \
    htop \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# ── VS Code (code-server) ──
RUN curl -fsSL https://code-server.dev/install.sh | sh -s -- --version 4.96.4

# ── Google Chrome ──
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/google.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ── Android Command Line Tools ──
RUN mkdir -p /opt/android-sdk/cmdline-tools \
    && wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip -O /tmp/cmdtools.zip \
    && unzip -q /tmp/cmdtools.zip -d /opt/android-sdk/cmdline-tools \
    && mv /opt/android-sdk/cmdline-tools/cmdline-tools /opt/android-sdk/cmdline-tools/latest \
    && rm /tmp/cmdtools.zip

ENV ANDROID_HOME=/opt/android-sdk
ENV PATH="${PATH}:${ANDROID_HOME}/cmdline-tools/latest/bin:${ANDROID_HOME}/platform-tools"

# Accept Android SDK licenses and install basic SDK components
RUN yes | sdkmanager --licenses > /dev/null 2>&1 || true \
    && sdkmanager "platforms;android-35" "build-tools;35.0.0" "platform-tools" --no_https > /dev/null 2>&1 || true

# ── Create workspace user ──
RUN useradd -m -s /bin/bash agent \
    && echo "agent:agent" | chpasswd \
    && usermod -aG sudo agent

# ── VNC setup ──
RUN mkdir -p /home/agent/.vnc \
    && echo "agent" | vncpasswd -f > /home/agent/.vnc/passwd \
    && chmod 600 /home/agent/.vnc/passwd \
    && chown -R agent:agent /home/agent/.vnc

# ── noVNC symlink ──
RUN ln -sf /usr/share/novnc/vnc.html /usr/share/novnc/index.html

# ── Supervisor config ──
COPY supervisord.conf /etc/supervisor/conf.d/agent-desktop.conf
COPY startup.sh /usr/local/bin/startup.sh
RUN chmod +x /usr/local/bin/startup.sh

# ── Workspace ──
RUN mkdir -p /workspace && chown agent:agent /workspace
WORKDIR /workspace

EXPOSE 5900 6080 8443

CMD ["/usr/local/bin/startup.sh"]
