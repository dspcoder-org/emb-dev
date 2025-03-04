# ------------------------------------------------------------------------------
# DSPCODER Software License
# ------------------------------------------------------------------------------
# 
# Licensed under the DSPCODER Software License (the "DspcoderSoftwareLicense");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
# 
#     http://www.dspcoder.com/licenses
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# 
# ------------------------------------------------------------------------------
# Project: Backend Image
# S/W Ver: dspcoderBI_0.1         
# Version: Renode v1.15.2.2748  (Link: https://builds.renode.io/renode-latest.linux-dotnet.tar.gz)
#          dspcoderVSCode_0.1
#          Valgrind v3.24.0
# Purpose: This Dockerfile is used to create a docker image for the backend server
#          of DSPCODER. The image is used to run the backend server and provide
#          the necessary tools for the backend server to function.
# 
# Host OS: Ubuntu 22.04
# 
# Copyright (c) 2024 DSPCODER. All rights reserved.
# 
# ------------------------------------------------------------------------------
# Usage:
# This Dockerfile is strictly for internal use within DSPCODER. Redistribution, 
# commercial use, or any form of usage outside of DSPCODER is strictly prohibited 
# without prior written consent from DSPCODER. 
# 
# The image supports the development for ARM and AVR architectures. Future releases 
#  will expand support for additional architectures.
# 
# ------------------------------------------------------------------------------
# Disclaimer:
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE 
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR 
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS 
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN 
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE 
# POSSIBILITY OF SUCH DAMAGE.
# ------------------------------------------------------------------------------


FROM ubuntu:22.04

# Set non-interactive frontend
ENV DEBIAN_FRONTEND=noninteractive

# Combine RUN commands and clean up in the same layer
RUN apt-get update && apt-get install -y --no-install-recommends sudo rsync curl libc6-dbg tmux\
    # will be useful for future
    # python3 make gcc-arm-none-eabi gdb-multiarch qemu-system gcc-avr avr-libc gdb-avr gcc g++ \  
    python3 make gcc-arm-none-eabi gdb-multiarch gcc g++ \
    clangd dotnet8 python3-pip \
    && apt install wget && apt install bzip2 \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/gdb-multiarch /usr/bin/arm-none-eabi-gdb


# Install Code Server
RUN curl -fsSL https://code-server.dev/install.sh | sh
# Uninstall curl
RUN apt-get remove -y curl && apt-get autoremove -y && apt-get clean

# Create dspcoder folder with root read/write permissions only
RUN mkdir /dspcoder && chmod 700 /dspcoder
RUN mkdir /dspcoder/codeFromServer
RUN mkdir /dspcoder/results
RUN mkdir /dspcoder/localSave
RUN mkdir /dspcoder/azure_setup
RUN mkdir /dspcoder/backend

# Install python support libraries
RUN pip install telnetlib3 pycryptodome
# RUN pip install azure-storage-blob --target /dspcoder/azure_setup

# Install Renode
COPY ./perry/renode-latest.linux-dotnet.tar.gz /tmp/
RUN mkdir /dspcoder/renode && \
    tar -xzf /tmp/renode-latest.linux-dotnet.tar.gz -C /dspcoder/renode --strip-components=1 && \
    rm /tmp/renode-latest.linux-dotnet.tar.gz

# # Install valgrind
# COPY ./koro/valgrind-3.24.0.tar.bz2 /dspcoder
# RUN cd /dspcoder && \
#     tar xvf valgrind-3.24.0.tar.bz2 && \
#     cd valgrind-3.24.0 && \
#     ./configure --prefix=/dspcoder/valgrind && \
#     make -j$(nproc) && \
#     make install && \
#     cd /dspcoder && \
#     rm -rf valgrind-3.24.0 valgrind-3.24.0.tar.bz2 && \
#     apt-get remove -y wget bzip2 build-essential && \
#     apt-get autoremove -y && \
#     apt-get clean

# Copy the scripts folder
COPY ./scripts /dspcoder/scripts
RUN chmod 700 /dspcoder/scripts/*

# Copy koro, perry and other support scripts
COPY ./setupCodeBase.py /dspcoder/
COPY ./JSONHandler.py /dspcoder/
COPY ./koro /dspcoder/koro/
COPY ./perry /dspcoder/perry/
COPY ./azureScripts/ /dspcoder/azure_setup/

#copy extension and users settings
COPY ./extension/dspcoder-panel-0.0.1.vsix /bin
COPY ./codeserver/settings.json /dspcoder/settings.json

# setting up the bash prompt
RUN bash -c 'echo "export PS1=\"\[\033[1;32m\]\u@dspcoder -> \[\033[1;31m\]\W \$ \[\033[0m\]\"" >> /etc/bash.bashrc'

# Expose the Nginx port
EXPOSE 8080 9090

# Start Supervisor
CMD ["/dspcoder/scripts/newUserSetup.sh"]